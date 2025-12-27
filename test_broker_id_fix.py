"""
Test script for broker_id integration fix
Tests the get_broker_id_from_auth() function and verifies all endpoints use it
"""

import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(parent_dir)

print("=" * 60)
print("Testing Broker ID Integration Fix")
print("=" * 60)

# Test 1: Import the helper function
print("\n[TEST 1] Testing helper function import...")
try:
    from src.config_dashboard import get_broker_id_from_auth
    print("[OK] Helper function imported successfully")
except Exception as e:
    print(f"[ERROR] Failed to import helper function: {e}")
    sys.exit(1)

# Test 2: Test function when not authenticated
print("\n[TEST 2] Testing function when not authenticated...")
try:
    broker_id = get_broker_id_from_auth()
    print(f"[OK] Function returned: '{broker_id}'")
    if broker_id == 'DEFAULT':
        print("  [OK] Correctly falls back to 'DEFAULT' when not authenticated")
    else:
        print(f"  [INFO] Returned '{broker_id}' (may be account_holder_name if set)")
except Exception as e:
    print(f"[ERROR] Function failed: {e}")

# Test 3: Verify all endpoints use the helper function
print("\n[TEST 3] Verifying all endpoints use get_broker_id_from_auth()...")
try:
    import inspect
    from src import config_dashboard
    
    # Read the source file to check for hardcoded 'DEFAULT'
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'config_dashboard.py')
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for problematic patterns
    problematic_patterns = [
        "broker_id = 'DEFAULT'  # TODO",
        "broker_id = 'DEFAULT'  # TODO: Get from authentication",
        "broker_id = 'DEFAULT'  # TODO: Get from authentication if available"
    ]
    
    found_issues = []
    for pattern in problematic_patterns:
        if pattern in content:
            found_issues.append(pattern)
    
    if found_issues:
        print(f"[WARNING] Found {len(found_issues)} potential issues:")
        for issue in found_issues:
            print(f"  - {issue}")
    else:
        print("[OK] No hardcoded 'DEFAULT' with TODO comments found")
    
    # Count uses of get_broker_id_from_auth()
    uses_count = content.count('get_broker_id_from_auth()')
    print(f"[OK] Found {uses_count} uses of get_broker_id_from_auth()")
    
    # Verify it's used in the 5 key endpoints
    endpoints_to_check = [
        '/api/dashboard/trade-history',
        '/api/dashboard/cumulative-pnl',
        '/api/dashboard/daily-stats',
        '/api/dashboard/pnl-calendar',
        '/api/dashboard/sync-orders'
    ]
    
    print("\n[TEST 4] Checking specific endpoints...")
    for endpoint in endpoints_to_check:
        # Find the route definition
        route_pattern = f"@app.route('{endpoint}'"
        if route_pattern in content:
            # Find the function body after the route
            route_idx = content.find(route_pattern)
            # Look for broker_id assignment in the next 100 lines
            section = content[route_idx:route_idx+2000]
            if 'get_broker_id_from_auth()' in section:
                print(f"  [OK] {endpoint} uses get_broker_id_from_auth()")
            elif "broker_id = 'DEFAULT'" in section:
                print(f"  [ERROR] {endpoint} still uses hardcoded 'DEFAULT'")
            else:
                print(f"  [WARNING] {endpoint} - Could not verify broker_id usage")
        else:
            print(f"  [WARNING] {endpoint} - Route not found")
    
except Exception as e:
    print(f"[ERROR] Endpoint verification failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Test function signature and docstring
print("\n[TEST 5] Testing function signature...")
try:
    sig = inspect.signature(get_broker_id_from_auth)
    print(f"[OK] Function signature: {sig}")
    
    doc = inspect.getdoc(get_broker_id_from_auth)
    if doc:
        print(f"[OK] Function has docstring")
        print(f"  Docstring preview: {doc[:80]}...")
    else:
        print("[WARNING] Function missing docstring")
except Exception as e:
    print(f"[ERROR] Signature check failed: {e}")

# Test 6: Check if function handles errors gracefully
print("\n[TEST 6] Testing error handling...")
try:
    # The function should handle None/empty values gracefully
    # We can't easily test with a real kite client, but we can verify
    # the function structure handles exceptions
    import ast
    import inspect
    
    source = inspect.getsource(get_broker_id_from_auth)
    if 'try:' in source and 'except' in source:
        print("[OK] Function has try/except error handling")
    else:
        print("[WARNING] Function may not have error handling")
    
    if 'validate_kite_connection' in source:
        print("[OK] Function uses validate_kite_connection")
    else:
        print("[WARNING] Function may not validate connection")
        
except Exception as e:
    print(f"[ERROR] Error handling check failed: {e}")

print("\n" + "=" * 60)
print("Testing Complete!")
print("=" * 60)
print("\nNext Steps:")
print("1. Start the dashboard: python app.py or python src/config_dashboard.py")
print("2. Authenticate with Zerodha credentials")
print("3. Check browser console for any errors")
print("4. Verify data is user-specific (if you have multiple accounts)")
print("5. Test all 5 endpoints return data filtered by broker_id")

