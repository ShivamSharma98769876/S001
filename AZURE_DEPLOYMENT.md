# Azure Cloud Deployment Guide

This guide will help you deploy the Trading Bot application to Azure App Service while maintaining the ability to run it locally.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Azure Setup](#azure-setup)
3. [Configuration](#configuration)
4. [Deployment](#deployment)
5. [Viewing Logs on Azure](#viewing-logs-on-azure)
6. [Local Development](#local-development)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

1. **Azure Account**: An active Azure subscription
2. **Azure CLI**: Install from [Azure CLI Installation](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
3. **Git**: For deployment (optional, can use Azure Portal)
4. **Python 3.9+**: For local development

## Azure Setup

### Option 1: Using Azure Portal (Recommended for beginners)

1. **Create Resource Group**:
   - Go to [Azure Portal](https://portal.azure.com)
   - Navigate to "Resource groups" > "Create"
   - Name: `trading-bot-rg`
   - Region: Choose closest to you (e.g., `East US`)

2. **Create App Service Plan**:
   - In your resource group, click "Create"
   - Search for "App Service Plan"
   - Select "App Service Plan (Linux)" for Linux or "App Service Plan (Windows)" for Windows
   - Choose pricing tier: **B1 Basic** (minimum for production) or **F1 Free** (for testing)
   - Create the plan

3. **Create Web App**:
   - In your resource group, click "Create"
   - Search for "Web App"
   - Configure:
     - **Name**: `trading-bot-app` (must be globally unique)
     - **Runtime stack**: Python 3.9 or 3.10
     - **Operating System**: Linux (recommended) or Windows
     - **App Service Plan**: Select the plan you created
   - Click "Review + create" > "Create"

### Option 2: Using Azure CLI

Run the deployment script:

```bash
chmod +x .azure/deploy.sh
./.azure/deploy.sh
```

Or manually:

```bash
# Login to Azure
az login

# Create resource group
az group create --name trading-bot-rg --location eastus

# Create App Service plan
az appservice plan create \
    --name trading-bot-plan \
    --resource-group trading-bot-rg \
    --sku B1 \
    --is-linux

# Create Web App
az webapp create \
    --name trading-bot-app \
    --resource-group trading-bot-rg \
    --plan trading-bot-plan \
    --runtime "PYTHON:3.9"
```

## Configuration

### 1. Enter Credentials via Web Interface

**Important**: Credentials are entered via a secure web interface, not environment variables.

**Note**: 
- **On Azure**: Credentials are entered via web interface popup when you first access the app
- **Locally**: The application will prompt you to enter credentials via CLI as you did before

**How it works on Azure:**
1. After deployment, access your Azure Web App URL
2. You'll be automatically redirected to a credentials input page
3. Enter your Zerodha Kite API credentials:
   - **Account Name**: Your trading account identifier
   - **API Key**: Your Zerodha Kite API key
   - **API Secret**: Your Zerodha Kite API secret
   - **Request Token**: Your Zerodha Kite request token
4. Click "Connect & Start Trading"
5. You'll be redirected to the main dashboard
6. The trading bot will automatically start using these credentials

**Optional: Configure Build Settings**
1. Go to Azure Portal > Your Web App > **Configuration** > **Application settings**
2. Add (optional):
   - `SCM_DO_BUILD_DURING_DEPLOYMENT` = `true`
   - `ENABLE_ORYX_BUILD` = `true`
3. Click **Save** (this will restart the app)

### 2. Enable Logging

1. Go to Azure Portal > Your Web App > **App Service logs**
2. Enable:
   - **Application Logging (Filesystem)**: ON
   - **Detailed Error Messages**: ON
   - **Failed Request Tracing**: ON
   - **Web server logging**: ON
3. Set **Retention Period (Days)**: 7 (or as needed)
4. Click **Save**

### 3. Configure Startup Command

For **Linux App Service**:
1. Go to **Configuration** > **General settings**
2. Set **Startup Command**:
   ```bash
   python src/start_with_monitoring.py
   ```

For **Windows App Service**:
- The `web.config` file will be used automatically
- Or set startup command in Configuration:
   ```
   python src\start_with_monitoring.py
   ```

## Deployment

### Method 1: Using Azure Portal (ZIP Deploy)

1. **Prepare your code**:
   ```bash
   # Create a ZIP file of your project (excluding venv, __pycache__, etc.)
   # On Windows:
   # Right-click project folder > Send to > Compressed (zipped) folder
   # On Linux/Mac:
   zip -r trading-bot.zip . -x "venv/*" "__pycache__/*" "*.pyc" ".git/*"
   ```

2. **Deploy via Portal**:
   - Go to Azure Portal > Your Web App > **Deployment Center**
   - Select **Local Git** or **ZIP Deploy**
   - Upload your ZIP file
   - Wait for deployment to complete

### Method 2: Using Azure CLI (ZIP Deploy)

```bash
# Create ZIP (exclude unnecessary files)
zip -r trading-bot.zip . -x "venv/*" "__pycache__/*" "*.pyc" ".git/*" "*.log"

# Deploy
az webapp deployment source config-zip \
    --resource-group trading-bot-rg \
    --name trading-bot-app \
    --src trading-bot.zip
```

### Method 3: Using Git (Continuous Deployment)

1. **Setup Local Git Repository**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Configure Azure for Git Deployment**:
   - Go to Azure Portal > Your Web App > **Deployment Center**
   - Select **Local Git** as source
   - Copy the Git deployment URL

3. **Deploy**:
   ```bash
   git remote add azure <your-azure-git-url>
   git push azure main
   ```

### Method 4: Using VS Code Azure Extension

1. Install **Azure App Service** extension in VS Code
2. Right-click your project folder
3. Select **Deploy to Web App**
4. Follow the prompts

## Viewing Logs on Azure

### Method 1: Log Stream (Real-time)

1. Go to Azure Portal > Your Web App > **Log stream**
2. You'll see real-time logs from your application
3. This shows both console output and file logs

### Method 2: Download Log Files

1. Go to Azure Portal > Your Web App > **Advanced Tools (Kudu)** > **Go**
2. Navigate to: `LogFiles/Application/`
3. Download log files:
   - `trading_bot.log` - Main application logs
   - `config_monitoring.log` - Config monitoring logs
   - `python.log` - Python runtime logs

### Method 3: Using Azure CLI

```bash
# Stream logs in real-time
az webapp log tail --name trading-bot-app --resource-group trading-bot-rg

# Download logs
az webapp log download --name trading-bot-app --resource-group trading-bot-rg --log-file logs.zip
```

### Method 4: Application Insights (Advanced)

For advanced logging and monitoring:

1. Create Application Insights resource
2. Link it to your Web App
3. View logs, metrics, and traces in Application Insights portal

## Local Development

The application automatically detects if it's running locally or on Azure:

### Running Locally

1. **Run the application**:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Run with monitoring
   python src/start_with_monitoring.py
   ```

2. **Enter credentials when prompted**:
   - The application will prompt you to enter credentials via CLI:
     - `Account: ` - Enter your account name
     - `Api_key: ` - Enter your API key
     - `Api_Secret: ` - Enter your API secret
     - `Request_Token: ` - Enter your request token
   - This is the same CLI input method you were using before

3. **Logs location**:
   - Local logs: `src/logs/{account} {date}_trading_log.log`
   - Config monitoring: `src/logs/config_monitoring.log`

**Note**: When running locally, credentials are entered via CLI prompts (as before). On Azure, they are automatically read from environment variables.

### Environment Detection

The application uses `src/environment.py` to:
- Detect Azure environment (checks for `WEBSITE_INSTANCE_ID`)
- Use appropriate log directories:
  - **Azure**: `/home/LogFiles/` (Linux) or `D:\home\LogFiles\` (Windows)
  - **Local**: `src/logs/`
- Configure logging for both environments

## Troubleshooting

### Application Not Starting

1. **Check Logs**:
   - Go to **Log stream** in Azure Portal
   - Look for error messages

2. **Common Issues**:
   - **Missing dependencies**: Check `requirements.txt` is included
   - **Wrong Python version**: Ensure runtime is Python 3.9+
   - **Missing environment variables**: Verify all KITE_* variables are set
   - **Startup command error**: Check startup command in Configuration

### Logs Not Appearing

1. **Enable Logging**:
   - Go to **App Service logs** > Enable all logging options
   - Set retention period

2. **Check Log Directory**:
   - Azure Linux: `/home/LogFiles/`
   - Azure Windows: `D:\home\LogFiles\`
   - Use Kudu to browse files

3. **Verify Permissions**:
   - App Service should have write permissions to log directory
   - Check if directory exists

### API Connection Issues

1. **Verify Credentials**:
   - Check environment variables in Azure Portal
   - Ensure no extra spaces or quotes

2. **Network Issues**:
   - Check if Zerodha API is accessible from Azure
   - Verify firewall rules

3. **Token Expiry**:
   - Kite request tokens expire
   - Update `KITE_REQUEST_TOKEN` in Azure App Settings

### Dashboard Not Accessible

1. **Check Port Configuration**:
   - Azure App Service uses port from `HTTP_PLATFORM_PORT` environment variable
   - Update `config.py` if needed:
     ```python
     DASHBOARD_HOST = '0.0.0.0'
     DASHBOARD_PORT = int(os.getenv('HTTP_PLATFORM_PORT', 8080))
     ```

2. **Verify Web App is Running**:
   - Check **Overview** > **Status** should be "Running"
   - Check **Log stream** for errors

## Best Practices

1. **Security**:
   - Never commit credentials to Git
   - Use Azure Key Vault for sensitive data (advanced)
   - Enable HTTPS only

2. **Monitoring**:
   - Set up Application Insights for production
   - Configure alerts for errors
   - Monitor resource usage

3. **Backup**:
   - Enable backup for App Service
   - Regularly export configuration

4. **Scaling**:
   - Start with B1 Basic tier
   - Scale up if needed based on usage
   - Consider auto-scaling for high traffic

## Support

For issues:
1. Check Azure Portal logs first
2. Review this documentation
3. Check Azure App Service documentation: [Azure Docs](https://docs.microsoft.com/azure/app-service/)

## File Structure

```
.
├── src/
│   ├── environment.py          # Environment detection and logging
│   ├── Straddle10PointswithSL-Limit.py  # Main trading script
│   ├── start_with_monitoring.py  # Startup script
│   └── ...
├── startup.sh                  # Linux startup script
├── startup.bat                 # Windows startup script
├── web.config                  # IIS configuration (Windows)
├── requirements.txt            # Python dependencies
└── AZURE_DEPLOYMENT.md         # This file
```

