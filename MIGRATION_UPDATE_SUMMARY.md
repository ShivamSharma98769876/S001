# Migration Script Update Summary

## ✅ What Was Updated

The migration script `migrations/migrate_json_to_database.py` has been updated to process **all JSON files** from the `pnl_data` folder, not just `daily_pnl.json`.

## 🔄 Changes Made

### 1. Support for Multiple JSON Files
- **Before**: Only processed `daily_pnl.json`
- **After**: Processes all JSON files in `pnl_data/` folder

### 2. Support for Position Snapshot Format
- **New**: Detects and processes `position_snapshot_*.json` files
- **Format**: Each file contains timestamp and positions array
- **Handles**: Multiple snapshots of the same day

### 3. Dual Format Support
The script now handles two formats:

#### Format 1: Daily P&L Records (`daily_pnl.json`)
```json
{
  "records": [
    {
      "date": "2025-01-15",
      "non_equity_pnl": 1250.50,
      "positions": [...]
    }
  ]
}
```

#### Format 2: Position Snapshots (`position_snapshot_*.json`)
```json
{
  "timestamp": "2025-12-26T08:54:17",
  "positions": [
    {
      "trading_symbol": "BANKNIFTY25DEC59400CE",
      "entry_price": 93.65,
      "current_price": 48.0,
      "unrealized_pnl": 1597.75
    }
  ]
}
```

### 4. Smart Duplicate Detection
- Checks for duplicate trades before inserting
- Uses: symbol + date + similar price (within 1 rupee)
- Prevents duplicate entries from multiple snapshots

### 5. Daily Stats Aggregation
- Groups positions by date
- Calculates total P&L per day
- Creates/updates daily stats records

## 📋 How It Works

1. **Find All JSON Files**: Scans `pnl_data/` folder for all `.json` files
2. **Detect Format**: Identifies file format (daily_pnl vs position snapshot)
3. **Process Daily P&L**: If `daily_pnl.json` exists, processes it first
4. **Process Snapshots**: Processes all `position_snapshot_*.json` files
5. **Create Trades**: Creates trade records from positions
6. **Create Daily Stats**: Aggregates positions by date for daily statistics
7. **Verify**: Verifies migration by counting records

## 🚀 Usage

```bash
python migrations/migrate_json_to_database.py
```

## 📊 What Gets Migrated

### From Position Snapshots:
- **Trades**: Each position becomes a trade record
  - Trading symbol, exchange, prices
  - Entry/exit times from snapshot
  - P&L from unrealized_pnl
- **Daily Stats**: Aggregated by date
  - Total P&L per day
  - Number of positions per day

### From Daily P&L JSON:
- **Trades**: All positions from records
- **Daily Stats**: Daily P&L summaries

## ⚠️ Important Notes

1. **Duplicate Prevention**: The script checks for duplicates before inserting
   - Same symbol + same date + similar price = duplicate
   - Prevents multiple entries from repeated snapshots

2. **Backup**: 
   - `daily_pnl.json` gets individual backup
   - Position snapshots can be backed up to a backup folder

3. **Broker ID**: Uses `'DEFAULT'` broker_id
   - Can be changed in the script if needed
   - All migrated data uses the same broker_id

4. **Performance**: 
   - Processes files sequentially
   - Duplicate check may slow down with many files
   - Consider running during off-peak hours for large datasets

## 📈 Expected Results

After migration, you should see:
- **Trades table**: All positions from all JSON files
- **Daily stats table**: Aggregated daily P&L data
- **Backup files**: Original JSON files backed up

## 🔍 Verification

The script automatically verifies migration by:
- Counting trades in database
- Counting daily stats in database
- Reporting summary statistics

## 🐛 Troubleshooting

**Issue**: Too many duplicate warnings
- **Solution**: This is normal if you have many snapshots of the same positions
- The script will skip duplicates automatically

**Issue**: Migration is slow
- **Solution**: This is expected with many files
- The script processes files sequentially for data integrity

**Issue**: Some positions not migrated
- **Solution**: Check logs for error messages
- Missing required fields (trading_symbol, prices) will skip positions

## ✅ Next Steps

1. **Run Migration**:
   ```bash
   python migrations/migrate_json_to_database.py
   ```

2. **Verify Results**:
   - Check database for trades and daily stats
   - Review migration summary in console output

3. **Test Dashboard**:
   - Start dashboard: `python app.py`
   - Verify data appears in trade history
   - Check daily stats and P&L charts

## 📝 Summary

The migration script now:
- ✅ Processes all JSON files from `pnl_data/` folder
- ✅ Supports both daily_pnl.json and position snapshot formats
- ✅ Prevents duplicate entries
- ✅ Creates trades and daily stats
- ✅ Provides detailed logging and verification

**Ready to migrate all your historical data!** 🎉

