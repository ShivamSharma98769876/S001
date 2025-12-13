# How Application Logs are Stored in Azure App Service

This guide explains how your trading bot application stores logs when running on Azure App Service.

---

## 📋 Overview: Three Log Storage Locations

Your application uses **three different methods** to store logs in Azure:

1. **Azure App Service Log Stream** (Real-time console output)
2. **Local File System** (`/tmp/{account_name}/logs/`)
3. **Azure Blob Storage** (Persistent cloud storage)

---

## 1️⃣ Azure App Service Log Stream (Automatic)

### How it Works:
- Azure App Service **automatically captures** all output sent to `stdout` and `stderr`
- Your application uses Python's `logging.StreamHandler()` which writes to console
- These logs are immediately visible in Azure Portal's **Log Stream**

### Location:
- **Azure Portal** → Your App Service → **Log stream**
- Real-time streaming of console output

### Code Reference:
```python
# From src/environment.py - setup_azure_logging()
console_handler = logging.StreamHandler()  # Writes to stdout/stderr
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
```

### Characteristics:
- ✅ **Real-time** - See logs as they happen
- ✅ **Automatic** - No configuration needed
- ⚠️ **Temporary** - Logs are not persisted long-term
- ⚠️ **Limited retention** - Based on Azure App Service settings

---

## 2️⃣ Local File System Logs (`/tmp/`)

### How it Works:
- When running on Azure, logs are written to the **local file system** at `/tmp/{account_name}/logs/`
- Files are named: `{sanitized_account}_{date}.log` (e.g., `S0001_2025Dec12.log`)
- These files persist during the app's lifetime but are **lost when the app restarts**

### Location:
- **Path**: `/tmp/{account_name}/logs/{account_name}_{date}.log`
- **Example**: `/tmp/S0001/logs/S0001_2025Dec12.log`

### Access Methods:

#### Method 1: Azure Portal - Kudu Console
1. Go to Azure Portal → Your App Service
2. Click **Advanced Tools (Kudu)** → **Go**
3. Navigate to: `Debug console` → `CMD` or `PowerShell`
4. Browse to: `/tmp/{account_name}/logs/`
5. Download or view log files

