# Quick Fix: Remove Secret from Git History

## The Problem
GitHub detected the Azure Storage Account key in commits `ac83088` and `35c451a`. Even though it's removed from current code, it's still in git history.

## Quick Solution (PowerShell)

Run these commands **one at a time**:

```powershell
# 1. Backup current state
git branch backup-before-secret-removal

# 2. Remove secret from all commits (this will take a few minutes)
git filter-branch --force --tree-filter "powershell -Command \"if (Test-Path src/config.py) { `$content = Get-Content src/config.py -Raw; `$content = `$content -replace 'AccountKey=2/ISQ/w7iTwGLYkGTc5h9Ly4rso1IKwADrcGqQnRvLsaNCryk4duOKUgJawXhXBuDdN0MJhM0a73\+AStu/d6UA==', 'AccountKey=[REMOVED_SECRET]'; [System.IO.File]::WriteAllText((Resolve-Path src/config.py), `$content) }\"" --prune-empty --tag-name-filter cat -- --all

# 3. Clean up git internals
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 4. Verify secret is gone (should return nothing)
git log -p --all | Select-String "2/ISQ"

# 5. Force push to GitHub (WARNING: Overwrites remote history!)
git push --force --all
```

## Alternative: Use BFG Repo-Cleaner (Easier)

1. Download BFG: https://rtyley.github.io/bfg-repo-cleaner/
2. Create `secrets.txt`:
   ```
   AccountKey=2/ISQ/w7iTwGLYkGTc5h9Ly4rso1IKwADrcGqQnRvLsaNCryk4duOKUgJawXhXBuDdN0MJhM0a73+AStu/d6UA==
   ```
3. Run:
   ```bash
   java -jar bfg.jar --replace-text secrets.txt .
   git reflog expire --expire=now --all && git gc --prune=now --aggressive
   git push --force --all
   ```

## After Fixing

1. ✅ Verify: `git log -p --all | Select-String "2/ISQ"` returns nothing
2. ✅ Force push: `git push --force --all`
3. ✅ **ROTATE THE KEY** in Azure Portal (it was exposed!)
4. ✅ Update `AzureBlobStorageKey` in Azure App Service with new key

## If Something Goes Wrong

```powershell
# Restore from backup
git reset --hard backup-before-secret-removal
```

