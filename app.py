"""
WSGI entry point for Azure App Service
This file exposes the Flask application from src.config_dashboard for Azure deployment
"""
import os
import sys
import logging

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, current_dir)
sys.path.insert(0, src_dir)

logger.info(f"Current directory: {current_dir}")
logger.info(f"Source directory: {src_dir}")
logger.info(f"Python path: {sys.path[:3]}")

# Disable Azure Monitor OpenTelemetry if not properly configured
# This prevents "Bad Request" errors when Application Insights is misconfigured
if not os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING'):
    os.environ.setdefault('APPLICATIONINSIGHTS_ENABLE_AGENT', 'false')
    logging.getLogger('azure.monitor.opentelemetry').setLevel(logging.CRITICAL)

# Import the Flask app from config_dashboard
try:
    logger.info("Attempting to import Flask app from src.config_dashboard...")
    # Try importing from src.config_dashboard first (if src is a package)
    from src.config_dashboard import app
    logger.info("Successfully imported Flask app from src.config_dashboard")
except ImportError as e1:
    logger.warning(f"Import from src.config_dashboard failed: {e1}")
    # Fallback: try direct import if src directory is in path
    try:
        logger.info("Attempting direct import of config_dashboard...")
        import config_dashboard
        app = config_dashboard.app
        logger.info("Successfully imported Flask app via direct import")
    except (ImportError, AttributeError) as e2:
        logger.error(f"All import attempts failed. Last error: {e2}")
        # If import fails, create a minimal Flask app to prevent startup failure
        from flask import Flask
        app = Flask(__name__)
        
        @app.route('/')
        def index():
            import traceback
            error_details = traceback.format_exc()
            return f"""
            <h1>Application Error</h1>
            <p>Failed to import config_dashboard</p>
            <h2>Import Errors:</h2>
            <pre>src.config_dashboard: {e1}\nconfig_dashboard: {e2}</pre>
            <h2>Traceback:</h2>
            <pre>{error_details}</pre>
            <p>Please check that src/config_dashboard.py exists and is properly configured.</p>
            """, 500

# Export the app for gunicorn/WSGI servers
__all__ = ['app']

logger.info("Flask app loaded successfully and ready for WSGI server")

