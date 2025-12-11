# How to Run Locally - Step by Step Guide

## Prerequisites

1. **Python 3.9 or higher** installed on your system
2. **pip** (Python package installer)
3. **Zerodha Kite API Credentials**:
   - API Key
   - API Secret
   - Request Token (generated from Zerodha Kite Connect)

---

## Step 1: Install Dependencies

Open a terminal/command prompt in the project directory and run:

```bash
pip install -r requirements.txt
```

This will install all required packages:
- `kiteconnect` (Zerodha API)
- `flask` (Web dashboard)
- `pandas`, `numpy`, `scipy` (Data processing)
- And other dependencies

---

## Step 2: Run the Application

### **Recommended Method: Full Application with Dashboard**

Run the main startup script:

```bash
python src/start_with_monitoring.py
```

**What this does:**
- ✅ Starts the web dashboard at `http://localhost:8080`
- ✅ Prompts for credentials via command line
- ✅ Starts the trading bot with all features
- ✅ Enables real-time monitoring and logging

### **Alternative Method: Trading Bot Only (No Dashboard)**

If you only want the trading bot without the web interface:

```bash
python src/Straddle10PointswithSL-Limit.py
```

**What this does:**
- ✅ Runs the trading strategy only
- ✅ Prompts for credentials via command line
- ❌ No web dashboard
- ❌ No web-based monitoring

---

## Step 3: Enter Credentials

When you run the application, you'll be prompted to enter your Zerodha Kite credentials:

```
Enter Account Name: [Enter your account name, e.g., "Priti"]
Enter API Key: [Enter your Zerodha API Key]
Enter API Secret: [Enter your Zerodha API Secret]
Enter Request Token: [Enter your Request Token]
```

**Note:** 
- The account name will be used for log file naming (e.g., `Priti 2024-01-15_trading_log.log`)
- Logs will be saved in `src/logs/` directory locally

---

## Step 4: Access the Web Dashboard (If using start_with_monitoring.py)

After the application starts:

1. **Open your web browser**
2. **Navigate to**: `http://localhost:8080`
3. **You'll see the dashboard** with:
   - Authentication status
   - Account holder name
   - Live trading controls
   - Real-time logs
   - Strategy status

---

## Step 5: Start Trading

### **Via Web Dashboard** (Recommended):
1. Go to `http://localhost:8080`
2. Click **"Authenticate"** button if not already authenticated
3. Enter your credentials in the popup
4. Navigate to **"Live Trader"** tab
5. Enter **Call Quantity** and **Put Quantity**
6. Click **"Start Live Trader"** button

### **Via Command Line**:
The trading bot will start automatically after authentication if configured to do so.

---

## Viewing Logs Locally

Logs are saved in: `src/logs/`

**Log file naming format:**
```
{AccountName} {Date}_trading_log.log
```

**Example:**
```
Priti 2024-01-15_trading_log.log
```

**To view logs:**
- **Via Web Dashboard**: Go to "Live Trader" tab → "Live Trading Logs" section
- **Via File System**: Open the log file in `src/logs/` directory

---

## Troubleshooting

### Issue: "Module not found" error
**Solution:** Make sure you've installed all dependencies:
```bash
pip install -r requirements.txt
```

### Issue: Port 8080 already in use
**Solution:** The application will try to use port 8080 by default. If it's busy:
1. Stop the application using the port
2. Or modify `src/config.py` to use a different port:
   ```python
   DASHBOARD_PORT = 8081  # Change to any available port
   ```

### Issue: "Connection refused" when accessing dashboard
**Solution:** 
- Make sure the application is running
- Check that you're using the correct URL: `http://localhost:8080`
- Verify the port number in `src/config.py`

### Issue: Authentication fails
**Solution:**
- Verify your API credentials are correct
- Make sure your Request Token is valid (they expire after some time)
- Check that your Zerodha account has API access enabled

---

## Quick Reference

| Task | Command |
|------|---------|
| **Run with dashboard** | `python src/start_with_monitoring.py` |
| **Run without dashboard** | `python src/Straddle10PointswithSL-Limit.py` |
| **Install dependencies** | `pip install -r requirements.txt` |
| **Access dashboard** | `http://localhost:8080` |
| **Log location** | `src/logs/` |

---

## File Structure

```
Strangle10Points/
├── src/
│   ├── start_with_monitoring.py      ← **RECOMMENDED: Run this**
│   ├── Straddle10PointswithSL-Limit.py  ← Alternative: Trading only
│   ├── config_dashboard.py          ← Dashboard (auto-started)
│   ├── config.py                    ← Configuration file
│   └── logs/                        ← Log files directory
├── requirements.txt                  ← Dependencies
└── HOW_TO_RUN_LOCALLY.md           ← This file
```

---

## Summary

**To run locally:**
1. Install dependencies: `pip install -r requirements.txt`
2. Run: `python src/start_with_monitoring.py`
3. Enter credentials when prompted
4. Open browser: `http://localhost:8080`
5. Start trading via the dashboard!

**That's it!** The application will automatically detect it's running locally and configure logging and ports accordingly.

