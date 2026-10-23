@echo off
title Sistem Scraping & Kurasi Dataset 3.000 Postingan UMKM (Skripsi)
echo ======================================================================
echo   SISTEM SCRAPING & KURASI DATASET INSTAGRAM UMKM (SKRIPSI)
echo   Target: 3.000 Postingan Valid (Januari - Juni 2026)
echo ======================================================================
echo.
echo Sedang menyiapkan server aplikasi Streamlit...
echo Halaman kurasi akan otomatis terbuka di browser Anda.
echo.

python -m streamlit run curation_app.py

pause
