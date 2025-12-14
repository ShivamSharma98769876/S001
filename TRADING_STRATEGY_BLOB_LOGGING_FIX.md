# Fix: Trading Strategy Logs Not Appearing in Azure Blob

## Current Situation

✅ **Dashboard logs ARE appearing in blob:**
- Path: `s0001strangle-log/logs/trading_2025Dec14.log`
- These are from `config_dashboard` logger (no account_name)

❌ **Trading strategy logs are NOT appearing in blob:**
- Strategy runs with account_name="Priti Sharma"
- Logs should go to: `Priti/logs/Priti_2025Dec14.log`
- But they're only in `/tmp/Priti/logs/` (local filesystem)

## Root Cause

The trading strategy runs as a subprocess and:
1. ✅ Environment variables are now explicitly passed (fixed)
2. ❌ Azure Blob logging setup may be failing silently
3. ❌ Diagnostic messages may not be appearing in log stream

## What Should Happen

When the trading strategy starts:

1. It calls `setup_logging(account_name="Priti Sharma")`
2. This should print in log stream:
   ```
   [STRATEGY] [SETUP LOGGING] Starting logging setup - account_name=Priti Sharma
   [STRATEGY] [SETUP LOGGING] Azure environment detected
   [STRATEGY] [LOG SETUP] Setting up Azure Blob Storage logging for account: Priti Sharma
   [STRATEGY] [AZURE BLOB] Checking configuration...
   [STRATEGY] [AZURE BLOB] AZURE_BLOB_LOGGING_ENABLED = True
   [STRATEGY] [AZURE BLOB] Connection string available: True
   [STRATEGY] [AZURE BLOB] Container name: s0001strangle
   [STRATEGY] [AZURE BLOB] Logging to Azure Blob: s0001strangle/Priti/logs/Priti_2025Dec14.log
   ```

3. Logs should appear in blob at: `Priti/logs/Priti_2025Dec14.log`

## Container Name Issue

The blob path shows `s0001strangle-log` instead of `s0001strangle`. This suggests:
- `AZURE_BLOB_CONTAINER_NAME` might be set to `s0001strangle-log` in Azure Portal
- Or there's a typo in the environment variable

**Check in Azure Portal:**
- Configuration > Application settings
- `AZURE_BLOB_CONTAINER_NAME` should be exactly `s0001strangle` (not `s0001strangle-log`)

## Next Steps

1. **Check Log Stream** for `[STRATEGY]` messages when starting a new trading strategy
2. **Look for** `[SETUP LOGGING]`, `[LOG SETUP]`, and `[AZURE BLOB]` messages
3. **Verify** container name in Azure Portal is `s0001strangle`
4. **Wait 30+ seconds** after strategy starts for first blob flush
5. **Check blob** at path: `Priti/logs/Priti_2025Dec14.log`

## Expected Blob Structure

After fix, you should see:

```
s0001strangle/
├── logs/
│   └── trading_2025Dec14.log          (Dashboard logs - no account)
└── Priti/
    └── logs/
        └── Priti_2025Dec14.log        (Trading strategy logs - with account)
```

## If Still Not Working

1. Check Log Stream for `[STRATEGY] [AZURE BLOB]` messages
2. Look for error messages like:
   - `[AZURE BLOB] ERROR: Azure Blob Storage connection string not available`
   - `[AZURE BLOB] Warning: Failed to setup Azure Blob logging`
3. Verify all environment variables are set correctly
4. Check if subprocess has access to environment variables (now fixed with explicit `env=env`)

