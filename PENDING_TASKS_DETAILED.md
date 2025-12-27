# Detailed Pending Tasks

## 🔴 CRITICAL - Must Fix Before Production

### 1. Broker ID Integration (5 locations)
**Problem**: All database queries use hardcoded `broker_id = 'DEFAULT'`

**Affected Endpoints**:
1. `/api/dashboard/trade-history` - Line 919
2. `/api/dashboard/cumulative-pnl` - Line 1052
3. `/api/dashboard/daily-stats` - Line 1120
4. `/api/dashboard/pnl-calendar` - Line 1186
5. `/api/dashboard/sync-orders` - Line 1248

**Current Code**:
```python
broker_id = 'DEFAULT'  # TODO: Get from authentication
```

**What Needs to be Done**:
- Create helper function to get broker_id from authenticated user
- Update all 5 endpoints to use the helper function
- Ensure it falls back to 'DEFAULT' if not authenticated

**Impact**: Without this, all users see the same data (no multi-user support)

---

## 🟡 HIGH PRIORITY - Testing & Verification

### 2. Run Test Script
**Status**: Test script created but not run yet

**Action**: Run `python test_implementation.py`

**What it tests**:
- SQLAlchemy installation
- Database initialization
- Model imports
- Repository classes
- Database queries
- Static files existence
- Flask app import
- API routes
- Database tables

### 3. Test Database Creation
**Action**: Verify database file is created

**Expected**: `data/strangle.db` should be created automatically

**Test**:
```python
from src.database.models import DatabaseManager
db = DatabaseManager()
print(f"Database: {db.db_path}")
```

### 4. Test API Endpoints
**Action**: Test each endpoint returns valid JSON

**Endpoints to test**:
- `GET /api/dashboard/cumulative-pnl`
- `GET /api/dashboard/daily-stats`
- `GET /api/dashboard/pnl-calendar`
- `GET /api/dashboard/trade-history`
- `GET /api/auth/details`

### 5. Test Frontend Features
**Action**: Start dashboard and test in browser

**Features to test**:
- Theme toggle
- Auth details widget
- Daily loss card
- Cumulative P&L chart
- Trade history table
- Calendar heatmap
- Help modals
- All filters

### 6. Data Migration (if you have existing data)
**Action**: Run migration script

**Command**: `python migrations/migrate_json_to_database.py`

**What it does**:
- Creates backup of JSON files
- Migrates data to database
- Verifies migration success

---

## 🟠 MEDIUM PRIORITY - Enhancements

### 7. Sync Orders Field Mapping
**Location**: `/api/dashboard/sync-orders` - Line 1190

**Issue**: Simplified implementation, may need field adjustments

**What Needs to be Done**:
- Test with real Zerodha orders API response
- Verify field mappings match actual API structure
- Handle different order types
- Test edge cases

### 8. Status Indicator Real-time Updates
**Issue**: Heartbeat animation exists but may not update based on connection

**What Needs to be Done**:
- Connect heartbeat to actual connection status
- Update status text dynamically
- Test status changes in real-time

### 9. User Profile Data Population
**Issue**: User info section in header needs data

**What Needs to be Done**:
- Populate user name from `/api/auth/details`
- Populate user ID from API
- Update when auth status changes

---

## 🟢 LOW PRIORITY - Optional Features

### 10. Advanced Date Range Picker
**Status**: Basic date filter exists

**Could Add**:
- Modal-based calendar picker
- Quick options (Last 7 days, Last 30 days, etc.)
- Better UX

### 11. Enhanced Notifications Panel
**Status**: Basic notifications exist

**Could Add**:
- Fixed position panel
- Auto-dismiss
- Notification history

### 12. Performance Optimizations
**Status**: Basic implementation complete

**Could Add**:
- Caching for cumulative P&L
- Pagination for trade tables
- Lazy loading

---

## 📊 Summary by Priority

### Critical (Do First):
1. ✅ Fix broker_id integration (5 locations)
2. ✅ Run test script
3. ✅ Test database creation
4. ✅ Test API endpoints
5. ✅ Test frontend features
6. ✅ Run migration (if you have data)

### High Priority (Do Next):
7. ⚠️ Verify sync orders works
8. ⚠️ Test status indicator updates
9. ⚠️ Populate user profile data

### Medium Priority (Nice to Have):
10. 💡 Advanced date picker
11. 💡 Enhanced notifications
12. 💡 Performance optimizations

---

## 🎯 Recommended Order

1. **First**: Fix broker_id integration (critical for multi-user)
2. **Second**: Run tests and verify everything works
3. **Third**: Run migration if you have existing data
4. **Fourth**: Test all features in browser
5. **Fifth**: Fix any bugs found during testing
6. **Sixth**: Add optional enhancements if needed

---

## Quick Fix for Broker ID

Here's what needs to be added to fix the broker_id issue:

```python
def get_broker_id_from_auth():
    """Get broker_id from authenticated user"""
    global kite_client_global
    
    if kite_client_global and hasattr(kite_client_global, 'kite'):
        try:
            profile = kite_client_global.kite.profile()
            return profile.get('user_id') or profile.get('user_name') or 'DEFAULT'
        except:
            return 'DEFAULT'
    return 'DEFAULT'
```

Then replace all instances of:
```python
broker_id = 'DEFAULT'  # TODO: Get from authentication
```

With:
```python
broker_id = get_broker_id_from_auth()
```

---

## Current Status

✅ **Completed**: ~95% of implementation
⚠️ **Pending**: Broker ID integration, testing, verification
💡 **Optional**: Advanced features, optimizations

**Bottom Line**: The implementation is functionally complete, but needs:
1. Broker ID fix (critical)
2. Testing and verification
3. Optional enhancements

