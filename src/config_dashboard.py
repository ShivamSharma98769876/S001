"""
Web Dashboard for Real-time Config Parameter Management
Provides web interface for monitoring and updating trading parameters
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
import sys
import subprocess
from datetime import datetime, timedelta
import threading
import time
import logging

# Add parent directory to path for config imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(parent_dir)
sys.path.append(current_dir)

# Import config monitor
from config_monitor import get_config_monitor

# Import dashboard configuration
try:
    # Try importing from src.config first (since config.py is in src/)
    try:
        from src import config
    except ImportError:
        # Fallback to direct import if src is not in path
        import config
    
    DASHBOARD_HOST = getattr(config, 'DASHBOARD_HOST', '0.0.0.0')
    DASHBOARD_PORT = getattr(config, 'DASHBOARD_PORT', 8080)
    LOT_SIZE = getattr(config, 'LOT_SIZE', 75)  # Get lot size from config
    
    # Check for Azure environment - Azure provides port via HTTP_PLATFORM_PORT
    if os.getenv('HTTP_PLATFORM_PORT'):
        DASHBOARD_PORT = int(os.getenv('HTTP_PLATFORM_PORT'))
        print(f"[CONFIG] Azure environment detected - using port from HTTP_PLATFORM_PORT: {DASHBOARD_PORT}")
    elif os.getenv('PORT'):  # Alternative Azure port variable
        DASHBOARD_PORT = int(os.getenv('PORT'))
        print(f"[CONFIG] Azure environment detected - using port from PORT: {DASHBOARD_PORT}")
    
    print(f"[CONFIG] Loaded dashboard config: host={DASHBOARD_HOST}, port={DASHBOARD_PORT}")
except (ImportError, AttributeError) as e:
    # Fallback defaults if config not available
    DASHBOARD_HOST = '0.0.0.0'
    # Check for Azure port
    if os.getenv('HTTP_PLATFORM_PORT'):
        DASHBOARD_PORT = int(os.getenv('HTTP_PLATFORM_PORT'))
    elif os.getenv('PORT'):
        DASHBOARD_PORT = int(os.getenv('PORT'))
    else:
        DASHBOARD_PORT = 8080
    print(f"[CONFIG] Using default config (import error: {e}): host={DASHBOARD_HOST}, port={DASHBOARD_PORT}")

app = Flask(__name__)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('dashboard.log', encoding='utf-8')  # File output
    ]
)
logger = logging.getLogger(__name__)
logger.info("[DASHBOARD] Dashboard application initialized")

# Global config monitor reference
config_monitor = None

# Global strategy thread reference
strategy_thread = None
strategy_bot = None
strategy_process = None
strategy_running = False

# Global Kite client for authentication (can be used independently)
kite_client_global = None
kite_api_key = None
kite_api_secret = None
account_holder_name = None  # Store account holder name from profile
strategy_account_name = None  # Store account name used when starting strategy (for log retrieval)

# Token persistence file path
TOKEN_STORAGE_FILE = os.path.join(current_dir, 'kite_tokens.json')

# Global trading credentials (for main trading script)
trading_credentials = {
    'account': None,
    'api_key': None,
    'api_secret': None,
    'request_token': None,
    'set': False
}

def set_config_monitor(monitor):
    """Set the global config monitor reference"""
    global config_monitor
    config_monitor = monitor

# Token Persistence Functions
def save_access_token(api_key, access_token, account_name=None):
    """Save access token to file for persistence"""
    try:
        tokens = {}
        if os.path.exists(TOKEN_STORAGE_FILE):
            try:
                with open(TOKEN_STORAGE_FILE, 'r') as f:
                    tokens = json.load(f)
            except (json.JSONDecodeError, IOError):
                tokens = {}
        
        tokens[api_key] = {
            'access_token': access_token,
            'account_name': account_name,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(TOKEN_STORAGE_FILE, 'w') as f:
            json.dump(tokens, f, indent=2)
        
        logging.info(f"[TOKEN] Saved access token for API key: {api_key[:8]}...")
        return True
    except Exception as e:
        logging.error(f"[TOKEN] Error saving token: {e}")
        return False

def load_access_token(api_key):
    """Load access token from file"""
    try:
        if os.path.exists(TOKEN_STORAGE_FILE):
            with open(TOKEN_STORAGE_FILE, 'r') as f:
                tokens = json.load(f)
                if api_key in tokens:
                    token_data = tokens[api_key]
                    logging.info(f"[TOKEN] Loaded access token for API key: {api_key[:8]}...")
                    return token_data.get('access_token'), token_data.get('account_name')
    except Exception as e:
        logging.error(f"[TOKEN] Error loading token: {e}")
    return None, None

def validate_kite_connection(kite_client, retry_count=2):
    """Validate Kite connection with retry logic"""
    if not kite_client or not hasattr(kite_client, 'kite'):
        return False, "Kite client not initialized"
    
    for attempt in range(retry_count + 1):
        try:
            profile = kite_client.kite.profile()
            return True, profile
        except Exception as e:
            error_msg = str(e).lower()
            if attempt < retry_count:
                logging.warning(f"[CONNECTION] Validation attempt {attempt + 1} failed: {e}, retrying...")
                time.sleep(0.5)  # Brief delay before retry
            else:
                if "invalid" in error_msg or "expired" in error_msg or "token" in error_msg:
                    return False, "Token expired or invalid"
                elif "network" in error_msg or "timeout" in error_msg or "connection" in error_msg:
                    return False, "Network error"
                else:
                    return False, f"Connection error: {str(e)[:100]}"
    
    return False, "Connection validation failed"

def reconnect_kite_client():
    """Attempt to reconnect using saved token"""
    global kite_client_global, kite_api_key, kite_api_secret, account_holder_name
    
    if not kite_api_key:
        logging.warning("[RECONNECT] No API key available for reconnection")
        return False
    
    access_token, saved_account_name = load_access_token(kite_api_key)
    if not access_token:
        logging.warning("[RECONNECT] No saved token found")
        return False
    
    try:
        try:
            from src.kite_client import KiteClient
        except ImportError:
            from kite_client import KiteClient
        
        kite_client_global = KiteClient(
            kite_api_key,
            kite_api_secret or '',
            access_token=access_token,
            account='DASHBOARD'
        )
        
        # Validate connection
        is_valid, result = validate_kite_connection(kite_client_global)
        if is_valid:
            profile = result
            account_holder_name = profile.get('user_name') or profile.get('user_id') or saved_account_name or 'Trading Account'
            kite_client_global.account = account_holder_name
            logging.info(f"[RECONNECT] Successfully reconnected. Account: {account_holder_name}")
            return True
        else:
            logging.warning(f"[RECONNECT] Reconnection failed: {result}")
            kite_client_global = None
            return False
    except Exception as e:
        logging.error(f"[RECONNECT] Error during reconnection: {e}")
        kite_client_global = None
        return False

@app.route('/')
def dashboard():
    """Main dashboard page - Zero Touch Strangle landing page"""
    import os
    from environment import is_azure_environment
    
    # Always show the landing page first
    # Get API key for authentication link (if available)
    api_key = None
    try:
        global kite_api_key
        if kite_api_key:
            api_key = kite_api_key
        else:
            # Try to get from environment or config
            api_key = os.getenv('KITE_API_KEY')
    except:
        pass
    
    # Get account holder name if authenticated
    global account_holder_name
    account_name_display = account_holder_name if account_holder_name else None
    
    # Pass account name to template
    return render_template('config_dashboard.html', 
                         api_key=api_key, 
                         is_azure=is_azure_environment(),
                         account_holder_name=account_name_display)

@app.route('/credentials')
def credentials_input():
    """Credentials input page for Azure"""
    return render_template('credentials_input.html')

@app.route('/api/config/current')
def get_current_config():
    """Get current configuration values"""
    try:
        monitor = get_config_monitor()
        if monitor:
            current_config = monitor.get_current_config()
            return jsonify({
                'status': 'success',
                'config': current_config,
                'timestamp': datetime.now().isoformat()
            })
        else:
            # Fallback: try to get config directly
            try:
                import config
                config_dict = {
                    'VIX_HEDGE_POINTS_CANDR': getattr(config, 'VIX_HEDGE_POINTS_CANDR', 8),
                    'HEDGE_TRIGGER_POINTS_STRANGLE': getattr(config, 'HEDGE_TRIGGER_POINTS_STRANGLE', 12),
                    'TARGET_DELTA_LOW': getattr(config, 'TARGET_DELTA_LOW', 0.29),
                    'TARGET_DELTA_HIGH': getattr(config, 'TARGET_DELTA_HIGH', 0.36),
                    'MAX_STOP_LOSS_TRIGGER': getattr(config, 'MAX_STOP_LOSS_TRIGGER', 6),
                    'VIX_DELTA_LOW': getattr(config, 'VIX_DELTA_LOW', 0.30),
                    'VIX_DELTA_HIGH': getattr(config, 'VIX_DELTA_HIGH', 0.40),
                    'VIX_DELTA_THRESHOLD': getattr(config, 'VIX_DELTA_THRESHOLD', 13),
                    'VIX_HEDGE_POINTS_CANDR': getattr(config, 'VIX_HEDGE_POINTS_CANDR', 16),
                    'DELTA_MONITORING_THRESHOLD': getattr(config, 'DELTA_MONITORING_THRESHOLD', 0.225),
                    'DELTA_MIN': getattr(config, 'DELTA_MIN', 0.29),
                    'DELTA_MAX': getattr(config, 'DELTA_MAX', 0.36),
                    'HEDGE_TRIGGER_POINTS': getattr(config, 'HEDGE_TRIGGER_POINTS', 16),
                    'HEDGE_TRIGGER_POINTS_STRANGLE': getattr(config, 'HEDGE_TRIGGER_POINTS_STRANGLE', 16),
                    'HEDGE_POINTS_DIFFERENCE': getattr(config, 'HEDGE_POINTS_DIFFERENCE', 100),
                    'VWAP_MINUTES': getattr(config, 'VWAP_MINUTES', 5),
                    'VWAP_MAX_PRICE_DIFF_PERCENT': getattr(config, 'VWAP_MAX_PRICE_DIFF_PERCENT', 15),
                    'VWAP_MIN_CANDLES': getattr(config, 'VWAP_MIN_CANDLES', 150),
                    'INITIAL_PROFIT_BOOKING': getattr(config, 'INITIAL_PROFIT_BOOKING', 32),
                    'SECOND_PROFIT_BOOKING': getattr(config, 'SECOND_PROFIT_BOOKING', 40),
                    'MAX_PRICE_DIFFERENCE_PERCENTAGE': getattr(config, 'MAX_PRICE_DIFFERENCE_PERCENTAGE', 1.5),
                    'STOP_LOSS_CONFIG': getattr(config, 'STOP_LOSS_CONFIG', {
                        'Tuesday': 30,
                        'Wednesday': 30,
                        'Thursday': 30,
                        'Friday': 30,
                        'Monday': 30,
                        'default': 30
                    })
                }
                return jsonify({
                    'status': 'success',
                    'config': config_dict,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Config monitor not initialized and fallback failed: {str(e)}'
                }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/config/lot-size', methods=['GET'])
def get_lot_size():
    """Get lot size from config"""
    try:
        return jsonify({
            'success': True,
            'lot_size': LOT_SIZE
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'lot_size': 75  # Fallback default
        }), 500

@app.route('/api/config/history')
def get_config_history():
    """Get configuration change history"""
    try:
        monitor = get_config_monitor()
        if monitor:
            history = monitor.get_config_history()
            return jsonify({
                'status': 'success',
                'history': history,
                'count': len(history)
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Config monitor not initialized'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/config/update', methods=['POST'])
def update_config():
    """Update configuration parameter"""
    try:
        data = request.get_json()
        param_name = data.get('parameter')
        new_value = data.get('value')
        
        if not param_name or new_value is None:
            return jsonify({
                'status': 'error',
                'message': 'Parameter name and value required'
            }), 400
            
        # Validate parameter
        monitor = get_config_monitor()
        if monitor:
            print(f"[DEBUG] Validating {param_name} = '{new_value}' (type: {type(new_value)})")
            if not monitor.validate_parameter(param_name, new_value):
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid value for parameter {param_name}. Please check the value range and type.'
                }), 400
        else:
            # If no monitor available, do basic validation
            print(f"[DEBUG] No config monitor available, doing basic validation for {param_name} = '{new_value}'")
            try:
                # Basic type conversion and range check
                if isinstance(new_value, str):
                    if '.' in new_value:
                        new_value = float(new_value)
                    else:
                        new_value = int(new_value)
                
                # Basic range validation for known parameters
                if param_name == 'HEDGE_TRIGGER_POINTS_STRANGLE':
                    if not (isinstance(new_value, (int, float)) and 0 < new_value <= 100):
                        return jsonify({
                            'status': 'error',
                            'message': f'Invalid value for parameter {param_name}. Must be between 0 and 100.'
                        }), 400
            except (ValueError, TypeError):
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid value for parameter {param_name}. Please enter a valid number.'
                }), 400
            
        # Convert value to appropriate type if needed
        if isinstance(new_value, dict):
            # Already a dict, use as is
            pass
        elif isinstance(new_value, str):
            # Try to convert to number if possible
            try:
                if '.' in new_value:
                    new_value = float(new_value)
                else:
                    new_value = int(new_value)
            except ValueError:
                # Keep as string
                pass
        
        # Update config file
        success = update_config_file(param_name, new_value)
        
        if success:
            # Trigger config reload if monitor is available
            monitor = get_config_monitor()
            if monitor:
                try:
                    monitor.reload_config()
                except Exception as reload_error:
                    print(f"Warning: Config reload failed: {reload_error}")
            
            return jsonify({
                'status': 'success',
                'message': f'Updated {param_name} to {new_value}',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to update parameter {param_name}. Check if the parameter exists in config.py'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/config/export')
def export_config():
    """Export configuration history"""
    try:
        monitor = get_config_monitor()
        if monitor:
            filename = f'config_history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            monitor.export_config_history(filename)
            return jsonify({
                'status': 'success',
                'message': f'Exported to {filename}',
                'filename': filename
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Config monitor not initialized'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/trading/positions')
def get_trading_positions():
    """Get current trading positions and P&L"""
    try:
        # Try to get positions from the main strategy
        import sys
        main_module = sys.modules.get('__main__')
        
        positions = []
        total_pnl = 0
        
        # Check if we have access to kite object and positions
        if hasattr(main_module, 'kite') and main_module.kite:
            try:
                # Get positions from Kite API
                kite_positions = main_module.kite.positions()
                
                if kite_positions and 'net' in kite_positions:
                    for position in kite_positions['net']:
                        if position['quantity'] != 0:  # Only show active positions
                            pnl = position.get('pnl', 0)
                            total_pnl += pnl
                            
                            positions.append({
                                'instrument': position.get('tradingsymbol', 'N/A'),
                                'product': position.get('product', 'NRML'),
                                'quantity': position.get('quantity', 0),
                                'average_price': position.get('average_price', 0),
                                'last_price': position.get('last_price', 0),
                                'pnl': pnl,
                                'pnl_percentage': position.get('pnl_percentage', 0),
                                'day_change': position.get('day_change', 0),
                                'day_change_percentage': position.get('day_change_percentage', 0)
                            })
            except Exception as e:
                # Fallback: return mock data for demo
                positions = [
                    {
                        'instrument': 'NIFTY 4th NOV 25900 PE NFO',
                        'product': 'NRML',
                        'quantity': 150,
                        'average_price': 104.25,
                        'last_price': 98.35,
                        'pnl': -885.00,
                        'pnl_percentage': -5.66,
                        'day_change': -5.90,
                        'day_change_percentage': -5.66
                    },
                    {
                        'instrument': 'NIFTY 4th NOV 26400 CE NFO',
                        'product': 'NRML',
                        'quantity': 150,
                        'average_price': 97.95,
                        'last_price': 98.25,
                        'pnl': 45.00,
                        'pnl_percentage': 0.31,
                        'day_change': 0.30,
                        'day_change_percentage': 0.31
                    }
                ]
                total_pnl = -840.00
        
        return jsonify({
            'status': 'success',
            'positions': positions,
            'total_pnl': total_pnl,
            'position_count': len(positions),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/trading/set-credentials', methods=['POST'])
def set_trading_credentials():
    """Set credentials for the main trading script (used on Azure)"""
    try:
        global trading_credentials
        
        data = request.get_json()
        
        account = data.get('account', '').strip()
        api_key = data.get('api_key', '').strip()
        api_secret = data.get('api_secret', '').strip()
        request_token = data.get('request_token', '').strip()
        
        if not all([account, api_key, api_secret, request_token]):
            return jsonify({
                'success': False,
                'error': 'All fields are required: account, api_key, api_secret, request_token'
            }), 400
        
        # Store credentials
        trading_credentials = {
            'account': account,
            'api_key': api_key,
            'api_secret': api_secret,
            'request_token': request_token,
            'set': True
        }
        
        logging.info(f"[CREDENTIALS] Credentials set for account: {account}")
        
        return jsonify({
            'success': True,
            'message': 'Credentials set successfully'
        })
    except Exception as e:
        logging.error(f"[CREDENTIALS] Error setting credentials: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trading/credentials-status', methods=['GET'])
def get_credentials_status():
    """Check if credentials are set"""
    global trading_credentials
    return jsonify({
        'credentials_set': trading_credentials['set'],
        'account': trading_credentials['account'] if trading_credentials['set'] else None
    })

@app.route('/api/trading/get-credentials', methods=['GET'])
def get_trading_credentials():
    """Get credentials for the main trading script (internal use)"""
    global trading_credentials
    if trading_credentials['set']:
        return jsonify({
            'success': True,
            'credentials': {
                'account': trading_credentials['account'],
                'api_key': trading_credentials['api_key'],
                'api_secret': trading_credentials['api_secret'],
                'request_token': trading_credentials['request_token']
            }
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Credentials not set'
        }), 404

@app.route('/api/trading/status')
def get_trading_status():
    """Get current trading status"""
    try:
        import sys
        main_module = sys.modules.get('__main__')
        
        status = {
            'is_trading_active': False,
            'current_time': datetime.now().strftime('%H:%M:%S'),
            'market_status': 'Unknown',
            'active_trades': 0,
            'total_pnl': 0
        }
        
        # Check if trading is active
        if hasattr(main_module, 'kite') and main_module.kite:
            try:
                # Get market status
                market_status = main_module.kite.instruments('NSE')
                if market_status:
                    status['market_status'] = 'Open'
                    status['is_trading_active'] = True
            except:
                status['market_status'] = 'Closed'
        
        return jsonify({
            'status': 'success',
            'data': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# New Dashboard API Endpoints
@app.route('/api/dashboard/metrics')
def get_dashboard_metrics():
    """Get Total Day P&L for trades with tag='S0001'"""
    try:
        global strategy_bot, kite_client_global
        
        total_day_pnl = 0.0
        
        # Try to get orders with tag="S0001" and calculate P&L
        kite_client = None
        if strategy_bot and hasattr(strategy_bot, 'kite_client'):
            kite_client = strategy_bot.kite_client
        elif kite_client_global:
            kite_client = kite_client_global
        
        if kite_client and hasattr(kite_client, 'kite'):
            try:
                # Get all orders
                orders = kite_client.kite.orders()
                
                # Filter orders by tag="S0001" and get today's date
                today = datetime.now().date()
                s0001_tradingsymbols = set()
                
                for order in orders:
                    if order.get('tag') == 'S0001':
                        # Check if order is from today
                        order_timestamp = order.get('order_timestamp', '')
                        if order_timestamp:
                            try:
                                order_date = datetime.strptime(order_timestamp, '%Y-%m-%d %H:%M:%S').date()
                                if order_date == today:
                                    tradingsymbol = order.get('tradingsymbol', '')
                                    exchange = order.get('exchange', 'NFO')
                                    if tradingsymbol:
                                        s0001_tradingsymbols.add((exchange, tradingsymbol))
                            except:
                                pass
                
                # Get positions and match with S0001 orders
                try:
                    positions = kite_client.kite.positions()
                    if positions and 'net' in positions:
                        for pos in positions['net']:
                            if pos.get('quantity', 0) != 0:
                                tradingsymbol = pos.get('tradingsymbol', '')
                                exchange = pos.get('exchange', 'NFO')
                                
                                # Check if this position matches any S0001 order
                                if (exchange, tradingsymbol) in s0001_tradingsymbols:
                                    total_day_pnl += pos.get('pnl', 0)
                except Exception as e:
                    print(f"Error checking positions: {e}")
                    
            except Exception as e:
                print(f"Error calculating Total Day P&L: {e}")
        
        return jsonify({
            'status': 'success',
            'totalDayPnl': round(total_day_pnl, 2)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'totalDayPnl': 0.0
        }), 500

@app.route('/api/dashboard/positions')
def get_dashboard_positions():
    """Get all positions (active and inactive) for dashboard"""
    try:
        global strategy_bot, kite_client_global
        
        positions = []
        total_pnl = 0.0
        
        kite_client = None
        if strategy_bot and hasattr(strategy_bot, 'kite_client'):
            kite_client = strategy_bot.kite_client
        elif kite_client_global:
            kite_client = kite_client_global
        
        if kite_client and hasattr(kite_client, 'kite'):
            try:
                kite_positions = kite_client.kite.positions()
                if kite_positions and 'net' in kite_positions:
                    # Get all positions including inactive ones (quantity = 0)
                    for pos in kite_positions['net']:
                        # Include all positions, even with quantity 0 (inactive)
                        pnl = pos.get('pnl', 0)
                        total_pnl += pnl
                        
                        positions.append({
                            'symbol': pos.get('tradingsymbol', 'N/A'),
                            'exchange': pos.get('exchange', 'NFO'),
                            'product': pos.get('product', 'NRML'),
                            'entryPrice': pos.get('average_price', 0),
                            'currentPrice': pos.get('last_price', 0),
                            'quantity': pos.get('quantity', 0),
                            'pnl': pnl,
                            'pnlPercentage': pos.get('pnl_percentage', 0),
                            'dayChange': pos.get('day_change', 0),
                            'dayChangePercentage': pos.get('day_change_percentage', 0),
                            'isActive': pos.get('quantity', 0) != 0
                        })
            except Exception as e:
                print(f"Error fetching positions: {e}")
        
        return jsonify({
            'status': 'success',
            'positions': positions,
            'totalPnl': round(total_pnl, 2)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/dashboard/trade-history')
def get_trade_history():
    """Get trade history"""
    try:
        date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        show_all = request.args.get('showAll', 'false').lower() == 'true'
        
        # Try to load from P&L data files
        trades = []
        summary = {
            'totalTrades': 0,
            'totalProfit': 0.0,
            'totalLoss': 0.0,
            'netPnl': 0.0,
            'winRate': 0.0
        }
        
        try:
            pnl_data_path = os.path.join('src', 'pnl_data', 'daily_pnl.json')
            if os.path.exists(pnl_data_path):
                with open(pnl_data_path, 'r') as f:
                    pnl_data = json.load(f)
                    
                # Filter by date if needed
                for trade in pnl_data.get('trades', []):
                    trade_date = trade.get('date', '')
                    if show_all or trade_date == date_filter:
                        trades.append({
                            'symbol': trade.get('symbol', 'N/A'),
                            'entryTime': trade.get('entry_time', ''),
                            'exitTime': trade.get('exit_time', ''),
                            'entryPrice': trade.get('entry_price', 0),
                            'exitPrice': trade.get('exit_price', 0),
                            'quantity': trade.get('quantity', 0),
                            'pnl': trade.get('pnl', 0),
                            'type': trade.get('type', 'SELL')
                        })
                        
                        # Update summary
                        summary['totalTrades'] += 1
                        if trade.get('pnl', 0) >= 0:
                            summary['totalProfit'] += trade.get('pnl', 0)
                        else:
                            summary['totalLoss'] += abs(trade.get('pnl', 0))
                        summary['netPnl'] += trade.get('pnl', 0)
                
                # Calculate win rate
                if summary['totalTrades'] > 0:
                    winning_trades = sum(1 for t in trades if t['pnl'] >= 0)
                    summary['winRate'] = (winning_trades / summary['totalTrades']) * 100
        except Exception as e:
            print(f"Error loading trade history: {e}")
        
        return jsonify({
            'status': 'success',
            'trades': trades,
            'summary': summary
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/dashboard/pnl-chart')
def get_pnl_chart_data():
    """Get P&L chart data"""
    try:
        # Generate sample time labels (last 30 data points)
        labels = []
        current_pnl = []
        protected_profit = []
        total_pnl = []
        
        # Generate sample data (in real implementation, fetch from actual P&L records)
        import random
        base_time = datetime.now()
        for i in range(30):
            time_label = (base_time.replace(second=0, microsecond=0) - 
                         timedelta(minutes=30-i)).strftime('%H:%M:%S')
            labels.append(time_label)
            
            # Sample data - replace with actual data
            current_pnl.append(random.uniform(-100, 100))
            protected_profit.append(random.uniform(0, 200))
            total_pnl.append(random.uniform(-50, 150))
        
        return jsonify({
            'status': 'success',
            'labels': labels,
            'currentPnl': current_pnl,
            'protectedProfit': protected_profit,
            'totalPnl': total_pnl
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/strategy/start', methods=['POST'])
def start_strategy():
    """Start the trading strategy"""
    try:
        global strategy_thread, strategy_bot, strategy_running
        
        if strategy_running:
            return jsonify({
                'status': 'error',
                'message': 'Strategy is already running'
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['apiKey', 'apiSecret', 'requestToken', 'account', 'callQuantity', 'putQuantity']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Store API credentials globally for authentication
        global kite_api_key, kite_api_secret, kite_client_global
        kite_api_key = data['apiKey']
        kite_api_secret = data['apiSecret']
        
        # Import TradingBot
        from src.trading_bot import TradingBot
        
        # Create bot instance
        strategy_bot = TradingBot(
            data['apiKey'],
            data['apiSecret'],
            data['requestToken'],
            data['account'],
            data['callQuantity'],
            data['putQuantity']
        )
        
        # Also create global kite client for authentication
        try:
            from src.kite_client import KiteClient
            kite_client_global = strategy_bot.kite_client
        except:
            pass
        
        # Start bot in separate thread
        def run_bot():
            global strategy_running
            try:
                strategy_running = True
                strategy_bot.run()
            except Exception as e:
                print(f"Strategy error: {e}")
            finally:
                strategy_running = False
        
        strategy_thread = threading.Thread(target=run_bot, daemon=True)
        strategy_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': 'Strategy started successfully'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/live/', methods=['GET'], strict_slashes=False)
def live_trader_page():
    """Live Trader dedicated page"""
    try:
        # Get account holder name if authenticated
        global account_holder_name
        account_name_display = account_holder_name if account_holder_name else None
        
        return render_template('live_trader.html', account_holder_name=account_name_display)
    except Exception as e:
        logging.error(f"[LIVE TRADER] Error loading page: {e}")
        return f"Error loading Live Trader page: {str(e)}", 500

@app.route('/api/live-trader/logs', methods=['GET'])
def get_live_trader_logs():
    """Get Live Trader logs"""
    try:
        global strategy_process
        
        logs = []
        
        # Import environment functions at the start
        from datetime import date
        from environment import format_date_for_filename, is_azure_environment, sanitize_account_name_for_filename
        
        # Try to read from log file if strategy is running
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        src_dir = os.path.join(script_dir, 'src')  # Log files are in src directory
        src_logs_dir = os.path.join(src_dir, 'logs')  # Log files are in src/logs directory (local)
        
        # Look for today's log file
        today = date.today().strftime('%Y-%m-%d')  # For backward compatibility searches
        today_formatted = format_date_for_filename(date.today())  # New format: YYYYMONDD
        
        # Try to find log files
        log_files = []
        
        # Get account name - CRITICAL: Use strategy_account_name first (account used when starting strategy)
        # This ensures we match the log file that was actually created
        global account_holder_name, strategy_account_name
        account = None
        
        # Priority 1: Use account name from strategy start (most accurate for log matching)
        if strategy_account_name:
            account = strategy_account_name
            logging.info(f"[LOGS] Using strategy account name for log matching: {account}")
        # Priority 2: Use account holder name from profile
        elif account_holder_name:
            account = account_holder_name
            logging.info(f"[LOGS] Using account holder name for log matching: {account}")
        # Priority 3: Use account from kite client
        elif kite_client_global and hasattr(kite_client_global, 'account'):
            account = kite_client_global.account or 'TRADING_ACCOUNT'
            logging.info(f"[LOGS] Using kite client account for log matching: {account}")
        else:
            account = 'TRADING_ACCOUNT'
            logging.info(f"[LOGS] Using default account name for log matching: {account}")
        
        # Simplify: Only look for today's log file in format: {account}_{YYYYMONDD}.log
        # Get sanitized account name (first name only)
        if not account:
            logging.warning(f"[LOGS] No account name available, cannot find log file")
        else:
            sanitized_account = sanitize_account_name_for_filename(account)
            log_filename = f'{sanitized_account}_{today_formatted}.log'
            logging.info(f"[LOGS] Looking for today's log file: '{log_filename}' for account: '{account}' (sanitized: '{sanitized_account}')")
            
            # LOCAL ENVIRONMENT: Check src/logs directory
            if not is_azure_environment():
                # Ensure directory exists
                if not os.path.exists(src_logs_dir):
                    try:
                        os.makedirs(src_logs_dir, exist_ok=True)
                        logging.info(f"[LOGS] Created src/logs directory: {src_logs_dir}")
                    except Exception as e:
                        logging.warning(f"[LOGS] Could not create src/logs directory: {e}")
                
                # Look for today's log file in src/logs
                today_log_path = os.path.join(src_logs_dir, log_filename)
                if os.path.exists(today_log_path):
                    log_files.append(today_log_path)
                    logging.info(f"[LOGS] ✓ Found today's log file: {today_log_path}")
                else:
                    logging.info(f"[LOGS] Today's log file does not exist: {today_log_path}")
            
            # AZURE ENVIRONMENT: Check /tmp/{account}/logs/ directory
            else:
                from environment import get_log_directory
                if account:
                    sanitized_account = sanitize_account_name_for_filename(account)
                    azure_log_dir = os.path.join('/tmp', sanitized_account, 'logs')
                else:
                    azure_log_dir = '/tmp/logs'
                
                # Ensure directory exists
                os.makedirs(azure_log_dir, exist_ok=True)
                logging.info(f"[LOGS] Azure environment - checking log directory: {azure_log_dir}")
                
                # Look for today's log file
                today_log_path = os.path.join(azure_log_dir, log_filename)
                if os.path.exists(today_log_path):
                    log_files.append(today_log_path)
                    logging.info(f"[LOGS] ✓ Found today's log file: {today_log_path}")
                else:
                    logging.info(f"[LOGS] Today's log file does not exist: {today_log_path}")
                    # List files in directory for debugging
                    try:
                        if os.path.exists(azure_log_dir):
                            all_files = os.listdir(azure_log_dir)
                            logging.info(f"[LOGS] Files in Azure log directory: {all_files}")
                    except Exception as e:
                        logging.warning(f"[LOGS] Could not list Azure log directory: {e}")
        
        if not log_files:
            logging.warning(f"[LOGS] No log files found for account: {account}, date: {today}")
            # Log checked directories based on environment
            if is_azure_environment():
                # For error message, try to get account-specific directory
                from environment import sanitize_account_name_for_filename
                if account:
                    sanitized_account = sanitize_account_name_for_filename(account)
                    checked_dirs = f"Azure log directory: /tmp/{sanitized_account}/logs/"
                else:
                    checked_dirs = f"Azure log directory: /tmp/logs/"
            else:
                checked_dirs = f"src_logs_dir={src_logs_dir}, src_dir={src_dir}, root={script_dir}, root_logs={log_dir}"
            logging.warning(f"[LOGS] Checked directories: {checked_dirs}")
            
            # List existing files for debugging
            if is_azure_environment():
                # Use account-specific directory: /tmp/{account_name}/logs/
                if account:
                    sanitized_account = sanitize_account_name_for_filename(account)
                    azure_log_dir = os.path.join('/tmp', sanitized_account, 'logs')
                else:
                    azure_log_dir = '/tmp/logs'
                # Ensure directory exists (create if it doesn't)
                os.makedirs(azure_log_dir, exist_ok=True)
                try:
                    existing_files = os.listdir(azure_log_dir)
                    logging.info(f"[LOGS] Files in Azure log directory ({azure_log_dir}): {existing_files}")
                except Exception as e:
                    logging.warning(f"[LOGS] Could not list Azure log directory: {e}")
            else:
                if os.path.exists(src_logs_dir):
                    try:
                        existing_files = os.listdir(src_logs_dir)
                        logging.info(f"[LOGS] Files in src/logs: {existing_files}")
                    except:
                        pass
            
            env_msg = "Azure log directory" if is_azure_environment() else "src/logs, src, root"
            return jsonify({
                'success': True,
                'logs': [],
                'log_file_path': None,
                'message': f'No log files found for account: {account}, date: {today}. Checked: {env_msg}. Logs will appear once the strategy starts.'
            })
        
        # Read last 500 lines from log files (increased to show more logs)
        # Prioritize: read from first file (most relevant) first, then others
        all_lines = []
        log_files_read = []
        for log_path in log_files:
            try:
                logging.info(f"[LOGS] Attempting to read log file: {log_path}")
                if not os.path.exists(log_path):
                    logging.warning(f"[LOGS] Log file does not exist: {log_path}")
                    continue
                    
                # Check file size
                file_size = os.path.getsize(log_path)
                logging.info(f"[LOGS] Log file size: {file_size} bytes")
                
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    # Get last 500 lines from each file to show more detailed logs
                    file_lines = lines[-500:] if len(lines) > 500 else lines
                    all_lines.extend(file_lines)
                    log_files_read.append(log_path)
                    logging.info(f"[LOGS] Successfully read {len(file_lines)} lines from {log_path} (total lines in file: {len(lines)})")
            except PermissionError as e:
                logging.error(f"[LOGS] Permission denied reading log file {log_path}: {e}")
            except Exception as e:
                logging.error(f"[LOGS] Error reading log file {log_path}: {e}")
                import traceback
                logging.error(f"[LOGS] Traceback: {traceback.format_exc()}")
                pass
        
        if log_files_read:
            logging.info(f"[LOGS] Successfully read from {len(log_files_read)} log file(s): {log_files_read}")
        else:
            logging.warning(f"[LOGS] No log files were successfully read from {len(log_files)} attempted file(s)")
        
        # Show ALL logs (remove filtering to display complete log details)
        # Sort by timestamp if available, otherwise keep order
        for line in all_lines[-500:]:  # Show last 500 lines
            line = line.strip()
            if line:  # Only add non-empty lines
                logs.append(line)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_logs = []
        for log in logs:
            if log not in seen:
                seen.add(log)
                unique_logs.append(log)
        
        # Include log file path and any error messages in response
        response_data = {
            'success': True,
            'logs': unique_logs[-500:],  # Last 500 entries
            'log_file_path': log_files[0] if log_files else None,  # Return log file path for reference
            'log_files_found': len(log_files),
            'log_files_read': len(log_files_read),
            'log_files': log_files_read if log_files_read else log_files[:5]  # Show up to 5 file paths
        }
        
        # Add log file path and debug info to logs for visibility
        if log_files and log_files[0]:
            log_path_msg = f"[LOG SETUP] Log file path: {log_files[0]}"
            # Check if already in logs to avoid duplicates
            if not any(log_path_msg in log for log in unique_logs):
                unique_logs.insert(0, log_path_msg)
            
            # Add info about log file search
            if response_data.get('log_files_found', 0) > 0:
                search_info = f"[LOG SETUP] Found {response_data['log_files_found']} log file(s), read {response_data['log_files_read']} successfully"
                if search_info not in unique_logs:
                    unique_logs.insert(1, search_info)
        else:
            # No log files found - add helpful message
            no_logs_msg = f"[LOG SETUP] No log files found yet. Logs will appear here once the strategy starts running."
            if no_logs_msg not in unique_logs:
                unique_logs.insert(0, no_logs_msg)
        
        response_data['logs'] = unique_logs[-500:]
        return jsonify(response_data)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logging.error(f"[LOGS] Error in get_live_trader_logs: {e}\n{error_traceback}")
        
        # Return error in logs so it shows up in Live Trading Log section
        error_logs = [
            f"[ERROR] Failed to retrieve logs: {str(e)}",
            f"[ERROR] Traceback: {error_traceback[:500]}"  # Limit traceback length
        ]
        
        return jsonify({
            'success': False,
            'error': str(e),
            'logs': error_logs,  # Include error in logs so it shows on screen
            'log_file_path': None,
            'log_files_found': 0
        }), 500

@app.route('/api/live-trader/status', methods=['GET'])
def live_trader_status():
    """Get Live Trader engine status"""
    try:
        global strategy_process, strategy_running
        
        # Check actual process status
        actual_running = False
        if strategy_process is not None:
            try:
                poll_result = strategy_process.poll()
                if poll_result is None:
                    # Process is still running
                    actual_running = True
                    logging.debug(f"[LIVE TRADER STATUS] Process is running (PID: {strategy_process.pid})")
                else:
                    # Process has terminated
                    logging.info(f"[LIVE TRADER STATUS] Process terminated with return code: {poll_result}")
                    strategy_running = False
                    strategy_process = None
                    actual_running = False
            except Exception as poll_error:
                # Process object might be invalid
                logging.warning(f"[LIVE TRADER STATUS] Error polling process: {poll_error}")
                strategy_running = False
                strategy_process = None
                actual_running = False
        else:
            # No process object, definitely not running
            actual_running = False
            strategy_running = False
        
        # Update strategy_running flag to match actual state
        strategy_running = actual_running
        
        logging.debug(f"[LIVE TRADER STATUS] Returning status - running: {actual_running}, strategy_running: {strategy_running}")
        
        return jsonify({
            'running': actual_running,
            'strategy_running': strategy_running,
            'process_id': strategy_process.pid if (strategy_process and actual_running) else None
        })
    except Exception as e:
        logging.error(f"[LIVE TRADER STATUS] Error: {e}")
        import traceback
        logging.error(f"[LIVE TRADER STATUS] Traceback: {traceback.format_exc()}")
        return jsonify({
            'running': False,
            'strategy_running': False,
            'error': str(e)
        }), 500

@app.route('/api/live-trader/start', methods=['POST'])
def start_live_trader():
    """Start Live Trader by running Straddle10PointswithSL-Limit.py"""
    try:
        global strategy_process, strategy_running, kite_client_global, kite_api_key, kite_api_secret
        
        # Check if process is actually running, not just the flag
        if strategy_running:
            # Verify the process is actually still running
            if strategy_process is not None:
                poll_result = strategy_process.poll()
                if poll_result is None:
                    # Process is still running
                    logging.warning("[LIVE TRADER] Strategy process is still running (PID: {})".format(strategy_process.pid))
                    return jsonify({
                        'success': False,
                        'error': 'Strategy is already running'
                    }), 400
                else:
                    # Process has terminated but flag wasn't reset
                    logging.warning("[LIVE TRADER] Strategy process terminated (return code: {}) but flag was still True. Resetting flag.".format(poll_result))
                    strategy_running = False
                    strategy_process = None
            else:
                # Flag is True but process is None - reset flag
                logging.warning("[LIVE TRADER] Strategy flag is True but process is None. Resetting flag.")
                strategy_running = False
        
        data = request.get_json()
        call_quantity = data.get('callQuantity')
        put_quantity = data.get('putQuantity')
        
        if not call_quantity or not put_quantity:
            return jsonify({
                'success': False,
                'error': 'Call Quantity and Put Quantity are required'
            }), 400
        
        # Convert to integers
        try:
            call_quantity = int(call_quantity)
            put_quantity = int(put_quantity)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Call Quantity and Put Quantity must be valid numbers'
            }), 400
        
        # Validate quantities are multiples of LOT_SIZE (from config)
        if call_quantity % LOT_SIZE != 0:
            return jsonify({
                'success': False,
                'error': f'Call Quantity must be a multiple of {LOT_SIZE}. You entered {call_quantity}. Nearest valid: {(call_quantity // LOT_SIZE) * LOT_SIZE}'
            }), 400
        
        if put_quantity % LOT_SIZE != 0:
            return jsonify({
                'success': False,
                'error': f'Put Quantity must be a multiple of {LOT_SIZE}. You entered {put_quantity}. Nearest valid: {(put_quantity // LOT_SIZE) * LOT_SIZE}'
            }), 400
        
        # Check if authenticated
        if not kite_client_global or not hasattr(kite_client_global, 'kite'):
            return jsonify({
                'success': False,
                'error': 'Not authenticated. Please authenticate first.'
            }), 401
        
        # Get credentials from authenticated client
        api_key = kite_client_global.api_key
        api_secret = kite_client_global.api_secret
        access_token = kite_client_global.access_token
        
        # Get account name from authenticated client (use account_holder_name if available)
        # CRITICAL: Use the account name that was used when starting the strategy for log matching
        global account_holder_name, strategy_account_name
        # Prefer strategy_account_name (account used when starting) for log retrieval
        account = strategy_account_name or account_holder_name or getattr(kite_client_global, 'account', 'TRADING_ACCOUNT') or 'TRADING_ACCOUNT'
        
        # Get the strategy file path
        # Use the correct path: PythonProgram\Strangle10Points\src\Straddle10PointswithSL-Limit.py
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # The file is in src directory (same directory as config_dashboard.py)
        # config_dashboard.py is at: PythonProgram\Strangle10Points\src\config_dashboard.py
        # Strategy file is at: PythonProgram\Strangle10Points\src\Straddle10PointswithSL-Limit.py
        strategy_file = os.path.join(script_dir, 'src', 'Straddle10PointswithSL-Limit.py')
        
        # Verify the file exists
        if not os.path.exists(strategy_file):
            # Try absolute path as fallback
            abs_path = r'C:\Users\SharmaS8\OneDrive - Unisys\Shivam Imp Documents-2024 June\PythonProgram\Strangle10Points\src\Straddle10PointswithSL-Limit.py'
            if os.path.exists(abs_path):
                strategy_file = abs_path
            else:
                # Last fallback: check old location (root directory)
                old_path = os.path.join(script_dir, 'Straddle10PointswithSL-Limit.py')
                if os.path.exists(old_path):
                    strategy_file = old_path
                else:
                    # Log error for debugging
                    print(f"[ERROR] Strategy file not found. Checked:")
                    print(f"  1. {os.path.join(script_dir, 'src', 'Straddle10PointswithSL-Limit.py')}")
                    print(f"  2. {abs_path}")
                    print(f"  3. {old_path}")
        
        if not os.path.exists(strategy_file):
            return jsonify({
                'success': False,
                'error': f'Strategy file not found: {strategy_file}'
            }), 404
        
        # Run the strategy file as subprocess
        # The file expects 6 inputs in order:
        # 1. Account (line 24)
        # 2. Api_key (line 25)
        # 3. Api_Secret (line 26)
        # 4. Request_Token (line 27) - we'll use access_token
        # 5. Call Quantity (line 2504)
        # 6. Put Quantity (line 2505)
        
        # Use a threading event to signal when process is created
        process_ready = threading.Event()
        process_error = [None]  # Use list to allow modification from inner function
        
        def run_strategy():
            global strategy_process, strategy_running
            try:
                strategy_running = True
                
                # Store the account name used for this strategy run (for log retrieval)
                global strategy_account_name
                strategy_account_name = account
                logging.info(f"[LIVE TRADER] Starting strategy with account name: {account} (will be used for log file matching)")
                
                # Prepare input string for stdin (matching the exact order of input() calls)
                inputs = f"{account}\n{api_key}\n{api_secret}\n{access_token}\n{call_quantity}\n{put_quantity}\n"
                
                # Run the strategy file
                # Use the directory containing the strategy file as working directory
                # This ensures relative imports and log file creation work correctly
                strategy_cwd = os.path.dirname(strategy_file) if os.path.exists(strategy_file) else script_dir
                
                # Log the paths for debugging
                logging.info(f"[LIVE TRADER] Strategy file: {strategy_file}")
                logging.info(f"[LIVE TRADER] Working directory: {strategy_cwd}")
                logging.info(f"[LIVE TRADER] File exists: {os.path.exists(strategy_file)}")
                logging.info(f"[LIVE TRADER] Python executable: {sys.executable}")
                
                try:
                    strategy_process = subprocess.Popen(
                        [sys.executable, strategy_file],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        cwd=strategy_cwd,
                        bufsize=1
                    )
                    
                    logging.info(f"[LIVE TRADER] Process created successfully (PID: {strategy_process.pid})")
                    
                    # Send inputs immediately
                    strategy_process.stdin.write(inputs)
                    strategy_process.stdin.flush()
                    strategy_process.stdin.close()
                    
                    # Signal that process is ready
                    process_ready.set()
                    
                    # Don't wait for completion - let it run in background
                    # Monitor the process in background
                    def monitor_process():
                        global strategy_process, strategy_running
                        # Store local reference to avoid race conditions
                        proc = strategy_process
                        if proc is None:
                            return
                        
                        try:
                            # Read output in background
                            for line in proc.stdout:
                                logging.info(f"[STRATEGY] {line.strip()}")
                        except Exception as e:
                            logging.warning(f"[STRATEGY] Monitor error: {e}")
                        finally:
                            # Check if process has terminated
                            try:
                                if proc is not None and proc.poll() is not None:
                                    returncode = proc.returncode
                                    logging.info(f"[STRATEGY] Process terminated with return code: {returncode}")
                                    strategy_running = False
                                    # Only set to None if it's still the same process
                                    if strategy_process == proc:
                                        strategy_process = None
                            except Exception as e:
                                logging.warning(f"[STRATEGY] Error checking process status: {e}")
                                strategy_running = False
                                if strategy_process == proc:
                                    strategy_process = None
                    
                    monitor_thread = threading.Thread(target=monitor_process, daemon=True)
                    monitor_thread.start()
                    
                except Exception as popen_error:
                    error_msg = f"Failed to create subprocess: {popen_error}"
                    logging.error(f"[LIVE TRADER] {error_msg}")
                    import traceback
                    logging.error(f"[LIVE TRADER] Traceback: {traceback.format_exc()}")
                    process_error[0] = error_msg
                    strategy_running = False
                    strategy_process = None
                    process_ready.set()  # Signal even on error so main thread can check
                
            except Exception as e:
                error_msg = f"Error running strategy: {e}"
                logging.error(f"[LIVE TRADER] {error_msg}")
                import traceback
                logging.error(f"[LIVE TRADER] Traceback: {traceback.format_exc()}")
                process_error[0] = error_msg
                strategy_running = False
                if strategy_process:
                    try:
                        strategy_process.terminate()
                    except:
                        pass
                strategy_process = None
                process_ready.set()  # Signal even on error so main thread can check
        
        strategy_thread = threading.Thread(target=run_strategy, daemon=True)
        strategy_thread.start()
        
        # Wait for process to be created (with timeout)
        if process_ready.wait(timeout=3.0):
            # Check if there was an error
            if process_error[0]:
                strategy_running = False
                logging.error(f"[LIVE TRADER] Strategy process creation failed: {process_error[0]}")
                return jsonify({
                    'success': False,
                    'error': f'Failed to start strategy process: {process_error[0]}'
                }), 500
            
            # Check if process started successfully
            if strategy_process is None:
                strategy_running = False
                logging.error("[LIVE TRADER] Strategy process is None after creation")
                return jsonify({
                    'success': False,
                    'error': 'Failed to start strategy process - process is None'
                }), 500
        else:
            # Timeout waiting for process
            strategy_running = False
            logging.error("[LIVE TRADER] Timeout waiting for strategy process to start")
            return jsonify({
                'success': False,
                'error': 'Timeout waiting for strategy process to start. Please check logs for details.'
            }), 500
        
        # Check if process has already terminated with error
        if strategy_process.poll() is not None:
            returncode = strategy_process.returncode
            strategy_running = False
            error_msg = f'Strategy process exited immediately with code {returncode}'
            logging.error(f"[LIVE TRADER] {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
        
        # Process started successfully
        logging.info("[LIVE TRADER] Strategy process started successfully")
        return jsonify({
            'success': True,
            'message': 'Live Trader started successfully',
            'process_id': strategy_process.pid if strategy_process else None
        })
        
    except Exception as e:
        logging.error(f"[LIVE TRADER] Error starting Live Trader: {e}")
        import traceback
        logging.error(f"[LIVE TRADER] Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'Failed to start Live Trader: {str(e)}'
        }), 500

@app.route('/api/strategy/stop', methods=['POST'])
def stop_strategy():
    """Stop the trading strategy"""
    try:
        global strategy_bot, strategy_process, strategy_running
        
        # Check actual process status
        actual_running = False
        if strategy_process is not None:
            poll_result = strategy_process.poll()
            if poll_result is None:
                actual_running = True
            else:
                # Process already terminated
                logging.info("[STRATEGY] Process already terminated with return code: {}".format(poll_result))
                strategy_running = False
                strategy_process = None
        
        if not actual_running and not strategy_running:
            return jsonify({
                'status': 'error',
                'message': 'Strategy is not running'
            }), 400
        
        logging.info("[STRATEGY] Stopping strategy (PID: {})".format(strategy_process.pid if strategy_process else 'N/A'))
        
        # Stop TradingBot if running
        if strategy_bot:
            strategy_bot.stop_requested = True
        
        # Stop subprocess if running
        if strategy_process:
            try:
                strategy_process.terminate()
                # Wait a bit for graceful shutdown
                import time
                time.sleep(2)
                if strategy_process.poll() is None:
                    strategy_process.kill()
                strategy_process.wait(timeout=3)
            except Exception as e:
                print(f"Error stopping process: {e}")
                try:
                    strategy_process.kill()
                except:
                    pass
            finally:
                strategy_process = None
        
        strategy_running = False
        
        return jsonify({
            'status': 'success',
            'message': 'Strategy stop requested'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Authentication API Endpoints
@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status with auto-reconnection"""
    try:
        global strategy_bot, kite_client_global, kite_api_key
        
        authenticated = False
        has_access_token = False
        
        # Check global kite client first
        global account_holder_name
        if kite_client_global and hasattr(kite_client_global, 'kite'):
            # Validate connection with retry
            is_valid, result = validate_kite_connection(kite_client_global)
            
            if is_valid:
                profile = result
                authenticated = True
                has_access_token = kite_client_global.access_token is not None
                
                # Update account holder name if available
                if profile:
                    new_account_name = profile.get('user_name') or profile.get('user_id') or account_holder_name or 'Trading Account'
                    if new_account_name != account_holder_name:
                        logging.info("[AUTH] Account holder name updated: {} -> {}".format(account_holder_name, new_account_name))
                    account_holder_name = new_account_name
                    kite_client_global.account = account_holder_name
                logging.debug("[AUTH] Authentication verified successfully for account: {}".format(account_holder_name))
            else:
                # Connection failed - try to reconnect if we have API key
                authenticated = False
                has_access_token = kite_client_global.access_token is not None
                logging.warning("[AUTH] Authentication check failed: {}. Attempting reconnection...".format(result))
                
                # Attempt auto-reconnection
                if kite_api_key and reconnect_kite_client():
                    authenticated = True
                    has_access_token = kite_client_global.access_token is not None
                    logging.info("[AUTH] Auto-reconnection successful")
        else:
            # No client - try to reconnect if we have API key
            if kite_api_key:
                logging.info("[AUTH] No kite client found, attempting reconnection...")
                if reconnect_kite_client():
                    authenticated = True
                    has_access_token = kite_client_global.access_token is not None
                    logging.info("[AUTH] Reconnection successful")
        
        # Also check bot's kite client
        if not authenticated and strategy_bot and hasattr(strategy_bot, 'kite_client'):
            try:
                if hasattr(strategy_bot.kite_client, 'kite'):
                    is_valid, _ = validate_kite_connection(strategy_bot.kite_client)
                    if is_valid:
                        authenticated = True
                        has_access_token = strategy_bot.kite_client.access_token is not None if hasattr(strategy_bot.kite_client, 'access_token') else False
            except:
                pass
        
        return jsonify({
            'authenticated': authenticated,
            'has_access_token': has_access_token,
            'account_name': account_holder_name if authenticated else None
        })
    except Exception as e:
        logging.error(f"[AUTH] Error checking auth status: {e}")
        return jsonify({
            'authenticated': False,
            'error': str(e)
        }), 500

