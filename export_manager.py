"""
export_manager.py
=================
Modul Ekspor Dataset Skripsi ke Format Microsoft Excel (.xlsx) dan CSV (.csv).
Menghasilkan 4 file utama + 1 laporan audit ringkasan:
1. dataset_mentah.xlsx : Seluruh data yang berhasil dikumpulkan sebelum seleksi final.
2. dataset_layak.xlsx  : Postingan yang telah lolos kriteria inklusi dan verifikasi manual.
3. dataset_eksklusi.xlsx : Postingan yang ditolak beserta rincian alasan eksklusinya.
4. dataset_layak.csv   : Salinan dataset final dalam format CSV standar (UTF-8 BOM).
5. laporan_ringkasan_seleksi.xlsx : Laporan kuantitatif tahapan seleksi purposive sampling.
"""

import os
import sqlite3
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

import database_manager as dbm
import sampling_filter as sf

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "hasil_ekspor")

def get_styled_excel_writer(filepath):
    """Menyiapkan Excel writer dengan engine openpyxl."""
    return pd.ExcelWriter(filepath, engine="openpyxl")

def apply_excel_styling(worksheet, header_color="1E3A8A"):
    """
    Menerapkan tata letak visual profesional pada file Excel:
    Header berwarna gelap teks putih tebal, zebra row striping, garis tipis, dan auto-fit column width.
    """
    header_fill = PatternFill(start_color=header_color, end_color=header_color, fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Segoe UI", size=10)
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=False)
    left_align = Alignment(horizontal="left", vertical="center", wrap_text=False)
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    # Style Header
    for col_num in range(1, worksheet.max_column + 1):
        cell = worksheet.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align

    # Style Data Cells
    for row_num in range(2, worksheet.max_row + 1):
        for col_num in range(1, worksheet.max_column + 1):
            cell = worksheet.cell(row=row_num, column=col_num)
            cell.font = data_font
            cell.border = thin_border
            
            # Format teks panjang atau angka
            val = str(cell.value or "")
            if val.startswith("http://") or val.startswith("https://"):
                cell.font = Font(name="Segoe UI", size=10, color="0000EE", underline="single")
            elif any(col_name in str(worksheet.cell(row=1, column=col_num).value).lower() for col_name in ["id", "tanggal", "likes", "komentar", "status"]):
                cell.alignment = center_align

    # Auto-adjust column widths
    for col in worksheet.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = min(60, len(val_str))
        worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

