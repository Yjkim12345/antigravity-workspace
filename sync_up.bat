@echo off
echo =========================================
echo  Antigravity Workspace Sync UP (Push)
echo =========================================

cd /d "%~dp0"

echo [1/3] Adding changes...
git add .
if %errorlevel% neq 0 (
    echo [ERROR] Failed to add changes. Is Git installed and initialized?
    pause
    exit /b %errorlevel%
)

echo [2/3] Committing...
set /p commit_msg="Enter commit message (or press enter for default): "
if "%commit_msg%"=="" set commit_msg="Auto-sync from %COMPUTERNAME% at %DATE% %TIME%"

git commit -m "%commit_msg%"
:: It's okay if commit fails because there are no changes
if %errorlevel% neq 0 (
    echo [INFO] No changes to commit or commit failed.
)

echo [3/3] Pushing to remote...
git push origin main
if %errorlevel% neq 0 (
    echo [ERROR] Failed to push to remote. Check your network or remote URL.
    pause
    exit /b %errorlevel%
)

echo.
echo =========================================
echo  Sync UP completed successfully!
echo =========================================
pause
