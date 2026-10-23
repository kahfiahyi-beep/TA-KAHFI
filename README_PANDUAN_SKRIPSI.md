# PANDUAN LENGKAP SISTEM SCRAPING & KURASI DATASET INSTAGRAM UMKM (SKRIPSI)

**Judul Penelitian:**  
*"Analisis Hubungan Karakteristik Visual Produk dengan Engagement pada Media Sosial UMKM dalam Perspektif Ekonomi Islam dan Perlindungan Konsumen Digital"*

Panduan ini disusun secara khusus dalam **Bahasa Indonesia yang sederhana dan langkah demi langkah** untuk pengguna laptop Windows yang masih pemula dalam pemrograman Python.

---

## 📁 1. Struktur File dan Lokasi Penyimpanan

Seluruh file sistem ini disimpan di dalam folder workspace Anda:  
📍 **`C:\Users\anif_\Downloads\vision\`**

Berikut adalah daftar file utama beserta fungsinya:

| Nama File / Folder | Fungsi & Penjelasan |
| :--- | :--- |
| **`run_scraping.bat`** | **Shortcut Eksekusi Windows:** Cukup klik ganda (*double-click*) file ini untuk langsung membuka aplikasi antarmuka web di browser Anda tanpa perlu mengetik perintah terminal. |
| **`curation_app.py`** | **Aplikasi Antarmuka Web (Streamlit):** Program visual untuk pengumpulan data, dashboard progres 3.000 data, kurasi manual foto produk, evaluasi inklusi/eksklusi, dan ekspor file. |
| **`config.json`** | **File Konfigurasi:** Mengatur rentang tanggal periode penelitian (**2026-01-01 s/d 2026-06-30**), target kuota (3.000 sampel valid), dan jeda waktu (*rate limit*). |
| **`scraper_engine.py`** | **Mesin Pengumpul Metadata:** Mengambil data postingan publik (shortcode, caption, tanggal publikasi, likes, komentar, jenis media) dan mengunduh gambar resolusi tinggi ke folder lokal. |
| **`sampling_filter.py`** | **Modul Penyaringan Otomatis:** Memeriksa kesesuaian kriteria inklusi (I1–I7) dan mendeteksi kriteria eksklusi (E1–E9) secara ter-audit. |
| **`database_manager.py`** | **Pengelola Database (SQLite):** Menyimpan metadata ke file database `dataset_skripsi.db`, mencegah duplikasi link/shortcode, dan mencatat riwayat verifikasi peneliti. |
| **`export_manager.py`** | **Modul Ekspor Excel & CSV:** Menghasilkan 4 file dataset utama dan 1 file laporan ringkasan seleksi dengan tata letak visual profesional. |
| **`input_akun_umkm.xlsx`** & **`.csv`** | **Template Input Akun:** Contoh daftar akun UMKM untuk diproses (kolom: `username`, `url_profil`, `kategori_produk`, `catatan`). |
| **`input_link_postingan.xlsx`** & **`.csv`** | **Template Input Link Postingan:** Contoh daftar tautan postingan Instagram publik untuk ditarik metadatanya sekaligus (*batch*). |
| **`dataset_images/`** | **Folder Foto Produk:** Tempat penyimpanan otomatis gambar postingan resolusi tinggi (`.jpg`) untuk pemeriksaan visual peneliti. |
| **`hasil_ekspor/`** | **Folder Output Dataset:** Tempat berkas Excel (`.xlsx`) dan CSV (`.csv`) disimpan setelah Anda menekan tombol ekspor. |
| **`dataset_skripsi.db`** | **Database Penyimpanan:** Berkas database lokal tempat seluruh data tersimpan secara aman dan permanen. |
| **`test_workflow.py`** | **Skrip Uji Otomatis:** Skrip pengujian alur kerja sistem (scraping, filter, verifikasi, dan ekspor). |

---

## 🔍 2. Evaluasi Ilmiah & Keterbatasan Scraping Instagram Tanpa Graph API

Sebelum menjalankan pengumpulan data, peneliti **wajib memahami batasan teknis dan etika ilmiah** berikut:

### A. Metode Penarikan Data yang Realistis
1. **Metode Input Link / Shortcode Postingan (Sangat Direkomendasikan):**  
   - Mengambil data melalui URL publik postingan (`https://www.instagram.com/p/SHORTCODE/`).  
   - **Kelebihan:** Sangat stabil, tidak memerlukan login akun Instagram, mengunduh gambar beresolusi penuh, dan tidak diblokir jika diberi jeda wajar (3–7 detik).
