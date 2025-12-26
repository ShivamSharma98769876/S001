# Daily P&L Records

This directory contains daily P&L (Profit & Loss) records for non-equity trades (Options, Futures, Currency Derivatives, Commodities).

## Files

- **daily_pnl.json**: JSON file containing all historical P&L records with detailed position information
- **daily_pnl.csv**: CSV file containing daily P&L summary (easy to open in Excel)

## Data Structure

### JSON Format
```json
{
  "records": [
    {
      "date": "2025-01-15",
      "timestamp": "2025-01-15T14:50:00",
      "account": "YourAccount",
      "non_equity_pnl": 1250.50,
      "total_pnl": 1250.50,
      "equity_pnl": 0.0,
      "positions_count": 2,
      "positions": [
        {
          "tradingsymbol": "NIFTY24JAN19000CE",
          "exchange": "NFO",
          "product": "NRML",
          "quantity": 1,
          "pnl": 625.25,
          "pnl_percentage": 5.2,
          "average_price": 120.50,
          "last_price": 125.75
        }
      ]
    }
  ],
  "last_updated": "2025-01-15T14:50:00"
}
```

### CSV Format
The CSV file contains one row per day with the following columns:
- date
- timestamp
- account
- non_equity_pnl
- total_pnl
- equity_pnl
- positions_count

## When Data is Saved

P&L data is automatically saved:
- **Before market close** (at 14:50) when trades are being monitored
- **At market end time** if no trades were taken during the session

## Accessing Historical Data

You can use the `PnLRecorder` class to access historical data programmatically:

```python
from src.pnl_recorder import PnLRecorder
from datetime import date

recorder = PnLRecorder()

# Get all historical records
all_records = recorder.get_historical_pnl()

# Get records for a date range
from datetime import date, timedelta
start_date = date.today() - timedelta(days=30)
end_date = date.today()
recent_records = recorder.get_historical_pnl(start_date, end_date)
```

## Notes

- Only **non-equity** trades are recorded (NFO, CDS, MCX exchanges)
- Equity trades are excluded from the non-equity P&L calculation
- Data is saved in both JSON (detailed) and CSV (summary) formats
- If a record for today already exists, it will be updated with the latest data

