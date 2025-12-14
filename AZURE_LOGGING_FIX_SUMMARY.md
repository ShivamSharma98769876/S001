# Azure Logging Fix Summary

## Problem Identified

Logging works on local machine but **NOT writing to log files in Azure**.

## Root Cause

1. **Logger Hierarchy Mismatch:**
   - Strategy code uses `logging.info()` which calls the **root logger**
   - But handlers were only added to a **named logger** (`STRATEGY_{account}`)
   - Root logger had no file handler, so logs went to console only

2. **File Handler Buffering:**
   - File handler was buffering writes
   - Logs might not flush before process ends

3. **Handler Propagation:**
   - Named logger might not propagate to root correctly

## Changes Made

### 1. Always Add Handlers to Root Logger ✅

**Before:**
```python
logger = logging.getLogger(logger_name)
logger.addHandler(file_handler)  # Only added to named logger
```

**After:**
```python
logger = logging.getLogger(logger_name)
root_logger = logging.getLogger()  # Root logger

# Add to ROOT logger (what logging.info() uses)
root_logger.addHandler(file_handler)
root_logger.setLevel(logging.INFO)

# Also add to named logger if different
if logger_name != 'root':
    logger.addHandler(file_handler)
```

### 2. Immediate File Flush ✅

**Added:**
```python
file_handler.flush()  # Force write to disk
os.fsync(file_handler.stream.fileno())  # Force OS-level flush
```

### 3. Prevent Duplicate Handlers ✅

**Added check:**
```python
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == log_file for h in root_logger.handlers):
    root_logger.addHandler(file_handler)
```

### 4. Better Error Handling ✅

- Test file write access after creation
- Verify file exists and is writable
- Better error messages

### 5. Diagnostic Output ✅

- Print number of handlers on root logger
- Print number of handlers on named logger
- Verify file creation and write access

## Files Modified

1. **`src/environment.py`:**
   - `setup_azure_logging()` - Fixed to add handlers to root logger
   - `setup_local_logging()` - Fixed for consistency

## Expected Behavior After Fix

1. ✅ All `logging.info()` calls will write to file
2. ✅ Logs will flush immediately (no buffering)
3. ✅ File will be created and verified as writable
4. ✅ Both root logger and named logger have handlers
5. ✅ Logs appear in both:
   - Local file: `/tmp/Priti/logs/Priti_2025Dec14.log`
   - Azure Blob: `s0001strangle/Priti/logs/Priti_2025Dec14.log`

## Testing

After deploying to Azure:

1. Check log stream for: `[LOG SETUP] ✓ Log file created and writable`
2. Check log stream for: `Root logger handlers: X` (should be > 0)
3. Verify file exists: `/tmp/Priti/logs/Priti_2025Dec14.log`
4. Check Azure Blob: `s0001strangle/Priti/logs/Priti_2025Dec14.log`
5. Verify logs contain `[FLOW]`, `[EXPIRY]`, etc.

## Key Insight

**The critical fix:** Always add file handlers to the **root logger**, not just named loggers, because `logging.info()` uses the root logger by default.

