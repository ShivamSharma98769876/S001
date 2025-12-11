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

def get_log_directory():
    """
    Get the appropriate log directory based on environment
    - Local: src/logs directory
    - Azure: /home/LogFiles (Azure App Service log directory)
    """
    if is_azure_environment():
        # Azure App Service log directory
        # Try multiple Azure log locations
        possible_dirs = [
            os.getenv('LOG_DIR'),
            '/home/LogFiles',
            '/home/LogFiles/Application',
            os.path.join(os.getenv('HOME', '/home'), 'LogFiles')
        ]
        log_dir = None
        for dir_path in possible_dirs:
            if dir_path and os.path.exists(dir_path):
                log_dir = dir_path
                break
        
        # Default to /home/LogFiles if none found (will be created)
        if not log_dir:
            log_dir = '/home/LogFiles'
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
    """
    logger = logging.getLogger(logger_name)
    
    # Get log directory
    log_dir = get_log_directory()
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler (Azure captures stdout/stderr automatically)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # File handler for persistent logs - use account name if provided
    from datetime import date
    if account_name:
        log_file = os.path.join(log_dir, f'{account_name} {date.today()}_trading_log.log')
    else:
        log_file = os.path.join(log_dir, 'trading_bot.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    
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
        log_filename = os.path.join(log_dir, f'{account_name} {date.today()}_trading_log.log')
    else:
        log_filename = os.path.join(log_dir, f'trading_{date.today()}_trading_log.log')
    
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    
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

