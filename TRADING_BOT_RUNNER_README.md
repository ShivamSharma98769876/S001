# Options Trading Bot Runner

This directory contains programs to easily run the `main.py` trading bot with API credentials loaded from `.env` file and custom parameters.

## Files Created

1. **`run_trading_bot.py`** - Main Python script that loads API credentials from .env file
2. **`setup_env.py`** - Script to create .env file with your API credentials
3. **`run_with_params.bat`** - Windows batch file with simplified parameters
4. **`run_with_params.ps1`** - PowerShell script with simplified parameters
5. **`TRADING_BOT_RUNNER_README.md`** - This documentation file

## Quick Start

### Step 1: Setup Environment
```bash
python setup_env.py
```

### Step 2: Update .env File
Edit the `.env` file and replace `your_request_token_here` with your actual access token.

### Step 3: Run Trading Bot

#### Method 1: Command Line (Recommended)
```bash
python run_trading_bot.py --request-token YOUR_TOKEN --call-quantity 50 --put-quantity 50
```

#### Method 2: Windows Batch File
Edit `run_with_params.bat` with your token, then run:
```cmd
run_with_params.bat
```

#### Method 3: PowerShell Script
Edit `run_with_params.ps1` with your token, then run:
```powershell
.\run_with_params.ps1
```

## Command Line Parameters

### Required Parameters
- `--request-token` - Your Kite Connect access token
- `--call-quantity` - Number of call options to trade
- `--put-quantity` - Number of put options to trade

### Optional Parameters
- `--account` - Account identifier (default: TRADING_ACCOUNT)
- `--delta-low` - Target Delta Low (default: 0.29)
- `--delta-high` - Target Delta High (default: 0.35)
- `--cleanup-logs` - Clean up old log files before starting
- `--log-days` - Days to keep log files (default: 30)

## Example Usage

### Basic Usage
```bash
python run_trading_bot.py \
    --request-token "qed5J2DoHsmx37m990hcN1fLuYsMpaCY" \
    --call-quantity 50 \
    --put-quantity 50
```

### With Additional Options
```bash
python run_trading_bot.py \
    --request-token "YOUR_ACCESS_TOKEN" \
    --call-quantity 100 \
    --put-quantity 75 \
    --account "MY_ACCOUNT" \
    --delta-low 0.25 \
    --delta-high 0.40 \
    --cleanup-logs
```

## Environment Setup

### Creating .env File
The `.env` file contains your API credentials:

```bash
# Run setup script
python setup_env.py
```

This creates a `.env` file with:
```env
KITE_API_KEY=n683nqe7f3l7nzxl
KITE_API_SECRET=11krc3ysc604ppxsvq60862pnq73t4qi
KITE_REQUEST_TOKEN=your_request_token_here
KITE_ACCOUNT=TRADING_ACCOUNT
```

### Getting Your Access Token
Use `InstallLibs.py` to generate your access token:

```python
from kiteconnect import KiteConnect

api_key = "n683nqe7f3l7nzxl"
api_secret = "11krc3ysc604ppxsvq60862pnq73t4qi"
request_token = "YOUR_REQUEST_TOKEN"  # Get this after login

kite = KiteConnect(api_key=api_key)
data = kite.generate_session(request_token, api_secret=api_secret)
access_token = data["access_token"]
print("Access Token:", access_token)
```

## Parameters Explained

- **REQUEST_TOKEN**: Your Kite Connect access token (generated from request token)
- **CALL_QUANTITY**: Number of call options to trade
- **PUT_QUANTITY**: Number of put options to trade
- **ACCOUNT**: Account identifier for logging and organization
- **DELTA_LOW/DELTA_HIGH**: Delta range for options selection
- **CLEANUP_LOGS**: Whether to clean old log files before starting
- **LOG_DAYS**: Number of days to keep log files

## Prerequisites

1. Python 3.6+ installed
2. All required dependencies installed (run `pip install -r requirements.txt`)
3. `main.py` file in the same directory
4. `.env` file with API credentials
5. Valid access token

## Error Handling

The scripts include comprehensive error handling:
- ✅ Loads API credentials from .env file automatically
- ✅ Validates that .env file exists and contains required credentials
- ✅ Checks if Python is installed
- ✅ Validates that `main.py` exists
- ✅ Handles API errors gracefully
- ✅ Provides clear error messages and usage examples

## Logging

The trading bot will create log files in the `logs/` directory with timestamps and account information.

## Security Notes

⚠️ **Important**: 
- API credentials are stored in `.env` file (more secure than command line)
- `.env` file is automatically ignored by git (see .gitignore)
- Never commit your `.env` file to version control
- Keep your access token secure and rotate it regularly

## Troubleshooting

### Common Issues

1. **".env file not found"**
   - Run `python setup_env.py` to create the .env file
   - Make sure you're in the correct directory

2. **"API credentials not found in .env"**
   - Check that `.env` file contains KITE_API_KEY and KITE_API_SECRET
   - Run `python setup_env.py` to recreate the file

3. **"Missing required argument"**
   - Ensure all required parameters are provided
   - Check parameter names and values

4. **"Python not found"**
   - Install Python and add it to PATH
   - Or use the full path to python.exe

5. **"main.py not found"**
   - Make sure you're running from the correct directory
   - Verify `main.py` exists in the current folder

### Getting Help

If you encounter issues:
1. Check the error messages in the console
2. Review the log files in the `logs/` directory
3. Verify your API credentials are correct
4. Ensure all dependencies are installed
5. Run with `--help` to see all available options

## Example Output

```
============================================================
                OPTIONS TRADING BOT RUNNER
============================================================

📁 Loading API credentials from .env file...
✅ API credentials loaded successfully!

🚀 Starting Trading Bot...
📅 Start Time: 2024-01-15 10:30:00
🔑 API Key: n683nqe7...nzxl
📊 Call Quantity: 50
📉 Put Quantity: 50
🎯 Delta Range: 0.29 - 0.35
🏦 Account: TRADING_ACCOUNT
🧹 Cleanup Logs: True
------------------------------------------------------------

✅ Trading bot completed successfully!
🎉 Trading bot execution completed!
```
