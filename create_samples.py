import os
from PIL import Image, ImageDraw, ImageFont

def generate_samples():
    samples_dir = os.path.join(os.path.dirname(__file__), "samples")
    os.makedirs(samples_dir, exist_ok=True)
    
    # 1. Sample Promo Kopi (Transparan, Ada Harga, Diskon, Halal)
    img1 = Image.new("RGB", (800, 800), color=(44, 24, 16))
    draw1 = ImageDraw.Draw(img1)
    # Background accent
    draw1.rectangle([(50, 50), (750, 750)], outline=(212, 175, 55), width=4)
    draw1.rectangle([(100, 100), (700, 200)], fill=(70, 40, 25))
    draw1.text((160, 130), "KOPI SUSU AREN BAROKAH", fill=(255, 255, 255))
    # Badge promo
    draw1.ellipse([(550, 240), (720, 410)], fill=(200, 30, 30))
    draw1.text((580, 300), "PROMO\nBELI 1\nGRATIS 1", fill=(255, 255, 255))
    # Product representation
    draw1.rounded_rectangle([(250, 260), (450, 560)], radius=20, fill=(180, 130, 90), outline=(255, 255, 255), width=3)
    draw1.text((290, 400), "[FOTO BOTOL\nKOPI AREN]", fill=(30, 20, 10))
    # Price
    draw1.rectangle([(100, 600), (400, 680)], fill=(34, 139, 34))
    draw1.text((120, 630), "HARGA: Rp 25.000,-", fill=(255, 255, 255))
    # Periode & S&K
    draw1.text((430, 615), "Berlaku: 1 - 10 Ramadhan\n*S&K Follow IG & Min Order 2", fill=(220, 220, 220))
    # Halal badge
    draw1.rounded_rectangle([(100, 700), (280, 740)], radius=5, fill=(0, 100, 0))
    draw1.text((115, 712), "100% Halal MUI & BPOM", fill=(255, 255, 255))
    img1.save(os.path.join(samples_dir, "sample_kopi_promo.jpg"))

    # 2. Sample Fashion Hijab (Tanpa Harga / DM for price)
    img2 = Image.new("RGB", (800, 800), color=(245, 235, 230))
    draw2 = ImageDraw.Draw(img2)
    draw2.rectangle([(40, 40), (760, 760)], outline=(190, 160, 150), width=3)
    draw2.text((220, 80), "ALYA VOAL PREMIUM HIJAB", fill=(80, 50, 50))
    # Model area
    draw2.rectangle([(180, 150), (620, 580)], fill=(225, 205, 195))
    draw2.text((310, 340), "[FOTO MODEL\nHIJAB SEGI EMPAT]", fill=(100, 70, 70))
    # Claim
    draw2.rectangle([(180, 600), (620, 650)], fill=(160, 110, 100))
    draw2.text((220, 618), "Klaim: Bahan Ultrafine Tegak Seharian", fill=(255, 255, 255))
    # DM for price
    draw2.rounded_rectangle([(250, 680), (550, 740)], radius=15, fill=(180, 50, 50))
    draw2.text((290, 700), "MINAT? CHAT DM UNTUK HARGA", fill=(255, 255, 255))
    img2.save(os.path.join(samples_dir, "sample_fashion_dm.jpg"))

    print("Sample images created successfully!")

if __name__ == "__main__":
    generate_samples()
