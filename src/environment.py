"""
Environment detection and configuration utilities
Supports both local and Azure cloud deployments
"""
import os
import logging
from pathlib import Path
import io
import threading
from datetime import date
import sys

# Safe formatter that handles Unicode encoding errors gracefully
class SafeFormatter(logging.Formatter):
    """Formatter that safely handles Unicode characters"""
    def format(self, record):
        try:
            return super().format(record)
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            # Fallback: replace problematic characters
            try:
                msg = record.getMessage()
                # Replace Unicode characters that can't be encoded
                safe_msg = msg.encode('ascii', 'replace').decode('ascii')
                record.msg = safe_msg
                return super().format(record)
            except Exception:
                # Last resort: return basic message
                return f"{record.levelname} - {record.name} - {record.getMessage()}"

def is_azure_environment():
    """
    Detect if running in Azure App Service
    """
    # Azure App Service sets WEBSITE_INSTANCE_ID
    # Also check for other Azure-specific environment variables
    azure_indicators = [
        'WEBSITE_INSTANCE_ID',
        'WEBSITE_SITE_NAME',
        'WEBSITE_RESOURCE_GROUP',
        'APPSETTING_WEBSITE_SITE_NAME'
    ]
    return any(os.getenv(var) for var in azure_indicators)

def sanitize_account_name_for_filename(account_name):
    """
    Sanitize account name for use in filenames
    - Extract first name only (first word before space)
    - Replace spaces with underscores
    - Remove or replace special characters that might cause filesystem issues
    - Limit length to avoid filesystem path length issues
    """
    if not account_name:
        return 'TRADING_ACCOUNT'
    
    # Extract first name only (first word before space)
    first_name = account_name.split()[0] if account_name.split() else account_name
    
    # Remove or replace other problematic characters
    # Keep only alphanumeric, underscores, and hyphens
    import re
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', first_name)
    
    # Limit length to 30 characters to avoid filesystem issues
    if len(sanitized) > 30:
        sanitized = sanitized[:30]
    
    return sanitized if sanitized else 'TRADING_ACCOUNT'

def format_date_for_filename(date_obj):
    """
    Format date as YYYYMONDD (e.g., 2025Dec11)
    """
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return f"{date_obj.year}{month_names[date_obj.month - 1]}{date_obj.day:02d}"

