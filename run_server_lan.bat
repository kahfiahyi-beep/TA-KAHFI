@echo off
title [LAN SERVER] Akses Lokal & Satu Jaringan Wi-Fi
echo ======================================================================
echo    AKSES WEBSITE DALAM SATU JARINGAN WI-FI (OFFLINE / LAN)
echo ======================================================================
echo.
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found_ip
)
:found_ip
set IP=%IP: =%
echo Laptop Anda bertindak sebagai Server.
echo.
echo Perangkat lain (HP/Laptop) yang terhubung ke Wi-Fi yang sama dapat
echo membuka alamat berikut di browser:
echo.
echo    ---> http://%IP%:8501
echo.
echo ======================================================================
echo.

"C:\Users\anif_\AppData\Local\Programs\Python\Python311\python.exe" -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0

pause
