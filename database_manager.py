"""
database_manager.py
===================
Modul pengelolaan database SQLite untuk penyimpanan metadata postingan Instagram,
pelacakan kriteria inklusi/eksklusi, log verifikasi manual, dan ekspor dataset.
"""

import sqlite3
import os
import json
from datetime import datetime
import pandas as pd

DB_FILE = os.path.join(os.path.dirname(__file__), "dataset_skripsi.db")

def get_connection(db_path=None):
    """Membuka koneksi ke database SQLite."""
    path = db_path or DB_FILE
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=None):
    """Inisialisasi tabel database skripsi dengan seluruh kolom yang dipersyaratkan."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dataset_posts (
        -- 1. IDENTITAS POSTINGAN
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_dataset TEXT UNIQUE,
        username_ig TEXT NOT NULL,
        nama_umkm TEXT,
        kategori_produk TEXT,
        link_profil TEXT,
        link_postingan TEXT NOT NULL UNIQUE,
        shortcode TEXT NOT NULL UNIQUE,
        tanggal_publikasi TEXT,
        caption TEXT,
        jenis_media TEXT DEFAULT 'Foto',
        tanggal_pengambilan_data TEXT,

        -- 2. INFORMASI VISUAL & PROMOSI
        lokasi_file_gambar TEXT,
        link_gambar TEXT,
        status_ketersediaan_gambar TEXT DEFAULT 'Tersedia',
        menampilkan_produk TEXT DEFAULT 'Perlu Verifikasi Manual',
        keterangan_produk TEXT,
        fungsi_promosi TEXT DEFAULT 'Perlu Verifikasi Manual',
        konten_asli_atau_repost TEXT DEFAULT 'Belum Terverifikasi',
        kelayakan_analisis_visual TEXT DEFAULT 'Perlu Verifikasi Manual',
        status_verifikasi_manual TEXT DEFAULT 'Belum Diperiksa',

        -- 3. DATA ENGAGEMENT
        jumlah_likes INTEGER,
        status_likes TEXT DEFAULT 'Tersedia',
        jumlah_komentar INTEGER,
        status_komentar TEXT DEFAULT 'Tersedia',
        jumlah_share INTEGER,
        status_share TEXT DEFAULT 'Tidak tersedia secara publik',
        waktu_pengambilan_engagement TEXT,
        metode_pengambilan_metrik TEXT DEFAULT 'Instaloader Public Inspection',

        -- 4. HASIL SELEKSI (PURPOSIVE SAMPLING)
        status_inklusi TEXT DEFAULT 'Perlu Verifikasi Manual',
        alasan_eksklusi TEXT,
        kriteria_belum_pasti TEXT DEFAULT 'I3 (Visual Produk), I4 (Fungsi Promosi)',
        catatan_pemeriksa TEXT,
        waktu_verifikasi TEXT,
        status_pemeriksaan_akhir TEXT DEFAULT 'Draft',

        -- 5. VARIABEL KARAKTERISTIK VISUAL (UNTUK ANALISIS LANJUTAN BAB 4)
        warna_dominan TEXT,
        kecerahan_brightness REAL,
        kontras_visual REAL,
        komposisi_visual TEXT,
        jumlah_produk_terlihat INTEGER,
        keberadaan_manusia TEXT,
        kejelasan_tampilan_produk TEXT,
        teks_promosi_pada_gambar TEXT,
        keberadaan_harga_info TEXT,
        kualitas_gambar TEXT,

        -- METADATA INTERNAL & LOG
        created_at TEXT,
        updated_at TEXT
    );
    """)

    # Tabel pelacakan akun UMKM
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS akun_umkm (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        url_profil TEXT,
        kategori_produk TEXT,
        catatan TEXT,
        status_proses TEXT DEFAULT 'Belum Diproses',
        total_post_ditemukan INTEGER DEFAULT 0,
        terakhir_diproses TEXT
    );
    """)

    conn.commit()
    conn.close()

def save_or_update_post(post_dict, db_path=None):
    """
    Menyimpan atau memperbarui data postingan.
    Mencegah duplikasi shortcode atau URL postingan.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    shortcode = post_dict.get("shortcode")
    link_postingan = post_dict.get("link_postingan")

    # Cek apakah sudah ada
    cursor.execute("SELECT id, id_dataset FROM dataset_posts WHERE shortcode = ? OR link_postingan = ?", (shortcode, link_postingan))
    existing = cursor.fetchone()

    if existing:
        post_id = existing["id"]
        id_dataset = existing["id_dataset"]
        # Update existing
        cursor.execute("""
        UPDATE dataset_posts SET
            caption = COALESCE(?, caption),
            tanggal_publikasi = COALESCE(?, tanggal_publikasi),
            jumlah_likes = ?,
            status_likes = ?,
            jumlah_komentar = ?,
            status_komentar = ?,
            lokasi_file_gambar = COALESCE(?, lokasi_file_gambar),
            link_gambar = COALESCE(?, link_gambar),
            status_ketersediaan_gambar = ?,
            jenis_media = COALESCE(?, jenis_media),
            status_inklusi = COALESCE(?, status_inklusi),
            alasan_eksklusi = COALESCE(?, alasan_eksklusi),
            kriteria_belum_pasti = COALESCE(?, kriteria_belum_pasti),
            updated_at = ?
        WHERE id = ?
        """, (
            post_dict.get("caption"),
            post_dict.get("tanggal_publikasi"),
            post_dict.get("jumlah_likes"),
            post_dict.get("status_likes", "Tersedia"),
            post_dict.get("jumlah_komentar"),
            post_dict.get("status_komentar", "Tersedia"),
            post_dict.get("lokasi_file_gambar"),
            post_dict.get("link_gambar"),
            post_dict.get("status_ketersediaan_gambar", "Tersedia"),
            post_dict.get("jenis_media", "Foto"),
            post_dict.get("status_inklusi"),
            post_dict.get("alasan_eksklusi"),
            post_dict.get("kriteria_belum_pasti"),
            now_str,
            post_id
        ))
        conn.commit()
        conn.close()
        return post_id, "updated", id_dataset
    else:
        # Generate new ID dataset
        cursor.execute("SELECT COUNT(*) as cnt FROM dataset_posts")
        count = cursor.fetchone()["cnt"] + 1
        id_dataset = f"DS-UMKM-{count:04d}"

        cursor.execute("""
        INSERT INTO dataset_posts (
            id_dataset, username_ig, nama_umkm, kategori_produk, link_profil,
            link_postingan, shortcode, tanggal_publikasi, caption, jenis_media,
            tanggal_pengambilan_data, lokasi_file_gambar, link_gambar,
            status_ketersediaan_gambar, menampilkan_produk, keterangan_produk,
            fungsi_promosi, konten_asli_atau_repost, kelayakan_analisis_visual,
            status_verifikasi_manual, jumlah_likes, status_likes, jumlah_komentar,
            status_komentar, jumlah_share, status_share, waktu_pengambilan_engagement,
            metode_pengambilan_metrik, status_inklusi, alasan_eksklusi,
            kriteria_belum_pasti, catatan_pemeriksa, status_pemeriksaan_akhir,
            created_at, updated_at
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?
        )
        """, (
            id_dataset,
            post_dict.get("username_ig", ""),
            post_dict.get("nama_umkm", ""),
            post_dict.get("kategori_produk", ""),
            post_dict.get("link_profil", f"https://www.instagram.com/{post_dict.get('username_ig', '')}/"),
            link_postingan,
            shortcode,
            post_dict.get("tanggal_publikasi", ""),
            post_dict.get("caption", ""),
            post_dict.get("jenis_media", "Foto"),
            post_dict.get("tanggal_pengambilan_data", now_str),
            post_dict.get("lokasi_file_gambar", ""),
            post_dict.get("link_gambar", ""),
            post_dict.get("status_ketersediaan_gambar", "Tersedia"),
            post_dict.get("menampilkan_produk", "Perlu Verifikasi Manual"),
            post_dict.get("keterangan_produk", ""),
            post_dict.get("fungsi_promosi", "Perlu Verifikasi Manual"),
            post_dict.get("konten_asli_atau_repost", "Belum Terverifikasi"),
            post_dict.get("kelayakan_analisis_visual", "Perlu Verifikasi Manual"),
            post_dict.get("status_verifikasi_manual", "Belum Diperiksa"),
            post_dict.get("jumlah_likes"),
            post_dict.get("status_likes", "Tersedia"),
            post_dict.get("jumlah_komentar"),
            post_dict.get("status_komentar", "Tersedia"),
            None, # jumlah_share wajib kosong (tidak ada di publik IG)
            "Tidak tersedia secara publik",
            post_dict.get("waktu_pengambilan_engagement", now_str),
            post_dict.get("metode_pengambilan_metrik", "Instaloader Public Inspection"),
            post_dict.get("status_inklusi", "Perlu Verifikasi Manual"),
            post_dict.get("alasan_eksklusi", ""),
            post_dict.get("kriteria_belum_pasti", "I3 (Visual Produk), I4 (Fungsi Promosi)"),
            post_dict.get("catatan_pemeriksa", ""),
            "Draft",
            now_str,
            now_str
        ))
        conn.commit()
        inserted_id = cursor.lastrowid
        conn.close()
        return inserted_id, "inserted", id_dataset

