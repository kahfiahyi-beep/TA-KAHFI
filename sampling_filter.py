"""
sampling_filter.py
==================
Modul Penyaringan Otomatis (Purposive Sampling) untuk Skripsi:
"Analisis Hubungan Karakteristik Visual Produk dengan Engagement pada Media Sosial UMKM
dalam Perspektif Ekonomi Islam dan Perlindungan Konsumen Digital"

Memvalidasi kriteria inklusi (I1 - I7) dan kriteria eksklusi (E1 - E9) secara transparan dan ter-audit.
"""

import json
import os
import re
from datetime import datetime

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    """Membaca konfigurasi periode penelitian dan parameter lainnya."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Peringatan: Gagal membaca config.json ({e}), menggunakan nilai default.")
    
    return {
        "periode_penelitian": {
            "tanggal_mulai": "2026-01-01",
            "tanggal_selesai": "2026-06-30"
        },
        "target_penelitian": {
            "target_sampel_valid": 3000
        }
    }

# Definisi Baku 7 Kriteria Inklusi
DAFTAR_KRITERIA_INKLUSI = {
    "I1": "Berasal dari akun Instagram UMKM yang telah dipilih sebagai objek penelitian",
    "I2": "Berupa gambar statis atau foto feed, bukan Reels maupun video",
    "I3": "Menampilkan produk yang dijual oleh UMKM (objek visual komoditas)",
    "I4": "Memiliki fungsi promosi atau pemasaran komersial produk",
    "I5": "Dipublikasikan dalam periode penelitian (Januari 2026 - Juni 2026)",
    "I6": "Memiliki gambar yang tersedia dan karakteristik visualnya dapat diamati",
    "I7": "Memiliki data engagement (Likes & Komentar) yang dapat dicatat"
}

# Definisi Baku 9 Kriteria Eksklusi
DAFTAR_KRITERIA_EKSKLUSI = {
    "E1": "Berupa Reels atau format video",
    "E2": "Berupa ucapan hari besar yang tidak menampilkan produk",
    "E3": "Berupa kutipan, quote, atau konten motivasi tanpa produk",
    "E4": "Berupa pengumuman internal operasional toko tanpa promosi produk",
    "E5": "Berupa repost pelanggan murni atau konten yang hanya menampilkan pembeli",
    "E6": "Hanya menampilkan pemilik (owner) UMKM tanpa produk",
    "E7": "Berupa giveaway yang tidak menampilkan produk secara relevan",
    "E8": "Memiliki gambar yang sudah tidak tersedia atau tautan rusak",
    "E9": "Tidak memiliki data engagement wajib yang dapat diperoleh"
}

def evaluasi_postingan(
    username: str,
    jenis_media: str,
    tanggal_publikasi: str,
    caption: str,
    status_gambar: str,
    likes: int | None,
    comments: int | None,
    daftar_akun_valid: list | None = None,
    config: dict | None = None
) -> dict:
    """
    Evaluasi awal terhadap kriteria inklusi dan eksklusi.
    
    Aturan Keras (Audit trail):
    1. Jika video/reels -> Gugur E1.
    2. Jika gambar tidak tersedia -> Gugur E8.
    3. Jika di luar rentang tanggal penelitian -> Gugur (Di luar periode penelitian).
    4. Jika bukan dari daftar akun UMKM yang disetujui -> Gugur (Bukan akun sampel).
    5. Jika engagement dinonaktifkan / kosong total -> Gugur E9.
    6. Jika lolos aturan otomatis awal: TANDAI SEBAGAI 'Perlu Verifikasi Manual'
       karena keberadaan visual produk (I3) dan fungsi promosi murni (I4)
       wajib diverifikasi oleh mata peneliti (tidak boleh disimpulkan sepihak).
    """
    cfg = config or load_config()
    periode = cfg.get("periode_penelitian", {})
    tgl_mulai_str = periode.get("tanggal_mulai", "2026-01-01")
    tgl_selesai_str = periode.get("tanggal_selesai", "2026-06-30")

    alasan_eksklusi = []
    kriteria_belum_pasti = []
    indikasi_eksklusi_awal = []

    # 1. Evaluasi I1: Akun UMKM
    if daftar_akun_valid and len(daftar_akun_valid) > 0:
        cleaned_valid = [u.lower().strip().replace("@", "") for u in daftar_akun_valid]
        curr_user = (username or "").lower().strip().replace("@", "")
        if curr_user not in cleaned_valid:
            alasan_eksklusi.append("I1 Gagal: Akun tidak terdaftar dalam daftar sampel UMKM yang disetujui")

    # 2. Evaluasi I2 & E1: Format Media (Bukan Video/Reels)
    media_clean = (jenis_media or "Foto").lower()
    is_video = any(v in media_clean for v in ["video", "reel", "igtv", "clip"])
    if is_video:
        alasan_eksklusi.append("E1: Berupa Reels atau video (bukan gambar statis feed)")

    # 3. Evaluasi I6 & E8: Ketersediaan Gambar
    if status_gambar == "Tidak Tersedia" or not status_gambar:
        alasan_eksklusi.append("E8: Gambar tidak tersedia, tautan rusak, atau gagal diunduh")

    # 4. Evaluasi I5: Periode Penelitian (Januari 2026 - Juni 2026)
    if tanggal_publikasi:
        try:
            p_date = datetime.strptime(tanggal_publikasi[:10], "%Y-%m-%d").date()
            s_date = datetime.strptime(tgl_mulai_str[:10], "%Y-%m-%d").date()
            e_date = datetime.strptime(tgl_selesai_str[:10], "%Y-%m-%d").date()
            if not (s_date <= p_date <= e_date):
                alasan_eksklusi.append(f"I5 Gagal: Tanggal publikasi ({tanggal_publikasi[:10]}) di luar periode penelitian ({tgl_mulai_str} s/d {tgl_selesai_str})")
        except Exception:
            kriteria_belum_pasti.append("I5 (Format tanggal publikasi belum terverifikasi)")
    else:
        kriteria_belum_pasti.append("I5 (Tanggal publikasi belum tercatat)")

    # 5. Evaluasi I7 & E9: Data Engagement
    if likes is None and comments is None:
        alasan_eksklusi.append("E9: Tidak memiliki data engagement wajib yang dapat diperoleh")

    # 6. Analisis Indikasi Konten dari Caption (Sebagai Bantuan Deteksi Dini)
    cap_lower = (caption or "").lower()
    
    # Deteksi indikasi ucapan hari besar (E2)
    holiday_kws = ["selamat hari raya", "idul fitri", "idul adha", "tahun baru", "dirgahayu", "isra mi'raj", "maulid nabi", "marhaban ya ramadhan"]
    if any(kw in cap_lower for kw in holiday_kws):
        indikasi_eksklusi_awal.append("Potensi E2 (Ucapan hari besar - periksa apakah ada produk)")

    # Deteksi indikasi quote / motivasi (E3)
    quote_kws = ["quote of the day", "kata mutiara", "semangat senin", "quotes", "jangan lupa bersyukur", "renungan"]
    if any(kw in cap_lower for kw in quote_kws) and len(cap_lower) < 120:
        indikasi_eksklusi_awal.append("Potensi E3 (Quote/Motivasi - periksa apakah ada produk)")

    # Deteksi indikasi pengumuman internal (E4)
    internal_kws = ["lowongan kerja", "loker", "kami tutup", "toko tutup", "maintenance", "rekrutmen", "libur lebaran"]
    if any(kw in cap_lower for kw in internal_kws):
        indikasi_eksklusi_awal.append("Potensi E4 (Pengumuman internal operasional toko)")

    # Deteksi indikasi repost / testimoni (E5)
    repost_kws = ["repost dari", "testimoni kak", "makasih orderannya kak", "regram", "customer review"]
    if any(kw in cap_lower for kw in repost_kws):
        indikasi_eksklusi_awal.append("Potensi E5 (Repost testimoni pelanggan murni)")

    # Deteksi indikasi owner personal photo (E6)
    owner_kws = ["owner time", "jalan-jalan owner", "me and my team", "quality time bersama keluarga"]
    if any(kw in cap_lower for kw in owner_kws):
        indikasi_eksklusi_awal.append("Potensi E6 (Foto pemilik tanpa fokus produk)")

    # Deteksi giveaway (E7)
    if "giveaway" in cap_lower or "bagi-bagi thr" in cap_lower or "bagi-bagi saldo" in cap_lower:
        indikasi_eksklusi_awal.append("Potensi E7 (Giveaway - periksa apakah menampilkan produk relevan)")

    # Kriteria yang TIDAK BOLEH diputuskan sepihak oleh otomatisasi:
    kriteria_belum_pasti.append("I3 (Verifikasi visual apakah produk UMKM terlihat jelas)")
    kriteria_belum_pasti.append("I4 (Verifikasi apakah konten berfungsi promosi komersial)")

    # KEPUTUSAN FILTER OTOMATIS
    if len(alasan_eksklusi) > 0:
        status_inklusi = "Gugur Eksklusi"
        ringkasan_alasan = " ; ".join(alasan_eksklusi)
    else:
        # Lolos pemeriksaan kriteria awal teknis -> Masuk antrean verifikasi manual
        status_inklusi = "Perlu Verifikasi Manual"
        if indikasi_eksklusi_awal:
            ringkasan_alasan = "Indikasi awal pemeriksa: " + " ; ".join(indikasi_eksklusi_awal)
        else:
            ringkasan_alasan = "Lolos filter otomatis awal. Menunggu verifikasi visual produk oleh peneliti."

    return {
        "status_inklusi": status_inklusi,
        "alasan_eksklusi": ringkasan_alasan if status_inklusi == "Gugur Eksklusi" else "",
        "indikasi_pemeriksa": " ; ".join(indikasi_eksklusi_awal),
        "kriteria_belum_pasti": " ; ".join(kriteria_belum_pasti),
        "lolos_teknis_awal": len(alasan_eksklusi) == 0
    }
