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
    
    # Definisi variabel untuk kemudahan
    gejala_mayor = max(gejala_fuzzy['nyeri_dada'], gejala_fuzzy['sesak_napas'])
    gejala_minor = max(gejala_fuzzy['jantung_berdebar'], gejala_fuzzy['keringat_dingin'], 
                      gejala_fuzzy['bengkak_kaki'], gejala_fuzzy['mudah_lelah'])
    gejala_non_spesifik = max(gejala_fuzzy['lemas'], gejala_fuzzy['pusing'])
    jumlah_gejala_aktif = sum(gejala_base.values())
    
    # Kombinasi gejala bermakna secara medis
    chest_pain_syndrome = min(gejala_fuzzy['nyeri_dada'], gejala_fuzzy['keringat_dingin'])
    heart_failure_syndrome = min(gejala_fuzzy['sesak_napas'], gejala_fuzzy['bengkak_kaki'])
    angina_syndrome = min(gejala_fuzzy['nyeri_dada'], gejala_fuzzy['mudah_lelah'])

    # --- ATURAN RISIKO TINGGI (Red Flags) ---
    
    # Rule 1: Sindrom Koroner Akut (chest pain + cold sweat)
    if chest_pain_syndrome > 0.5:
        rules.append(('tinggi', 0.95))
    
    # Rule 2: Nyeri dada pada usia berisiko tinggi
    if gejala_fuzzy['nyeri_dada'] > 0 and (age_fuzzy['dewasa'] > 0.7 or age_fuzzy['lansia'] > 0.3):
        strength = min(gejala_fuzzy['nyeri_dada'], max(age_fuzzy['dewasa'] * 0.7, age_fuzzy['lansia']))
        rules.append(('tinggi', strength * 0.9))
    
    # Rule 3: Multiple major symptoms
    if gejala_fuzzy['nyeri_dada'] > 0 and gejala_fuzzy['sesak_napas'] > 0:
        strength = min(gejala_fuzzy['nyeri_dada'], gejala_fuzzy['sesak_napas'])
        rules.append(('tinggi', strength * 0.85))
    
    # Rule 4: Riwayat penyakit + gejala mayor
    if riwayat_fuzzy['penyakit'] > 0 and gejala_mayor > 0.3:
        rules.append(('tinggi', min(1.0, gejala_mayor * 1.2) * 0.9))
    
    # Rule 5: Hipertensi berat + gejala
    if tekanan_darah_fuzzy['sangat_tinggi'] > 0.6 and (gejala_mayor > 0 or gejala_minor > 0):
        strength = min(tekanan_darah_fuzzy['sangat_tinggi'], max(gejala_mayor, gejala_minor))
        rules.append(('tinggi', strength * 0.85))
    
    # Rule 6: Sindrom gagal jantung
    if heart_failure_syndrome > 0.4:
        rules.append(('tinggi', heart_failure_syndrome * 0.8))

    # --- ATURAN RISIKO SEDANG (Intermediate Risk) ---
    
    # Rule 7: Angina pada aktivitas (chest pain + fatigue)
    if angina_syndrome > 0.3:
        rules.append(('sedang', angina_syndrome * 0.8))
    
    # Rule 8: Faktor risiko multipel tanpa gejala mayor
    faktor_risiko = (riwayat_fuzzy['merokok'] + 
                    max(bmi_fuzzy['overweight'], bmi_fuzzy['obese']) + 
                    max(tekanan_darah_fuzzy['tinggi'], tekanan_darah_fuzzy['sangat_tinggi']))
    if faktor_risiko >= 2 and gejala_minor > 0:
        strength = min(faktor_risiko / 3, 1.0) * max(gejala_minor, 0.3)
        rules.append(('sedang', strength * 0.75))
    
    # Rule 9: Obesitas + hipertensi + gejala
    if (bmi_fuzzy['obese'] > 0.5 and tekanan_darah_fuzzy['tinggi'] > 0.5 and 
        (gejala_fuzzy['bengkak_kaki'] > 0 or gejala_fuzzy['sesak_napas'] > 0)):
        strength = min(bmi_fuzzy['obese'], tekanan_darah_fuzzy['tinggi'])
        rules.append(('sedang', strength * 0.7))
    
    # Rule 10: Palpitasi + faktor psikologis + faktor risiko lain
    if (gejala_fuzzy['jantung_berdebar'] > 0.5 and riwayat_fuzzy['psikologis_berat'] > 0 and
        (riwayat_fuzzy['merokok'] > 0 or tekanan_darah_fuzzy['tinggi'] > 0.3)):
        rules.append(('sedang', 0.6))
    
    # Rule 11: Multiple minor symptoms
    if jumlah_gejala_aktif >= 3 and gejala_mayor == 0 and gejala_minor > 0.5:
        rules.append(('sedang', 0.65))
    
    # Rule 12: Usia lanjut + gejala non-spesifik + faktor risiko
    if (age_fuzzy['lansia'] > 0.6 and gejala_non_spesifik > 0 and
        (riwayat_fuzzy['merokok'] > 0 or tekanan_darah_fuzzy['tinggi'] > 0)):
        strength = age_fuzzy['lansia'] * 0.8
        rules.append(('sedang', strength * 0.6))

    # --- ATURAN RISIKO RENDAH (Low Risk) ---
    
    # Rule 13: Gejala non-spesifik pada usia muda dengan BMI normal
    if (gejala_non_spesifik > 0 and age_fuzzy['dewasa'] < 0.5 and 
        bmi_fuzzy['normal'] > 0.5 and not any(riwayat_fuzzy.values())):
        rules.append(('rendah', 0.5))
    
    # Rule 14: Single minor symptom tanpa faktor risiko
    if (jumlah_gejala_aktif == 1 and gejala_mayor == 0 and 
        not any(riwayat_fuzzy.values()) and tekanan_darah_fuzzy['normal'] > 0.5):
        rules.append(('rendah', 0.6))
    
    # Rule 15: Palpitasi isolated dengan stress
    if (gejala_fuzzy['jantung_berdebar'] > 0.5 and jumlah_gejala_aktif <= 2 and
        riwayat_fuzzy['psikologis_berat'] > 0 and gejala_mayor == 0):
        rules.append(('rendah', 0.55))
    
    # Rule 16: Fatigue isolated pada kondisi normal
    if (gejala_fuzzy['mudah_lelah'] > 0.5 and jumlah_gejala_aktif <= 2 and
        tekanan_darah_fuzzy['normal'] > 0.5 and bmi_fuzzy['normal'] > 0.3):
        rules.append(('rendah', 0.4))

    # --- ATURAN DEFAULT ---
    
    # Rule 17: Tidak ada gejala
    if jumlah_gejala_aktif == 0:
        if any(riwayat_fuzzy.values()) or tekanan_darah_fuzzy['tinggi'] > 0.5:
            rules.append(('rendah', 0.3))  # Masih ada faktor risiko
        else:
            rules.append(('tidak_terdeteksi', 1.0))
    
    # Fallback jika tidak ada rule yang terpicu
    if not rules:
        if jumlah_gejala_aktif > 0:
            rules.append(('rendah', 0.3))
        else:
            rules.append(('tidak_terdeteksi', 0.5))
            
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