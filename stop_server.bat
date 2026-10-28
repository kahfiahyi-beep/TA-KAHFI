@echo off
title Hentikan Server Hosting
echo ======================================================================
echo   Menghentikan Server Streamlit dan Cloudflare Tunnel...
echo ======================================================================
taskkill /f /im cloudflared.exe >nul 2>&1
taskkill /f /im python.exe /fi "WINDOWTITLE eq Streamlit*" >nul 2>&1
echo.
echo Server berhasil dihentikan dengan aman.
timeout /t 3 >nul
