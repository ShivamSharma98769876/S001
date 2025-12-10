# Authentication Disconnection Issues - Causes & Solutions

## Why Authentication Gets Disconnected

### Main Reasons:

1. **Access Token Expiry** ⏰
   - Zerodha access tokens expire after **24 hours** or when you log out from Kite
   - Tokens also expire if you log in from another device/session
   - No automatic token refresh mechanism

2. **Application Restart** 🔄
   - Tokens are stored **in memory only** (not persisted)
   - If Azure restarts your app (deployment, auto-restart, etc.), tokens are lost
   - Application restarts clear all in-memory variables

3. **Session Invalidation** 🚫
   - Zerodha invalidates sessions after extended inactivity
   - Multiple logins from different locations can invalidate previous sessions
   - Security policies may force re-authentication

4. **Network Issues** 🌐
   - Temporary network disconnections can break the session
   - Azure network issues or timeouts

5. **Token Not Persisted** 💾
   - Current implementation stores tokens in memory only
   - No token storage/retrieval mechanism

## Solutions

### Solution 1: Add Token Persistence (Recommended)

Store access tokens securely so they survive app restarts:

```python
# Add to src/config_dashboard.py
import json
import os
from pathlib import Path

TOKEN_STORAGE_FILE = os.path.join(os.path.dirname(__file__), 'tokens.json')

def save_access_token(api_key, access_token):
    """Save access token to file"""
    try:
        tokens = {}
        if os.path.exists(TOKEN_STORAGE_FILE):
            with open(TOKEN_STORAGE_FILE, 'r') as f:
                tokens = json.load(f)
        
        tokens[api_key] = {
            'access_token': access_token,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(TOKEN_STORAGE_FILE, 'w') as f:
            json.dump(tokens, f)
    except Exception as e:
        logging.error(f"Error saving token: {e}")

def load_access_token(api_key):
    """Load access token from file"""
    try:
        if os.path.exists(TOKEN_STORAGE_FILE):
            with open(TOKEN_STORAGE_FILE, 'r') as f:
                tokens = json.load(f)
                if api_key in tokens:
                    return tokens[api_key]['access_token']
    except Exception as e:
        logging.error(f"Error loading token: {e}")
    return None
```

### Solution 2: Add Token Refresh Check

Check token validity before it expires and prompt for refresh:

```python
# Add to auth status check
def check_token_validity():
    """Check if token is still valid"""
    global kite_client_global
    if kite_client_global:
        try:
            kite_client_global.kite.profile()
            return True
        except Exception as e:
            if "Invalid" in str(e) or "expired" in str(e).lower():
                return False
    return False
```

### Solution 3: Auto-Reconnect on Disconnection

Add automatic reconnection logic:

```python
# Add to config_dashboard.py
def auto_reconnect():
    """Attempt to reconnect using saved token"""
    global kite_client_global, kite_api_key
    if kite_api_key:
        saved_token = load_access_token(kite_api_key)
        if saved_token:
            try:
                from src.kite_client import KiteClient
                kite_client_global = KiteClient(
                    kite_api_key,
                    kite_api_secret or '',
                    access_token=saved_token,
                    account='DASHBOARD'
                )
                kite_client_global.kite.profile()
                return True
            except:
                return False
    return False
```

### Solution 4: Enhanced Auth Status Check

Improve the auth status endpoint to handle token expiry:

```python
@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status with token validation"""
    try:
        global kite_client_global
        
        authenticated = False
        has_access_token = False
        token_expired = False
        
        # Check global kite client first
        if kite_client_global and hasattr(kite_client_global, 'kite'):
            try:
                # Try to get profile to verify authentication
                kite_client_global.kite.profile()
                authenticated = True
                has_access_token = kite_client_global.access_token is not None
            except Exception as e:
                error_msg = str(e).lower()
                if "invalid" in error_msg or "expired" in error_msg or "unauthorized" in error_msg:
                    token_expired = True
                authenticated = False
                has_access_token = kite_client_global.access_token is not None
        
        # Try to reconnect if token expired
        if token_expired:
            if auto_reconnect():
                authenticated = True
        
        return jsonify({
            'authenticated': authenticated,
            'has_access_token': has_access_token,
            'token_expired': token_expired,
            'message': 'Token expired. Please re-authenticate.' if token_expired else None
        })
    except Exception as e:
        return jsonify({
            'authenticated': False,
            'has_access_token': False,
            'error': str(e)
        }), 500
```

### Solution 5: Frontend Token Expiry Warning

Add warning in the dashboard when token is about to expire:

```javascript
// Add to config_dashboard.html
async function checkTokenExpiry() {
    try {
        const response = await fetch('/api/auth/status');
        const data = await response.json();
        
        if (data.token_expired) {
            // Show warning banner
            showTokenExpiredWarning();
        } else if (data.authenticated) {
            // Token is valid, hide warning
            hideTokenExpiredWarning();
        }
    } catch (error) {
        console.error('Error checking token expiry:', error);
    }
}

// Check every 5 minutes
setInterval(checkTokenExpiry, 5 * 60 * 1000);
```

## Quick Fixes (Immediate Actions)

### 1. Re-authenticate When Disconnected
- Click on "Not Authenticated" badge
- Enter your access token again
- Or use Request Token method to generate new token

### 2. Check Token Validity
- Access tokens from Zerodha expire after 24 hours
- Generate a new token if it's been more than 24 hours

### 3. Avoid Multiple Logins
- Don't log in to Kite from multiple devices simultaneously
- This can invalidate your access token

### 4. Monitor Application Restarts
- Check Azure Portal > Activity log for app restarts
- Re-authenticate after any restart

## Best Practices

1. **Save Access Token**: Implement token persistence (Solution 1)
2. **Monitor Expiry**: Add token expiry warnings (Solution 5)
3. **Auto-Reconnect**: Implement auto-reconnect logic (Solution 3)
4. **Regular Checks**: Check auth status every few minutes
5. **User Notification**: Show clear messages when token expires

## Implementation Priority

1. **High Priority**: Solution 1 (Token Persistence) - Prevents loss on restart
2. **High Priority**: Solution 4 (Enhanced Auth Check) - Better error handling
3. **Medium Priority**: Solution 3 (Auto-Reconnect) - Better UX
4. **Low Priority**: Solution 5 (Frontend Warning) - User awareness

## Testing

After implementing solutions:
1. Authenticate and verify token is saved
2. Restart the application
3. Verify token is loaded automatically
4. Test token expiry handling
5. Test reconnection logic

