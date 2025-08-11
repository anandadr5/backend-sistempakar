import numpy as np
from utils import gaussian_membership, get_skor_tekanan_darah, format_diagnosis_result

def normalize_symptom_keys(symptoms):
    return {
        key.lower().replace(" ", "_"): value.lower()
        for key, value in symptoms.items()
    }

def fuzzifikasi_usia(age):
    # Fuzzifikasi usia
    return {
        'bayi': gaussian_membership(age, mean=2.5, std=2),
        'anak': gaussian_membership(age, mean=7, std=2),
        'remaja': gaussian_membership(age, mean=14, std=4),
        'dewasa': gaussian_membership(age, mean=39, std=15),
        'lansia': gaussian_membership(age, mean=70, std=10)
    }

def fuzzifikasi_bmi(bmi):
    # Fuzzifikasi BMI
    return {
        'underweight': gaussian_membership(bmi, mean=16.5, std=2),
        'normal': gaussian_membership(bmi, mean=21.75, std=3),
        'overweight': gaussian_membership(bmi, mean=27.5, std=2.5),
        'obese': gaussian_membership(bmi, mean=35, std=5)
    }

def fuzzifikasi_tekanan_darah(skor_td):
    """Fuzzifikasi skor tekanan darah."""
    return {
        'rendah': gaussian_membership(skor_td, mean=-20, std=10),
        'normal': gaussian_membership(skor_td, mean=0, std=10),
        'tinggi': gaussian_membership(skor_td, mean=25, std=15),
        'sangat_tinggi': gaussian_membership(skor_td, mean=50, std=20)
    }

def fuzzifikasi_riwayat(riwayat_penyakit, riwayat_merokok, aspek_psikologis):
    """Memberikan skor fuzzy berdasarkan faktor risiko riwayat."""
    return {
        'penyakit': 1.0 if riwayat_penyakit.lower() == 'ada' else 0.0,
        'merokok': 1.0 if riwayat_merokok.lower() == 'ya' else 0.0,
        'psikologis_berat': 1.0 if aspek_psikologis.lower() in ['depresi', 'cemas', 'kecenderungan bunuh diri', 'takut', 'marah'] else 0.0,
    }

#Bobot gejala
GEJALA_WEIGHTS = {
    'nyeri_dada': 1.0,
    'sesak_napas': 1.0,
    'jantung_berdebar': 0.95,
    'keringat_dingin': 0.95,
    'bengkak_kaki': 0.8,
    'mudah_lelah': 0.7,
    'lemas': 0.5,
    'pusing': 0.4
}

def fuzzifikasi_gejala(symptoms):
    symptoms = normalize_symptom_keys(symptoms)
    base_fuzzy = {key: 1.0 if symptoms.get(key, "tidak") == "ya" else 0.0 for key in GEJALA_WEIGHTS}
    fuzzy_weighted = {key: base_fuzzy[key] * GEJALA_WEIGHTS[key] for key in base_fuzzy}
    return fuzzy_weighted, base_fuzzy

