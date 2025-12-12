# Removing Azure Storage Account Key from Git History

GitHub has detected the Azure Storage Account key in your git history. Even though it's been removed from the current code, it still exists in previous commits.

## Option 1: Using git filter-branch (Works on Windows PowerShell)

Run these commands one by one:

```powershell
# 1. Create a backup branch
git branch backup-before-secret-removal

# 2. Remove the secret from all commits
git filter-branch --force --tree-filter `
    "if (Test-Path src/config.py) { `$content = Get-Content src/config.py -Raw; `$content = `$content -replace 'AccountKey=2/ISQ/w7iTwGLYkGTc5h9Ly4rso1IKwADrcGqQnRvLsaNCryk4duOKUgJawXhXBuDdN0MJhM0a73\+AStu/d6UA==', 'AccountKey=[REMOVED_SECRET]'; Set-Content src/config.py -Value `$content -NoNewline }" `
    --prune-empty --tag-name-filter cat -- --all

# 3. Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 4. Verify the secret is gone
git log -p --all | Select-String "2/ISQ"

# 5. Force push (WARNING: This overwrites remote history!)
git push --force --all
```

## Option 2: Using BFG Repo-Cleaner (Easier, but requires Java)

1. Download BFG from: https://rtyley.github.io/bfg-repo-cleaner/
2. Create a file `secrets.txt` with the secret to remove:
   ```
   AccountKey=2/ISQ/w7iTwGLYkGTc5h9Ly4rso1IKwADrcGqQnRvLsaNCryk4duOKUgJawXhXBuDdN0MJhM0a73+AStu/d6UA==
   ```
3. Run:
   ```bash
   git clone --mirror your-repo-url.git
   java -jar bfg.jar --replace-text secrets.txt your-repo-url.git
   cd your-repo-url.git
   git reflog expire --expire=now --all && git gc --prune=now --aggressive
   git push --force
   ```

## Option 3: Interactive Rebase (For few commits)

If you only have a few commits with the secret:

```bash
# Find commits with the secret
git log --all --source --full-history -- src/config.py | grep -B 5 "2/ISQ"

# Interactive rebase to edit those commits
git rebase -i <commit-before-first-secret>

# In the editor, mark commits as 'edit', then:
# - Edit src/config.py to remove/replace the secret
# - git add src/config.py
# - git commit --amend --no-edit
# - git rebase --continue
```

## Important Notes:

1. **Backup First**: Always create a backup branch before rewriting history
2. **Force Push Required**: After rewriting history, you'll need to force push
3. **Team Coordination**: If others have cloned the repo, they'll need to re-clone
4. **Rotate the Key**: Since the key was exposed, consider rotating it in Azure Portal

## After Removing the Secret:

1. Verify it's gone: `git log -p --all | grep "2/ISQ"` (should return nothing)
2. Force push: `git push --force --all`
3. Rotate the Azure Storage Account key in Azure Portal
4. Update the `AzureBlobStorageKey` environment variable in Azure App Service with the new key

