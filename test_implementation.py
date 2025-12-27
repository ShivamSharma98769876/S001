"""
Test script for dashboard implementation
Tests database, API endpoints, and static files
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

print("=" * 60)
print("Testing Dashboard Implementation")
print("=" * 60)

# Test 1: Check SQLAlchemy
print("\n[TEST 1] Checking SQLAlchemy installation...")
try:
    import sqlalchemy
    print(f"[OK] SQLAlchemy version: {sqlalchemy.__version__}")
except ImportError:
    print("[ERROR] SQLAlchemy not installed. Run: pip install sqlalchemy")
    sys.exit(1)

# Test 2: Database Initialization
print("\n[TEST 2] Testing database initialization...")
try:
    from src.database.models import DatabaseManager
    db_manager = DatabaseManager()
    print(f"[OK] Database initialized successfully")
    print(f"  Database path: {db_manager.db_path}")
    print(f"  Database exists: {os.path.exists(db_manager.db_path)}")
except Exception as e:
    print(f"[ERROR] Database initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Database Models
print("\n[TEST 3] Testing database models...")
try:
    from src.database.models import Position, Trade, DailyStats, AuditLog
    print("[OK] All models imported successfully")
    print("  - Position model")
    print("  - Trade model")
    print("  - DailyStats model")
    print("  - AuditLog model")
except Exception as e:
    print(f"[ERROR] Model import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Repository Classes
print("\n[TEST 4] Testing repository classes...")
try:
    from src.database.repository import TradeRepository, PositionRepository, DailyStatsRepository
    trade_repo = TradeRepository(db_manager)
    position_repo = PositionRepository(db_manager)
    stats_repo = DailyStatsRepository(db_manager)
    print("[OK] All repository classes initialized successfully")
    print("  - TradeRepository")
    print("  - PositionRepository")
    print("  - DailyStatsRepository")
except Exception as e:
    print(f"[ERROR] Repository initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Database Queries
print("\n[TEST 5] Testing database queries...")
try:
    # Test getting trades (should work even if empty)
    trades = trade_repo.get_trades(broker_id='DEFAULT')
    print(f"[OK] Trade query successful: {len(trades)} trades found")
    
    # Test getting daily stats
    from datetime import date
    today_stat = stats_repo.get_today_stats(broker_id='DEFAULT')
    if today_stat:
        print(f"[OK] Daily stats query successful: Found today's stats")
    else:
        print("[OK] Daily stats query successful: No stats for today (expected if no data)")
    
    # Test cumulative P&L
    cumulative = trade_repo.get_cumulative_pnl(broker_id='DEFAULT')
    print(f"[OK] Cumulative P&L query successful: Rs.{cumulative:.2f}")
except Exception as e:
    print(f"[ERROR] Database query failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Static Files
print("\n[TEST 6] Checking static files...")
static_css = os.path.join('src', 'static', 'css', 'dashboard_features.css')
static_js = os.path.join('src', 'static', 'js', 'dashboard_features.js')

if os.path.exists(static_css):
    print(f"[OK] CSS file exists: {static_css}")
else:
    print(f"[ERROR] CSS file missing: {static_css}")

if os.path.exists(static_js):
    print(f"[OK] JavaScript file exists: {static_js}")
else:
    print(f"[ERROR] JavaScript file missing: {static_js}")

# Test 7: Flask App Import
print("\n[TEST 7] Testing Flask app import...")
try:
    from src.config_dashboard import app
    print("[OK] Flask app imported successfully")
    print(f"  App name: {app.name}")
    print(f"  Static folder: {app.static_folder}")
    print(f"  Static URL path: {app.static_url_path}")
except Exception as e:
    print(f"[ERROR] Flask app import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 8: API Routes
print("\n[TEST 8] Checking API routes...")
try:
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.rule.startswith('/api'):
            routes.append(rule.rule)
    
    required_routes = [
        '/api/dashboard/cumulative-pnl',
        '/api/dashboard/daily-stats',
        '/api/dashboard/pnl-calendar',
        '/api/dashboard/trade-history',
        '/api/auth/details'
    ]
    
    print(f"[OK] Found {len(routes)} API routes")
    for route in required_routes:
        if route in routes:
            print(f"  [OK] {route}")
        else:
            print(f"  [MISSING] {route}")
except Exception as e:
    print(f"✗ Route check failed: {e}")
    import traceback
    traceback.print_exc()

# Test 9: Database Tables
print("\n[TEST 9] Checking database tables...")
try:
    from sqlalchemy import inspect
    inspector = inspect(db_manager.engine)
    tables = inspector.get_table_names()
    
    required_tables = ['trades', 'positions', 'daily_stats', 'audit_logs']
    
    print(f"[OK] Found {len(tables)} tables in database")
    for table in required_tables:
        if table in tables:
            print(f"  [OK] {table}")
        else:
            print(f"  [MISSING] {table}")
except Exception as e:
    print(f"✗ Table check failed: {e}")
    import traceback
    traceback.print_exc()

# Test 10: PnLRecorder Database Support
print("\n[TEST 10] Testing PnLRecorder database support...")
try:
    from src.pnl_recorder import PnLRecorder
    recorder = PnLRecorder(use_database=True)
    if recorder.use_database:
        print("[OK] PnLRecorder database mode enabled")
    else:
        print("[WARNING] PnLRecorder database mode disabled (falling back to files)")
except Exception as e:
    print(f"[WARNING] PnLRecorder test warning: {e}")

print("\n" + "=" * 60)
print("Testing Complete!")
print("=" * 60)
print("\nNext steps:")
print("1. If migration needed, run: python migrations/migrate_json_to_database.py")
print("2. Start dashboard: python app.py")
print("3. Navigate to: http://localhost:8080")
print("4. Test all features in the browser")

