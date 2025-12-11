"""
Environment detection and configuration utilities
Supports both local and Azure cloud deployments
"""
import os
import logging
from pathlib import Path

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
    Logs are stored in /tmp/{account_name}/logs/
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
    from datetime import date
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
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    
    # Log the file path where logs are being written
    logger.info(f"[LOG SETUP] Log file created at: {log_file}")
    logger.info(f"[LOG SETUP] Log directory: {log_dir}")
    print(f"[LOG SETUP] Log file will be written to: {log_file}")
    print(f"[LOG SETUP] Log directory: {log_dir}")
    
    return logger, log_file

def setup_local_logging(log_dir=None, account_name=None, logger_name='root'):
    """
    Setup logging for local environment
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
    from datetime import date
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
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    
    # Log the file path where logs are being written
    logger.info(f"[LOG SETUP] Log file created at: {log_filename}")
    logger.info(f"[LOG SETUP] Log directory: {log_dir}")
    print(f"[LOG SETUP] Log file will be written to: {log_filename}")
    print(f"[LOG SETUP] Log directory: {log_dir}")
    
    return logger, log_filename

def setup_logging(account_name=None, logger_name='root'):
    """
    Universal logging setup that works in both local and Azure environments
    """
    if is_azure_environment():
        logger, log_file = setup_azure_logging(logger_name, account_name=account_name)
        logging.info(f"[ENV] Running in Azure App Service - Logs: {log_file}")
        logging.info(f"[ENV] Azure Log Stream: Available via Azure Portal > Log stream")
        if account_name:
            logging.info(f"[ENV] Account name: {account_name}")
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

