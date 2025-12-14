# Fix: Strategy Not Reading Credentials from Dashboard

## Problem

The strategy was running but waiting for credentials from a "web interface" API endpoint that doesn't exist. The dashboard was passing credentials via stdin, but the strategy was ignoring stdin in Azure mode.

## Root Cause

The strategy script had two different credential input methods:
1. **Azure mode**: Tries to get credentials from `/api/trading/get-credentials` API endpoint
2. **Local mode**: Reads credentials from stdin using `input()`

When the dashboard starts the strategy as a subprocess, it passes credentials via stdin, but the strategy was in Azure mode, so it ignored stdin and tried to use the API endpoint instead.

## Solution

Modified the strategy script to:
1. **First try stdin** (when started as subprocess by dashboard)
2. **Fall back to API** (if stdin is not available)

### Changes Made

1. **Check stdin first in Azure mode:**
   - Detect if stdin is a pipe (subprocess mode)
   - Read credentials from stdin in the correct order:
     - Account
     - Api_key
     - Api_secret
     - Request_Token
     - Call_Quantity
     - Put_Quantity

2. **Fall back to API method:**
   - If stdin read fails, try the API endpoint method
   - This maintains backward compatibility

## Expected Behavior

After starting "Live Trader" from dashboard:

1. **Strategy starts** → Detects Azure environment
2. **Reads from stdin** → Gets credentials from dashboard
3. **Logs success** → `[ENV] Credentials read from stdin for account: Priti Sharma`
4. **Continues execution** → Sets up logging and starts trading

## What You Should See Now

Instead of:
```
[ENV] Waiting for credentials... (0 seconds)
[ENV] Waiting for credentials... (60 seconds)
[ENV] Credentials not set via web interface!
```

You should see:
```
[ENV] Azure environment detected
[ENV] stdin is a pipe, attempting to read credentials from stdin (subprocess mode)
[ENV] Credentials read from stdin for account: Priti Sharma
[STRATEGY] Starting logging setup for account: Priti Sharma
[STRATEGY] [SETUP LOGGING] Starting logging setup...
```

## Testing

1. Stop the current strategy (if running)
2. Start a new strategy from the dashboard
3. Check the logs - you should see credentials being read from stdin
4. Strategy should proceed to setup_logging and start trading