class AzureBlobStorageHandler(logging.Handler):
    """
    Custom logging handler that writes logs to Azure Blob Storage
    Logs are buffered and uploaded periodically to maintain performance
    """
    def __init__(self, connection_string, container_name, blob_path, account_name=None):
        super().__init__()
        self.connection_string = connection_string
        self.container_name = container_name
        self.blob_path = blob_path  # Full path including folder structure
        self.account_name = account_name
        self.buffer = io.StringIO()
        self.buffer_lock = threading.Lock()
        self.flush_interval = 30  # Flush every 30 seconds
        import time
        self.last_flush = time.time()
        self._ensure_container_exists()
        
    def _ensure_container_exists(self):
        """Ensure the container exists in Azure Blob Storage"""
        try:
            from azure.storage.blob import BlobServiceClient
            blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            container_client = blob_service_client.get_container_client(self.container_name)
            
            if container_client.exists():
                print(f"[AZURE BLOB] Container '{self.container_name}' already exists")
            else:
                print(f"[AZURE BLOB] Container '{self.container_name}' does not exist, creating...")
                container_client.create_container()
                print(f"[AZURE BLOB] ✓ Container '{self.container_name}' created successfully")
                
                # Verify container was created
                if container_client.exists():
                    print(f"[AZURE BLOB] ✓✓ Verified: Container '{self.container_name}' exists")
                else:
                    print(f"[AZURE BLOB] ⚠ Warning: Container '{self.container_name}' creation verification failed")
        except Exception as e:
            print(f"[AZURE BLOB] ✗ ERROR: Could not ensure container exists: {type(e).__name__}: {e}")
            import traceback
            print(f"[AZURE BLOB] Container creation traceback: {traceback.format_exc()}")
    
    def emit(self, record):
        """Emit a log record to the buffer"""
        try:
            msg = self.format(record)
            with self.buffer_lock:
                self.buffer.write(msg + '\n')
                # Flush if buffer is large enough or enough time has passed
                import time
                current_time = time.time()
                if (self.buffer.tell() > 8192 or  # 8KB buffer
                    current_time - self.last_flush > self.flush_interval):
                    self._flush_to_blob()
        except Exception:
            self.handleError(record)
    
    def _flush_to_blob(self, force=False):
        """Flush buffer contents to Azure Blob Storage
        
        Args:
            force: If True, create blob even if buffer is empty (for initial blob creation)
        """
        try:
            with self.buffer_lock:
                # Get current buffer content
                self.buffer.seek(0)
                content = self.buffer.read()
                self.buffer.seek(0)
                self.buffer.truncate(0)
                
                # If buffer is empty and not forcing, skip
                if not content and not force:
                    return
                
                # Ensure we have at least a newline for empty blob creation
                if not content and force:
                    content = "\n"
                
                # Upload to Azure Blob Storage
                from azure.storage.blob import BlobServiceClient
                blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
                blob_client = blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=self.blob_path
                )
                
                # Append to existing blob or create new one
                existing_content = None
                try:
                    # Try to download existing content and append
                    existing_content = blob_client.download_blob().readall().decode('utf-8')
                    content = existing_content + content
                    print(f"[AZURE BLOB] Appending to existing blob (existing size: {len(existing_content)} bytes)")
                except Exception as download_error:
                    # Blob doesn't exist yet, create new one
                    print(f"[AZURE BLOB] Blob doesn't exist yet, creating new blob: {download_error}")
                
                # Upload the content (this creates the blob if it doesn't exist)
                try:
                    print(f"[AZURE BLOB] Attempting to upload {len(content)} bytes to {self.container_name}/{self.blob_path}")
                    blob_client.upload_blob(content, overwrite=True)
                    print(f"[AZURE BLOB] ✓ Upload successful: {len(content)} bytes uploaded")
                    
                    import time
                    self.last_flush = time.time()
                    
                    # Verify blob exists immediately after upload
                    import time as time_module
                    time_module.sleep(0.5)  # Small delay for Azure to propagate
                    
                    verification_attempts = 3
                    blob_exists = False
                    for attempt in range(verification_attempts):
                        try:
                            if blob_client.exists():
                                blob_exists = True
                                print(f"[AZURE BLOB] ✓✓ Verified: Blob exists at {self.container_name}/{self.blob_path} (attempt {attempt + 1})")
                                break
                            else:
                                print(f"[AZURE BLOB] ⚠ Verification attempt {attempt + 1}: Blob not found yet, retrying...")
                                time_module.sleep(1)
                        except Exception as verify_error:
                            print(f"[AZURE BLOB] ⚠ Verification attempt {attempt + 1} failed: {verify_error}")
                            time_module.sleep(1)
                    
                    if not blob_exists:
                        print(f"[AZURE BLOB] ⚠⚠ WARNING: Blob verification failed after {verification_attempts} attempts")
                        print(f"[AZURE BLOB] Container: {self.container_name}, Blob path: {self.blob_path}")
                        print(f"[AZURE BLOB] Full URL would be: https://<account>.blob.core.windows.net/{self.container_name}/{self.blob_path}")
                        
                except Exception as upload_error:
                    error_details = f"[AZURE BLOB] ✗✗ UPLOAD FAILED: {type(upload_error).__name__}: {str(upload_error)}"
                    print(error_details)
                    import traceback
                    print(f"[AZURE BLOB] Upload traceback: {traceback.format_exc()}")
                    raise  # Re-raise to be caught by outer exception handler
                
        except Exception as e:
            error_msg = f"[AZURE BLOB] Error flushing to blob {self.container_name}/{self.blob_path}: {e}"
            print(error_msg)
            import traceback
            print(f"[AZURE BLOB] Traceback: {traceback.format_exc()}")
            # Put content back in buffer for retry if we have content
            if 'content' in locals() and content and content != "\n":
                with self.buffer_lock:
                    self.buffer.seek(0, 2)  # Seek to end
                    self.buffer.write(content)
    
    def flush(self, force=False):
        """Flush any buffered logs to Azure Blob Storage
        
        Args:
            force: If True, create blob even if buffer is empty (for initial blob creation)
        """
        self._flush_to_blob(force=force)
        super().flush()
    
    def close(self):
        """Close the handler and flush any remaining logs"""
        self.flush()
        super().close()

