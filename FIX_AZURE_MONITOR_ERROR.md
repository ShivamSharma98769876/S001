# Fix Azure Monitor OpenTelemetry Error

## Error
```
2025-12-13T09:16:14.5884672Z 2025-12-13 09:16:13,560 - azure.monitor.opentelemetry.exporter.export._base - ERROR - Non-retryable server side error: Operation returned an invalid status 'Bad Request'.
```

## Cause
Azure App Service automatically enables Application Insights/OpenTelemetry monitoring if Application Insights is configured. The "Bad Request" error indicates:
- Invalid or missing Application Insights connection string
- Application Insights resource is misconfigured
- Telemetry data format issue

## Solutions

### Option 1: Disable Application Insights (If Not Needed)

If you don't need Application Insights monitoring:

1. **In Azure Portal:**
   - Go to your App Service > **Configuration** > **Application settings**
   - Remove or clear these environment variables:
     - `APPLICATIONINSIGHTS_CONNECTION_STRING`
     - `APPINSIGHTS_INSTRUMENTATIONKEY`
     - `APPLICATIONINSIGHTS_ENABLE_AGENT`
   - Save and restart the app

2. **Or set to disable:**
   ```
   APPLICATIONINSIGHTS_ENABLE_AGENT = false
   ```

### Option 2: Fix Application Insights Configuration (If Needed)

If you want to use Application Insights:

1. **Create/Verify Application Insights Resource:**
   - Go to Azure Portal > Create Resource > Application Insights
   - Create a new Application Insights resource
   - Copy the **Connection String**

2. **Configure in App Service:**
   - Go to App Service > **Configuration** > **Application settings**
   - Add/Update:
     ```
     APPLICATIONINSIGHTS_CONNECTION_STRING = <your-connection-string>
     ```
   - Save and restart

### Option 3: Suppress the Error in Code

Add this to your startup code to suppress the error if monitoring isn't critical:

```python
import os
import logging

# Disable Azure Monitor OpenTelemetry if not properly configured
if not os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING'):
    # Suppress OpenTelemetry errors
    logging.getLogger('azure.monitor.opentelemetry').setLevel(logging.CRITICAL)
    os.environ['APPLICATIONINSIGHTS_ENABLE_AGENT'] = 'false'
```

### Option 4: Add to startup.py

Create or update `startup.py` to disable OpenTelemetry:

```python
import os
import logging

# Disable Azure Monitor OpenTelemetry exporter errors
os.environ.setdefault('APPLICATIONINSIGHTS_ENABLE_AGENT', 'false')
logging.getLogger('azure.monitor.opentelemetry').setLevel(logging.CRITICAL)
```

## Quick Fix (Recommended)

The easiest solution is to disable Application Insights in Azure Portal:

1. Azure Portal > Your App Service
2. Configuration > Application settings
3. Find `APPLICATIONINSIGHTS_CONNECTION_STRING` or `APPINSIGHTS_INSTRUMENTATIONKEY`
4. Either delete it or set `APPLICATIONINSIGHTS_ENABLE_AGENT` to `false`
5. Save and restart

## Verify Fix

After applying the fix, check logs:
- The error should no longer appear
- Application should run normally
- Your custom logging (Azure Blob Storage) will continue to work

