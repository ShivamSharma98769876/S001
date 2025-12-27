# Dashboard Database Migration & Feature Implementation Plan

## Overview
This plan outlines the step-by-step implementation of database migration and dashboard features to match the disciplined-Trader application.

## Phase 1: Database Setup (Tasks 1-4)

### Task 1: Create Database Directory Structure
- Create `src/database/` directory
- Create `src/database/__init__.py`
- Create `src/database/models.py` with SQLAlchemy models
- Create `src/database/repository.py` with CRUD operations

**Models to Create:**
- `Position` - Active/inactive positions
- `Trade` - Completed trades
- `DailyStats` - Daily statistics
- `DatabaseManager` - Database connection manager

### Task 2: Create Database Repository Classes
- `TradeRepository` - Trade CRUD operations
- `PositionRepository` - Position CRUD operations
- `DailyStatsRepository` - Daily stats operations
- Helper methods for queries

### Task 3: Database Initialization
- Create `__init__.py` with exports
- Set up database path configuration
- Handle database creation on first run

### Task 4: Update Dependencies
- Add `sqlalchemy` to `requirements.txt`
- Document installation steps

## Phase 2: Data Migration (Task 5)

### Task 5: Create Migration Script
- Read existing JSON/CSV files
- Parse trade data
- Insert into database tables
- Handle duplicates
- Verify data integrity
- Create backup before migration

## Phase 3: Code Updates (Tasks 6-7)

### Task 6: Update PnLRecorder
- Modify to use database instead of files
- Keep backward compatibility during transition
- Update save methods to write to database

### Task 7: Update Dashboard API Endpoints
- Update existing endpoints to use database
- Maintain API compatibility
- Add error handling

## Phase 4: New API Endpoints (Tasks 8-10)

### Task 8: Cumulative P&L Endpoint
- `/api/cumulative-pnl`
- Calculate all-time, year, month, week, day P&L
- Return JSON for frontend

### Task 9: Daily Stats Endpoint
- `/api/daily-stats`
- Get today's daily statistics
- Return loss used, loss limit, trading status

### Task 10: Enhanced Trade History Endpoint
- Update `/api/trade-history`
- Add filtering by date range, symbol, segment
- Add summary statistics calculation
- Return formatted data for frontend

## Implementation Order

1. ✅ **Phase 1** - Database Setup (Foundation)
2. ✅ **Phase 2** - Data Migration (Move existing data)
3. ✅ **Phase 3** - Code Updates (Use database)
4. ✅ **Phase 4** - New Features (Dashboard APIs)

## Testing Checklist

After each phase:
- [ ] Database tables created correctly
- [ ] Data migration successful
- [ ] API endpoints working
- [ ] No data loss
- [ ] Backward compatibility maintained

## Files to Create/Modify

### New Files:
- `src/database/__init__.py`
- `src/database/models.py`
- `src/database/repository.py`
- `migrations/migrate_json_to_database.py`

### Modified Files:
- `requirements.txt` - Add sqlalchemy
- `src/pnl_recorder.py` - Update to use database
- `src/config_dashboard.py` - Update API endpoints

### Database File:
- `data/strangle.db` - Created automatically

## Risk Mitigation

1. **Backup First**: Always backup JSON/CSV files before migration
2. **Test Migration**: Test on copy of data first
3. **Dual Write**: Optionally write to both database and files during transition
4. **Rollback Plan**: Keep file-based code until database is verified

## Success Criteria

- ✅ Database created and initialized
- ✅ All existing data migrated successfully
- ✅ All API endpoints working with database
- ✅ No data loss or corruption
- ✅ Performance improved over file-based approach
- ✅ Ready for dashboard feature implementation

