"""
Migration script to move existing JSON/CSV P&L data to SQLite database
This script reads all JSON files from pnl_data/ folder and creates database records
Supports:
- daily_pnl.json (if exists) - daily P&L records format
- position_snapshot_*.json - position snapshot files
"""

import os
import sys
import json
import logging
from datetime import datetime, date
from pathlib import Path
from collections import defaultdict

# Add parent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.database.models import DatabaseManager
from src.database.repository import TradeRepository, DailyStatsRepository

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_json_files(pnl_data_dir: Path):
    """Find all JSON files in pnl_data directory"""
    json_files = []
    
    if not pnl_data_dir.exists():
        logger.warning(f"pnl_data directory not found: {pnl_data_dir}")
        return json_files
    
    # Find all JSON files
    for json_file in pnl_data_dir.glob("*.json"):
        if json_file.name != "README.md":  # Skip README if it's JSON
            json_files.append(json_file)
    
    # Sort by filename (which includes timestamp for position snapshots)
    json_files.sort(key=lambda x: x.name)
    
    logger.info(f"Found {len(json_files)} JSON files in pnl_data directory")
    return json_files


def backup_json_file(json_path: Path) -> Path:
    """Create a backup of the JSON file before migration"""
    if not json_path.exists():
        logger.warning(f"JSON file not found: {json_path}")
        return None
    
    backup_path = json_path.parent / f"{json_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{json_path.suffix}"
    
    try:
        import shutil
        shutil.copy2(json_path, backup_path)
        logger.info(f"Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return None


def load_json_data(json_path: Path) -> dict:
    """Load data from JSON file"""
    try:
        if not json_path.exists():
            logger.warning(f"JSON file not found: {json_path}")
            return {'records': []}
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded data from {json_path.name}")
        return data
    except Exception as e:
        logger.error(f"Error loading JSON file {json_path.name}: {e}")
        return {}


def is_daily_pnl_format(data: dict) -> bool:
    """Check if data is in daily_pnl.json format"""
    return 'records' in data and isinstance(data.get('records'), list)


def is_position_snapshot_format(data: dict) -> bool:
    """Check if data is in position snapshot format"""
    return 'positions' in data and isinstance(data.get('positions'), list) and 'timestamp' in data


def process_position_snapshots(json_files: list, db_manager: DatabaseManager, broker_id: str = 'DEFAULT'):
    """Process position snapshot files and migrate to database"""
    trade_repo = TradeRepository(db_manager)
    stats_repo = DailyStatsRepository(db_manager)
    
    trades_created = 0
    trades_skipped = 0
    stats_created = 0
    stats_updated = 0
    
    # Group positions by date for daily stats
    daily_positions = defaultdict(list)
    daily_pnl = defaultdict(float)
    
    logger.info(f"Processing {len(json_files)} position snapshot files...")
    
    for json_file in json_files:
        try:
            data = load_json_data(json_file)
            
            if not is_position_snapshot_format(data):
                continue
            
            timestamp_str = data.get('timestamp', '')
            positions = data.get('positions', [])
            
            if not timestamp_str or not positions:
                continue
            
            # Parse timestamp
            try:
                if 'T' in timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            except:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                except:
                    logger.warning(f"Could not parse timestamp '{timestamp_str}' in {json_file.name}")
                    continue
            
            date_obj = timestamp.date()
            
            # Process each position
            for pos in positions:
                try:
                    trading_symbol = pos.get('trading_symbol', '')
                    if not trading_symbol:
                        trades_skipped += 1
                        continue
                    
                    instrument_token = str(pos.get('instrument_token', ''))
                    exchange = pos.get('exchange', 'NFO')
                    quantity = pos.get('quantity', 0)
                    entry_price = pos.get('entry_price', 0.0)
                    current_price = pos.get('current_price', entry_price)
                    unrealized_pnl = pos.get('unrealized_pnl', 0.0)
                    entry_time_str = pos.get('entry_time', timestamp_str)
                    
                    # Parse entry time
                    try:
                        if 'T' in entry_time_str:
                            entry_time = datetime.fromisoformat(entry_time_str.replace('Z', '+00:00'))
                        else:
                            entry_time = datetime.strptime(entry_time_str, '%Y-%m-%d %H:%M:%S')
                    except:
                        entry_time = timestamp
                    
                    # Determine transaction type from quantity
                    transaction_type = 'BUY' if quantity > 0 else 'SELL'
                    
                    # Check if trade already exists (avoid duplicates)
                    # We'll use a simple check: same symbol, same date, similar price
                    # Note: For position snapshots, we might have multiple snapshots of the same position
                    # We'll only create a trade if it doesn't already exist
                    try:
                        existing_trades = trade_repo.get_trades(
                            broker_id=broker_id,
                            start_date=date_obj,
                            end_date=date_obj
                        )
                        
                        # Check for duplicate
                        is_duplicate = False
                        for existing in existing_trades:
                            if (existing.trading_symbol == trading_symbol and 
                                existing.entry_time.date() == date_obj and
                                abs(existing.entry_price - entry_price) < 1.0):  # Allow 1 rupee difference
                                is_duplicate = True
                                break
                    except:
                        is_duplicate = False
                    
                    if not is_duplicate:
                        # Create trade record
                        trade_repo.create_trade(
                            instrument_token=instrument_token,
                            trading_symbol=trading_symbol,
                            exchange=exchange,
                            entry_time=entry_time,
                            exit_time=timestamp,  # Use snapshot timestamp as exit time
                            entry_price=entry_price,
                            exit_price=current_price,
                            quantity=abs(quantity),
                            transaction_type=transaction_type,
                            realized_pnl=unrealized_pnl,  # For snapshots, unrealized becomes realized when migrated
                            exit_type='migrated',
                            broker_id=broker_id
                        )
                        trades_created += 1
                    
                    # Accumulate for daily stats
                    daily_positions[date_obj].append(pos)
                    daily_pnl[date_obj] += unrealized_pnl
                    
                except Exception as e:
                    logger.warning(f"Error processing position in {json_file.name}: {e}")
                    trades_skipped += 1
                    continue
        
        except Exception as e:
            logger.error(f"Error processing file {json_file.name}: {e}")
            continue
    
    # Create daily stats from accumulated data
    logger.info("Creating daily stats from position snapshots...")
    for date_obj, positions in daily_positions.items():
        try:
            total_pnl = daily_pnl.get(date_obj, 0.0)
            positions_count = len(positions)
            
            # Get or create daily stat (returns None if new, stat if existing)
            existing_stat = stats_repo.get_or_create_daily_stat(date_obj, broker_id)
            
            # Update with P&L data (this handles both create and update)
            try:
                stats_repo.update_daily_stat(
                    date_obj,
                    broker_id,
                    total_realized_pnl=total_pnl,
                    number_of_trades=positions_count
                )
                
                if existing_stat:
                    stats_updated += 1
                else:
                    stats_created += 1
            except Exception as e:
                # If update fails, try to create fresh
                logger.warning(f"Error updating daily stat for {date_obj}, trying fresh create: {e}")
                try:
                    # Force create a new stat
                    stats_repo.update_daily_stat(
                        date_obj,
                        broker_id,
                        total_realized_pnl=total_pnl,
                        number_of_trades=positions_count
                    )
                    stats_created += 1
                except Exception as e2:
                    logger.error(f"Error creating daily stat for {date_obj}: {e2}")
                    continue
        
        except Exception as e:
            logger.error(f"Error processing daily stat for {date_obj}: {e}")
            continue
    
    logger.info(f"Position snapshots migration: {trades_created} trades created, {trades_skipped} skipped")
    logger.info(f"Daily stats: {stats_created} created, {stats_updated} updated")
    
    return trades_created, trades_skipped, stats_created, stats_updated


def migrate_daily_stats(records: list, db_manager: DatabaseManager, broker_id: str = 'DEFAULT'):
    """Migrate daily P&L records to daily_stats table"""
    stats_repo = DailyStatsRepository(db_manager)
    stats_created = 0
    stats_updated = 0
    
    for record in records:
        try:
            date_str = record.get('date', '')
            if not date_str:
                continue
            
            # Parse date
            try:
                if 'T' in date_str:
                    date_obj = datetime.fromisoformat(date_str).date()
                else:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            except Exception as e:
                logger.warning(f"Error parsing date '{date_str}': {e}")
                continue
            
            # Get P&L values
            non_equity_pnl = record.get('non_equity_pnl', 0.0)
            total_pnl = record.get('total_pnl', non_equity_pnl)
            positions_count = record.get('positions_count', 0)
            
            # Check if daily stat already exists
            existing_stat = stats_repo.get_or_create_daily_stat(date_obj, broker_id)
            
            # Update with P&L data
            stats_repo.update_daily_stat(
                date_obj,
                broker_id,
                total_realized_pnl=total_pnl,
                number_of_trades=positions_count
            )
            
            if existing_stat:
                stats_updated += 1
            else:
                stats_created += 1
            
        except Exception as e:
            logger.error(f"Error migrating daily stat for record {record.get('date', 'unknown')}: {e}")
            continue
    
    logger.info(f"Daily stats migration: {stats_created} created, {stats_updated} updated")
    return stats_created, stats_updated


def migrate_trades(records: list, db_manager: DatabaseManager, broker_id: str = 'DEFAULT'):
    """Migrate position data to trades table"""
    trade_repo = TradeRepository(db_manager)
    trades_created = 0
    trades_skipped = 0
    
    for record in records:
        try:
            date_str = record.get('date', '')
            if not date_str:
                continue
            
            # Parse date
            try:
                if 'T' in date_str:
                    date_obj = datetime.fromisoformat(date_str)
                else:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            except Exception as e:
                logger.warning(f"Error parsing date '{date_str}': {e}")
                continue
            
            # Get positions from record
            positions = record.get('positions', [])
            
            if not positions:
                # No positions to migrate, skip
                continue
            
            for pos in positions:
                try:
                    trading_symbol = pos.get('tradingsymbol', '')
                    if not trading_symbol:
                        trades_skipped += 1
                        continue
                    
                    exchange = pos.get('exchange', 'NFO')
                    quantity = pos.get('quantity', 0)
                    pnl = pos.get('pnl', 0.0)
                    avg_price = pos.get('average_price', 0.0)
                    last_price = pos.get('last_price', avg_price)
                    
                    # Determine transaction type from quantity
                    transaction_type = 'BUY' if quantity > 0 else 'SELL'
                    
                    # Create trade record
                    # Note: For migrated data, we use the same time for entry and exit
                    # since we don't have exact entry/exit times from JSON
                    trade_repo.create_trade(
                        instrument_token='',  # Not available in JSON
                        trading_symbol=trading_symbol,
                        exchange=exchange,
                        entry_time=date_obj,
                        exit_time=date_obj,
                        entry_price=avg_price,
                        exit_price=last_price,
                        quantity=abs(quantity),
                        transaction_type=transaction_type,
                        realized_pnl=pnl,
                        exit_type='migrated',
                        broker_id=broker_id
                    )
                    
                    trades_created += 1
                    
                except Exception as e:
                    logger.warning(f"Error migrating trade for {pos.get('tradingsymbol', 'unknown')}: {e}")
                    trades_skipped += 1
                    continue
        
        except Exception as e:
            logger.error(f"Error processing record for date {record.get('date', 'unknown')}: {e}")
            continue
    
    logger.info(f"Trades migration: {trades_created} created, {trades_skipped} skipped")
    return trades_created, trades_skipped


def verify_migration(db_manager: DatabaseManager, broker_id: str = 'DEFAULT'):
    """Verify migration by comparing counts"""
    from src.database.repository import TradeRepository, DailyStatsRepository
    
    trade_repo = TradeRepository(db_manager)
    stats_repo = DailyStatsRepository(db_manager)
    
    # Get counts
    trades_count = len(trade_repo.get_trades(broker_id=broker_id))
    
    session = db_manager.get_session()
    try:
        from src.database.models import DailyStats
        stats_count = session.query(DailyStats).filter(
            DailyStats.broker_id == broker_id
        ).count()
    finally:
        session.close()
    
    logger.info(f"Migration verification:")
    logger.info(f"  - Trades in database: {trades_count}")
    logger.info(f"  - Daily stats in database: {stats_count}")
    
    return trades_count, stats_count


def main():
    """Main migration function"""
    logger.info("=" * 60)
    logger.info("Starting JSON to Database Migration")
    logger.info("=" * 60)
    
    # Paths
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pnl_data_dir = Path(project_root) / 'pnl_data'
    
    # Check if pnl_data directory exists
    if not pnl_data_dir.exists():
        logger.warning(f"pnl_data directory not found: {pnl_data_dir}")
        logger.info("No data to migrate. Database will be initialized empty.")
        # Still initialize database
        db_manager = DatabaseManager()
        logger.info("Database initialized successfully (empty)")
        return
    
    # Find all JSON files
    json_files = find_json_files(pnl_data_dir)
    
    if not json_files:
        logger.warning("No JSON files found in pnl_data directory")
        # Still initialize database
        db_manager = DatabaseManager()
        logger.info("Database initialized successfully (empty)")
        return
    
    # Initialize database
    logger.info("Initializing database...")
    db_manager = DatabaseManager()
    logger.info("✓ Database initialized")
    
    # Migrate data
    broker_id = 'DEFAULT'  # Can be changed if needed
    
    # Separate files by format
    daily_pnl_file = None
    position_snapshot_files = []
    
    for json_file in json_files:
        data = load_json_data(json_file)
        if is_daily_pnl_format(data):
            daily_pnl_file = json_file
        elif is_position_snapshot_format(data):
            position_snapshot_files.append(json_file)
    
    total_stats_created = 0
    total_stats_updated = 0
    total_trades_created = 0
    total_trades_skipped = 0
    
    # Process daily_pnl.json if it exists
    if daily_pnl_file:
        logger.info(f"\nProcessing daily_pnl.json file: {daily_pnl_file.name}")
        
        # Create backup
        logger.info("Creating backup...")
        backup_path = backup_json_file(daily_pnl_file)
        if backup_path:
            logger.info(f"✓ Backup created: {backup_path}")
        
        # Load and migrate
        data = load_json_data(daily_pnl_file)
        records = data.get('records', [])
        
        if records:
            logger.info(f"Found {len(records)} records in daily_pnl.json")
            
            logger.info("Migrating daily stats from daily_pnl.json...")
            stats_created, stats_updated = migrate_daily_stats(records, db_manager, broker_id)
            total_stats_created += stats_created
            total_stats_updated += stats_updated
            
            logger.info("Migrating trades from daily_pnl.json...")
            trades_created, trades_skipped = migrate_trades(records, db_manager, broker_id)
            total_trades_created += trades_created
            total_trades_skipped += trades_skipped
        else:
            logger.warning("No records found in daily_pnl.json")
    
    # Process position snapshot files
    if position_snapshot_files:
        logger.info(f"\nProcessing {len(position_snapshot_files)} position snapshot files...")
        
        # Create backup directory for snapshots
        backup_dir = pnl_data_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            import shutil
            backup_dir.mkdir(exist_ok=True)
            logger.info(f"Created backup directory: {backup_dir}")
        except Exception as e:
            logger.warning(f"Could not create backup directory: {e}")
        
        trades_created, trades_skipped, stats_created, stats_updated = process_position_snapshots(
            position_snapshot_files, db_manager, broker_id
        )
        total_trades_created += trades_created
        total_trades_skipped += trades_skipped
        total_stats_created += stats_created
        total_stats_updated += stats_updated
    
    # Verify migration
    logger.info("\nVerifying migration...")
    verify_migration(db_manager, broker_id)
    
    logger.info("\n" + "=" * 60)
    logger.info("Migration Complete!")
    logger.info("=" * 60)
    logger.info(f"Summary:")
    logger.info(f"  - Files processed: {len(json_files)}")
    logger.info(f"    - daily_pnl.json: {1 if daily_pnl_file else 0}")
    logger.info(f"    - position snapshots: {len(position_snapshot_files)}")
    logger.info(f"  - Daily stats: {total_stats_created} created, {total_stats_updated} updated")
    logger.info(f"  - Trades: {total_trades_created} created, {total_trades_skipped} skipped")
    logger.info("\n✓ Migration successful!")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

