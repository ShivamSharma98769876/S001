# Quick Fix: Logs Not Appearing in Azure Blob Container

## Most Common Issues

### 1. Environment Variables Not Set

Check in Azure Portal > App Service > Configuration > Application settings:

**Required Variables:**
- `AzureBlobStorageKey` = Your storage account key
- `AZURE_BLOB_ACCOUNT_NAME` = `s0001strangle` (or your account name)
- `AZURE_BLOB_CONTAINER_NAME` = `s0001strangle` (or your container name)
- `AZURE_BLOB_LOGGING_ENABLED` = `True` (must be exactly "True")

### 2. Check Where Logs Are Being Written

Logs are written to different paths based on whether `account_name` is provided:

**With account_name:**
- Path: `{account_name}/logs/{account_name}_{date}.log`
- Example: `John/logs/John_2025Dec13.log`

**Without account_name (current Azure setup):**
- Path: `logs/trading_{date}.log`
- Example: `logs/trading_2025Dec13.log`

**Check both locations in your container!**

### 3. Logs Are Buffered

Logs are flushed:
- Every 30 seconds
- When buffer exceeds 8KB
- On application restart

**Wait at least 1 minute after app starts, then check the container.**

### 4. Check Application Logs for Errors

In Azure Portal:
1. Go to **Log stream** or **Logs**
2. Look for messages starting with `[AZURE BLOB]`
3. Check for any error messages

Common error messages:
- `[AZURE BLOB] Warning: Azure Blob Storage connection string not available` → Environment variables not set
- `[AZURE BLOB] Error flushing to blob: ...` → Connection/authentication issue

## Quick Diagnostic Steps

### Step 1: Verify Environment Variables

Run this in Azure App Service SSH/Console:
```python
import os
print("AzureBlobStorageKey:", "SET" if os.getenv('AzureBlobStorageKey') else "NOT SET")
print("AZURE_BLOB_ACCOUNT_NAME:", os.getenv('AZURE_BLOB_ACCOUNT_NAME', 'NOT SET'))
print("AZURE_BLOB_CONTAINER_NAME:", os.getenv('AZURE_BLOB_CONTAINER_NAME', 'NOT SET'))
print("AZURE_BLOB_LOGGING_ENABLED:", os.getenv('AZURE_BLOB_LOGGING_ENABLED', 'NOT SET'))
```

### Step 2: Run Diagnostic Script

Upload `test_azure_blob_logging.py` to Azure and run:
```bash
python test_azure_blob_logging.py
```

This will:
- Check all environment variables
- Test connection to Azure Blob Storage
- Create a test log file
- Show you exactly where logs are being written

### Step 3: Check Container Manually

In Azure Portal:
1. Go to **Storage Account** > **Containers**
2. Open your container (e.g., `s0001strangle`)
3. Check these folders:
   - `logs/` folder (for logs without account name)
   - Any folder with account name (e.g., `John/logs/`)

### Step 4: Force Immediate Flush

If you want to see logs immediately, you can temporarily reduce the flush interval:

In `src/environment.py`, line 72, change:
```python
self.flush_interval = 30  # Change to 5 for testing
```

Then restart the app and logs will flush every 5 seconds.

## Expected Behavior

When logging is working correctly, you should see in application logs:
```
[AZURE BLOB] Logging to Azure Blob: s0001strangle/logs/trading_2025Dec13.log
[AZURE BLOB] Azure Blob Storage logging initialized: s0001strangle/logs/trading_2025Dec13.log
[AZURE BLOB] Successfully uploaded X bytes to s0001strangle/logs/trading_2025Dec13.log
```

## Still Not Working?

1. **Check storage account firewall**: Make sure App Service IP is allowed
2. **Verify storage account key**: Regenerate if needed
3. **Check container permissions**: Container should allow writes
4. **Review detailed troubleshooting**: See `TROUBLESHOOT_BLOB_LOGGING.md`

