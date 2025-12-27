# Database Migration Plan for Dashboard Features

## Current State Analysis

### Strangle10Points (Current)
- **Data Storage**: JSON and CSV files
  - `pnl_data/daily_pnl.json` - Daily P&L records in JSON format
  - `pnl_data/daily_pnl.csv` - Daily P&L records in CSV format
- **No Database**: Currently no SQLite database
- **Data Access**: File-based reading/writing via `PnLRecorder` class

### disciplined-Trader (Target Reference)
- **Data Storage**: SQLite database (`data/strangle.db`)
- **ORM**: SQLAlchemy with declarative models
- **Tables**:
  1. `positions` - Active and inactive positions
  2. `trades` - Completed trades with entry/exit details
  3. `daily_stats` - Daily statistics (loss used, P&L, etc.)
  4. `audit_logs` - Audit trail for critical operations
  5. `daily_purge_flags` - Track daily data purging
  6. `candles` - OHLCV candle data (optional)

---

## Why Database is Needed

### Current Limitations (File-Based)
1. ❌ **No Query Capabilities**: Can't filter, sort, or aggregate efficiently
2. ❌ **No Relationships**: Can't link trades to positions
3. ❌ **Performance Issues**: Reading entire JSON file for each query
4. ❌ **No Transactions**: Risk of data corruption
5. ❌ **Limited Filtering**: Hard to filter by date range, symbol, segment
6. ❌ **No Indexing**: Slow searches on large datasets
7. ❌ **Concurrency Issues**: File locking problems with multiple processes

### Benefits of SQLite Database
1. ✅ **Efficient Queries**: SQL queries for filtering, sorting, aggregating
2. ✅ **Relationships**: Foreign keys linking trades to positions
3. ✅ **Performance**: Indexed queries, fast lookups
4. ✅ **Transactions**: ACID compliance, data integrity
5. ✅ **Complex Filtering**: Easy date range, symbol, segment filtering
6. ✅ **Indexing**: Fast searches on broker_id, date, symbol, etc.
7. ✅ **Concurrency**: SQLite handles concurrent reads well
8. ✅ **Scalability**: Can handle thousands of trades efficiently

---

## Required Database Schema

### 1. Positions Table
```sql
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    broker_id VARCHAR(50) NOT NULL,  -- User ID from Kite API
    instrument_token VARCHAR(50) NOT NULL,
    trading_symbol VARCHAR(100) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    entry_time DATETIME NOT NULL,
    entry_price FLOAT NOT NULL,
    current_price FLOAT,
    quantity INTEGER NOT NULL,
    lot_size INTEGER DEFAULT 1,
    unrealized_pnl FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_broker_instrument_active ON positions(broker_id, instrument_token, is_active);
CREATE INDEX idx_broker_active ON positions(broker_id, is_active);
```

### 2. Trades Table
```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    broker_id VARCHAR(50) NOT NULL,  -- User ID from Kite API
    position_id INTEGER,  -- Foreign key to positions (optional)
    instrument_token VARCHAR(50) NOT NULL,
    trading_symbol VARCHAR(100) NOT NULL,
    exchange VARCHAR(10) NOT NULL,
    entry_time DATETIME NOT NULL,
    exit_time DATETIME NOT NULL,
    entry_price FLOAT NOT NULL,
    exit_price FLOAT NOT NULL,
    quantity INTEGER NOT NULL,  -- Positive for BUY, Negative for SELL
    transaction_type VARCHAR(10) NOT NULL DEFAULT 'BUY',  -- 'BUY' or 'SELL'
    realized_pnl FLOAT NOT NULL,
    is_profit BOOLEAN NOT NULL,
    exit_type VARCHAR(50) NOT NULL,  -- 'manual', 'auto_loss_limit', 'auto_trailing_sl', 'stop_loss'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_broker_trade_date ON trades(broker_id, exit_time);
CREATE INDEX idx_broker_trade_symbol ON trades(broker_id, trading_symbol);
CREATE INDEX idx_trade_date ON trades(exit_time);
```

### 3. Daily Stats Table
```sql
CREATE TABLE daily_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    broker_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    total_realized_pnl FLOAT DEFAULT 0.0,
    total_unrealized_pnl FLOAT DEFAULT 0.0,
    protected_profit FLOAT DEFAULT 0.0,
    number_of_trades INTEGER DEFAULT 0,
    daily_loss_used FLOAT DEFAULT 0.0,
    daily_loss_limit FLOAT DEFAULT 5000.0,
    loss_limit_hit BOOLEAN DEFAULT 0,
    trading_blocked BOOLEAN DEFAULT 0,
    trailing_sl_active BOOLEAN DEFAULT 0,
    trailing_sl_level FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(broker_id, date)
);

CREATE UNIQUE INDEX idx_broker_date ON daily_stats(broker_id, date);
```