@app.route('/api/auth/set-credentials', methods=['POST'])
def set_credentials():
    """Set API credentials for authentication"""
    try:
        global kite_api_key, kite_api_secret
        
        data = request.get_json()
        kite_api_key = data.get('api_key', '').strip()
        kite_api_secret = data.get('api_secret', '').strip()
        
        if not kite_api_key or not kite_api_secret:
            return jsonify({
                'success': False,
                'error': 'API key and secret are required'
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'API credentials set successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/auth/authenticate', methods=['POST'])
def authenticate():
    """Authenticate with Zerodha using request token"""
    try:
        global strategy_bot, kite_client_global, kite_api_key, kite_api_secret
        
        data = request.get_json() or {}
        request_token = data.get('request_token', '').strip()
        incoming_api_key = data.get('api_key', '').strip()
        incoming_api_secret = data.get('api_secret', '').strip()
        
        if not request_token:
            return jsonify({
                'success': False,
                'error': 'Request token is required'
            }), 400
        
        # Allow API key/secret to be provided in the same call
        if incoming_api_key and incoming_api_secret:
            kite_api_key = incoming_api_key
            kite_api_secret = incoming_api_secret
        elif incoming_api_key or incoming_api_secret:
            return jsonify({
                'success': False,
                'error': 'Both API key and API secret are required'
            }), 400
        
        # Need API key and secret for authentication
        if not kite_api_key or not kite_api_secret:
            return jsonify({
                'success': False,
                'error': 'API credentials not configured. Please provide API key and secret.'
            }), 400
        
        # Create or update global kite client
        try:
            try:
                from src.kite_client import KiteClient  # when running from repo root
            except ImportError:
                from kite_client import KiteClient       # fallback when src on PYTHONPATH
            kite_client_global = KiteClient(
                kite_api_key,
                kite_api_secret,
                request_token=request_token,
                account='DASHBOARD'
            )
            
            # Verify authentication by getting profile
            is_valid, result = validate_kite_connection(kite_client_global)
            if not is_valid:
                raise Exception(result)
            
            profile = result
            
            # Extract and store account holder name
            global account_holder_name, strategy_account_name
            account_holder_name = profile.get('user_name') or profile.get('user_id') or 'Trading Account'
            kite_client_global.account = account_holder_name  # Update account name in client
            # Keep strategy account name in sync for log matching
            strategy_account_name = account_holder_name
            
            # Save token for persistence
            if kite_client_global.access_token:
                save_access_token(kite_api_key, kite_client_global.access_token, account_holder_name)
            
            logging.info(f"[AUTH] Account holder name: {account_holder_name}")
            
            return jsonify({
                'success': True,
                'message': 'Authentication successful',
                'account_name': account_holder_name
            })
        except Exception as e:
            logger.error("[AUTH] Authentication failed: {}".format(str(e)))
            import traceback
            logger.error("[AUTH] Traceback: {}".format(traceback.format_exc()))
            return jsonify({
                'success': False,
                'error': f'Authentication failed: {str(e)}'
            }), 401
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/auth/set-access-token', methods=['POST'])
def set_access_token():
    """Set access token directly (if user already has one)"""
    try:
        global strategy_bot, kite_client_global, kite_api_key, kite_api_secret
        
        data = request.get_json() or {}
        access_token = data.get('access_token', '').strip()
        api_key = data.get('api_key', '').strip() or kite_api_key  # Allow overriding API key
        api_secret_override = data.get('api_secret', '').strip()
        
        if api_secret_override:
            kite_api_secret = api_secret_override  # persist secret if provided
        
        if not access_token:
            return jsonify({
                'success': False,
                'error': 'Access token is required'
            }), 400
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'API key is required. Please provide it in the form or configure it when starting the strategy.'
            }), 400
        
        # Create or update global kite client with access token
        try:
            try:
                from src.kite_client import KiteClient
            except ImportError:
                from kite_client import KiteClient
            kite_client_global = KiteClient(
                api_key,
                kite_api_secret or '',  # API secret not needed for access token
                access_token=access_token,
                account='DASHBOARD'
            )
            
            # Verify the token works by getting profile
            is_valid, result = validate_kite_connection(kite_client_global)
            if not is_valid:
                raise Exception(result)
            
            profile = result
            
            # Extract and store account holder name
            global account_holder_name, strategy_account_name
            account_holder_name = profile.get('user_name') or profile.get('user_id') or 'Trading Account'
            kite_client_global.account = account_holder_name  # Update account name in client
            # Keep strategy account name in sync for log matching
            strategy_account_name = account_holder_name
            
            # Save token for persistence
            if kite_client_global.access_token:
                save_access_token(api_key, kite_client_global.access_token, account_holder_name)
            
            logging.info(f"[AUTH] Account holder name: {account_holder_name}")
            
            # Store API key if provided
            if data.get('api_key'):
                kite_api_key = api_key
            
            return jsonify({
                'success': True,
                'message': 'Connected successfully',
                'authenticated': True,
                'account_name': account_holder_name
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Invalid or expired access token: {str(e)}'
            }), 401
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/connectivity', methods=['GET'])
def check_connectivity():
    """Check system connectivity status"""
    try:
        global strategy_bot, kite_client_global
        
        connectivity = {
            'connected': False,
            'api_connected': False,
            'websocket_connected': False,
            'api_authenticated': False,
            'last_check': datetime.now().isoformat(),
            'status_message': ''
        }
        
        # Check global kite client first
        if kite_client_global and hasattr(kite_client_global, 'kite'):
            is_valid, result = validate_kite_connection(kite_client_global)
            if is_valid:
                connectivity['api_authenticated'] = True
                connectivity['api_connected'] = True
                connectivity['status_message'] = 'API Connected'
            else:
                connectivity['api_authenticated'] = kite_client_global.access_token is not None
                connectivity['api_connected'] = False
                connectivity['status_message'] = f'API Error: {result[:50]}'
                
                # Try auto-reconnection
                if kite_api_key:
                    if reconnect_kite_client():
                        connectivity['api_authenticated'] = True
                        connectivity['api_connected'] = True
                        connectivity['status_message'] = 'API Connected (reconnected)'
        
        # Also check bot's kite client
        if not connectivity['api_connected'] and strategy_bot and hasattr(strategy_bot, 'kite_client'):
            try:
                if hasattr(strategy_bot.kite_client, 'kite'):
                    strategy_bot.kite_client.kite.profile()
                    connectivity['api_authenticated'] = True
                    connectivity['api_connected'] = True
                    connectivity['status_message'] = 'API Connected'
            except Exception as api_error:
                if not connectivity['status_message']:
                    connectivity['api_authenticated'] = strategy_bot.kite_client.access_token is not None if hasattr(strategy_bot.kite_client, 'access_token') else False
                    connectivity['api_connected'] = False
                    connectivity['status_message'] = f'API Error: {str(api_error)[:50]}'
        
        if not connectivity['status_message']:
            connectivity['status_message'] = 'Not Authenticated'
        
        connectivity['connected'] = connectivity['api_connected']
        
        return jsonify(connectivity)
    except Exception as e:
        return jsonify({
            'connected': False,
            'api_connected': False,
            'websocket_connected': False,
            'error': str(e),
            'status_message': f'Error: {str(e)}'
        }), 500

