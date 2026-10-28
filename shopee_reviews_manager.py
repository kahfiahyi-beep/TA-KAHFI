"""
shopee_reviews_manager.py
=========================
Modul Pengelolaan Ulasan dan Komentar Pembeli Shopee (Fungsional, Persistent SQLite, Analisis Sentimen).
Fitur:
- CRUD Ulasan Pembeli (Tambah Manual, Edit, Hapus dengan konfirmasi)
- Penyimpanan Database SQLite (ta_umkm_vision.db -> tabel shopee_reviews)
- Analisis Sentimen Otomatis (Leksikon Bahasa Indonesia + Rating Prior + Koreksi Manual)
- Impor Fleksibel CSV / Excel (.xlsx, .xls) dengan Pemetaan Kolom, Validasi, & Deteksi Duplikat
- Unduh Template CSV Resmi
- Filter Bintang (1-5), Filter Sentimen (Positif, Netral, Negatif), Filter Tanggal, Pencarian Kata Kunci
- Pengurutan (Terbaru, Terlama, Rating Tertinggi, Rating Terendah)
- Statistik Ringkasan Real-time (Total, Rata-rata Rating, Distribusi Sentimen & Bintang)
- Sinkronisasi dengan Metrik Engagement Postingan (Jumlah Penilaian & Rating Produk)
- UI Dark Theme Responsif & Konsisten
"""

import os
import re
import io
import sqlite3
from datetime import datetime, date
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(__file__), "ta_umkm_vision.db")