2. **Metode Scraping Profil Akun Publik Tanpa Login:**  
   - Instagram menerapkan pembatasan ketat (*HTTP 401 Unauthorized / Please wait a few minutes*) pada akses daftar feed akun publik tanpa sesi login resmi.  
   - **Solusi Praktis Bagi Peneliti:** Buka akun UMKM di browser laptop Anda, salin (*copy link*) beberapa tautan postingan produknya, lalu tempelkan ke menu **"Input Link Postingan"** di aplikasi. Cara ini 100% berhasil dan aman dari pemblokiran.

### B. Transparansi & Kejujuran Data Engagement
- **Jumlah Likes & Komentar:** **DAPAT DIPEROLEH** secara sah jika postingan bersifat publik dan pemilik tidak menyembunyikan angka suka (*hide like count*).
- **Jumlah Share & Save:** **TIDAK DAPAT DIAKSES SECARA PUBLIK**.  
  Instagram tidak pernah menampilkan angka share dan save ke publik. Data tersebut adalah metrik rahasia (*private insights*) yang hanya bisa dilihat oleh pemilik akun melalui dashboard *Instagram Creator*.  
  > ⚠️ **Prinsip Kejujuran Akademik:** Dalam dataset skripsi ini, kolom `jumlah_share` **sengaja dibiarkan kosong (NULL/kosong)** dan diberi keterangan status *"Tidak tersedia secara publik"*. Program **tidak mengarang angka nol** agar dataset Anda valid dan dapat dipertanggungjawabkan di hadapan dosen penguji.

---

## 🎯 3. Protokol Kriteria Inklusi & Eksklusi Penelitian

Sistem menerapkan kriteria seleksi ketat sesuai metodologi skripsi Anda:

### Kriteria Inklusi (I1 – I7)
1. **I1 (Akun UMKM Terpilih):** Berasal dari akun Instagram UMKM yang telah disetujui sebagai objek penelitian.
2. **I2 (Format Foto Statis):** Berupa gambar statis (single image atau carousel feed), bukan video atau reels.
3. **I3 (Menampilkan Produk):** Konten visual secara nyata menampilkan produk barang/jasa komoditas UMKM.
4. **I4 (Fungsi Promosi/Pemasaran):** Memiliki narasi atau tujuan penawaran komersial produk.
5. **I5 (Periode Penelitian):** Dipublikasikan antara **Januari 2026 s/d Juni 2026**.
6. **I6 (Karakteristik Visual Teramati):** File gambar berhasil diunduh dan kualitasnya memadai untuk dianalisis.
7. **I7 (Data Engagement Tersedia):** Memiliki angka likes dan komentar yang dapat diverifikasi.

### Kriteria Eksklusi (E1 – E9)
1. **E1:** Format video / Reels / TikTok video.
2. **E2:** Ucapan hari besar nasional/keagamaan yang tidak menampilkan produk dagang.
3. **E3:** Kutipan kata-kata mutiara / quotes motivasi tanpa menampilkan produk.
4. **E4:** Pengumuman internal operasional toko (loker, tutup libur, dsb.) tanpa produk.
5. **E5:** Repost testimoni pelanggan murni (*User Generated Content*).
6. **E6:** Hanya menampilkan foto pemilik (*owner*) tanpa produk dagangan.
7. **E7:** Konten giveaway tanpa produk relevan.
8. **E8:** File gambar rusak, kadaluarsa, atau postingan telah dihapus.
9. **E9:** Data engagement disembunyikan total atau dinonaktifkan oleh pemilik akun.

