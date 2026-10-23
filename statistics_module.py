import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

def get_descriptive_stats(df):
    """
    Menghitung statistik deskriptif untuk variabel penelitian.
    """
    if df.empty:
        return {}
        
    num_cols = ["followers", "likes", "comments", "total_visible_engagement", "shares", "saves", "engagement_rate", "islamic_compliance_score", "consumer_protection_score"]
    available_cols = [c for c in num_cols if c in df.columns]
    
    desc_df = df[available_cols].describe().T
    desc_df["median"] = df[available_cols].median()
    
    # Frekuensi indikator K1 - K8
    indicator_cols = [f"k{i}_{name}" for i, name in [
        (1, "nama_produk"), (2, "harga"), (3, "diskon"), (4, "periode_promo"),
        (5, "syarat_promo"), (6, "info_produk"), (7, "klaim"), (8, "visual_caption")
    ] if f"k{i}_{name}" in df.columns]
    
    k_summary = []
    for col in indicator_cols:
        count_yes = int(df[col].sum())
        total = len(df)
        pct = round((count_yes / total) * 100, 2) if total > 0 else 0
        k_summary.append({
            "Indikator": col.upper().replace("_", " "),
            "Jumlah (Ada)": count_yes,
            "Jumlah (Tidak Ada)": total - count_yes,
            "Persentase (%)": pct
        })
        
    return {
        "numeric_summary": desc_df,
        "indicator_summary": pd.DataFrame(k_summary)
    }

def calculate_correlations(df, target_col="total_visible_engagement"):
    """
    Menghitung korelasi Pearson dan Spearman antara indikator K1-K8
    dengan metrik target (Total Visible Engagement).
    """
    if df.empty or len(df) < 2:
        return pd.DataFrame()
        
    if target_col not in df.columns:
        target_col = "engagement_rate" if "engagement_rate" in df.columns else df.columns[0]

    indicator_cols = [c for c in [
        "k1_nama_produk", "k2_harga", "k3_diskon", "k4_periode_promo",
        "k5_syarat_promo", "k6_info_produk", "k7_klaim", "k8_visual_caption",
        "cv_brightness", "cv_contrast", "cv_text_density",
        "islamic_compliance_score", "consumer_protection_score"
    ] if c in df.columns]
    
    results = []
    y = df[target_col].astype(float)
    
    for col in indicator_cols:
        x = df[col].astype(float)
        # Pearson
        try:
            r_p, p_p = stats.pearsonr(x, y)
        except Exception:
            r_p, p_p = 0.0, 1.0
            
        # Spearman
        try:
            r_s, p_s = stats.spearmanr(x, y)
        except Exception:
            r_s, p_s = 0.0, 1.0
            
        # Interpretasi kekuatan
        abs_r = abs(r_p)
        if abs_r >= 0.7:
            kekuatan = "Sangat Kuat"
        elif abs_r >= 0.5:
            kekuatan = "Kuat"
        elif abs_r >= 0.3:
            kekuatan = "Sedang"
        elif abs_r >= 0.1:
            kekuatan = "Lemah"
        else:
            kekuatan = "Sangat Lemah / Tidak Ada"
            
        arah = "Positif (+)" if r_p > 0 else ("Negatif (-)" if r_p < 0 else "Netral")
        signifikan = "Signifikan (p < 0.05)" if p_p < 0.05 else "Tidak Signifikan (p >= 0.05)"
        
        results.append({
            "Variabel": col.upper().replace("_", " "),
            "Korelasi Pearson (r)": round(r_p, 4),
            "p-value (Pearson)": round(p_p, 4),
            "Korelasi Spearman (rho)": round(r_s, 4),
            "p-value (Spearman)": round(p_s, 4),
            "Arah": arah,
            "Kekuatan Hubungan": kekuatan,
            "Signifikansi (alpha 5%)": signifikan
        })
        
    return pd.DataFrame(results)

