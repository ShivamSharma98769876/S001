# Azure Log File Locations

## Trading Strategy Logs (The logs you're seeing)

These logs contain:
- `[FLOW]` messages
- `[EXPIRY]` messages  
- `ATM strike`, `Finding strikes`, etc.
- All trading activity

### Location in Azure Blob Storage

**Container:** `s0001strangle`

**Path:** `{AccountName}/logs/{AccountName}_{Date}.log`

**Example:**
- Account: "Priti Sharma"
- Date: 2025-12-14
- **Full Path:** `Priti/logs/Priti_2025Dec14.log`
- **Full URL:** `https://s0001str.blob.core.windows.net/s0001strangle/Priti/logs/Priti_2025Dec14.log`

### How to Access

1. **Azure Portal:**
   - Go to **Storage accounts** → `s0001str`
   - Click **Containers** → `s0001strangle`
   - Navigate to **`Priti/logs/`** folder
   - Click on **`Priti_2025Dec14.log`** to view/download

2. **Path Structure:**
   ```
   s0001strangle/
   └── Priti/
       └── logs/
           └── Priti_2025Dec14.log  ← Your trading strategy logs are here
   ```

### Local Filesystem (Temporary)

In Azure App Service, logs are also written to:
- **Path:** `/tmp/Priti/logs/Priti_2025Dec14.log`
- **Note:** This is temporary storage and may be cleared on restart
- **Primary Location:** Azure Blob Storage (persistent)

## Dashboard Logs

**Path:** `s0001strangle/logs/trading_2025Dec14.log`

These are dashboard initialization logs (no account name).

## Summary

Your trading strategy logs (`[FLOW]`, `[EXPIRY]`, etc.) are in:
- **Azure Blob:** `s0001strangle/Priti/logs/Priti_2025Dec14.log`
- **Local (temp):** `/tmp/Priti/logs/Priti_2025Dec14.log`

The account name "Priti Sharma" is sanitized to "Priti" for the folder name.