def setup_azure_blob_logging(account_name=None, logger_name='root'):
    """
    Setup Azure Blob Storage logging handler
    Creates logs in Azure Blob Storage with folder structure: {account_name}/logs/{filename}.log
    """
    try:
        # Try different import paths to work in both local and Azure environments
        try:
            from src.config import AZURE_BLOB_CONNECTION_STRING, AZURE_BLOB_CONTAINER_NAME, AZURE_BLOB_LOGGING_ENABLED
        except ImportError:
            # Fallback for Azure environment where 'src' might not be in path
            import sys
            import os
            # Add parent directory to path if not already there
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            # Try importing again
            from src.config import AZURE_BLOB_CONNECTION_STRING, AZURE_BLOB_CONTAINER_NAME, AZURE_BLOB_LOGGING_ENABLED
        
        # Add prefix to identify if this is from trading strategy (has account_name) vs dashboard (no account_name)
        prefix = "[STRATEGY]" if account_name else "[DASHBOARD]"
        
        # Always print diagnostic info (even if disabled)
        print(f"{prefix} [AZURE BLOB] Checking configuration...")
        print(f"{prefix} [AZURE BLOB] AZURE_BLOB_LOGGING_ENABLED = {AZURE_BLOB_LOGGING_ENABLED}")
        print(f"{prefix} [AZURE BLOB] Connection string available: {AZURE_BLOB_CONNECTION_STRING is not None}")
        print(f"{prefix} [AZURE BLOB] Container name: {AZURE_BLOB_CONTAINER_NAME}")
        if account_name:
            print(f"{prefix} [AZURE BLOB] Account name: {account_name} (will create folder: {sanitize_account_name_for_filename(account_name)})")
        
        if not AZURE_BLOB_LOGGING_ENABLED:
            print("[AZURE BLOB] Logging is DISABLED. Set AZURE_BLOB_LOGGING_ENABLED=True in Azure Portal.")
            return None, None
        
        # Check if connection string is available
        if not AZURE_BLOB_CONNECTION_STRING:
            print("[AZURE BLOB] ERROR: Azure Blob Storage connection string not available.")
            print("[AZURE BLOB] Required environment variables in Azure Portal:")
            print("[AZURE BLOB]   1. AzureBlobStorageKey = <your-storage-account-key>")
            print("[AZURE BLOB]   2. AZURE_BLOB_ACCOUNT_NAME = s0001strangle")
            print("[AZURE BLOB]   3. AZURE_BLOB_CONTAINER_NAME = s0001strangle")
            print("[AZURE BLOB]   4. AZURE_BLOB_LOGGING_ENABLED = True")
            print("[AZURE BLOB] Go to: Azure Portal > App Service > Configuration > Application settings")
            return None, None
        
        logger = logging.getLogger(logger_name)
        
        # Determine blob path
        if account_name:
            sanitized_account = sanitize_account_name_for_filename(account_name)
            date_str = format_date_for_filename(date.today())
            # Folder structure: {sanitized_account_name}/logs/{sanitized_account}_{date_str}.log
            # Use sanitized account name for folder to avoid blob path issues
            blob_path = f"{sanitized_account}/logs/{sanitized_account}_{date_str}.log"
        else:
            date_str = format_date_for_filename(date.today())
            blob_path = f"logs/trading_{date_str}.log"
        
        # Create Azure Blob handler
        blob_handler = AzureBlobStorageHandler(
            connection_string=AZURE_BLOB_CONNECTION_STRING,
            container_name=AZURE_BLOB_CONTAINER_NAME,
            blob_path=blob_path,
            account_name=account_name
        )
        
        # Set formatter (same format as file handler)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        blob_handler.setFormatter(formatter)
        blob_handler.setLevel(logging.INFO)
        
        # Add handler to logger
        logger.addHandler(blob_handler)
        
        # Write initial test message to verify it works
        prefix = "[STRATEGY]" if account_name else "[DASHBOARD]"
        print(f"{prefix} [AZURE BLOB] Writing initial test message to blob...")
        logger.info(f"[AZURE BLOB] Azure Blob Storage logging initialized: {AZURE_BLOB_CONTAINER_NAME}/{blob_path}")
        
        # Give a small delay to ensure the log message is written to buffer
        import time
        time.sleep(1.0)  # Increased delay to ensure message is in buffer
        
        # Force immediate flush of initial message (force=True ensures blob is created even if empty)
        print(f"{prefix} [AZURE BLOB] Flushing buffer to create blob...")
        try:
            blob_handler.flush(force=True)
            print(f"{prefix} [AZURE BLOB] Flush completed")
        except Exception as flush_error:
            print(f"{prefix} [AZURE BLOB] ✗ Flush failed: {flush_error}")
            import traceback
            print(f"{prefix} [AZURE BLOB] Flush traceback: {traceback.format_exc()}")
        
        # Verify blob was created with retries
        print(f"{prefix} [AZURE BLOB] Verifying blob creation...")
        blob_verified = False
        for verify_attempt in range(5):
            try:
                from azure.storage.blob import BlobServiceClient
                blob_service_client = BlobServiceClient.from_connection_string(AZURE_BLOB_CONNECTION_STRING)
                blob_client = blob_service_client.get_blob_client(
                    container=AZURE_BLOB_CONTAINER_NAME,
                    blob=blob_path
                )
                if blob_client.exists():
                    print(f"{prefix} [AZURE BLOB] ✓✓✓ SUCCESS: Blob verified at attempt {verify_attempt + 1}")
                    print(f"{prefix} [AZURE BLOB] Blob URL: https://<account>.blob.core.windows.net/{AZURE_BLOB_CONTAINER_NAME}/{blob_path}")
                    blob_verified = True
                    break
                else:
                    print(f"{prefix} [AZURE BLOB] ⚠ Verification attempt {verify_attempt + 1}: Blob not found, waiting...")
                    time.sleep(2)
            except Exception as verify_error:
                print(f"{prefix} [AZURE BLOB] ⚠ Verification attempt {verify_attempt + 1} error: {verify_error}")
                time.sleep(2)
        
        if not blob_verified:
            print(f"{prefix} [AZURE BLOB] ✗✗✗ WARNING: Blob verification FAILED after 5 attempts")
            print(f"{prefix} [AZURE BLOB] Container: {AZURE_BLOB_CONTAINER_NAME}")
            print(f"{prefix} [AZURE BLOB] Blob path: {blob_path}")
            print(f"{prefix} [AZURE BLOB] Expected URL: https://<account>.blob.core.windows.net/{AZURE_BLOB_CONTAINER_NAME}/{blob_path}")
            print(f"{prefix} [AZURE BLOB] Please check Azure Portal > Storage Account > Container for errors")
        
        print(f"{prefix} [AZURE BLOB] Logging to Azure Blob: {AZURE_BLOB_CONTAINER_NAME}/{blob_path}")
        print(f"{prefix} [AZURE BLOB] Initial test message sent. Check container: {AZURE_BLOB_CONTAINER_NAME}")
        if account_name:
            print(f"{prefix} [AZURE BLOB] Full blob path: {AZURE_BLOB_CONTAINER_NAME}/{blob_path}")
        return blob_handler, blob_path
        
    except ImportError as e:
        print(f"[AZURE BLOB] Warning: Azure Blob Storage not available: {e}")
        return None, None
    except Exception as e:
        print(f"[AZURE BLOB] Warning: Failed to setup Azure Blob logging: {e}")
        import traceback
        print(traceback.format_exc())
        return None, None