def update_config_file(param_name, new_value):
    """Update parameter in config.py file"""
    try:
        # Determine config file path - check both locations
        config_path = os.path.join('src', 'config.py')
        if not os.path.exists(config_path):
            config_path = 'config.py'
        if not os.path.exists(config_path):
            # Try absolute path
            import sys
            if 'src' in sys.path:
                config_path = os.path.join(sys.path[0], 'src', 'config.py')
            else:
                config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.py')
        
        # Read current config file
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Handle dictionary values (like STOP_LOSS_CONFIG)
        if isinstance(new_value, dict):
            # Find the start of the dictionary
            start_idx = None
            
            for i, line in enumerate(lines):
                if line.strip().startswith(f'{param_name} ='):
                    start_idx = i
                    break
            
            if start_idx is None:
                print(f"Parameter {param_name} not found in config file")
                return False
            
            # Find the end of the dictionary (matching braces)
            brace_count = 0
            end_idx = start_idx
            found_opening = False
            
            for i in range(start_idx, len(lines)):
                line = lines[i]
                brace_count += line.count('{')
                brace_count -= line.count('}')
                if '{' in line:
                    found_opening = True
                if found_opening and brace_count == 0:
                    end_idx = i
                    break
            
            # Build dictionary string with proper formatting
            dict_lines = [f'{param_name} = {{\n']
            for key, value in new_value.items():
                dict_lines.append(f'    "{key}": {value},\n')
            dict_lines.append('}')
            
            # Extract comment from original start line if exists
            comment = ''
            if '#' in lines[start_idx]:
                comment = ' #' + lines[start_idx].split('#', 1)[1].strip()
            dict_lines[-1] = dict_lines[-1].rstrip('\n') + comment + '\n'
            
            # Replace the dictionary block
            lines = lines[:start_idx] + dict_lines + lines[end_idx+1:]
            updated = True
        else:
            # Handle simple values
            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f'{param_name} ='):
                    # Extract the comment if it exists
                    comment = ''
                    if '#' in line:
                        comment = ' #' + line.split('#', 1)[1].strip()
                    
                    # Format the value appropriately
                    if isinstance(new_value, str):
                        value_str = f"'{new_value}'"
                    elif isinstance(new_value, bool):
                        value_str = str(new_value)
                    elif isinstance(new_value, float):
                        value_str = str(new_value)
                    else:
                        value_str = str(new_value)
                    
                    # Update the line
                    lines[i] = f'{param_name} = {value_str}{comment}\n'
                    updated = True
                    break
                    
        if not updated:
            print(f"Parameter {param_name} not found in config file")
            return False
            
        # Write updated config back to file
        with open(config_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
            
        print(f"Successfully updated {param_name} = {new_value}")
        return True
        
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        return False
    except PermissionError:
        print(f"Permission denied: Cannot write to {config_path}")
        return False
    except Exception as e:
        print(f"Error updating config file: {e}")
        import traceback
        traceback.print_exc()
        return False

def initialize_dashboard():
    """Initialize dashboard and attempt to reconnect if token exists"""
    global kite_api_key
    try:
        # Try to load saved token if API key is available
        if kite_api_key:
            logging.info("[INIT] Attempting to reconnect with saved token...")
            if reconnect_kite_client():
                logging.info("[INIT] Successfully reconnected on startup")
            else:
                logging.info("[INIT] No valid saved token found or reconnection failed")
    except Exception as e:
        logging.warning(f"[INIT] Error during initialization: {e}")

def start_dashboard(host=None, port=None, debug=False):
    """Start the config dashboard web server"""
    try:
        # Initialize dashboard (try to reconnect)
        initialize_dashboard()
        
        # Use config values if not provided
        if host is None:
            host = DASHBOARD_HOST
        if port is None:
            port = DASHBOARD_PORT
        
        print("=" * 60)
        print(f"[CONFIG DASHBOARD] Starting web server")
        print(f"[CONFIG DASHBOARD] Host: {host}")
        print(f"[CONFIG DASHBOARD] Port: {port}")
        print(f"[CONFIG DASHBOARD] Dashboard URL: http://{host}:{port}")
        print(f"[CONFIG DASHBOARD] Configuration loaded from: src/config.py")
        print("=" * 60)
        
        # Log startup info
        logging.info(f"[DASHBOARD] Starting Flask app on {host}:{port}")
        logging.info(f"[DASHBOARD] Dashboard will be available at http://{host}:{port}")
        
        # Run Flask app (blocking call)
        app.run(host=host, port=port, debug=debug, use_reloader=False)
    except Exception as e:
        error_msg = f"[DASHBOARD] Failed to start dashboard: {e}"
        print(error_msg)
        logging.error(error_msg)
        import traceback
        traceback_str = traceback.format_exc()
        logging.error(f"[DASHBOARD] Traceback: {traceback_str}")
        print(traceback_str)
        raise  # Re-raise to see error in Azure logs

if __name__ == '__main__':
    start_dashboard()
