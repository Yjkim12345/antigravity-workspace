@echo off
echo ===========================================
echo  Antigravity Workspace Sync DOWN (Pull)
echo ===========================================

cd /d "%~dp0"

echo [1/2] Fetching from remote...
git fetch origin
if %errorlevel% neq 0 (
    echo [ERROR] Failed to fetch. Check network or Git credentials.
    pause
    exit /b %errorlevel%
)

echo [2/2] Pulling changes...
:: Using --rebase to avoid ugly merge commits on simple fast-forwards
git pull origin main --rebase
if %errorlevel% neq 0 (
    echo [ERROR] Failed to pull. You might have local conflicts.
    echo Please resolve them manually using 'git status' and 'git rebase --continue'.
    pause
    exit /b %errorlevel%
)

echo.
echo ===========================================
echo  Sync DOWN completed successfully!
echo ===========================================
pause