def get_log_directory(account_name=None):
    """
    Get the appropriate log directory based on environment
    - Local: src/logs directory
    - Azure: /tmp/{account_name}/logs/ (account-specific directory in /tmp)
    """
    if is_azure_environment():
        # Azure: Use /tmp/{account_name}/logs/ structure
        if account_name:
            # Sanitize account name for directory name
            sanitized_account = sanitize_account_name_for_filename(account_name)
            log_dir = os.path.join('/tmp', sanitized_account, 'logs')
        else:
            # Fallback to /tmp/logs if no account name
            log_dir = '/tmp/logs'
    else:
        # Local: use src/logs directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(current_dir, 'logs')
    
    # Create directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

def setup_azure_logging(logger_name='root', account_name=None):
    """
    Setup logging for Azure App Service
    Azure automatically captures stdout/stderr, so we configure both file and console logging
    Logs are stored in /tmp/{account_name}/logs/ and also uploaded to Azure Blob Storage
    
    CRITICAL FIX: Always add handlers to root logger to ensure logging.info() calls work
    """
    # Get both named logger and root logger
    logger = logging.getLogger(logger_name)
    root_logger = logging.getLogger()  # Root logger - this is what logging.info() uses
    
    # Get log directory (account-specific for Azure)
    log_dir = get_log_directory(account_name=account_name)
    
    # Create safe formatter that handles Unicode characters
    formatter = SafeFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler (Azure captures stdout/stderr automatically)
    # Set stream encoding to UTF-8 for Windows compatibility
    console_handler = logging.StreamHandler()
    # On Windows, ensure stdout/stderr use UTF-8
    if sys.platform == 'win32':
        try:
            import codecs
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass  # Fallback to default if reconfigure fails
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # File handler for persistent logs - use account name if provided
    if account_name:
        # Sanitize account name for filename (first name only)
        sanitized_account = sanitize_account_name_for_filename(account_name)
        # Format date as YYYYMONDD (e.g., 2025Dec11)
        date_str = format_date_for_filename(date.today())
        log_file = os.path.join(log_dir, f'{sanitized_account}_{date_str}.log')
    else:
        log_file = os.path.join(log_dir, 'trading_bot.log')
    # Ensure directory exists before creating file handler
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Create file handler with immediate flush (unbuffered) and UTF-8 encoding
    try:
        # Use mode='a' for append, UTF-8 encoding, and errors='replace' to handle any Unicode issues
        # Note: FileHandler doesn't support errors parameter directly, but we use SafeFormatter
        file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a', delay=False)
        file_handler.setFormatter(formatter)  # SafeFormatter handles Unicode encoding errors
        file_handler.setLevel(logging.INFO)
        
        # CRITICAL FIX: Add handlers to ROOT logger (what logging.info() uses)
        # This ensures all logging.info() calls throughout the codebase write to file
        if not any(isinstance(h, logging.FileHandler) and h.baseFilename == log_file for h in root_logger.handlers):
            root_logger.addHandler(file_handler)
            root_logger.setLevel(logging.INFO)
        
        # Also add to named logger if it's different from root
        if logger_name != 'root' and logger != root_logger:
            if not any(isinstance(h, logging.FileHandler) and h.baseFilename == log_file for h in logger.handlers):
                logger.addHandler(file_handler)
                logger.setLevel(logging.INFO)
        
        # Add console handler to root logger as well
        if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
            root_logger.addHandler(console_handler)
        
        # Ensure named logger propagates to root (default behavior, but make explicit)
        logger.propagate = True
        
        # Setup Azure Blob Storage logging
        prefix = "[STRATEGY]" if account_name else "[DASHBOARD]"
        print(f"{prefix} [LOG SETUP] Setting up Azure Blob Storage logging for account: {account_name}")
        blob_handler, blob_path = setup_azure_blob_logging(account_name=account_name, logger_name=logger_name)
        if blob_handler:
            logger.info(f"[LOG SETUP] Azure Blob Storage logging enabled: {blob_path}")
            print(f"{prefix} [LOG SETUP] SUCCESS: Azure Blob Storage logging configured: {blob_path}")
            if account_name:
                print(f"{prefix} [LOG SETUP] Strategy logs will be written to: s0001strangle/{blob_path}")
        else:
            print(f"{prefix} [LOG SETUP] ERROR: Azure Blob Storage logging NOT configured (check environment variables)")
            logger.warning(f"[LOG SETUP] Azure Blob Storage logging not available - check environment variables")
        
        # Force file creation by writing an initial log message
        # This ensures the file exists immediately
        # Use root logger to ensure it works
        root_logger.info(f"[LOG SETUP] Log file created at: {log_file}")
        root_logger.info(f"[LOG SETUP] Log directory: {log_dir}")
        file_handler.flush()  # Force write to disk
        os.fsync(file_handler.stream.fileno()) if hasattr(file_handler.stream, 'fileno') else None  # Force OS-level flush
        
        # Verify file was created and is writable
        if os.path.exists(log_file):
            try:
                # Test write access with UTF-8 encoding
                with open(log_file, 'a', encoding='utf-8', errors='replace') as test_file:
                    test_file.write("")
                # Use ASCII-safe characters for print statements to avoid encoding issues
                print(f"[LOG SETUP] SUCCESS: Log file created and writable: {log_file}")
            except Exception as write_test:
                print(f"[LOG SETUP] WARNING: Log file exists but may not be writable: {write_test}")
        else:
            print(f"[LOG SETUP] ERROR: Log file was NOT created: {log_file}")
        
        print(f"[LOG SETUP] Log file path: {log_file}")
        print(f"[LOG SETUP] Log directory: {log_dir}")
        print(f"[LOG SETUP] Root logger handlers: {len(root_logger.handlers)}")
        print(f"[LOG SETUP] Named logger handlers: {len(logger.handlers)}")
        
    except Exception as e:
        error_msg = f"[LOG SETUP] Failed to create log file {log_file}: {e}"
        print(error_msg)
        import traceback
        error_trace = traceback.format_exc()
        print(error_trace)
        # Try to log to root logger (might not have handlers yet)
        try:
            root_logger.error(error_msg)
            root_logger.error(error_trace)
        except:
            pass
        # Fallback: try to create at least console logging on root logger
        if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
            root_logger.addHandler(console_handler)
            root_logger.setLevel(logging.INFO)
        return logger, None
    
    return logger, log_file

