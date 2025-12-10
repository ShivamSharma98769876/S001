# Local Run Guide - Which File to Run

## Recommended: Main Startup Script

**File to run**: `src/start_with_monitoring.py`

### Command:
```bash
python src/start_with_monitoring.py
```

### What it does:
- ✅ Sets up logging
- ✅ Starts the web dashboard (http://localhost:8080)
- ✅ Starts config monitoring
- ✅ Runs the main trading strategy
- ✅ Prompts for credentials via CLI

### This is the **recommended** way to run locally as it includes:
- Web dashboard for monitoring
- Real-time config monitoring
- All features integrated

---

## Alternative: Direct Strategy File

**File to run**: `src/Straddle10PointswithSL-Limit.py`

### Command:
```bash
python src/Straddle10PointswithSL-Limit.py
```

### What it does:
- ✅ Runs the main trading strategy only
- ✅ Prompts for credentials via CLI
- ❌ No web dashboard
- ❌ No config monitoring dashboard

### Use this if:
- You only need the trading bot without the web interface
- You want a simpler setup

---

## Using Batch/PowerShell Scripts

### Windows Batch File:
```bash
# Option 1: Using startup.bat
startup.bat

# Option 2: Using run_trading_bot.bat
run_trading_bot.bat
```

### PowerShell:
```powershell
# Option 1: Using run_trading_bot.ps1
.\run_trading_bot.ps1
```

These scripts will call the appropriate Python file for you.

---

## Quick Start (Recommended)

1. **Open terminal/command prompt** in the project directory

2. **Run the main startup script**:
   ```bash
   python src/start_with_monitoring.py
   ```

3. **Enter credentials when prompted**:
   ```
   Account: [enter your account]
   Api_key: [enter your API key]
   Api_Secret: [enter your API secret]
   Request_Token: [enter your request token]
   ```

4. **Access the web dashboard**:
   - Open browser: `http://localhost:8080`
   - Monitor trading, view logs, manage config

---

## File Structure

```
Strangle10Points/
├── src/
│   ├── start_with_monitoring.py      ← **RECOMMENDED: Run this**
│   ├── Straddle10PointswithSL-Limit.py  ← Alternative: Run this for strategy only
│   ├── config_dashboard.py          ← Dashboard (auto-started by start_with_monitoring.py)
│   └── ...
├── startup.bat                       ← Windows batch script
├── run_trading_bot.bat              ← Alternative batch script
└── ...
```

---

## Summary

| File | Use Case | Features |
|------|----------|----------|
| `src/start_with_monitoring.py` | **Recommended** | Full features: Dashboard + Monitoring + Trading |
| `src/Straddle10PointswithSL-Limit.py` | Simple setup | Trading only (no dashboard) |

**Answer: Run `src/start_with_monitoring.py` for the complete experience!**