def generate_selection_summary(conn):
    """Membuat laporan ringkasan audit kuantitatif seleksi purposive sampling."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM dataset_posts")
    total_raw = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dataset_posts WHERE jenis_media IN ('Foto', 'Carousel/Foto')")
    total_foto = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dataset_posts WHERE status_ketersediaan_gambar = 'Tersedia'")
    total_img_ok = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dataset_posts WHERE status_inklusi = 'Lolos Inklusi'")
    total_layak = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dataset_posts WHERE status_inklusi = 'Gugur Eksklusi'")
    total_eksklusi = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM dataset_posts WHERE status_inklusi = 'Perlu Verifikasi Manual'")
    total_pending = cursor.fetchone()[0]

    # Rincian eksklusi per kriteria
    cursor.execute("SELECT alasan_eksklusi, COUNT(*) as cnt FROM dataset_posts WHERE status_inklusi = 'Gugur Eksklusi' GROUP BY alasan_eksklusi")
    eksklusi_breakdown = cursor.fetchall()

    target = 3000
    sisa = max(0, target - total_layak)

    summary_rows = [
        {"Tahapan Seleksi Purposive Sampling": "1. Total Postingan Ditemukan (Data Mentah)", "Jumlah Postingan": total_raw, "Persentase": "100.0%"},
        {"Tahapan Seleksi Purposive Sampling": "2. Format Foto Statis / Carousel (Bukan Video/Reels)", "Jumlah Postingan": total_foto, "Persentase": f"{(total_foto/total_raw*100) if total_raw else 0:.1f}%"},
        {"Tahapan Seleksi Purposive Sampling": "3. Gambar Tersedia & Berhasil Diunduh", "Jumlah Postingan": total_img_ok, "Persentase": f"{(total_img_ok/total_raw*100) if total_raw else 0:.1f}%"},
        {"Tahapan Seleksi Purposive Sampling": "4. Menunggu Verifikasi Manual Peneliti", "Jumlah Postingan": total_pending, "Persentase": f"{(total_pending/total_raw*100) if total_raw else 0:.1f}%"},
        {"Tahapan Seleksi Purposive Sampling": "5. Gugur Kriteria Eksklusi", "Jumlah Postingan": total_eksklusi, "Persentase": f"{(total_eksklusi/total_raw*100) if total_raw else 0:.1f}%"},
        {"Tahapan Seleksi Purposive Sampling": "6. Lolos Inklusi Final (Dataset Penelitian)", "Jumlah Postingan": total_layak, "Persentase": f"{(total_layak/total_raw*100) if total_raw else 0:.1f}%"},
        {"Tahapan Seleksi Purposive Sampling": "Target Sampel Penelitian", "Jumlah Postingan": target, "Persentase": "Target Baku"},
        {"Tahapan Seleksi Purposive Sampling": "Sisa Kebutuhan Menuju Target 3.000", "Jumlah Postingan": sisa, "Persentase": f"{(sisa/target*100):.1f}% sisa"}
    ]

    df_summary = pd.DataFrame(summary_rows)
    return df_summary

def export_all_datasets(db_path=None, output_folder=None):
    """
    Mengekspor seluruh file dataset yang dipersyaratkan:
    - dataset_mentah.xlsx
    - dataset_layak.xlsx
    - dataset_eksklusi.xlsx
    - dataset_layak.csv
    - laporan_ringkasan_seleksi.xlsx
    """
    out_dir = output_folder or EXPORT_DIR
    os.makedirs(out_dir, exist_ok=True)
    conn = dbm.get_connection(db_path)

    # Ambil seluruh data dari database
    query_all = "SELECT * FROM dataset_posts ORDER BY id ASC"
    df_all = pd.read_sql_query(query_all, conn)

    # Pastikan jumlah_share tetap kosong (None/NaN) tanpa dikonversi ke 0
    # Kolom-kolom yang dipersyaratkan untuk dataset publikasi
    kolom_publikasi = [
        "id_dataset", "username_ig", "nama_umkm", "kategori_produk", "link_profil",
        "link_postingan", "shortcode", "tanggal_publikasi", "caption", "jenis_media",
        "tanggal_pengambilan_data", "lokasi_file_gambar", "status_ketersediaan_gambar",
        "menampilkan_produk", "keterangan_produk", "fungsi_promosi", "konten_asli_atau_repost",
        "kelayakan_analisis_visual", "status_verifikasi_manual",
        "jumlah_likes", "status_likes", "jumlah_komentar", "status_komentar",
        "jumlah_share", "status_share", "waktu_pengambilan_engagement", "metode_pengambilan_metrik",
        "status_inklusi", "alasan_eksklusi", "kriteria_belum_pasti", "catatan_pemeriksa",
        "waktu_verifikasi", "status_pemeriksaan_akhir",
        # Variabel visual untuk analisis Bab 4
        "warna_dominan", "kecerahan_brightness", "kontras_visual", "komposisi_visual",
        "jumlah_produk_terlihat", "keberadaan_manusia", "kejelasan_tampilan_produk",
        "teks_promosi_pada_gambar", "keberadaan_harga_info", "kualitas_gambar"
    ]

    # Saring kolom yang ada
    kolom_tersedia = [c for c in kolom_publikasi if c in df_all.columns]
    df_export = df_all[kolom_tersedia].copy()

    # 1. FILE 1: DATASET MENTAH (Sebelum Seleksi)
    file_mentah = os.path.join(out_dir, "dataset_mentah.xlsx")
    with pd.ExcelWriter(file_mentah, engine="openpyxl") as writer:
        df_export.to_excel(writer, sheet_name="Data_Mentah", index=False)
        apply_excel_styling(writer.sheets["Data_Mentah"], header_color="334155")

    # 2. FILE 2: DATASET LAYAK (Lolos Inklusi)
    df_layak = df_export[df_export["status_inklusi"] == "Lolos Inklusi"].copy()
    file_layak = os.path.join(out_dir, "dataset_layak.xlsx")
    with pd.ExcelWriter(file_layak, engine="openpyxl") as writer:
        df_layak.to_excel(writer, sheet_name="Dataset_Layak", index=False)
        apply_excel_styling(writer.sheets["Dataset_Layak"], header_color="065F46")

    # 3. FILE 3: DATASET EKSKLUSI (Postingan Ditolak Beserta Alasannya)
    df_eksklusi = df_export[df_export["status_inklusi"] == "Gugur Eksklusi"].copy()
    file_eksklusi = os.path.join(out_dir, "dataset_eksklusi.xlsx")
    with pd.ExcelWriter(file_eksklusi, engine="openpyxl") as writer:
        df_eksklusi.to_excel(writer, sheet_name="Dataset_Eksklusi", index=False)
        apply_excel_styling(writer.sheets["Dataset_Eksklusi"], header_color="991B1B")

    # 4. FILE 4: DATASET LAYAK FORMAT CSV (UTF-8 BOM agar rapi di Microsoft Excel)
    file_layak_csv = os.path.join(out_dir, "dataset_layak.csv")
    df_layak.to_csv(file_layak_csv, index=False, encoding="utf-8-sig")

    # 5. FILE 5: LAPORAN RINGKASAN PROSES SELEKSI
    df_summary = generate_selection_summary(conn)
    file_summary = os.path.join(out_dir, "laporan_ringkasan_seleksi.xlsx")
    with pd.ExcelWriter(file_summary, engine="openpyxl") as writer:
        df_summary.to_excel(writer, sheet_name="Ringkasan_Seleksi", index=False)
        apply_excel_styling(writer.sheets["Ringkasan_Seleksi"], header_color="1E3A8A")

    conn.close()

    return {
        "status": "success",
        "output_folder": out_dir,
        "files": {
            "dataset_mentah": file_mentah,
            "dataset_layak": file_layak,
            "dataset_eksklusi": file_eksklusi,
            "dataset_layak_csv": file_layak_csv,
            "laporan_ringkasan": file_summary
        },
        "counts": {
            "total_mentah": len(df_export),
            "total_layak": len(df_layak),
            "total_eksklusi": len(df_eksklusi)
        }
    }

if __name__ == "__main__":
    res = export_all_datasets()
    print("Hasil ekspor:", res)