def setup_local_logging(log_dir=None, account_name=None, logger_name='root'):
    """
    Setup logging for local environment
    Logs are stored locally and also uploaded to Azure Blob Storage if enabled
    
    CRITICAL FIX: Always add handlers to root logger to ensure logging.info() calls work
    """
    # Get both named logger and root logger
    logger = logging.getLogger(logger_name)
    root_logger = logging.getLogger()  # Root logger - this is what logging.info() uses
    
    if log_dir is None:
        log_dir = get_log_directory()
    
    # Create safe formatter that handles Unicode characters
    formatter = SafeFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler with UTF-8 encoding for Windows
    console_handler = logging.StreamHandler()
    # On Windows, ensure stdout/stderr use UTF-8
    if sys.platform == 'win32':
        try:
            import codecs
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass  # Fallback to default if reconfigure fails
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # File handler with account name
    if account_name:
        # Sanitize account name for filename (first name only)
        sanitized_account = sanitize_account_name_for_filename(account_name)
        # Format date as YYYYMONDD (e.g., 2025Dec11)
        date_str = format_date_for_filename(date.today())
        log_filename = os.path.join(log_dir, f'{sanitized_account}_{date_str}.log')
    else:
        # Format date as YYYYMONDD
        date_str = format_date_for_filename(date.today())
        log_filename = os.path.join(log_dir, f'trading_{date_str}.log')
    
    # Ensure directory exists before creating file handler
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    
    # Create file handler with UTF-8 encoding and safe formatter
    try:
        # Use UTF-8 encoding with SafeFormatter to handle Unicode characters
        file_handler = logging.FileHandler(log_filename, encoding='utf-8', mode='a', delay=False)
        file_handler.setFormatter(formatter)  # SafeFormatter handles Unicode encoding errors
        file_handler.setLevel(logging.INFO)
        
        # CRITICAL FIX: Add handlers to ROOT logger (what logging.info() uses)
        # This ensures all logging.info() calls throughout the codebase write to file
        if not any(isinstance(h, logging.FileHandler) and h.baseFilename == log_filename for h in root_logger.handlers):
            root_logger.addHandler(file_handler)
            root_logger.setLevel(logging.INFO)
        
        # Also add to named logger if it's different from root
        if logger_name != 'root' and logger != root_logger:
            if not any(isinstance(h, logging.FileHandler) and h.baseFilename == log_filename for h in logger.handlers):
                logger.addHandler(file_handler)
                logger.setLevel(logging.INFO)
        
        # Add console handler to root logger as well
        if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
            root_logger.addHandler(console_handler)
        
        # Ensure named logger propagates to root (default behavior, but make explicit)
        logger.propagate = True
        
        # Setup Azure Blob Storage logging
        blob_handler, blob_path = setup_azure_blob_logging(account_name=account_name, logger_name=logger_name)
        if blob_handler:
            logger.info(f"[LOG SETUP] Azure Blob Storage logging enabled: {blob_path}")
        
        # Force file creation by writing an initial log message
        # This ensures the file exists immediately
        # Use root logger to ensure it works
        root_logger.info(f"[LOG SETUP] Log file created at: {log_filename}")
        root_logger.info(f"[LOG SETUP] Log directory: {log_dir}")
        file_handler.flush()  # Force write to disk
        os.fsync(file_handler.stream.fileno()) if hasattr(file_handler.stream, 'fileno') else None  # Force OS-level flush
        
        # Verify file was created and is writable
        if os.path.exists(log_filename):
            try:
                # Test write access with UTF-8 encoding
                with open(log_filename, 'a', encoding='utf-8', errors='replace') as test_file:
                    test_file.write("")
                print(f"[LOG SETUP] SUCCESS: Log file created and writable: {log_filename}")
            except Exception as write_test:
                print(f"[LOG SETUP] WARNING: Log file exists but may not be writable: {write_test}")
        else:
            print(f"[LOG SETUP] ERROR: Log file was NOT created: {log_filename}")
        
        print(f"[LOG SETUP] Log file path: {log_filename}")
        print(f"[LOG SETUP] Log directory: {log_dir}")
        print(f"[LOG SETUP] Root logger handlers: {len(root_logger.handlers)}")
        print(f"[LOG SETUP] Named logger handlers: {len(logger.handlers)}")
        
    except Exception as e:
        error_msg = f"[LOG SETUP] Failed to create log file {log_filename}: {e}"
        print(error_msg)
        logging.error(error_msg)
        import traceback
        logging.error(traceback.format_exc())
        # Fallback: try to create at least console logging
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
        return logger, None
    
    return logger, log_filename

