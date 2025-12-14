# Where to Set Environment Variables in Azure Portal

## ✅ Correct Location

**Path:** App Service → **Configuration** → **Application settings**

OR

**Path:** App Service → **Settings** → **Configuration** → **Application settings**

Both paths lead to the same place! ✅

## Step-by-Step Navigation

1. **Go to Azure Portal**
   - Navigate to your App Service: **S00001**

2. **Open Configuration**
   - Click **Configuration** in the left menu (under Settings section)
   - OR click **Settings** → **Configuration**

3. **Open Application Settings Tab**
   - Click the **Application settings** tab at the top
   - This is where you add/edit environment variables

4. **Add/Edit Settings**
   - Click **+ New application setting** to add a new one
   - OR click on an existing setting to edit it

## Required Settings

Add these 4 settings in **Application settings**:

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

## Important Notes

1. **Case-Sensitive Names**: The setting names must match exactly (case-sensitive)
2. **Case-Sensitive Values**: `AZURE_BLOB_LOGGING_ENABLED` must be exactly `True` (capital T)
3. **No Quotes**: Don't put quotes around the values
4. **Save Required**: Click **Save** at the top after adding/editing settings

## After Saving

1. Azure will automatically restart your app
2. Wait 2-3 minutes for restart to complete
3. Check Log Stream for diagnostic messages

## Alternative Names You Might See

The tab might be labeled as:
- **Application settings** (most common)
- **App settings**
- **Environment variables**
- **Configuration settings**

All of these refer to the same place! ✅

## Verification

After setting, you can verify by:
1. Running the diagnostic script: `python check_azure_blob_config.py`
2. Checking Log Stream for `[AZURE BLOB]` messages
3. Looking for logs in your blob container

