"""
ocr_engine.py
=============
Modul OCR & Analisis Cerdas untuk Karakteristik Postingan UMKM & Engagement.
Mendukung:
  1. EasyOCR (offline engine)
  2. Deteksi Screenshot Profil Instagram (Username, Display Name, Followers 575K, Bio)
  3. Deteksi Screenshot Post Feed (Likes, Komentar, Caption)
  4. Deteksi Foto Promosi / Banner Makanan & UMKM (Brand tanpa @, Menu, Paket)
  5. Pencocokan Otomatis dengan Profil UMKM yang Tersimpan di Database
  6. Estimasi Realistis Metrik Engagement Sesuai Skala Followers Akun
"""

import re
import hashlib
import numpy as np
from PIL import Image
import database as db

# Cache reader agar tidak reload tiap kali
_reader_cache = {}


def _get_reader():
    """Inisialisasi EasyOCR reader (lazy, cache per proses)."""
    key = "id_en"
    if key not in _reader_cache:
        import easyocr  # noqa: import di sini
        _reader_cache[key] = easyocr.Reader(
            ["id", "en"],
            gpu=False,
            verbose=False,
            download_enabled=True,
        )
    return _reader_cache[key]


# ─────────────────────────────────────────────────────────────
# 1.  EKSTRAKSI TEKS DARI GAMBAR
# ─────────────────────────────────────────────────────────────

def extract_text(pil_image: Image.Image) -> dict:
    """Jalankan OCR pada pil_image."""
    try:
        reader = _get_reader()
        img_array = np.array(pil_image.convert("RGB"))
        raw = reader.readtext(img_array, detail=1, paragraph=False)

        # Filter confidence rendah
        texts = [r[1].strip() for r in raw if r[2] >= 0.20 and r[1].strip()]

        full_text = "\n".join(texts)
        return {"status": "success", "texts": texts, "full_text": full_text}

    except ImportError:
        return {
            "status": "error",
            "message": "EasyOCR belum terinstall.",
            "texts": [],
            "full_text": "",
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": f"OCR gagal: {exc}",
            "texts": [],
            "full_text": "",
        }


# ─────────────────────────────────────────────────────────────
# 2.  PARSING ANGKA (MENDUKUNG 575K, 1.2M, 3.191, DLL)
# ─────────────────────────────────────────────────────────────

def _parse_number(text: str) -> int:
    """Ubah teks angka (mis. '575K', '1.2M', '3.500', '12,3 rb') ke int."""
    text = text.strip().lower()
    
    # 575K / 1.2M / 12rb
    if "rb" in text or "k" in text:
        clean = re.sub(r"[^\d.,]", "", text).replace(",", ".")
        try:
            return int(float(clean) * 1000)
        except ValueError:
            return 0
    if "jt" in text or "m" in text:
        clean = re.sub(r"[^\d.,]", "", text).replace(",", ".")
        try:
            return int(float(clean) * 1_000_000)
        except ValueError:
            return 0

    # Angka ribuan dengan format '3.191' atau '12.500'
    if re.match(r"^\d{1,3}\.\d{3}$", text):
        clean = text.replace(".", "")
        try:
            return int(clean)
        except ValueError:
            pass

    clean = re.sub(r"[^\d]", "", text)
    try:
        return int(clean)
    except ValueError:
        return 0


def _search_num(patterns: list, combined: str) -> int:
    """Cari angka pertama yang cocok dengan salah satu pola regex."""
    for pat in patterns:
        m = re.search(pat, combined, re.IGNORECASE)
        if m:
            val = _parse_number(m.group(1))
            if val > 0:
                return val
    return 0


# ─────────────────────────────────────────────────────────────
# 3.  DETEKSI PROFIL INSTAGRAM (SEPERTI GAMBAR KE-3)
# ─────────────────────────────────────────────────────────────

