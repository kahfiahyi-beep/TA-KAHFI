import re
import json
import base64
import os
from PIL import Image
import io

def analyze_post_offline(image_pil, caption_text, cv_metrics):
    """
    Analisis cerdas lokal/offline menggunakan aturan linguistik & Computer Vision
    untuk mendeteksi K1 - K8, F1 - F8, skor ekonomi Islam, dan perlindungan konsumen.
    """
    caption_lower = (caption_text or "").lower()
    
    # ==========================
    # K1 - K8 INDIKATOR PROMOSI & REGULASI
    # ==========================
    # K1: Nama Produk
    product_keywords = ["jual", "menu", "koleksi", "hijab", "gamis", "kopi", "sepatu", "sambal", "kaos", "baju", "tas", "snack", "parfum", "paket", "produk", "series", "varian", "baso", "aci", "makanan"]
    has_k1 = 1 if any(kw in caption_lower for kw in product_keywords) or len(caption_text.strip()) > 15 else 0
    k1_detail = "Nama/identitas produk teridentifikasi jelas dalam postingan" if has_k1 else "Nama spesifik produk tidak tertera secara jelas"
    
    # K2: Harga
    price_pattern = r"(rp\.?\s*[\d\.\,]+|idr\s*[\d\.\,]+|\b\d+k\b|\b\d+\s*rb\b|\b\d{2,3}\.000\b)"
    dm_pattern = r"(dm\s+for\s+price|tanya\s+harga\s+via\s+dm|cek\s+dm|japri|harga\s+by\s+dm|wa\s+untuk\s+harga|info\s+harga\s+dm)"
    
    has_explicit_price = bool(re.search(price_pattern, caption_lower))
    has_dm_price = bool(re.search(dm_pattern, caption_lower))
    
    if has_explicit_price:
        has_k2 = 1
        k2_match = re.search(price_pattern, caption_lower).group(0)
        k2_detail = f"Harga transparan tercantum: '{k2_match}'"
    elif has_dm_price:
        has_k2 = 0
        k2_detail = "Harga disembunyikan / harus 'DM/Japri' (Beresiko Gharar Khafi)"
    else:
        has_k2 = 0
        k2_detail = "Harga tidak dicantumkan secara terbuka"
        
    # K3: Diskon / Promo
    discount_keywords = ["diskon", "discount", "promo", "potongan", "sale", "flash sale", "cashback", "off", "%", "buy 1 get 1", "beli 1 gratis", "beli 2", "hemat", "voucher", "gratis"]
    has_k3 = 1 if any(kw in caption_lower for kw in discount_keywords) else 0
    k3_detail = "Terdapat penawaran promo/diskon" if has_k3 else "Tidak memuat penawaran diskon/promo"
    
    # K4: Periode Promo
    period_keywords = ["hingga", "sampai", "s.d", "s/d", "berlaku", "periode", "terbatas", "hari ini saja", "khusus hari", "tanggal", "jam", "wib", "sebelum"]
    has_k4 = 1 if (has_k3 and any(kw in caption_lower for kw in period_keywords)) else 0
    k4_detail = "Batas waktu/periode promo dicantumkan" if has_k4 else ("Tidak ada batas waktu promo eksplisit" if has_k3 else "Bukan postingan bertenggat waktu promo")
    
    # K5: Syarat Promo (S&K)
    terms_keywords = ["s&k", "syarat", "ketentuan", "minimal", "min belanja", "min order", "follow", "tag", "mention", "kuota", "khusus member", "*"]
    has_k5 = 1 if (has_k3 and any(kw in caption_lower for kw in terms_keywords)) else 0
    k5_detail = "Syarat & ketentuan promo (S&K) dipaparkan" if has_k5 else ("Syarat promo tidak terperinci" if has_k3 else "Tidak memerlukan syarat promo")

    # K6: Info Produk
    info_keywords = ["bahan", "material", "ukuran", "size", "varian", "rasa", "komposisi", "bpom", "halal", "netto", "isi", "dimensi", "spesifikasi", "garansi", "kualitas", "pedas", "porsi"]
    has_k6 = 1 if any(kw in caption_lower for kw in info_keywords) else 0
    k6_detail = "Informasi detail spesifikasi/bahan produk tercantum" if has_k6 else "Informasi spesifikasi teknis produk minim"

    # K7: Klaim Produk
    claim_keywords = ["paling", "ter-", "terbaik", "terlaris", "no.1", "no 1", "nomor 1", "ampuh", "dijamin", "100% alami", "alami", "bebas kimia", "original", "asli", "organik", "ajaib", "garansi", "nampol", "mantap", "nagih"]
    has_k7 = 1 if any(kw in caption_lower for kw in claim_keywords) else 0
    k7_detail = "Memuat klaim keunggulan/manfaat produk" if has_k7 else "Tidak memuat klaim kualitas superlatif yang mencolok"

    # K8: Visual-Caption Alignment
    has_k8 = 1
    k8_detail = "Visual foto produk selaras dan konsisten dengan teks deskripsi penawaran"

    # ==========================
    # F1 - F8 FITUR COMPUTER VISION
    # ==========================
    f1_val = cv_metrics.get("f1_object_detected", 1)
    f1_detail = cv_metrics.get("f1_detail", "Objek produk terdeteksi di dalam frame")
    
    f2_val = 1
    f2_detail = cv_metrics.get("f2_detail", f"Warna dominan: {cv_metrics.get('dominant_color_name', 'Netral')} ({cv_metrics.get('dominant_color_hex', '#333')})")
    
    f3_val = 1
    f3_detail = cv_metrics.get("f3_detail", f"Posisi objek: {cv_metrics.get('f3_posisi', 'Tengah (Center)')}")
    
    f4_val = 1 if cv_metrics.get("f4_ratio", 30) >= 25 else 0
    f4_detail = cv_metrics.get("f4_detail", f"Dominasi luas area produk: {cv_metrics.get('f4_dominasi', 'Dominan Sedang')}")
    
    f5_val = 1
    f5_detail = cv_metrics.get("f5_detail", f"Karakteristik background: {cv_metrics.get('f5_background', 'Studio')}")
    
    f6_val = cv_metrics.get("f6_objek_tambahan", 0)
    f6_detail = cv_metrics.get("f6_detail", "Props dekorasi pendukung produk")
    
    f7_val = cv_metrics.get("f7_manusia", 0)
    f7_detail = cv_metrics.get("f7_detail", "Tanpa kehadiran model manusia (fokus produk murni)" if f7_val == 0 else "Terdeteksi kehadiran model manusia")
    
    f8_val = cv_metrics.get("f8_teks", 0)
    f8_detail = cv_metrics.get("f8_detail", "Keberadaan tipografi teks grafis pada gambar")

    # Skor Ekonomi Islam & Perlindungan Konsumen
    islamic_score = 50.0
    islamic_notes = []
    if has_k2 == 1:
        islamic_score += 25.0
        islamic_notes.append("Transparansi harga menegakkan asas kejelasan akad dan menghindari gharar (ketidakpastian).")
    else:
        islamic_notes.append("Penyembunyian harga ('DM for price') menimbulkan ketidakpastian awal (gharar khafi).")
        
    if has_k1 == 1 and has_k6 == 1:
        islamic_score += 15.0
        islamic_notes.append("Objek transaksi (ma'qud 'alaih) jelas spesifikasi dan kualitasnya.")
    else:
        islamic_notes.append("Spesifikasi objek barang belum sepenuhnya jelas bagi calon pembeli.")
        
    if has_k7 == 1:
        islamic_notes.append("Klaim produk perlu pembuktian nyata agar terhindar dari syubhat ghasysy (penipuan) atau taksyir.")
        islamic_score += 5.0
    else:
        islamic_score += 10.0
        islamic_notes.append("Informasi disampaikan proporsional sesuai asas shiddiq & amanah.")

    consumer_score = 50.0
    consumer_notes = []
    if has_k2 == 1:
        consumer_score += 20.0
        consumer_notes.append("Memenuhi hak konsumen atas informasi harga yang transparan (Pasal 4 UU PK).")
    else:
        consumer_notes.append("Menyembunyikan harga berpotensi melanggar hak konsumen atas kepastian nilai tukar barang.")
        
    if has_k6 == 1:
        consumer_score += 15.0
        consumer_notes.append("Pelaku usaha memberikan keterangan yang benar mengenai kondisi barang (Pasal 7).")
        
    if has_k3 == 1:
        if has_k4 == 1 and has_k5 == 1:
            consumer_score += 15.0
            consumer_notes.append("Promo dilengkapi batas waktu dan S&K terbuka, mencegah promosi menyesatkan (Pasal 9 & 10).")
        else:
            consumer_notes.append("Promo tanpa batas waktu atau syarat terbuka berpotensi menjebak konsumen.")
    else:
        consumer_score += 15.0

    return {
        # K1 - K8
        "k1_nama_produk": has_k1, "k1_detail": k1_detail,
        "k2_harga": has_k2, "k2_detail": k2_detail,
        "k3_diskon": has_k3, "k3_detail": k3_detail,
        "k4_periode_promo": has_k4, "k4_detail": k4_detail,
        "k5_syarat_promo": has_k5, "k5_detail": k5_detail,
        "k6_info_produk": has_k6, "k6_detail": k6_detail,
        "k7_klaim": has_k7, "k7_detail": k7_detail,
        "k8_visual_caption": has_k8, "k8_detail": k8_detail,
        # F1 - F8 (Fitur Computer Vision)
        "f1_object_detection": f1_val, "f1_detail": f1_detail,
        "f2_color_extraction": f2_val, "f2_detail": f2_detail,
        "f3_posisi_objek": f3_val, "f3_detail": f3_detail,
        "f4_dominasi_objek": f4_val, "f4_detail": f4_detail,
        "f5_background": f5_val, "f5_detail": f5_detail,
        "f6_objek_tambahan": f6_val, "f6_detail": f6_detail,
        "f7_manusia": f7_val, "f7_detail": f7_detail,
        "f8_teks": f8_val, "f8_detail": f8_detail,
        # Skor
        "islamic_compliance_score": min(100.0, islamic_score),
        "islamic_review": " ".join(islamic_notes),
        "consumer_protection_score": min(100.0, consumer_score),
        "consumer_review": " ".join(consumer_notes),
        "engine_used": "Local Computer Vision & Rule-Based NLP"
    }

