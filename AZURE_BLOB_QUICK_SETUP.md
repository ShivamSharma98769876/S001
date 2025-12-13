# Quick Setup: Azure Blob Storage for Logs

## 🚀 Quick Steps (5 minutes)

### 1. Create Storage Account
- Azure Portal → **Create resource** → **Storage account**
- Name: `s0001stranglelogs` (or your choice)
- Click **Create**

### 2. Create Container
- Storage Account → **Containers** → **+ Container**
- Name: `trading-logs`
- Access: **Private**
- Click **Create**

### 3. Get Access Key
- Storage Account → **Access keys**
- Click **Show** next to **key1**
- **Copy the key** (save it)

### 4. Configure App Service
- App Service → **Configuration** → **Application settings**
- Add these 4 settings:

```
Name: AZURE_BLOB_ACCOUNT_NAME
Value: s0001stranglelogs

Name: AzureBlobStorageKey
Value: <paste the key you copied>

Name: AZURE_BLOB_CONTAINER_NAME
Value: trading-logs

Name: AZURE_BLOB_LOGGING_ENABLED
Value: True
```

- Click **Save** (app restarts automatically)

### 5. Verify
- Wait 1-2 minutes
- Storage Account → **Containers** → `trading-logs`
- You should see log files appear!

---

## ✅ Done!

Logs will now be stored in Azure Blob Storage automatically.

**See `AZURE_BLOB_SETUP_GUIDE.md` for detailed instructions.**

