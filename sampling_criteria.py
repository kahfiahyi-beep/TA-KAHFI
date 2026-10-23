"""
sampling_criteria.py
====================
Modul Metodologi Penentuan Sampel Penelitian (Purposive Sampling).
Mengevaluasi Kelayakan Sampel Postingan UMKM berdasarkan:
  - 7 Kriteria Inklusi (I1 - I7)
  - 9 Kriteria Eksklusi (E1 - E9)
  - Validasi Periode Waktu Penelitian
"""

import re
from datetime import datetime

# Definisi Baku 7 Kriteria Inklusi (I1 - I7)
INCLUSION_CRITERIA = {
    "I1": {
        "code": "I1",
        "title": "Berasal dari Akun UMKM",
        "desc": "Postingan dipublikasikan oleh akun resmi pelaku UMKM yang menjadi objek penelitian."
    },
    "I2": {
        "code": "I2",
        "title": "Berupa Gambar / Static Image",
        "desc": "Format konten berupa foto atau grafis statis (single image / carousel feed), bukan format video."
    },
    "I3": {
        "code": "I3",
        "title": "Menampilkan Produk yang Dijual",
        "desc": "Konten visual secara eksplisit memperlihatkan barang/jasa komoditas dagang UMKM."
    },
    "I4": {
        "code": "I4",
        "title": "Mempunyai Fungsi Promosi",
        "desc": "Memiliki tujuan pemasaran komersial (penawaran, pengenalan menu, promo diskon, atau ajakan membeli)."
    },
    "I5": {
        "code": "I5",
        "title": "Dipublikasikan dalam Periode Penelitian",
        "desc": "Tanggal unggah postingan berada dalam rentang waktu observasi penelitian yang ditentukan."
    },
    "I6": {
        "code": "I6",
        "title": "Dapat Diamati Karakteristik Visualnya",
        "desc": "Kualitas visual memadai untuk diekstraksi parameter citra (kecerahan, kontras, warna, dan 8 indikator K1–K8)."
    },
    "I7": {
        "code": "I7",
        "title": "Mempunyai Data Engagement Tercatat",
        "desc": "Memiliki metrik respons audiens (Likes & Comments) yang dapat diverifikasi dan dicatat."
    }
}

# Definisi Baku 9 Kriteria Eksklusi (E1 - E9)
EXCLUSION_CRITERIA = {
    "E1": {
        "code": "E1",
        "title": "Format Video / Reels / TikTok Video",
        "desc": "Konten berupa video bergerak / reels, bukan gambar statis."
    },
    "E2": {
        "code": "E2",
        "title": "Ucapan Hari Besar Tanpa Produk",
        "desc": "Ucapan hari raya/nasional yang tidak menampilkan produk atau penawaran komersial."
    },
    "E3": {
        "code": "E3",
        "title": "Konten Quote / Kata Motivasi",
        "desc": "Hanya berisi teks kutipan bijak, humor, atau motivasi tanpa kaitan produk jualan."
    },
    "E4": {
        "code": "E4",
        "title": "Pengumuman Internal Operasional",
        "desc": "Informasi lowongan kerja, pengumuman toko libur/tutup, atau pemeliharaan internal tanpa jualan produk."
    },
    "E5": {
        "code": "E5",
        "title": "Repost Pelanggan Murni (UGC)",
        "desc": "Tangkapan layar repost story/feed pembeli tanpa materi promosi resmi dari UMKM."
    },
    "E6": {
        "code": "E6",
        "title": "Hanya Menampilkan Pemilik Tanpa Produk",
        "desc": "Foto personal branding pemilik/owner UMKM tanpa menampilkan komoditas yang dijual."
    },
    "E7": {
        "code": "E7",
        "title": "Giveaway Tanpa Relevansi Produk",
        "desc": "Program bagi-bagi hadiah yang tidak menampilkan produk jualan secara relevan."
    },
    "E8": {
        "code": "E8",
        "title": "Gambar Tidak Tersedia / Rusak",
        "desc": "Tautan gambar rusak, postingan dihapus, atau file gambar korup sehingga tidak dapat dianalisis."
    },
    "E9": {
        "code": "E9",
        "title": "Data Engagement Tidak Dapat Diperoleh",
        "desc": "Jumlah likes/komentar dinonaktifkan atau disembunyikan oleh pemilik akun."
    }
}


