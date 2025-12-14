# Fix: API Secret Not Being Passed to Strategy

## Problem

The strategy was reading credentials from stdin, but `api_secret` was empty:
```
api_key : 14vxzgvarfrfxs5k
api_secret :  (empty!)
request_token : 1P8lBqtKd5Ff2SZfHFlx6a3aMMfJx6JA
Account : Priti Sharma
```

## Root Cause

When setting the access token via `/api/auth/set-access-token`, the `api_secret` was not being:
1. **Stored in `kite_client_global`** - The KiteClient was created with empty api_secret
2. **Retrieved when starting strategy** - The dashboard tried to get `api_secret` from `kite_client_global.api_secret`, which was empty

## Solution

### Fix 1: Store API Secret When Setting Access Token

Modified `/api/auth/set-access-token` to:
- Accept `api_secret` in the request (optional)
- Store it in global `kite_api_secret` variable
- Store it in `kite_client_global.api_secret` so it's available later

### Fix 2: Fallback When Getting Credentials

Modified `/api/live-trader/start` to:
- Try to get `api_secret` from `kite_client_global.api_secret`
- Fall back to global `kite_api_secret` if empty
- Validate that `api_secret` is available before starting strategy
- Return clear error if `api_secret` is missing

### Fix 3: Better Logging

Added logging to show credential status:
- Logs whether each credential (api_key, api_secret, access_token) is SET or NOT SET
- Warns if api_secret is missing

## Expected Behavior

### When Setting Access Token

If you provide `api_secret`:
```json
{
  "api_key": "your_api_key",
  "access_token": "your_access_token",
  "api_secret": "your_api_secret"  // Optional but recommended
}
```

The `api_secret` will be stored and available when starting the strategy.

### When Starting Strategy

The dashboard will:
1. Check `kite_client_global.api_secret`
2. Fall back to `kite_api_secret` if empty
3. Validate that `api_secret` exists
4. Pass it to the strategy via stdin

## What You Need to Do

### Option 1: Provide API Secret When Setting Access Token (Recommended)

When you set the access token in the dashboard, also provide the `api_secret`:
- This ensures it's stored and available for the strategy

### Option 2: Re-authenticate with Full Credentials

If you haven't provided `api_secret` yet:
1. Use the `/api/auth/authenticate` endpoint with:
   - `api_key`
   - `api_secret`
   - `request_token`
2. This will create a KiteClient with all credentials stored

## Testing

After the fix:
1. Set access token (with api_secret if possible)
2. Start the strategy
3. Check logs - you should see:
   ```
   [LIVE TRADER] Credentials check - api_key: SET, api_secret: SET, access_token: SET
   [ENV] Credentials read from stdin for account: Priti Sharma
   ```
4. Strategy should proceed without "Credentials not yet available" error

