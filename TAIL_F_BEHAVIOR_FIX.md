# Fix: Auto-Refresh Logs Every 3 Seconds (Tail -f Behavior)

## Requirement

When Live Trader is running, the system should:
1. **Fetch latest logs every 3 seconds** automatically
2. **Show new logs at the bottom** (like `tail -f`)
3. **Auto-scroll to bottom** when new logs arrive
4. **Continue refreshing** as long as strategy is running

## Current Implementation

The system already has:
- ✅ `setInterval(loadLogs, 3000)` - Fetches logs every 3 seconds
- ✅ Tail-like behavior - Only appends new logs (doesn't replace all)
- ✅ Auto-scroll when user is at bottom

## Improvements Made

### 1. Ensure Interval Runs When Strategy Starts

When strategy starts:
- Clears any existing interval
- Starts fresh 3-second interval
- Loads logs immediately to show current state

### 2. Improved Auto-Scroll Behavior

- **If user is at bottom**: Always scrolls to show new logs (true tail -f)
- **If user scrolled up**: Only auto-scrolls if many new logs (>5) arrived
- **On first load**: Always scrolls to bottom

### 3. Ensure Interval Persists

- Interval is started on page load
- Restarted when strategy starts
- Continues running as long as page is open

## How It Works

1. **Page Loads** → Interval starts: `setInterval(loadLogs, 3000)`
2. **Strategy Starts** → Interval restarted to ensure it's running
3. **Every 3 Seconds** → `loadLogs()` fetches latest logs
4. **New Logs Detected** → Only new logs are appended (tail behavior)
5. **Auto-Scroll** → Scrolls to bottom if user was at bottom
6. **Continues** → Keeps refreshing every 3 seconds

## Expected Behavior

When Live Trader is running:

1. **Logs appear automatically** every 3 seconds
2. **New logs appear at bottom** (like `tail -f`)
3. **Auto-scrolls to bottom** when new logs arrive (if user was at bottom)
4. **No manual refresh needed** - it's automatic

## Testing

1. Start Live Trader
2. Watch the "Live Trading Logs" section
3. You should see:
   - Logs appearing automatically every 3 seconds
   - New logs appearing at the bottom
   - Auto-scrolling to show latest logs
   - No need to click "Refresh" button

The system now works like `tail -f` - continuously showing the latest logs!