def setup_logging(account_name=None, logger_name='root'):
    """
    Universal logging setup that works in both local and Azure environments
    """
    # Add prefix to identify if this is from trading strategy (has account_name) vs dashboard (no account_name)
    prefix = "[STRATEGY]" if account_name else "[DASHBOARD]"
    print(f"{prefix} [SETUP LOGGING] Starting logging setup - account_name={account_name}, logger_name={logger_name}")
    
    if is_azure_environment():
        print(f"{prefix} [SETUP LOGGING] Azure environment detected")
        logger, log_file = setup_azure_logging(logger_name, account_name=account_name)
        logging.info(f"[ENV] Running in Azure App Service - Logs: {log_file}")
        logging.info(f"[ENV] Azure Log Stream: Available via Azure Portal > Log stream")
        if account_name:
            logging.info(f"[ENV] Account name: {account_name}")
            print(f"{prefix} [SETUP LOGGING] Strategy logs will be written to blob: {account_name}/logs/")
        print(f"{prefix} [SETUP LOGGING] Azure logging setup complete - log_file={log_file}")
        return logger, log_file
    else:
        logger, log_file = setup_local_logging(account_name=account_name, logger_name=logger_name)
        logging.info(f"[ENV] Running locally - Log file: {log_file}")
        if account_name:
            logging.info(f"[ENV] Account name: {account_name}")
        return logger, log_file

def get_config_value(key, default=None):
    """
    Get configuration value from environment variables (Azure) or config file (local)
    Azure App Service uses environment variables prefixed with APPSETTING_
    """
    # Try Azure App Service environment variable format
    azure_key = f'APPSETTING_{key}'
    value = os.getenv(azure_key)
    if value:
        return value
    
    # Try direct environment variable
    value = os.getenv(key)
    if value:
        return value
    
    # Fallback to default
    return default

