# 🧠 StockSage - AI-Powered Options Trading Bot

A sophisticated options trading bot that implements a strangle strategy with dynamic stop-loss management and VWAP analysis using the Kite Connect API. StockSage combines advanced AI analytics with professional trading algorithms for optimal market performance.

## 🚀 Features

- **🧠 AI-Powered Analytics**: Advanced algorithms for market analysis and decision making
- **📊 Delta-based Strike Selection**: Automatically selects optimal call and put strikes based on target delta range
- **📈 VWAP Analysis**: 5-minute Volume Weighted Average Price calculation for enhanced entry timing
- **🛡️ Dynamic Stop-Loss**: Adjusts stop-loss levels based on market conditions and day of the week
- **🔄 Hedge Management**: Automatically places hedge positions when certain profit targets are reached
- **📱 Real-time Monitoring**: Continuous monitoring of positions with automatic adjustments
- **🎨 Modern Web UI**: Beautiful Streamlit-based web interface with professional StockSage branding
- **🔐 Automatic Access Token Generation**: Automatically generates access tokens from request tokens for seamless authentication
- **💻 Command Line Interface**: CLI option for headless operation
- **📝 Comprehensive Logging**: Detailed logging for all trading activities with dedicated Log management

## 📋 Prerequisites

- Python 3.8 or higher
- Kite Connect API credentials
- Active trading account with Zerodha

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Strangle10Points
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env_example.txt .env
   ```
   
   Edit the `.env` file with your Kite Connect credentials:
   ```
   KITE_API_KEY=your_api_key_here
   KITE_API_SECRET=your_api_secret_here
   KITE_ACCOUNT=your_account_here
   ```
   
   **Note**: The `KITE_REQUEST_TOKEN` is no longer required in the `.env` file. StockSage will automatically generate the access token from the request token you provide in the UI.

## 🔐 Authentication

StockSage features an improved authentication workflow:

1. **Environment Setup**: Store your `KITE_API_KEY` and `KITE_API_SECRET` in the `.env` file
2. **Request Token**: Generate a request token from your Kite Connect console
3. **Automatic Token Generation**: StockSage automatically generates an access token from your request token
4. **Seamless Trading**: Once authenticated, the bot starts trading immediately

This eliminates the need to manually manage access tokens and provides a more user-friendly experience.

## 🎯 Usage

### Web Interface (Recommended)

1. **Start the StockSage web application**
   ```bash
   streamlit run app.py
   ```

2. **Open your browser** and navigate to `http://localhost:8501`

3. **Configure StockSage** using the modern sidebar interface:
   - API Key and Secret are automatically loaded from your `.env` file
   - Set call and put quantities
   - Adjust delta range if needed
   - Click "🚀 Start Bot" to begin trading
   - Enter your request token when prompted (StockSage will automatically generate the access token)

### Command Line Interface

```bash
python main.py --api-key YOUR_API_KEY --api-secret YOUR_API_SECRET --request-token YOUR_REQUEST_TOKEN --account YOUR_ACCOUNT --call-quantity 50 --put-quantity 50
```

Or use environment variables:
```bash
python main.py
```

## 📊 Strategy Overview

### Core Strategy: AI-Enhanced Strangle with Dynamic Stop-Loss and VWAP Analysis

1. **🧠 AI-Powered Strike Selection**: 
   - Finds call and put options with delta between 0.29-0.35
   - Selects strikes with minimal price difference (< 1.5%)
   - **NEW**: Analyzes 5-minute VWAP for optimal entry timing

2. **📈 Advanced VWAP Analysis**:
   - Calculates 5-minute Volume Weighted Average Price for each strike
   - Prioritizes strikes where current price < VWAP (indicating potential reversal)
   - Provides detailed VWAP analysis in logs for decision-making

3. **🔄 Intelligent Position Management**:
   - Sells both call and put options
   - Places stop-loss orders based on day-specific percentages
   - Monitors delta changes and rebalances if needed

4. **🛡️ Smart Risk Management**:
   - Dynamic stop-loss adjustment at 14 and 28 points
   - Hedge positions triggered at 10 points profit
   - Maximum 3 stop-loss triggers per session

5. **📅 Adaptive Stop-Loss by Day**:
   - Tuesday: 30% (Weekly expiry day - higher stop loss)
   - Wednesday: 27%
   - Thursday: 25%
   - Friday: 25%
   - Monday: 30%
   - Default: 25%

## 🏗️ Project Structure

```
StockSage/
├── src/                    # Source code
│   ├── __init__.py
│   ├── kite_client.py      # Kite Connect API wrapper with VWAP functionality
│   ├── options_calculator.py # Options calculations and VWAP analysis
│   ├── trading_bot.py      # Main trading bot logic
│   └── utils.py            # Utility functions
├── Log/                    # Dedicated log directory
├── app.py                  # StockSage web application with modern UI
├── main.py                 # Command line interface
├── config.py               # Configuration constants
├── requirements.txt        # Python dependencies
├── env_example.txt         # Environment variables template
├── manage_logs.py          # Log management utilities
└── README.md              # This file
```

