# Troubleshoot: Trading Strategy Logs Not Appearing

## Current Situation

✅ **Environment variables are set correctly** (diagnostic script confirms)
❌ **No `[STRATEGY]` messages in Log Stream**
❌ **No `[AZURE BLOB]` messages from trading strategy**

## What This Means

The log stream only shows dashboard logs (`[LOGS]`), which means:
1. **Trading strategy may not be running** - OR
2. **Strategy output isn't being captured** - OR  
3. **Code with diagnostics hasn't been deployed yet**

## Step 1: Check if Strategy is Running

1. Go to your dashboard: `http://your-app-url/live/`
2. Check the **Live Trader Status** section
3. Look for:
   - **Engine Status**: Should show "Running" or "Stopped"
   - **Process ID**: Should show a number if running

## Step 2: Start a New Trading Strategy

If the strategy is not running:

1. Go to **Live Trader** page in dashboard
2. Enter your credentials and quantities
3. Click **Start Live Trader**
4. Wait 10-15 seconds
5. Check Log Stream for `[STRATEGY]` messages

## Step 3: Check Log Stream for Strategy Messages

After starting the strategy, you should see messages like:

```
[STRATEGY] [SETUP LOGGING] Starting logging setup - account_name=Priti Sharma
[STRATEGY] [SETUP LOGGING] Azure environment detected
[STRATEGY] [LOG SETUP] Setting up Azure Blob Storage logging for account: Priti Sharma
[STRATEGY] [AZURE BLOB] Checking configuration...
[STRATEGY] [AZURE BLOB] AZURE_BLOB_LOGGING_ENABLED = True
[STRATEGY] [AZURE BLOB] Connection string available: True
[STRATEGY] [AZURE BLOB] Container name: s0001strangle
[STRATEGY] [AZURE BLOB] Logging to Azure Blob: s0001strangle/Priti/logs/Priti_2025Dec14.log
```

## Step 4: If No [STRATEGY] Messages Appear

This could mean:

### Option A: Code Not Deployed
- The updated code with diagnostic messages hasn't been deployed
- **Fix**: Deploy the latest code to Azure

### Option B: Strategy Not Starting
- The strategy subprocess is failing to start
- **Check**: Look for error messages in Log Stream
- **Check**: Verify strategy file exists and is executable

### Option C: Stdout Not Being Captured
- The subprocess stdout isn't being read properly
- **Check**: Look for `[LIVE TRADER]` messages about process creation

## Step 5: Verify Code Deployment

Make sure the latest code is deployed:

1. Check if `src/environment.py` has the diagnostic messages:
   - Look for `[SETUP LOGGING]` print statements
   - Look for `[AZURE BLOB]` print statements

2. If not deployed, deploy:
   ```bash
   git add .
   git commit -m "Add Azure Blob Storage logging diagnostics"
   git push origin main
   ```

3. Wait 2-3 minutes for Azure to deploy

4. Restart the trading strategy

## Expected Behavior

When everything is working:

1. **Dashboard starts** → You see `[STARTUP]` messages (if code is deployed)
2. **Strategy starts** → You see `[STRATEGY]` messages
3. **Logging setup** → You see `[AZURE BLOB]` messages
4. **Logs appear in blob** → After 30+ seconds, check container

## Quick Test

1. **Stop** any running strategy (if running)
2. **Start** a new strategy from dashboard
3. **Immediately check** Log Stream
4. **Look for** `[STRATEGY]` prefix on messages
5. **Wait 30 seconds** and check blob container

If you still don't see `[STRATEGY]` messages, the strategy may not be starting correctly.