### 4. Audit Logs Table (Optional but Recommended)
```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(100) NOT NULL,
    user VARCHAR(100),
    details TEXT,  -- JSON string
    ip_address VARCHAR(50)
);

CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_action ON audit_logs(action);
```

---

## Implementation Steps

### Phase 1: Database Setup
1. **Create Database Module**
   - Create `src/database/` directory
   - Create `src/database/models.py` with SQLAlchemy models
   - Create `src/database/repository.py` with CRUD operations
   - Create `src/database/__init__.py`

2. **Database Manager**
   - Initialize SQLite database
   - Create tables on first run
   - Handle migrations for schema changes
   - Set up connection pooling

3. **Dependencies**
   - Add `sqlalchemy` to `requirements.txt`
   - Install: `pip install sqlalchemy`

### Phase 2: Data Migration
1. **Migrate Existing JSON/CSV Data**
   - Read existing `pnl_data/daily_pnl.json`
   - Parse trade data from JSON
   - Insert into database tables
   - Verify data integrity

2. **Migration Script**
   - Create `migrate_to_database.py` script
   - Convert JSON records to database records
   - Handle duplicate detection
   - Preserve all historical data

### Phase 3: Update Code
1. **Replace File-Based Access**
   - Update `PnLRecorder` to use database
   - Or create new `TradeRepository` class
   - Update dashboard API endpoints to use database

2. **API Endpoints Update**
   - `/api/trades` - Query from database
   - `/api/cumulative-pnl` - Calculate from database
   - `/api/daily-stats` - Query daily_stats table
   - `/api/pnl-calendar` - Query trades by date range

### Phase 4: Dashboard Features
1. **Cumulative P&L Widget**
   - Query trades table for all-time, year, month, week, day
   - Calculate cumulative sums
   - Return JSON for frontend

2. **Trade History Table**
   - Query trades table with filters
   - Support date range, symbol, segment filtering
   - Calculate summary statistics (win rate, total profit/loss)

3. **P&L Calendar Heatmap**
   - Query daily_stats or aggregate from trades
   - Group by date
   - Return daily P&L values for calendar rendering

4. **Daily Loss Used Card**
   - Query daily_stats for today
   - Get daily_loss_used and daily_loss_limit
   - Calculate percentage

---

## Database Models (Python/SQLAlchemy)

### models.py Structure
```python
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean, ForeignKey, Index, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

class Position(Base):
    __tablename__ = 'positions'
    # ... (see full schema above)

class Trade(Base):
    __tablename__ = 'trades'
    # ... (see full schema above)

class DailyStats(Base):
    __tablename__ = 'daily_stats'
    # ... (see full schema above)

class DatabaseManager:
    def __init__(self, db_path: str = "data/strangle.db"):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self._create_tables()
    
    def _create_tables(self):
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        return self.SessionLocal()
```

---

## Repository Pattern Implementation

### TradeRepository Example
```python
class TradeRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_trade(self, trade_data: dict) -> Trade:
        """Create a new trade record"""
        session = self.db_manager.get_session()
        try:
            trade = Trade(**trade_data)
            session.add(trade)
            session.commit()
            return trade
        finally:
            session.close()
    
    def get_trades_by_date_range(self, start_date, end_date, broker_id=None):
        """Get trades within date range"""
        session = self.db_manager.get_session()
        try:
            query = session.query(Trade).filter(
                Trade.exit_time >= start_date,
                Trade.exit_time <= end_date
            )
            if broker_id:
                query = query.filter(Trade.broker_id == broker_id)
            return query.all()
        finally:
            session.close()
    
    def get_cumulative_pnl(self, broker_id=None, start_date=None):
        """Calculate cumulative P&L"""
        session = self.db_manager.get_session()
        try:
            query = session.query(func.sum(Trade.realized_pnl))
            if broker_id:
                query = query.filter(Trade.broker_id == broker_id)
            if start_date:
                query = query.filter(Trade.exit_time >= start_date)
            return query.scalar() or 0.0
        finally:
            session.close()
```

---

## Data Migration Strategy

