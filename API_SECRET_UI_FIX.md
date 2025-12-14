# Fix: API Secret Not Available Error in Live Trader

## Problem

The dashboard shows "Connected" and "Authenticated" at the top, but when trying to start the Live Trader, it shows:
```
API secret not available. Please authenticate with API key and secret first.
```

## Root Cause

When authenticating with just an access token (without API secret), the `api_secret` was not stored. The strategy requires `api_secret` to work properly.

## Solution Applied

### 1. Added API Secret Field to Authentication Form

Updated the "Set Access Token" form in the authentication modal to include:
- **API Secret field** (password type, recommended)
- Helpful text explaining it's required for starting strategy

### 2. Updated Frontend to Send API Secret

Modified `authenticateWithAccessToken()` function to:
- Read `api_secret` from the form
- Send it to the backend when authenticating

### 3. Improved Error Messages

- Backend now returns a clear error message
- Frontend shows helpful instructions when API secret is missing
- Tells user to click "Authenticated" badge to update credentials

### 4. Better Validation

- Validates that `api_secret` exists before starting strategy
- Returns clear error with instructions if missing

## What You Need to Do

### Step 1: Re-authenticate with API Secret

1. Click on the **"Authenticated"** status badge at the top of the page
2. In the authentication modal, go to the **"Access Token"** tab
3. Fill in:
   - **API Key** (if not already configured)
   - **API Secret** ← **This is the important one!**
   - **Access Token**
4. Click **"Connect"**

### Step 2: Start Strategy

After re-authenticating with API secret:
1. The error message should disappear
2. Click **"Start Live Trader"**
3. Strategy should start successfully

## Expected Result

After providing API secret:
- ✅ No more "API secret not available" error
- ✅ Strategy starts successfully
- ✅ All credentials are properly stored

## Why API Secret is Required

The trading strategy needs `api_secret` to:
- Generate new access tokens if the current one expires
- Authenticate with Kite Connect API
- Execute trades properly

Even though you have a valid access token now, the strategy needs `api_secret` for long-term operation.

