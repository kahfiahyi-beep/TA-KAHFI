"""
scraper_engine.py
=================
Modul Pengumpulan Metadata Postingan Instagram untuk Dataset Skripsi.
Mendukung:
1. Pengumpulan metadata via link/shortcode postingan secara mandiri (tanpa login).
2. Pengumpulan postingan dari profil akun UMKM menggunakan Instaloader (dengan session atau profil publik).
3. Pengunduhan citra resolusi tinggi secara sah ke direktori lokal untuk audit visual.
4. Jeda waktu acak (rate limiting) dan mekanisme penghentian ramah saat terkena limit.
"""

import os
import re
import time
import random
import json
import logging
from datetime import datetime, timezone, timedelta
import requests
from PIL import Image
import io

import instaloader
import database_manager as dbm
import sampling_filter as sf

# Inisialisasi Logger
LOG_FILE = os.path.join(os.path.dirname(__file__), "scraper_process.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("InstagramScraper")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}

def extract_shortcode_from_url(url: str) -> str | None:
    """Ekstraksi kode shortcode unik dari link postingan Instagram."""
    if not url:
        return None
    clean = url.split("?")[0].rstrip("/")
    m = re.search(r"instagram\.com/(?:p|reel|reels|tv)/([^/?#&]+)", clean)
    if m:
        return m.group(1)
    # Jika url hanya berupa shortcode itu sendiri
    if re.match(r"^[A-Za-z0-9_-]{10,13}$", url.strip()):
        return url.strip()
    return None

def download_and_save_image(image_url: str, shortcode: str, target_folder: str = "dataset_images") -> tuple[str | None, str]:
    """
    Mengunduh gambar postingan dan menyimpannya di direktori lokal untuk verifikasi visual.
    Mengembalikan (lokasi_file_lokal, status_ketersediaan).
    """
    if not image_url:
        return None, "Tidak Tersedia"

    abs_folder = os.path.join(os.path.dirname(__file__), target_folder)
    os.makedirs(abs_folder, exist_ok=True)
    filename = f"{shortcode}.jpg"
    filepath = os.path.join(abs_folder, filename)

    # Jika file sudah pernah diunduh sebelumnya, gunakan yang sudah ada
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        return filepath, "Tersedia"

    try:
        resp = requests.get(image_url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            pil_img = Image.open(io.BytesIO(resp.content)).convert("RGB")
            pil_img.save(filepath, "JPEG", quality=92)
            return filepath, "Tersedia"
        else:
            logger.warning(f"Gagal mengunduh gambar {shortcode}, HTTP {resp.status_code}")
            return None, "Tidak Tersedia"
    except Exception as e:
        logger.error(f"Error download gambar {shortcode}: {e}")
        return None, "Tidak Tersedia"

def fetch_single_post(
    url_or_shortcode: str,
    username_fallback: str = "",
    nama_umkm: str = "",
    kategori_produk: str = "",
    config: dict | None = None,
    loader_instance: instaloader.Instaloader | None = None
) -> dict:
    """
    Mengambil metadata lengkap satu postingan Instagram.
    Metode 1: Instaloader Shortcode Query (Paling akurat & resolusi penuh).
    Metode 2: Embed Scraping Fallback jika metode 1 mengalami kendala koneksi.
    """
    cfg = config or sf.load_config()
    scraping_cfg = cfg.get("pengaturan_scraping", {})
    folder_gambar = scraping_cfg.get("folder_gambar", "dataset_images")
    simpan_lokal = scraping_cfg.get("simpan_gambar_lokal", True)

    shortcode = extract_shortcode_from_url(url_or_shortcode)
    if not shortcode:
        return {
            "status": "error",
            "message": f"Format URL/Shortcode Instagram tidak valid: {url_or_shortcode}"
        }

    link_postingan = f"https://www.instagram.com/p/{shortcode}/"
    waktu_ambil = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Inisialisasi Instaloader jika belum disediakan
    L = loader_instance or instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        max_connection_attempts=1,
        quiet=True
    )

    post_data = {
        "shortcode": shortcode,
        "link_postingan": link_postingan,
        "username_ig": username_fallback,
        "nama_umkm": nama_umkm,
        "kategori_produk": kategori_produk,
        "link_profil": f"https://www.instagram.com/{username_fallback}/" if username_fallback else "",
        "tanggal_publikasi": "",
        "caption": "",
        "jenis_media": "Foto",
        "tanggal_pengambilan_data": waktu_ambil,
        "lokasi_file_gambar": "",
        "link_gambar": "",
        "status_ketersediaan_gambar": "Tidak Tersedia",
        "jumlah_likes": None,
        "status_likes": "Tidak Tersedia",
        "jumlah_komentar": None,
        "status_komentar": "Tidak Tersedia",
        "jumlah_share": None, # Sesuai ketentuan, share private tidak ada di publik IG
        "status_share": "Tidak tersedia secara publik",
        "waktu_pengambilan_engagement": waktu_ambil,
        "metode_pengambilan_metrik": "Instaloader Shortcode Query"
    }

    # 1. COBA METODE UTAMA: Instaloader
    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        # Username pemilik postingan
        owner = post.owner_username or username_fallback
        post_data["username_ig"] = owner
        post_data["link_profil"] = f"https://www.instagram.com/{owner}/"
        if not post_data["nama_umkm"]:
            post_data["nama_umkm"] = owner

        # Tanggal publikasi (convert UTC ke lokal WIB / +7 jam)
        if post.date_utc:
            # Format lokal YYYY-MM-DD HH:MM:SS
            local_date = post.date_utc.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=7)))
            post_data["tanggal_publikasi"] = local_date.strftime("%Y-%m-%d %H:%M:%S")

        # Caption
        post_data["caption"] = post.caption or ""

        # Jenis media
        if post.is_video:
            post_data["jenis_media"] = "Video/Reels"
        elif post.typename == "GraphSidecar":
            post_data["jenis_media"] = "Carousel/Foto"
        else:
            post_data["jenis_media"] = "Foto"

        # Metrik Engagement: Likes & Komentar
        # Pada postingan dengan like disembunyikan oleh pemilik, post.likes bernilai None
        if post.likes is not None:
            post_data["jumlah_likes"] = int(post.likes)
            post_data["status_likes"] = "Tersedia"
        else:
            post_data["jumlah_likes"] = None
            post_data["status_likes"] = "Disembunyikan oleh pemilik akun"

        if post.comments is not None:
            post_data["jumlah_komentar"] = int(post.comments)
            post_data["status_komentar"] = "Tersedia"
        else:
            post_data["jumlah_komentar"] = None
            post_data["status_komentar"] = "Dinonaktifkan / Tidak Tersedia"

        # Link Gambar resolusi tinggi
        img_url = post.url
        post_data["link_gambar"] = img_url

        # Unduh gambar lokal jika diaktifkan
        if simpan_lokal and img_url:
            local_path, img_status = download_and_save_image(img_url, shortcode, folder_gambar)
            post_data["lokasi_file_gambar"] = local_path or ""
            post_data["status_ketersediaan_gambar"] = img_status
        else:
            post_data["status_ketersediaan_gambar"] = "Tersedia" if img_url else "Tidak Tersedia"

    except Exception as e_inst:
        logger.warning(f"Instaloader shortcode gagal untuk {shortcode}: {e_inst}. Mencoba Fallback Embed...")
        # 2. METODE CADANGAN: Instagram Embed Page
        embed_success = False
        try:
            embed_url = f"https://www.instagram.com/p/{shortcode}/embed/captioned/"
            resp = requests.get(embed_url, headers=HEADERS, timeout=12)
            if resp.status_code == 200:
                html = resp.text
                # Ekstraksi gambar dari CDN
                img_matches = re.findall(r'https?://[^\s"\'\\]+(?:cdninstagram|fbcdn)[^\s"\'\\]+', html)
                clean_img = None
                for m in img_matches:
                    clean = m.replace('\\u0026', '&').replace('\\/', '/')
                    if any(ext in clean.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']) and 'rsrc.php' not in clean:
                        clean_img = clean
                        break

                if clean_img:
                    post_data["link_gambar"] = clean_img
                    if simpan_lokal:
                        local_path, img_status = download_and_save_image(clean_img, shortcode, folder_gambar)
                        post_data["lokasi_file_gambar"] = local_path or ""
                        post_data["status_ketersediaan_gambar"] = img_status
                    else:
                        post_data["status_ketersediaan_gambar"] = "Tersedia"

                # Ekstraksi caption dari div class Caption
                cap_m = re.findall(r'class=\"Caption\"[^>]*>(.*?)</div>', html, re.DOTALL)
                if cap_m:
                    clean_cap = re.sub(r'<[^>]+>', '', cap_m[0]).strip()
                    post_data["caption"] = clean_cap

                post_data["metode_pengambilan_metrik"] = "Instagram Public Embed Fallback"
                embed_success = True
        except Exception as e_embed:
            logger.error(f"Fallback Embed juga gagal untuk {shortcode}: {e_embed}")

        if not embed_success and not post_data["link_gambar"]:
            return {
                "status": "error",
                "message": f"Gagal mengambil metadata postingan {shortcode}: {e_inst}"
            }

    # 3. PENYARINGAN OTOMATIS (PURPOSIVE SAMPLING EVALUATION)
    hasil_eval = sf.evaluasi_postingan(
        username=post_data["username_ig"],
        jenis_media=post_data["jenis_media"],
        tanggal_publikasi=post_data["tanggal_publikasi"],
        caption=post_data["caption"],
        status_gambar=post_data["status_ketersediaan_gambar"],
        likes=post_data["jumlah_likes"],
        comments=post_data["jumlah_komentar"],
        config=cfg
    )

    post_data["status_inklusi"] = hasil_eval["status_inklusi"]
    post_data["alasan_eksklusi"] = hasil_eval["alasan_eksklusi"]
    post_data["kriteria_belum_pasti"] = hasil_eval["kriteria_belum_pasti"]

    # 4. SIMPAN KE DATABASE
    post_id, action, id_dataset = dbm.save_or_update_post(post_data)
    post_data["id"] = post_id
    post_data["id_dataset"] = id_dataset
    post_data["db_action"] = action

    return {
        "status": "success",
        "data": post_data
    }

def process_batch_post_links(
    links_list: list[str],
    kategori_produk: str = "UMKM",
    delay_range: tuple[int, int] = (3, 6),
    progress_callback=None
) -> list[dict]:
    """
    Memproses daftar link/shortcode postingan secara sekuensial dengan jeda rate-limit.
    """
    dbm.init_db()
    cfg = sf.load_config()
    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        quiet=True
    )

    results = []
    total = len(links_list)

    for idx, raw_url in enumerate(links_list):
        url = raw_url.strip()
        if not url:
            continue

        logger.info(f"[{idx+1}/{total}] Memproses: {url}")
        res = fetch_single_post(
            url_or_shortcode=url,
            kategori_produk=kategori_produk,
            config=cfg,
            loader_instance=L
        )
        results.append(res)

        if progress_callback:
            progress_callback(idx + 1, total, res)

        # Jeda waktu antar postingan untuk mencegah blokir/HTTP 429
        if idx < total - 1:
            delay = random.uniform(delay_range[0], delay_range[1])
            logger.info(f"Jeda aman {delay:.1f} detik sebelum permintaan berikutnya...")
            time.sleep(delay)

    return results