> 💡 **Penting:** Sistem otomatis menandai postingan yang lolos kriteria teknis awal sebagai **"Perlu Verifikasi Manual"** karena keberadaan fisik produk (I3) dan fungsi promosi komersial (I4) harus diverifikasi langsung oleh mata peneliti.

---

## 🚀 4. Cara Menjalankan Program di Windows (Langkah demi Langkah)

### Metode 1: Menggunakan File Batch (Paling Praktis)
1. Buka folder: `C:\Users\anif_\Downloads\vision\` di File Explorer Windows Anda.
2. Cari file bernama **`run_scraping.bat`**.
3. **Klik ganda (*double-click*)** pada file `run_scraping.bat`.
4. Jendela terminal hitam akan muncul dan otomatis menjalankan server Streamlit.
5. Dalam beberapa detik, browser Anda (Google Chrome / Microsoft Edge) akan otomatis terbuka dan menampilkan halaman aplikasi di:  
   👉 **`http://localhost:8501`**

### Metode 2: Melalui Terminal PowerShell
Jika Anda ingin menjalankannya lewat PowerShell:
1. Buka PowerShell di laptop Anda.
2. Jalankan perintah berikut:
   ```powershell
   python -m streamlit run curation_app.py
   ```
3. Tekan Enter.

---

## 🖥️ 5. Panduan Penggunaan Antarmuka Aplikasi (Tab demi Tab)

### Tab 1: 📥 Pengumpulan Metadata (Scraper)
- **Opsi A (Uji Coba Cepat 1 Link):** Masukkan 1 link postingan Instagram (misal: `https://www.instagram.com/p/DZ9xP_AyYAM/`) dan klik **🚀 Tarik Metadata**. Gambar akan langsung diunduh dan metadata tersimpan ke database.
- **Opsi B (Input Banyak Link Postingan):**  
  - Unggah file Excel/CSV berisi daftar link postingan Anda, ATAU
  - Tempel (*paste*) daftar link postingan pada kotak teks yang tersedia (satu link per baris).
  - Tentukan jeda waktu aman (misal 3–5 detik).
  - Klik **🚀 Mulai Penarikan Data Massal**. Sistem akan memproses satu per satu postingan secara otomatis tanpa risiko pemblokiran.

### Tab 2: 🔍 Verifikasi Manual & Kurasi Visual
- Anda dapat memilih postingan dari daftar dropdown.
- **Di sisi kiri:** Anda dapat melihat foto produk resolusi tinggi, username UMKM, tanggal publikasi, likes, komentar, dan teks caption lengkap. Terdapat juga link langsung untuk membuka postingan asli di Instagram.
- **Di sisi kanan (Formulir Peneliti):**
  1. Pilih apakah gambar menampilkan produk (`Ya` / `Tidak`).
  2. Ketik nama/keterangan produk yang terlihat (misal: *"Baso Aci Paket Komplit"*).
  3. Konfirmasi apakah postingan berfungsi promosi komersial (`Ya` / `Tidak`).
  4. Tentukan keputusan akhir: **`Lolos Inklusi`** atau **`Gugur Eksklusi`**.
  5. Jika memilih *Gugur Eksklusi*, pilih kode alasan eksklusinya (E1 sampai E9).
  6. Tambahkan catatan kualitatif pemeriksa.
  7. Klik tombol **💾 Simpan Hasil Verifikasi**. Data akan langsung terbarui di database!

### Tab 3: 🎨 Variabel Visual (Persiapan Analisis Bab 4)
- Sesuai rancangan skripsi Anda, tab ini digunakan untuk menilai variabel visual postingan yang telah berstatus *Lolos Inklusi*:
  - Warna dominan produk/gambar.
  - Nilai kecerahan (*brightness*) dan kontras.
  - Komposisi visual (*Rule of Thirds, Center, Flat Lay, Close-Up*).
  - Jumlah produk yang terlihat dalam gambar.
  - Keberadaan model/manusia.
  - Kejelasan tampilan produk.
  - Keberadaan teks promosi pada gambar.
  - Pencantuman harga nominal (Keterbukaan harga vs *DM for price* — variabel penting dalam tinjauan Fiqh Muamalah untuk pencegahan *Gharar*).
  - Kualitas gambar (HD / Sedang / Buram).

