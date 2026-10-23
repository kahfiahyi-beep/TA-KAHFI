import cv2
import numpy as np
from PIL import Image
import os

_FACE_DETECTOR = None

def _get_face_detector():
    global _FACE_DETECTOR
    if _FACE_DETECTOR is None:
        try:
            from skimage import data as sk_data
            from skimage.feature import Cascade
            _FACE_DETECTOR = Cascade(sk_data.lbp_frontal_face_cascade_filename())
        except Exception as e:
            _FACE_DETECTOR = False
    return _FACE_DETECTOR

def analyze_visual_features(image_input):
    """
    Menganalisis karakteristik visual citra menggunakan Computer Vision (OpenCV):
    - F1 Object Detection (Deteksi objek produk & bounding box)
    - F2 Color Extraction (Ekstraksi warna dominan & palet)
    - F3 Posisi Objek (Center, Rule of Thirds, Kiri, Kanan)
    - F4 Dominasi Objek (Rasio luas area objek terhadap kanvas %)
    - F5 Background (Polos/Studio, Kompleks/Outdoor, Gradien/Bokeh)
    - F6 Objek Tambahan (Props pendukung, ornamen, stiker badge)
    - F7 Manusia (Deteksi wajah / model manusia)
    - F8 Teks Visual (Kepadatan & keberadaan tipografi teks pada gambar)
    """
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
        if img is None:
            pil_img = Image.open(image_input).convert("RGB")
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    elif isinstance(image_input, Image.Image):
        img = cv2.cvtColor(np.array(image_input.convert("RGB")), cv2.COLOR_RGB2BGR)
    elif isinstance(image_input, np.ndarray):
        img = image_input
    else:
        raise ValueError("Format gambar tidak didukung")

    h, w, c = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    total_area = float(h * w)

    # 1. Kecerahan & Kontras
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))

    # 2. F7: Deteksi Manusia / Model (Face Detection)
    face_detected = 0
    num_faces = 0
    face_boxes = []

    detector = _get_face_detector()
    if detector:
        try:
            min_dim = min(h, w)
            min_sz = max(40, int(min_dim * 0.08))
            max_sz = int(min_dim * 0.85)
            if max_sz > min_sz:
                detections = detector.detect_multi_scale(
                    gray,
                    scale_factor=1.2,
                    step_ratio=1.2,
                    min_size=(min_sz, min_sz),
                    max_size=(max_sz, max_sz),
                    min_neighbor_number=3
                )
                num_faces = len(detections)
                if num_faces > 0:
                    face_detected = 1
                    for d in detections:
                        face_boxes.append((int(d['c']), int(d['r']), int(d['width']), int(d['height'])))
        except Exception:
            face_detected = 0
            num_faces = 0

    # PENTING: Kehadiran model manusia HANYA bernilai 1 jika benar-benar terdeteksi wajah manusia.
    # Penilaian warna kulit (skin tone) dihapus karena makanan, minuman, kayu, dan kulit kerajinan
    # memicu false-positive tinggi pada foto produk UMKM.
    human_present = 1 if face_detected == 1 else 0

    # 3. F8: Deteksi Teks Visual (Typography & Edge Density)
    edges = cv2.Canny(gray, 100, 200)
    text_density = float(np.count_nonzero(edges) / total_area)
    
    # Deteksi kontur teks potensial (horizontal high-frequency boxes)
    kernel_text = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
    text_morph = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_text)
    contours_text, _ = cv2.findContours(text_morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    has_visual_text = 1 if (text_density > 0.08 or len(contours_text) > 8) else 0

    # 4. F1, F3, F4: Deteksi Objek Utama & Bounding Box Saliency
    # Gunakan thresholding adaptif & kontur terbesar di area tengah
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    main_box = None
    max_area = 0
    valid_contours = []
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > (total_area * 0.03): # minimal 3% luas kanvas
            valid_contours.append(cnt)
            if area > max_area:
                max_area = area
                main_box = cv2.boundingRect(cnt)

    if main_box is None:
        # Fallback jika kontur tunggal tidak terisolasi (gunakan crop sentral 60%)
        bx, by = int(w * 0.15), int(h * 0.15)
        bw, bh = int(w * 0.70), int(h * 0.70)
        main_box = (bx, by, bw, bh)
        max_area = bw * bh

    bx, by, bw, bh = main_box
    obj_area_ratio = round((float(bw * bh) / total_area) * 100.0, 1)
    
    # F3: Posisi Objek
    cx = bx + (bw / 2.0)
    cy = by + (bh / 2.0)
    norm_cx = cx / w
    norm_cy = cy / h
    
    if 0.35 <= norm_cx <= 0.65 and 0.35 <= norm_cy <= 0.65:
        obj_position = "Tengah (Center Composition)"
    elif norm_cx < 0.35:
        obj_position = "Sisi Kiri (Left-Aligned)"
    elif norm_cx > 0.65:
        obj_position = "Sisi Kanan (Right-Aligned)"
    elif (0.30 <= norm_cx <= 0.38 or 0.62 <= norm_cx <= 0.70):
        obj_position = "Sepertiga Bidang (Rule of Thirds)"
    else:
        obj_position = "Asimetris / Dinamis"

    # F4: Dominasi Objek
    if obj_area_ratio >= 45.0:
        obj_dominance_cat = f"Sangat Dominan ({obj_area_ratio}% kanvas - Close-up / Macro)"
    elif obj_area_ratio >= 25.0:
        obj_dominance_cat = f"Dominan Sedang ({obj_area_ratio}% kanvas - Medium Shot)"
    else:
        obj_dominance_cat = f"Rendah / Proporsional ({obj_area_ratio}% kanvas - Wide View)"

    # F5: Karakteristik Background (Cek varians pixel pada border frame 10%)
    border_pixels = []
    border_pixels.append(gray[:int(h * 0.1), :]) # Top
    border_pixels.append(gray[int(h * 0.9):, :]) # Bottom
    border_pixels.append(gray[:, :int(w * 0.1)]) # Left
    border_pixels.append(gray[:, int(w * 0.9):]) # Right
    combined_borders = np.concatenate([bp.flatten() for bp in border_pixels])
    bg_variance = float(np.std(combined_borders))
    
    if bg_variance < 18.0:
        bg_type = "Polos / Studio Clean (Solid Background)"
    elif bg_variance < 40.0:
        bg_type = "Sederhana / Gradien / Soft Bokeh"
    else:
        bg_type = "Kompleks / Real-Life Setting (Outdoor/Ramai)"

    # F6: Objek Tambahan (Props / Elemen Pendukung)
    has_extra_objects = 1 if len(valid_contours) >= 2 else 0

    # 5. F2: Ekstraksi Palet Warna Dominan (K-Means Clustering k=3)
    pixels = img.reshape((-1, 3)).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixels, 3, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    counts = np.bincount(labels.flatten())
    dominant_bgr = centers[np.argmax(counts)].astype(int)
    dominant_rgb = (int(dominant_bgr[2]), int(dominant_bgr[1]), int(dominant_bgr[0]))
    hex_color = "#{:02x}{:02x}{:02x}".format(dominant_rgb[0], dominant_rgb[1], dominant_rgb[2])
    color_name = get_color_category(dominant_rgb)

    # Ekstraksi 3 palet warna
    palette = []
    for center in centers:
        c_rgb = (int(center[2]), int(center[1]), int(center[0]))
        palette.append({
            "hex": "#{:02x}{:02x}{:02x}".format(c_rgb[0], c_rgb[1], c_rgb[2]),
            "name": get_color_category(c_rgb)
        })

    # Format Tipe Aspek
    aspect_ratio = round(w / h, 2)
    if 0.95 <= aspect_ratio <= 1.05:
        format_type = "Square (1:1 Feed)"
    elif 0.75 <= aspect_ratio <= 0.85:
        format_type = "Portrait (4:5 Feed)"
    elif aspect_ratio < 0.65:
        format_type = "Story / Reels (9:16)"
    elif aspect_ratio > 1.2:
        format_type = "Landscape (16:9)"
    else:
        format_type = f"Custom ({w}x{h})"

    return {
        "width": w,
        "height": h,
        "brightness": round(brightness, 1),
        "contrast": round(contrast, 2),
        "text_density": round(text_density, 4),
        "aspect_ratio": aspect_ratio,
        "format_type": format_type,
        "dominant_color_hex": hex_color,
        "dominant_color_name": color_name,
        "palette": palette,
        # 8 Fitur Computer Vision F1 - F8
        "f1_object_detected": 1,
        "f1_detail": "Objek produk utama berhasil diidentifikasi di dalam frame",
        "f1_box": main_box,
        "f2_color": color_name,
        "f2_hex": hex_color,
        "f2_detail": f"Warna dominan {color_name} ({hex_color}) dengan palet {', '.join([p['name'] for p in palette])}",
        "f3_posisi": obj_position,
        "f3_detail": f"Objek produk berada di posisi {obj_position}",
        "f4_dominasi": obj_dominance_cat,
        "f4_ratio": obj_area_ratio,
        "f4_detail": f"Objek mencakup {obj_area_ratio}% dari seluruh area kanvas postingan",
        "f5_background": bg_type,
        "f5_detail": f"Latar belakang citra bertipe {bg_type}",
        "f6_objek_tambahan": has_extra_objects,
        "f6_detail": "Terdapat props/ornamen dekorasi tambahan pendukung produk" if has_extra_objects else "Objek tunggal terfokus tanpa props tambahan yang ramai",
        "f7_manusia": human_present,
        "f7_detail": f"Terdeteksi kehadiran model manusia ({num_faces} wajah teridentifikasi)" if human_present == 1 else "Tanpa kehadiran model manusia (fokus produk murni)",
        "f8_teks": has_visual_text,
        "f8_detail": f"Terdeteksi tipografi/teks tertulis pada gambar (kepadatan {text_density*100:.1f}%)" if has_visual_text else "Visual bersih tanpa overlay teks grafis yang mencolok",
        "face_boxes": face_boxes,
        "face_detected": human_present,
        "num_faces": num_faces
    }

def get_color_category(rgb):
    r, g, b = rgb
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    diff = max_c - min_c
    
    if max_c < 45:
        return "Hitam / Gelap Pekat"
    if min_c > 210 and diff < 30:
        return "Putih / Terang Bersih"
    if diff < 25:
        return "Abu-abu / Netral"
    
    if r > 180 and g < 100 and b < 100:
        return "Merah Mencolok"
    elif r > 180 and g > 130 and b < 70:
        return "Kuning / Oranye Cerah"
    elif g > r and g > b:
        return "Hijau Segar"
    elif b > r and b > g:
        return "Biru Elegan"
    elif r > 140 and g < 90 and b > 140:
        return "Ungu / Magenta"
    elif r > 120 and g > 70 and b < 60:
        return "Coklat Hangat / Earth Tone"
    elif r > 200 and g > 150 and b > 150:
        return "Pastel / Soft Pink"
    return "Multi-tone"

def generate_annotated_preview(image_pil, cv_results, indicators):
    """
    Membuat visual bounding box dan indikator overlay F1-F8 dan K1-K8
    pada citra yang dianalisis.
    """
    img_cv = cv2.cvtColor(np.array(image_pil.convert("RGB")), cv2.COLOR_RGB2BGR)
    h, w, _ = img_cv.shape
    
    overlay = img_cv.copy()
    
    # 1. Gambar Bounding Box Objek Utama (F1 & F3)
    if "f1_box" in cv_results and cv_results["f1_box"]:
        bx, by, bw, bh = cv_results["f1_box"]
        # Kotak hijau neon untuk produk utama
        cv2.rectangle(img_cv, (bx, by), (bx + bw, by + bh), (0, 255, 127), 3)
        cv2.putText(img_cv, f"F1: Produk ({cv_results.get('f4_ratio', 0)}%)", (bx + 8, by + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 127), 2)
        
    # 2. Gambar Bounding Box Wajah/Manusia (F7)
    if "face_boxes" in cv_results and cv_results["face_boxes"]:
        for (fx, fy, fw, fh) in cv_results["face_boxes"]:
            cv2.rectangle(img_cv, (fx, fy), (fx + fw, fy + fh), (255, 191, 0), 3) # Cyan/Kuning
            cv2.putText(img_cv, "F7: Model", (fx + 5, fy - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 191, 0), 2)

    # 3. Label Badge K1 - K8 di Pojok Kiri Atas
    badges = []
    if indicators.get("k1_nama_produk", 0) == 1:
        badges.append(("K1: Nama Produk", (34, 139, 34)))
    if indicators.get("k2_harga", 0) == 1:
        badges.append(("K2: Harga Jelas", (0, 165, 255)))
    else:
        badges.append(("K2: Tanpa Harga", (0, 0, 205)))
        
    if indicators.get("k3_diskon", 0) == 1:
        badges.append(("K3: Promo/Diskon", (255, 105, 180)))
    if indicators.get("k7_klaim", 0) == 1:
        badges.append(("K7: Ada Klaim", (147, 20, 255)))
    if indicators.get("k8_visual_caption", 0) == 1:
        badges.append(("K8: Sinkron", (0, 200, 0)))

    y_pos = 35
    for text, color in badges:
        cv2.rectangle(overlay, (20, y_pos - 24), (220, y_pos + 6), color, -1)
        cv2.putText(overlay, text, (28, y_pos - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
        y_pos += 36

    cv2.addWeighted(overlay, 0.85, img_cv, 0.15, 0, img_cv)
    return Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