def _detect_instagram_profile(texts: list) -> dict | None:
    """
    Mendeteksi apakah gambar adalah screenshot profil Instagram.
    Contoh: 'basoaciakang', 'Baso Aci Akang', '2,970 posts', '575K followers', '16 following'
    """
    combined = " ".join(texts)

    # Indikator kuat header profil Instagram
    has_posts = bool(re.search(r"\b\d+[\d.,]*\s*(posts|postingan)\b", combined, re.I))
    has_followers = bool(re.search(r"\b\d+[\d.,]*(?:k|m|rb|jt)?\s*(followers|pengikut)\b", combined, re.I))

    if not (has_posts or has_followers):
        return None

    # Ekstraksi followers
    fol_match = re.search(r"(\d+[\d.,]*(?:k|m|rb|jt)?)\s*(?:followers|pengikut)", combined, re.I)
    followers = _parse_number(fol_match.group(1)) if fol_match else 0

    # Ekstraksi username & display name
    # Di profil IG, baris 0 biasanya username, baris 1 nama tampilan
    username = ""
    display_name = ""

    for i, t in enumerate(texts[:5]):
        t_clean = t.strip()
        if re.search(r"\b(posts|followers|following|pengikut|mengikuti)\b", t_clean, re.I):
            continue
        if not username:
            username = t_clean.replace("@", "")
        elif not display_name:
            display_name = t_clean

    # Brand formatting
    if display_name and display_name.lower() != username.lower():
        brand = f"{display_name} (@{username})"
    elif username:
        brand = f"@{username}"
    else:
        brand = "UMKM Instagram"

    # Bio / Caption
    bio_candidates = []
    for t in texts:
        tc = t.strip()
        if not re.search(r"\b(posts|followers|following|pengikut|mengikuti|product/service|followed by)\b", tc, re.I):
            if len(tc) > 8 and not re.fullmatch(r"[\d.,\s:~]+", tc):
                bio_candidates.append(tc)

    bio = " | ".join(bio_candidates[:5])

    return {
        "is_profile": True,
        "umkm_name": brand,
        "username": username,
        "title": f"Profil Resmi {display_name or username} (@{username})",
        "followers": followers,
        "caption": bio or f"Profil Instagram resmi @{username}",
        "platform": "Instagram",
    }


# ─────────────────────────────────────────────────────────────
# 4.  EKSTRAKSI BRAND DARI POSTINGAN PROMOSI / KULINER
# ─────────────────────────────────────────────────────────────

def _extract_brand_from_promo(texts: list) -> str:
    """Mendeteksi nama brand UMKM dari teks promo/poster (mis. 'Basoaci AKANG', 'Pentol Gila')."""
    combined = " ".join(texts)

    # 1. Cari @username jika ada
    usernames = re.findall(r"@([A-Za-z0-9_.]{3,30})", combined)
    if usernames:
        return f"@{usernames[0]}"

    # 2. Cari kombinasi kata Brand F&B / UMKM khas Indonesia
    # Contoh: 'Basoaci AKANG', 'Bakso Akang', 'Mie Gacoan', 'Kopi Senja', dll.
    for t in texts:
        m = re.search(
            r"\b(baso\s*aci|basoaci|bakso|mie|ayam|bebek|kopi|teh|dapur|kedai|warung|cafe|seblak|pentol|pontol|snack|hijab|butik)\s+([A-Za-z0-9_]{3,20})\b",
            t, re.IGNORECASE
        )
        if m:
            category = m.group(1).title()
            name = m.group(2).title()
            return f"{category} {name}"

    # 3. Cari kata berhuruf kapital kuat yang merupakan nama brand (mis. 'AKANG', 'PENTOL GILA')
    for t in texts:
        words = t.strip().split()
        if 1 <= len(words) <= 3:
            for w in words:
                if w.isupper() and len(w) >= 4 and not re.search(r"\b(PROMO|DISKON|PAKET|MENU|HARI|SENIN|MINGGU|GRATIS)\b", w):
                    return w.title()

    # 4. Cek domain website
    dom_match = re.search(r"www\s*[\.\s]*([A-Za-z0-9_-]+)\s*[\.\s]*(id|com|co\.id)", combined, re.IGNORECASE)
    if dom_match:
        return dom_match.group(1).replace("-", " ").title()

    return ""


# ─────────────────────────────────────────────────────────────
# 5.  EKSTRAKSI JUDUL POSTINGAN YANG BERMAKNA
# ─────────────────────────────────────────────────────────────

def _extract_meaningful_title(texts: list, brand: str) -> str:
    """Menghasilkan judul postingan yang informatif, menghindari judul 1 kata seperti 'Paket'."""
    clean_brand = brand.split("(")[0].strip().replace("@", "")

    # Cari kalimat promo terkuat (panjang > 6 karakter, mengandung kata kunci)
    candidates = []
    for t in texts:
        tc = t.strip()
        if len(tc) < 6:
            continue
        if re.search(r"\b(promo|diskon|paket|menu|spesial|jajan|beli|hemat|baru|ramadhan|cashback)\b", tc, re.I):
            candidates.append(tc)

    if candidates:
        # Pilih kalimat promo terpanjang / paling informatif
        chosen = max(candidates[:3], key=len)
        if clean_brand and clean_brand.lower() not in chosen.lower():
            return f"{chosen.title()} - {clean_brand}"
        return chosen.title()

    # Jika tidak ada kalimat promo, gunakan nama brand + produk
    if clean_brand and clean_brand != "Umkm Unggulan":
        return f"Promosi Menu {clean_brand}"

    return "Postingan Promosi Produk UMKM"


