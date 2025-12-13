# Complete Guide: Setting Up Azure Blob Storage for Application Logs

This guide provides step-by-step instructions for configuring Azure Blob Storage to store your application logs in Azure App Service.

---

## 📋 Prerequisites

- Azure subscription
- Azure App Service already deployed
- Access to Azure Portal

---

## Step 1: Create Azure Storage Account

### 1.1 Navigate to Storage Accounts

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **"Create a resource"** (or search for "Storage account")
3. Search for **"Storage account"** and select it
4. Click **"Create"**

### 1.2 Configure Storage Account

Fill in the following details:

**Basics Tab:**
- **Subscription**: Select your subscription
- **Resource group**: Select existing or create new (e.g., `trading-bot-rg`)
- **Storage account name**: 
  - Must be globally unique
  - 3-24 characters, lowercase letters and numbers only
  - Example: `s0001stranglelogs` or `tradingbotlogs`
- **Region**: Select same region as your App Service (recommended)
- **Performance**: 
  - **Standard** (recommended for logs)
- **Redundancy**: 
  - **LRS** (Locally Redundant Storage) - cheapest option
  - Or **GRS** (Geo-Redundant Storage) for backup

Click **"Review + create"** → **"Create"**

### 1.3 Wait for Deployment

Wait 1-2 minutes for the storage account to be created.

---

## Step 2: Create Container in Storage Account

### 2.1 Open Storage Account

1. Go to **"Storage accounts"** in Azure Portal
2. Click on your newly created storage account

### 2.2 Create Container

1. In the left menu, under **"Data storage"**, click **"Containers"**
2. Click **"+ Container"**
3. Fill in:
   - **Name**: 
     - Lowercase, numbers, and hyphens only
     - Example: `trading-logs` or `s0001strangle`
   - **Public access level**: **Private** (no anonymous access)
4. Click **"Create"**

---

## Step 3: Get Storage Account Access Key

### 3.1 Navigate to Access Keys

1. In your Storage Account, go to **"Security + networking"** → **"Access keys"**
2. You'll see two keys: **key1** and **key2**

### 3.2 Copy the Key

1. Click the **"Show"** button next to **key1** (or key2)
2. Click the **copy icon** to copy the key
3. **Save it securely** - you'll need it in the next step

**⚠️ Important**: Keep this key secure. It provides full access to your storage account.

---

## Step 4: Configure Azure App Service Environment Variables

### 4.1 Navigate to App Service Configuration

1. Go to **"App Services"** in Azure Portal
2. Click on your App Service (your trading bot app)
3. In the left menu, click **"Configuration"**
4. Click on the **"Application settings"** tab

### 4.2 Add Environment Variables

Click **"+ New application setting"** and add the following **4 settings**:

#### Setting 1: Storage Account Name
- **Name**: `AZURE_BLOB_ACCOUNT_NAME`
- **Value**: Your storage account name (e.g., `s0001stranglelogs`)
- Click **"OK"**

#### Setting 2: Storage Account Key
- **Name**: `AzureBlobStorageKey`
- **Value**: The key you copied in Step 3.2 (e.g., `2/ISQ/w7iTwGLYkGTc5h9Ly4rso1IKwADrcGqQnRvLsaNCryk4duOKUgJawXhXBuDdN0MJhM0a73+AStu/d6UA==`)
- Click **"OK"**

#### Setting 3: Container Name
- **Name**: `AZURE_BLOB_CONTAINER_NAME`
- **Value**: The container name you created (e.g., `trading-logs`)
- Click **"OK"**

#### Setting 4: Enable Logging
- **Name**: `AZURE_BLOB_LOGGING_ENABLED`
- **Value**: `True`
- Click **"OK"**

### 4.3 Save Configuration

1. Click **"Save"** at the top of the page
2. Click **"Continue"** when prompted
3. Wait for the app to restart (this happens automatically)

---

## Step 5: Verify Code Configuration

### 5.1 Check config.py

The code should already have Azure Blob Storage configuration. Verify `src/config.py` contains:

```python
# Azure Blob Storage Configuration for Logs
AZURE_BLOB_ACCOUNT_NAME = os.getenv('AZURE_BLOB_ACCOUNT_NAME', '')
AZURE_BLOB_STORAGE_KEY = os.getenv('AzureBlobStorageKey', '')
AZURE_BLOB_CONTAINER_NAME = os.getenv('AZURE_BLOB_CONTAINER_NAME', '')
AZURE_BLOB_LOGGING_ENABLED = os.getenv('AZURE_BLOB_LOGGING_ENABLED', 'False').lower() == 'true'

# Construct connection string
if AZURE_BLOB_ACCOUNT_NAME and AZURE_BLOB_STORAGE_KEY:
    AZURE_BLOB_CONNECTION_STRING = (
        f"DefaultEndpointsProtocol=https;"
        f"AccountName={AZURE_BLOB_ACCOUNT_NAME};"
        f"AccountKey={AZURE_BLOB_STORAGE_KEY};"
        f"EndpointSuffix=core.windows.net"
    )
else:
    AZURE_BLOB_CONNECTION_STRING = None
```

### 5.2 Verify environment.py

The `src/environment.py` file should already have:
- `AzureBlobStorageHandler` class
- `setup_azure_blob_logging()` function
- Integration in `setup_azure_logging()` function

**✅ No code changes needed** - the code is already set up!

---

## Step 6: Deploy Updated Code (if needed)

### 6.1 Commit and Push Changes

If you made any changes to `config.py`:

```powershell
# Check status
git status

# Add changes
git add src/config.py

# Commit
git commit -m "Add Azure Blob Storage configuration"

# Push to prod branch
git push origin prod
```

### 6.2 Verify Deployment

1. Go to Azure Portal → Your App Service → **"Deployment Center"**
2. Verify your latest commit is deployed
3. Check **"Logs"** to see deployment status

---

## Step 7: Verify Logging is Working

### 7.1 Check Application Logs

1. Go to Azure Portal → Your App Service → **"Log stream"**
2. Look for messages like:
   ```
   [AZURE BLOB] Logging to Azure Blob: trading-logs/S0001/logs/S0001_2025Dec13.log
   ```

### 7.2 Check Blob Storage

1. Go to Azure Portal → **"Storage accounts"** → Your storage account
2. Click **"Containers"** → Your container name
3. You should see folders like:
   - `S0001/logs/` (if account name is provided)
   - `logs/` (if no account name)
4. Inside, you should see log files like:
   - `S0001_2025Dec13.log`
   - `trading_2025Dec13.log`

### 7.3 Download and View Logs

1. Click on a log file
2. Click **"Download"** to download the log file
3. Open it in a text editor to view logs

---

## Step 8: Troubleshooting

### Issue: No logs appearing in Blob Storage

**Check 1: Environment Variables**
- Go to App Service → **Configuration** → **Application settings**
- Verify all 4 variables are set correctly
- Check for typos in variable names

**Check 2: Application Logs**
- Go to **Log stream** and look for error messages
- Look for: `[AZURE BLOB] Warning:` messages

**Check 3: Container Name**
- Verify container name matches exactly (case-sensitive)
- Container name should be lowercase

**Check 4: Storage Account Key**
- Verify the key is correct (no extra spaces)
- Try regenerating the key if needed

### Issue: "Connection string not available"

**Solution:**
- Verify `AZURE_BLOB_ACCOUNT_NAME` and `AzureBlobStorageKey` are set
- Restart the App Service after setting variables

### Issue: "Container does not exist"

**Solution:**
- The code automatically creates the container
- If it fails, manually create it in Azure Portal
- Check container name spelling

### Issue: Logs not uploading

**Check:**
- Logs are buffered and uploaded every 30 seconds or when buffer reaches 8KB
- Wait at least 30 seconds after application starts
- Check application is actually generating logs

---

## Step 9: Monitor and Maintain

### 9.1 View Logs Regularly

1. Go to Storage Account → Containers → Your container
2. Browse log files by date
3. Download and analyze as needed

### 9.2 Set Up Lifecycle Management (Optional)

To automatically delete old logs:

1. Go to Storage Account → **"Lifecycle management"**
2. Click **"+ Add a rule"**
3. Configure:
   - **Rule name**: `Delete old logs`
   - **Blob type**: **Block blobs**
   - **Blob prefix**: `logs/` (or your container path)
   - **Action**: **Move to cool/archive tier** or **Delete**
   - **Days after last modification**: `30` (or as needed)
4. Click **"Create"**

### 9.3 Monitor Storage Costs

- Go to Storage Account → **"Cost analysis"**
- Monitor storage usage
- Logs are typically small, but monitor if you have many accounts

---

## 📊 Summary of Configuration

### Environment Variables in Azure App Service:

| Variable Name | Example Value | Description |
|--------------|---------------|-------------|
| `AZURE_BLOB_ACCOUNT_NAME` | `s0001stranglelogs` | Storage account name |
| `AzureBlobStorageKey` | `2/ISQ/w7iTw...` | Storage account access key |
| `AZURE_BLOB_CONTAINER_NAME` | `trading-logs` | Container name for logs |
| `AZURE_BLOB_LOGGING_ENABLED` | `True` | Enable/disable blob logging |

### Log File Structure:

```
Container: trading-logs
  └── S0001/
      └── logs/
          └── S0001_2025Dec13.log
```

Or if no account name:
```
Container: trading-logs
  └── logs/
      └── trading_2025Dec13.log
```

### Log Upload Behavior:

- **Buffer size**: 8KB or 30 seconds (whichever comes first)
- **Upload frequency**: Every 30 seconds
- **Format**: Appends to existing blob or creates new one
- **Encoding**: UTF-8

---

## ✅ Verification Checklist

- [ ] Storage account created
- [ ] Container created
- [ ] Access key copied
- [ ] All 4 environment variables set in App Service
- [ ] App Service restarted
- [ ] Code deployed (if changes made)
- [ ] Logs appearing in Blob Storage
- [ ] Can download and view log files

---

## 🔐 Security Best Practices

1. **Rotate keys regularly** - Regenerate storage account keys periodically
2. **Use Private containers** - Never set container to public access
3. **Monitor access** - Check Storage Account logs for suspicious activity
4. **Use Azure Key Vault** (Advanced) - Store keys in Key Vault instead of App Settings
5. **Limit access** - Use SAS tokens for specific access if needed

---

## 📚 Additional Resources

- [Azure Blob Storage Documentation](https://docs.microsoft.com/azure/storage/blobs/)
- [Azure App Service Configuration](https://docs.microsoft.com/azure/app-service/configure-common)
- [Azure Storage Pricing](https://azure.microsoft.com/pricing/details/storage/)

---

## 🆘 Need Help?

If you encounter issues:

1. Check **Log stream** in App Service for error messages
2. Verify all environment variables are set correctly
3. Check Storage Account → **"Access keys"** to verify key is valid
4. Review the troubleshooting section above

---

**Last Updated**: December 2025