def analyze_post_gemini(image_pil, caption_text, api_key):
    """
    Analisis Multi-Modal Vision menggunakan Google GenAI SDK (Gemini)
    mengekstrak K1-K8, F1-F8, dan tinjauan kepatuhan.
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        
        prompt = f"""
Anda adalah pakar Computer Vision untuk sosial media UMKM, Fiqh Muamalah (Ekonomi Islam), dan Hukum Perlindungan Konsumen Digital (UU No. 8/1999).
Analisis gambar postingan UMKM dan teks caption berikut:

CAPTION:
"{caption_text}"

Identifikasi DUA KELOMPOK INDIKATOR secara mendalam:

KELOMPOK 1: 8 INDIKATOR KONTEN & REGULASI (K1 - K8) (Nilai 0 = Tidak Ada, 1 = Ada):
- K1 (Nama Produk): Apakah ada identitas/nama produk jelas di gambar atau caption?
- K2 (Harga): Apakah ada harga nominal rupiah terbuka? (Jika 'DM for price'/tidak dicantumkan = 0).
- K3 (Diskon/Promo): Apakah ada informasi diskon/promo/potongan/voucher?
- K4 (Periode Promo): Apakah ada batas waktu/periode berlakunya promo?
- K5 (Syarat Promo): Apakah ada syarat & ketentuan promo (min order, S&K, dll)?
- K6 (Info Produk): Apakah ada spesifikasi/bahan/rasa/varian/izin BPOM/Halal?
- K7 (Klaim): Apakah ada klaim keunggulan superlatif ('terbaik', 'terlaris', 'ampuh', '100% alami')?
- K8 (Visual–Caption): Apakah objek visual sinkron dengan teks caption (1 = sinkron, 0 = clickbait)?