# ─────────────────────────────────────────────────────────────
# 6.  ESTIMASI CERDAS METRIK ENGAGEMENT SESUAI SKALA FOLLOWERS
# ─────────────────────────────────────────────────────────────

def estimate_engagement_for_followers(followers: int, cv_feats: dict | None = None) -> dict:
    """
    Menghitung estimasi realistis likes, comments, shares, saves
    berdasarkan skala followers akun.

    Rasio Engagement Rate Berdasarkan Skala Akun Instagram:
      - Akun Mikro (<10k followers): ER 4.0% – 7.5%
      - Akun Mid-Tier (10k - 100k): ER 2.5% – 4.5%
      - Akun Makro (>100k, misal 575k): ER 1.2% – 2.8%
    """
    if followers <= 0:
        followers = 5000

    # Tentukan base ER sesuai skala akun
    if followers > 200_000:
        base_er = 0.018  # Akun besar seperti Baso Aci Akang (575k) -> ~1.8% ER
    elif followers > 50_000:
        base_er = 0.028
    elif followers > 10_000:
        base_er = 0.038
    else:
        base_er = 0.048  # Akun mikro UMKM -> ~4.8% ER

    # Pengaruh Computer Vision
    cv_multiplier = 1.0
    if cv_feats:
        if 110 <= cv_feats.get("brightness", 150) <= 210:
            cv_multiplier += 0.08
        if cv_feats.get("contrast", 50) >= 45:
            cv_multiplier += 0.08
        if cv_feats.get("face_detected", 0) == 1:
            cv_multiplier += 0.12

    er = base_er * cv_multiplier
    total_interactions = int(followers * er)

    likes = max(int(total_interactions * 0.88), 10)
    comments = max(int(total_interactions * 0.06), 2)
    shares = max(int(total_interactions * 0.03), 1)
    saves = max(int(total_interactions * 0.03), 1)

    return {
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "saves": saves,
        "is_estimated": True,
    }


