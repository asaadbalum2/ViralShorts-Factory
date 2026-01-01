@echo off
echo ============================================================
echo Restoring Chat: Recurring stuck issue
echo ============================================================
echo.
cd /d "%~dp0"
python complete_chat_rebuild.py
echo.
echo ============================================================
echo Done! Please restart Cursor now.
echo ============================================================
pause