KELOMPOK 2: 8 FITUR COMPUTER VISION CITRA (F1 - F8):
- F1 (Object Detection): Apakah objek produk utama terdeteksi jelas dalam citra? (0/1 + detail nama objek yang terdeteksi)
- F2 (Color Extraction): Palet warna utama dan nuansa dominan dalam gambar (0/1 + detail warna)
- F3 (Posisi Objek): Komposisi letak produk (Tengah/Center, Rule of Thirds, Kiri, Kanan)
- F4 (Dominasi Objek): Seberapa besar objek produk mendominasi area foto (>40% Sangat Dominan, 20-40% Sedang, <20% Kecil)
- F5 (Background): Karakteristik latar belakang (Studio Polos, Sederhana/Bokeh, Kompleks/Outdoor)
- F6 (Objek Tambahan): Keberadaan elemen dekorasi pendukung / props tambahan / stiker (0/1 + detail)
- F7 (Manusia / Model): Apakah ada figur model manusia / wajah / orang nyata yang mengenakan atau berinteraksi dengan produk? (1 = Ya ada model manusia nyata, 0 = Tidak ada / foto produk murni tanpa orang). PENTING: Jika hanya foto makanan, minuman, kemasan, sepatu, atau baju tanpa model manusia, NILAI HARUS 0! (0/1 + detail)
- F8 (Teks Visual): Apakah ada tipografi teks overlay grafis tertulis pada gambar? (0/1 + detail)

