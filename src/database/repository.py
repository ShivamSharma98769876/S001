"""
Data Repository for CRUD operations
All operations support broker_id filtering for multi-tenancy
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_, desc
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from src.database.models import (
    Position, Trade, DailyStats, AuditLog, DatabaseManager
)
import logging

logger = logging.getLogger(__name__)


class TradeRepository:
    """Repository for trade operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_trade(
        self,
        instrument_token: str,
        trading_symbol: str,
        exchange: str,
        entry_time: datetime,
        exit_time: datetime,
        entry_price: float,
        exit_price: float,
        quantity: int,
        transaction_type: str = 'SELL',
        realized_pnl: float = 0.0,
        exit_type: str = 'manual',
        broker_id: str = 'DEFAULT',
        position_id: Optional[int] = None
    ) -> Trade:
        """Create a new trade record"""
        session = self.db_manager.get_session()
        try:
            is_profit = realized_pnl >= 0
            
            trade = Trade(
                broker_id=broker_id,
                position_id=position_id,
                instrument_token=instrument_token,
                trading_symbol=trading_symbol,
                exchange=exchange,
                entry_time=entry_time,
                exit_time=exit_time,
                entry_price=entry_price,
                exit_price=exit_price,
                quantity=quantity,
                transaction_type=transaction_type,
                realized_pnl=realized_pnl,
                is_profit=is_profit,
                exit_type=exit_type
            )
            session.add(trade)
            session.commit()
            session.refresh(trade)
            logger.info(f"Created trade: {trading_symbol} P&L: ₹{realized_pnl:.2f}")
            return trade
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating trade: {e}")
            raise
        finally:
            session.close()
    
    def get_trades(
        self,
        broker_id: str = 'DEFAULT',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        symbol: Optional[str] = None,
        exchange: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Trade]:
        """Get trades with optional filters"""
        session = self.db_manager.get_session()
        try:
            query = session.query(Trade).filter(
                Trade.broker_id == broker_id
            )
            
            if start_date:
                query = query.filter(Trade.exit_time >= start_date)
            if end_date:
                query = query.filter(Trade.exit_time <= end_date)
            if symbol:
                query = query.filter(Trade.trading_symbol.like(f'%{symbol}%'))
            if exchange:
                query = query.filter(Trade.exchange == exchange)
            
            query = query.order_by(desc(Trade.exit_time))
            
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            
            return query.all()
        finally:
            session.close()
    
    def get_trades_summary(
        self,
        broker_id: str = 'DEFAULT',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get trade summary statistics"""
        session = self.db_manager.get_session()
        try:
            query = session.query(Trade).filter(
                Trade.broker_id == broker_id
            )
            
            if start_date:
                query = query.filter(Trade.exit_time >= start_date)
            if end_date:
                query = query.filter(Trade.exit_time <= end_date)
            
            total_trades = query.count()
            
            if total_trades == 0:
                return {
                    'totalTrades': 0,
                    'totalProfit': 0.0,
                    'totalLoss': 0.0,
                    'netPnl': 0.0,
                    'winRate': 0.0
                }
            
            # Calculate profit trades
            profit_trades = query.filter(Trade.is_profit == True).count()
            win_rate = (profit_trades / total_trades * 100) if total_trades > 0 else 0.0
            
            # Calculate P&L sums
            total_profit = query.filter(Trade.realized_pnl > 0).with_entities(
                func.sum(Trade.realized_pnl)
            ).scalar() or 0.0
            
            total_loss = abs(query.filter(Trade.realized_pnl < 0).with_entities(
                func.sum(Trade.realized_pnl)
            ).scalar() or 0.0)
            
            net_pnl = query.with_entities(func.sum(Trade.realized_pnl)).scalar() or 0.0
            
            return {
                'totalTrades': total_trades,
                'totalProfit': round(total_profit, 2),
                'totalLoss': round(total_loss, 2),
                'netPnl': round(net_pnl, 2),
                'winRate': round(win_rate, 2)
            }
        finally:
            session.close()
    
    def get_cumulative_pnl(
        self,
        broker_id: str = 'DEFAULT',
        start_date: Optional[datetime] = None
    ) -> float:
        """Calculate cumulative P&L from start_date to now"""
        session = self.db_manager.get_session()
        try:
            query = session.query(func.sum(Trade.realized_pnl)).filter(
                Trade.broker_id == broker_id
            )
            
            if start_date:
                query = query.filter(Trade.exit_time >= start_date)
            
            result = query.scalar()
            return round(result or 0.0, 2)
        finally:
            session.close()
    
    def get_daily_pnl(
        self,
        broker_id: str = 'DEFAULT',
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Get daily P&L grouped by date"""
        session = self.db_manager.get_session()
        try:
            query = session.query(
                func.date(Trade.exit_time).label('date'),
                func.sum(Trade.realized_pnl).label('pnl'),
                func.count(Trade.id).label('trades_count')
            ).filter(
                Trade.broker_id == broker_id
            )
            
            if start_date:
                query = query.filter(func.date(Trade.exit_time) >= start_date)
            if end_date:
                query = query.filter(func.date(Trade.exit_time) <= end_date)
            
            query = query.group_by(func.date(Trade.exit_time)).order_by(
                func.date(Trade.exit_time)
            )
            
            results = query.all()
            
            return [
                {
                    'date': str(row.date),
                    'pnl': round(row.pnl or 0.0, 2),
                    'trades_count': row.trades_count
                }
                for row in results
            ]
        finally:
            session.close()


class PositionRepository:
    """Repository for position operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_or_update_position(
        self,
        instrument_token: str,
        trading_symbol: str,
        exchange: str,
        entry_price: float,
        quantity: int,
        lot_size: int = 1,
        current_price: Optional[float] = None,
        broker_id: str = 'DEFAULT'
    ) -> Position:
        """Create new position or update existing"""
        session = self.db_manager.get_session()
        try:
            # Check if active position exists
            position = session.query(Position).filter(
                and_(
                    Position.broker_id == broker_id,
                    Position.instrument_token == instrument_token,
                    Position.is_active == True
                )
            ).first()
            
            if position:
                # Update existing position
                position.quantity = quantity
                position.current_price = current_price or position.current_price
                position.updated_at = datetime.utcnow()
                if current_price:
                    # Calculate unrealized P&L
                    position.unrealized_pnl = (current_price - entry_price) * quantity * lot_size
            else:
                # Create new position
                position = Position(
                    broker_id=broker_id,
                    instrument_token=instrument_token,
                    trading_symbol=trading_symbol,
                    exchange=exchange,
                    entry_price=entry_price,
                    current_price=current_price or entry_price,
                    quantity=quantity,
                    lot_size=lot_size,
                    unrealized_pnl=0.0
                )
                session.add(position)
            
            session.commit()
            session.refresh(position)
            return position
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating/updating position: {e}")
            raise
        finally:
            session.close()
    
    def get_active_positions(self, broker_id: str = 'DEFAULT') -> List[Position]:
        """Get all active positions"""
        session = self.db_manager.get_session()
        try:
            return session.query(Position).filter(
                and_(
                    Position.broker_id == broker_id,
                    Position.is_active == True
                )
            ).all()
        finally:
            session.close()
    
    def deactivate_position(self, position_id: int, broker_id: str = 'DEFAULT'):
        """Mark position as inactive"""
        session = self.db_manager.get_session()
        try:
            position = session.query(Position).filter(
                and_(
                    Position.broker_id == broker_id,
                    Position.id == position_id
                )
            ).first()
            if position:
                position.is_active = False
                position.updated_at = datetime.utcnow()
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error deactivating position: {e}")
            raise
        finally:
            session.close()


class DailyStatsRepository:
    """Repository for daily statistics operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_or_create_daily_stat(
        self,
        stat_date: date,
        broker_id: str = 'DEFAULT'
    ) -> DailyStats:
        """Get or create daily stat for a date"""
        session = self.db_manager.get_session()
        try:
            daily_stat = session.query(DailyStats).filter(
                and_(
                    DailyStats.broker_id == broker_id,
                    DailyStats.date == stat_date
                )
            ).first()
            
            if not daily_stat:
                daily_stat = DailyStats(
                    broker_id=broker_id,
                    date=stat_date,
                    daily_loss_limit=5000.0
                )
                session.add(daily_stat)
                session.commit()
                session.refresh(daily_stat)
            
            return daily_stat
        except Exception as e:
            session.rollback()
            logger.error(f"Error getting/creating daily stat: {e}")
            raise
        finally:
            session.close()
    
    def update_daily_stat(
        self,
        stat_date: date,
        broker_id: str = 'DEFAULT',
        **kwargs
    ) -> DailyStats:
        """Update daily stat fields"""
        session = self.db_manager.get_session()
        try:
            # Query the object in the current session (don't use get_or_create_daily_stat)
            daily_stat = session.query(DailyStats).filter(
                and_(
                    DailyStats.broker_id == broker_id,
                    DailyStats.date == stat_date
                )
            ).first()
            
            if not daily_stat:
                # Create new if it doesn't exist
                daily_stat = DailyStats(
                    broker_id=broker_id,
                    date=stat_date,
                    daily_loss_limit=5000.0
                )
                session.add(daily_stat)
            
            # Update fields from kwargs
            for key, value in kwargs.items():
                if hasattr(daily_stat, key):
                    setattr(daily_stat, key, value)
            
            daily_stat.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(daily_stat)
            return daily_stat
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating daily stat: {e}")
            raise
        finally:
            session.close()
    
    def get_today_stats(self, broker_id: str = 'DEFAULT') -> Optional[DailyStats]:
        """Get today's daily statistics"""
        session = self.db_manager.get_session()
        try:
            today = date.today()
            return session.query(DailyStats).filter(
                and_(
                    DailyStats.broker_id == broker_id,
                    DailyStats.date == today
                )
            ).first()
        finally:
            session.close()
    
    def calculate_daily_pnl(self, stat_date: date, broker_id: str = 'DEFAULT') -> float:
        """Calculate total realized P&L for a date"""
        trade_repo = TradeRepository(self.db_manager)
        
        start_datetime = datetime.combine(stat_date, datetime.min.time())
        end_datetime = datetime.combine(stat_date, datetime.max.time())
        
        return trade_repo.get_cumulative_pnl(
            broker_id=broker_id,
            start_date=start_datetime
        ) - trade_repo.get_cumulative_pnl(
            broker_id=broker_id,
            start_date=end_datetime + timedelta(days=1)
        )


class AuditLogRepository:
    """Repository for audit log operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_audit_log(
        self,
        action: str,
        user: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Create an audit log entry"""
        session = self.db_manager.get_session()
        try:
            audit_log = AuditLog(
                action=action,
                user=user,
                details=details,
                ip_address=ip_address
            )
            session.add(audit_log)
            session.commit()
            session.refresh(audit_log)
            return audit_log
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating audit log: {e}")
            raise
        finally:
            session.close()

