@echo off
title [ONLINE SERVER] Sistem Analisis Karakteristik Visual UMKM
color 0b
echo ======================================================================
echo    HOSTING WEBSITE DARI LAPTOP (ONLINE KE SELURUH INTERNET)
echo    Sistem Analisis Karakteristik Visual UMKM vs Engagement
echo ======================================================================
echo.
echo [1/3] Menyiapkan server Streamlit lokal...
start "Streamlit Server Background" /min "C:\Users\anif_\AppData\Local\Programs\Python\Python311\python.exe" -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false

echo [2/3] Menunggu server siap...
timeout /t 4 /nobreak >nul

echo [3/3] Menghubungkan ke Cloudflare Tunnel (HTTPS Publik Aman)...
echo.
echo ======================================================================
echo   PETUNJUK:
echo   1. Tunggu 5-10 detik sampai muncul kotak bergaris berisi link:
echo      https://[nama-acak].trycloudflare.com
echo   2. Blok dan Copy link tersebut, lalu bagikan ke Dosen / Penguji / Teman.
echo   3. JANGAN TUTUP jendela ini selama web ingin tetap bisa diakses!
echo ======================================================================
echo.

"%~dp0cloudflared.exe" tunnel --url http://localhost:8501

pause
