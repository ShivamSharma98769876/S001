# Azure Portal Configuration Guide

## Where to Set Environment Variables

**Location:** Azure Portal > Your App Service > **Configuration** > **Application settings** (or "App settings")

This is the correct place! ✅

## Required Application Settings

Add these settings in the **Application settings** tab:

### 1. Azure Blob Storage Key
- **Name:** `AzureBlobStorageKey`
- **Value:** Your Azure Storage Account access key
- **Example:** `2/ISQ/w7iTwGLYkGTc5h9Ly4rso1IKwADrcGqQnRvLsaNCryk4duOKUgJawXhXBuDdN0MJhM0a73+AStu/d6UA==`
- **Note:** This is the storage account key (not connection string)

### 2. Storage Account Name
- **Name:** `AZURE_BLOB_ACCOUNT_NAME`
- **Value:** Your storage account name
- **Example:** `s0001strangle`

### 3. Container Name
- **Name:** `AZURE_BLOB_CONTAINER_NAME`
- **Value:** Your container name
- **Example:** `s0001strangle`

### 4. Enable Logging
- **Name:** `AZURE_BLOB_LOGGING_ENABLED`
- **Value:** `True` (must be exactly "True", case-sensitive)
- **Important:** This must be set to `True` for logging to work!

## Step-by-Step Instructions

1. **Go to Azure Portal**
   - Navigate to your App Service

2. **Open Configuration**
   - Click on **Configuration** in the left menu
   - Click on **Application settings** tab (or "App settings")

3. **Add/Edit Settings**
   - Click **+ New application setting** for each setting
   - Or click on existing setting to edit

4. **Add Each Setting:**
   ```
   Name: AzureBlobStorageKey
   Value: <your-storage-account-key>
   
   Name: AZURE_BLOB_ACCOUNT_NAME
   Value: s0001strangle
   
   Name: AZURE_BLOB_CONTAINER_NAME
   Value: s0001strangle
   
   Name: AZURE_BLOB_LOGGING_ENABLED
   Value: True
   ```

5. **Save**
   - Click **Save** at the top
   - Azure will restart your app automatically

## How to Get Storage Account Key

1. Go to **Storage accounts** in Azure Portal
2. Click on your storage account (e.g., `s0001strangle`)
3. Go to **Access keys** in the left menu
4. Click **Show** next to `key1` or `key2`
5. Copy the key value

## Verification

After saving, check the logs:

1. Go to **Log stream** in your App Service
2. Look for messages like:
   ```
   [AZURE BLOB] Logging to Azure Blob: s0001strangle/logs/trading_2025Dec13.log
   [AZURE BLOB] Azure Blob Storage logging initialized: ...
   ```

If you see these messages, logging is configured correctly!

## Common Mistakes

❌ **Wrong:** `AZURE_BLOB_LOGGING_ENABLED = true` (lowercase)
✅ **Correct:** `AZURE_BLOB_LOGGING_ENABLED = True` (capital T)

❌ **Wrong:** Setting connection string instead of just the key
✅ **Correct:** Set `AzureBlobStorageKey` with just the key value

❌ **Wrong:** Using different names (e.g., `AZURE_BLOB_KEY`)
✅ **Correct:** Use exact names: `AzureBlobStorageKey`, `AZURE_BLOB_ACCOUNT_NAME`, etc.

## Screenshot Reference

The Application settings page should look like this:

```
Application settings
├── AzureBlobStorageKey = <your-key>
├── AZURE_BLOB_ACCOUNT_NAME = s0001strangle
├── AZURE_BLOB_CONTAINER_NAME = s0001strangle
└── AZURE_BLOB_LOGGING_ENABLED = True
```

## After Configuration

1. **Wait 1-2 minutes** for the app to restart
2. **Check Log stream** for `[AZURE BLOB]` messages
3. **Wait 30+ seconds** for first log flush
4. **Check container** in Storage Account for log files

