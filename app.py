import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os
import io

import database as db
import vision_engine as ve
import multimodal_analyzer as ma
import statistics_module as sm
import url_fetcher as uf
import ocr_engine as ocr
import sampling_criteria as sc
import json
from datetime import datetime, date

# Set konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Analisis Visual Postingan UMKM - TA",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS: Hide Deploy Button, perbaiki posisi Tabs, & dukungan Dark/Light Mode
st.markdown("""
<style>
    /* 1. SEMBUNYIKAN TOMBOL DEPLOY & HEADER STREAMLIT DI POJOK ATAS */
    .stDeployButton,
    [data-testid="stDeployButton"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    header [data-testid="stToolbarActions"],
    #MainMenu,
    footer {
        display: none !important;
        visibility: hidden !important;
    }
    header {
        background: transparent !important;
        height: 0px !important;
        min-height: 0px !important;
    }

    /* 2. AREA KONTEN UTAMA LEGA & TIDAK MENUTUPI NAVIGASI */
    .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 3rem !important;
        max-width: 96% !important;
    }

    /* 3. PERBAIKAN NAVIGASI TAB UTAMA & SUB-TAB (TIDAK TERPOTONG!) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background-color: transparent !important;
        padding-top: 6px !important;
        padding-bottom: 12px !important;
        border-bottom: 2px solid rgba(148, 163, 184, 0.25) !important;
        overflow-x: auto !important;
        flex-wrap: wrap !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: auto !important;
        min-height: 42px !important;
        padding: 8px 18px !important;
        white-space: normal !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        border: 1px solid rgba(148, 163, 184, 0.25) !important;
        background-color: rgba(148, 163, 184, 0.08) !important;
        transition: all 0.2s ease !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        border-color: #38BDF8 !important;
        background-color: rgba(56, 189, 248, 0.12) !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(56, 189, 248, 0.22) !important;
        border-color: #38BDF8 !important;
        color: #38BDF8 !important;
    }

    /* 4. TIPOGRAFI & WARNA ELEGAN (COCOK UNTUK DARK MODE & LIGHT MODE) */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38BDF8 0%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.02rem;
        color: #94A3B8;
        margin-bottom: 1.5rem;
    }

    /* 5. KARTU METRIK & STATISTIK */
    .metric-card {
        background: rgba(30, 41, 59, 0.55);
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .cv-stat-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(135px, 1fr));
        gap: 12px;
        margin-top: 10px;
        margin-bottom: 14px;
    }
    .cv-stat-box {
        background-color: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 10px;
        padding: 12px 14px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .cv-stat-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .cv-stat-val {
        font-size: 1.25rem;
        font-weight: 800;
        color: #F8FAFC;
        white-space: normal;
        word-break: break-word;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.35rem !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
    }
    [data-testid="stMetricLabel"] {
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }
    .badge-yes {
        background-color: #064E3B;
        color: #A7F3D0;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
        border: 1px solid #059669;
    }
    .badge-no {
        background-color: #7F1D1D;
        color: #FECACA;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
        border: 1px solid #DC2626;
    }
    .indicator-card {
        background-color: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }

    /* 6. MODEL HUBUNGAN VARIABEL PENELITIAN (X -> Y) */
    .model-box-x {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.88), rgba(15, 23, 42, 0.88));
        border: 2px solid #38BDF8;
        border-radius: 12px;
        padding: 16px 18px;
        height: 100%;
        box-shadow: 0 4px 14px rgba(56, 189, 248, 0.12);
    }
    .model-box-y {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.88), rgba(15, 23, 42, 0.88));
        border: 2px solid #10B981;
        border-radius: 12px;
        padding: 16px 18px;
        height: 100%;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.12);
    }
    .model-arrow-box {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        height: 100%;
        padding: 8px 4px;
    }
    .var-chip-x {
        display: inline-block;
        background: rgba(56, 189, 248, 0.12);
        color: #BAE6FD;
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 6px;
        padding: 4px 8px;
        font-size: 0.8rem;
        margin: 2px 2px;
        font-weight: 600;
    }
    .var-chip-y {
        display: inline-block;
        background: rgba(16, 185, 129, 0.12);
        color: #A7F3D0;
        border: 1px solid rgba(16, 185, 129, 0.35);
        border-radius: 6px;
        padding: 4px 8px;
        font-size: 0.8rem;
        margin: 2px 2px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Inisialisasi Database
db.init_db()
db.seed_sample_data()

# Sidebar: Pengaturan & Navigasi
st.sidebar.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=70)
st.sidebar.title("Sistem Computer Vision TA")
st.sidebar.caption("Analisis Karakteristik Visual UMKM vs Engagement (Perspektif Ekonomi Islam & Perlindungan Konsumen)")

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Konfigurasi Engine AI")
engine_choice = st.sidebar.radio(
    "Pilihan Engine Identifikasi:",
    ["Local CV & Rule-Based (100% Offline)", "Google Gemini Vision AI (Cloud)"],
    index=0
)

gemini_key = ""
if engine_choice == "Google Gemini Vision AI (Cloud)":
    gemini_key = st.sidebar.text_input(
        "Google AI Studio API Key:",
        type="password",
        value=os.environ.get("GEMINI_API_KEY", ""),
        help="Masukkan Gemini API Key gratis dari aistudio.google.com"
    )
    if not gemini_key:
        st.sidebar.info("💡 Jika belum ada API key, sistem otomatis menggunakan Local Engine.")

st.sidebar.markdown("---")
st.sidebar.markdown("""
**8 Indikator Penelitian (K1 - K8):**
- **K1:** Nama Produk
- **K2:** Harga
- **K3:** Diskon/Promo
- **K4:** Periode Promo
- **K5:** Syarat Promo
- **K6:** Info Produk
- **K7:** Klaim Kualitas
- **K8:** Visual–Caption
""")

# Inisialisasi session state untuk input postingan
if "active_image" not in st.session_state:
    st.session_state["active_image"] = None
if "last_fetched_url" not in st.session_state:
    st.session_state["last_fetched_url"] = ""
if "url_input_text" not in st.session_state:
    st.session_state["url_input_text"] = ""
if "in_caption" not in st.session_state:
    st.session_state["in_caption"] = ""
if "in_umkm" not in st.session_state:
    st.session_state["in_umkm"] = "UMKM Unggulan"
if "in_title" not in st.session_state:
    st.session_state["in_title"] = "Postingan Produk"
if "in_platform" not in st.session_state:
    st.session_state["in_platform"] = "Instagram"
if "in_followers" not in st.session_state:
    st.session_state["in_followers"] = 5000
if "in_likes" not in st.session_state:
    st.session_state["in_likes"] = 250
if "in_comments" not in st.session_state:
    st.session_state["in_comments"] = 30
if "in_shares" not in st.session_state:
    st.session_state["in_shares"] = 12
if "in_saves" not in st.session_state:
    st.session_state["in_saves"] = 20
if "in_rating" not in st.session_state:
    st.session_state["in_rating"] = 4.8
if "period_start" not in st.session_state:
    st.session_state["period_start"] = date(2025, 1, 1)
if "period_end" not in st.session_state:
    st.session_state["period_end"] = date(2026, 12, 31)
if "in_post_date" not in st.session_state:
    st.session_state["in_post_date"] = date.today()

# Navigasi Tab Utama (Lega dan Responsive)
tab_identify, tab_dataset, tab_statistics, tab_sharia_law, tab_export = st.tabs([
    "📸 Identifikasi Postingan",
    "📂 Dataset Penelitian",
    "📊 Analisis Statistik (Bab 4)",
    "⚖️ Fiqh & Hukum Konsumen",
    "📥 Ekspor Data (Gretl/SPSS)"
])

# ==========================================
# TAB 1: IDENTIFIKASI POSTINGAN
# ==========================================
with tab_identify:
    st.markdown('<div class="main-title">📸 Identifikasi Karakteristik Visual Postingan UMKM</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Ekstraksi otomatis 8 indikator visual (K1–K8), parameter Computer Vision, penghitungan Total Visible Engagement (TVE = Likes + Comments), serta skor kepatuhan Fiqh Muamalah dan UU Perlindungan Konsumen.</div>', unsafe_allow_html=True)
    
    col_input, col_result = st.columns([1, 1.25], gap="large")
    
    with col_input:
        st.subheader("1. Masukkan Media & Data Postingan")
        
        input_method = st.radio(
            "Pilih Metode Input Postingan:",
            [
                "🔗 Ambil dari Link (Instagram / Shopee)",
                "📷 Scan Screenshot (OCR Auto-Fill)",
                "📁 Unggah File Gambar (JPG / PNG)",
                "🎯 Contoh Sampel Cepat",
            ],
            horizontal=False
        )
        
        url_input = ""
        # --- METODE 1: LINK INSTAGRAM / SHOPEE ---
        if input_method == "🔗 Ambil dari Link (Instagram / Shopee)":
            st.markdown("##### Tempelkan Tautan Link Postingan:")
            url_input = st.text_input(
                "URL Link Instagram atau Shopee:",
                value=st.session_state.get("url_input_text", ""),
                placeholder="Contoh: https://www.instagram.com/p/... atau https://id.shp.ee/3fqXfQCV atau https://shopee.co.id/...",
                help="Mendukung link postingan Instagram (p/reel) serta link produk Shopee (shopee.co.id, id.shp.ee, shp.ee, s.shopee.co.id)."
            )
            st.session_state["url_input_text"] = url_input
            
            c_btn_fetch, _ = st.columns([1.2, 1])
            with c_btn_fetch:
                btn_fetch_url = st.button("🌐 Ambil Gambar & Data Link", type="secondary", use_container_width=True)
                
            if btn_fetch_url:
                if not url_input.strip():
                    st.warning("⚠️ Mohon tempelkan URL postingan terlebih dahulu.")
                else:
                    with st.spinner("Mengunduh gambar postingan dan membaca caption..."):
                        fetch_res = uf.fetch_media_from_url(url_input)
                        if fetch_res["status"] == "success":
                            st.session_state["active_image"] = fetch_res["image"]
                            st.session_state["last_fetched_url"] = url_input.strip()
                            st.session_state["in_title"] = fetch_res["title"]
                            st.session_state["in_caption"] = fetch_res["caption"]
                            default_brand = "UMKM Shopee" if fetch_res.get("platform") == "Shopee" else "UMKM Instagram"
                            st.session_state["in_umkm"] = fetch_res.get("umkm_name", default_brand)
                            st.session_state["in_platform"] = fetch_res["platform"]
                            st.session_state["in_likes"] = fetch_res.get("likes", 0)
                            st.session_state["in_comments"] = fetch_res.get("comments", 0)
                            st.session_state["in_shares"] = fetch_res.get("shares", 0)
                            st.session_state["in_saves"] = fetch_res.get("saves", 0)
                            if fetch_res.get("rating", 0) > 0:
                                st.session_state["in_rating"] = float(fetch_res["rating"])
                            if fetch_res.get("followers", 0) > 0:
                                st.session_state["in_followers"] = fetch_res["followers"]
                            st.session_state["is_from_link"] = True
                            st.session_state["is_estimated_engagement"] = False
                            st.session_state["auto_cv_pending"] = True
                            
                            fol_disp = fetch_res.get("followers", st.session_state.get("in_followers", 0))
                            rating_disp = f", Rating: {fetch_res['rating']} ⭐" if fetch_res.get("rating") else ""
                            st.success(f"🎉 Berhasil mengambil data {fetch_res['platform']} ({fetch_res.get('umkm_name','')})! Likes/Favorit: {fetch_res.get('likes', 0):,}, Comments/Ulasan: {fetch_res.get('comments', 0):,}, Followers: {fol_disp:,}{rating_disp}")
                            st.rerun()
                        else:
                            st.error(f"❌ {fetch_res['message']}")

        # --- METODE 2: SCAN SCREENSHOT OCR ---
        elif input_method == "📷 Scan Screenshot (OCR Auto-Fill)":
            st.markdown("##### 📷 Upload Screenshot Postingan Instagram / Shopee:")
            st.info(
                "Upload screenshot postingan (foto profil, feed, atau halaman produk). "
                "OCR akan membaca teks dan **otomatis mengisi** Caption, Likes, Comments, Followers, dll.",
                icon="🤖"
            )

            ocr_upload = st.file_uploader(
                "Unggah Screenshot Postingan:",
                type=["jpg", "jpeg", "png", "webp"],
                key="ocr_screenshot_upload",
            )

            if ocr_upload is not None:
                ocr_img = Image.open(ocr_upload)
                st.image(ocr_img, caption="Screenshot yang akan di-scan", use_container_width=True)

                btn_ocr = st.button(
                    "🔍 Scan & Ekstrak Data Otomatis (OCR)",
                    type="primary",
                    use_container_width=True,
                )

                if btn_ocr:
                    with st.spinner("🤖 Menjalankan OCR... (pertama kali butuh beberapa detik untuk memuat model)"):
                        ocr_result = ocr.extract_text(ocr_img)

                    if ocr_result["status"] == "error":
                        st.error(f"❌ {ocr_result['message']}")
                        # Ekstraksi visual awal untuk estimasi jika screenshot tidak punya angka
                        _cv_pre = ve.analyze_visual_features(ocr_img)
                        parsed = ocr.parse_post_data(
                            ocr_result["full_text"],
                            ocr_result["texts"],
                            _cv_pre
                        )

                        # ── Auto-fill session state ──────────────────────────
                        st.session_state["active_image"] = ocr_img
                        st.session_state["in_umkm"] = parsed["umkm_name"]
                        st.session_state["in_title"] = parsed["title"]
                        st.session_state["in_caption"] = parsed["caption"]
                        st.session_state["in_platform"] = parsed["platform"]
                        st.session_state["in_followers"] = parsed["followers"]
                        st.session_state["in_likes"] = parsed["likes"]
                        st.session_state["in_comments"] = parsed["comments"]
                        st.session_state["in_shares"] = parsed["shares"]
                        st.session_state["in_saves"] = parsed["saves"]
                        if parsed.get("rating"):
                            st.session_state["in_rating"] = float(parsed["rating"])
                        st.session_state["is_estimated_engagement"] = parsed.get("is_estimated", False)
                        st.session_state["ocr_last_text"] = ocr_result["full_text"]
                        st.session_state["auto_cv_pending"] = True

                        st.success("✅ OCR selesai! Informasi postingan & metrik engagement berhasil diisi otomatis.")
                        st.rerun()

        # --- METODE 3: UPLOAD FILE GAMBAR (Auto-Ekstraksi Detail, Metrik & CV) ---
        elif input_method == "📁 Unggah File Gambar (JPG / PNG)":
            file_upload = st.file_uploader(
                "Unggah File Gambar Postingan (JPG / PNG / WEBP):",
                type=["jpg", "jpeg", "png", "webp"]
            )
            if file_upload is not None:
                fingerprint = f"{file_upload.name}_{file_upload.size}"

                if st.session_state.get("upload_fingerprint") != fingerprint:
                    st.session_state["upload_fingerprint"] = fingerprint
                    img = Image.open(file_upload)

                    with st.spinner("🤖 Menganalisis visual citra & mengekstrak data postingan otomatis..."):
                        # 1. Analisis Computer Vision awal
                        _cv_pre = ve.analyze_visual_features(img)
                        # 2. OCR untuk membaca teks & identitas dalam gambar
                        ocr_res = ocr.extract_text(img)
                        # 3. Parsing pintar Brand, Judul, Caption & Engagement
                        parsed = ocr.parse_post_data(
                            ocr_res.get("full_text", ""),
                            ocr_res.get("texts", []),
                            _cv_pre
                        )

                    # ── Isi otomatis Detail Informasi Postingan & Metrik Engagement ──
                    st.session_state["active_image"] = img
                    st.session_state["in_umkm"] = parsed["umkm_name"]
                    st.session_state["in_title"] = parsed["title"]
                    st.session_state["in_caption"] = parsed["caption"]
                    st.session_state["in_platform"] = parsed["platform"]
                    st.session_state["in_followers"] = parsed["followers"]
                    st.session_state["in_likes"] = parsed["likes"]
                    st.session_state["in_comments"] = parsed["comments"]
                    st.session_state["in_shares"] = parsed["shares"]
                    st.session_state["in_saves"] = parsed["saves"]
                    if parsed.get("rating"):
                        st.session_state["in_rating"] = float(parsed["rating"])
                    st.session_state["is_estimated_engagement"] = parsed.get("is_estimated", False)
                    if ocr_res.get("full_text"):
                        st.session_state["ocr_last_text"] = ocr_res["full_text"]

                    # Set trigger agar Computer Vision langsung berjalan otomatis
                    st.session_state["auto_cv_pending"] = True
                    st.rerun()

                else:
                    if st.session_state.get("active_image") is None:
                        st.session_state["active_image"] = Image.open(file_upload)

        # --- METODE 4: CONTOH SAMPEL CEPAT ---
        else:
            sample_opt = st.selectbox(
                "Pilih Sampel Data Pengujian:",
                ["Contoh 1: Promo Kopi Aren (Lengkap & Halal)", "Contoh 2: Fashion Hijab (DM for Price)"]
            )
            samples_dir = os.path.join(os.path.dirname(__file__), "samples")
            if sample_opt == "Contoh 1: Promo Kopi Aren (Lengkap & Halal)":
                sample_path = os.path.join(samples_dir, "sample_kopi_promo.jpg")
                if os.path.exists(sample_path):
                    st.session_state["active_image"] = Image.open(sample_path)
                st.session_state["in_caption"] = "Menu Kopi Susu Aren gula asli! Beli 1 Gratis 1 promo Rp 25.000 berlaku 1-10 Ramadhan. Syarat follow IG & min 2 pcs. 100% Halal MUI & BPOM."
                st.session_state["in_umkm"] = "Kopi Barokah"
                st.session_state["in_title"] = "Promo Ramadhan Kopi Susu Aren"
                st.session_state["in_followers"] = 4500
                st.session_state["in_likes"] = 320
                st.session_state["in_comments"] = 45
                st.session_state["in_shares"] = 18
                st.session_state["in_saves"] = 35
            else:
                sample_path = os.path.join(samples_dir, "sample_fashion_dm.jpg")
                if os.path.exists(sample_path):
                    st.session_state["active_image"] = Image.open(sample_path)
                st.session_state["in_caption"] = "Alya Voal Premium Segi Empat bahan ultrafine tegak seharian anti kusut! Minat langsung DM ya kak, stok rebutan!!"
                st.session_state["in_umkm"] = "Alya Hijab Official"
                st.session_state["in_title"] = "Koleksi Hijab Voal Premium"
                st.session_state["in_followers"] = 12000
                st.session_state["in_likes"] = 540
                st.session_state["in_comments"] = 110
                st.session_state["in_shares"] = 15
                st.session_state["in_saves"] = 80

        # Tampilkan Preview Gambar Terpilih
        if st.session_state.get("active_image") is not None:
            st.image(st.session_state["active_image"], caption="Gambar yang Aktif untuk Dianalisis", use_container_width=True)
            st.success("✅ Gambar aktif siap diproses!")
            
        st.markdown("#### Detail Informasi Postingan")
        if st.session_state.get("in_umkm") and st.session_state.get("in_umkm") != "UMKM Unggulan":
            st.caption("✨ *Nama Brand, Judul, dan Caption terisi otomatis dari analisis gambar (dapat disunting bebas).*")
        in_umkm = st.text_input("Nama Brand / UMKM:", value=st.session_state.get("in_umkm", "UMKM Unggulan"))
        in_title = st.text_input("Judul / Keterangan Postingan:", value=st.session_state.get("in_title", "Postingan Produk"))
        in_caption = st.text_area("Teks Caption Postingan:", value=st.session_state.get("in_caption", ""), height=110, help="Teks yang tertera pada caption postingan")
        
        # ── Periode Penelitian & Tanggal Postingan (Purposive Sampling) ──
        st.markdown("#### 📅 Periode Postingan & Waktu Penelitian")
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            in_post_date = st.date_input(
                "Tanggal Postingan:",
                value=st.session_state.get("in_post_date", date.today()),
                help="Tanggal publikasi konten pada media sosial"
            )
            st.session_state["in_post_date"] = in_post_date
        with c_p2:
            period_start = st.date_input(
                "Awal Periode Penelitian:",
                value=st.session_state.get("period_start", date(2025, 1, 1)),
                help="Batas awal rentang observasi penelitian"
            )
            st.session_state["period_start"] = period_start
        with c_p3:
            period_end = st.date_input(
                "Akhir Periode Penelitian:",
                value=st.session_state.get("period_end", date(2026, 12, 31)),
                help="Batas akhir rentang observasi penelitian"
            )
            st.session_state["period_end"] = period_end

        curr_plat = st.session_state.get("in_platform", "Instagram")
        is_shopee = (curr_plat == "Shopee")
        plat_icon = "🛍️ E-Commerce Shopee" if is_shopee else "📸 Media Sosial Instagram"
        
        st.markdown(f"#### Metrik Engagement ({plat_icon})")
        if st.session_state.get("is_from_link", False):
            if is_shopee:
                st.caption("🔗 *Metrik engagement terisi otomatis dari data produk Shopee (Favorit, Penilaian/Ulasan, Pengikut Toko) — dapat disesuaikan.*")
            else:
                st.caption("🔗 *Metrik engagement terisi otomatis dari data tautan link Instagram (Likes, Comments, Followers) — dapat disesuaikan.*")
        elif st.session_state.get("is_estimated_engagement", False):
            st.caption(f"⚡ *Metrik diestimasi otomatis oleh AI & Computer Vision untuk platform {curr_plat} (dapat disesuaikan).*")
        elif st.session_state.get("active_image") is not None and st.session_state.get("in_likes", 0) > 0:
            st.caption(f"🎯 *Metrik engagement terdeteksi otomatis dari gambar/screenshot {curr_plat} (dapat disesuaikan).*")

        lbl_fol = "Pengikut Toko (Followers):" if is_shopee else "Followers Akun:"
        lbl_lik = "Jumlah Favorit / Suka (Likes):" if is_shopee else "Jumlah Likes:"
        lbl_com = "Jumlah Penilaian / Ulasan (Comments):" if is_shopee else "Jumlah Comments:"
        lbl_sha = "Jumlah Dibagikan (Shares):" if is_shopee else "Jumlah Shares:"
        lbl_sav = "Jumlah Keranjang / Wishlist (Saves):" if is_shopee else "Jumlah Saves:"

        c_e1, c_e2 = st.columns(2)
        with c_e1:
            in_fol = st.number_input(lbl_fol, min_value=1, value=st.session_state.get("in_followers", 5000), step=100)
            in_lik = st.number_input(lbl_lik, min_value=0, value=st.session_state.get("in_likes", 250), step=10)
            in_com = st.number_input(lbl_com, min_value=0, value=st.session_state.get("in_comments", 30), step=5)
        with c_e2:
            in_sha = st.number_input(lbl_sha, min_value=0, value=st.session_state.get("in_shares", 12), step=5)
            in_sav = st.number_input(lbl_sav, min_value=0, value=st.session_state.get("in_saves", 20), step=5)
            if is_shopee:
                in_rating = st.number_input(
                    "Rating Penilaian Produk (⭐ 1.0 – 5.0):",
                    min_value=1.0,
                    max_value=5.0,
                    value=float(st.session_state.get("in_rating", 4.8)),
                    step=0.1,
                    format="%.1f",
                    help="Skor rating bintang ulasan produk di Shopee (skala 1.0 hingga 5.0)"
                )
                st.session_state["in_rating"] = in_rating
            else:
                in_rating = float(st.session_state.get("in_rating", 0.0))
            
        btn_analyze = st.button("🚀 Jalankan Identifikasi Computer Vision (K1–K8)", type="primary", use_container_width=True)

    with col_result:
        st.subheader("2. Hasil Analisis & Identifikasi")

        # ── AUTO-RUN CV jika ada trigger dari upload file baru ───────────────
        if st.session_state.pop("auto_cv_pending", False):
            if st.session_state.get("active_image") is not None:
                _img_auto  = st.session_state["active_image"]
                _cap_auto  = st.session_state.get("in_caption", "")
                _fol_auto  = st.session_state.get("in_followers", 5000)
                _lik_auto  = st.session_state.get("in_likes", 250)
                _com_auto  = st.session_state.get("in_comments", 30)
                _sha_auto  = st.session_state.get("in_shares", 12)
                _sav_auto  = st.session_state.get("in_saves", 20)

                with st.spinner("🔍 Menganalisis Computer Vision secara otomatis..."):
                    _cv_auto = ve.analyze_visual_features(_img_auto)
                    if engine_choice == "Google Gemini Vision AI (Cloud)" and gemini_key:
                        _ev_auto = ma.analyze_post_gemini(_img_auto, _cap_auto, gemini_key)
                    else:
                        _ev_auto = ma.analyze_post_offline(_img_auto, _cap_auto, _cv_auto)
                    _tve_auto = db.calculate_total_visible_engagement(_lik_auto, _com_auto)
                    _er_auto  = db.calculate_engagement_rate(_lik_auto, _com_auto, _sha_auto, _sav_auto, _fol_auto)
                    _ann_auto = ve.generate_annotated_preview(_img_auto, _cv_auto, _ev_auto)

                st.session_state["latest_analysis"] = {
                    "cv_feats": _cv_auto,
                    "eval_res": _ev_auto,
                    "tve_val":  _tve_auto,
                    "er_val":   _er_auto,
                    "annotated_img": _ann_auto,
                    "raw_input": {
                        "post_title": st.session_state.get("in_title", "Postingan Produk"),
                        "umkm_name":  st.session_state.get("in_umkm", "UMKM"),
                        "platform":   st.session_state.get("in_platform", "Instagram"),
                        "post_date":  in_post_date.strftime("%Y-%m-%d") if isinstance(in_post_date, (date, datetime)) else str(in_post_date),
                        "caption":    _cap_auto,
                        "followers":  _fol_auto,
                        "likes":      _lik_auto,
                        "comments":   _com_auto,
                        "shares":     _sha_auto,
                        "saves":      _sav_auto,
                        "product_rating": float(st.session_state.get("in_rating", 4.8 if st.session_state.get("in_platform") == "Shopee" else 0.0)),
                    }
                }

                # Tampilkan notif OCR jika ada teks yang terbaca
                ocr_txt = st.session_state.get("ocr_last_text", "")
                if ocr_txt:
                    st.success("✅ Gambar berhasil di-scan OCR & Computer Vision otomatis!")
                    with st.expander("📄 Teks OCR yang Terbaca dari Gambar", expanded=False):
                        st.text(ocr_txt[:1500])
                else:
                    st.success("✅ Computer Vision berjalan otomatis!")

        if btn_analyze:
            # FITUR OTOMATIS: Unduh link saat tombol Analisis diklik
            if input_method == "🔗 Ambil dari Link (Instagram / Shopee)" and url_input.strip():
                if st.session_state.get("active_image") is None or st.session_state.get("last_fetched_url") != url_input.strip():
                    with st.spinner("Mendeteksi dan mengunduh gambar dari tautan..."):
                        fetch_res = uf.fetch_media_from_url(url_input)
                        if fetch_res["status"] == "success":
                            st.session_state["active_image"] = fetch_res["image"]
                            st.session_state["last_fetched_url"] = url_input.strip()
                            st.session_state["in_title"] = fetch_res["title"]
                            default_umkm = "UMKM Shopee" if fetch_res.get("platform") == "Shopee" else "UMKM Instagram"
                            st.session_state["in_umkm"] = fetch_res.get("umkm_name", default_umkm)
                            st.session_state["in_platform"] = fetch_res["platform"]
                            in_title = fetch_res["title"]
                            in_caption = fetch_res["caption"]
                            in_umkm = fetch_res.get("umkm_name", default_umkm)
                            in_lik = fetch_res.get("likes", in_lik)
                            in_com = fetch_res.get("comments", in_com)
                            in_sha = fetch_res.get("shares", in_sha)
                            in_sav = fetch_res.get("saves", in_sav)
                            if fetch_res.get("rating", 0) > 0:
                                in_rating = float(fetch_res["rating"])
                                st.session_state["in_rating"] = in_rating
                            if fetch_res.get("followers", 0) > 0:
                                in_fol = fetch_res["followers"]
                                st.session_state["in_followers"] = in_fol
                            st.session_state["in_likes"] = in_lik
                            st.session_state["in_comments"] = in_com
                            st.session_state["is_from_link"] = True
                            st.session_state["is_estimated_engagement"] = False
                        else:
                            st.error(f"❌ {fetch_res['message']}")
            
            if st.session_state.get("active_image") is None:
                st.error("⚠️ Silakan pilih sampel, unggah gambar, atau tempelkan link valid terlebih dahulu!")
            else:
                with st.spinner("Memproses ekstraksi parameter citra & penalaran indikator K1–K8..."):
                    # 1. Ekstraksi Fitur Computer Vision
                    cv_feats = ve.analyze_visual_features(st.session_state["active_image"])
                    
                    # 2. Identifikasi K1 - K8 & Compliance
                    if engine_choice == "Google Gemini Vision AI (Cloud)" and gemini_key:
                        eval_res = ma.analyze_post_gemini(st.session_state["active_image"], in_caption, gemini_key)
                    else:
                        eval_res = ma.analyze_post_offline(st.session_state["active_image"], in_caption, cv_feats)
                        
                    # Simpan data sementara di session_state
                    tve_val = db.calculate_total_visible_engagement(in_lik, in_com)
                    er_val = db.calculate_engagement_rate(in_lik, in_com, in_sha, in_sav, in_fol)
                    
                    # Bikin visual annotated preview
                    annotated_img = ve.generate_annotated_preview(st.session_state["active_image"], cv_feats, eval_res)
                    
                    st.session_state["latest_analysis"] = {
                        "cv_feats": cv_feats,
                        "eval_res": eval_res,
                        "tve_val": tve_val,
                        "er_val": er_val,
                        "annotated_img": annotated_img,
                        "raw_input": {
                            "post_title": in_title,
                            "umkm_name": in_umkm,
                            "platform": st.session_state.get("in_platform", "Instagram"),
                            "post_date": in_post_date.strftime("%Y-%m-%d") if isinstance(in_post_date, (date, datetime)) else str(in_post_date),
                            "caption": in_caption,
                            "followers": in_fol,
                            "likes": in_lik,
                            "comments": in_com,
                            "shares": in_sha,
                            "saves": in_sav,
                            "product_rating": in_rating,
                        }
                    }
                    st.success("✅ Identifikasi berhasil diselesaikan!")

        if "latest_analysis" in st.session_state:
            res_data = st.session_state["latest_analysis"]
            cv_f = res_data["cv_feats"]
            ev_r = res_data["eval_res"]
            tve_v = res_data.get("tve_val", db.calculate_total_visible_engagement(res_data['raw_input']['likes'], res_data['raw_input']['comments']))
            er_v = res_data["er_val"]
            
            # Preview terannotasi & Metrik CV yang LEBAR dan JELAS (TIDAK TERPOTONG!)
            with st.expander("👁️ Gambar Terannotasi & Karakteristik Citra (OpenCV)", expanded=True):
                st.image(res_data["annotated_img"], caption="Preview Hasil Deteksi Indikator Visual", use_container_width=True)
                
                st.markdown(f"""
                <div class="cv-stat-grid">
                    <div class="cv-stat-box">
                        <div class="cv-stat-title">Kecerahan</div>
                        <div class="cv-stat-val">{cv_f['brightness']} <span style="font-size:0.8rem; color:#94A3B8;">/ 255</span></div>
                    </div>
                    <div class="cv-stat-box">
                        <div class="cv-stat-title">Kontras RMS</div>
                        <div class="cv-stat-val">{cv_f['contrast']}</div>
                    </div>
                    <div class="cv-stat-box">
                        <div class="cv-stat-title">Kepadatan Teks</div>
                        <div class="cv-stat-val">{cv_f['text_density']*100:.1f}%</div>
                    </div>
                    <div class="cv-stat-box">
                        <div class="cv-stat-title">Format Aspek</div>
                        <div class="cv-stat-val" style="font-size:1.0rem;">{cv_f['format_type']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="background:rgba(30,41,59,0.6); border:1px solid rgba(148,163,184,0.25); border-radius:8px; padding:10px 14px; font-size:0.9rem; color:#E2E8F0;">
                    🎨 <b>Warna Dominan:</b> {cv_f['dominant_color_name']} 
                    <span style="display:inline-block; width:14px; height:14px; background-color:{cv_f['dominant_color_hex']}; vertical-align:middle; border-radius:3px; border:1px solid #94A3B8; margin:0 4px;"></span> 
                    <code>{cv_f['dominant_color_hex']}</code> &nbsp;|&nbsp; 
                    👤 <b>Deteksi Wajah/Model:</b> {'Ada (' + str(cv_f['num_faces']) + ' wajah)' if cv_f['face_detected']==1 else 'Tidak Ada'}
                </div>
                """, unsafe_allow_html=True)

            # Kartu Total Visible Engagement (TVE)
            cur_p = res_data['raw_input'].get('platform', 'Instagram')
            fol_lbl = "Pengikut Toko" if cur_p == "Shopee" else "Followers"
            rat_html = ""
            if cur_p == "Shopee" and res_data['raw_input'].get('product_rating', 0) > 0:
                p_rat = res_data['raw_input']['product_rating']
                rat_html = f"<br>⭐ Rating: <b style='color:#FBBF24;'>{p_rat:.1f} / 5.0</b>"

            st.markdown(f"""
            <div class="metric-card">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                    <div>
                        <h4 style="margin:0; color:#38BDF8;">📊 Total Visible Engagement (TVE): <span style="font-size:1.85rem; font-weight:800; color:#60A5FA;">{tve_v:,} Interaksi</span></h4>
                        <p style="margin:6px 0 0 0; font-size:0.9rem; color:#E2E8F0;">
                            <b>Rumus:</b> Likes <b>{res_data['raw_input']['likes']:,}</b> + Comments <b>{res_data['raw_input']['comments']:,}</b> = <b>{tve_v:,}</b> total interaksi publik yang terlihat langsung pada postingan.
                        </p>
                    </div>
                    <div style="background:rgba(15,23,42,0.6); padding:8px 14px; border-radius:8px; border:1px solid rgba(148,163,184,0.2); font-size:0.85rem; color:#94A3B8;">
                        📈 Rasio ER: <b style="color:#38BDF8;">{er_v}%</b> <br>
                        👥 {fol_lbl}: <b style="color:#F1F5F9;">{res_data['raw_input']['followers']:,}</b>{rat_html}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── EVALUASI PURPOSIVE SAMPLING (7 Inklusi I1-I7 & 9 Eksklusi E1-E9) ──
            post_d_str = res_data["raw_input"].get("post_date", date.today().strftime("%Y-%m-%d"))
            p_start_str = period_start.strftime("%Y-%m-%d") if isinstance(period_start, (date, datetime)) else str(period_start)
            p_end_str = period_end.strftime("%Y-%m-%d") if isinstance(period_end, (date, datetime)) else str(period_end)
            
            sample_eval = sc.evaluate_sampling_criteria(
                post_date_str=post_d_str,
                period_start_str=p_start_str,
                period_end_str=p_end_str,
                caption=res_data["raw_input"].get("caption", ""),
                has_image=True,
                is_video_or_reel=False,
                object_detected=bool(ev_r.get("k1_nama_produk", 0) == 1 or cv_f.get("f1_object_detected", 1) == 1),
                likes=res_data["raw_input"].get("likes", 0),
                comments=res_data["raw_input"].get("comments", 0),
                is_umkm_account=True
            )
            res_data["sample_eval"] = sample_eval

            # Tampilan Status Kelayakan Sampel
            if sample_eval["is_valid"]:
                st.markdown(f"""
                <div class="metric-card" style="border-left: 5px solid #10B981; background: rgba(6, 78, 59, 0.25);">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <h4 style="margin:0; color:#34D399;">✅ MEMENUHI SYARAT SAMPEL (Purposive Sampling Valid)</h4>
                            <p style="margin:4px 0 0 0; font-size:0.88rem; color:#A7F3D0;">
                                Postingan lolos 7 Kriteria Inklusi (I1–I7) dan bebas dari 9 Kriteria Eksklusi (E1–E9). Memenuhi rentang waktu observasi ({p_start_str} s.d. {p_end_str}).
                            </p>
                        </div>
                        <span class="badge-yes" style="font-size:0.95rem;">SAMPEL VALID</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="metric-card" style="border-left: 5px solid #EF4444; background: rgba(127, 29, 29, 0.25);">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <h4 style="margin:0; color:#F87171;">❌ TIDAK MEMENUHI SYARAT SAMPEL (Gugur / Eksklusi)</h4>
                            <p style="margin:4px 0 0 0; font-size:0.88rem; color:#FECACA;">
                                <b>Catatan Gugur:</b> {sample_eval['notes']}
                            </p>
                        </div>
                        <span class="badge-no" style="font-size:0.95rem;">GUGUR SAMPEL</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with st.expander("📋 Rincian Evaluasi 7 Kriteria Inklusi & 9 Kriteria Eksklusi", expanded=False):
                col_inc_ui, col_exc_ui = st.columns(2)
                with col_inc_ui:
                    st.markdown("##### 🟢 7 Kriteria Inklusi (Harus Semua Terpenuhi):")
                    for code, info in sc.INCLUSION_CRITERIA.items():
                        is_ok = sample_eval["inclusions"].get(code, False)
                        st_icon = "✅" if is_ok else "❌"
                        st_color = "#34D399" if is_ok else "#F87171"
                        st.markdown(f"""
                        <div style="margin-bottom:8px; padding:6px 10px; background:rgba(30,41,59,0.5); border-radius:6px; border-left:3px solid {st_color};">
                            <b>{st_icon} {code}: {info['title']}</b><br>
                            <span style="font-size:0.82rem; color:#94A3B8;">{info['desc']}</span>
                        </div>
                        """, unsafe_allow_html=True)

                with col_exc_ui:
                    st.markdown("##### 🔴 9 Kriteria Eksklusi (Tidak Boleh Ada Yang Memicu):")
                    for code, info in sc.EXCLUSION_CRITERIA.items():
                        is_trig = sample_eval["exclusions"].get(code, False)
                        st_icon = "⚠️ Terpicu (Gugur)" if is_trig else "✔️ Bebas (Aman)"
                        st_color = "#EF4444" if is_trig else "#10B981"
                        st.markdown(f"""
                        <div style="margin-bottom:8px; padding:6px 10px; background:rgba(30,41,59,0.5); border-radius:6px; border-left:3px solid {st_color};">
                            <b>{code}: {info['title']}</b> — <span style="color:{st_color}; font-weight:700;">{st_icon}</span><br>
                            <span style="font-size:0.82rem; color:#94A3B8;">{info['desc']}</span>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Matriks 8 Indikator K1 - K8 dalam Card Luas
            st.markdown("#### 🎯 Hasil Deteksi 8 Indikator Karakteristik Visual")
            
            indicators_list = [
                ("K1: Nama Produk", ev_r.get("k1_nama_produk", 0), ev_r.get("k1_detail", "")),
                ("K2: Harga", ev_r.get("k2_harga", 0), ev_r.get("k2_detail", "")),
                ("K3: Diskon/Promo", ev_r.get("k3_diskon", 0), ev_r.get("k3_detail", "")),
                ("K4: Periode Promo", ev_r.get("k4_periode_promo", 0), ev_r.get("k4_detail", "")),
                ("K5: Syarat Promo", ev_r.get("k5_syarat_promo", 0), ev_r.get("k5_detail", "")),
                ("K6: Info Produk", ev_r.get("k6_info_produk", 0), ev_r.get("k6_detail", "")),
                ("K7: Klaim Kualitas", ev_r.get("k7_klaim", 0), ev_r.get("k7_detail", "")),
                ("K8: Visual–Caption", ev_r.get("k8_visual_caption", 0), ev_r.get("k8_detail", ""))
            ]
            
            for name, val, desc in indicators_list:
                badge = '<span class="badge-yes">✓ ADA (1)</span>' if val == 1 else '<span class="badge-no">✗ TIDAK (0)</span>'
                if name.startswith("K8"):
                    badge = '<span class="badge-yes">✓ SINKRON (1)</span>' if val == 1 else '<span class="badge-no">✗ TIDAK SINKRON (0)</span>'
                    
                st.markdown(f"""
                <div class="indicator-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <span style="font-weight:700; font-size:0.95rem; color:#F1F5F9;">{name}</span>
                        {badge}
                    </div>
                    <div style="font-size:0.88rem; color:#94A3B8;">{desc}</div>
                </div>
                """, unsafe_allow_html=True)

            # ─── SECTION F1–F8: ANALISIS COMPUTER VISION ───────────────────
            st.markdown("---")
            st.markdown("#### 🖥️ Analisis Computer Vision (F1 – F8)")

            cv_features_list = [
                (
                    "F1: Object Detection",
                    "🔲",
                    ev_r.get("f1_object_detection", cv_f.get("f1_object_detected", 1)),
                    ev_r.get("f1_detail", cv_f.get("f1_detail", "Deteksi objek pada gambar")),
                    "TERDETEKSI", "TIDAK TERDETEKSI"
                ),
                (
                    "F2: Color Extraction",
                    "🎨",
                    ev_r.get("f2_color_extraction", 1),
                    ev_r.get("f2_detail", cv_f.get("f2_detail",
                        f"Warna dominan: {cv_f.get('dominant_color_name','–')} ({cv_f.get('dominant_color_hex','–')})")),
                    "TEREKSTRAK", "TIDAK"
                ),
                (
                    "F3: Posisi Objek",
                    "📐",
                    ev_r.get("f3_posisi_objek", 1),
                    ev_r.get("f3_detail", cv_f.get("f3_detail",
                        f"Posisi: {cv_f.get('f3_posisi','Tengah (Center)')}")),
                    "TERIDENTIFIKASI", "TIDAK"
                ),
                (
                    "F4: Dominasi Objek",
                    "📊",
                    ev_r.get("f4_dominasi_objek", 1),
                    ev_r.get("f4_detail", cv_f.get("f4_detail",
                        f"Dominasi: {cv_f.get('f4_dominasi','–')} | Rasio: {cv_f.get('f4_ratio', 0):.1%}")),
                    "DOMINAN", "TIDAK DOMINAN"
                ),
                (
                    "F5: Background",
                    "🖼️",
                    ev_r.get("f5_background", 1),
                    ev_r.get("f5_detail", cv_f.get("f5_detail",
                        f"Tipe background: {cv_f.get('f5_background','–')}")),
                    "TERIDENTIFIKASI", "TIDAK"
                ),
                (
                    "F6: Objek Tambahan",
                    "➕",
                    ev_r.get("f6_objek_tambahan", cv_f.get("f6_objek_tambahan", 0)),
                    ev_r.get("f6_detail", cv_f.get("f6_detail", "Elemen pendukung / prop dalam gambar")),
                    "ADA", "TIDAK ADA"
                ),
                (
                    "F7: Manusia / Model",
                    "🧑",
                    ev_r.get("f7_manusia", cv_f.get("f7_manusia", 0)),
                    ev_r.get("f7_detail", cv_f.get("f7_detail", "Tanpa kehadiran model manusia (fokus produk murni)")),
                    "ADA", "TIDAK ADA"
                ),
                (
                    "F8: Teks Visual",
                    "🔤",
                    ev_r.get("f8_teks", cv_f.get("f8_teks", 0)),
                    ev_r.get("f8_detail", cv_f.get("f8_detail", "Keberadaan teks/tulisan pada gambar")),
                    "ADA", "TIDAK ADA"
                ),
            ]

            for fname, ficon, fval, fdesc, label_yes, label_no in cv_features_list:
                if fval == 1:
                    badge = f'<span class="badge-yes">✓ {label_yes} (1)</span>'
                    card_border = "border-left: 4px solid #10B981;"
                else:
                    badge = f'<span class="badge-no">✗ {label_no} (0)</span>'
                    card_border = "border-left: 4px solid #EF4444;"

                st.markdown(f"""
                <div class="indicator-card" style="{card_border}">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <span style="font-weight:700; font-size:0.95rem; color:#F1F5F9;">{ficon} {fname}</span>
                        {badge}
                    </div>
                    <div style="font-size:0.88rem; color:#94A3B8;">{fdesc}</div>
                </div>
                """, unsafe_allow_html=True)

            # ─── EVALUASI PERSPEKTIF SYARIAH & KONSUMEN ─────────────────────
            # Evaluasi Perspektif Syariah & Konsumen
            st.markdown("---")
            st.markdown("#### ⚖️ Evaluasi Perspektif Penelitian Tugas Akhir")
            
            col_sharia, col_cons = st.columns(2)
            with col_sharia:
                st.markdown(f"""
                <div class="metric-card" style="border-left: 5px solid #10B981;">
                    <h5 style="color:#34D399; margin:0; font-weight:700;">🕌 Skor Kepatuhan Ekonomi Islam</h5>
                    <div style="font-size:1.8rem; font-weight:800; color:#10B981; margin:4px 0;">{ev_r.get('islamic_compliance_score', 0):.1f}%</div>
                    <p style="font-size:0.86rem; color:#CBD5E1; margin:0; line-height:1.45;">{ev_r.get('islamic_review', '')}</p>
                </div>
                """, unsafe_allow_html=True)
                
            with col_cons:
                st.markdown(f"""
                <div class="metric-card" style="border-left: 5px solid #3B82F6;">
                    <h5 style="color:#60A5FA; margin:0; font-weight:700;">🛡️ Skor Perlindungan Konsumen</h5>
                    <div style="font-size:1.8rem; font-weight:800; color:#3B82F6; margin:4px 0;">{ev_r.get('consumer_protection_score', 0):.1f}%</div>
                    <p style="font-size:0.86rem; color:#CBD5E1; margin:0; line-height:1.45;">{ev_r.get('consumer_review', '')}</p>
                </div>
                """, unsafe_allow_html=True)

            # ─── VERIFIKASI & KOREKSI INDIKATOR MANUAL (OPSIONAL OLEH PENELITI) ───
            with st.expander("🛠️ Verifikasi & Koreksi Manual Indikator (Opsional)", expanded=False):
                st.caption("Peneliti dapat memverifikasi atau menyesuaikan hasil ekstraksi AI sebelum disimpan ke dataset TA:")
                col_k_adj, col_f_adj = st.columns(2)
                with col_k_adj:
                    st.markdown("##### 🎯 8 Indikator Konten (K1–K8):")
                    adj_k1 = st.checkbox("K1: Nama Produk", value=bool(ev_r.get("k1_nama_produk", 0) == 1), key="chk_k1")
                    adj_k2 = st.checkbox("K2: Harga Nominal Terbuka", value=bool(ev_r.get("k2_harga", 0) == 1), key="chk_k2")
                    adj_k3 = st.checkbox("K3: Promo / Diskon", value=bool(ev_r.get("k3_diskon", 0) == 1), key="chk_k3")
                    adj_k4 = st.checkbox("K4: Batas Waktu / Periode Promo", value=bool(ev_r.get("k4_periode_promo", 0) == 1), key="chk_k4")
                    adj_k5 = st.checkbox("K5: Syarat Ketentuan Promo (S&K)", value=bool(ev_r.get("k5_syarat_promo", 0) == 1), key="chk_k5")
                    adj_k6 = st.checkbox("K6: Info Spesifikasi & Izin", value=bool(ev_r.get("k6_info_produk", 0) == 1), key="chk_k6")
                    adj_k7 = st.checkbox("K7: Klaim Kualitas", value=bool(ev_r.get("k7_klaim", 0) == 1), key="chk_k7")
                    adj_k8 = st.checkbox("K8: Visual-Caption Sinkron", value=bool(ev_r.get("k8_visual_caption", 1) == 1), key="chk_k8")
                with col_f_adj:
                    st.markdown("##### 🖥️ Fitur Computer Vision (F1–F8):")
                    adj_f1 = st.checkbox("F1: Objek Produk Terdeteksi", value=bool(ev_r.get("f1_object_detection", cv_f.get("f1_object_detected", 1)) == 1), key="chk_f1")
                    adj_f6 = st.checkbox("F6: Objek Tambahan / Props", value=bool(ev_r.get("f6_objek_tambahan", cv_f.get("f6_objek_tambahan", 0)) == 1), key="chk_f6")
                    adj_f7 = st.checkbox("F7: Kehadiran Model / Manusia", value=bool(ev_r.get("f7_manusia", cv_f.get("f7_manusia", 0)) == 1), key="chk_f7")
                    adj_f8 = st.checkbox("F8: Teks Visual Grafis", value=bool(ev_r.get("f8_teks", cv_f.get("f8_teks", 0)) == 1), key="chk_f8")
                
            # Tombol Simpan ke Database
            st.write("")
            if st.button("💾 Simpan Hasil Analisis Ini ke Database Penelitian", type="secondary", use_container_width=True):
                cur_sample_eval = res_data.get("sample_eval", {})
                is_samp_valid = 1 if cur_sample_eval.get("is_valid", True) else 0
                samp_inc_json = json.dumps(cur_sample_eval.get("inclusions", {}))
                samp_exc_json = json.dumps(cur_sample_eval.get("exclusions", {}))
                samp_notes = cur_sample_eval.get("notes", "Memenuhi kriteria purposive sampling")

                save_payload = {
                    **res_data["raw_input"],
                    "image_path": "",
                    "total_visible_engagement": tve_v,
                    "engagement_rate": er_v,
                    "is_sample_valid": is_samp_valid,
                    "sampling_inclusion": samp_inc_json,
                    "sampling_exclusion": samp_exc_json,
                    "sampling_notes": samp_notes,
                    "k1_nama_produk": 1 if adj_k1 else 0,
                    "k1_detail": ev_r.get("k1_detail", ""),
                    "k2_harga": 1 if adj_k2 else 0,
                    "k2_detail": ev_r.get("k2_detail", ""),
                    "k3_diskon": 1 if adj_k3 else 0,
                    "k3_detail": ev_r.get("k3_detail", ""),
                    "k4_periode_promo": 1 if adj_k4 else 0,
                    "k4_detail": ev_r.get("k4_detail", ""),
                    "k5_syarat_promo": 1 if adj_k5 else 0,
                    "k5_detail": ev_r.get("k5_detail", ""),
                    "k6_info_produk": 1 if adj_k6 else 0,
                    "k6_detail": ev_r.get("k6_detail", ""),
                    "k7_klaim": 1 if adj_k7 else 0,
                    "k7_detail": ev_r.get("k7_detail", ""),
                    "k8_visual_caption": 1 if adj_k8 else 0,
                    "k8_detail": ev_r.get("k8_detail", ""),
                    # ── F1–F8 Computer Vision Features ──
                    "f1_object_detection": 1 if adj_f1 else 0,
                    "f1_detail": ev_r.get("f1_detail", cv_f.get("f1_detail", "")),
                    "f2_color_extraction": ev_r.get("f2_color_extraction", 1),
                    "f2_detail": ev_r.get("f2_detail", cv_f.get("f2_detail", "")),
                    "f3_posisi_objek": ev_r.get("f3_posisi_objek", 1),
                    "f3_detail": ev_r.get("f3_detail", cv_f.get("f3_detail", "")),
                    "f4_dominasi_objek": ev_r.get("f4_dominasi_objek", 1),
                    "f4_detail": ev_r.get("f4_detail", cv_f.get("f4_detail", "")),
                    "f5_background": ev_r.get("f5_background", 1),
                    "f5_detail": ev_r.get("f5_detail", cv_f.get("f5_detail", "")),
                    "f6_objek_tambahan": 1 if adj_f6 else 0,
                    "f6_detail": ev_r.get("f6_detail", cv_f.get("f6_detail", "")),
                    "f7_manusia": 1 if adj_f7 else 0,
                    "f7_detail": "Terdeteksi kehadiran model manusia" if adj_f7 else "Tanpa kehadiran model manusia (fokus produk murni)",
                    "f8_teks": 1 if adj_f8 else 0,
                    "f8_detail": ev_r.get("f8_detail", cv_f.get("f8_detail", "")),
                    # ── CV Metrics ──
                    "cv_brightness": cv_f.get("brightness", 0),
                    "cv_contrast": cv_f.get("contrast", 0),
                    "cv_text_density": cv_f.get("text_density", 0),
                    "cv_dominant_color": cv_f.get("dominant_color_name", ""),
                    "cv_face_detected": cv_f.get("face_detected", 0),
                    "islamic_compliance_score": ev_r.get("islamic_compliance_score", 0),
                    "islamic_review": ev_r.get("islamic_review", ""),
                    "consumer_protection_score": ev_r.get("consumer_protection_score", 0),
                    "consumer_review": ev_r.get("consumer_review", ""),
                }
                new_id = db.insert_post(save_payload)
                st.success(f"🎉 Postingan berhasil disimpan dengan ID #{new_id} ke tabel dataset TA!")
                st.rerun()
        else:
            st.info("👈 Silakan tentukan postingan (melalui Link Instagram/Shopee, File, atau Sampel) lalu klik tombol 'Jalankan Identifikasi'.")

# ==========================================
# TAB 2: DATASET PENELITIAN
# ==========================================
with tab_dataset:
    st.markdown('<div class="main-title">📂 Database & Dataset Postingan UMKM</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Kelola data sampel postingan yang telah diidentifikasi untuk penelitian Tugas Akhir.</div>', unsafe_allow_html=True)
    
    df_posts = db.get_all_posts()
    
    if df_posts.empty:
        st.warning("Belum ada data postingan dalam database. Silakan jalankan identifikasi postingan terlebih dahulu.")
    else:
        # Metrik Ringkasan Atas
        valid_sample_count = len(df_posts[df_posts['is_sample_valid'] == 1]) if 'is_sample_valid' in df_posts.columns else len(df_posts)
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Postingan", len(df_posts))
        m2.metric("Sampel Valid (Lolos)", f"{valid_sample_count} Data", help="Postingan yang lolos kriteria inklusi I1-I7 dan bebas eksklusi E1-E9")
        tve_mean = df_posts['total_visible_engagement'].mean() if 'total_visible_engagement' in df_posts.columns else (df_posts['likes'] + df_posts['comments']).mean()
        m3.metric("Rata-rata TVE", f"{tve_mean:.1f} Interaksi", help="Rata-rata Total Visible Engagement (Likes + Comments)")
        m4.metric("Rerata Skor Syariah", f"{df_posts['islamic_compliance_score'].mean():.1f}%")
        m5.metric("Rerata Perlindungan Konsumen", f"{df_posts['consumer_protection_score'].mean():.1f}%")
        
        st.write("")
        # ── MODEL HUBUNGAN VARIABEL PENELITIAN (VARIABEL X ➔ VARIABEL Y) ──
        with st.expander("🧩 MODEL HUBUNGAN VARIABEL PENELITIAN (X: Karakteristik Visual Produk ➔ Y: Engagement Media Sosial UMKM)", expanded=True):
            col_vx, col_vrel, col_vy = st.columns([1.3, 0.8, 1.3], gap="medium")
            
            with col_vx:
                st.markdown("""
                <div class="model-box-x">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="background:#0284C7; color:#FFF; font-size:0.75rem; font-weight:800; padding:2px 8px; border-radius:4px;">VARIABEL INDEPENDEN (X)</span>
                        <span style="color:#38BDF8; font-weight:700; font-size:0.82rem;">8 Indikator + F1-F8 CV</span>
                    </div>
                    <h3 style="margin:0 0 6px 0; color:#F8FAFC; font-size:1.15rem; font-weight:800;">🖼️ Karakteristik Visual Produk</h3>
                    <p style="font-size:0.82rem; color:#94A3B8; margin-bottom:12px; line-height:1.45;">
                        Atribut materi visual promosi produk UMKM yang diidentifikasi melalui Computer Vision & indikator transparansi informasi:
                    </p>
                    <div style="display:flex; flex-wrap:wrap; gap:3px;">
                        <span class="var-chip-x">🏷️ X₁: Nama Produk (K1)</span>
                        <span class="var-chip-x">💰 X₂: Harga Nominal (K2)</span>
                        <span class="var-chip-x">🏷️ X₃: Diskon/Promo (K3)</span>
                        <span class="var-chip-x">⏳ X₄: Periode Promo (K4)</span>
                        <span class="var-chip-x">📋 X₅: Syarat & Ketentuan (K5)</span>
                        <span class="var-chip-x">📦 X₆: Info & Izin Produk (K6)</span>
                        <span class="var-chip-x">⭐ X₇: Klaim Kualitas (K7)</span>
                        <span class="var-chip-x">🔄 X₈: Visual-Caption (K8)</span>
                        <span class="var-chip-x" style="border-color:#818CF8; color:#C7D2FE;">🎨 CV: Objek, Dominasi, Warna & Teks (F1–F8)</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with col_vrel:
                st.markdown("""
                <div class="model-arrow-box">
                    <div style="font-size:0.75rem; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px;">
                        Alur Pengaruh
                    </div>
                    <div style="background:rgba(56, 189, 248, 0.15); border:1px solid #38BDF8; border-radius:8px; padding:6px 12px; margin-bottom:6px; width:100%;">
                        <span style="color:#38BDF8; font-weight:800; font-size:0.82rem;">Uji Simultan (Uji F)</span>
                    </div>
                    <div style="font-size:2rem; line-height:1; color:#38BDF8; margin:2px 0;">
                        ➔
                    </div>
                    <div style="background:rgba(16, 185, 129, 0.15); border:1px solid #10B981; border-radius:8px; padding:6px 12px; margin-top:2px; width:100%;">
                        <span style="color:#34D399; font-weight:800; font-size:0.82rem;">Uji Parsial (Uji t)</span>
                    </div>
                    <div style="font-size:0.77rem; color:#CBD5E1; margin-top:10px; line-height:1.35; background:rgba(30,41,59,0.5); padding:6px 8px; border-radius:6px; border:1px solid rgba(148,163,184,0.2);">
                        <b>Hipotesis (H₁):</b><br>
                        Karakteristik Visual ($X$) berpengaruh positif & signifikan terhadap Engagement ($Y$).
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with col_vy:
                st.markdown("""
                <div class="model-box-y">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="background:#059669; color:#FFF; font-size:0.75rem; font-weight:800; padding:2px 8px; border-radius:4px;">VARIABEL DEPENDEN (Y)</span>
                        <span style="color:#34D399; font-weight:700; font-size:0.82rem;">Instagram & Shopee</span>
                    </div>
                    <h3 style="margin:0 0 6px 0; color:#F8FAFC; font-size:1.15rem; font-weight:800;">📈 Engagement Media Sosial UMKM</h3>
                    <p style="font-size:0.82rem; color:#94A3B8; margin-bottom:12px; line-height:1.45;">
                        Tingkat keterlibatan dan respons audiens konsumen terhadap materi promosi produk UMKM pada media sosial & e-commerce:
                    </p>
                    <div style="display:flex; flex-wrap:wrap; gap:3px;">
                        <span class="var-chip-y">🚀 Y₁: Total Visible Engagement (TVE)</span>
                        <span class="var-chip-y">❤️ Y₂: Likes / Favorit (Suka)</span>
                        <span class="var-chip-y">💬 Y₃: Comments / Ulasan</span>
                        <span class="var-chip-y">🔄 Y₄: Shares (Dibagikan)</span>
                        <span class="var-chip-y">🔖 Y₅: Saves / Keranjang Belanja</span>
                        <span class="var-chip-y">⭐ Y₆: Rating Produk (1.0 – 5.0)</span>
                        <span class="var-chip-y">📊 Y₇: Engagement Rate (%)</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<hr style='margin:14px 0 10px 0; border:0; border-top:1px solid rgba(148,163,184,0.2);'>", unsafe_allow_html=True)
            
            # Sub-tab penjelasan di dalam expander
            tab_mod_persamaan, tab_mod_op, tab_mod_korelasi = st.tabs([
                "📐 Spesifikasi Model Ekonometrika & Regresi",
                "📋 Matriks Operasionalisasi Variabel (X & Y)",
                "⚡ Snapshot Korelasi Empiris (Data Saat Ini)"
            ])
            
            with tab_mod_persamaan:
                st.markdown(r"""
                **1. Persamaan Regresi Linier Berganda (Ordinary Least Squares - OLS):**
                $$\text{Engagement } (Y) = \beta_0 + \beta_1 X_1 + \beta_2 X_2 + \beta_3 X_3 + \beta_4 X_4 + \beta_5 X_5 + \beta_6 X_6 + \beta_7 X_7 + \beta_8 X_8 + \epsilon$$
                
                **2. Persamaan Operasional Penelitian (Target Utama: Total Visible Engagement):**
                $$\text{TVE}_i = \beta_0 + \beta_1 K_{1i} + \beta_2 K_{2i} + \beta_3 K_{3i} + \beta_4 K_{4i} + \beta_5 K_{5i} + \beta_6 K_{6i} + \beta_7 K_{7i} + \beta_8 K_{8i} + \epsilon_i$$
                
                *Keterangan Model Ekonometrika:*
                - $\text{TVE}_i$ = Total Visible Engagement postingan ke-$i$ ($\text{Likes} + \text{Comments}$).
                - $\beta_0$ = Konstanta intersep keterlibatan dasar.
                - $\beta_1 \dots \beta_8$ = Parameter koefisien pengaruh masing-masing indikator karakteristik visual produk.
                - $K_1 \dots K_8$ = Variabel dummy indikator visual ($1 = \text{Ada/Lengkap}$, $0 = \text{Tidak Ada/Disembunyikan}$).
                - $\epsilon_i$ = Nilai residu / error term penelitian.
                """)

            with tab_mod_op:
                mod_op_df = pd.DataFrame([
                    {"Variabel": "X1 (K1): Nama Produk", "Dimensi / Atribut": "Kejelasan identitas nama/merek komoditas pada gambar", "Skala": "Nominal (0/1)"},
                    {"Variabel": "X2 (K2): Pencantuman Harga", "Dimensi / Atribut": "Keterbukaan harga nominal rupiah vs DM for price (Anti-Gharar)", "Skala": "Nominal (0/1)"},
                    {"Variabel": "X3 (K3): Diskon/Promo", "Dimensi / Atribut": "Penawaran potongan harga khusus / promo transaksi", "Skala": "Nominal (0/1)"},
                    {"Variabel": "X4 (K4): Periode Promo", "Dimensi / Atribut": "Pencantuman batas kepastian waktu promo berlaku", "Skala": "Nominal (0/1)"},
                    {"Variabel": "X5 (K5): Syarat Promo (S&K)", "Dimensi / Atribut": "Keterbukaan klausula ketentuan transaksi tanpa jebakan", "Skala": "Nominal (0/1)"},
                    {"Variabel": "X6 (K6): Info & Spesifikasi", "Dimensi / Atribut": "Informasi detail bahan/varian/legalitas Halal & BPOM", "Skala": "Nominal (0/1)"},
                    {"Variabel": "X7 (K7): Klaim Kualitas", "Dimensi / Atribut": "Pernyataan keunggulan produk (Prinsip Amanah vs Tadlis)", "Skala": "Nominal (0/1)"},
                    {"Variabel": "X8 (K8): Visual-Caption", "Dimensi / Atribut": "Kongruensi kesesuaian gambar citra dengan narasi caption", "Skala": "Nominal (0/1)"},
                    {"Variabel": "X (CV): Fitur Komputer Vision", "Dimensi / Atribut": "Dominasi objek (F4), Posisi (F3), Wajah manusia (F7), Teks (F8)", "Skala": "Rasio / Nominal"},
                    {"Variabel": "Y1: TVE (Total Engagement)", "Dimensi / Atribut": "Total interaksi publik teramati langsung (Likes + Comments)", "Skala": "Rasio (Interaksi)"},
                    {"Variabel": "Y2: Likes / Suka", "Dimensi / Atribut": "Tingkat apresiasi visual audiens terhadap konten", "Skala": "Rasio (Interaksi)"},
                    {"Variabel": "Y3: Comments / Ulasan", "Dimensi / Atribut": "Tingkat diskusi publik, pertanyaan harga, dan umpan balik", "Skala": "Rasio (Interaksi)"},
                    {"Variabel": "Y4: Shares (Dibagikan)", "Dimensi / Atribut": "Frekuensi penyebaran dan viralitas konten", "Skala": "Rasio (Interaksi)"},
                    {"Variabel": "Y5: Saves / Keranjang", "Dimensi / Atribut": "Indikasi niat pembelian produk (Consideration/Wishlist)", "Skala": "Rasio (Interaksi)"},
                    {"Variabel": "Y6: Product Rating (⭐)", "Dimensi / Atribut": "Skor rating evaluasi produk konsumen Shopee (skala 1.0 - 5.0)", "Skala": "Rasio (Desimal)"},
                    {"Variabel": "Y7: Engagement Rate (%)", "Dimensi / Atribut": "Rasio interaksi relatif terhadap basis pengikut (Followers)", "Skala": "Rasio (%)"}
                ])
                st.dataframe(mod_op_df, use_container_width=True, hide_index=True)

            with tab_mod_korelasi:
                if len(df_posts) >= 2:
                    corr_quick = sm.calculate_correlations(df_posts, target_col="total_visible_engagement")
                    if not corr_quick.empty:
                        st.caption("⚡ *Korelasi Pearson empiris dihitung otomatis secara real-time dari data postingan aktif:*")
                        cols_sub_corr = ["Variabel", "Korelasi Pearson (r)", "Arah", "Kekuatan Hubungan", "Signifikansi (alpha 5%)"]
                        valid_sub_corr = [c for c in cols_sub_corr if c in corr_quick.columns]
                        st.dataframe(corr_quick[valid_sub_corr], use_container_width=True, hide_index=True)
                        st.info("💡 Untuk pengujian hipotesis regresi OLS, uji parsial t-test, dan koefisien determinasi ($R^2$) lengkap, silakan buka **Tab 📊 Analisis Statistik (Bab 4)**.")
                    else:
                        st.info("Korelasi belum dapat dihitung.")
                else:
                    st.info("Dibutuhkan minimal 2 postingan sampel untuk memunculkan korelasi empiris.")

        st.write("")
        # Filter interaktif
        c_f1, c_f2, c_f3 = st.columns(3)
        with c_f1:
            filter_sample = st.selectbox(
                "Filter Kelayakan Sampel (Purposive Sampling):",
                ["Semua Postingan", "Hanya Sampel Valid (Lolos I1-I7)", "Hanya Postingan Gugur (Eksklusi)"]
            )
        with c_f2:
            filter_k2 = st.selectbox("Filter Indikator K2 (Pencantuman Harga):", ["Semua", "Ada Harga (K2=1)", "Tanpa Harga / DM (K2=0)"])
        with c_f3:
            filter_k3 = st.selectbox("Filter Indikator K3 (Diskon/Promo):", ["Semua", "Ada Diskon (K3=1)", "Tanpa Diskon (K3=0)"])
            
        filtered_df = df_posts.copy()
        
        # Filter status sampel
        if "is_sample_valid" in filtered_df.columns:
            if filter_sample == "Hanya Sampel Valid (Lolos I1-I7)":
                filtered_df = filtered_df[filtered_df["is_sample_valid"] == 1]
            elif filter_sample == "Hanya Postingan Gugur (Eksklusi)":
                filtered_df = filtered_df[filtered_df["is_sample_valid"] == 0]

        if filter_k2 == "Ada Harga (K2=1)":
            filtered_df = filtered_df[filtered_df["k2_harga"] == 1]
        elif filter_k2 == "Tanpa Harga / DM (K2=0)":
            filtered_df = filtered_df[filtered_df["k2_harga"] == 0]
            
        if filter_k3 == "Ada Diskon (K3=1)":
            filtered_df = filtered_df[filtered_df["k3_diskon"] == 1]
        elif filter_k3 == "Tanpa Diskon (K3=0)":
            filtered_df = filtered_df[filtered_df["k3_diskon"] == 0]
            
        # Tabel Utama
        cols_display = [
            "id", "umkm_name", "post_title", "platform", "post_date",
            "is_sample_valid", "sampling_notes",
            "total_visible_engagement", "likes", "comments", "product_rating", "engagement_rate",
            "k1_nama_produk", "k2_harga", "k3_diskon", "k4_periode_promo",
            "k5_syarat_promo", "k6_info_produk", "k7_klaim", "k8_visual_caption",
            "islamic_compliance_score", "consumer_protection_score"
        ]
        valid_cols_disp = [c for c in cols_display if c in filtered_df.columns]
        st.dataframe(filtered_df[valid_cols_disp], use_container_width=True)
        
        # Opsi Hapus
        with st.expander("🗑️ Manajemen & Penghapusan Data"):
            col_del1, col_del2 = st.columns(2)
            with col_del1:
                del_id = st.number_input("Hapus Postingan Berdasarkan ID:", min_value=1, step=1)
                if st.button("Hapus Postingan Ini", type="secondary"):
                    db.delete_post(del_id)
                    st.success(f"Postingan ID #{del_id} berhasil dihapus.")
                    st.rerun()
            with col_del2:
                if st.button("Reset Database ke Contoh Semula", type="secondary"):
                    db.clear_all_posts()
                    db.seed_sample_data()
                    st.success("Database berhasil di-reset dengan sampel awal!")
                    st.rerun()

# ==========================================
# TAB 3: ANALISIS STATISTIK & EKONOMETRIKA (BAB 4)
# ==========================================
with tab_statistics:
    st.markdown('<div class="main-title">📊 Analisis Statistik & Ekonometrika (Bab 4 Pembahasan TA)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Uji empiris hubungan karakteristik visual (K1–K8) terhadap Total Visible Engagement (TVE = Likes + Comments).</div>', unsafe_allow_html=True)
    
    df_stat_all = db.get_all_posts()
    
    # Toggle Penggunaan Sampel Valid untuk Uji Ekonometrika Bab 4
    c_st_opt, c_st_info = st.columns([1.2, 2])
    with c_st_opt:
        only_valid_stat = st.checkbox(
            "🎯 Hanya Olah Data Sampel Valid (Lolos Purposive Sampling)",
            value=True,
            help="Sesuai metodologi Bab 3, pengujian empiris hanya dilakukan pada postingan yang lolos 7 Kriteria Inklusi dan bebas Kriteria Eksklusi."
        )
    with c_st_info:
        if "is_sample_valid" in df_stat_all.columns:
            n_valid = len(df_stat_all[df_stat_all["is_sample_valid"] == 1])
            n_total = len(df_stat_all)
            st.caption(f"ℹ️ Status Sampel: **{n_valid}** lolos kriteria dari total **{n_total}** postingan dalam database.")

    if only_valid_stat and "is_sample_valid" in df_stat_all.columns:
        df_stat = df_stat_all[df_stat_all["is_sample_valid"] == 1].copy()
    else:
        df_stat = df_stat_all.copy()

    if len(df_stat) < 2:
        st.info("Dibutuhkan minimal 2 postingan sampel valid untuk memunculkan analisis korelasi dan regresi statistik.")
    else:
        # Sub-tab: Judul Ringkas & Responsif agar TIDAK TERPOTONG!
        sub1, sub2, sub3, sub4 = st.tabs([
            "📊 Statistik Deskriptif",
            "🔗 Korelasi (Pearson & Spearman)",
            "⚖️ Uji Beda (t-Test)",
            "📈 Regresi Linier (OLS)"
        ])
        
        with sub1:
            st.subheader("Distribusi Frekuensi Indikator Karakteristik Visual")
            desc_dict = sm.get_descriptive_stats(df_stat)
            
            c_tb1, c_tb2 = st.columns([1, 1.2])
            with c_tb1:
                st.dataframe(desc_dict["indicator_summary"], use_container_width=True)
            with c_tb2:
                fig_freq = px.bar(
                    desc_dict["indicator_summary"],
                    x="Indikator",
                    y="Persentase (%)",
                    color="Persentase (%)",
                    color_continuous_scale="Blues",
                    title="Persentase Keberadaan Indikator K1 - K8 pada Postingan UMKM"
                )
                fig_freq.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_freq, use_container_width=True)
                
            st.subheader("Ringkasan Metrik Numerik (Engagement & Skor Kepatuhan)")
            st.dataframe(desc_dict["numeric_summary"], use_container_width=True)
            
        with sub2:
            st.subheader("Uji Hubungan Korelasi antara Karakteristik Visual dengan Total Visible Engagement (TVE)")
            corr_df = sm.calculate_correlations(df_stat, target_col="total_visible_engagement")
            st.dataframe(corr_df, use_container_width=True)
            
            if not corr_df.empty:
                fig_corr = px.bar(
                    corr_df,
                    x="Variabel",
                    y="Korelasi Pearson (r)",
                    color="Korelasi Pearson (r)",
                    color_continuous_scale="RdBu_r",
                    range_color=[-1, 1],
                    title="Koefisien Korelasi Pearson terhadap Total Visible Engagement"
                )
                fig_corr.add_hline(y=0, line_dash="dash", line_color="gray")
                fig_corr.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_corr, use_container_width=True)
                
            st.info("""
            💡 **Interpretasi Akademis untuk Skripsi:**
            - **Koefisien Positif (+):** Karakteristik visual tersebut berhubungan searah dengan peningkatan jumlah interaksi publik (Likes & Comments).
            - **Koefisien Negatif (-):** Keberadaan karakteristik visual tersebut cenderung menurunkan minat interaksi audiens.
            - **Nilai p-value < 0.05:** Hubungan terbukti **signifikan secara statistik** pada taraf signifikansi 5%.
            """)
            
        with sub3:
            st.subheader("Uji Beda Rata-rata Total Visible Engagement (Group Comparison)")
            st.markdown("Membandingkan apakah terdapat perbedaan Total Visible Engagement (Likes + Comments) yang signifikan antara postingan yang **menerapkan** indikator vs yang **tidak menerapkan**.")
            
            comp_df = sm.calculate_group_comparisons(df_stat, target_col="total_visible_engagement")
            st.dataframe(comp_df, use_container_width=True)
            
            target_metric = "total_visible_engagement" if "total_visible_engagement" in df_stat.columns else "engagement_rate"
            metric_label = "Total Visible Engagement (Interaksi)" if target_metric == "total_visible_engagement" else "Engagement Rate (%)"
            fig_box = px.box(
                df_stat,
                x="k2_harga",
                y=target_metric,
                color="k2_harga",
                labels={"k2_harga": "Indikator K2 (Harga Dicantumkan)", target_metric: metric_label},
                title="Perbandingan Sebaran Total Visible Engagement: Ada Harga (1) vs Tanpa Harga / DM (0)"
            )
            st.plotly_chart(fig_box, use_container_width=True)
            
        with sub4:
            st.subheader("Estimasi Regresi Linier Berganda (OLS)")
            st.markdown(r"$$\text{Total Visible Engagement} = \beta_0 + \beta_1 K_1 + \beta_2 K_2 + \beta_3 K_3 + \beta_4 K_4 + \beta_5 K_5 + \beta_6 K_6 + \beta_7 K_7 + \beta_8 K_8 + e$$")
            
            reg_res = sm.run_ols_regression(df_stat, target_col="total_visible_engagement")
            if reg_res["status"] == "error":
                st.warning(f"⚠️ {reg_res['message']}")
            else:
                c_rg1, c_rg2 = st.columns(2)
                c_rg1.metric("Koefisien Determinasi (R²)", f"{reg_res['r_squared']*100:.2f}%", help="Persentase variasi Total Visible Engagement yang mampu dijelaskan oleh indikator visual")
                c_rg2.metric("Adjusted R²", f"{reg_res['adj_r_squared']*100:.2f}%")
                
                st.dataframe(reg_res["coefficients_table"], use_container_width=True)
                st.caption(f"Jumlah sampel yang diestimasi: {reg_res['n_samples']} postingan.")

# ==========================================
# TAB 4: TINJAUAN FIQH & HUKUM KONSUMEN
# ==========================================
with tab_sharia_law:
    st.markdown('<div class="main-title">⚖️ Tinjauan Fiqh Muamalah & Hukum Perlindungan Konsumen</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Kerangka teori dan analisis kritis untuk Bab 2 dan Bab 5 naskah Tugas Akhir.</div>', unsafe_allow_html=True)
    
    col_fiqh, col_hukum = st.columns(2)
    
    with col_fiqh:
        st.markdown("""
        ### 🕌 Perspektif Ekonomi Islam (Fiqh Muamalah)
        
        #### 1. Larangan Gharar dalam Pencantuman Harga (K2)
        - **Prinsip Utama:** Objek akad dan harga (*tsaman*) harus jelas (*ma'lum*) saat penawaran dilakukan.
        - **Praktik UMKM 'DM for Price':** Menyembunyikan harga dan mewajibkan calon pembeli mengirim pesan privat (*DM*) berpotensi menimbulkan *gharar khafi* (ketidakpastian terselubung) dan asimetri informasi yang merugikan pembeli.
        - **Dalil & Kaidah Fiqh:**
          > *"Rasulullah SAW melarang jual beli hashah (melempar batu) dan jual beli gharar."* (HR. Muslim No. 1513)
        
        #### 2. Larangan Tadlis dan Ghasysy pada Klaim Produk (K7)
        - Menampilkan klaim berlebihan (*overclaiming*) seperti "Terenak di Dunia", "100% Manjur", atau mencantumkan klaim "Halal" tanpa sertifikasi resmi tergolong dalam perbuatan *tadlis* (pengelabuan) dan *kizhb* (kebohongan) yang diharamkan.
        
        #### 3. Kejelasan Objek Jual Beli (*Ma'qud 'Alaih*) (K1 & K6)
        - Foto produk yang menampilkan visual asli tanpa manipulasi pencahayaan berlebihan memenuhi prinsip *Amanah* dan *Shiddiq*, memastikan pembeli mendapatkan hak khiyar yang adil.
        
        #### 4. Transparansi Akad Promo (K3, K4, K5)
        - Promo diskon tidak boleh menggunakan strategi diskon semu (*fake discount* / mark-up harga sebelum diskon) karena menyerupai manipulasi harga (*najasy*).
        """)
        
    with col_hukum:
        st.markdown("""
        ### 🛡️ Perspektif Perlindungan Konsumen Digital
        
        #### 1. Hak Konsumen atas Informasi yang Jelas & Jujur
        - **UU No. 8 Tahun 1999 Pasal 4 huruf c:**
          > *"Hak atas informasi yang benar, jelas, dan jujur mengenai kondisi dan jaminan barang dan/atau jasa."*
        - Kewajiban pelaku usaha (Pasal 7 huruf b) menjamin bahwa harga yang tertera tidak disembunyikan.
        
        #### 2. Larangan Promosi Menyesatkan (Deceptive Advertising)
        - **Pasal 9 & 10 UUPK No. 8/1999:**
          - Pelaku usaha dilarang menawarkan barang dengan menyatakan seolah-olah barang telah memenuhi standar tertentu yang sebenarnya tidak dimiliki.
          - Larangan menawarkan potongan harga semu (*misleading discount*) yang tidak sesuai fakta.
        
        #### 3. Klausula Baku dan Syarat Promo Tersembunyi (K5)
        - **Pasal 18 UUPK:**
          - Melarang pencantuman klausula baku yang letak atau bentuknya sulit dilihat atau tidak dapat dibaca secara jelas (seperti teks S&K ukuran sangat kecil / *dark pattern*).
          
        #### 4. Keterkaitan dengan Perdagangan Melalui Sistem Elektronik (PMSE)
        - **PP No. 71 Tahun 2019 & Permendag No. 31 Tahun 2023:**
          - Pedagang di media sosial wajib menampilkan identitas barang, legalitas perizinan, dan harga secara transparan kepada konsumen publik.
        """)

# ==========================================
# TAB 5: EKSPOR DATA & PANDUAN TA
# ==========================================
with tab_export:
    st.markdown('<div class="main-title">📥 Ekspor Data Siap Olah & Pedoman Tugas Akhir</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Unduh dataset penelitian untuk diolah di Gretl, SPSS, SmartPLS, atau disalin ke naskah skripsi Anda.</div>', unsafe_allow_html=True)
    
    df_all = db.get_all_posts()
    
    c_dl1, c_dl2 = st.columns(2)
    
    with c_dl1:
        st.subheader("1. Unduh Dataset Penelitian (Excel / CSV)")
        
        buffer_excel = io.BytesIO()
        with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
            df_all.to_excel(writer, index=False, sheet_name="Data_Penelitian_TA")
            
            coding_cols = [
                "id", "followers", "likes", "comments", "total_visible_engagement", "shares", "saves", "product_rating", "engagement_rate",
                "k1_nama_produk", "k2_harga", "k3_diskon", "k4_periode_promo",
                "k5_syarat_promo", "k6_info_produk", "k7_klaim", "k8_visual_caption",
                "cv_brightness", "cv_contrast", "cv_text_density", "cv_face_detected",
                "islamic_compliance_score", "consumer_protection_score"
            ]
            valid_coding = [c for c in coding_cols if c in df_all.columns]
            df_all[valid_coding].to_excel(writer, index=False, sheet_name="Coding_SPSS_Gretl")
            
        st.download_button(
            label="📊 Download Dataset Lengkap (.xlsx Excel)",
            data=buffer_excel.getvalue(),
            file_name="dataset_ta_karakteristik_visual_umkm.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        csv_data = df_all.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download Dataset CSV (.csv)",
            data=csv_data,
            file_name="dataset_ta_karakteristik_visual_umkm.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.markdown("""
        **Petunjuk Import ke Software Analisis:**
        - **Gretl:** Buka Gretl -> *File* -> *Open Data* -> *User File* -> pilih file `.csv` atau `.xlsx`. Variabel `total_visible_engagement` sebagai variabel dependen ($Y$), dan `k1` s.d `k8` sebagai variabel independen ($X$).
        - **SPSS:** Buka SPSS -> *File* -> *Open* -> *Data* -> sheet `Coding_SPSS_Gretl`.
        """)

    with c_dl2:
        st.subheader("2. Matriks Operasionalisasi Variabel Skripsi")
        
        op_data = pd.DataFrame([
            {"Variabel": "Y: Total Visible Engagement (TVE)", "Skala": "Rasio (Jumlah Interaksi)", "Definisi": "Total interaksi publik yang terlihat langsung pada postingan = Likes + Comments"},
            {"Variabel": "Y (Alt): Engagement Rate", "Skala": "Rasio (%)", "Definisi": "Rasio keterlibatan relatif audiens = (Likes + Comments + Shares + Saves) / Followers * 100%"},
            {"Variabel": "X1 (K1): Nama Produk", "Skala": "Nominal (0/1)", "Definisi": "Kejelasan identitas nama/merek komoditas pada postingan"},
            {"Variabel": "X2 (K2): Harga", "Skala": "Nominal (0/1)", "Definisi": "Keterbukaan harga nominal rupiah vs disembunyikan (DM for price)"},
            {"Variabel": "X3 (K3): Diskon/Promo", "Skala": "Nominal (0/1)", "Definisi": "Adanya penawaran potongan harga/promo khusus"},
            {"Variabel": "X4 (K4): Periode Promo", "Skala": "Nominal (0/1)", "Definisi": "Pencantuman batas waktu berlakunya promo"},
            {"Variabel": "X5 (K5): Syarat Promo", "Skala": "Nominal (0/1)", "Definisi": "Keterbukaan syarat & ketentuan (S&K) transaksi"},
            {"Variabel": "X6 (K6): Info Produk", "Skala": "Nominal (0/1)", "Definisi": "Informasi spesifikasi bahan/manfaat/izin Halal/BPOM"},
            {"Variabel": "X7 (K7): Klaim", "Skala": "Nominal (0/1)", "Definisi": "Keberadaan klaim keunggulan atau klaim superlatif produk"},
            {"Variabel": "X8 (K8): Visual-Caption", "Skala": "Nominal (0/1)", "Definisi": "Kongruensi/keselarasan antara visual gambar dengan teks caption"}
        ])
        st.dataframe(op_data, use_container_width=True)

    # ── BAGIAN 3: OPERASIONALISASI PURPOSIVE SAMPLING (BAB 3 METODOLOGI PENELITIAN) ──
    st.markdown("---")
    st.subheader("3. Operasionalisasi Kriteria Purposive Sampling (Bab 3 Metodologi Penelitian)")
    st.caption("Matriks definisi operasional penentuan sampel penelitian untuk disalin ke naskah skripsi Bab 3.")

    c_m_inc, c_m_exc = st.columns(2)
    with c_m_inc:
        st.markdown("##### 🟢 7 Kriteria Inklusi ($I_1 - I_7$):")
        inc_rows = []
        for code, info in sc.INCLUSION_CRITERIA.items():
            inc_rows.append({
                "Kode": code,
                "Kriteria Inklusi": info["title"],
                "Definisi Operasional": info["desc"]
            })
        st.dataframe(pd.DataFrame(inc_rows), use_container_width=True, hide_index=True)

    with c_m_exc:
        st.markdown("##### 🔴 9 Kriteria Eksklusi ($E_1 - E_9$):")
        exc_rows = []
        for code, info in sc.EXCLUSION_CRITERIA.items():
            exc_rows.append({
                "Kode": code,
                "Kriteria Eksklusi": info["title"],
                "Definisi Operasional": info["desc"]
            })
        st.dataframe(pd.DataFrame(exc_rows), use_container_width=True, hide_index=True)

