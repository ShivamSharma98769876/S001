# Browser Testing Guide for Broker ID Integration

## ✅ Automated Tests - All Passed!

All automated tests have passed:
- ✅ Helper function imports successfully
- ✅ Function returns 'DEFAULT' when not authenticated
- ✅ All 5 endpoints use `get_broker_id_from_auth()`
- ✅ Function has proper error handling
- ✅ Function uses `validate_kite_connection`

## 🌐 Browser Testing Steps

### Step 1: Start the Dashboard

```bash
# Option 1: Using app.py
python app.py

# Option 2: Using config_dashboard.py directly
python src/config_dashboard.py
```

The dashboard should start on: `http://localhost:8080`

### Step 2: Open Browser Developer Tools

1. Open your browser (Chrome/Firefox/Edge)
2. Press `F12` or `Ctrl+Shift+I` to open Developer Tools
3. Go to the **Console** tab
4. Go to the **Network** tab (to monitor API calls)

### Step 3: Test Authentication

1. Navigate to the dashboard
2. Authenticate with your Zerodha credentials
3. Check the console for any errors
4. Verify authentication status shows as "Authenticated"

### Step 4: Test API Endpoints

Open the browser console and run these tests:

#### Test 1: Check Auth Details (to see broker_id source)
```javascript
fetch('/api/auth/details')
  .then(r => r.json())
  .then(data => {
    console.log('Auth Details:', data);
    console.log('User ID:', data.details?.user_id);
    console.log('Account Name:', data.details?.account_name);
  });
```

#### Test 2: Test Trade History Endpoint
```javascript
fetch('/api/dashboard/trade-history')
  .then(r => r.json())
  .then(data => {
    console.log('Trade History:', data);
    console.log('Number of trades:', data.trades?.length || 0);
  });
```

#### Test 3: Test Cumulative P&L Endpoint
```javascript
fetch('/api/dashboard/cumulative-pnl')
  .then(r => r.json())
  .then(data => {
    console.log('Cumulative P&L:', data);
    console.log('All-time P&L:', data.all_time);
  });
```

#### Test 4: Test Daily Stats Endpoint
```javascript
fetch('/api/dashboard/daily-stats')
  .then(r => r.json())
  .then(data => {
    console.log('Daily Stats:', data);
    console.log('Daily Loss Used:', data.daily_loss_used);
  });
```

#### Test 5: Test P&L Calendar Endpoint
```javascript
fetch('/api/dashboard/pnl-calendar')
  .then(r => r.json())
  .then(data => {
    console.log('P&L Calendar:', data);
    console.log('Number of days:', data.length || 0);
  });
```

### Step 5: Verify Data Isolation (Multi-User Test)

If you have access to multiple Zerodha accounts:

1. **Test with Account 1**:
   - Authenticate with Account 1
   - Note the trades/P&L data
   - Check the broker_id being used (from auth details)

2. **Test with Account 2**:
   - Log out or clear session
   - Authenticate with Account 2
   - Verify the data is different (account-specific)
   - Check the broker_id is different

### Step 6: Test Fallback Behavior

1. **Test without Authentication**:
   - Clear authentication or don't authenticate
   - All endpoints should still work but use 'DEFAULT' broker_id
   - Verify no errors occur

2. **Test with Invalid Token**:
   - Use an expired/invalid access token
   - Verify function falls back gracefully
   - Check error messages are user-friendly

## 🔍 What to Check

### In Browser Console:
- ✅ No JavaScript errors
- ✅ No 404 errors for static files
- ✅ API endpoints return valid JSON
- ✅ No CORS errors

### In Network Tab:
- ✅ All API calls return status 200 (or appropriate status)
- ✅ Response times are reasonable
- ✅ No failed requests

### In Dashboard UI:
- ✅ Theme toggle works
- ✅ Auth details widget shows correct user info
- ✅ Daily loss card displays data
- ✅ Cumulative P&L chart renders
- ✅ Trade history table displays data
- ✅ Calendar heatmap renders
- ✅ All filters work correctly

## 🐛 Troubleshooting

### Issue: "broker_id is undefined"
**Solution**: Check that `get_broker_id_from_auth()` is being called correctly

### Issue: All users see same data
**Solution**: 
- Verify authentication is working
- Check that `kite_client_global` is set
- Verify profile is being retrieved correctly

### Issue: API returns 401 Unauthorized
**Solution**: 
- Authenticate first
- Check access token is valid
- Verify Kite connection is active

### Issue: Function returns 'DEFAULT' even when authenticated
**Solution**:
- Check `validate_kite_connection` is working
- Verify profile contains `user_id` or `user_name`
- Check `account_holder_name` is set

## 📊 Expected Results

### When Authenticated:
- `get_broker_id_from_auth()` returns user's `user_id` or `user_name`
- All endpoints filter data by this broker_id
- Each user sees only their own data

### When Not Authenticated:
- `get_broker_id_from_auth()` returns `'DEFAULT'`
- All endpoints use `'DEFAULT'` broker_id
- System still works but shows default data

## ✅ Success Criteria

1. ✅ All 5 endpoints use `get_broker_id_from_auth()`
2. ✅ Function returns correct broker_id when authenticated
3. ✅ Function falls back to 'DEFAULT' when not authenticated
4. ✅ No errors in browser console
5. ✅ All API endpoints return valid responses
6. ✅ Data is filtered by broker_id correctly
7. ✅ Multi-user isolation works (if testing with multiple accounts)

## 🎯 Quick Test Checklist

- [ ] Dashboard starts without errors
- [ ] Can authenticate with Zerodha
- [ ] Auth details endpoint shows user info
- [ ] Trade history endpoint returns data
- [ ] Cumulative P&L endpoint returns data
- [ ] Daily stats endpoint returns data
- [ ] P&L calendar endpoint returns data
- [ ] No JavaScript errors in console
- [ ] No 404 errors for static files
- [ ] All dashboard features work correctly

## 📝 Notes

- The broker_id is derived from the authenticated user's profile
- If profile is not available, it falls back to `account_holder_name`
- Final fallback is `'DEFAULT'` for backward compatibility
- All database queries now filter by broker_id automatically