# ─────────────────────────────────────────────────────────────────────────────
# 1. DATABASE ACCESS & TABLE INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────────

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_reviews_table():
    """Inisialisasi tabel shopee_reviews di database SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shopee_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER DEFAULT NULL,
        product_name TEXT DEFAULT '',
        review_id TEXT DEFAULT '',
        reviewer_name TEXT NOT NULL,
        review_date TEXT NOT NULL,
        rating INTEGER NOT NULL,
        review_text TEXT NOT NULL,
        product_variant TEXT DEFAULT '',
        verified_purchase INTEGER DEFAULT 1,
        source TEXT DEFAULT 'Input Manual',
        sentiment_auto TEXT DEFAULT 'Netral',
        sentiment TEXT DEFAULT 'Netral',
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_shopee_rev_rating ON shopee_reviews(rating);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_shopee_rev_sentiment ON shopee_reviews(sentiment);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_shopee_rev_date ON shopee_reviews(review_date);")
    conn.commit()
    conn.close()

# Pastikan tabel dibuat saat modul di-load
init_reviews_table()

# ─────────────────────────────────────────────────────────────────────────────
# 2. SENTIMENT ANALYSIS ENGINE (Indonesian Lexicon + Negation + Rating Prior)
# ─────────────────────────────────────────────────────────────────────────────

class ShopeeSentimentAnalyzer:
    """
    Mesin Analisis Sentimen Ulasan E-Commerce Bahasa Indonesia.
    Menggunakan leksikon kata positif/negatif, penanganan negasi, dan prior rating bintang.
    """
    
    POSITIVE_WORDS = {
        "bagus", "bagus banget", "mantap", "mantul", "puas", "recomended", "recommended",
        "rekomen", "suka", "suka banget", "oke", "ok", "keren", "original", "ori",
        "cepat", "rapi", "raping", "aman", "berkualitas", "kualitas terbaik", "terbaik",
        "top", "sesuai", "sesuai deskripsi", "sesuai ekspektasi", "ramah", "wangi",
        "enak", "sedap", "makasih", "terima kasih", "thanks", "worth it", "terjangkau",
        "murah", "awet", "estetik", "cantik", "adem", "nyaman", "tebal", "pas",
        "baguss", "suksess", "love", "memuaskan", "cepat sampai", "fast respon",
        "packing rapi", "pelayanan baik", "sempurna", "jos", "juara"
    }

    NEGATIVE_WORDS = {
        "kecewa", "jelek", "rusak", "pecah", "bocor", "lambat", "lama", "lelet",
        "bohong", "palsu", "cacat", "tumpah", "kurang", "tidak sesuai", "beda",
        "mahal", "kasar", "bau", "apek", "zonk", "mengecewakan", "buruk", "rugi",
        "cancel", "penipu", "basi", "expired", "tipis", "sobek", "patah", "kotor",
        "parah", "nyesel", "menyesal", "tidak ori", "kw", "kapok", "bad", "lelet",
        "salah warna", "salah ukuran", "kurang ajar", "penjual cuek", "komplain"
    }

    NEGATION_WORDS = {
        "tidak", "bukan", "ga", "gak", "nggak", "ngga", "tak", "kurang", "jangan", "bkn"
    }

    BOOSTER_WORDS = {
        "sangat", "banget", "bgt", "amat", "sekali", "super", "pol", "bener-bener", "benar-benar"
    }

    @classmethod
    def analyze(cls, text: str, rating: Optional[int] = None) -> Tuple[str, float, str]:
        """
        Menganalisis teks ulasan dan mengembalikan:
        (sentiment_label: 'Positif'|'Netral'|'Negatif', confidence_score, penjelasan)
        """
        if not text or not text.strip():
            # Jika teks kosong, gunakan rating bintang sebagai referensi
            if rating is not None:
                if rating >= 4:
                    return "Positif", 0.70, "Berdasarkan rating bintang (⭐ 4–5)"
                elif rating <= 2:
                    return "Negatif", 0.70, "Berdasarkan rating bintang (⭐ 1–2)"
                else:
                    return "Netral", 0.60, "Berdasarkan rating bintang netral (⭐ 3)"
            return "Netral", 0.50, "Tidak ada teks atau rating ulasan"

        clean = text.lower()
        # Bersihkan tanda baca sederhana tapi pertahankan spasi
        words = re.findall(r"\b[a-z0-9\-]+\b", clean)
        
        pos_score = 0.0
        neg_score = 0.0
        
        # Deteksi n-gram 2 kata terlebih dahulu (misal: "tidak bagus", "bagus banget", "packing rapi")
        matched_ngrams = set()
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            if bigram in cls.POSITIVE_WORDS:
                pos_score += 2.0
                matched_ngrams.add(i)
                matched_ngrams.add(i+1)
            elif bigram in cls.NEGATIVE_WORDS:
                neg_score += 2.0
                matched_ngrams.add(i)
                matched_ngrams.add(i+1)
            elif words[i] in cls.NEGATION_WORDS and words[i+1] in cls.POSITIVE_WORDS:
                # "tidak bagus" -> menjadi sinyal negatif kuat
                neg_score += 2.0
                matched_ngrams.add(i)
                matched_ngrams.add(i+1)
            elif words[i] in cls.NEGATION_WORDS and words[i+1] in cls.NEGATIVE_WORDS:
                # "tidak kecewa" -> menjadi sinyal positif
                pos_score += 1.5
                matched_ngrams.add(i)
                matched_ngrams.add(i+1)

        # Analisis kata tunggal
        for idx, w in enumerate(words):
            if idx in matched_ngrams:
                continue
            is_negated = (idx > 0 and words[idx - 1] in cls.NEGATION_WORDS)
            
            if w in cls.POSITIVE_WORDS:
                if is_negated:
                    neg_score += 1.5
                else:
                    pos_score += 1.0
            elif w in cls.NEGATIVE_WORDS:
                if is_negated:
                    pos_score += 1.0
                else:
                    neg_score += 1.5

        # Evaluasi pengaruh rating bintang
        if rating is not None:
            if rating >= 4:
                pos_score += 1.2
            elif rating <= 2:
                neg_score += 1.5
            elif rating == 3:
                # Bintang 3 memberi bobot netral
                pass

        # Penentuan label
        diff = pos_score - neg_score
        if diff > 0.4:
            conf = min(0.98, 0.65 + (diff * 0.1))
            return "Positif", round(conf, 2), f"Terdeteksi kata kepuasan (Positif: {pos_score:.1f}, Negatif: {neg_score:.1f})"
        elif diff < -0.4:
            conf = min(0.98, 0.65 + (abs(diff) * 0.1))
            return "Negatif", round(conf, 2), f"Terdeteksi keluhan/ketidakpuasan (Positif: {pos_score:.1f}, Negatif: {neg_score:.1f})"
        else:
            return "Netral", 0.60, f"Ulasan bernada seimbang / informatif (Positif: {pos_score:.1f}, Negatif: {neg_score:.1f})"

# ─────────────────────────────────────────────────────────────────────────────
# 3. CRUD DATABASE OPERATIONS FOR SHOPEE REVIEWS
# ─────────────────────────────────────────────────────────────────────────────

def add_review(
    reviewer_name: str,
    review_date: str,
    rating: int,
    review_text: str,
    product_variant: str = "",
    verified_purchase: bool = True,
    source: str = "Input Manual",
    sentiment_override: Optional[str] = None,
    notes: str = "",
    post_id: Optional[int] = None,
    product_name: str = "",
    review_id: str = ""
) -> Tuple[bool, str, Optional[int]]:
    """
    Menambahkan ulasan pembeli baru dengan validasi dan pencegahan duplikasi.
    """
    # 1. Validasi Kolom Wajib
    if not review_text or not review_text.strip():
        return False, "Isi komentar ulasan wajib diisi dan tidak boleh kosong.", None
    
    if not (1 <= int(rating) <= 5):
        return False, f"Rating harus bernilai bilangan bulat 1 hingga 5 (Diterima: {rating}).", None

    reviewer_name = reviewer_name.strip() if reviewer_name else "Pengguna Shopee (Anonim)"
    
    # 2. Validasi Tanggal
    clean_date = review_date.strip() if review_date else datetime.now().strftime("%Y-%m-%d")
    try:
        # Coba parse tanggal
        datetime.strptime(clean_date[:10], "%Y-%m-%d")
    except ValueError:
        clean_date = datetime.now().strftime("%Y-%m-%d")

    # 3. Analisis Sentimen Otomatis
    auto_sent, _, _ = ShopeeSentimentAnalyzer.analyze(review_text, rating)
    final_sentiment = sentiment_override if sentiment_override in ["Positif", "Netral", "Negatif"] else auto_sent

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 4. Deteksi Duplikasi
        if review_id and review_id.strip():
            cursor.execute("SELECT id FROM shopee_reviews WHERE review_id = ?", (review_id.strip(),))
            if cursor.fetchone():
                conn.close()
                return False, f"Ulasan dengan ID '{review_id}' sudah tersimpan sebelumnya (Duplikat).", None
        else:
            # Periksa kombinasi reviewer_name, review_date, dan teks ulasan
            cursor.execute(
                "SELECT id FROM shopee_reviews WHERE reviewer_name = ? AND review_date = ? AND review_text = ?",
                (reviewer_name, clean_date, review_text.strip())
            )
            if cursor.fetchone():
                conn.close()
                return False, f"Ulasan serupa dari '{reviewer_name}' pada tanggal {clean_date} sudah ada.", None

        # 5. Insert ke Database
        cursor.execute("""
            INSERT INTO shopee_reviews (
                post_id, product_name, review_id, reviewer_name, review_date,
                rating, review_text, product_variant, verified_purchase,
                source, sentiment_auto, sentiment, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            post_id,
            product_name.strip(),
            review_id.strip(),
            reviewer_name,
            clean_date,
            int(rating),
            review_text.strip(),
            product_variant.strip(),
            1 if verified_purchase else 0,
            source,
            auto_sent,
            final_sentiment,
            notes.strip(),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        new_id = cursor.lastrowid
        conn.commit()
        return True, "Ulasan berhasil disimpan ke database!", new_id
    except Exception as e:
        conn.rollback()
        return False, f"Gagal menyimpan ke database: {str(e)}", None
    finally:
        conn.close()

def update_review(
    review_pk: int,
    reviewer_name: str,
    review_date: str,
    rating: int,
    review_text: str,
    product_variant: str,
    verified_purchase: bool,
    sentiment: str,
    notes: str
) -> Tuple[bool, str]:
    """Mengubah data ulasan yang sudah tersimpan."""
    if not review_text or not review_text.strip():
        return False, "Isi komentar ulasan tidak boleh kosong."
    if not (1 <= int(rating) <= 5):
        return False, "Rating harus bernilai 1 hingga 5."

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Jalankan ulang analisis sentimen otomatis
        auto_sent, _, _ = ShopeeSentimentAnalyzer.analyze(review_text, rating)
        
        cursor.execute("""
            UPDATE shopee_reviews
            SET reviewer_name = ?,
                review_date = ?,
                rating = ?,
                review_text = ?,
                product_variant = ?,
                verified_purchase = ?,
                sentiment_auto = ?,
                sentiment = ?,
                notes = ?
            WHERE id = ?
        """, (
            reviewer_name.strip() or "Pengguna Shopee (Anonim)",
            review_date,
            int(rating),
            review_text.strip(),
            product_variant.strip(),
            1 if verified_purchase else 0,
            auto_sent,
            sentiment if sentiment in ["Positif", "Netral", "Negatif"] else auto_sent,
            notes.strip(),
            review_pk
        ))
        conn.commit()
        return True, "Ulasan berhasil diperbarui!"
    except Exception as e:
        conn.rollback()
        return False, f"Gagal memperbarui ulasan: {str(e)}"
    finally:
        conn.close()

def delete_review(review_pk: int) -> Tuple[bool, str]:
    """Menghapus ulasan dari database berdasarkan primary key id."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM shopee_reviews WHERE id = ?", (review_pk,))
        conn.commit()
        return True, "Ulasan berhasil dihapus."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal menghapus ulasan: {str(e)}"
    finally:
        conn.close()

def clear_all_reviews() -> Tuple[bool, str]:
    """Menghapus seluruh ulasan (fungsi reset/pembersihan)."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM shopee_reviews")
        conn.commit()
        return True, "Seluruh ulasan Shopee berhasil dibersihkan."
    except Exception as e:
        conn.rollback()
        return False, f"Gagal membersihkan ulasan: {str(e)}"
    finally:
        conn.close()

