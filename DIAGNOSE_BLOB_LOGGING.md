# Diagnose Why [AZURE BLOB] Messages Don't Appear

## What to Check in Log Stream

After deploying the updated code, you should see diagnostic messages in the log stream. Look for:

### 1. Configuration Diagnostic Messages

You should see messages like:
```
[CONFIG] Azure Blob Storage Configuration:
[CONFIG]   AZURE_BLOB_ACCOUNT_NAME = 's0001strangle' (SET)
[CONFIG]   AzureBlobStorageKey = SET
[CONFIG]   AZURE_BLOB_CONTAINER_NAME = 's0001strangle' (SET)
[CONFIG]   AZURE_BLOB_LOGGING_ENABLED = 'True' -> True
```

### 2. Azure Blob Setup Messages

You should see:
```
[AZURE BLOB] Checking configuration...
[AZURE BLOB] AZURE_BLOB_LOGGING_ENABLED = True
[AZURE BLOB] Connection string available: True
[AZURE BLOB] Container name: s0001strangle
[AZURE BLOB] Logging to Azure Blob: s0001strangle/logs/trading_2025Dec13.log
[AZURE BLOB] Azure Blob Storage logging initialized: ...
```

## If You Don't See [AZURE BLOB] Messages

### Scenario 1: No [CONFIG] Messages Either

**Problem:** The config.py file is not being loaded
**Solution:** Check if the app is starting correctly. Look for any import errors.

### Scenario 2: See [CONFIG] but Shows "NOT SET"

**Problem:** Environment variables are not set in Azure Portal
**Solution:** 
1. Go to Azure Portal > App Service > Configuration > Application settings
2. Add the missing variables
3. Save and wait for restart

### Scenario 3: See [CONFIG] but AZURE_BLOB_LOGGING_ENABLED = 'False'

**Problem:** The setting is not set to exactly "True"
**Solution:**
1. Check the value in Azure Portal
2. It must be exactly `True` (capital T, no quotes)
3. Common mistakes:
   - `true` (lowercase) ❌
   - `"True"` (with quotes) ❌
   - `TRUE` (all caps) ❌
   - `True` (correct) ✅

### Scenario 4: See [AZURE BLOB] Checking configuration... but then nothing

**Problem:** Connection string is not being constructed
**Solution:**
- Check if both `AzureBlobStorageKey` and `AZURE_BLOB_ACCOUNT_NAME` are set
- The connection string is built from these two values
- If either is missing, connection string will be None

### Scenario 5: See Error Messages

Look for error messages like:
- `[AZURE BLOB] ERROR: Azure Blob Storage connection string not available`
- `[AZURE BLOB] Warning: Failed to setup Azure Blob logging`

**Solution:** Follow the instructions in the error message.

## Quick Diagnostic Checklist

Run through this checklist:

1. ✅ App is running (you see other log messages)
2. ✅ See `[CONFIG] Azure Blob Storage Configuration:` messages
3. ✅ All variables show as "SET" (not "NOT SET")
4. ✅ `AZURE_BLOB_LOGGING_ENABLED` shows `'True' -> True`
5. ✅ See `[AZURE BLOB] Checking configuration...` message
6. ✅ See `[AZURE BLOB] Logging to Azure Blob: ...` message

## Still Not Working?

1. **Check the exact error messages** in log stream
2. **Verify environment variables** are saved (click Save in Azure Portal)
3. **Wait 2-3 minutes** after saving for app to restart
4. **Check if app restarted** - you should see startup messages
5. **Run diagnostic script**: Upload `test_azure_blob_logging.py` and run it

## Expected Full Output

When everything is configured correctly, you should see:

```
[CONFIG] Azure Blob Storage Configuration:
[CONFIG]   AZURE_BLOB_ACCOUNT_NAME = 's0001strangle' (SET)
[CONFIG]   AzureBlobStorageKey = SET
[CONFIG]   AZURE_BLOB_CONTAINER_NAME = 's0001strangle' (SET)
[CONFIG]   AZURE_BLOB_LOGGING_ENABLED = 'True' -> True
[AZURE BLOB] Checking configuration...
[AZURE BLOB] AZURE_BLOB_LOGGING_ENABLED = True
[AZURE BLOB] Connection string available: True
[AZURE BLOB] Container name: s0001strangle
[AZURE BLOB] Logging to Azure Blob: s0001strangle/logs/trading_2025Dec13.log
[AZURE BLOB] Azure Blob Storage logging initialized: s0001strangle/logs/trading_2025Dec13.log
[AZURE BLOB] Successfully uploaded X bytes to s0001strangle/logs/trading_2025Dec13.log
```

If you see all of these, logging is working! Check your container after 30 seconds.

