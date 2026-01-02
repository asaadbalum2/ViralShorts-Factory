@echo off
echo ===============================================
echo ViralShorts Factory - Directory Rename Script
echo ===============================================
echo.
echo This script will rename YShortsGen to ViralShorts-Factory
echo.
echo CLOSE CURSOR IDE FIRST before running this!
echo.
pause

cd C:\Users\SoulsTaker7
ren YShortsGen ViralShorts-Factory

if exist "ViralShorts-Factory" (
    echo.
    echo SUCCESS! Directory renamed to ViralShorts-Factory
    echo.
    echo Now open Cursor and:
    echo   File > Open Folder > C:\Users\SoulsTaker7\ViralShorts-Factory
    echo.
) else (
    echo.
    echo FAILED - Make sure Cursor is closed and try again
)

pause


