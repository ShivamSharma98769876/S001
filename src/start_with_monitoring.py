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

# Import dashboard configuration
try:
    import config
    DASHBOARD_HOST = getattr(config, 'DASHBOARD_HOST', '127.0.0.1')
    DASHBOARD_PORT = getattr(config, 'DASHBOARD_PORT', 5000)
except (ImportError, AttributeError):
    # Fallback defaults if config not available
    DASHBOARD_HOST = '127.0.0.1'
    DASHBOARD_PORT = 5000

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
        logging.info(f"[DASHBOARD] Starting web dashboard on {DASHBOARD_HOST}:{DASHBOARD_PORT}...")
        # Pass None to use config values from config_dashboard.py
        start_dashboard(host=None, port=None, debug=False)
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
    
    print(f"\nWeb Dashboard: http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
    print("Config Monitor: Active")
    print("Auto-reload: Enabled")
    print("\n" + "=" * 60)
    
    try:
        # Import and run the main strategy
        import importlib.util
        
        # Get the correct path to the strategy file
        # Strategy file is at: PythonProgram\Strangle10Points\src\Straddle10PointswithSL-Limit.py
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        strategy_file = os.path.join(script_dir, 'src', 'Straddle10PointswithSL-Limit.py')
        
        # Fallback to absolute path if relative doesn't work
        if not os.path.exists(strategy_file):
            abs_path = r'C:\Users\SharmaS8\OneDrive - Unisys\Shivam Imp Documents-2024 June\PythonProgram\Strangle10Points\src\Straddle10PointswithSL-Limit.py'
            if os.path.exists(abs_path):
                strategy_file = abs_path
            else:
                # Last fallback: check old location
                old_path = os.path.join(script_dir, 'Straddle10PointswithSL-Limit.py')
                if os.path.exists(old_path):
                    strategy_file = old_path
        
        if not os.path.exists(strategy_file):
            logging.error(f"[STARTUP] Strategy file not found. Checked:")
            logging.error(f"  1. {os.path.join(script_dir, 'src', 'Straddle10PointswithSL-Limit.py')}")
            logging.error(f"  2. {abs_path if 'abs_path' in locals() else 'N/A'}")
            logging.error(f"  3. {os.path.join(script_dir, 'Straddle10PointswithSL-Limit.py')}")
            logging.error("[STARTUP] Please ensure the strategy file exists at one of these locations.")
            return
        
        logging.info(f"[STARTUP] Loading strategy from: {strategy_file}")
        spec = importlib.util.spec_from_file_location("strategy", strategy_file)
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