### Migration Script Structure
```python
# migrate_json_to_database.py

from src.database.models import DatabaseManager, Trade, DailyStats
from src.pnl_recorder import PnLRecorder
from datetime import datetime

def migrate_json_to_database():
    """Migrate existing JSON/CSV data to SQLite database"""
    
    # Initialize database
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    
    # Load existing JSON data
    recorder = PnLRecorder()
    historical_records = recorder.get_historical_pnl()
    
    trades_created = 0
    stats_created = 0
    
    try:
        for record in historical_records:
            date_str = record['date']
            date_obj = datetime.fromisoformat(date_str).date()
            
            # Create daily stats
            daily_stat = DailyStats(
                broker_id='DEFAULT',  # Or get from record
                date=date_obj,
                total_realized_pnl=record.get('non_equity_pnl', 0.0),
                number_of_trades=record.get('positions_count', 0)
            )
            session.add(daily_stat)
            stats_created += 1
            
            # Create trades from positions (if available)
            positions = record.get('positions', [])
            for pos in positions:
                # Create trade record (you may need to adjust based on your data structure)
                trade = Trade(
                    broker_id='DEFAULT',
                    trading_symbol=pos.get('tradingsymbol', ''),
                    exchange=pos.get('exchange', ''),
                    entry_time=datetime.fromisoformat(date_str),
                    exit_time=datetime.fromisoformat(date_str),
                    entry_price=pos.get('average_price', 0.0),
                    exit_price=pos.get('last_price', 0.0),
                    quantity=pos.get('quantity', 0),
                    realized_pnl=pos.get('pnl', 0.0),
                    is_profit=pos.get('pnl', 0.0) >= 0,
                    exit_type='manual'
                )
                session.add(trade)
                trades_created += 1
        
        session.commit()
        print(f"Migration complete: {stats_created} daily stats, {trades_created} trades")
        
    except Exception as e:
        session.rollback()
        print(f"Migration error: {e}")
        raise
    finally:
        session.close()
```

---

## API Endpoint Updates

### Before (File-Based)
```python
@app.route('/api/trades')
def get_trades():
    # Read from JSON file
    with open('pnl_data/daily_pnl.json') as f:
        data = json.load(f)
    return jsonify(data['records'])
```

### After (Database-Based)
```python
@app.route('/api/trades')
def get_trades():
    from src.database.repository import TradeRepository
    from src.database.models import DatabaseManager
    
    db_manager = DatabaseManager()
    repo = TradeRepository(db_manager)
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    broker_id = get_current_broker_id()  # From authentication
    
    trades = repo.get_trades_by_date_range(start_date, end_date, broker_id)
    
    return jsonify([{
        'id': t.id,
        'symbol': t.trading_symbol,
        'entry_time': t.entry_time.isoformat(),
        'exit_time': t.exit_time.isoformat(),
        'entry_price': t.entry_price,
        'exit_price': t.exit_price,
        'quantity': t.quantity,
        'pnl': t.realized_pnl,
        'type': t.transaction_type
    } for t in trades])
```

---

## Dashboard Feature Requirements

### 1. Cumulative P&L Widget
**Database Query Needed:**
```python
# All-time cumulative
all_time_pnl = session.query(func.sum(Trade.realized_pnl)).filter(
    Trade.broker_id == broker_id
).scalar()

# Year-to-date
year_start = datetime(datetime.now().year, 1, 1)
ytd_pnl = session.query(func.sum(Trade.realized_pnl)).filter(
    Trade.broker_id == broker_id,
    Trade.exit_time >= year_start
).scalar()

# Month-to-date
month_start = datetime(datetime.now().year, datetime.now().month, 1)
mtd_pnl = session.query(func.sum(Trade.realized_pnl)).filter(
    Trade.broker_id == broker_id,
    Trade.exit_time >= month_start
).scalar()

# Week-to-date (Monday)
from datetime import timedelta
today = datetime.now().date()
week_start = today - timedelta(days=today.weekday())
wtd_pnl = session.query(func.sum(Trade.realized_pnl)).filter(
    Trade.broker_id == broker_id,
    Trade.exit_time >= week_start
).scalar()

# Day-to-date
today_start = datetime.now().replace(hour=0, minute=0, second=0)
dtd_pnl = session.query(func.sum(Trade.realized_pnl)).filter(
    Trade.broker_id == broker_id,
    Trade.exit_time >= today_start
).scalar()
```

### 2. Trade History Table
**Database Query Needed:**
```python
# Get trades with filters
query = session.query(Trade).filter(
    Trade.broker_id == broker_id
)

# Date filter
if start_date:
    query = query.filter(Trade.exit_time >= start_date)
if end_date:
    query = query.filter(Trade.exit_time <= end_date)

# Symbol filter
if symbol:
    query = query.filter(Trade.trading_symbol.like(f'%{symbol}%'))

# Calculate summary
total_trades = query.count()
total_profit = query.filter(Trade.realized_pnl > 0).with_entities(
    func.sum(Trade.realized_pnl)
).scalar() or 0.0
total_loss = abs(query.filter(Trade.realized_pnl < 0).with_entities(
    func.sum(Trade.realized_pnl)
).scalar() or 0.0)
net_pnl = query.with_entities(func.sum(Trade.realized_pnl)).scalar() or 0.0
win_rate = (query.filter(Trade.is_profit == True).count() / total_trades * 100) if total_trades > 0 else 0.0
```