#### Method 2: Azure Portal - Log Files Download
1. Go to Azure Portal → Your App Service → **App Service logs**
2. Enable **Application Logging (Filesystem)**: ON
3. Go to **Advanced Tools (Kudu)** → **LogFiles/Application/**
4. Download log files

#### Method 3: Azure CLI
```bash
# Download all logs
az webapp log download --name <your-app-name> --resource-group <your-rg> --log-file logs.zip

# View log files via SSH (if enabled)
az webapp ssh --name <your-app-name> --resource-group <your-rg>
```

### Code Reference:
```python
# From src/environment.py - get_log_directory()
if is_azure_environment():
    if account_name:
        sanitized_account = sanitize_account_name_for_filename(account_name)
        log_dir = os.path.join('/tmp', sanitized_account, 'logs')
    else:
        log_dir = '/tmp/logs'
```

### Characteristics:
- ✅ **Persistent** during app lifetime
- ✅ **Account-specific** - Separate logs per trading account
- ⚠️ **Lost on restart** - `/tmp` is cleared when app restarts
- ⚠️ **Limited space** - Depends on App Service plan

---

## 3️⃣ Azure Blob Storage (Persistent Cloud Storage)

### How it Works:
- Logs are **buffered in memory** (8KB buffer or 30 seconds)
- Periodically **uploaded to Azure Blob Storage**
- Stored with folder structure: `{account_name}/logs/{account_name}_{date}.log`

### Location:
- **Storage Account**: Your Azure Storage Account
- **Container**: Set by `AZURE_BLOB_CONTAINER_NAME` environment variable
- **Blob Path**: `{account_name}/logs/{account_name}_{date}.log`
- **Example**: `s0001strangle/logs/S0001/2025Dec12.log`

### Configuration Required:

You need to set these **environment variables** in Azure App Service:

1. **`AzureBlobStorageKey`** - Storage account access key
2. **`AZURE_BLOB_ACCOUNT_NAME`** - Storage account name (e.g., `s0001strangle`)
3. **`AZURE_BLOB_CONTAINER_NAME`** - Container name (e.g., `s0001strangle`)
4. **`AZURE_BLOB_LOGGING_ENABLED`** - Set to `True` to enable

### How to Configure:

1. Go to Azure Portal → Your App Service
2. Click **Configuration** → **Application settings**
3. Add these settings:
   ```
   AzureBlobStorageKey = <your-storage-account-key>
   AZURE_BLOB_ACCOUNT_NAME = <your-storage-account-name>
   AZURE_BLOB_CONTAINER_NAME = <your-container-name>
   AZURE_BLOB_LOGGING_ENABLED = True
   ```
4. Click **Save** (restarts the app)

### Access Methods:

#### Method 1: Azure Portal
1. Go to Azure Portal → **Storage accounts**
2. Select your storage account
3. Click **Containers** → Select your container
4. Navigate to: `{account_name}/logs/`
5. Download log files

#### Method 2: Azure Storage Explorer
1. Download [Azure Storage Explorer](https://azure.microsoft.com/features/storage-explorer/)
2. Connect to your storage account
3. Navigate to container → `{account_name}/logs/`
4. Download or view log files

#### Method 3: Azure CLI
```bash
# List blobs
az storage blob list --account-name <account-name> --account-key <key> \
    --container-name <container-name> --prefix "<account-name>/logs/"

# Download a blob
az storage blob download --account-name <account-name> --account-key <key> \
    --container-name <container-name> \
    --name "<account-name>/logs/<account-name>_2025Dec12.log" \
    --file "log.txt"
```

### Code Reference:
```python
# From src/environment.py - AzureBlobStorageHandler class
class AzureBlobStorageHandler(logging.Handler):
    def __init__(self, connection_string, container_name, blob_path, account_name=None):
        self.buffer = io.StringIO()  # In-memory buffer
        self.flush_interval = 30  # Flush every 30 seconds
        # ... uploads to blob storage
    
    def _flush_to_blob(self):
        # Uploads buffered logs to Azure Blob Storage
        # Appends to existing blob or creates new one
```

### Characteristics:
- ✅ **Persistent** - Logs survive app restarts
- ✅ **Scalable** - Unlimited storage capacity
- ✅ **Account-specific** - Organized by account name
- ✅ **Date-based** - Separate file per day
- ⚠️ **Requires configuration** - Must set environment variables
- ⚠️ **Buffered** - Logs uploaded every 30 seconds or 8KB

---

## 🔄 Log Flow Diagram

```
Application Code
    │
    ├─→ Console Handler (stdout/stderr)
    │       │
    │       └─→ Azure Log Stream (Real-time)
    │
    ├─→ File Handler
    │       │
    │       └─→ /tmp/{account}/logs/{account}_{date}.log
    │
    └─→ Azure Blob Handler (if enabled)
            │
            ├─→ Buffer (8KB or 30 seconds)
            │
            └─→ Azure Blob Storage
                    └─→ {container}/{account}/logs/{account}_{date}.log
```

---

## 📊 Comparison Table

| Feature | Log Stream | File System | Blob Storage |
|---------|-----------|-------------|--------------|
| **Real-time** | ✅ Yes | ❌ No | ❌ No (30s delay) |
| **Persistent** | ❌ No | ⚠️ During app lifetime | ✅ Yes |
| **Survives Restart** | ❌ No | ❌ No | ✅ Yes |
| **Account-specific** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Configuration** | ✅ Automatic | ✅ Automatic | ⚠️ Requires setup |
| **Storage Limit** | N/A | Limited (App Service) | Unlimited |
| **Access Method** | Portal Log Stream | Kudu/SSH | Portal/Storage Explorer |

---

## 🛠️ Setup Instructions

### Step 1: Enable App Service Logging
1. Azure Portal → Your App Service → **App Service logs**
2. Enable:
   - ✅ **Application Logging (Filesystem)**: ON
   - ✅ **Detailed Error Messages**: ON
   - ✅ **Failed Request Tracing**: ON
3. Set **Retention Period**: 7 days (or as needed)
4. Click **Save**

### Step 2: Configure Azure Blob Storage (Optional but Recommended)
1. Azure Portal → Your App Service → **Configuration** → **Application settings**
2. Add:
   ```
   AzureBlobStorageKey = <your-storage-key>
   AZURE_BLOB_ACCOUNT_NAME = <your-storage-account>
   AZURE_BLOB_CONTAINER_NAME = <your-container>
   AZURE_BLOB_LOGGING_ENABLED = True
   ```
3. Click **Save**

### Step 3: Verify Logging
1. Check **Log Stream** - Should see real-time logs
2. Check **Kudu** → `/tmp/{account}/logs/` - Should see log files
3. Check **Blob Storage** → `{account}/logs/` - Should see uploaded logs (if enabled)

---

## 🔍 Troubleshooting

### No logs in Log Stream
- Check if app is running
- Verify logging is enabled in App Service logs settings
- Check application code for errors

### No logs in `/tmp/`
- Verify account name is provided
- Check file permissions
- App may have restarted (logs cleared)

### No logs in Blob Storage
- Verify environment variables are set correctly
- Check `AZURE_BLOB_LOGGING_ENABLED = True`
- Verify storage account key is correct
- Check container exists and is accessible
- Wait 30 seconds for buffer to flush

### Logs missing after app restart
- **File system logs** (`/tmp/`) are cleared on restart - this is expected
- **Blob Storage logs** should persist - check blob storage
- **Log Stream** only shows current session

---

## 📝 Log File Naming Convention

### File System:
- Format: `{sanitized_account}_{date}.log`
- Example: `S0001_2025Dec12.log`
- Location: `/tmp/{account}/logs/`

### Blob Storage:
- Format: `{sanitized_account}/logs/{sanitized_account}_{date}.log`
- Example: `S0001/logs/S0001_2025Dec12.log`
- Location: `{container}/{account}/logs/`

### Date Format:
- Format: `YYYYMonDD` (e.g., `2025Dec12`)
- Example: December 12, 2025 = `2025Dec12`

---

## 💡 Best Practices

1. **Enable all three logging methods** for comprehensive coverage
2. **Use Blob Storage** for long-term log retention
3. **Monitor Log Stream** for real-time debugging
4. **Set appropriate retention periods** to manage costs
5. **Rotate storage account keys** regularly for security
6. **Use account-specific folders** to organize logs by trading account

---

## 🔐 Security Notes

- **Storage account keys** are stored as environment variables (secure)
- **Never commit keys** to Git (use environment variables)
- **Rotate keys** if exposed (see `ROTATE_AZURE_KEY_GUIDE.md`)
- **Use Azure Key Vault** for production (advanced)

---

## 📚 Related Documentation

- `AZURE_DEPLOYMENT.md` - Full deployment guide
- `ROTATE_AZURE_KEY_GUIDE.md` - How to rotate storage account keys
- `env_example.txt` - Environment variable examples

