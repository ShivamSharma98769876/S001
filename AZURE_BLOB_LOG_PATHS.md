# Azure Blob Storage Log File Paths

## Storage Account Information

- **Storage Account Name:** `s0001str`
- **Container Name:** `s0001strangle`
- **Base URL:** `https://s0001str.blob.core.windows.net/s0001strangle/`

## Log File Paths

### 1. Dashboard Logs (No Account Name)

**Path in Container:**
```
logs/trading_YYYYMonDD.log
```

**Example:**
```
logs/trading_2025Dec14.log
```

**Full Azure Blob URL:**
```
https://s0001str.blob.core.windows.net/s0001strangle/logs/trading_2025Dec14.log
```

**When Created:**
- When dashboard starts (no account name provided)
- Contains dashboard initialization and configuration logs

---

### 2. Trading Strategy Logs (With Account Name)

**Path in Container:**
```
{AccountName}/logs/{AccountName}_YYYYMonDD.log
```

**Example for "Priti Sharma":**
```
Priti/logs/Priti_2025Dec14.log
```

**Full Azure Blob URL:**
```
https://s0001str.blob.core.windows.net/s0001strangle/Priti/logs/Priti_2025Dec14.log
```

**When Created:**
- When trading strategy starts with account name "Priti Sharma"
- Contains all application logs: `[FLOW]`, `[EXPIRY]`, `[LOG]`, etc.

---

## How to Access Logs

### Option 1: Azure Portal

1. Go to **Storage accounts** → `s0001str`
2. Click **Containers** → `s0001strangle`
3. Navigate to the folder:
   - For dashboard: `logs/`
   - For strategy: `Priti/logs/`
4. Click on the log file to view/download

### Option 2: Azure Storage Explorer

1. Connect to storage account `s0001str`
2. Open container `s0001strangle`
3. Navigate to:
   - `logs/trading_2025Dec14.log` (dashboard)
   - `Priti/logs/Priti_2025Dec14.log` (strategy)

### Option 3: Direct URL

Use the full Azure Blob URLs above (requires authentication)

---

## Current Status

Based on your logs:

✅ **Dashboard logs ARE being written:**
- Path: `s0001strangle/logs/trading_2025Dec14.log`
- Status: Working (you can see uploads in log stream)

❌ **Trading strategy logs NOT yet created:**
- Path: `s0001strangle/Priti/logs/Priti_2025Dec14.log`
- Status: Will be created when you start the trading strategy

---

## Date Format

Log files use format: `YYYYMonDD`
- `YYYY` = 4-digit year (e.g., 2025)
- `Mon` = 3-letter month (e.g., Dec)
- `DD` = 2-digit day (e.g., 14)

Example: `2025Dec14.log` = December 14, 2025

---

## Summary

**To find your logs:**

1. **Dashboard logs:** `s0001strangle/logs/trading_2025Dec14.log` ✅ (already exists)
2. **Strategy logs:** `s0001strangle/Priti/logs/Priti_2025Dec14.log` (will appear after starting strategy)

**In Azure Portal:**
- Storage Account: `s0001str`
- Container: `s0001strangle`
- Navigate to the paths above