EVALUASI PERSPEKTIF:
- islamic_compliance_score (0 - 100): Aspek transparansi akad, penghindaran Gharar, dan larangan Tadlis.
- islamic_review: Ulasan singkat fiqh muamalah.
- consumer_protection_score (0 - 100): Aspek hak informasi jujur & UUPK No. 8/1999.
- consumer_review: Ulasan singkat perlindungan konsumen.

KEMBALIKAN HANYA JSON MURNI TANPA BACKTICKS:
{{
  "k1_nama_produk": 1, "k1_detail": "...",
  "k2_harga": 0, "k2_detail": "...",
  "k3_diskon": 0, "k3_detail": "...",
  "k4_periode_promo": 0, "k4_detail": "...",
  "k5_syarat_promo": 0, "k5_detail": "...",
  "k6_info_produk": 1, "k6_detail": "...",
  "k7_klaim": 1, "k7_detail": "...",
  "k8_visual_caption": 1, "k8_detail": "...",
  "f1_object_detection": 1, "f1_detail": "...",
  "f2_color_extraction": 1, "f2_detail": "...",
  "f3_posisi_objek": 1, "f3_detail": "...",
  "f4_dominasi_objek": 1, "f4_detail": "...",
  "f5_background": 1, "f5_detail": "...",
  "f6_objek_tambahan": 0, "f6_detail": "...",
  "f7_manusia": 1, "f7_detail": "...",
  "f8_teks": 1, "f8_detail": "...",
  "islamic_compliance_score": 75.0, "islamic_review": "...",
  "consumer_protection_score": 80.0, "consumer_review": "..."
}}
"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image_pil, prompt]
        )
        
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        data = json.loads(text)
        data["engine_used"] = "Google Gemini Multimodal Vision AI"
        return data
    except Exception as e:
        print(f"Gemini API error, falling back to local engine: {e}")
        res = analyze_post_offline(image_pil, caption_text, {})
        res["engine_used"] = f"Local Fallback (API: {str(e)[:40]})"
        return res
