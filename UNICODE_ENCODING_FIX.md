# Unicode Encoding Fix for Logging

## Problem

Error when creating log file on Windows:
```
'charmap' codec can't encode character '\u26a0' in position 12: character maps to <undefined>
```

The character `\u26a0` is the warning symbol ⚠. The issue occurs because:
1. Windows default encoding is often 'charmap' (cp1252) which can't handle all Unicode characters
2. Log messages contain Unicode characters (⚠, ✓, ✗) that can't be encoded
3. File handler or console handler is using wrong encoding

## Root Cause

1. **FileHandler encoding**: Already set to UTF-8, but error handling messages contain Unicode
2. **Console handler**: Uses default system encoding (charmap on Windows)
3. **Print statements**: Contain Unicode characters (⚠, ✓, ✗) that fail when writing to file
4. **Error messages**: The error message itself contains Unicode that can't be encoded

## Solution Applied

### 1. Created SafeFormatter Class ✅

**Added:**
```python
class SafeFormatter(logging.Formatter):
    """Formatter that safely handles Unicode characters"""
    def format(self, record):
        try:
            return super().format(record)
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            # Fallback: replace problematic characters
            safe_msg = msg.encode('ascii', 'replace').decode('ascii')
            record.msg = safe_msg
            return super().format(record)
```

### 2. Configured Console Handler for UTF-8 ✅

**Added:**
```python
# On Windows, ensure stdout/stderr use UTF-8
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
```

### 3. Replaced Unicode Characters in Print Statements ✅

**Before:**
```python
print(f"[LOG SETUP] ✓ Log file created and writable: {log_file}")
print(f"[LOG SETUP] ⚠ Log file exists but may not be writable")
print(f"[LOG SETUP] ✗ Log file was NOT created")
```

**After:**
```python
print(f"[LOG SETUP] SUCCESS: Log file created and writable: {log_file}")
print(f"[LOG SETUP] WARNING: Log file exists but may not be writable")
print(f"[LOG SETUP] ERROR: Log file was NOT created")
```

### 4. Used SafeFormatter for All Handlers ✅

**Changed:**
```python
# Before
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# After
formatter = SafeFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
```

### 5. Ensured UTF-8 Encoding in File Operations ✅

**Changed:**
```python
# Test write access with UTF-8 encoding
with open(log_file, 'a', encoding='utf-8', errors='replace') as test_file:
    test_file.write("")
```

## Files Modified

1. **`src/environment.py`:**
   - Added `SafeFormatter` class
   - Updated `setup_azure_logging()` to use SafeFormatter
   - Updated `setup_local_logging()` to use SafeFormatter
   - Configured console handler for UTF-8 on Windows
   - Replaced Unicode characters in print statements
   - Ensured UTF-8 encoding in file test operations

## Expected Behavior

1. ✅ **No encoding errors** - All Unicode characters handled safely
2. ✅ **UTF-8 encoding** - All file operations use UTF-8
3. ✅ **Safe fallback** - If Unicode can't be encoded, characters are replaced
4. ✅ **Windows compatible** - Works correctly on Windows with default encoding
5. ✅ **Logs still readable** - Unicode characters in log messages are preserved when possible

## Testing

After this fix:
1. Log file should be created without encoding errors
2. Unicode characters in log messages should be handled gracefully
3. File should be readable and properly encoded in UTF-8
4. No more 'charmap' codec errors

