# Troubleshooting Azure Blob Storage Logging

## Issue: Logs Not Appearing in Container

### Step 1: Verify Environment Variables

In Azure Portal, go to your App Service:
1. **Configuration** > **Application settings**
2. Verify these are set:
   - `AzureBlobStorageKey` - Your storage account key
   - `AZURE_BLOB_ACCOUNT_NAME` - Storage account name (e.g., `s0001strangle`)
   - `AZURE_BLOB_CONTAINER_NAME` - Container name (e.g., `s0001strangle`)
   - `AZURE_BLOB_LOGGING_ENABLED` - Set to `True`

### Step 2: Run Diagnostic Script

Upload and run the diagnostic script in Azure:

```bash
# In Azure App Service SSH/Console
python test_azure_blob_logging.py
```

This will check:
- Environment variables
- Connection string construction
- Container existence
- Blob creation

### Step 3: Check Application Logs

View logs in Azure Portal:
1. Go to **Log stream** or **Logs**
2. Look for messages starting with `[AZURE BLOB]`
3. Check for any error messages

### Step 4: Common Issues

#### Issue 1: Environment Variables Not Set
**Symptom**: `[AZURE BLOB] Warning: Azure Blob Storage connection string not available`

**Fix**: Set all required environment variables in Azure Portal

#### Issue 2: Container Doesn't Exist
**Symptom**: `Container exists: False`

**Fix**: The code should create it automatically, but you can create manually:
- Azure Portal > Storage Account > Containers > Create

#### Issue 3: Invalid Connection String
**Symptom**: `Error flushing to blob: Authentication failed`

**Fix**: 
- Verify `AzureBlobStorageKey` is correct
- Verify `AZURE_BLOB_ACCOUNT_NAME` matches the storage account
- Check that the key has proper permissions

#### Issue 4: Logs Buffered (Not Flushed Yet)
**Symptom**: No errors, but no logs in container

**Fix**: 
- Logs are flushed every 30 seconds or when buffer exceeds 8KB
- Wait a few minutes and check again
- Or trigger a flush by restarting the app

### Step 5: Manual Test

Test the connection manually:

```python
from azure.storage.blob import BlobServiceClient
import os

# Get from environment
connection_string = f"DefaultEndpointsProtocol=https;AccountName={os.getenv('AZURE_BLOB_ACCOUNT_NAME')};AccountKey={os.getenv('AzureBlobStorageKey')};EndpointSuffix=core.windows.net"
container_name = os.getenv('AZURE_BLOB_CONTAINER_NAME')

# Test connection
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

# List blobs
blobs = list(container_client.list_blobs())
print(f"Found {len(blobs)} blobs")
for blob in blobs:
    print(f"  - {blob.name}")
```

### Step 6: Check Blob Path

Logs are stored with this structure:
- `{account_name}/logs/{account_name}_{date}.log`
- Example: `John/logs/John_2025Dec13.log`

Make sure you're looking in the right folder in the container.

### Step 7: Enable Debug Logging

Add this to see more details:

```python
import logging
logging.getLogger('azure.storage').setLevel(logging.DEBUG)
```

### Step 8: Force Immediate Flush

If you want to see logs immediately, you can modify the flush interval:

In `src/environment.py`, change:
```python
self.flush_interval = 30  # Change to 5 for testing
```

Or call `blob_handler.flush()` manually after logging.

## Quick Checklist

- [ ] Environment variables set in Azure Portal
- [ ] `AZURE_BLOB_LOGGING_ENABLED=True`
- [ ] Container exists (or can be created)
- [ ] Storage account key is valid
- [ ] Application is logging (check console logs)
- [ ] Waited at least 30 seconds for flush
- [ ] Checked correct folder path in container

## Still Not Working?

1. Check Azure Portal > Storage Account > Activity log for errors
2. Verify storage account firewall allows App Service access
3. Check App Service logs for detailed error messages
4. Run the diagnostic script and share the output