def _detect_shopee_product(texts: list, full_text: str = "") -> dict | None:
    """
    Mendeteksi apakah gambar/screenshot berasal dari aplikasi atau web Shopee.
    Mengekstrak nama toko, judul produk, harga, ulasan (comments), favorit (likes), dan pengikut toko.
    """
    combined = (full_text + " " + " ".join(texts)).lower()

    # Indikator kata kunci antarmuka Shopee
    shopee_kw = [
        "shopee", "terjual", "penilaian", "kunjungi toko", "garansi shopee",
        "beli sekarang", "masukkan keranjang", "gratis ongkir", "star+",
        "shopee mall", "shopeepay", "cod-cek dulu", "koin shopee"
    ]
    matches = sum(1 for kw in shopee_kw if kw in combined)
    if matches < 2 and "shopee" not in combined:
        return None

    # 1. Ekstraksi Likes / Favorit Produk (❤️)
    likes_m = (re.search(r"(\d+[\d.,]*(?:k|m|rb|jt)?)\s*(?:favorit|disukai|suka)", combined, re.I)
               or re.search(r"favorit\s*\(?(\d+[\d.,]*(?:k|m|rb|jt)?)\)?", combined, re.I)
               or re.search(r"[❤️❤]\s*([\d.,]+(?:k|m|rb|jt)?)", combined, re.I))
    real_likes = _parse_number(likes_m.group(1)) if likes_m else 0

    # 2. Ekstraksi Comments / Penilaian / Ulasan (⭐)
    comments_m = (re.search(r"(\d+[\d.,]*(?:k|m|rb|jt)?)\s*(?:penilaian|ulasan|review)", combined, re.I)
                  or re.search(r"penilaian\s*\(?(\d+[\d.,]*(?:k|m|rb|jt)?)\)?", combined, re.I))
    real_comments = _parse_number(comments_m.group(1)) if comments_m else 0

    # 3. Ekstraksi Terjual (Sales)
    sold_m = re.search(r"(\d+[\d.,]*(?:k|m|rb|jt)?)\s*(?:terjual|sold)", combined, re.I)
    sold_count = _parse_number(sold_m.group(1)) if sold_m else 0

    # 4. Ekstraksi Followers / Pengikut Toko
    fol_m = (re.search(r"(\d+[\d.,]*(?:k|m|rb|jt)?)\s*(?:pengikut|followers)", combined, re.I)
             or re.search(r"pengikut\s*[:\-]?\s*(\d+[\d.,]*(?:k|m|rb|jt)?)", combined, re.I))
    real_followers = _parse_number(fol_m.group(1)) if fol_m else 0

    # 5. Ekstraksi Harga
    price_m = re.search(r"(?:rp\.?|idr)\s*([\d.,]+)", combined, re.I)
    price = f"Rp {price_m.group(1)}" if price_m else ""

    # 6. Ekstraksi Nama Toko & Produk
    shop_name = "Toko Shopee"
    title_candidates = []
    for i, t in enumerate(texts):
        tc = t.strip()
        if re.search(r"\b(official store|official shop)\b", tc, re.I) and len(tc) >= 4:
            shop_name = tc
        elif shop_name == "Toko Shopee" and re.search(r"\b(kunjungi toko|chat penjual|ikuti)\b", tc, re.I) and i > 0:
            for prev_idx in range(i - 1, -1, -1):
                prev_cand = texts[prev_idx].strip()
                if not re.search(r"(favorit|terjual|penilaian|ulasan|bintang|rating|\d+k|\d+rb|rp|^[\d.,]+$)", prev_cand, re.I) and len(prev_cand) > 2:
                    shop_name = prev_cand
                    break
        elif len(tc) > 15 and not re.search(r"(garansi|ongkir|gratis|cashback|voucher|cicilan|metode|bayar)", tc, re.I):
            title_candidates.append(tc)

    title = max(title_candidates[:3], key=len) if title_candidates else "Produk Shopee"

    # Fallback estimasi jika sebagian angka tidak tertangkap di screenshot
    is_estimated = False
    if real_followers == 0:
        real_followers = 35000 if "mall" in combined else 6500
        is_estimated = True
    if real_likes == 0:
        if sold_count > 0:
            real_likes = max(int(sold_count * 0.35), 45)
        else:
            real_likes = max(int(real_followers * 0.04), 50)
        is_estimated = True
    if real_comments == 0:
        real_comments = max(int(real_likes * 0.18), 8)
        is_estimated = True

    real_shares = max(int(real_likes * 0.05), 3)
    real_saves = sold_count if sold_count > 0 else max(int(real_likes * 0.22), 12)

    # Caption deskriptif
    caption_lines = [t.strip() for t in texts if len(t.strip()) > 6 and not re.fullmatch(r"[\d.,\s%]+", t.strip())]
    caption = " ".join(caption_lines[:8]) if caption_lines else f"Produk {title} dari toko {shop_name}"
    if price and "harga" not in caption.lower():
        caption = f"Harga: {price} | {caption}"

    # 7. Ekstraksi Rating Produk (⭐ 1.0 - 5.0)
    rating_m = (re.search(r"\b([1-5][.,]\d)\b", combined)
                or re.search(r"rating\s*[:\-]?\s*([1-5][.,]\d)", combined, re.I)
                or re.search(r"([1-5][.,]\d)\s*(?:/5|bintang|penilaian)", combined, re.I))
    if rating_m:
        try:
            real_rating = float(rating_m.group(1).replace(",", "."))
            real_rating = min(max(real_rating, 1.0), 5.0)
        except ValueError:
            real_rating = 4.8
    else:
        real_rating = 4.8

    return {
        "umkm_name": shop_name,
        "title": title,
        "caption": caption,
        "followers": real_followers,
        "likes": real_likes,
        "comments": real_comments,
        "shares": real_shares,
        "saves": real_saves,
        "rating": real_rating,
        "platform": "Shopee",
        "price": price,
        "is_estimated": is_estimated,
    }


# ─────────────────────────────────────────────────────────────
# 7.  FUNGSI UTAMA: PARSE POST DATA
# ─────────────────────────────────────────────────────────────

