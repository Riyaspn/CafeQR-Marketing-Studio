@echo off
title Cafe QR 2.0 - Viral Marketing & Content Studio
cd /d "%~dp0"
echo ========================================================
echo  CAFE QR 2.0 - VIRAL MARKETING & CONTENT STUDIO
echo ========================================================
echo.
echo Starting Marketing Studio on http://localhost:8899...
start "" http://localhost:8899
python studio_server.py
pause
