# Sistem Analisis Karakteristik Visual Postingan UMKM Berbasis Computer Vision (Tugas Akhir)

Aplikasi web cerdas untuk penelitian Tugas Akhir (TA) berjudul:
**"Analisis Hubungan Karakteristik Visual Produk dengan Engagement pada Sosial Media UMKM dalam Perspektif Ekonomi Islam dan Perlindungan Konsumen Digital"**

---

## 📌 Indikator Penelitian yang Diidentifikasi (K1 – K8)

1. **K1 (Nama Produk):** Kejelasan nama/merek komoditas pada visual atau caption (kejelasan objek transaksi / *ma'qud 'alaih*).
2. **K2 (Harga):** Keterbukaan harga nominal rupiah vs disembunyikan (*DM for price*). Ini merupakan variabel sentral dalam fiqh muamalah untuk mencegah **Gharar** (ketidakpastian).
3. **K3 (Diskon/Promo):** Identifikasi elemen potongan harga, diskon persentase, voucher, atau *Buy 1 Get 1*.
4. **K4 (Periode Promo):** Pencantuman batas waktu berlakunya promo untuk mencegah manipulasi psikologis konsumen.
5. **K5 (Syarat Promo / S&K):** Keterbukaan syarat & ketentuan promo (klausula baku yang transparan sesuai Pasal 18 UU Perlindungan Konsumen).
6. **K6 (Info Produk):** Spesifikasi bahan, netto/ukuran, rasa, legalitas izin edar BPOM dan sertifikasi Halal.
7. **K7 (Klaim Kualitas):** Identifikasi klaim superlatif ("terbaik", "terlaris", "ampuh", dsb.) untuk dievaluasi dari prinsip kejujuran (*Shiddiq*) dan larangan *Tadlis* (penipuan).
8. **K8 (Visual–Caption Alignment):** Keselarasan antara gambar visual produk dengan narasi caption (tidak *clickbait*).

---

## 🚀 Fitur Unggulan Sistem

- **Dual-Engine Computer Vision & AI**:
  - *Local OpenCV Engine:* Ekstraksi kecerahan (*brightness*), kontras RMS, kepadatan elemen teks/garis (*edge density*), deteksi wajah/manusia, dan palet warna dominan (100% offline).
  - *Google Gemini Vision AI (Cloud):* Penalaran multimodal mutakhir untuk verifikasi semantik K1–K8 dengan tingkat akurasi tinggi.
- **Perhitungan Engagement Rate (ER) Otomatis**:
  $$\text{Engagement Rate} = \frac{\text{Likes} + \text{Comments} + \text{Shares} + \text{Saves}}{\text{Followers}} \times 100\%$$
- **Analisis Statistik & Ekonometrika (Bab 4 Skripsi)**:
  - Statistik Deskriptif (Mean, Median, Min, Max, Standar Deviasi).
  - Matriks Korelasi Bivariat (Pearson & Spearman) lengkap dengan signifikansi *p-value*.
  - Uji Beda Rata-rata (*Independent Sample t-Test*) untuk membandingkan postingan dengan vs tanpa harga.
  - Estimasi Model Regresi Linier Berganda (*Ordinary Least Squares / OLS*).
- **Tinjauan Kritis Fiqh Muamalah & UUPK**:
  - Kerangka teoritis komparatif Fiqh Muamalah (Gharar, Tadlis, Ghasysy, Shiddiq, Amanah).
  - Tinjauan UU Perlindungan Konsumen No. 8 Tahun 1999 (Pasal 4, 7, 9, 10, 18) dan PP PMSE.
- **Ekspor Siap Olah untuk Software Gretl & SPSS**:
  - Unduh format Excel (`.xlsx`) dan CSV (`.csv`) dengan pengkodean numerik biner (0 dan 1) yang siap di-import langsung ke **Gretl** atau **SPSS**.

---

## 💻 Cara Menjalankan Aplikasi

Aplikasi saat ini telah aktif di:
👉 **[http://localhost:8501](http://localhost:8501)**

Untuk menjalankannya kembali di kemudian hari, cukup **klik ganda (double-click)** pada file:
```
run_app.bat
```
Atau melalui terminal PowerShell:
```powershell
python -m streamlit run app.py
```