def get_reviews(
    search: Optional[str] = None,
    rating_filter: Optional[int] = None,
    sentiment_filter: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    sort_by: str = "Terbaru",
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Mengambil daftar ulasan dari database dengan query dinamis."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM shopee_reviews WHERE 1=1"
    params = []

    if search and search.strip():
        q_term = f"%{search.strip()}%"
        query += " AND (reviewer_name LIKE ? OR review_text LIKE ? OR product_variant LIKE ? OR notes LIKE ?)"
        params.extend([q_term, q_term, q_term, q_term])

    if rating_filter and 1 <= rating_filter <= 5:
        query += " AND rating = ?"
        params.append(rating_filter)

    if sentiment_filter and sentiment_filter in ["Positif", "Netral", "Negatif"]:
        query += " AND sentiment = ?"
        params.append(sentiment_filter)

    if start_date:
        query += " AND date(review_date) >= date(?)"
        params.append(start_date.strftime("%Y-%m-%d"))

    if end_date:
        query += " AND date(review_date) <= date(?)"
        params.append(end_date.strftime("%Y-%m-%d"))

    # Sorting
    if sort_by == "Terbaru":
        query += " ORDER BY date(review_date) DESC, id DESC"
    elif sort_by == "Terlama":
        query += " ORDER BY date(review_date) ASC, id ASC"
    elif sort_by == "Rating Tertinggi":
        query += " ORDER BY rating DESC, date(review_date) DESC"
    elif sort_by == "Rating Terendah":
        query += " ORDER BY rating ASC, date(review_date) DESC"
    else:
        query += " ORDER BY id DESC"

    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_review_statistics(
    search: Optional[str] = None,
    rating_filter: Optional[int] = None,
    sentiment_filter: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Dict[str, Any]:
    """Menghitung ringkasan statistik ulasan nyata secara real-time dari data tersimpan."""
    reviews = get_reviews(
        search=search,
        rating_filter=rating_filter,
        sentiment_filter=sentiment_filter,
        start_date=start_date,
        end_date=end_date,
        sort_by="Terbaru",
        limit=None
    )
    
    total = len(reviews)
    if total == 0:
        return {
            "total": 0,
            "avg_rating": 0.0,
            "positive_count": 0,
            "neutral_count": 0,
            "negative_count": 0,
            "positive_pct": 0.0,
            "neutral_pct": 0.0,
            "negative_pct": 0.0,
            "rating_distribution": {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
        }

    sum_rating = sum(r["rating"] for r in reviews)
    avg_rating = round(sum_rating / total, 2)
    
    pos = sum(1 for r in reviews if r.get("sentiment") == "Positif")
    neu = sum(1 for r in reviews if r.get("sentiment") == "Netral")
    neg = sum(1 for r in reviews if r.get("sentiment") == "Negatif")
    
    dist_rating = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for r in reviews:
        star = r.get("rating", 5)
        if star in dist_rating:
            dist_rating[star] += 1

    return {
        "total": total,
        "avg_rating": avg_rating,
        "positive_count": pos,
        "neutral_count": neu,
        "negative_count": neg,
        "positive_pct": round((pos / total) * 100, 1),
        "neutral_pct": round((neu / total) * 100, 1),
        "negative_pct": round((neg / total) * 100, 1),
        "rating_distribution": dist_rating
    }

# ─────────────────────────────────────────────────────────────────────────────
# 4. CSV / EXCEL IMPORT & EXPORT ENGINE
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_CSV_CONTENT = """review_id,product_name,reviewer_name,review_date,rating,review_text,product_variant,verified_purchase,source,sentiment,notes
SHOPEE-001,Kopi Susu Aren 250ml,Budi Santoso,2025-02-10,5,Rasanya mantap banget! Manisnya pas gula aren asli, packing aman tidak bocor sampai tujuan.,Botol 250ml,1,Impor File,Positif,Pelanggan repeat order
SHOPEE-002,Kopi Susu Aren 250ml,Siti Rahmawati,2025-02-12,4,Kopi enak dan segar, pengiriman cepat sampai. Cuma botolnya sedikit penyok tapi aman.,Botol 250ml,1,Impor File,Positif,Saran bubble wrap tebal
SHOPEE-003,Kopi Susu Aren 250ml,Ahmad Pratama,2025-02-14,3,Rasa kopinya standar, harga terjangkau. Kurir agak lama sampainya.,Botol 500ml,1,Impor File,Netral,Pengiriman kendala ekspedisi
SHOPEE-004,Kopi Susu Aren 250ml,Dewi Lestari,2025-02-15,1,Kecewa sekali, tutup botol kendor jadi kopinya tumpah berantakan di kardus!,Botol 250ml,1,Impor File,Negatif,Ajukan komplain refund
SHOPEE-005,Kopi Susu Aren 250ml,Rian Kusuma,2025-02-18,5,Kualitas terbaik! Sudah beli 3 kali tidak pernah mengecewakan. Rekomen banget.,Family Pack 1L,1,Impor File,Positif,Langganan kantor
"""

def generate_csv_template() -> bytes:
    """Mengembalikan byte template CSV resmi ulasan Shopee untuk diunduh."""
    return SAMPLE_CSV_CONTENT.encode("utf-8")

def parse_uploaded_file(file_obj, filename: str) -> Tuple[Optional[pd.DataFrame], str]:
    """Membaca file upload (CSV atau Excel) ke dalam Pandas DataFrame."""
    try:
        lower_name = filename.lower()
        if lower_name.endswith(".csv"):
            # Coba deteksi delimiter koma atau titik koma
            try:
                df = pd.read_csv(file_obj, encoding="utf-8")
            except Exception:
                file_obj.seek(0)
                df = pd.read_csv(file_obj, encoding="latin-1", sep=None, engine="python")
        elif lower_name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_obj)
        else:
            return None, "Format file tidak didukung. Harap unggah file .csv atau .xlsx / .xls."
        
        # Bersihkan spasi nama kolom
        df.columns = [str(c).strip() for c in df.columns]
        return df, "OK"
    except Exception as e:
        return None, f"Gagal membaca file: {str(e)}"

def detect_column_mappings(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """
    Secara pintar memetakan nama kolom di file Excel/CSV ke kolom standar aplikasi.
    """
    cols = {c.lower(): c for c in df.columns}
    
    def find_match(candidates: List[str]) -> Optional[str]:
        for cand in candidates:
            for lower_c, orig_c in cols.items():
                if cand == lower_c or cand in lower_c:
                    return orig_c
        return None

    mapping = {
        "review_text": find_match(["review_text", "ulasan", "komentar", "review", "comment", "isi", "feedback", "pesan"]),
        "rating": find_match(["rating", "bintang", "star", "stars", "nilai", "skor", "score"]),
        "reviewer_name": find_match(["reviewer_name", "nama_pembeli", "reviewer", "nama", "buyer", "user", "username", "customer"]),
        "review_date": find_match(["review_date", "tanggal", "tgl", "date", "waktu", "created"]),
        "product_variant": find_match(["product_variant", "varian", "variant", "variasi", "opsi", "type"]),
        "verified_purchase": find_match(["verified_purchase", "terverifikasi", "verified", "is_verified"]),
        "source": find_match(["source", "sumber"]),
        "sentiment": find_match(["sentiment", "sentimen", "label"]),
        "notes": find_match(["notes", "catatan", "note", "keterangan"]),
        "review_id": find_match(["review_id", "id_ulasan", "id", "no_ulasan"]),
        "product_name": find_match(["product_name", "nama_produk", "produk", "product"])
    }
    return mapping

def import_reviews_from_dataframe(
    df: pd.DataFrame,
    column_mapping: Dict[str, str],
    source_name: str = "Impor CSV/Excel"
) -> Dict[str, Any]:
    """
    Memproses impor data dari DataFrame dengan validasi baris per baris,
    pencegahan duplikasi, dan pencatatan error yang detail.
    """
    total_rows = len(df)
    success_count = 0
    duplicate_count = 0
    rejected_count = 0
    error_details = []

    text_col = column_mapping.get("review_text")
    if not text_col or text_col not in df.columns:
        return {
            "success": False,
            "message": "Kolom 'Isi Ulasan' wajib dipetakan untuk melakukan impor.",
            "total": total_rows,
            "imported": 0,
            "duplicates": 0,
            "rejected": total_rows,
            "errors": ["Kolom isi ulasan tidak ditemukan."]
        }

    rating_col = column_mapping.get("rating")
    reviewer_col = column_mapping.get("reviewer_name")
    date_col = column_mapping.get("review_date")
    variant_col = column_mapping.get("product_variant")
    verified_col = column_mapping.get("verified_purchase")
    sentiment_col = column_mapping.get("sentiment")
    notes_col = column_mapping.get("notes")
    id_col = column_mapping.get("review_id")
    product_col = column_mapping.get("product_name")

    for idx, row in df.iterrows():
        row_num = idx + 2 # asumsi baris header adalah baris 1
        
        # 1. Teks ulasan
        raw_text = str(row.get(text_col, "")).strip()
        if not raw_text or raw_text.lower() == "nan":
            rejected_count += 1
            error_details.append(f"Baris {row_num}: Isi ulasan kosong.")
            continue

        # 2. Rating
        raw_rating = row.get(rating_col) if rating_col and rating_col in df.columns else 5
        try:
            if pd.isna(raw_rating):
                rating_val = 5
            else:
                rating_val = int(float(str(raw_rating).strip()))
            if not (1 <= rating_val <= 5):
                rejected_count += 1
                error_details.append(f"Baris {row_num}: Rating bernilai {raw_rating} (harus antara 1 hingga 5).")
                continue
        except Exception:
            rejected_count += 1
            error_details.append(f"Baris {row_num}: Nilai rating '{raw_rating}' tidak valid.")
            continue

        # 3. Reviewer Name
        raw_name = str(row.get(reviewer_col, "")).strip() if reviewer_col and reviewer_col in df.columns else ""
        if not raw_name or raw_name.lower() == "nan":
            raw_name = f"Pengguna Shopee (Baris {row_num})"

        # 4. Tanggal
        raw_date = row.get(date_col) if date_col and date_col in df.columns else ""
        if pd.isna(raw_date) or not str(raw_date).strip():
            date_val = datetime.now().strftime("%Y-%m-%d")
        else:
            try:
                date_val = pd.to_datetime(raw_date).strftime("%Y-%m-%d")
            except Exception:
                date_val = datetime.now().strftime("%Y-%m-%d")

        # 5. Varian
        raw_variant = str(row.get(variant_col, "")).strip() if variant_col and variant_col in df.columns else ""
        if raw_variant.lower() == "nan":
            raw_variant = ""

        # 6. Verified Purchase
        raw_ver = row.get(verified_col) if verified_col and verified_col in df.columns else 1
        if pd.isna(raw_ver):
            ver_val = True
        else:
            ver_val = str(raw_ver).strip().lower() in ["1", "true", "ya", "yes", "verified", "terverifikasi"]

        # 7. Sentimen
        raw_sent = str(row.get(sentiment_col, "")).strip().capitalize() if sentiment_col and sentiment_col in df.columns else None
        if raw_sent not in ["Positif", "Netral", "Negatif"]:
            raw_sent = None

        # 8. Notes & IDs
        raw_notes = str(row.get(notes_col, "")).strip() if notes_col and notes_col in df.columns else ""
        if raw_notes.lower() == "nan":
            raw_notes = ""
            
        raw_id = str(row.get(id_col, "")).strip() if id_col and id_col in df.columns else ""
        if raw_id.lower() == "nan":
            raw_id = ""

        raw_prod = str(row.get(product_col, "")).strip() if product_col and product_col in df.columns else ""
        if raw_prod.lower() == "nan":
            raw_prod = ""

        # 9. Insert
        ok, msg, _ = add_review(
            reviewer_name=raw_name,
            review_date=date_val,
            rating=rating_val,
            review_text=raw_text,
            product_variant=raw_variant,
            verified_purchase=ver_val,
            source=source_name,
            sentiment_override=raw_sent,
            notes=raw_notes,
            product_name=raw_prod,
            review_id=raw_id
        )

        if ok:
            success_count += 1
        else:
            if "Duplikat" in msg or "sudah ada" in msg:
                duplicate_count += 1
            else:
                rejected_count += 1
                error_details.append(f"Baris {row_num}: {msg}")

    return {
        "success": True,
        "message": f"Proses impor selesai: {success_count} berhasil, {duplicate_count} duplikat diabaikan, {rejected_count} ditolak.",
        "total": total_rows,
        "imported": success_count,
        "duplicates": duplicate_count,
        "rejected": rejected_count,
        "errors": error_details
    }

# ─────────────────────────────────────────────────────────────────────────────
# 5. STREAMLIT UI COMPONENT: RENDER SECTION
# ─────────────────────────────────────────────────────────────────────────────

def render_shopee_reviews_section(
    current_comments: int = 0,
    current_rating: float = 0.0,
    product_title: str = "Produk Shopee"
):
    """
    Merender antarmuka lengkap Ulasan dan Komentar Pembeli Shopee.
    Ditempatkan langsung di bawah Metrik Engagement Shopee.
    """
    st.markdown("---")
    
    # Header Bagian
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
                    border: 1px solid #334155; border-radius: 12px; padding: 18px 22px; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <h3 style="margin: 0; color: #f8fafc; font-size: 1.25rem; font-weight: 700; display: flex; align-items: center; gap: 8px;">
                        <span>🛍️</span> Ulasan dan Komentar Pembeli Shopee
                    </h3>
                    <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 0.88rem;">
                        Kelola data ulasan pembeli nyata, analisis sentimen otomatis (Positif / Netral / Negatif), filter bintang, serta integrasi dengan metrik engagement.
                    </p>
                </div>
                <div>
                    <span style="background-color: #0369a1; color: #e0f2fe; padding: 4px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">
                        Shopee Reviews v2.0
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ── HITUNG STATISTIK DARI DATABASE REAL ────────────────────────────────────
    stats_all = get_review_statistics()
    total_stored = stats_all["total"]
    avg_rating_stored = stats_all["avg_rating"]

    # ── INTEGRASI & SINKRONISASI DENGAN METRIK ENGAGEMENT ───────────────────────
    st.markdown(
        """
        <div style="background: #111827; border-left: 4px solid #38bdf8; padding: 12px 16px; border-radius: 6px; margin-bottom: 16px;">
            <div style="font-weight: 600; color: #e2e8f0; font-size: 0.9rem; margin-bottom: 4px;">
                🔄 Integrasi Data dengan Metrik Engagement Postingan
            </div>
            <div style="color: #94a3b8; font-size: 0.82rem;">
                Anda dapat menghubungkan jumlah ulasan tersimpan dan rata-rata rating ulasan ke input form 
                <b>"Jumlah Penilaian / Ulasan (Comments)"</b> dan <b>"Rating Penilaian Produk"</b> di atas.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_sync1, col_sync2, col_sync3 = st.columns([1.5, 1.5, 1.0])
    with col_sync1:
        st.markdown(f"**Data Ulasan Tersimpan:** {total_stored} Ulasan | ⭐ {avg_rating_stored:.1f}")
    with col_sync2:
        st.markdown(f"**Metrik Input Form Saat Ini:** {current_comments} Ulasan | ⭐ {current_rating:.1f}")
    with col_sync3:
        if st.button("🔗 Sinkronkan ke Metrik", use_container_width=True, help="Otomatis memperbarui input form engagement di atas sesuai data ulasan nyata."):
            if total_stored > 0:
                st.session_state["in_comments"] = total_stored
                st.session_state["in_rating"] = avg_rating_stored
                st.success("✅ Metrik engagement berhasil disinkronkan dengan dataset ulasan pembeli!")
                st.rerun()
            else:
                st.warning("⚠️ Belum ada ulasan yang tersimpan untuk disinkronkan.")

    # ── TABS PENGELOLA ULASAN ─────────────────────────────────────────────────
    tab_list, tab_add, tab_import, tab_policy = st.tabs([
        f"📋 Daftar & Filter Ulasan ({total_stored})",
        "➕ Tambah Ulasan Manual",
        "📥 Impor File (CSV / Excel)",
        "ℹ️ Keterangan & Kebijakan Shopee"
    ])

    # =========================================================================
    # TAB 1: DAFTAR & FILTER ULASAN
    # =========================================================================
    with tab_list:
        # Ringkasan Statistik Kartu
        st.markdown("##### Ringkasan Statistik Ulasan")
        c_st1, c_st2, c_st3, c_st4, c_st5 = st.columns(5)
        with c_st1:
            st.metric("Total Ulasan", f"{stats_all['total']}")
        with c_st2:
            st.metric("Rata-Rata Rating", f"⭐ {stats_all['avg_rating']:.2f}")
        with c_st3:
            st.metric("Positif 👍", f"{stats_all['positive_count']}", f"{stats_all['positive_pct']}%")
        with c_st4:
            st.metric("Netral 💬", f"{stats_all['neutral_count']}", f"{stats_all['neutral_pct']}%")
        with c_st5:
            st.metric("Negatif 👎", f"{stats_all['negative_count']}", f"{stats_all['negative_pct']}%")

        st.markdown("<hr style='margin: 12px 0; border-color: #334155;'/>", unsafe_allow_html=True)

        # Bar Kontrol Pencarian, Filter & Sorting
        st.markdown("##### 🔍 Filter & Pencarian Ulasan")
        f_c1, f_c2, f_c3, f_c4 = st.columns([2, 1.2, 1.2, 1.4])
        
        with f_c1:
            search_query = st.text_input(
                "Cari Ulasan (Nama / Komentar / Varian):",
                placeholder="Ketik kata kunci...",
                key="shopee_search_q"
            )
        with f_c2:
            star_options = ["Semua Bintang", "⭐ 5 Bintang", "⭐ 4 Bintang", "⭐ 3 Bintang", "⭐ 2 Bintang", "⭐ 1 Bintang"]
            sel_star = st.selectbox("Filter Rating:", star_options, key="shopee_filter_star")
            star_val = int(sel_star.split()[1]) if sel_star != "Semua Bintang" else None
        with f_c3:
            sent_options = ["Semua Sentimen", "Positif", "Netral", "Negatif"]
            sel_sent = st.selectbox("Filter Sentimen:", sent_options, key="shopee_filter_sent")
            sent_val = sel_sent if sel_sent != "Semua Sentimen" else None
        with f_c4:
            sort_options = ["Terbaru", "Terlama", "Rating Tertinggi", "Rating Terendah"]
            sel_sort = st.selectbox("Urutkan:", sort_options, key="shopee_sort_by")

        # Filter Rentang Tanggal (Opsional)
        with st.expander("📅 Filter Rentang Tanggal Ulasan", expanded=False):
            d_c1, d_c2, d_c3 = st.columns([1.5, 1.5, 1])
            with d_c1:
                use_date_filter = st.checkbox("Aktifkan filter tanggal", key="shopee_use_date")
                start_d = st.date_input("Mulai Tanggal:", value=date(2025, 1, 1), key="shopee_start_d") if use_date_filter else None
            with d_c2:
                end_d = st.date_input("Sampai Tanggal:", value=date.today(), key="shopee_end_d") if use_date_filter else None
            with d_c3:
                if use_date_filter and st.button("Reset Tanggal", key="shopee_reset_d"):
                    st.session_state["shopee_use_date"] = False
                    st.rerun()

        # Ambil ulasan terfilter
        filtered_reviews = get_reviews(
            search=search_query,
            rating_filter=star_val,
            sentiment_filter=sent_val,
            start_date=start_d if use_date_filter else None,
            end_date=end_d if use_date_filter else None,
            sort_by=sel_sort
        )

        st.caption(f"Menampilkan **{len(filtered_reviews)}** ulasan yang cocok dengan kriteria filter.")

        # Pagination / Pemuatan Bertahap
        items_per_page = st.selectbox("Jumlah ulasan per halaman:", [5, 10, 20, 50], index=1, key="shopee_page_size")
        total_pages = max(1, (len(filtered_reviews) + items_per_page - 1) // items_per_page)
        curr_page = st.number_input("Halaman:", min_value=1, max_value=total_pages, value=1, step=1, key="shopee_curr_page")

        start_idx = (curr_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_reviews = filtered_reviews[start_idx:end_idx]

        # Tampilkan Ulasan dalam Bentuk Kartu Dark Theme
        if not page_reviews:
            st.info("💡 Belum ada ulasan yang sesuai dengan filter atau kata kunci di atas. Tambahkan ulasan manual atau impor dari file CSV/Excel.")
        else:
            for r in page_reviews:
                rev_id = r["id"]
                r_name = r.get("reviewer_name") or "Pengguna Shopee"
                r_date = r.get("review_date") or "-"
                r_rating = int(r.get("rating", 5))
                r_stars = "⭐" * r_rating
                r_text = r.get("review_text", "")
                r_var = r.get("product_variant", "")
                r_ver = bool(r.get("verified_purchase", 1))
                r_sent = r.get("sentiment", "Netral")
                r_sent_auto = r.get("sentiment_auto", "Netral")
                r_src = r.get("source", "Input Manual")
                r_notes = r.get("notes", "")

                # Badge Sentimen
                if r_sent == "Positif":
                    sent_badge_style = "background-color: #065f46; color: #a7f3d0; border: 1px solid #10b981;"
                    sent_icon = "👍"
                elif r_sent == "Negatif":
                    sent_badge_style = "background-color: #991b1b; color: #fecaca; border: 1px solid #ef4444;"
                    sent_icon = "👎"
                else:
                    sent_badge_style = "background-color: #374151; color: #e5e7eb; border: 1px solid #6b7280;"
                    sent_icon = "💬"

                # Container Kartu
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 14px 18px; margin-bottom: 12px;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                                <div>
                                    <span style="font-weight: 700; color: #f1f5f9; font-size: 0.95rem;">{r_name}</span>
                                    {'<span style="background-color: #064e3b; color: #6ee7b7; font-size: 0.72rem; padding: 2px 7px; border-radius: 9999px; margin-left: 6px; font-weight: 600;">✓ Terverifikasi</span>' if r_ver else ''}
                                    <div style="color: #94a3b8; font-size: 0.78rem; margin-top: 2px;">
                                        📅 {r_date} • <i>{r_src}</i>
                                    </div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 0.95rem; margin-bottom: 4px;">{r_stars} <span style="font-weight: 600; color: #f59e0b; font-size: 0.85rem;">({r_rating}/5)</span></div>
                                    <span style="{sent_badge_style} font-size: 0.75rem; padding: 3px 8px; border-radius: 6px; font-weight: 600; display: inline-block;">
                                        {sent_icon} Sentimen: {r_sent}
                                    </span>
                                </div>
                            </div>
                            {f'<div style="background-color: #0f172a; padding: 3px 8px; border-radius: 4px; display: inline-block; color: #cbd5e1; font-size: 0.75rem; margin-bottom: 8px;">📦 Varian: {r_var}</div>' if r_var else ''}
                            <div style="color: #e2e8f0; font-size: 0.9rem; line-height: 1.45; margin-top: 4px;">
                                "{r_text}"
                            </div>
                            {f'<div style="color: #94a3b8; font-size: 0.78rem; margin-top: 6px; font-style: italic;">📝 Catatan: {r_notes}</div>' if r_notes else ''}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Aksi Edit dan Hapus untuk Kartu Ini
                    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 4])
                    with btn_col1:
                        edit_expanded = st.session_state.get(f"edit_exp_{rev_id}", False)
                        if st.button("✏️ Edit", key=f"btn_edit_toggle_{rev_id}"):
                            st.session_state[f"edit_exp_{rev_id}"] = not edit_expanded
                            st.rerun()
                    with btn_col2:
                        del_confirm = st.session_state.get(f"del_confirm_{rev_id}", False)
                        if not del_confirm:
                            if st.button("🗑️ Hapus", key=f"btn_del_init_{rev_id}"):
                                st.session_state[f"del_confirm_{rev_id}"] = True
                                st.rerun()
                        else:
                            if st.button("⚠️ Yakin Hapus?", key=f"btn_del_exec_{rev_id}", type="primary"):
                                ok, msg = delete_review(rev_id)
                                st.session_state[f"del_confirm_{rev_id}"] = False
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                    with btn_col3:
                        if st.session_state.get(f"del_confirm_{rev_id}", False):
                            if st.button("Batal", key=f"btn_del_cancel_{rev_id}"):
                                st.session_state[f"del_confirm_{rev_id}"] = False
                                st.rerun()

                    # FORM EDIT MODAL / EXPANDER
                    if st.session_state.get(f"edit_exp_{rev_id}", False):
                        with st.expander(f"⚙️ Form Edit Ulasan #{rev_id}", expanded=True):
                            with st.form(key=f"form_edit_{rev_id}"):
                                e_name = st.text_input("Nama Pembeli:", value=r_name)
                                e_col1, e_col2 = st.columns(2)
                                with e_col1:
                                    e_date = st.text_input("Tanggal (YYYY-MM-DD):", value=r_date)
                                    e_rating = st.number_input("Rating Bintang:", min_value=1, max_value=5, value=r_rating, step=1)
                                with e_col2:
                                    e_var = st.text_input("Varian Produk:", value=r_var)
                                    e_ver = st.checkbox("Pembelian Terverifikasi", value=r_ver)
                                
                                e_text = st.text_area("Isi Komentar / Ulasan Pembeli:", value=r_text, height=90)
                                e_sent = st.selectbox("Koreksi Label Sentimen:", ["Positif", "Netral", "Negatif"], index=["Positif", "Netral", "Negatif"].index(r_sent) if r_sent in ["Positif", "Netral", "Negatif"] else 1)
                                e_notes = st.text_input("Catatan Tambahan:", value=r_notes)

                                e_submit = st.form_submit_button("💾 Simpan Perubahan Ulasan", type="primary")
                                if e_submit:
                                    ok, msg = update_review(
                                        review_pk=rev_id,
                                        reviewer_name=e_name,
                                        review_date=e_date,
                                        rating=int(e_rating),
                                        review_text=e_text,
                                        product_variant=e_var,
                                        verified_purchase=e_ver,
                                        sentiment=e_sent,
                                        notes=e_notes
                                    )
                                    if ok:
                                        st.success(msg)
                                        st.session_state[f"edit_exp_{rev_id}"] = False
                                        st.rerun()
                                    else:
                                        st.error(msg)

        # Tombol Bersihkan Seluruh Ulasan (Safety Reset)
        if total_stored > 0:
            st.markdown("---")
            with st.expander("⚠️ Opsi Lanjutan / Bersihkan Database Ulasan", expanded=False):
                st.warning("Tindakan ini akan menghapus seluruh data ulasan pembeli Shopee yang tersimpan di database.")
                if st.button("Hapus Seluruh Ulasan Shopee", key="btn_clear_all_shopee"):
                    ok, msg = clear_all_reviews()
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    # =========================================================================
    # TAB 2: TAMBAH ULASAN MANUAL
    # =========================================================================
    with tab_add:
        st.markdown("##### 📝 Formulir Input Ulasan Pembeli Shopee")
        st.caption("Masukkan data ulasan pembeli secara manual. Sentimen akan diprediksi otomatis dan dapat disesuaikan.")

        with st.form("form_add_shopee_review"):
            m_anon = st.checkbox("Gunakan identitas anonim / default", value=False)
            m_name = st.text_input("Nama Pembeli / Akun Shopee:", value="" if not m_anon else "Pengguna Shopee", placeholder="Contoh: Rina Kusuma atau a*****9")
            
            c_m1, c_m2 = st.columns(2)
            with c_m1:
                m_date = st.date_input("Tanggal Ulasan Dibuat:", value=date.today())
                m_rating = st.slider("Rating Bintang (1–5):", min_value=1, max_value=5, value=5, step=1, help="Pilih 1 (Sangat Buruk) hingga 5 (Sangat Puas)")
            with c_m2:
                m_variant = st.text_input("Varian Produk (Opsional):", placeholder="Contoh: 250ml Botol, Warna Hijau, Ukuran L")
                m_verified = st.checkbox("Status Pembelian Terverifikasi (Verified Purchase)", value=True, help="Menandakan transaksi telah sukses diselesaikan di Shopee")

            m_text = st.text_area("Isi Komentar / Ulasan Pembeli (Wajib):", placeholder="Tuliskan pengalaman ulasan pembeli mengenai kualitas produk, rasa, kemasan, atau pelayanan...", height=100)
            
            # Pilihan Sentimen (Otomatis atau Manual)
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                m_sent_mode = st.radio("Metode Penentuan Sentimen:", ["Prediksi Otomatis (Rekomendasi)", "Pilih Manual"], horizontal=True)
            with c_s2:
                m_manual_sent = st.selectbox("Label Sentimen Manual:", ["Positif", "Netral", "Negatif"]) if m_sent_mode == "Pilih Manual" else None

            m_notes = st.text_input("Catatan Tambahan (Opsional):", placeholder="Contoh: Ditinjau untuk sampel laporan Tugas Akhir")

            submit_manual = st.form_submit_button("🚀 Simpan Ulasan ke Database", type="primary", use_container_width=True)

            if submit_manual:
                final_name = "Pengguna Shopee" if (m_anon or not m_name.strip()) else m_name.strip()
                ok, msg, new_id = add_review(
                    reviewer_name=final_name,
                    review_date=m_date.strftime("%Y-%m-%d"),
                    rating=int(m_rating),
                    review_text=m_text,
                    product_variant=m_variant,
                    verified_purchase=m_verified,
                    source="Input Manual",
                    sentiment_override=m_manual_sent,
                    notes=m_notes,
                    product_name=product_title
                )
                if ok:
                    st.success(f"✅ {msg} (ID Ulasan: #{new_id})")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

    # =========================================================================
    # TAB 3: IMPOR DARI FILE CSV / EXCEL
    # =========================================================================
    with tab_import:
        st.markdown("##### 📥 Impor Ulasan Masal dari File CSV / Excel")
        st.caption("Unggah data ulasan hasil ekspor Shopee Seller Center atau file dataset (.csv, .xlsx, .xls).")

        # Tombol Download Template CSV
        c_tpl1, c_tpl2 = st.columns([3, 1])
        with c_tpl1:
            st.info("💡 Belum memiliki format file? Unduh template CSV resmi berikut yang siap diisi:")
        with c_tpl2:
            st.download_button(
                label="📄 Unduh Template CSV",
                data=generate_csv_template(),
                file_name="template_ulasan_shopee.csv",
                mime="text/csv",
                use_container_width=True
            )

        uploaded_file = st.file_uploader(
            "Pilih File Ulasan (.csv, .xlsx, .xls):",
            type=["csv", "xlsx", "xls"],
            key="shopee_file_uploader"
        )

        if uploaded_file is not None:
            df_preview, status_msg = parse_uploaded_file(uploaded_file, uploaded_file.name)
            
            if df_preview is None:
                st.error(f"❌ {status_msg}")
            else:
                st.success(f"✅ File berhasil dibaca: **{len(df_preview)}** baris ditemukan.")
                
                # Pratinjau 5 Baris Pertama
                st.markdown("###### Pratinjau 5 Baris Data Teratas:")
                st.dataframe(df_preview.head(5), use_container_width=True)

                # Deteksi dan Pemetaan Kolom Fleksibel
                st.markdown("###### 🔄 Pemetaan Kolom File ke Kolom Aplikasi:")
                auto_map = detect_column_mappings(df_preview)
                all_cols = ["(Tidak Ada / Abaikan)"] + list(df_preview.columns)

                def get_col_index(target_key: str) -> int:
                    matched = auto_map.get(target_key)
                    if matched and matched in all_cols:
                        return all_cols.index(matched)
                    return 0

                c_m1, c_m2 = st.columns(2)
                with c_m1:
                    m_text_col = st.selectbox("Kolom Isi Ulasan / Komentar (Wajib):", all_cols, index=get_col_index("review_text"))
                    m_rating_col = st.selectbox("Kolom Rating Bintang (1-5):", all_cols, index=get_col_index("rating"))
                    m_reviewer_col = st.selectbox("Kolom Nama Pembeli:", all_cols, index=get_col_index("reviewer_name"))
                    m_date_col = st.selectbox("Kolom Tanggal Ulasan:", all_cols, index=get_col_index("review_date"))
                with c_m2:
                    m_variant_col = st.selectbox("Kolom Varian Produk:", all_cols, index=get_col_index("product_variant"))
                    m_verified_col = st.selectbox("Kolom Status Verifikasi:", all_cols, index=get_col_index("verified_purchase"))
                    m_sentiment_col = st.selectbox("Kolom Label Sentimen (Opsional):", all_cols, index=get_col_index("sentiment"))
                    m_id_col = st.selectbox("Kolom Review ID (Shopee ID):", all_cols, index=get_col_index("review_id"))

                final_mapping = {
                    "review_text": m_text_col if m_text_col != "(Tidak Ada / Abaikan)" else None,
                    "rating": m_rating_col if m_rating_col != "(Tidak Ada / Abaikan)" else None,
                    "reviewer_name": m_reviewer_col if m_reviewer_col != "(Tidak Ada / Abaikan)" else None,
                    "review_date": m_date_col if m_date_col != "(Tidak Ada / Abaikan)" else None,
                    "product_variant": m_variant_col if m_variant_col != "(Tidak Ada / Abaikan)" else None,
                    "verified_purchase": m_verified_col if m_verified_col != "(Tidak Ada / Abaikan)" else None,
                    "sentiment": m_sentiment_col if m_sentiment_col != "(Tidak Ada / Abaikan)" else None,
                    "review_id": m_id_col if m_id_col != "(Tidak Ada / Abaikan)" else None,
                }

                if st.button("🚀 Jalankan Impor Data ke Database", type="primary", use_container_width=True):
                    if not final_mapping["review_text"]:
                        st.error("❌ Kolom 'Isi Ulasan / Komentar' wajib dipilih!")
                    else:
                        with st.spinner("Mengimpor dan menganalisis ulasan pembeli..."):
                            res = import_reviews_from_dataframe(
                                df=df_preview,
                                column_mapping=final_mapping,
                                source_name=f"Impor ({uploaded_file.name})"
                            )
                        
                        if res["success"]:
                            st.success(res["message"])
                            c_r1, c_r2, c_r3 = st.columns(3)
                            with c_r1:
                                st.metric("Berhasil Diimpor", f"{res['imported']}")
                            with c_r2:
                                st.metric("Duplikat Diabaikan", f"{res['duplicates']}")
                            with c_r3:
                                st.metric("Ditolak / Error", f"{res['rejected']}")

                            if res["errors"]:
                                with st.expander("Lihat Detail Baris yang Bermasalah", expanded=False):
                                    for err in res["errors"]:
                                        st.caption(f"⚠️ {err}")
                            st.rerun()
                        else:
                            st.error(f"❌ {res['message']}")

    # =========================================================================
    # TAB 4: KETERANGAN & KEBIJAKAN SHOPEE
    # =========================================================================
    with tab_policy:
        st.markdown("##### 🛡️ Kepatuhan & Kebijakan Data Shopee")
        st.markdown(
            """
            1. **Metode Akuisisi Data yang Sah & Etis (Shopee Terms of Service):**
               - Fitur ini dirancang khusus untuk mematuhi ketentuan layanan resmi. Aplikasi tidak menggunakan bot web scraper ilegal yang melewati autentikasi atau melanggar *Shopee Terms of Service*.
               - Data ulasan dimasukkan secara sah melalui:
                 - **Input Manual** oleh peneliti / pemilik UMKM.
                 - **Impor File CSV / Excel** yang diunduh langsung dari menu *Shopee Seller Center* (*Pesanan > Penilaian Toko / Komentar Produk*).
            
            2. **Status Integrasi Shopee Open Platform:**
               - API resmi Shopee Open Platform memerlukan pendaftaran *Shopee Partner App* terverifikasi dengan kredensial `partner_id` dan `partner_key`.
               - Sesuai arsitektur Tugas Akhir saat ini, alur kerja utama menggunakan integrasi berkas lokal (CSV/Excel) yang bersifat offline-first, cepat, dan 100% aman tanpa risiko suspensi akun.
            
            3. **Indikator Sentimen Otomatis:**
               - Sentimen diidentifikasi menggunakan model berbasis aturan leksikon bahasa Indonesia yang diselaraskan dengan rating bintang pembeli.
               - Hasil otomatis dapat ditinjau dan dikoreksi sewaktu-waktu oleh pengguna melalui tombol **Edit** pada kartu ulasan.
            """
        )
