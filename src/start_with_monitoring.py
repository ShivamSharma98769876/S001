"""
Startup script for Trading Bot with Real-time Config Monitoring
Integrates config monitoring, web dashboard, and main strategy
"""

import os
import sys
import threading
import time
import logging
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_logging():
    """Setup logging for the monitoring system"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('config_monitoring.log'),
            logging.StreamHandler()
        ]
    )

def start_config_dashboard():
    """Start the web dashboard in a separate thread"""
    try:
        from config_dashboard import start_dashboard
        logging.info("[DASHBOARD] Starting web dashboard...")
        start_dashboard(host='127.0.0.1', port=5000, debug=False)
    except Exception as e:
        logging.error(f"[DASHBOARD] Failed to start dashboard: {e}")

def main():
    """Main startup function"""
    setup_logging()
    
    print("=" * 60)
    print("TRADING BOT WITH REAL-TIME CONFIG MONITORING")
    print("=" * 60)
    print("Features:")
    print("[OK] Real-time config file monitoring")
    print("[OK] Auto-reload parameters without restart")
    print("[OK] Web dashboard for parameter management")
    print("[OK] Configuration change history tracking")
    print("[OK] Parameter validation and rollback")
    print("=" * 60)
    
    # Start web dashboard in background thread
    dashboard_thread = threading.Thread(target=start_config_dashboard, daemon=True)
    dashboard_thread.start()
    
    # Give dashboard time to start
    time.sleep(2)
    
    print("\nWeb Dashboard: http://127.0.0.1:5000")
    print("Config Monitor: Active")
    print("Auto-reload: Enabled")
    print("\n" + "=" * 60)
    
    try:
        # Import and run the main strategy
        import importlib.util
        spec = importlib.util.spec_from_file_location("strategy", "Straddle10PointswithSL-Limit.py")
        strategy_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(strategy_module)
        strategy_main = strategy_module.main
        
        logging.info("[STARTUP] Starting main trading strategy...")
        strategy_main()
        
    except KeyboardInterrupt:
        logging.info("[STARTUP] Shutdown requested by user")
    except Exception as e:
        logging.error(f"[STARTUP] Unexpected error: {e}")
    finally:
        logging.info("[STARTUP] Shutting down monitoring system...")
        print("\n[STOPPED] Config monitoring stopped")

if __name__ == "__main__":
    main()