### Tab 4: 💾 Ekspor Dataset (Excel & CSV)
- Klik tombol **🔄 Generate & Perbarui Seluruh File Ekspor Sekarang**.
- Sistem akan otomatis menghasilkan 5 berkas di folder `hasil_ekspor/`:
  1. **`dataset_mentah.xlsx`**: Seluruh data yang berhasil dikumpulkan sebelum seleksi.
  2. **`dataset_layak.xlsx`**: Postingan yang telah lolos kriteria inklusi dan verifikasi manual (siap digunakan untuk analisis skripsi).
  3. **`dataset_eksklusi.xlsx`**: Seluruh postingan yang ditolak beserta rincian alasannya (sebagai bukti audit seleksi purposive sampling).
  4. **`dataset_layak.csv`**: Salinan dataset final dalam format CSV standar (UTF-8 BOM sehingga karakter tidak berantakan saat dibuka di Excel).
  5. **`laporan_ringkasan_seleksi.xlsx`**: Tabel rekapitulasi jumlah data pada setiap tahapan seleksi beserta persentasenya.
- Tersedia tombol unduh (*download button*) langsung di halaman web untuk mengunduh setiap file dengan 1 klik.

---

## 📈 6. Strategi Mencapai Target 3.000 Postingan Secara Bertahap

Target 3.000 postingan adalah jumlah yang signifikan dalam penelitian media sosial. Agar proses pengumpulan data berjalan lancar, aman dari pembatasan akses, dan tidak melelahkan:

1. **Pengumpulan Bertahap per Hari:**  
   - Kumpulkan sekitar **150 – 250 link postingan per sesi/hari** dari beberapa akun UMKM yang menjadi objek penelitian.
   - Dengan rata-rata 10–20 postingan per akun UMKM, Anda memerlukan sekitar **150 – 200 akun UMKM** dalam periode Januari – Juni 2026.
2. **Database Aman & Anti-Duplikasi:**  
   - Program menggunakan database SQLite lokal (`dataset_skripsi.db`). Jika laptop Anda dimatikan atau aplikasi ditutup, data yang telah terkumpul **tidak akan hilang**.
   - Jika Anda tidak sengaja memasukkan link yang sama dua kali, program akan secara cerdas mengenali shortcode tersebut dan **tidak membuat data ganda** (*anti-duplicate*).
3. **Pemantauan Melalui Sidebar:**  
   - Perhatikan indikator progres pada sidebar kiri aplikasi yang selalu menampilkan jumlah data lolos inklusi aktual dan sisa kebutuhan menuju 3.000 postingan.

---

## ⚙️ 7. Cara Mengubah Periode Tanggal Penelitian

Jika di kemudian hari dosen pembimbing Anda meminta penyesuaian rentang waktu observasi:
1. Buka file **`config.json`** menggunakan Notepad.
2. Ubah nilai pada bagian `"tanggal_mulai"` atau `"tanggal_selesai"`.  
   Contoh format:
   ```json
   "periode_penelitian": {
     "tanggal_mulai": "2026-01-01",
     "tanggal_selesai": "2026-06-30"
   }
   ```
3. Simpan (*Save*) file `config.json`. Sistem penyaringan otomatis akan langsung menyesuaikan aturan tanggal tanpa perlu mengubah kode program.

---

## 🧪 8. Menjalankan Uji Coba Sistem Mandiri

Untuk memastikan seluruh modul program (koneksi, penarikan, filter, database, dan ekspor) berfungsi normal di laptop Anda kapan pun dibutuhkan:
1. Buka PowerShell di folder `C:\Users\anif_\Downloads\vision\`.
2. Jalankan perintah:
   ```powershell
   python test_workflow.py
   ```
3. Program pengujian akan menjalankan 7 tahapan uji otomatis dan memberikan laporan kelulusan 100%.
