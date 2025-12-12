# How to Rotate Azure Storage Account Key

## ⚠️ IMPORTANT: Your Azure Storage Account Key is Compromised

The key `AccountKey=2/ISQ/w7iTwGLYkGTc5h9Ly4rso1IKwADrcGqQnRvLsaNCryk4duOKUgJawXhXBuDdN0MJhM0a73+AStu/d6UA==` was exposed in your Git history and must be rotated immediately.

---

## Step-by-Step Instructions

### Step 1: Log into Azure Portal

1. Go to [https://portal.azure.com](https://portal.azure.com)
2. Sign in with your Azure account

### Step 2: Navigate to Your Storage Account

1. In the search bar at the top, type **"Storage accounts"**
2. Click on **"Storage accounts"** from the results
3. Find and click on your storage account (likely named something like `s0001strangle` or similar)

### Step 3: Access Access Keys

1. In the left menu of your Storage Account, scroll down to **"Security + networking"**
2. Click on **"Access keys"**
3. You'll see two keys: **key1** and **key2**

### Step 4: Regenerate the Key

**Option A: Regenerate key1 (if that's what you're using)**
1. Find the **key1** section
2. Click the **"Regenerate"** button (or the refresh icon) next to key1
3. Click **"Yes"** to confirm
4. **Copy the new key** immediately (you'll need it in the next step)

**Option B: Regenerate key2 (if that's what you're using)**
1. Find the **key2** section
2. Click the **"Regenerate"** button (or the refresh icon) next to key2
3. Click **"Yes"** to confirm
4. **Copy the new key** immediately (you'll need it in the next step)

**⚠️ Important**: Only regenerate the key you're currently using. If you're not sure which one, regenerate key1 (it's the default).

### Step 5: Update Azure App Service Configuration

After regenerating the key, you need to update your Azure App Service to use the new key:

1. In Azure Portal, go to **"App Services"** (search for it in the top bar)
2. Click on your App Service (your trading bot app)
3. In the left menu, click on **"Configuration"**
4. Under **"Application settings"**, find the setting named **`AzureBlobStorageKey`**
5. Click on the value to edit it
6. **Paste the new key** you copied in Step 4
7. Click **"OK"**
8. Click **"Save"** at the top of the page
9. Click **"Continue"** when prompted (this will restart your app)

### Step 6: Verify the Update

1. Wait a few minutes for the app to restart
2. Check your app's logs to ensure it's connecting to Azure Blob Storage successfully
3. Go to **"Log stream"** in your App Service to verify there are no errors

---

## Alternative: Using Azure CLI

If you prefer using command line:

```powershell
# Login to Azure
az login

# List your storage accounts to find the right one
az storage account list --query "[].{Name:name, ResourceGroup:resourceGroup}" --output table

# Regenerate key1 (replace with your storage account name and resource group)
az storage account keys renew --resource-group <your-resource-group> --name <your-storage-account-name> --key key1

# Get the new key
az storage account keys list --resource-group <your-resource-group> --name <your-storage-account-name> --query "[0].value" --output tsv

# Update App Service environment variable (replace with your app name and resource group)
az webapp config appsettings set --resource-group <your-resource-group> --name <your-app-name> --settings AzureBlobStorageKey="<new-key-value>"
```

---

## What Happens After Rotation?

1. **Old key stops working**: The old key will no longer work for accessing your storage account
2. **App Service uses new key**: Your app will use the new key from the environment variable
3. **Logging continues**: Azure Blob Storage logging will continue working with the new key
4. **Old key is invalid**: Anyone who had the old key can no longer access your storage account

---

## Security Best Practices

1. ✅ **Never commit keys to Git** - Always use environment variables or Azure Key Vault
2. ✅ **Rotate keys regularly** - Even if not compromised, rotate keys periodically
3. ✅ **Use Azure Key Vault** - For production, consider using Azure Key Vault instead of App Settings
4. ✅ **Monitor access** - Check Storage Account logs for suspicious activity
5. ✅ **Use separate keys** - Use key1 for one service and key2 for another, so you can rotate independently

---

## Troubleshooting

### App stops logging to Azure Blob Storage
- Verify the new key is correctly set in App Service Configuration
- Check that the key was copied completely (no missing characters)
- Restart the App Service after updating the key

### Can't find the Storage Account
- Check if you're in the correct Azure subscription
- Verify the storage account name matches what's in your code
- Check the `AZURE_BLOB_ACCOUNT_NAME` environment variable in your App Service

### Need to find which key you're using
- Check your App Service Configuration for `AzureBlobStorageKey`
- Compare it with key1 and key2 in the Storage Account Access Keys page

---

## Next Steps After Rotation

1. ✅ Verify your app is working correctly
2. ✅ Check that logs are being written to Azure Blob Storage
3. ✅ Monitor for any access errors
4. ✅ Consider setting up Azure Key Vault for better security management

