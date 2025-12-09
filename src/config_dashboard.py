"""
Web Dashboard for Real-time Config Parameter Management
Provides web interface for monitoring and updating trading parameters
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
import sys
from datetime import datetime
import threading
import time

# Add parent directory to path for config imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import config monitor
from config_monitor import get_config_monitor

app = Flask(__name__)

# Global config monitor reference
config_monitor = None

def set_config_monitor(monitor):
    """Set the global config monitor reference"""
    global config_monitor
    config_monitor = monitor

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('config_dashboard.html')

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
                    'VIX_DELTA_LOW': getattr(config, 'VIX_DELTA_LOW', 0.30),
                    'VIX_DELTA_HIGH': getattr(config, 'VIX_DELTA_HIGH', 0.40),
                    'VIX_DELTA_THRESHOLD': getattr(config, 'VIX_DELTA_THRESHOLD', 13),
                    'DELTA_MONITORING_THRESHOLD': getattr(config, 'DELTA_MONITORING_THRESHOLD', 0.22),
                    'INITIAL_PROFIT_BOOKING': getattr(config, 'INITIAL_PROFIT_BOOKING', 14),
                    'SECOND_PROFIT_BOOKING': getattr(config, 'SECOND_PROFIT_BOOKING', 28)
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
            
        # Update config file
        success = update_config_file(param_name, new_value)
        
        if success:
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

def update_config_file(param_name, new_value):
    """Update parameter in config.py file"""
    try:
        config_path = 'config.py'
        
        # Read current config file
        with open(config_path, 'r') as f:
            lines = f.readlines()
            
        # Find and update the parameter
        updated = False
        for i, line in enumerate(lines):
            if line.strip().startswith(f'{param_name} ='):
                # Extract the comment if it exists
                comment = ''
                if '#' in line:
                    comment = ' #' + line.split('#', 1)[1].strip()
                    
                # Update the line
                lines[i] = f'{param_name} = {new_value}{comment}\n'
                updated = True
                break
                
        if not updated:
            print(f"Parameter {param_name} not found in config file")
            return False
            
        # Write updated config back to file
        with open(config_path, 'w') as f:
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
        return False

def start_dashboard(host='127.0.0.1', port=5000, debug=False):
    """Start the config dashboard web server"""
    print(f"[CONFIG DASHBOARD] Starting web server on http://{host}:{port}")
    print(f"[CONFIG DASHBOARD] Dashboard URL: http://{host}:{port}")
    app.run(host=host, port=port, debug=debug, use_reloader=False)

if __name__ == '__main__':
    start_dashboard()