def calculate_group_comparisons(df, target_col="total_visible_engagement"):
    """
    Uji komparasi (t-test) rata-rata Total Visible Engagement antara postingan
    yang memiliki indikator (1) vs tidak memiliki indikator (0).
    """
    if df.empty or len(df) < 3:
        return pd.DataFrame()
        
    if target_col not in df.columns:
        target_col = "engagement_rate" if "engagement_rate" in df.columns else df.columns[0]

    indicator_cols = [c for c in [
        "k1_nama_produk", "k2_harga", "k3_diskon", "k4_periode_promo",
        "k5_syarat_promo", "k6_info_produk", "k7_klaim", "k8_visual_caption"
    ] if c in df.columns]
    
    comparisons = []
    for col in indicator_cols:
        group_1 = df[df[col] == 1][target_col].dropna()
        group_0 = df[df[col] == 0][target_col].dropna()
        
        mean_1 = round(group_1.mean(), 2) if len(group_1) > 0 else 0.0
        mean_0 = round(group_0.mean(), 2) if len(group_0) > 0 else 0.0
        diff = round(mean_1 - mean_0, 2)
        
        if len(group_1) > 1 and len(group_0) > 1:
            try:
                t_stat, p_val = stats.ttest_ind(group_1, group_0, equal_var=False)
            except Exception:
                t_stat, p_val = 0.0, 1.0
        else:
            t_stat, p_val = 0.0, 1.0
            
        unit = " Interaksi" if target_col == "total_visible_engagement" else "%"
        comparisons.append({
            "Indikator": col.upper().replace("_", " "),
            "Mean TVE (Ada = 1)": f"{mean_1}{unit}",
            "Mean TVE (Tidak = 0)": f"{mean_0}{unit}",
            "Selisih TVE": f"{'+' if diff > 0 else ''}{diff}{unit}",
            "t-statistic": round(t_stat, 3),
            "p-value": round(p_val, 4),
            "Kesimpulan Beda": "Berbeda Signifikan" if p_val < 0.05 else "Tidak Berbeda Nyata"
        })
        
    return pd.DataFrame(comparisons)

def run_ols_regression(df, target_col="total_visible_engagement"):
    """
    Regresi Linier Berganda:
    Total Visible Engagement = b0 + b1*K1 + b2*K2 + ... + b8*K8
    """
    if df.empty or len(df) < 5:
        return {"status": "error", "message": "Dibutuhkan minimal 5 data postingan untuk menjalankan regresi berganda."}
        
    if target_col not in df.columns:
        target_col = "engagement_rate" if "engagement_rate" in df.columns else df.columns[0]

    x_cols = [c for c in [
        "k1_nama_produk", "k2_harga", "k3_diskon", "k4_periode_promo",
        "k5_syarat_promo", "k6_info_produk", "k7_klaim", "k8_visual_caption"
    ] if c in df.columns]
    
    X = df[x_cols].astype(float)
    y = df[target_col].astype(float)
    
    # Cek varians
    valid_cols = [col for col in x_cols if X[col].std() > 0]
    if not valid_cols:
        return {"status": "error", "message": "Varians data indikator masih nol (nilai sama semua)."}
        
    X_clean = X[valid_cols]
    model = LinearRegression()
    model.fit(X_clean, y)
    
    y_pred = model.predict(X_clean)
    r2 = r2_score(y, y_pred)
    n = len(y)
    p = len(valid_cols)
    adj_r2 = 1 - (1 - r2) * (n - 1) / (n - p - 1) if (n - p - 1) > 0 else r2
    
    coef_df = pd.DataFrame({
        "Variabel": ["(Konstanta)"] + [c.upper().replace("_", " ") for c in valid_cols],
        "Koefisien (Beta)": [round(model.intercept_, 4)] + [round(c, 4) for c in model.coef_],
        "Dampak ke TVE": ["Titik Dasar TVE"] + [("Meningkatkan TVE" if c > 0 else "Menurunkan TVE") for c in model.coef_]
    })
    
    return {
        "status": "success",
        "r_squared": round(r2, 4),
        "adj_r_squared": round(adj_r2, 4),
        "f_stat": "Tersedia di Gretl/SPSS",
        "n_samples": n,
        "coefficients_table": coef_df
    }
