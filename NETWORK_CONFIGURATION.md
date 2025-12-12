# Network Configuration: IP and Port Settings

## Summary

| Environment | Host (IP) | Port | Access URL |
|------------|-----------|------|------------|
| **Local** | `0.0.0.0` | `8080` | `http://localhost:8080` or `http://127.0.0.1:8080` |
| **Azure** | `0.0.0.0` | Auto (from Azure) | `https://your-app-name.azurewebsites.net` |

## Detailed Configuration

### Local Environment

**Configuration File**: `src/config.py`

```python
DASHBOARD_HOST = '0.0.0.0'  # Listen on all network interfaces
DASHBOARD_PORT = 8080        # Default port (or auto-detected from Azure)
```

**What this means:**
- **Host `0.0.0.0`**: The application listens on all available network interfaces
  - Accessible via `localhost` or `127.0.0.1` from the same machine
  - Accessible via your machine's local IP address from other devices on the same network
  - Example: If your local IP is `192.168.1.100`, you can access it at `http://192.168.1.100:8080`

- **Port `8080`**: Default port for local development
  - You can change this in `src/config.py` if port 8080 is already in use
  - Access URL: `http://localhost:8080`

**Access URLs (Local):**
- `http://localhost:8080`
- `http://127.0.0.1:8080`
- `http://[your-local-ip]:8080` (from other devices on your network)

### Azure Environment

**Configuration**: Automatically detected from Azure environment variables

**Host**: `0.0.0.0` (same as local - listens on all interfaces)

**Port**: Automatically detected from Azure environment variables:
- Primary: `HTTP_PLATFORM_PORT` (Azure App Service standard)
- Fallback: `PORT` (alternative Azure variable)
- If neither is set: Falls back to `8080`

**What this means:**
- Azure App Service automatically assigns a port via the `HTTP_PLATFORM_PORT` environment variable
- The application automatically detects and uses this port
- You don't need to configure the port manually on Azure
- Azure handles routing external traffic to your app

**Access URLs (Azure):**
- `https://your-app-name.azurewebsites.net` (HTTPS - recommended)
- `http://your-app-name.azurewebsites.net` (HTTP - redirects to HTTPS)

**Note**: On Azure, you don't specify the port in the URL - Azure handles this automatically.

## Configuration Files

### 1. `src/config.py`
```python
# Dashboard Configuration
DASHBOARD_HOST = '0.0.0.0'  # Dashboard host address
# Port will be auto-detected from Azure environment or use default
import os
DASHBOARD_PORT = int(os.getenv('HTTP_PLATFORM_PORT', os.getenv('PORT', 8080)))
```

### 2. `src/config_dashboard.py`
The dashboard automatically:
- Uses `DASHBOARD_HOST` and `DASHBOARD_PORT` from config.py
- Overrides port if Azure environment variables are detected
- Logs the actual host and port being used

## Changing the Configuration

### To Change Local Port

Edit `src/config.py`:
```python
DASHBOARD_PORT = 5000  # Change to your preferred port
```

### To Change Local Host

Edit `src/config.py`:
```python
DASHBOARD_HOST = '127.0.0.1'  # Only listen on localhost (more secure)
# OR
DASHBOARD_HOST = '0.0.0.0'    # Listen on all interfaces (default)
```

**Security Note**: 
- `0.0.0.0` allows access from any network interface (useful for Azure, but less secure locally)
- `127.0.0.1` only allows access from the same machine (more secure for local development)

### Azure Port Configuration

**You cannot manually set the port on Azure** - it's automatically assigned by Azure App Service. The application automatically detects and uses the correct port.

## Verification

### Check Current Configuration (Local)

When you start the application, you'll see:
```
============================================================
[CONFIG DASHBOARD] Starting web server
[CONFIG DASHBOARD] Host: 0.0.0.0
[CONFIG DASHBOARD] Port: 8080
[CONFIG DASHBOARD] Dashboard URL: http://0.0.0.0:8080
============================================================
```

### Check Current Configuration (Azure)

In Azure Portal > Log stream, you'll see:
```
[CONFIG] Azure environment detected - using port from HTTP_PLATFORM_PORT: [port-number]
[CONFIG] Loaded dashboard config: host=0.0.0.0, port=[port-number]
```

## Troubleshooting

### Port Already in Use (Local)

**Error**: `Address already in use` or `Port 8080 is already in use`

**Solution**: 
1. Change the port in `src/config.py`:
   ```python
   DASHBOARD_PORT = 8081  # or any other available port
   ```
2. Or stop the application using port 8080

### Cannot Access from Other Devices (Local)

**Issue**: Can't access `http://[your-ip]:8080` from another device

**Solutions**:
1. Ensure `DASHBOARD_HOST = '0.0.0.0'` (not `127.0.0.1`)
2. Check Windows Firewall allows port 8080
3. Verify both devices are on the same network
4. Check your local IP address: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)

### Azure Port Issues

**Issue**: Application not accessible on Azure

**Solutions**:
1. Check Azure Portal > Log stream for port information
2. Verify the application is running (Status should be "Running")
3. Check Azure Portal > Configuration > General settings for any port restrictions
4. Ensure HTTPS is enabled (Azure uses HTTPS by default)

## Network Security

### Local Development
- `0.0.0.0` allows access from any device on your network
- For better security, use `127.0.0.1` if you only need local access
- Consider using a firewall to restrict access

### Azure
- Azure automatically handles HTTPS/SSL
- Azure provides built-in DDoS protection
- Access is controlled via Azure authentication (if configured)

## Quick Reference

**Local Access:**
```bash
# Start the application
python src/start_with_monitoring.py

# Access at:
http://localhost:8080
```

**Azure Access:**
```bash
# Deploy to Azure (see AZURE_DEPLOYMENT.md)
# Access at:
https://your-app-name.azurewebsites.net
```

