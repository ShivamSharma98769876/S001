"""
Migration script to move existing JSON/CSV P&L data to SQLite database
This script reads from pnl_data/daily_pnl.json and creates database records
"""

import os
import sys
import json
import logging
from datetime import datetime, date
from pathlib import Path

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
        
        logger.info(f"Loaded {len(data.get('records', []))} records from JSON")
        return data
    except Exception as e:
        logger.error(f"Error loading JSON file: {e}")
        return {'records': []}


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
    json_path = Path(project_root) / 'pnl_data' / 'daily_pnl.json'
    
    # Check if JSON file exists
    if not json_path.exists():
        logger.warning(f"JSON file not found: {json_path}")
        logger.info("No data to migrate. Database will be initialized empty.")
        # Still initialize database
        db_manager = DatabaseManager()
        logger.info("Database initialized successfully (empty)")
        return
    
    # Create backup
    logger.info("Creating backup of JSON file...")
    backup_path = backup_json_file(json_path)
    if backup_path:
        logger.info(f"✓ Backup created: {backup_path}")
    else:
        logger.warning("⚠ Could not create backup. Proceeding anyway...")
    
    # Load JSON data
    logger.info("Loading JSON data...")
    data = load_json_data(json_path)
    records = data.get('records', [])
    
    if not records:
        logger.warning("No records found in JSON file")
        # Still initialize database
        db_manager = DatabaseManager()
        logger.info("Database initialized successfully (empty)")
        return
    
    logger.info(f"Found {len(records)} records to migrate")
    
    # Initialize database
    logger.info("Initializing database...")
    db_manager = DatabaseManager()
    logger.info("✓ Database initialized")
    
    # Migrate data
    broker_id = 'DEFAULT'  # Can be changed if needed
    
    logger.info("\nMigrating daily stats...")
    stats_created, stats_updated = migrate_daily_stats(records, db_manager, broker_id)
    
    logger.info("\nMigrating trades...")
    trades_created, trades_skipped = migrate_trades(records, db_manager, broker_id)
    
    # Verify migration
    logger.info("\nVerifying migration...")
    verify_migration(db_manager, broker_id)
    
    logger.info("\n" + "=" * 60)
    logger.info("Migration Complete!")
    logger.info("=" * 60)
    logger.info(f"Summary:")
    logger.info(f"  - Daily stats: {stats_created} created, {stats_updated} updated")
    logger.info(f"  - Trades: {trades_created} created, {trades_skipped} skipped")
    if backup_path:
        logger.info(f"  - Backup saved: {backup_path}")
    logger.info("\n✓ Migration successful!")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

