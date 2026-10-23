"""
test_workflow.py
================
Skrip pengujian otomatis menyeluruh untuk sistem scraping dan kurasi dataset skripsi:
1. Validasi penarikan metadata postingan (shortcode, tanggal publikasi, likes, komentar).
2. Validasi penanganan duplikasi data (mencegah double entry).
3. Validasi aturan kriteria inklusi dan eksklusi.
4. Validasi proses verifikasi manual.
5. Validasi ekspor 4 file dataset + 1 laporan ringkasan seleksi.
"""

import os
import json
import sqlite3
import pandas as pd
import database_manager as dbm
import sampling_filter as sf
import scraper_engine as se
import export_manager as em

def run_all_tests():
    print("=" * 70)
    print("MEMULAI PENGUJIAN SISTEM SCRAPING & KURASI DATASET SKRIPSI")
    print("=" * 70)

    # 1. Inisialisasi DB
    dbm.init_db()
    print("\n[TEST 1] Inisialisasi Database: BERHASIL")

    # 2. Uji Penarikan Postingan Nyata
    test_shortcode = "DZ9xP_AyYAM"
    print(f"\n[TEST 2] Menguji penarikan metadata postingan nyata: {test_shortcode}")
    res = se.fetch_single_post(
        url_or_shortcode=test_shortcode,
        username_fallback="basoaciakang",
        nama_umkm="Baso Aci Akang",
        kategori_produk="Kuliner / F&B"
    )
    assert res.get("status") == "success", f"Gagal fetch: {res.get('message')}"
    data = res["data"]
    print(f"  • ID Dataset        : {data.get('id_dataset')}")
    print(f"  • Username          : @{data.get('username_ig')}")
    print(f"  • Tanggal Publikasi : {data.get('tanggal_publikasi')}")
    print(f"  • Format Media      : {data.get('jenis_media')}")
    print(f"  • Likes             : {data.get('jumlah_likes')} ({data.get('status_likes')})")
    print(f"  • Komentar          : {data.get('jumlah_komentar')} ({data.get('status_komentar')})")
    print(f"  • Shares (Private)  : {data.get('jumlah_share')} ({data.get('status_share')})")
    print(f"  • Status Gambar     : {data.get('status_ketersediaan_gambar')}")
    print(f"  • File Gambar Lokal : {os.path.basename(data.get('lokasi_file_gambar') or '')}")
    print(f"  • Keputusan Awal    : {data.get('status_inklusi')}")
    assert data.get("jumlah_share") is None, "Shares harus None / kosong (tidak boleh 0!)"
    assert data.get("status_inklusi") == "Perlu Verifikasi Manual", "Harus perlu verifikasi manual"
    print("  -> TEST 2 BERHASIL.")

    # 3. Uji Penanganan Duplikasi URL / Shortcode
    print("\n[TEST 3] Menguji pencegahan duplikasi data...")
    res_dup = se.fetch_single_post(
        url_or_shortcode=test_shortcode,
        username_fallback="basoaciakang"
    )
    assert res_dup["data"]["db_action"] == "updated", "Postingan duplikat harus diperbarui, bukan diduplikasi!"
    print("  • Terdeteksi duplikat shortcode, aksi DB: updated (Bukan membuat baris ganda)")
    print("  -> TEST 3 BERHASIL.")

    # 4. Uji Simulasi Kasus Eksklusi (Video, Tanggal Kadaluarsa, Gambar Hilang)
    print("\n[TEST 4] Menguji aturan penyaringan kriteria eksklusi (E1 - E9)...")
    eval_video = sf.evaluasi_postingan(
        username="umkm_contoh",
        jenis_media="Video/Reels",
        tanggal_publikasi="2026-03-01 10:00:00",
        caption="Video reels promosi menu",
        status_gambar="Tersedia",
        likes=10,
        comments=2
    )
    assert eval_video["status_inklusi"] == "Gugur Eksklusi"
    assert "E1" in eval_video["alasan_eksklusi"]
    print(f"  • Kasus Reels/Video : {eval_video['status_inklusi']} -> {eval_video['alasan_eksklusi']}")

    eval_old = sf.evaluasi_postingan(
        username="umkm_contoh",
        jenis_media="Foto",
        tanggal_publikasi="2025-10-10 10:00:00",
        caption="Postingan tahun 2025 lalu",
        status_gambar="Tersedia",
        likes=10,
        comments=2
    )
    assert eval_old["status_inklusi"] == "Gugur Eksklusi"
    assert "I5 Gagal" in eval_old["alasan_eksklusi"]
    print(f"  • Kasus Di Luar Periode : {eval_old['status_inklusi']} -> {eval_old['alasan_eksklusi']}")
    print("  -> TEST 4 BERHASIL.")

    # 5. Uji Verifikasi Manual Peneliti
    print("\n[TEST 5] Menguji mekanisme verifikasi manual...")
    post_id = data["id"]
    manual_data = {
        "status_inklusi": "Lolos Inklusi",
        "alasan_eksklusi": "",
        "menampilkan_produk": "Ya",
        "keterangan_produk": "Paket Baso Aci Akang Spesial Tulang Rangu",
        "fungsi_promosi": "Ya",
        "konten_asli_atau_repost": "Konten Asli",
        "kelayakan_analisis_visual": "Layak",
        "catatan_pemeriksa": "Objek baso aci terlihat jelas di tengah mangkuk, memuat informasi harga."
    }
    dbm.update_manual_verification(post_id, manual_data)
    
    # Cek di database
    conn = dbm.get_connection()
    c = conn.cursor()
    c.execute("SELECT status_inklusi, status_verifikasi_manual, keterangan_produk FROM dataset_posts WHERE id = ?", (post_id,))
    row = c.fetchone()
    conn.close()
    assert row["status_inklusi"] == "Lolos Inklusi"
    assert row["status_verifikasi_manual"] == "Sudah Diperiksa"
    print(f"  • Status Setelah Verifikasi Manual: {row['status_inklusi']} ({row['status_verifikasi_manual']})")
    print(f"  • Keterangan Produk Diset         : {row['keterangan_produk']}")
    print("  -> TEST 5 BERHASIL.")

    # 6. Uji Ekspor 4 File + Laporan Ringkasan
    print("\n[TEST 6] Menguji ekspor dataset ke Excel dan CSV...")
    exp_res = em.export_all_datasets()
    assert exp_res["status"] == "success"
    print("  • File hasil ekspor:")
    for key, fpath in exp_res["files"].items():
        assert os.path.exists(fpath), f"File {fpath} tidak tercipta!"
        sz = os.path.getsize(fpath)
        print(f"    - {key:<20}: {os.path.basename(fpath)} ({sz:,} bytes)")
    
    # Periksa isi dataset_layak.xlsx
    df_layak = pd.read_excel(exp_res["files"]["dataset_layak"])
    assert len(df_layak) >= 1
    assert "jumlah_share" in df_layak.columns
    assert pd.isna(df_layak["jumlah_share"].iloc[0]), "Share harus tetap kosong/NaN di Excel!"
    print("  • Verifikasi integritas kolom Excel: Kolom share kosong (tidak diisi angka 0 palsu)")
    print("  -> TEST 6 BERHASIL.")

    # 7. Statistik Progres
    print("\n[TEST 7] Metrik Progres Menuju Target 3.000:")
    stt = dbm.get_post_statistics()
    print(f"  • Total Post Mentah   : {stt['total_postingan']}")
    print(f"  • Total Foto Terdata  : {stt['total_foto']}")
    print(f"  • Lolos Inklusi Valid : {stt['total_layak']}")
    print(f"  • Sisa Kebutuhan      : {stt['sisa_kebutuhan']} / {stt['target']}")
    print("  -> TEST 7 BERHASIL.")

    print("\n" + "=" * 70)
    print("SEMUA PENGUJIAN (TEST 1 - TEST 7) BERHASIL 100% TANPA KESALAHAN!")
    print("=" * 70)

if __name__ == "__main__":
    run_all_tests()