def process_umkm_profile_posts(
    username: str,
    max_posts: int = 50,
    kategori_produk: str = "UMKM",
    session_file: str | None = None,
    delay_range: tuple[int, int] = (4, 8),
    progress_callback=None
) -> dict:
    """
    Mencoba mengumpulkan postingan dari profil username UMKM.
    Catatan Teknis: Jika Instagram membatasi akses tanpa login (HTTP 401),
    fungsi ini akan mencatat pesan edukatif dan menyarankan pengumpulan berbasis link.
    """
    dbm.init_db()
    cfg = sf.load_config()
    clean_user = username.replace("@", "").strip()

    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        quiet=True
    )

    if session_file and os.path.exists(session_file):
        try:
            L.load_session_from_file(clean_user, session_file)
            logger.info(f"Session login berhasil dimuat untuk @{clean_user}")
        except Exception as e:
            logger.warning(f"Gagal memuat session file: {e}")

    try:
        profile = instaloader.Profile.from_username(L.context, clean_user)
        logger.info(f"Berhasil mengakses profil @{clean_user} (Total media publik: {profile.mediacount})")

        collected = []
        count = 0

        for post in profile.get_posts():
            if count >= max_posts:
                break

            shortcode = post.shortcode
            url = f"https://www.instagram.com/p/{shortcode}/"
            res = fetch_single_post(
                url_or_shortcode=shortcode,
                username_fallback=clean_user,
                nama_umkm=profile.full_name or clean_user,
                kategori_produk=kategori_produk,
                config=cfg,
                loader_instance=L
            )
            collected.append(res)
            count += 1

            if progress_callback:
                progress_callback(count, max_posts, res)

            # Jeda waktu aman
            delay = random.uniform(delay_range[0], delay_range[1])
            time.sleep(delay)

        return {
            "status": "success",
            "username": clean_user,
            "total_collected": len(collected),
            "results": collected
        }

    except Exception as e:
        err_msg = str(e)
        logger.error(f"Gagal mengakses profil @{clean_user}: {err_msg}")
        return {
            "status": "error",
            "username": clean_user,
            "error_type": type(e).__name__,
            "message": (
                f"Instagram membatasi pembacaan daftar feed akun @{clean_user} secara langsung tanpa sesi login ({err_msg}). "
                "Solusi Direkomendasikan: Kumpulkan link postingan UMKM tersebut (buka browser atau copy link postingannya), "
                "lalu masukkan link ke menu 'Input Link Postingan' untuk ditarik metadatanya secara otomatis tanpa risiko blokir."
            )
        }
