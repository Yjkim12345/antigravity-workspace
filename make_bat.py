import os

bat_content = """@echo off
set "TEMP_DIR=%TEMP%\\antigravity_memos"
set "WATCH_DIR=%USERPROFILE%\\Desktop\\노션_자동업로드"

if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"
if not exist "%WATCH_DIR%" mkdir "%WATCH_DIR%"

for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "FILENAME=지식메모_%dt:~0,14%.txt"
set "TEMP_FILE=%TEMP_DIR%\\%FILENAME%"

echo. > "%TEMP_FILE%"
start "" /wait notepad.exe "%TEMP_FILE%"

for %%I in ("%TEMP_FILE%") do set SIZE=%%~zI

if %SIZE% GTR 5 (
    move "%TEMP_FILE%" "%WATCH_DIR%\\%FILENAME%" >nul
) else (
    del "%TEMP_FILE%"
)
"""

with open(r'c:\Users\user\Desktop\새법리_입력기.bat', 'w', encoding='cp949') as f:
    f.write(bat_content)