## ⚙️ Configuration

### Trading Parameters

- **Delta Range**: 0.29 - 0.35 (configurable)
- **Call/Put Quantities**: Default 50 each (configurable)
- **Market Hours**: 9:15 AM - 3:30 PM IST
- **Trading Start**: 9:45 AM IST

### VWAP Configuration

- **VWAP Minutes**: 5 minutes (configurable)
- **VWAP Enabled**: True/False to enable/disable VWAP analysis
- **VWAP Priority**: True/False to prioritize VWAP-suitable strikes

### API Configuration

- **VIX Fetch Interval**: 120 seconds
- **Hedge Points Difference**: 100 points
- **Max Price Difference**: 1.5%
- **Max Stop-Loss Triggers**: 3

## 📈 VWAP Analysis Features

### What is VWAP?
Volume Weighted Average Price (VWAP) is a trading indicator that shows the average price a security has traded at throughout the day, based on both volume and price.

### VWAP Integration Benefits:
1. **Better Entry Timing**: Identifies when strikes are trading below their VWAP, indicating potential reversal
2. **Enhanced Decision Making**: Provides detailed VWAP analysis for each strike pair
3. **Risk Reduction**: Prioritizes strikes with favorable VWAP conditions
4. **Detailed Logging**: Comprehensive VWAP analysis in trading logs

### VWAP Analysis Output:
```
============================================================
ANALYZING STRIKE PAIR:
Call: NIFTY24JAN19000CE | Price: 45.20 | VWAP: 47.85 | Delta: 0.325
Put:  NIFTY24JAN19000PE | Price: 42.10 | VWAP: 44.30 | Delta: 0.312
Price Difference: 3.10 (3.65%)
Call below VWAP: True
Put below VWAP: True
Both below VWAP: True
============================================================
SUITABLE PAIRS SUMMARY:
Total suitable pairs found: 3
Pairs with both strikes below VWAP: 2
1. ✅ VWAP-SUITABLE | Call: NIFTY24JAN19000CE | Put: NIFTY24JAN19000PE | Diff: 3.65%
2. ⚠️ PRICE-ONLY | Call: NIFTY24JAN19100CE | Put: NIFTY24JAN19100PE | Diff: 2.10%
```

## 📈 Monitoring

### StockSage Dashboard Features

- **🎨 Modern UI**: Beautiful, responsive design with professional branding
- **📊 Real-time Analytics**: Live P&L charts and market status
- **🔍 Live Monitoring**: Real-time bot status and trading logs
- **⚙️ Smart Configuration**: Intuitive sidebar for easy parameter adjustment
- **📱 Mobile Responsive**: Works seamlessly on all devices

### Log Files

Logs are automatically saved to the `Log/` directory with files named:
```
Log/{account}_{date}_trading_log.log
```

#### Log Management

StockSage includes a comprehensive log management system:

1. **Automatic Log Directory**: Logs are stored in a dedicated `Log/` folder
2. **Log Cleanup**: Automatically remove old log files to save disk space
3. **Log Management Script**: Use `manage_logs.py` to manage log files

**Log Management Commands:**
```bash
# List all log files
python manage_logs.py --list

# Show log statistics
python manage_logs.py --stats

# Clean up logs older than 30 days
python manage_logs.py --cleanup --days 30

# Clean up logs before starting bot
python main.py --cleanup-logs --log-days 30
```

**Log File Information:**
- **Location**: `Log/` directory (created automatically)
- **Naming**: `{account}_{date}_trading_log.log`
- **Content**: All trading activities, VWAP analysis, and error messages
- **Rotation**: New log file created each day
- **Cleanup**: Optional automatic cleanup of old files

## ⚠️ Important Notes

1. **Risk Disclaimer**: StockSage is for educational purposes. Trading involves risk and you may lose money.

2. **API Limits**: Be aware of Kite Connect API rate limits to avoid throttling.

3. **Market Hours**: StockSage is designed to work during Indian market hours.

4. **Testing**: Always test with small quantities before using real money.

5. **Monitoring**: Regularly monitor StockSage's performance and adjust parameters as needed.

6. **VWAP Analysis**: VWAP calculations require historical data and may be limited by API availability.

## 🔧 Troubleshooting

### Common Issues

1. **API Connection Errors**:
   - Verify your API credentials
   - Check internet connection
   - Ensure request token is valid

2. **No Suitable Strikes Found**:
   - Market may be closed
   - Delta range may be too restrictive
   - Check option chain availability

3. **VWAP Calculation Errors**:
   - Insufficient historical data
   - API rate limits exceeded
   - Check VWAP configuration settings

4. **Order Placement Failures**:
   - Insufficient margin
   - Market closed
   - Invalid strike prices

### Debug Mode

Enable detailed logging by modifying the log level in `src/utils.py`:
```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is for educational purposes. Use at your own risk.

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error messages
3. Create an issue in the repository

---

**⚠️ Disclaimer**: StockSage is provided as-is for educational purposes. Trading involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results.
