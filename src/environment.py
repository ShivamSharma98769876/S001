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
            if not container_client.exists():
                container_client.create_container()
        except Exception as e:
            print(f"[AZURE BLOB] Warning: Could not ensure container exists: {e}")
    
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
    
    def _flush_to_blob(self):
        """Flush buffer contents to Azure Blob Storage"""
        try:
            with self.buffer_lock:
                if self.buffer.tell() == 0:
                    return
                
                # Get current buffer content
                self.buffer.seek(0)
                content = self.buffer.read()
                self.buffer.seek(0)
                self.buffer.truncate(0)
                
                if not content:
                    return
                
                # Upload to Azure Blob Storage
                from azure.storage.blob import BlobServiceClient
                blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
                blob_client = blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=self.blob_path
                )
                
                # Append to existing blob or create new one
                try:
                    # Try to download existing content and append
                    existing_content = blob_client.download_blob().readall().decode('utf-8')
                    content = existing_content + content
                except Exception:
                    # Blob doesn't exist yet, create new one
                    pass
                
                # Upload the content
                blob_client.upload_blob(content, overwrite=True)
                
                import time
                self.last_flush = time.time()
                
                # Log success (to console only, to avoid recursion)
                print(f"[AZURE BLOB] Successfully uploaded {len(content)} bytes to {self.container_name}/{self.blob_path}")
                
        except Exception as e:
            error_msg = f"[AZURE BLOB] Error flushing to blob {self.container_name}/{self.blob_path}: {e}"
            print(error_msg)
            import traceback
            print(f"[AZURE BLOB] Traceback: {traceback.format_exc()}")
            # Put content back in buffer for retry if we have content
            if 'content' in locals() and content:
                with self.buffer_lock:
                    self.buffer.seek(0, 2)  # Seek to end
                    self.buffer.write(content)
    
    def flush(self):
        """Flush any buffered logs to Azure Blob Storage"""
        self._flush_to_blob()
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
        
        # Always print diagnostic info (even if disabled)
        print(f"[AZURE BLOB] Checking configuration...")
        print(f"[AZURE BLOB] AZURE_BLOB_LOGGING_ENABLED = {AZURE_BLOB_LOGGING_ENABLED}")
        print(f"[AZURE BLOB] Connection string available: {AZURE_BLOB_CONNECTION_STRING is not None}")
        print(f"[AZURE BLOB] Container name: {AZURE_BLOB_CONTAINER_NAME}")
        
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
        logger.info(f"[AZURE BLOB] Azure Blob Storage logging initialized: {AZURE_BLOB_CONTAINER_NAME}/{blob_path}")
        blob_handler.flush()  # Force immediate flush of initial message
        
        print(f"[AZURE BLOB] Logging to Azure Blob: {AZURE_BLOB_CONTAINER_NAME}/{blob_path}")
        print(f"[AZURE BLOB] Initial test message sent. Check container: {AZURE_BLOB_CONTAINER_NAME}")
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
    """
    logger = logging.getLogger(logger_name)
    
    # Get log directory (account-specific for Azure)
    log_dir = get_log_directory(account_name=account_name)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler (Azure captures stdout/stderr automatically)
    console_handler = logging.StreamHandler()
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
    
    # Create file handler
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')  # 'a' for append mode
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        # Add handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)
        
        # Setup Azure Blob Storage logging
        print(f"[LOG SETUP] Setting up Azure Blob Storage logging for account: {account_name}")
        blob_handler, blob_path = setup_azure_blob_logging(account_name=account_name, logger_name=logger_name)
        if blob_handler:
            logger.info(f"[LOG SETUP] Azure Blob Storage logging enabled: {blob_path}")
            print(f"[LOG SETUP] ✓ Azure Blob Storage logging configured: {blob_path}")
        else:
            print(f"[LOG SETUP] ✗ Azure Blob Storage logging NOT configured (check environment variables)")
            logger.warning(f"[LOG SETUP] Azure Blob Storage logging not available - check environment variables")
        
        # Force file creation by writing an initial log message
        # This ensures the file exists immediately
        logger.info(f"[LOG SETUP] Log file created at: {log_file}")
        logger.info(f"[LOG SETUP] Log directory: {log_dir}")
        file_handler.flush()  # Force write to disk
        
        print(f"[LOG SETUP] Log file created at: {log_file}")
        print(f"[LOG SETUP] Log directory: {log_dir}")
        print(f"[LOG SETUP] File exists: {os.path.exists(log_file)}")
        
    except Exception as e:
        error_msg = f"[LOG SETUP] Failed to create log file {log_file}: {e}"
        print(error_msg)
        logging.error(error_msg)
        import traceback
        logging.error(traceback.format_exc())
        # Fallback: try to create at least console logging
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
        return logger, None
    
    return logger, log_file

def setup_local_logging(log_dir=None, account_name=None, logger_name='root'):
    """
    Setup logging for local environment
    Logs are stored locally and also uploaded to Azure Blob Storage if enabled
    """
    logger = logging.getLogger(logger_name)
    
    if log_dir is None:
        log_dir = get_log_directory()
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler
    console_handler = logging.StreamHandler()
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
    
    # Create file handler
    try:
        file_handler = logging.FileHandler(log_filename, encoding='utf-8', mode='a')  # 'a' for append mode
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        # Add handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)
        
        # Setup Azure Blob Storage logging
        blob_handler, blob_path = setup_azure_blob_logging(account_name=account_name, logger_name=logger_name)
        if blob_handler:
            logger.info(f"[LOG SETUP] Azure Blob Storage logging enabled: {blob_path}")
        
        # Force file creation by writing an initial log message
        # This ensures the file exists immediately
        logger.info(f"[LOG SETUP] Log file created at: {log_filename}")
        logger.info(f"[LOG SETUP] Log directory: {log_dir}")
        file_handler.flush()  # Force write to disk
        
        print(f"[LOG SETUP] Log file created at: {log_filename}")
        print(f"[LOG SETUP] Log directory: {log_dir}")
        print(f"[LOG SETUP] File exists: {os.path.exists(log_filename)}")
        
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
    print(f"[SETUP LOGGING] Starting logging setup - account_name={account_name}, logger_name={logger_name}")
    if is_azure_environment():
        print(f"[SETUP LOGGING] Azure environment detected")
        logger, log_file = setup_azure_logging(logger_name, account_name=account_name)
        logging.info(f"[ENV] Running in Azure App Service - Logs: {log_file}")
        logging.info(f"[ENV] Azure Log Stream: Available via Azure Portal > Log stream")
        if account_name:
            logging.info(f"[ENV] Account name: {account_name}")
        print(f"[SETUP LOGGING] Azure logging setup complete - log_file={log_file}")
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

