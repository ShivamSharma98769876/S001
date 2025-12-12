# Credentials Setup Guide

## Overview

The application now supports two different methods for entering credentials based on the environment:

- **Azure Cloud**: Web-based credential input popup
- **Local**: CLI prompts (as before)

## How It Works

### On Azure Cloud

1. **Automatic Redirect**: When you access your Azure Web App URL, if credentials are not set, you'll be automatically redirected to a credentials input page.

2. **Credential Input Page**: A secure web form where you enter:
   - Account Name
   - API Key
   - API Secret
   - Request Token

3. **Automatic Start**: After submitting credentials:
   - Credentials are stored in memory (not saved to disk)
   - You're redirected to the main dashboard
   - The trading bot automatically starts using these credentials

4. **Security**: 
   - Credentials are stored in memory only
   - They are not persisted to disk or environment variables
   - If the app restarts, you'll need to re-enter credentials

### Locally

1. **CLI Prompts**: When you run the application locally, you'll be prompted via command line:
   ```
   Account: [enter your account]
   Api_key: [enter your API key]
   Api_Secret: [enter your API secret]
   Request_Token: [enter your request token]
   ```

2. **Same as Before**: This works exactly as it did before - no changes to your local workflow.

## Accessing Credentials Page on Azure

### Method 1: Automatic Redirect
- Simply visit your Azure Web App URL
- If credentials aren't set, you'll be redirected automatically

### Method 2: Direct URL
- Visit: `https://your-app-name.azurewebsites.net/credentials`

## API Endpoints

The following API endpoints are available for credential management:

- `GET /api/trading/credentials-status` - Check if credentials are set
- `POST /api/trading/set-credentials` - Set credentials (used by the web form)
- `GET /api/trading/get-credentials` - Get credentials (internal use by main script)

## Troubleshooting

### Credentials Not Working on Azure

1. **Check Logs**: View Azure Portal > Log stream to see if credentials were received
2. **Re-enter Credentials**: If the app restarted, you'll need to re-enter credentials
3. **Verify URL**: Make sure you're accessing the correct Azure Web App URL

### Main Script Waiting for Credentials

If you see logs like:
```
[ENV] Waiting for credentials... (60 seconds)
```

This means:
- The main trading script is waiting for credentials from the web interface
- Visit the web interface URL and enter credentials
- The script will automatically detect and use them

### Credentials Page Not Showing

1. Check if you're accessing the correct URL
2. Check Azure Portal > Log stream for errors
3. Verify the application is running

## Security Notes

- Credentials are stored in memory only
- They are never written to disk
- They are not logged or exposed in error messages
- If the application restarts, credentials must be re-entered
- This provides better security than environment variables for sensitive credentials

## Flow Diagram

```
Azure Deployment:
┌─────────────────┐
│  Access Web App │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Credentials Set?        │
│ (Check in memory)       │
└────────┬────────────────┘
         │
    ┌────┴────┐
    │         │
   No        Yes
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────┐
│Redirect │ │ Show         │
│to       │ │ Dashboard    │
│Creds    │ └──────────────┘
│Page     │
└────┬────┘
     │
     ▼
┌──────────────┐
│ User Enters  │
│ Credentials  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Store in     │
│ Memory       │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Redirect to  │
│ Dashboard    │
└──────────────┘
       │
       ▼
┌──────────────┐
│ Main Script  │
│ Retrieves    │
│ Credentials  │
│ & Starts     │
└──────────────┘

Local Deployment:
┌─────────────────┐
│ Run Script      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ CLI Prompts     │
│ (Account, etc.) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Start Trading   │
└─────────────────┘
```

