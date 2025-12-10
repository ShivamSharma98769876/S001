# Quick Start: Azure Deployment

## Quick Deployment Steps

### 1. Prepare Your Code
```bash
# Ensure all files are committed (or create ZIP excluding venv, __pycache__)
```

### 2. Create Azure Resources
- Go to [Azure Portal](https://portal.azure.com)
- Create Resource Group: `trading-bot-rg`
- Create App Service Plan (Linux, B1 Basic)
- Create Web App (Python 3.9)

### 3. Enter Credentials via Web Interface
After deployment, when you access your Azure Web App URL:
1. You'll be automatically redirected to a credentials input page
2. Enter your Zerodha Kite API credentials:
   - Account Name
   - API Key
   - API Secret
   - Request Token
3. Click "Connect & Start Trading"
4. You'll be redirected to the dashboard

**Note**: 
- **On Azure**: Credentials are entered via web interface popup (not environment variables)
- **Locally**: You'll be prompted to enter credentials via CLI as before

### 4. Enable Logging
Azure Portal > Your Web App > App Service logs:
- Enable "Application Logging (Filesystem)"
- Enable "Detailed Error Messages"
- Save

### 5. Deploy
- Method 1: ZIP Deploy via Portal
- Method 2: `az webapp deployment source config-zip --resource-group trading-bot-rg --name trading-bot-app --src trading-bot.zip`

### 6. View Logs
- Real-time: Azure Portal > Log stream
- Files: Azure Portal > Advanced Tools (Kudu) > LogFiles/Application/

## Local vs Azure

The application **automatically detects** the environment:
- **Local**: 
  - Logs to `src/logs/` directory
  - Dashboard: `http://localhost:8080` (default port)
  - Host: `0.0.0.0` (accessible from network)
- **Azure**: 
  - Logs to `/home/LogFiles/` (captured by Azure)
  - Dashboard: `https://your-app-name.azurewebsites.net`
  - Port: Auto-detected from Azure environment

**Network Configuration:**
- **Local IP/Port**: `0.0.0.0:8080` (configurable in `src/config.py`)
- **Azure IP/Port**: `0.0.0.0:[auto]` (automatically detected)

No code changes needed - it works in both environments!

See [NETWORK_CONFIGURATION.md](NETWORK_CONFIGURATION.md) for detailed network settings.

## Running Locally

**Main file to run**: `src/start_with_monitoring.py`

```bash
python src/start_with_monitoring.py
```

This will:
- Start the web dashboard at `http://localhost:8080`
- Prompt for credentials via CLI
- Start the trading bot with all features

See [LOCAL_RUN_GUIDE.md](LOCAL_RUN_GUIDE.md) for detailed local run instructions.

## Full Documentation

See [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md) for complete guide.