def get_post_statistics(db_path=None):
    """
    Menghitung metrik progres pengumpulan data terhadap target 3.000 postingan.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(DISTINCT username) FROM akun_umkm WHERE status_proses = 'Selesai'")
    total_akun_selesai = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM akun_umkm")
    total_akun = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dataset_posts")
    total_postingan = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT link_postingan) FROM dataset_posts")
    total_url_unik = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dataset_posts WHERE jenis_media IN ('Foto', 'Carousel/Foto')")
    total_foto = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dataset_posts WHERE status_inklusi = 'Lolos Inklusi'")
    total_layak = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dataset_posts WHERE status_inklusi = 'Gugur Eksklusi'")
    total_eksklusi = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dataset_posts WHERE status_inklusi = 'Perlu Verifikasi Manual'")
    total_menunggu_verifikasi = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dataset_posts WHERE status_ketersediaan_gambar = 'Tidak Tersedia'")
    total_gagal_gambar = cursor.fetchone()[0]

    target = 3000
    sisa_kebutuhan = max(0, target - total_layak)

    conn.close()
    return {
        "target": target,
        "total_akun": total_akun,
        "total_akun_selesai": total_akun_selesai,
        "total_postingan": total_postingan,
        "total_url_unik": total_url_unik,
        "total_foto": total_foto,
        "total_layak": total_layak,
        "total_eksklusi": total_eksklusi,
        "total_menunggu_verifikasi": total_menunggu_verifikasi,
        "total_gagal_gambar": total_gagal_gambar,
        "sisa_kebutuhan": sisa_kebutuhan,
        "persentase_tercapai": round((total_layak / target) * 100, 2)
    }

def update_manual_verification(post_id, updates, db_path=None):
    """Memperbarui hasil verifikasi manual oleh peneliti."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    UPDATE dataset_posts SET
        status_inklusi = ?,
        alasan_eksklusi = ?,
        menampilkan_produk = ?,
        keterangan_produk = ?,
        fungsi_promosi = ?,
        konten_asli_atau_repost = ?,
        kelayakan_analisis_visual = ?,
        status_verifikasi_manual = 'Sudah Diperiksa',
        kriteria_belum_pasti = ?,
        catatan_pemeriksa = ?,
        status_pemeriksaan_akhir = ?,
        waktu_verifikasi = ?,
        updated_at = ?
    WHERE id = ?
    """, (
        updates.get("status_inklusi"),
        updates.get("alasan_eksklusi", ""),
        updates.get("menampilkan_produk", "Ya"),
        updates.get("keterangan_produk", ""),
        updates.get("fungsi_promosi", "Ya"),
        updates.get("konten_asli_atau_repost", "Konten Asli"),
        updates.get("kelayakan_analisis_visual", "Layak"),
        updates.get("kriteria_belum_pasti", ""),
        updates.get("catatan_pemeriksa", ""),
        updates.get("status_pemeriksaan_akhir", "Final"),
        now_str,
        now_str,
        post_id
    ))
    conn.commit()
    conn.close()

def update_visual_features(post_id, visual_dict, db_path=None):
    """Menyimpan fitur karakteristik visual untuk persiapan analisis Bab 4 skripsi."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    UPDATE dataset_posts SET
        warna_dominan = ?,
        kecerahan_brightness = ?,
        kontras_visual = ?,
        komposisi_visual = ?,
        jumlah_produk_terlihat = ?,
        keberadaan_manusia = ?,
        kejelasan_tampilan_produk = ?,
        teks_promosi_pada_gambar = ?,
        keberadaan_harga_info = ?,
        kualitas_gambar = ?,
        updated_at = ?
    WHERE id = ?
    """, (
        visual_dict.get("warna_dominan"),
        visual_dict.get("kecerahan_brightness"),
        visual_dict.get("kontras_visual"),
        visual_dict.get("komposisi_visual"),
        visual_dict.get("jumlah_produk_terlihat"),
        visual_dict.get("keberadaan_manusia"),
        visual_dict.get("kejelasan_tampilan_produk"),
        visual_dict.get("teks_promosi_pada_gambar"),
        visual_dict.get("keberadaan_harga_info"),
        visual_dict.get("kualitas_gambar"),
        now_str,
        post_id
    ))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    stats = get_post_statistics()
    print("Database terinisialisasi dengan sukses.")
    print("Statistik awal:", stats)
