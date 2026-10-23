import sqlite3
import json
import os
from datetime import datetime
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "ta_umkm_vision.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_title TEXT,
        umkm_name TEXT,
        platform TEXT DEFAULT 'Instagram',
        post_date TEXT,
        image_path TEXT,
        caption TEXT,
        
        -- Engagement Metrics
        followers INTEGER DEFAULT 0,
        likes INTEGER DEFAULT 0,
        comments INTEGER DEFAULT 0,
        total_visible_engagement INTEGER DEFAULT 0,
        shares INTEGER DEFAULT 0,
        saves INTEGER DEFAULT 0,
        product_rating REAL DEFAULT 0.0,
        engagement_rate REAL DEFAULT 0.0,
        
        -- Indikator Karakteristik Visual K1 - K8 (0 = Tidak ada, 1 = Ada)
        k1_nama_produk INTEGER DEFAULT 0,
        k1_detail TEXT,
        k2_harga INTEGER DEFAULT 0,
        k2_detail TEXT,
        k3_diskon INTEGER DEFAULT 0,
        k3_detail TEXT,
        k4_periode_promo INTEGER DEFAULT 0,
        k4_detail TEXT,
        k5_syarat_promo INTEGER DEFAULT 0,
        k5_detail TEXT,
        k6_info_produk INTEGER DEFAULT 0,
        k6_detail TEXT,
        k7_klaim INTEGER DEFAULT 0,
        k7_detail TEXT,
        k8_visual_caption INTEGER DEFAULT 0,
        k8_detail TEXT,

        -- 8 Fitur Computer Vision F1 - F8
        f1_object_detection INTEGER DEFAULT 1,
        f1_detail TEXT,
        f2_color_extraction INTEGER DEFAULT 1,
        f2_detail TEXT,
        f3_posisi_objek INTEGER DEFAULT 1,
        f3_detail TEXT,
        f4_dominasi_objek INTEGER DEFAULT 1,
        f4_detail TEXT,
        f5_background INTEGER DEFAULT 1,
        f5_detail TEXT,
        f6_objek_tambahan INTEGER DEFAULT 0,
        f6_detail TEXT,
        f7_manusia INTEGER DEFAULT 0,
        f7_detail TEXT,
        f8_teks INTEGER DEFAULT 0,
        f8_detail TEXT,
        
        -- Fitur Computer Vision Tambahan
        cv_brightness REAL DEFAULT 0.0,
        cv_contrast REAL DEFAULT 0.0,
        cv_text_density REAL DEFAULT 0.0,
        cv_dominant_color TEXT,
        cv_face_detected INTEGER DEFAULT 0,
        
        -- Analisis Perspektif Tugas Akhir
        islamic_compliance_score REAL DEFAULT 0.0,
        islamic_review TEXT,
        consumer_protection_score REAL DEFAULT 0.0,
        consumer_review TEXT,
        
        created_at TEXT
    )
    """)
    conn.commit()
    
    # Migrasi kolom F1 - F8 dan total_visible_engagement jika tabel sudah pernah dibuat sebelumnya
    cursor.execute("PRAGMA table_info(posts)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    
    f_cols = [
        ("total_visible_engagement", "INTEGER DEFAULT 0"),
        ("product_rating", "REAL DEFAULT 0.0"),
        ("is_sample_valid", "INTEGER DEFAULT 1"),
        ("sampling_inclusion", "TEXT DEFAULT '{}'"),
        ("sampling_exclusion", "TEXT DEFAULT '{}'"),
        ("sampling_notes", "TEXT DEFAULT 'Memenuhi kriteria purposive sampling'"),
        ("f1_object_detection", "INTEGER DEFAULT 1"), ("f1_detail", "TEXT"),
        ("f2_color_extraction", "INTEGER DEFAULT 1"), ("f2_detail", "TEXT"),
        ("f3_posisi_objek", "INTEGER DEFAULT 1"), ("f3_detail", "TEXT"),
        ("f4_dominasi_objek", "INTEGER DEFAULT 1"), ("f4_detail", "TEXT"),
        ("f5_background", "INTEGER DEFAULT 1"), ("f5_detail", "TEXT"),
        ("f6_objek_tambahan", "INTEGER DEFAULT 0"), ("f6_detail", "TEXT"),
        ("f7_manusia", "INTEGER DEFAULT 0"), ("f7_detail", "TEXT"),
        ("f8_teks", "INTEGER DEFAULT 0"), ("f8_detail", "TEXT"),
    ]
    for col_name, col_type in f_cols:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE posts ADD COLUMN {col_name} {col_type}")
            
    # Backfill nilai Total Visible Engagement = likes + comments jika masih 0/null
    cursor.execute("""
        UPDATE posts 
        SET total_visible_engagement = COALESCE(likes, 0) + COALESCE(comments, 0)
        WHERE total_visible_engagement IS NULL OR total_visible_engagement = 0
    """)
    cursor.execute("""
        UPDATE posts 
        SET is_sample_valid = 1 
        WHERE is_sample_valid IS NULL
    """)

    conn.commit()
    conn.close()

def calculate_total_visible_engagement(likes, comments):
    """
    Menghitung Total Visible Engagement (TVE).
    TVE = Likes + Comments
    (Total interaksi publik yang terlihat langsung oleh konsumen pada postingan).
    """
    return int((likes or 0) + (comments or 0))

def calculate_engagement_rate(likes, comments, shares, saves, followers):
    if followers and followers > 0:
        total_eng = (likes or 0) + (comments or 0) + (shares or 0) + (saves or 0)
        return round((total_eng / followers) * 100.0, 4)
    elif (likes or 0) + (comments or 0) > 0:
        return round(((likes or 0) + (comments or 0) * 2) / 100.0, 4)
    return 0.0

def insert_post(data):
    conn = get_connection()
    cursor = conn.cursor()
    
    tve = calculate_total_visible_engagement(
        data.get("likes", 0),
        data.get("comments", 0)
    )
    er = calculate_engagement_rate(
        data.get("likes", 0),
        data.get("comments", 0),
        data.get("shares", 0),
        data.get("saves", 0),
        data.get("followers", 0)
    )
    data["total_visible_engagement"] = tve
    data["engagement_rate"] = er
    data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Pastikan default keys ada
    data.setdefault("image_path", "")
    data.setdefault("caption", "")
    data.setdefault("followers", 0)
    data.setdefault("likes", 0)
    data.setdefault("comments", 0)
    data.setdefault("shares", 0)
    data.setdefault("saves", 0)
    data.setdefault("product_rating", 0.0)
    data.setdefault("platform", "Shopee")
    data.setdefault("post_title", "Postingan Produk")
    data.setdefault("umkm_name", "UMKM")
    data.setdefault("post_date", datetime.now().strftime("%Y-%m-%d"))
    data.setdefault("is_sample_valid", 1)
    data.setdefault("sampling_inclusion", "{}")
    data.setdefault("sampling_exclusion", "{}")
    data.setdefault("sampling_notes", "Memenuhi kriteria purposive sampling")

    data.setdefault("cv_brightness", 0.0)
    data.setdefault("cv_contrast", 0.0)
    data.setdefault("cv_text_density", 0.0)
    data.setdefault("cv_dominant_color", "")
    data.setdefault("cv_face_detected", 0)
    data.setdefault("islamic_compliance_score", 0.0)
    data.setdefault("islamic_review", "")
    data.setdefault("consumer_protection_score", 0.0)
    data.setdefault("consumer_review", "")

    for i in range(1, 9):
        data.setdefault(f"k{i}_detail", "")
        data.setdefault(f"f{i}_detail", "")

    data.setdefault("k1_nama_produk", 0)
    data.setdefault("k2_harga", 0)
    data.setdefault("k3_diskon", 0)
    data.setdefault("k4_periode_promo", 0)
    data.setdefault("k5_syarat_promo", 0)
    data.setdefault("k6_info_produk", 0)
    data.setdefault("k7_klaim", 0)
    data.setdefault("k8_visual_caption", 0)

    data.setdefault("f1_object_detection", 1)
    data.setdefault("f2_color_extraction", 1)
    data.setdefault("f3_posisi_objek", 1)
    data.setdefault("f4_dominasi_objek", 1)
    data.setdefault("f5_background", 1)
    data.setdefault("f6_objek_tambahan", 0)
    data.setdefault("f7_manusia", 0)
    data.setdefault("f8_teks", 0)

    query = """
    INSERT INTO posts (
        post_title, umkm_name, platform, post_date, image_path, caption,
        followers, likes, comments, total_visible_engagement, shares, saves, product_rating, engagement_rate,
        is_sample_valid, sampling_inclusion, sampling_exclusion, sampling_notes,
        k1_nama_produk, k1_detail,
        k2_harga, k2_detail,
        k3_diskon, k3_detail,
        k4_periode_promo, k4_detail,
        k5_syarat_promo, k5_detail,
        k6_info_produk, k6_detail,
        k7_klaim, k7_detail,
        k8_visual_caption, k8_detail,
        f1_object_detection, f1_detail,
        f2_color_extraction, f2_detail,
        f3_posisi_objek, f3_detail,
        f4_dominasi_objek, f4_detail,
        f5_background, f5_detail,
        f6_objek_tambahan, f6_detail,
        f7_manusia, f7_detail,
        f8_teks, f8_detail,
        cv_brightness, cv_contrast, cv_text_density, cv_dominant_color, cv_face_detected,
        islamic_compliance_score, islamic_review,
        consumer_protection_score, consumer_review,
        created_at
    ) VALUES (
        :post_title, :umkm_name, :platform, :post_date, :image_path, :caption,
        :followers, :likes, :comments, :total_visible_engagement, :shares, :saves, :product_rating, :engagement_rate,
        :is_sample_valid, :sampling_inclusion, :sampling_exclusion, :sampling_notes,
        :k1_nama_produk, :k1_detail,
        :k2_harga, :k2_detail,
        :k3_diskon, :k3_detail,
        :k4_periode_promo, :k4_detail,
        :k5_syarat_promo, :k5_detail,
        :k6_info_produk, :k6_detail,
        :k7_klaim, :k7_detail,
        :k8_visual_caption, :k8_detail,
        :f1_object_detection, :f1_detail,
        :f2_color_extraction, :f2_detail,
        :f3_posisi_objek, :f3_detail,
        :f4_dominasi_objek, :f4_detail,
        :f5_background, :f5_detail,
        :f6_objek_tambahan, :f6_detail,
        :f7_manusia, :f7_detail,
        :f8_teks, :f8_detail,
        :cv_brightness, :cv_contrast, :cv_text_density, :cv_dominant_color, :cv_face_detected,
        :islamic_compliance_score, :islamic_review,
        :consumer_protection_score, :consumer_review,
        :created_at
    )
    """
    cursor.execute(query, data)
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return post_id

def get_all_posts():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM posts ORDER BY id DESC", conn)
    conn.close()
    return df

def delete_post(post_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()

def clear_all_posts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts")
    conn.commit()
    conn.close()

def seed_sample_data():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM posts")
    count = cursor.fetchone()[0]
    
    if count == 0:
        samples = [
            {
                "post_title": "Promo Kopi Susu Aren Spesial Ramadhan",
                "umkm_name": "Kopi Senja Barokah",
                "platform": "Instagram",
                "post_date": "2026-03-15",
                "image_path": "",
                "caption": "Menu Kopi Susu Aren gula asli! Beli 2 Gratis 1 hanya Rp 35.000 berlaku hingga 20 Maret 2026. Syarat follow & mention 3 teman. 100% Halal MUI bersertifikat.",
                "followers": 4500, "likes": 320, "comments": 45, "shares": 18, "saves": 32,
                "k1_nama_produk": 1, "k1_detail": "Nama 'Kopi Susu Aren' tertera jelas di visual tengah",
                "k2_harga": 1, "k2_detail": "Harga Rp 35.000 tertera transparan di pojok kanan bawah",
                "k3_diskon": 1, "k3_detail": "Beli 2 Gratis 1 dengan badge promo merah",
                "k4_periode_promo": 1, "k4_detail": "Tertulis 'Berlaku s.d 20 Maret 2026'",
                "k5_syarat_promo": 1, "k5_detail": "Syarat follow IG & mention dicantumkan jelas",
                "k6_info_produk": 1, "k6_detail": "Keterangan biji kopi arabika & gula aren asli",
                "k7_klaim": 1, "k7_detail": "Klaim '100% Halal MUI' dengan logo resmi",
                "k8_visual_caption": 1, "k8_detail": "Sangat sinkron: visual botol kopi sesuai dengan deskripsi caption",
                "f1_object_detection": 1, "f1_detail": "Objek botol minuman kopi terdeteksi jelas",
                "f2_color_extraction": 1, "f2_detail": "Warna dominan Coklat Hangat (#542d17) & Emas",
                "f3_posisi_objek": 1, "f3_detail": "Tengah (Center Composition)",
                "f4_dominasi_objek": 1, "f4_detail": "Sangat Dominan (48% kanvas foto)",
                "f5_background": 1, "f5_detail": "Studio Polos Bersih (Clean Solid)",
                "f6_objek_tambahan": 1, "f6_detail": "Stiker badge promo merah & logo halal",
                "f7_manusia": 0, "f7_detail": "Fokus objek produk murni tanpa model manusia",
                "f8_teks": 1, "f8_detail": "Overlay teks tipografi promo & harga pada gambar",
                "cv_brightness": 142.5, "cv_contrast": 68.2, "cv_text_density": 0.28, "cv_dominant_color": "Coklat Hangat", "cv_face_detected": 0,
                "islamic_compliance_score": 95.0,
                "islamic_review": "Sangat baik: Bebas gharar (harga transparan, akad jelas), kejujuran klaim (shiddiq) terbukti sertifikasi halal.",
                "consumer_protection_score": 92.0,
                "consumer_review": "Memenuhi UU PK No. 8/1999: Informasi harga, masa promo, dan syarat disampaikan transparan."
            },
            {
                "post_title": "Hijab Voal Premium Segi Empat",
                "umkm_name": "Alya Hijab Official",
                "platform": "Instagram",
                "post_date": "2026-03-18",
                "image_path": "",
                "caption": "Tampil anggun dengan hijab voal ultrafine tebal & tegak di dahi. Minat langsung DM ya ukh sayyy, stok terbatas!!",
                "followers": 12000, "likes": 540, "comments": 110, "shares": 15, "saves": 85,
                "k1_nama_produk": 1, "k1_detail": "Terlihat teks 'Voal Ultrafine Segi Empat'",
                "k2_harga": 0, "k2_detail": "Harga tidak dicantumkan di visual maupun caption (hanya 'DM')",
                "k3_diskon": 0, "k3_detail": "Tidak ada elemen diskon",
                "k4_periode_promo": 0, "k4_detail": "Tidak ada periode promo",
                "k5_syarat_promo": 0, "k5_detail": "Tidak ada syarat promo",
                "k6_info_produk": 1, "k6_detail": "Tersedia info material voal dan warna",
                "k7_klaim": 1, "k7_detail": "Klaim 'Tegak seharian & anti kusut'",
                "k8_visual_caption": 1, "k8_detail": "Visual model memakai hijab sesuai caption",
                "f1_object_detection": 1, "f1_detail": "Objek fashion hijab / pakaian terdeteksi",
                "f2_color_extraction": 1, "f2_detail": "Warna dominan Pastel Pink (#e8c5c8)",
                "f3_posisi_objek": 1, "f3_detail": "Tengah (Center)",
                "f4_dominasi_objek": 1, "f4_detail": "Dominan Sedang (38% area)",
                "f5_background": 1, "f5_detail": "Studio Soft Bokeh",
                "f6_objek_tambahan": 0, "f6_detail": "Tanpa ornamen grafis ramai",
                "f7_manusia": 1, "f7_detail": "Model wanita mengenakan hijab terdeteksi jelas",
                "f8_teks": 1, "f8_detail": "Teks logo brand di bagian atas",
                "cv_brightness": 165.0, "cv_contrast": 72.0, "cv_text_density": 0.12, "cv_dominant_color": "Pastel Pink", "cv_face_detected": 1,
                "islamic_compliance_score": 60.0,
                "islamic_review": "Catatan Fiqh Muamalah: Menyembunyikan harga ('DM for price') menimbulkan ketidakpastian (gharar khafi) sebelum akad.",
                "consumer_protection_score": 65.0,
                "consumer_review": "Kurang patuh UU PK Pasal 4 & 7: Hak konsumen untuk mengetahui kepastian harga sejak awal tidak terpenuhi."
            }
        ]
        for s in samples:
            insert_post(s)
            
    conn.close()

def find_known_brand_followers(brand_query: str) -> int:
    """Cari jumlah followers tersimpan untuk brand yang cocok di database."""
    if not brand_query:
        return 0
    import re
    clean_q = re.sub(r"[^a-zA-Z0-9]", "", brand_query.lower())
    if not clean_q or len(clean_q) < 3:
        return 0
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT followers, umkm_name FROM posts WHERE followers > 0 ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        for r in rows:
            db_umkm = re.sub(r"[^a-zA-Z0-9]", "", (r["umkm_name"] or "").lower())
            if clean_q in db_umkm or db_umkm in clean_q:
                return int(r["followers"])
    except Exception:
        pass
    return 0

if __name__ == "__main__":
    init_db()
    seed_sample_data()
    print("Database schema updated with F1-F8 successfully!")
