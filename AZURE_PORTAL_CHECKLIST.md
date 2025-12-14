# Azure Portal Configuration Checklist

## Quick Check in Azure Portal

Go to your App Service: **S00001**

### Step 1: Open Configuration

1. In Azure Portal, navigate to your App Service
2. Click **Configuration** in the left menu
3. Click **Application settings** tab

### Step 2: Verify These 4 Settings

Check each setting below. If any are missing or incorrect, click **+ New application setting** or click to edit:

#### ✅ Setting 1: AzureBlobStorageKey
- **Name:** `AzureBlobStorageKey`
- **Value:** Your storage account access key
- **Status:** Should be SET
- **How to get:** Storage Account > Access keys > Show key1

#### ✅ Setting 2: AZURE_BLOB_ACCOUNT_NAME
- **Name:** `AZURE_BLOB_ACCOUNT_NAME`
- **Value:** `s0001strangle` (your storage account name)
- **Status:** Should be SET
- **Note:** This is the storage account name, not the container name

#### ✅ Setting 3: AZURE_BLOB_CONTAINER_NAME
- **Name:** `AZURE_BLOB_CONTAINER_NAME`
- **Value:** `s0001strangle` (your container name)
- **Status:** Should be SET
- **Note:** Make sure it's exactly `s0001strangle` (not `s0001strangle-log`)

#### ✅ Setting 4: AZURE_BLOB_LOGGING_ENABLED
- **Name:** `AZURE_BLOB_LOGGING_ENABLED`
- **Value:** `True` (must be exactly "True", case-sensitive)
- **Status:** Should be SET to `True`
- **Common mistakes:**
  - ❌ `true` (lowercase)
  - ❌ `"True"` (with quotes)
  - ❌ `TRUE` (all caps)
  - ✅ `True` (correct)

### Step 3: Save and Restart

1. Click **Save** at the top
2. Wait 2-3 minutes for app to restart
3. Check Log Stream for diagnostic messages

## Run Diagnostic Script

After checking Azure Portal, run the diagnostic script:

1. Go to **SSH** or **Console** in your App Service
2. Run:
   ```bash
   python check_azure_blob_config.py
   ```

This will show you exactly what's missing or incorrect.

## Expected Output (When Working)

```
✓ AzureBlobStorageKey              = SET
✓ AZURE_BLOB_ACCOUNT_NAME          = 's0001strangle' (SET)
✓ AZURE_BLOB_CONTAINER_NAME        = 's0001strangle' (SET)
✓ AZURE_BLOB_LOGGING_ENABLED       = 'True' -> True
✓ Connection string can be constructed
✓ Logging is ENABLED
```

## Common Issues

### Issue 1: "Azure Blob Storage logging not available"
**Cause:** Environment variables not set or incorrect
**Fix:** Add all 4 settings in Azure Portal

### Issue 2: Container name shows `s0001strangle-log`
**Cause:** `AZURE_BLOB_CONTAINER_NAME` is set incorrectly
**Fix:** Change to exactly `s0001strangle`

### Issue 3: Logging disabled
**Cause:** `AZURE_BLOB_LOGGING_ENABLED` is not `True`
**Fix:** Set to exactly `True` (case-sensitive)

## After Fixing

1. Wait 2-3 minutes for app restart
2. Start a new trading strategy
3. Check Log Stream for:
   ```
   [AZURE BLOB] Checking configuration...
   [AZURE BLOB] Logging to Azure Blob: s0001strangle/Priti/logs/Priti_2025Dec14.log
   ```
4. Wait 30+ seconds, then check blob container