### 3. P&L Calendar Heatmap
**Database Query Needed:**
```python
# Get daily P&L grouped by date
daily_pnl = session.query(
    func.date(Trade.exit_time).label('date'),
    func.sum(Trade.realized_pnl).label('pnl')
).filter(
    Trade.broker_id == broker_id,
    Trade.exit_time >= start_date,
    Trade.exit_time <= end_date
).group_by(
    func.date(Trade.exit_time)
).all()

# Convert to dictionary for calendar rendering
pnl_by_date = {str(row.date): row.pnl for row in daily_pnl}
```

### 4. Daily Loss Used Card
**Database Query Needed:**
```python
# Get today's daily stats
today = datetime.now().date()
daily_stat = session.query(DailyStats).filter(
    DailyStats.broker_id == broker_id,
    DailyStats.date == today
).first()

if daily_stat:
    loss_used = daily_stat.daily_loss_used
    loss_limit = daily_stat.daily_loss_limit
    percentage = (loss_used / loss_limit * 100) if loss_limit > 0 else 0.0
else:
    # Create default if not exists
    loss_used = 0.0
    loss_limit = 5000.0
    percentage = 0.0
```

---

## File Structure

```
Strangle10Points/
├── src/
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py          # SQLAlchemy models
│   │   └── repository.py      # CRUD operations
│   ├── pnl_recorder.py        # Update to use database
│   └── config_dashboard.py    # Update API endpoints
├── data/
│   └── strangle.db     # SQLite database (created automatically)
├── migrations/
│   └── migrate_json_to_database.py  # One-time migration script
└── requirements.txt           # Add sqlalchemy
```

---

## Migration Checklist

### Pre-Migration
- [ ] Backup existing JSON/CSV files
- [ ] Install SQLAlchemy: `pip install sqlalchemy`
- [ ] Create `src/database/` directory structure
- [ ] Create database models
- [ ] Create repository classes

### Migration
- [ ] Create migration script
- [ ] Test migration on copy of data
- [ ] Run migration on production data
- [ ] Verify data integrity
- [ ] Compare counts (JSON records vs DB records)

### Post-Migration
- [ ] Update `PnLRecorder` to use database
- [ ] Update dashboard API endpoints
- [ ] Test all API endpoints
- [ ] Update frontend to use new data format
- [ ] Keep JSON/CSV as backup (optional)

### Testing
- [ ] Test trade creation
- [ ] Test trade queries with filters
- [ ] Test cumulative P&L calculations
- [ ] Test daily stats updates
- [ ] Test calendar heatmap data
- [ ] Performance test with large datasets

---

## Backward Compatibility

### Option 1: Dual Write (Recommended for Transition)
- Write to both database AND JSON/CSV files
- Gradually phase out file writes
- Allows rollback if needed

### Option 2: Database Only
- Migrate all data to database
- Remove file-based code
- Cleaner but requires full migration

### Option 3: Hybrid
- Use database for new data
- Keep JSON/CSV for historical data
- Read from both sources

---

## Performance Considerations

### Indexing
- All foreign keys indexed
- Date columns indexed for range queries
- broker_id indexed for multi-tenant queries
- Composite indexes for common query patterns

### Query Optimization
- Use `func.sum()` for aggregations
- Limit results with `.limit()` for pagination
- Use `.filter()` before joins
- Cache frequently accessed data

### Database Size
- SQLite handles up to ~140TB
- For large datasets, consider:
  - Archiving old trades
  - Partitioning by date
  - Regular VACUUM operations

---

## Security Considerations

### Multi-Tenancy
- Always filter by `broker_id`
- Never expose data from other brokers
- Validate broker_id in all queries

### Data Validation
- Validate all inputs before database writes
- Use SQLAlchemy's type system
- Sanitize user inputs

### Backup Strategy
- Regular database backups
- Export to JSON/CSV periodically
- Azure Blob Storage backup (if on Azure)

---

## Summary

**YES, database changes are required** to implement the dashboard features properly. The current file-based approach (JSON/CSV) is insufficient for:

1. ✅ Efficient querying and filtering
2. ✅ Cumulative P&L calculations
3. ✅ Trade history with complex filters
4. ✅ P&L calendar heatmap
5. ✅ Daily statistics tracking
6. ✅ Performance with large datasets

**Recommended Approach:**
1. Set up SQLite database with SQLAlchemy
2. Create database models (trades, positions, daily_stats)
3. Migrate existing JSON/CSV data to database
4. Update code to use database instead of files
5. Implement dashboard features using database queries

This will provide a solid foundation for all the dashboard features and future enhancements.