def parse_post_data(full_text: str, texts: list, cv_feats: dict | None = None) -> dict:
    """
    Parsing cerdas yang mendeteksi:
      1. Screenshot Halaman Produk Shopee (Favorit, Penilaian, Terjual, dll)
      2. Screenshot Profil Instagram (Followers 575K, Username, dll)
      3. Screenshot Post Feed Instagram (Likes, Komentar riil)
      4. Foto Promosi / Menu (Brand terdeteksi, Followers dicocokkan dengan DB)
    """
    combined = " ".join(texts)

    # ── KASUS 1: GAMBAR ADALAH SCREENSHOT PRODUK SHOPEE ─────────
    shopee_data = _detect_shopee_product(texts, full_text)
    if shopee_data:
        return shopee_data

    # ── KASUS 2: GAMBAR ADALAH SCREENSHOT PROFIL INSTAGRAM ──────
    prof = _detect_instagram_profile(texts)
    if prof:
        # Hitung likes/komentar rata-rata per postingan untuk akun sebesar ini
        eng = estimate_engagement_for_followers(prof["followers"], cv_feats)
        return {
            "umkm_name": prof["umkm_name"],
            "title": prof["title"],
            "caption": prof["caption"],
            "followers": prof["followers"],
            "likes": eng["likes"],
            "comments": eng["comments"],
            "shares": eng["shares"],
            "saves": eng["saves"],
            "platform": "Instagram",
            "is_estimated": True,
        }

    # ── KASUS 2: GAMBAR ADALAH POST FEED / FOTO PROMOSI ─────────
    # 1. Ekstraksi Brand
    brand = _extract_brand_from_promo(texts)
    if not brand:
        brand = "UMKM Unggulan"

    # 2. Ekstraksi Judul yang bermakna
    title = _extract_meaningful_title(texts, brand)

    # 3. Ekstraksi Likes dari teks jika ada screenshot post
    liked_by_match = re.search(r"disukai\s+oleh\s+[\w.]+\s+dan\s+([\d.,]+)\s+lainnya", combined, re.I)
    real_likes = (_parse_number(liked_by_match.group(1)) + 1) if liked_by_match else 0
    if real_likes == 0:
        real_likes = _search_num([
            r"([\d.,]+\s*(?:rb|k|jt|m)?)\s*(?:suka|like[s]?|❤|♥|👍)",
            r"(?:suka|like[s]?|❤|♥|👍)\s*[:\-]?\s*([\d.,]+\s*(?:rb|k|jt|m)?)",
        ], combined)

    # 4. Ekstraksi Komentar dari teks
    real_comments = _search_num([
        r"lihat\s+semua\s+([\d.,]+)\s+komentar",
        r"([\d.,]+\s*(?:rb|k|jt|m)?)\s*(?:komentar|comment[s]?)",
    ], combined)

    # 5. Ekstraksi Followers langsung dari gambar jika tertera
    real_followers = _search_num([
        r"([\d.,]+\s*(?:rb|k|jt|m)?)\s*(?:followers|pengikut)",
    ], combined)

    # 6. JIKA FOLLOWERS TIDAK ADA DI GAMBAR:
    # Cek apakah brand ini sudah tersimpan di database TA kita!
    if real_followers == 0 and brand and brand != "UMKM Unggulan":
        known_followers = db.find_known_brand_followers(brand)
        if known_followers > 0:
            real_followers = known_followers

    # Jika masih belum ada, estimasi basis followers UMKM
    is_estimated = False
    if real_followers == 0:
        seed_str = f"{brand}_{title}".lower()
        hash_val = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
        real_followers = 3500 + (hash_val % 4500)
        is_estimated = True

    # 7. Likes & Komentar
    if real_likes == 0:
        eng = estimate_engagement_for_followers(real_followers, cv_feats)
        real_likes = eng["likes"]
        real_comments = eng["comments"]
        real_shares = eng["shares"]
        real_saves = eng["saves"]
        is_estimated = True
    else:
        real_shares = max(int(real_likes * 0.04), 1)
        real_saves = max(int(real_likes * 0.08), 2)

    # 8. Caption
    caption_lines = [t.strip() for t in texts if len(t.strip()) > 5 and not re.fullmatch(r"[\d.,\s%]+", t.strip())]
    caption = " ".join(caption_lines[:8]) if caption_lines else full_text.replace("\n", " ").strip()

    return {
        "umkm_name": brand,
        "title": title,
        "caption": caption,
        "followers": real_followers,
        "likes": real_likes,
        "comments": real_comments,
        "shares": real_shares,
        "saves": real_saves,
        "platform": "Instagram",
        "is_estimated": is_estimated,
    }
