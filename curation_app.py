"""
curation_app.py
===============
Aplikasi Kurasi, Scraping & Pengelolaan Dataset 3.000 Postingan Instagram UMKM
untuk Penelitian Skripsi:
"Analisis Hubungan Karakteristik Visual Produk dengan Engagement pada Media Sosial UMKM
dalam Perspektif Ekonomi Islam dan Perlindungan Konsumen Digital"

Dibuat ramah pemula dengan visual interaktif, audit trail purposive sampling,
dan ekspor data otomatis ke Microsoft Excel dan CSV.
"""

import streamlit as st
import pandas as pd
import os
import json
import time
from datetime import datetime
from PIL import Image
import io

import database_manager as dbm
import sampling_filter as sf
import scraper_engine as se
import export_manager as em

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Kurasi & Scraping Dataset Instagram UMKM (TA)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inisialisasi Database jika belum ada
dbm.init_db()

# Custom CSS untuk tampilan profesional dan ramah pemula
st.markdown("""
<style>
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 4px;
    }
    .sub-header {
        font-size: 14px;
        color: #475569;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 16px;
        text-align: center;
    }
    .metric-val {
        font-size: 24px;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-label {
        font-size: 12px;
        color: #64748B;
        text-transform: uppercase;
        font-weight: 600;
    }
    .badge-layak {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .badge-eksklusi {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .badge-manual {
        background-color: #FEF08A;
        color: #854D0E;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# SIDEBAR: RINGKASAN PROGRES TARGET 3.000 DATA
# ─────────────────────────────────────────────────────────────
stats = dbm.get_post_statistics()
cfg = sf.load_config()
periode = cfg.get("periode_penelitian", {})
target_baku = cfg.get("target_penelitian", {}).get("target_sampel_valid", 3000)

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/instagram-new.png", width=64)
    st.title("Progres Skripsi")
    st.caption("Target: 3.000 Postingan Valid & Unik")
    
    # Progress Bar
    progres_ratio = min(1.0, stats["total_layak"] / target_baku) if target_baku else 0
    st.progress(progres_ratio)
    st.write(f"**Tercapai:** {stats['total_layak']} / {target_baku} ({stats['persentase_tercapai']}%)")
    st.write(f"**Sisa Kebutuhan:** :red[{stats['sisa_kebutuhan']} postingan]")

    st.divider()
    st.markdown("**Periode Penelitian:**")
    st.info(f"📅 **{periode.get('tanggal_mulai', '2026-01-01')}** s/d **{periode.get('tanggal_selesai', '2026-06-30')}**")

    st.markdown("**Status Kriteria:**")
    st.write(f"• Total Data Mentah: **{stats['total_postingan']}**")
    st.write(f"• Total URL Unik: **{stats['total_url_unik']}**")
    st.write(f"• Format Foto: **{stats['total_foto']}**")
    st.write(f"• Butuh Verifikasi Manual: **{stats['total_menunggu_verifikasi']}**")
    st.write(f"• Lolos Inklusi (Valid): **{stats['total_layak']}**")
    st.write(f"• Gugur Eksklusi: **{stats['total_eksklusi']}**")

    st.divider()
    st.caption("💡 Catatan: Target 3.000 mengacu pada data yang telah diverifikasi manual memenuhi kriteria inklusi, bukan sekadar jumlah link.")

# ─────────────────────────────────────────────────────────────
# HEADER UTAMA
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="main-header">Sistem Pengumpulan & Kurasi Dataset Instagram UMKM</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Penelitian Skripsi: Analisis Hubungan Karakteristik Visual Produk dengan Engagement pada Media Sosial UMKM dalam Perspektif Ekonomi Islam dan Perlindungan Konsumen Digital</div>', unsafe_allow_html=True)

# Kartu Metrik Ringkas
col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
with col_m1:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{stats["total_postingan"]}</div><div class="metric-label">Total Post Ditemukan</div></div>', unsafe_allow_html=True)
with col_m2:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{stats["total_foto"]}</div><div class="metric-label">Format Foto/Gambar</div></div>', unsafe_allow_html=True)
with col_m3:
    st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#B45309;">{stats["total_menunggu_verifikasi"]}</div><div class="metric-label">Perlu Verifikasi</div></div>', unsafe_allow_html=True)
with col_m4:
    st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#047857;">{stats["total_layak"]}</div><div class="metric-label">Lolos Inklusi (Valid)</div></div>', unsafe_allow_html=True)
with col_m5:
    st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#B91C1C;">{stats["sisa_kebutuhan"]}</div><div class="metric-label">Sisa Menuju 3.000</div></div>', unsafe_allow_html=True)

st.write("")

# ─────────────────────────────────────────────────────────────
# NAVIGASI TABS APLIKASI
# ─────────────────────────────────────────────────────────────
tab_scrape, tab_verify, tab_visual, tab_export, tab_guide = st.tabs([
    "📥 1. Pengumpulan Metadata (Scraper)",
    "🔍 2. Verifikasi Manual & Kurasi Visual",
    "🎨 3. Variabel Visual (Analisis Bab 4)",
    "💾 4. Ekspor Dataset (Excel & CSV)",
    "📖 5. Panduan Protokol & Batasan Instagram"
])

# =============================================================
# TAB 1: PENGUMPULAN METADATA POSTINGAN
# =============================================================
with tab_scrape:
    st.subheader("Pengumpulan Data Postingan Instagram UMKM")
    st.caption("Pilih metode pengumpulan data yang sesuai dengan protokol penelitian dan ketersediaan akses.")

    # Kotak Evaluasi Keterbatasan Metode
    with st.expander("ℹ️ Evaluasi Keterbatasan Scraping Tanpa Graph API (Wajib Dipahami Peneliti)", expanded=False):
        st.markdown("""
        **Transparansi Akademik Pengumpulan Data Instagram:**
        1. **Metode Shortcode/Link Postingan (Paling Stabil):** Mengambil data postingan publik langsung melalui URL (`/p/SHORTCODE/`). Metode ini **sangat akurat**, tidak memerlukan login akun, mengambil gambar kualitas penuh, dan tidak diblokir oleh Instagram jika diberi jeda wajar (3–7 detik).
        2. **Metode Daftar Feed Akun:** Instagram secara berkala mengunci endpoint profil publik (`api/v1/users/web_profile_info/`) dengan respon HTTP 401 Unauthorized untuk mencegah bot. Jika akun Anda terkena batasan ini, **gunakan metode input link postingan**.
        3. **Data Engagement:**
           - **Likes & Komentar:** Dapat dicatat secara sah jika postingan bersifat publik dan pemilik tidak menyembunyikan jumlah like.
           - **Shares & Saves:** **TIDAK TERSEDIA SECARA PUBLIK** pada Instagram. Data ini adalah metrik internal pribadi pemilik akun (*Instagram Creator Insights*). Kolom share/save akan dibiarkan kosong (NULL) dan ditandai "Tidak tersedia secara publik" demi menjaga integritas ilmiah (tidak mengarang angka nol).
        """)

    metode_input = st.radio(
        "Pilih Metode Sumber Input Data:",
        [
            "🔗 Input Daftar Link Postingan (Direkomendasikan & Sangat Stabil)",
            "📁 Input Daftar Akun UMKM dari File Excel / CSV",
            "🎯 Uji Coba Cepat 1 Link Postingan"
        ]
    )

    if "🎯 Uji Coba Cepat 1 Link Postingan" in metode_input:
        st.markdown("#### Uji Coba Metadata Satu Postingan")
        col_u1, col_u2 = st.columns([2, 1])
        with col_u1:
            input_url = st.text_input("Masukkan URL Postingan Instagram:", value="https://www.instagram.com/p/DZ9xP_AyYAM/", placeholder="https://www.instagram.com/p/...")
        with col_u2:
            input_kat = st.selectbox("Kategori Produk:", ["Kuliner / F&B", "Fashion Muslim", "Kerajinan / Kriya", "Kecantikan / Herbal", "Jasa / Lainnya"])

        if st.button("🚀 Tarik Metadata & Simpan ke Dataset", type="primary"):
            with st.spinner("Menghubungi server Instagram dan mengunduh gambar..."):
                res = se.fetch_single_post(input_url, kategori_produk=input_kat)
                if res.get("status") == "success":
                    st.success("Berhasil mengambil metadata postingan!")
                    d = res["data"]
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        if d.get("lokasi_file_gambar") and os.path.exists(d["lokasi_file_gambar"]):
                            st.image(d["lokasi_file_gambar"], caption=f"Shortcode: {d['shortcode']}", use_container_width=True)
                        elif d.get("link_gambar"):
                            st.image(d["link_gambar"], caption=f"Shortcode: {d['shortcode']}", use_container_width=True)
                        else:
                            st.warning("Gambar tidak dapat ditampilkan.")
                    with c2:
                        st.write(f"**Username:** @{d['username_ig']}")
                        st.write(f"**Tanggal Publikasi:** {d['tanggal_publikasi']}")
                        st.write(f"**Jenis Media:** {d['jenis_media']}")
                        st.write(f"**Likes:** {d['jumlah_likes']} ({d['status_likes']})")
                        st.write(f"**Komentar:** {d['jumlah_komentar']} ({d['status_komentar']})")
                        st.write(f"**Status Inklusi:** `{d['status_inklusi']}`")
                        st.write(f"**Catatan Otomatis:** {d['alasan_eksklusi'] or d['kriteria_belum_pasti']}")
                        st.caption(f"Tersimpan di database dengan ID: {d.get('id')}")
                    st.rerun()
                else:
                    st.error(f"Gagal mengambil metadata: {res.get('message')}")

    elif "🔗 Input Daftar Link Postingan" in metode_input:
        st.markdown("#### Input Sekaligus Banyak Link Postingan UMKM")
        st.write("Masukkan tautan postingan Instagram yang Anda kumpulkan dari akun UMKM objek penelitian.")

        tab_link_file, tab_link_paste = st.tabs(["📄 Unggah File Excel/CSV Link", "📝 Tempel (Paste) Teks Link"])

        link_list_to_process = []
        kategori_batch = "Kuliner / F&B"

        with tab_link_file:
            st.info("Format file: Kolom pertama berisi link postingan (`https://www.instagram.com/p/...`). Contoh file: `input_link_postingan.xlsx`")
            uploaded_file = st.file_uploader("Pilih file Excel (.xlsx) atau CSV (.csv):", type=["xlsx", "csv"], key="uploader_link")
            if uploaded_file:
                try:
                    if uploaded_file.name.endswith(".csv"):
                        df_upload = pd.read_csv(uploaded_file)
                    else:
                        df_upload = pd.read_excel(uploaded_file)
                    st.write("Pratinjau Data Unggahan:", df_upload.head(5))
                    # Cari kolom link
                    link_col = None
                    for c in df_upload.columns:
                        if "url" in c.lower() or "link" in c.lower() or "post" in c.lower():
                            link_col = c
                            break
                    if not link_col:
                        link_col = df_upload.columns[0]
                    link_list_to_process = df_upload[link_col].dropna().astype(str).tolist()
                    st.success(f"Ditemukan {len(link_list_to_process)} link postingan dari file.")
                except Exception as e_up:
                    st.error(f"Error membaca file: {e_up}")

        with tab_link_paste:
            paste_text = st.text_area(
                "Atau tempelkan daftar link di sini (satu link per baris):",
                placeholder="https://www.instagram.com/p/DZ9xP_AyYAM/\nhttps://www.instagram.com/p/...\n...",
                height=150
            )
            if paste_text.strip():
                p_lines = [l.strip() for l in paste_text.strip().split("\n") if l.strip().startswith("http")]
                if p_lines:
                    link_list_to_process = p_lines
                    st.write(f"Ditemukan **{len(link_list_to_process)}** link valid dari teks.")

        col_p1, col_p2 = st.columns([1, 1])
        with col_p1:
            kategori_batch = st.selectbox("Kategori Produk Default:", ["Kuliner / F&B", "Fashion Muslim", "Kerajinan / Kriya", "Kecantikan / Herbal", "Jasa / Lainnya"], key="kat_batch")
        with col_p2:
            delay_sec = st.slider("Jeda Waktu Aman per Postingan (Detik):", min_value=2, max_value=10, value=4, help="Penting untuk mencegah pemblokiran IP oleh Instagram")

        if st.button("🚀 Mulai Penarikan Data Massal", type="primary", disabled=len(link_list_to_process) == 0):
            prog_bar = st.progress(0.0)
            status_text = st.empty()
            log_container = st.empty()

            sukses_count = 0
            gagal_count = 0

            for i, l_url in enumerate(link_list_to_process):
                status_text.write(f"Memproses postingan [{i+1}/{len(link_list_to_process)}]: `{l_url}`")
                res = se.fetch_single_post(l_url, kategori_produk=kategori_batch)
                if res.get("status") == "success":
                    sukses_count += 1
                else:
                    gagal_count += 1

                prog_bar.progress((i + 1) / len(link_list_to_process))
                if i < len(link_list_to_process) - 1:
                    time.sleep(delay_sec)

            st.success(f"Selesai! Berhasil mengumpulkan: {sukses_count} postingan. Gagal: {gagal_count}.")
            st.rerun()

    elif "📁 Input Daftar Akun UMKM dari File" in metode_input:
        st.markdown("#### Input Daftar Akun UMKM")
        st.write("Membaca daftar akun UMKM dari file `input_akun_umkm.xlsx` atau `.csv`.")

        sample_account_path = os.path.join(os.path.dirname(__file__), "input_akun_umkm.xlsx")
        if os.path.exists(sample_account_path):
            df_akun = pd.read_excel(sample_account_path)
            st.write("Daftar Akun Terdaftar Saat Ini:", df_akun)
        else:
            st.warning("File input_akun_umkm.xlsx belum ditemukan.")

        col_ak1, col_ak2 = st.columns([2, 1])
        with col_ak1:
            user_target = st.text_input("Pilih Username UMKM yang Ingin Diproses:", value="basoaciakang", placeholder="nama_akun_umkm")
        with col_ak2:
            limit_post = st.number_input("Maksimal Postingan:", min_value=5, max_value=100, value=20)

        if st.button("🔍 Coba Tarik Postingan dari Akun", type="primary"):
            with st.spinner(f"Menghubungi profil @{user_target}..."):
                res_prof = se.process_umkm_profile_posts(user_target, max_posts=limit_post)
                if res_prof.get("status") == "success":
                    st.success(f"Berhasil menarik {res_prof.get('total_collected')} postingan dari @{user_target}!")
                    st.rerun()
                else:
                    st.warning(res_prof.get("message"))
                    st.info("💡 **Solusi Praktis Peneliti:** Karena Instagram membatasi listing akun publik, buka Instagram di browser laptop Anda, copy 10-30 link postingan dari akun tersebut, lalu tempelkan di tab **'Input Daftar Link Postingan'** di atas. Cara ini dijamin 100% aman dan berhasil!")

# =============================================================
# TAB 2: VERIFIKASI MANUAL & KURASI VISUAL
# =============================================================
with tab_verify:
    st.subheader("Verifikasi Manual Kelayakan Postingan (Purposive Sampling)")
    st.caption("Peneliti wajib memeriksa tampilan visual produk untuk memastikan Kriteria Inklusi I3 (Menampilkan Produk) dan I4 (Fungsi Promosi).")

    conn = dbm.get_connection()
    df_posts = pd.read_sql_query("SELECT * FROM dataset_posts ORDER BY id DESC", conn)
    conn.close()

    if df_posts.empty:
        st.info("Belum ada data postingan dalam database. Silakan jalankan penarikan data di Tab 1 terlebih dahulu.")
    else:
        # Filter status
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            filter_status = st.selectbox(
                "Filter Status Postingan:",
                ["Perlu Verifikasi Manual", "Lolos Inklusi", "Gugur Eksklusi", "Semua Postingan"]
            )
        
        if filter_status == "Semua Postingan":
            filtered_df = df_posts
        else:
            filtered_df = df_posts[df_posts["status_inklusi"] == filter_status]

        st.write(f"Menampilkan **{len(filtered_df)}** postingan:")

        if filtered_df.empty:
            st.success(f"Tidak ada postingan dengan status '{filter_status}'. Seluruh antrean telah terverifikasi!")
        else:
            # Dropdown pilih postingan
            post_options = [f"ID {row['id']} | {row['id_dataset']} | @{row['username_ig']} | {row['tanggal_publikasi'] or 'Tanpa Tanggal'}" for _, row in filtered_df.iterrows()]
            selected_option = st.selectbox("Pilih Postingan untuk Diperiksa:", post_options)

            selected_id = int(selected_option.split("|")[0].replace("ID", "").strip())
            row_data = filtered_df[filtered_df["id"] == selected_id].iloc[0]

            col_view_img, col_view_form = st.columns([1.1, 1.4], gap="large")

            # 1. TAMPILAN GAMBAR & METADATA
            with col_view_img:
                st.markdown("##### 🖼️ Tampilan Visual Postingan")
                img_path = row_data.get("lokasi_file_gambar")
                img_url = row_data.get("link_gambar")

                if img_path and os.path.exists(img_path):
                    st.image(img_path, caption=f"File: {os.path.basename(img_path)}", use_container_width=True)
                elif img_url:
                    st.image(img_url, caption=f"Gambar CDN Instagram", use_container_width=True)
                else:
                    st.warning("⚠️ File gambar tidak ditemukan secara lokal.")

                st.markdown(f"👉 **[Buka Postingan Asli di Instagram]({row_data['link_postingan']})**", unsafe_allow_html=True)

                st.markdown("##### 📋 Metadata Postingan")
                st.write(f"• **ID Dataset:** `{row_data['id_dataset']}`")
                st.write(f"• **Akun UMKM:** @{row_data['username_ig']}")
                st.write(f"• **Kategori:** {row_data['kategori_produk'] or '-'}")
                st.write(f"• **Tanggal Unggah:** {row_data['tanggal_publikasi'] or '-'}")
                st.write(f"• **Format Media:** `{row_data['jenis_media']}`")
                st.write(f"• **Likes:** {row_data['jumlah_likes']} ({row_data['status_likes']})")
                st.write(f"• **Komentar:** {row_data['jumlah_komentar']} ({row_data['status_komentar']})")
                st.write(f"• **Share:** {row_data['jumlah_share'] if pd.notnull(row_data['jumlah_share']) else 'Tidak tersedia secara publik'}")

                with st.expander("📝 Teks Caption Postingan", expanded=True):
                    st.write(row_data.get("caption") or "*(Tanpa caption)*")

            # 2. FORMULIR VERIFIKASI PENELITI
            with col_view_form:
                st.markdown("##### ✍️ Formulir Verifikasi Purposive Sampling")
                
                with st.form(key=f"form_verify_{selected_id}"):
                    # Kriteria Inklusi I3: Menampilkan Produk
                    menampilkan_produk = st.radio(
                        "1. Apakah gambar secara eksplisit menampilkan produk UMKM? (I3)",
                        ["Ya", "Tidak", "Belum Jelas"],
                        index=0 if row_data.get("menampilkan_produk") == "Ya" else (1 if row_data.get("menampilkan_produk") == "Tidak" else 2)
                    )

                    keterangan_produk = st.text_input(
                        "Keterangan/Nama Produk yang Terlihat:",
                        value=row_data.get("keterangan_produk") or "",
                        placeholder="Contoh: Paket Baso Aci Urat + Cuanki"
                    )

                    # Kriteria Inklusi I4: Fungsi Promosi
                    fungsi_promosi = st.radio(
                        "2. Apakah postingan memiliki fungsi promosi komersial? (I4)",
                        ["Ya", "Tidak"],
                        index=0 if row_data.get("fungsi_promosi") == "Ya" else 1
                    )

                    # Konten Asli / Repost
                    konten_asli = st.radio(
                        "3. Jenis Konten Publikasi:",
                        ["Konten Asli", "Repost Pelanggan / UGC", "Belum Terverifikasi"],
                        index=0 if row_data.get("konten_asli_atau_repost") == "Konten Asli" else (1 if row_data.get("konten_asli_atau_repost") == "Repost Pelanggan / UGC" else 2)
                    )

                    # Kelayakan Visual
                    kelayakan_visual = st.radio(
                        "4. Kelayakan Kualitas Citra untuk Analisis Visual: (I6)",
                        ["Layak", "Tidak Layak"],
                        index=0 if row_data.get("kelayakan_analisis_visual") == "Layak" else 1
                    )

                    st.markdown("---")
                    # KEPUTUSAN FINAL
                    status_keputusan = st.radio(
                        "⭐ KEPUTUSAN AKHIR SELEKSI:",
                        ["Lolos Inklusi", "Gugur Eksklusi", "Perlu Verifikasi Manual"],
                        index=0 if row_data.get("status_inklusi") == "Lolos Inklusi" else (1 if row_data.get("status_inklusi") == "Gugur Eksklusi" else 2)
                    )

                    # Alasan Eksklusi jika Gugur
                    alasan_pilihan = st.selectbox(
                        "Alasan Eksklusi (Wajib dipilih jika Gugur Eksklusi):",
                        [
                            "None (Bukan Eksklusi)",
                            "E1: Format Video / Reels / TikTok Video",
                            "E2: Ucapan Hari Besar Tanpa Produk",
                            "E3: Konten Quote / Kata Motivasi Tanpa Produk",
                            "E4: Pengumuman Internal Operasional Tanpa Produk",
                            "E5: Repost Pelanggan Murni (UGC)",
                            "E6: Hanya Menampilkan Pemilik Tanpa Produk",
                            "E7: Giveaway Tanpa Relevansi Produk",
                            "E8: Gambar Tidak Tersedia / Tautan Rusak",
                            "E9: Data Engagement Wajib Tidak Tersedia",
                            "Di luar periode penelitian (Januari - Juni 2026)",
                            "Lainnya (Tulis di catatan)"
                        ],
                        index=0
                    )

                    catatan_pemeriksa = st.text_area(
                        "Catatan Tambahan Pemeriksa:",
                        value=row_data.get("catatan_pemeriksa") or "",
                        placeholder="Contoh: Produk terlihat di tengah meja, caption memuat harga Rp 25.000."
                    )

                    submit_verify = st.form_submit_button("💾 Simpan Hasil Verifikasi Postingan Ini", type="primary")

                    if submit_verify:
                        alasan_final = ""
                        if status_keputusan == "Gugur Eksklusi":
                            alasan_final = alasan_pilihan if alasan_pilihan != "None (Bukan Eksklusi)" else "Gugur kriteria inklusi"

                        updates = {
                            "status_inklusi": status_keputusan,
                            "alasan_eksklusi": alasan_final,
                            "menampilkan_produk": menampilkan_produk,
                            "keterangan_produk": keterangan_produk,
                            "fungsi_promosi": fungsi_promosi,
                            "konten_asli_atau_repost": konten_asli,
                            "kelayakan_analisis_visual": kelayakan_visual,
                            "kriteria_belum_pasti": "" if status_keputusan != "Perlu Verifikasi Manual" else "Menunggu telaah lanjut",
                            "catatan_pemeriksa": catatan_pemeriksa,
                            "status_pemeriksaan_akhir": "Final"
                        }
                        dbm.update_manual_verification(selected_id, updates)
                        st.success(f"Status postingan ID {selected_id} ({row_data['id_dataset']}) berhasil disimpan sebagai: {status_keputusan}!")
                        time.sleep(0.8)
                        st.rerun()

# =============================================================
# TAB 3: VARIABEL KARAKTERISTIK VISUAL (BAB 4 SKRIPSI)
# =============================================================
with tab_visual:
    st.subheader("Variabel Karakteristik Visual Produk untuk Analisis Ekonometrika (Bab 4)")
    st.caption("Pemberian label dan pengamatan karakteristik visual untuk analisis hubungan dengan engagement. Data mentah tetap dipisahkan dari variabel turunan.")

    conn = dbm.get_connection()
    df_layak = pd.read_sql_query("SELECT * FROM dataset_posts WHERE status_inklusi = 'Lolos Inklusi' ORDER BY id ASC", conn)
    conn.close()

    if df_layak.empty:
        st.info("Belum ada postingan yang berstatus 'Lolos Inklusi'. Lakukan verifikasi manual pada Tab 2 terlebih dahulu.")
    else:
        st.write(f"Terdapat **{len(df_layak)}** postingan yang telah lolos kriteria inklusi dan siap dianalisis karakteristik visualnya:")

        selected_vis_opt = st.selectbox(
            "Pilih Postingan untuk Diberi Variabel Visual:",
            [f"ID {r['id']} | {r['id_dataset']} | {r['keterangan_produk'] or r['username_ig']}" for _, r in df_layak.iterrows()]
        )
        vis_id = int(selected_vis_opt.split("|")[0].replace("ID", "").strip())
        vis_row = df_layak[df_layak["id"] == vis_id].iloc[0]

        c_vimg, c_vform = st.columns([1, 1.5], gap="large")
        with c_vimg:
            if vis_row.get("lokasi_file_gambar") and os.path.exists(vis_row["lokasi_file_gambar"]):
                st.image(vis_row["lokasi_file_gambar"], caption=vis_row["id_dataset"], use_container_width=True)
            elif vis_row.get("link_gambar"):
                st.image(vis_row["link_gambar"], caption=vis_row["id_dataset"], use_container_width=True)

        with c_vform:
            with st.form(key=f"form_vis_{vis_id}"):
                st.markdown("##### Variabel Visual Produk")
                v_warna = st.text_input("Warna Dominan Gambar / Produk:", value=vis_row.get("warna_dominan") or "Merah / Cokelat")
                
                c_v1, c_v2 = st.columns(2)
                with c_v1:
                    v_bright = st.slider("Kecerahan Gambar (0 - 100):", min_value=0.0, max_value=100.0, value=float(vis_row.get("kecerahan_brightness") or 65.0))
                    v_komposisi = st.selectbox("Komposisi Visual:", ["Rule of Thirds", "Center / Simetris", "Flat Lay (Atas)", "Close-Up / Makro"], index=1)
                    v_manusia = st.selectbox("Keberadaan Manusia (Model/Talent):", ["Tidak Ada", "Ada Wajah Model", "Ada Bagian Tangan/Tubuh"], index=0)
                    v_kejelasan = st.selectbox("Kejelasan Tampilan Produk:", ["Sangat Jelas / Menonjol", "Cukup Jelas", "Kurang Jelas / Tertutup Objek Lain"], index=0)
                with c_v2:
                    v_kontras = st.slider("Kontras Visual (0 - 100):", min_value=0.0, max_value=100.0, value=float(vis_row.get("kontras_visual") or 55.0))
                    v_jumlah_prod = st.number_input("Jumlah Produk yang Terlihat:", min_value=1, max_value=20, value=int(vis_row.get("jumlah_produk_terlihat") or 1))
                    v_teks_promo = st.selectbox("Teks Promosi pada Gambar:", ["Ada (Teks Promo Menonjol)", "Tidak Ada (Hanya Gambar Murni)"], index=0)
                    v_harga = st.selectbox("Pencantuman Harga Nominal pada Visual/Caption:", ["Harga Dicantumkan Transparan", "Harga Disembunyikan (DM for Price)"], index=0)

                v_kualitas = st.selectbox("Kualitas Gambar:", ["Tinggi / HD", "Sedang", "Rendah / Buram"], index=0)

                submit_vis = st.form_submit_button("💾 Simpan Karakteristik Visual", type="primary")
                if submit_vis:
                    v_dict = {
                        "warna_dominan": v_warna,
                        "kecerahan_brightness": v_bright,
                        "kontras_visual": v_kontras,
                        "komposisi_visual": v_komposisi,
                        "jumlah_produk_terlihat": v_jumlah_prod,
                        "keberadaan_manusia": v_manusia,
                        "kejelasan_tampilan_produk": v_kejelasan,
                        "teks_promosi_pada_gambar": v_teks_promo,
                        "keberadaan_harga_info": v_harga,
                        "kualitas_gambar": v_kualitas
                    }
                    dbm.update_visual_features(vis_id, v_dict)
                    st.success("Variabel karakteristik visual berhasil disimpan untuk analisis ekonometrika!")
                    st.rerun()

# =============================================================
# TAB 4: EKSPOR DATASET & LAPORAN AUDIT
# =============================================================
with tab_export:
    st.subheader("Ekspor Dataset Penelitian ke Microsoft Excel & CSV")
    st.write("Sesuai protokol penelitian, sistem menghasilkan 4 file dataset utama dan 1 laporan ringkasan seleksi purposive sampling:")

    c_exp1, c_exp2 = st.columns([1, 1])
    with c_exp1:
        st.markdown("""
        **Daftar File Keluaran:**
        1. 📗 `dataset_mentah.xlsx` : Seluruh data yang berhasil dikumpulkan sebelum seleksi.
        2. 📗 `dataset_layak.xlsx` : Postingan yang lolos kriteria inklusi dan verifikasi manual.
        3. 📕 `dataset_eksklusi.xlsx` : Postingan yang ditolak beserta rincian alasannya.
        4. 📄 `dataset_layak.csv` : Salinan dataset final dalam format CSV (UTF-8 BOM).
        5. 📘 `laporan_ringkasan_seleksi.xlsx` : Laporan tabel tahapan seleksi purposive sampling.
        """)

    with c_exp2:
        if st.button("🔄 Generate & Perbarui Seluruh File Ekspor Sekarang", type="primary"):
            with st.spinner("Membuat file Excel dan CSV..."):
                res_exp = em.export_all_datasets()
                st.success(f"Berhasil mengekspor 5 file ke folder `{res_exp['output_folder']}`!")
                st.write(f"• Data Mentah: **{res_exp['counts']['total_mentah']}** baris")
                st.write(f"• Data Lolos Inklusi: **{res_exp['counts']['total_layak']}** baris")
                st.write(f"• Data Eksklusi: **{res_exp['counts']['total_eksklusi']}** baris")

    st.divider()

    # Tombol Download Langsung untuk Peneliti
    st.markdown("##### 📥 Unduh File Hasil Ekspor:")
    export_folder = os.path.join(os.path.dirname(__file__), "hasil_ekspor")
    
    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    with col_d1:
        f_mentah = os.path.join(export_folder, "dataset_mentah.xlsx")
        if os.path.exists(f_mentah):
            with open(f_mentah, "rb") as f:
                st.download_button("📗 Unduh dataset_mentah.xlsx", data=f.read(), file_name="dataset_mentah.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with col_d2:
        f_layak = os.path.join(export_folder, "dataset_layak.xlsx")
        if os.path.exists(f_layak):
            with open(f_layak, "rb") as f:
                st.download_button("📗 Unduh dataset_layak.xlsx", data=f.read(), file_name="dataset_layak.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with col_d3:
        f_eksklusi = os.path.join(export_folder, "dataset_eksklusi.xlsx")
        if os.path.exists(f_eksklusi):
            with open(f_eksklusi, "rb") as f:
                st.download_button("📕 Unduh dataset_eksklusi.xlsx", data=f.read(), file_name="dataset_eksklusi.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with col_d4:
        f_csv = os.path.join(export_folder, "dataset_layak.csv")
        if os.path.exists(f_csv):
            with open(f_csv, "rb") as f:
                st.download_button("📄 Unduh dataset_layak.csv", data=f.read(), file_name="dataset_layak.csv", mime="text/csv")

    st.write("")
    f_sum = os.path.join(export_folder, "laporan_ringkasan_seleksi.xlsx")
    if os.path.exists(f_sum):
        with open(f_sum, "rb") as f:
            st.download_button("📘 Unduh laporan_ringkasan_seleksi.xlsx", data=f.read(), file_name="laporan_ringkasan_seleksi.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # Pratinjau Tabel Ekspor
    with st.expander("👀 Pratinjau Data Lolos Inklusi (dataset_layak.xlsx)", expanded=False):
        if os.path.exists(f_layak):
            df_preview = pd.read_excel(f_layak)
            st.dataframe(df_preview, use_container_width=True)

# =============================================================
# TAB 5: PANDUAN PROTOKOL & METODOLOGI
# =============================================================
with tab_guide:
    st.subheader("Panduan Protokol Metodologi Penelitian & Keterbatasan Akses")
    
    st.markdown("""
    ### A. Definisi Operasional 7 Kriteria Inklusi (I1 – I7)
    1. **I1 (Akun UMKM Terpilih):** Postingan berasal dari akun resmi pelaku UMKM yang telah ditetapkan sebagai populasi/sampel penelitian.
    2. **I2 (Format Gambar Statis):** Berupa single photo atau multi-slide carousel photo pada feed, bukan format video/reels.
    3. **I3 (Menampilkan Produk Dagang):** Konten visual memperlihatkan secara jelas produk fisik yang diperjualbelikan UMKM.
    4. **I4 (Fungsi Promosi/Pemasaran):** Bertujuan komersial (penawaran menu, info diskon, ajakan order, pengenalan katalog).
    5. **I5 (Periode Observasi):** Dipublikasikan dalam rentang **Januari 2026 s/d Juni 2026**.
    6. **I6 (Karakteristik Visual Teramati):** File gambar dapat diunduh, tidak rusak/korup, dan elemen visualnya dapat diekstraksi.
    7. **I7 (Data Engagement Tercatat):** Memiliki data likes dan komentar publik yang dapat diverifikasi secara empiris.

    ---

    ### B. Definisi Operasional 9 Kriteria Eksklusi (E1 – E9)
    1. **E1 (Format Video / Reels):** Seluruh konten video dieliminasi karena faktor algoritma dan karakteristik visual video berbeda dengan foto statis.
    2. **E2 (Ucapan Hari Besar Tanpa Produk):** Ucapan selamat hari raya tanpa menampilkan produk dagang.
    3. **E3 (Quote / Kata Motivasi):** Kutipan kata mutiara tanpa relevansi komoditas.
    4. **E4 (Pengumuman Internal Operasional):** Info lowongan kerja, pengumuman toko tutup/libur.
    5. **E5 (Repost Pelanggan Murni / UGC):** Tangkapan layar review/story pembeli tanpa materi promosi resmi.
    6. **E6 (Hanya Menampilkan Pemilik):** Foto personal branding owner tanpa produk.
    7. **E7 (Giveaway Non-Relevan):** Bagi-bagi hadiah/saldo tanpa produk utama.
    8. **E8 (Gambar Rusak / Tidak Tersedia):** Postingan yang dihapus atau link gambar kadaluarsa.
    9. **E9 (Data Engagement Disembunyikan / Tidak Tersedia):** Postingan yang mematikan fitur likes dan komentar.

    ---

    ### C. Batasan Teknis Instagram & Kejujuran Data Engagement
    - **Jumlah Share & Save:** Instagram sama sekali **tidak menampilkan angka share dan save ke publik**. Data ini hanya dapat dilihat oleh pemilik akun melalui Instagram Insights pribadi. Dalam dataset ini, kolom share sengaja dibiarkan kosong (NULL) dan ditandai *"Tidak tersedia secara publik"*, tidak diubah menjadi angka nol palsu agar mematuhi etika penelitian ilmiah.
    - **Rate Limit Instagram:** Untuk mencapai target 3.000 data tanpa pemblokiran IP, lakukan penarikan secara bertahap (misal 100–300 link per hari) dengan jeda 3–7 detik antar permintaan.
    """)