def inference_mamdani(age_fuzzy, bmi_fuzzy, gejala_fuzzy, gejala_base, tekanan_darah_fuzzy, riwayat_fuzzy):
    rules = []
    gejala_berat = max(gejala_fuzzy['nyeri_dada'], gejala_fuzzy['sesak_napas'])
    gejala_ringan = max(gejala_fuzzy['lemas'], gejala_fuzzy['pusing'], gejala_fuzzy['mudah_lelah'])
    jumlah_gejala_aktif = sum(gejala_base.values())

    # --- Aturan Prioritas (Riwayat & Tekanan Darah Darurat) ---
    if riwayat_fuzzy['penyakit'] and (gejala_berat > 0 or tekanan_darah_fuzzy['tinggi'] > 0.5):
        rules.append(('tinggi', 1.0))
    if tekanan_darah_fuzzy['sangat_tinggi'] > 0.5:
        rules.append(('tinggi', tekanan_darah_fuzzy['sangat_tinggi']))

    # --- Aturan Risiko Tinggi ---
    if min(gejala_fuzzy['nyeri_dada'], gejala_fuzzy['sesak_napas'], gejala_fuzzy['keringat_dingin']) > 0:
        rules.append(('tinggi', 0.95))
    if age_fuzzy['lansia'] > 0.5 and gejala_berat > 0:
        rules.append(('tinggi', age_fuzzy['lansia'] * 0.9))

    # --- Aturan Risiko Sedang ---
    if riwayat_fuzzy['merokok'] and bmi_fuzzy['overweight'] and tekanan_darah_fuzzy['tinggi']:
        rules.append(('sedang', 0.85))
    if riwayat_fuzzy['psikologis_berat'] and gejala_fuzzy['jantung_berdebar']:
        rules.append(('sedang', 0.8))
    if bmi_fuzzy['obese'] and (gejala_fuzzy['bengkak_kaki'] or gejala_fuzzy['sesak_napas']):
        rules.append(('sedang', 0.75))
    if jumlah_gejala_aktif >= 4 and gejala_berat > 0:
        rules.append(('sedang', 0.7))

    # --- Aturan Risiko Rendah ---
    if 1 <= jumlah_gejala_aktif <= 3 and gejala_berat == 0 and not any(riwayat_fuzzy.values()):
        rules.append(('rendah', 0.6))
    if gejala_ringan > 0 and gejala_berat == 0 and bmi_fuzzy['normal'] > 0.5:
        rules.append(('rendah', 0.5))

    # Fallback
    if not rules:
        if jumlah_gejala_aktif == 0:
            rules.append(('tidak_terdeteksi', 1.0))
        else:
            rules.append(('rendah', 0.3))
            
    return rules


def agregasi_output(rules):
    aggregated = {'rendah': 0, 'sedang': 0, 'tinggi': 0, 'tidak_terdeteksi': 0}
    for kategori, strength in rules:
        if kategori in aggregated:
            aggregated[kategori] = max(aggregated[kategori], strength)
    return aggregated

def defuzzifikasi_centroid(aggregated):
    if aggregated.get('tidak_terdeteksi') == 1.0: return 0
    risiko_params = {'rendah': {'mean': 25, 'std': 15}, 'sedang': {'mean': 55, 'std': 15}, 'tinggi': {'mean': 85, 'std': 10}}
    x_range = np.arange(0, 101, 1)
    output_membership = np.zeros_like(x_range, dtype=float)
    for kategori, strength in aggregated.items():
        if kategori in risiko_params and strength > 0:
            kategori_membership = np.array([gaussian_membership(x, **risiko_params[kategori]) for x in x_range])
            clipped = np.minimum(kategori_membership, strength)
            output_membership = np.maximum(output_membership, clipped)
    if np.sum(output_membership) == 0: return 0
    return np.sum(x_range * output_membership) / np.sum(output_membership)

def fuzzy_diagnosis(age, gender, bmi, sistolik, diastolik, riwayat_penyakit, riwayat_merokok, aspek_psikologis, symptoms):
    skor_td = get_skor_tekanan_darah(sistolik, diastolik, age, gender)
    
    age_fuzzy = fuzzifikasi_usia(age)
    bmi_fuzzy = fuzzifikasi_bmi(bmi)
    gejala_fuzzy, gejala_base = fuzzifikasi_gejala(symptoms)
    tekanan_darah_fuzzy = fuzzifikasi_tekanan_darah(skor_td)
    riwayat_fuzzy = fuzzifikasi_riwayat(riwayat_penyakit, riwayat_merokok, aspek_psikologis)

    rules_output = inference_mamdani(age_fuzzy, bmi_fuzzy, gejala_fuzzy, gejala_base, tekanan_darah_fuzzy, riwayat_fuzzy)
    
    aggregated = agregasi_output(rules_output)
    centroid_score = defuzzifikasi_centroid(aggregated)
    
    result = format_diagnosis_result(centroid_score)
    result_score = round(centroid_score, 2)

    return result['diagnosis'], result_score, result['risiko'], result['saran']