def evaluate_sampling_criteria(
    post_date_str: str,
    period_start_str: str,
    period_end_str: str,
    caption: str,
    has_image: bool,
    is_video_or_reel: bool,
    object_detected: bool,
    likes: int,
    comments: int,
    is_umkm_account: bool = True,
    manual_overrides: dict | None = None
) -> dict:
    """
    Evaluasi otomatis kelayakan sampel berdasarkan 7 Kriteria Inklusi dan 9 Kriteria Eksklusi.
    """
    caption_lower = (caption or "").lower()

    # ─────────────────────────────────────────────────────────
    # 1. EVALUASI OTOMATIS KRITERIA INKLUSI (I1 - I7)
    # ─────────────────────────────────────────────────────────
    inc = {}

    # I1: Berasal dari akun UMKM
    inc["I1"] = bool(is_umkm_account)

    # I2: Berupa gambar/static image
    inc["I2"] = bool(has_image and not is_video_or_reel)

    # I3: Menampilkan produk yang dijual
    # Jika objek produk terdeteksi dan tidak murni pengumuman non-produk
    inc["I3"] = bool(has_image and object_detected)

    # I4: Mempunyai fungsi promosi
    promo_keywords = [
        "promo", "diskon", "paket", "menu", "harga", "rp", "order", "pesan",
        "beli", "ready", "open", "sale", "gratis", "free", "produk", "jual",
        "koleksi", "hijab", "kopi", "makanan", "minuman", "stok", "dm", "wa"
    ]
    has_promo_kw = any(kw in caption_lower for kw in promo_keywords)
    inc["I4"] = bool(has_promo_kw or len(caption_lower) > 20)

    # I5: Dipublikasikan dalam periode penelitian
    in_period = True
    try:
        if post_date_str and period_start_str and period_end_str:
            p_date = datetime.strptime(post_date_str[:10], "%Y-%m-%d").date()
            s_date = datetime.strptime(period_start_str[:10], "%Y-%m-%d").date()
            e_date = datetime.strptime(period_end_str[:10], "%Y-%m-%d").date()
            in_period = (s_date <= p_date <= e_date)
    except Exception:
        in_period = True
    inc["I5"] = bool(in_period)

    # I6: Karakteristik visual dapat diamati
    inc["I6"] = bool(has_image)

    # I7: Mempunyai data engagement yang dapat dicatat
    # Memiliki angka likes atau comments (bukan None/negatif)
    inc["I7"] = bool(likes is not None and likes >= 0)

    # ─────────────────────────────────────────────────────────
    # 2. EVALUASI OTOMATIS KRITERIA EKSKLUSI (E1 - E9)
    # ─────────────────────────────────────────────────────────
    exc = {}

    # E1: Format video/reels
    exc["E1"] = bool(is_video_or_reel)

    # E2: Ucapan hari besar yang tidak menampilkan produk
    holiday_kw = ["selamat hari raya", "idul fitri", "idul adha", "tahun baru", "dirgahayu", "isra miraj", "maulid nabi"]
    is_holiday = any(kw in caption_lower for kw in holiday_kw)
    exc["E2"] = bool(is_holiday and not object_detected and not has_promo_kw)

    # E3: Quote / motivasi tanpa produk
    quote_kw = ["quote of the day", "kata mutiara", "semangat senin", "jangan menyerah", "renungan", "bismillah pagiku"]
    is_quote = any(kw in caption_lower for kw in quote_kw)
    exc["E3"] = bool(is_quote and not object_detected and not has_promo_kw)

    # E4: Pengumuman internal operasional
    internal_kw = ["lowongan kerja", "loker", "toko tutup", "kami tutup", "buka kembali", "maintenance", "rekrutmen"]
    is_internal = any(kw in caption_lower for kw in internal_kw)
    exc["E4"] = bool(is_internal and not object_detected and not has_promo_kw)

    # E5: Repost pelanggan murni
    repost_kw = ["repost dari", "testimoni kak", "makasih orderannya kak", "regram"]
    is_repost = any(kw in caption_lower for kw in repost_kw) and ("review" in caption_lower or "story" in caption_lower)
    exc["E5"] = bool(is_repost and not object_detected)

    # E6: Konten yang hanya menampilkan pemilik tanpa produk
    owner_kw = ["owner time", "jalan-jalan owner", "me and my family", "liburan bersama"]
    is_owner_only = any(kw in caption_lower for kw in owner_kw)
    exc["E6"] = bool(is_owner_only and not object_detected)

    # E7: Giveaway tanpa relevansi produk
    is_giveaway = "giveaway" in caption_lower or "bagi-bagi saldo" in caption_lower
    exc["E7"] = bool(is_giveaway and not object_detected)

    # E8: Postingan yang gambarnya tidak tersedia
    exc["E8"] = not bool(has_image)

    # E9: Data engagement tidak dapat diperoleh
    exc["E9"] = bool(likes is None or likes < 0)

    # Terapkan manual overrides jika peneliti mengubah status kriteria
    if manual_overrides:
        for k, v in manual_overrides.items():
            if k in inc:
                inc[k] = bool(v)
            elif k in exc:
                exc[k] = bool(v)

    # ─────────────────────────────────────────────────────────
    # 3. KESIMPULAN KELAYAKAN PURPOSIVE SAMPLING
    # ─────────────────────────────────────────────────────────
    all_inclusions_met = all(inc.values())
    any_exclusion_triggered = any(exc.values())

    is_valid_sample = all_inclusions_met and (not any_exclusion_triggered)

    # Catatan alasan gugur jika tidak valid
    failed_reasons = []
    if not all_inclusions_met:
        failed_inc = [k for k, v in inc.items() if not v]
        failed_reasons.append(f"Inklusi belum terpenuhi: {', '.join(failed_inc)}")
    if any_exclusion_triggered:
        triggered_exc = [k for k, v in exc.items() if v]
        failed_reasons.append(f"Memicu Kriteria Eksklusi: {', '.join(triggered_exc)}")

    sampling_notes = " | ".join(failed_reasons) if failed_reasons else "Memenuhi seluruh kriteria purposive sampling (Sampel Valid)."

    return {
        "is_valid": is_valid_sample,
        "all_inclusions_met": all_inclusions_met,
        "any_exclusion_triggered": any_exclusion_triggered,
        "inclusions": inc,
        "exclusions": exc,
        "notes": sampling_notes
    }
