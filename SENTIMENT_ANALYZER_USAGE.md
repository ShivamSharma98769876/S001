# Greeks Sentiment Analyzer - Usage Guide

## Overview
The Greeks Sentiment Analyzer has been successfully integrated with both the standalone and modular trading bot programs. It provides real-time market sentiment analysis based on Vega, Theta, and Delta values across Nifty, Bank Nifty, and Fin Nifty.

## Features
- **Real-time Analysis**: Runs every 3 minutes during market hours
- **Multi-Index Support**: Analyzes Nifty, Bank Nifty, and Fin Nifty
- **Greeks Calculation**: Calculates Vega, Theta, and Delta for options
- **Sentiment Classification**: Bullish, Bearish, or Neutral based on threshold rules
- **Persistent Storage**: Master copy (daily) and live copy (every 3 minutes)

## Configuration

### Enable/Disable Sentiment Analysis
In `config.py`:
```python
GREEKS_ANALYSIS_ENABLED = True  # Set to False to disable
GREEKS_ANALYSIS_INTERVAL = 180  # 3 minutes in seconds
GREEKS_DELTA_MIN = 0.05         # Minimum delta for strike selection
GREEKS_DELTA_MAX = 0.6          # Maximum delta for strike selection
GREEKS_SENTIMENT_THRESHOLD = 5.0 # Threshold for sentiment classification
```

## Integration Status

### ✅ Standalone Program (`Straddle10PointswithSL-Limit.py`)
- **Status**: Fully Integrated
- **Features**: 
  - Automatic sentiment analysis every 3 minutes
  - Logs sentiment results to trading log
  - Graceful fallback if analyzer unavailable
- **Usage**: Run normally - sentiment analysis runs automatically

### ✅ Modular Bot (`src/trading_bot.py`)
- **Status**: Fully Integrated
- **Features**:
  - Automatic sentiment analysis every 3 minutes
  - Logs sentiment results to trading log
  - Graceful fallback if analyzer unavailable
- **Usage**: Run normally - sentiment analysis runs automatically

## How It Works

### 1. Master Copy (Daily)
- Created once per day at market open
- Stores baseline Greeks values
- Used as reference for sentiment calculation

### 2. Live Copy (Every 3 Minutes)
- Updated every 3 minutes during market hours
- Contains current market Greeks values
- Compared against master copy

### 3. Sentiment Calculation
- **Difference > +5**: Bullish (Green)
- **Difference -5 to +5**: Neutral (White)
- **Difference < -5**: Bearish (Red)
- **Multiple sentiments**: Final = Neutral

## Example Output

### Log Output
```
2025-09-12 10:51:40 - INFO - Running Greeks sentiment analysis...
2025-09-12 10:51:41 - INFO - Sentiment analysis completed successfully
2025-09-12 10:51:41 - INFO - Sentiment - NIFTY CE: Neutral
2025-09-12 10:51:41 - INFO - Sentiment - NIFTY PE: Neutral
2025-09-12 10:51:41 - INFO - Sentiment - BANKNIFTY CE: Neutral
2025-09-12 10:51:41 - INFO - Sentiment - BANKNIFTY PE: Bearish
2025-09-12 10:51:41 - INFO - Sentiment - FINNIFTY CE: Neutral
2025-09-12 10:51:41 - INFO - Sentiment - FINNIFTY PE: Bullish
```

### Data Files
- **Master Copy**: `data/greeks_master_copy.json`
- **Live Data**: `data/greeks_live_data.json`

## Testing

### Run Integration Test
```bash
python test_sentiment_integration.py
```

### Run Demo
```bash
python demo_sentiment_analysis.py
```

## Troubleshooting

### Common Issues

1. **Import Error**: 
   - Ensure `src/greeks_sentiment_analyzer.py` exists
   - Check Python path

2. **Configuration Error**:
   - Verify `GREEKS_ANALYSIS_ENABLED` is set in `config.py`
   - Check all required configuration parameters

3. **Data Directory Error**:
   - Ensure `data/` directory exists
   - Check write permissions

4. **KiteClient Error**:
   - Verify KiteConnect credentials
   - Check API access

### Log Messages
- **Success**: "Greeks Sentiment Analyzer initialized successfully"
- **Warning**: "Greeks Sentiment Analyzer not available. Sentiment analysis will be skipped."
- **Error**: "Failed to initialize Greeks Sentiment Analyzer: [error details]"

## Performance Notes

- **Memory Usage**: Minimal impact on bot performance
- **CPU Usage**: Lightweight analysis every 3 minutes
- **Storage**: Small JSON files (few KB each)
- **Network**: Uses existing KiteConnect API calls

## Future Enhancements

- **Web Dashboard**: Real-time sentiment display
- **Historical Analysis**: Trend analysis over time
- **Alert System**: Notifications for sentiment changes
- **Custom Thresholds**: Per-index sentiment thresholds

## Support

For issues or questions:
1. Check the logs for error messages
2. Run the integration test script
3. Verify configuration settings
4. Check KiteConnect API access

---

**Note**: The sentiment analyzer is designed to complement your existing trading strategy and does not interfere with the core trading logic.
