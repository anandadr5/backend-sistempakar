import numpy as np
import math
from utils import gaussian_membership, get_active_symptoms, format_diagnosis_result

def normalize_symptom_keys(symptoms):
    return {
        key.lower().replace(" ", "_"): value.lower()
        for key, value in symptoms.items()
    }

def convert_string_to_symptom_dict(gejala_str):
    return {
        symptom.strip(): "ya"
        for symptom in gejala_str.split(",")
        if symptom.strip()
    }

def fuzzifikasi_usia(age):
    # Fuzzifikasi usia
    if gender == 1:  # Laki-laki
        return {
            'bayi': gaussian_membership(age, mean=2.5, std=2),
            'anak': gaussian_membership(age, mean=7, std=2),
            'remaja': gaussian_membership(age, mean=14, std=4),
            'dewasa': gaussian_membership(age, mean=39, std=15),
            'lansia': gaussian_membership(age, mean=70, std=10)
        }
    else:  # Perempuan
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

def fuzzifikasi_tekanan_darah(sistolik, diastolik, age, gender):
    #Fuzzifikasi Tekanan Darah
    
    if gender == 0:  # Perempuan
        if 18 <= age <= 39:
            normal_sistolik, normal_diastolik = 110, 68
        elif 40 <= age <= 59:
            normal_sistolik, normal_diastolik = 122, 74
        else:  # >= 60
            normal_sistolik, normal_diastolik = 139, 68
    else:  # Laki-laki
        if 18 <= age <= 39:
            normal_sistolik, normal_diastolik = 119, 70
        elif 40 <= age <= 59:
            normal_sistolik, normal_diastolik = 124, 77
        else:  # >= 60
            normal_sistolik, normal_diastolik = 133, 69
    
    # Fuzzifikasi berdasarkan klasifikasi standar
    td_fuzzy = {
        'hipotensi': min(
            gaussian_membership(sistolik, mean=85, std=5) if sistolik < 90 else 0,
            gaussian_membership(diastolik, mean=55, std=5) if diastolik < 60 else 0
        ),
        'normal': min(
            gaussian_membership(sistolik, mean=normal_sistolik, std=15),
            gaussian_membership(diastolik, mean=normal_diastolik, std=10)
        ),
        'prehipertensi': min(
            gaussian_membership(sistolik, mean=130, std=9),
            gaussian_membership(diastolik, mean=85, std=4)
        ),
        'hipertensi_1': min(
            gaussian_membership(sistolik, mean=150, std=9),
            gaussian_membership(diastolik, mean=95, std=4)
        ),
        'hipertensi_2': min(
            gaussian_membership(sistolik, mean=170, std=9),
            gaussian_membership(diastolik, mean=105, std=4)
        ),
        'hipertensi_darurat': min(
            gaussian_membership(sistolik, mean=190, std=10) if sistolik >= 180 else 0,
            gaussian_membership(diastolik, mean=115, std=5) if diastolik >= 110 else 0
        )
    }
    
    return td_fuzzy

def fuzzifikasi_riwayat_penyakit(riwayat_penyakit):
    #Fuzzifikasi Riwayat Penyakit
    return 1.0 if riwayat_penyakit.lower() in ['ada', 'ya', '1'] else 0.0

def fuzzifikasi_riwayat_merokok(riwayat_merokok):
    #Fuzzifikasi Riwayat Merokok
    return 1.0 if riwayat_merokok.lower() in ['ya', 'iya', '1'] else 0.0

def fuzzifikasi_aspek_psikologis(aspek_psikologis):
    #Fuzzifikasi Aspek Psikologis
    aspek_mapping = {
        'tenang': {'stres_rendah': 1.0, 'stres_sedang': 0.0, 'stres_tinggi': 0.0},
        'takut': {'stres_rendah': 0.2, 'stres_sedang': 0.8, 'stres_tinggi': 0.0},
        'marah': {'stres_rendah': 0.0, 'stres_sedang': 0.7, 'stres_tinggi': 0.3},
        'depresi': {'stres_rendah': 0.0, 'stres_sedang': 0.3, 'stres_tinggi': 0.7},
        'cemas': {'stres_rendah': 0.0, 'stres_sedang': 0.6, 'stres_tinggi': 0.4},
        'kecenderungan bunuh diri': {'stres_rendah': 0.0, 'stres_sedang': 0.0, 'stres_tinggi': 1.0}
    }
    
    return aspek_mapping.get(aspek_psikologis.lower(), {'stres_rendah': 0.0, 'stres_sedang': 0.0, 'stres_tinggi': 0.0})

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
    # Fuzzifikasi gejala
    if isinstance(symptoms, str):
        symptoms = convert_string_to_symptom_dict(symptoms)

    symptoms = normalize_symptom_keys(symptoms)
    print(f"🔍 DEBUG - Normalized symptoms input: {symptoms}")

    base_fuzzy = {
        'nyeri_dada': 1.0 if symptoms.get("nyeri_dada", "tidak") == "ya" else 0.0,
        'sesak_napas': 1.0 if symptoms.get("sesak_napas", "tidak") == "ya" else 0.0,
        'pusing': 1.0 if symptoms.get("pusing", "tidak") == "ya" else 0.0,
        'lemas': 1.0 if symptoms.get("lemas", "tidak") == "ya" else 0.0,
        'jantung_berdebar': 1.0 if symptoms.get("jantung_berdebar", "tidak") == "ya" else 0.0,
        'mudah_lelah': 1.0 if symptoms.get("mudah_lelah", "tidak") == "ya" else 0.0,
        'bengkak_kaki': 1.0 if symptoms.get("bengkak_kaki", "tidak") == "ya" else 0.0,
        'keringat_dingin': 1.0 if symptoms.get("keringat_dingin", "tidak") == "ya" else 0.0
    }

    fuzzy_weighted = {key: base_fuzzy[key] * GEJALA_WEIGHTS[key] for key in base_fuzzy}
    return fuzzy_weighted, base_fuzzy

def inference_mamdani_enhanced(age_fuzzy, bmi_fuzzy, td_fuzzy, gejala_fuzzy, gejala_base, 
                              riwayat_penyakit, riwayat_merokok, psikologis_fuzzy, age, gender):
#Inferensi Mamdani
    rules = []
    total_gejala = sum(gejala_fuzzy.values())
    gejala_berat = max(
        gejala_fuzzy['nyeri_dada'],
        gejala_fuzzy['sesak_napas'],
        gejala_fuzzy['jantung_berdebar'],
        gejala_fuzzy['keringat_dingin']
    )
    jumlah_gejala_aktif = sum(1 for value in gejala_base.values() if value > 0)

    print(f"DEBUG - jumlah_gejala_aktif: {jumlah_gejala_aktif}")
    print(f"DEBUG - total_gejala: {total_gejala}")
    
    # Rule 1: Hipertensi darurat dengan gejala berat
    rule1 = min(td_fuzzy['hipertensi_darurat'], gejala_berat)
    if rule1 > 0.1: 
        rules.append(('tinggi', min(rule1 * 1.2, 1.0)))
    
    # Rule 2: Nyeri dada + keringat dingin + sesak napas
    rule2 = min(gejala_fuzzy['nyeri_dada'], gejala_fuzzy['keringat_dingin'], gejala_fuzzy['sesak_napas'])
    if rule2 > 0.1: 
        rules.append(('tinggi', rule2))
    
    # Rule 3: Nyeri dada + jantung berdebar + riwayat penyakit
    rule3 = min(gejala_fuzzy['nyeri_dada'], gejala_fuzzy['jantung_berdebar'], riwayat_penyakit)
    if rule3 > 0.1: 
        rules.append(('tinggi', rule3))
    
    # Rule 4: Sesak napas + bengkak kaki + mudah lelah
    rule4 = min(gejala_fuzzy['sesak_napas'], gejala_fuzzy['bengkak_kaki'], gejala_fuzzy['mudah_lelah'])
    if rule4 > 0.1: 
        rules.append(('tinggi', rule4))
    
    # Rule 5: Lansia + hipertensi + riwayat merokok
    rule5 = min(age_fuzzy['lansia'], 
                max(td_fuzzy['hipertensi_1'], td_fuzzy['hipertensi_2']), 
                riwayat_merokok)
    if rule5 > 0.1: 
        rules.append(('tinggi', rule5))
    
    # Rule 6: Bayi/anak dengan gejala berat
    usia_kecil = max(age_fuzzy['bayi'], age_fuzzy['anak'])
    rule6 = min(usia_kecil, gejala_berat)
    if rule6 > 0.1: 
        rules.append(('tinggi', rule6))
    
    # Rule 7: Hipertensi + Obesitas + Stres Tinggi
    rule7 = min(max(td_fuzzy['hipertensi_1'], td_fuzzy['hipertensi_2']), 
                bmi_fuzzy['obese'], 
                psikologis_fuzzy['stres_tinggi'])
    if rule7 > 0.1: 
        rules.append(('tinggi', rule7))
    
    # Rule 8: Prehipertensi + Overweight + Gejala Ringan
    gejala_ringan = max(gejala_fuzzy['mudah_lelah'], gejala_fuzzy['pusing'], gejala_fuzzy['lemas'])
    rule8 = min(td_fuzzy['prehipertensi'], bmi_fuzzy['overweight'], gejala_ringan)
    if rule8 > 0.1: 
        rules.append(('sedang', rule8))
    
    # Rule 9: Jantung berdebar + pusing + riwayat penyakit
    rule9 = min(gejala_fuzzy['jantung_berdebar'], gejala_fuzzy['pusing'], riwayat_penyakit)
    if rule9 > 0.1: 
        rules.append(('sedang', rule9))
    
    # Rule 10: Obesitas + Multiple Gejala Ringan
    rule10 = min(bmi_fuzzy['obese'], min(0.8, total_gejala / 4))
    if rule10 > 0.1 and gejala_berat == 0: 
        rules.append(('sedang', rule10))
    
    # Rule 11: Stres Psikologis + Gejala Fisik
    rule11 = min(max(psikologis_fuzzy['stres_sedang'], psikologis_fuzzy['stres_tinggi']), 
                 max(gejala_fuzzy['jantung_berdebar'], gejala_fuzzy['pusing']))
    if rule11 > 0.1: 
        rules.append(('sedang', rule11))
    
    # Rule 12: Hipotensi dengan gejala
    rule12 = min(td_fuzzy['hipotensi'], max(gejala_fuzzy['pusing'], gejala_fuzzy['lemas']))
    if rule12 > 0.1: 
        rules.append(('sedang', rule12))
    
    # Rule 13: Faktor Risiko Gender-Spesifik
    if gender == 1 and age >= 45:  # Pria >= 45 tahun
        rule13 = min(age_fuzzy['dewasa'], max(td_fuzzy['prehipertensi'], riwayat_merokok))
        if rule13 > 0.1: 
            rules.append(('sedang', rule13))
    elif gender == 0 and age >= 55:  # Wanita >= 55 tahun
        rule13 = min(age_fuzzy['lansia'], max(td_fuzzy['prehipertensi'], bmi_fuzzy['overweight']))
        if rule13 > 0.1: 
            rules.append(('sedang', rule13))
    
    # Rule 14: Tekanan darah normal + BMI normal + tidak ada gejala berat
    rule14 = min(td_fuzzy['normal'], bmi_fuzzy['normal'], 1 - gejala_berat)
    if rule14 > 0.3 and jumlah_gejala_aktif <= 2: 
        rules.append(('rendah', rule14))
    
    # Rule 15: Remaja/Dewasa Muda Sehat
    rule15 = min(max(age_fuzzy['remaja'], age_fuzzy['dewasa']), 
                 td_fuzzy['normal'], 
                 max(bmi_fuzzy['normal'], bmi_fuzzy['overweight']),
                 psikologis_fuzzy['stres_rendah'])
    if rule15 > 0.2 and total_gejala <= 1: 
        rules.append(('rendah', rule15))
    
    # Rule 16: Tidak Terdeteksi - Kondisi optimal
    if jumlah_gejala_aktif == 0:
        optimal_condition = min(td_fuzzy['normal'], 
                               max(bmi_fuzzy['normal'], bmi_fuzzy['overweight']),
                               psikologis_fuzzy['stres_rendah'])
        if optimal_condition > 0.5:
            return [('tidak_terdeteksi', 1.0)]
    
    # Fallback jika tidak ada rules yang terpicu
    if len(rules) == 0:
        if jumlah_gejala_aktif == 0:
            return [('tidak_terdeteksi', 1.0)]
        else:
            return [('rendah', 0.3)]
    
    return rules

def agregasi_output(rules):
    # Agregasi output
    aggregated = {'rendah': 0, 'sedang': 0, 'tinggi': 0}
    for kategori, strength in rules:
        if kategori in aggregated:
            aggregated[kategori] = max(aggregated[kategori], strength)
    return aggregated

def defuzzifikasi_centroid(aggregated):
    # Defuzzifikasi centroid
    risiko_params = {
        'rendah': {'mean': 25, 'std': 15},
        'sedang': {'mean': 50, 'std': 15},
        'tinggi': {'mean': 75, 'std': 15}
    }

    x_range = np.arange(0, 101, 1)
    output_membership = np.zeros_like(x_range, dtype=float)
    
    for kategori, strength in aggregated.items():
        if strength > 0:
            kategori_membership = np.array([
                gaussian_membership(x, **risiko_params[kategori]) for x in x_range
            ])
            clipped = np.minimum(kategori_membership, strength)
            output_membership = np.maximum(output_membership, clipped)
    
    if np.sum(output_membership) == 0:
        return 0
        
    numerator = np.sum(x_range * output_membership)
    denominator = np.sum(output_membership)
    return numerator / denominator

def fuzzy_diagnosis_enhanced(age, gender, bmi, sistolik, diastolik, symptoms, 
                            riwayat_penyakit, riwayat_merokok, aspek_psikologis):
    
    # Konversi tipe data
    age = int(age)
    gender = int(gender)  # 1 = Laki-laki, 0 = Perempuan
    bmi = float(bmi)
    sistolik = float(sistolik)
    diastolik = float(diastolik)
    
    # Fuzzifikasi semua parameter
    age_fuzzy = fuzzifikasi_usia(age, gender)
    bmi_fuzzy = fuzzifikasi_bmi(bmi)
    td_fuzzy = fuzzifikasi_tekanan_darah(sistolik, diastolik, age, gender)
    gejala_fuzzy, gejala_base = fuzzifikasi_gejala(symptoms)
    riwayat_penyakit_fuzzy = fuzzifikasi_riwayat_penyakit(riwayat_penyakit)
    riwayat_merokok_fuzzy = fuzzifikasi_riwayat_merokok(riwayat_merokok)
    psikologis_fuzzy = fuzzifikasi_aspek_psikologis(aspek_psikologis)
    
    # Inferensi
    rules_output = inference_mamdani_enhanced(
        age_fuzzy, bmi_fuzzy, td_fuzzy, gejala_fuzzy, gejala_base,
        riwayat_penyakit_fuzzy, riwayat_merokok_fuzzy, psikologis_fuzzy, age, gender
    )
    
    # Agregasi
    aggregated = agregasi_output(rules_output)
    
    # Defuzzifikasi
    centroid_score = defuzzifikasi_centroid(aggregated)
    
    # Format hasil
    result = format_diagnosis_result(centroid_score)
    result_score = round(centroid_score, 2)
    
    return result['diagnosis'], result_score, result['risiko'], result['saran']

def fuzzy_diagnosis(age, gender, bmi, symptoms, sistolik=120, diastolik=80, 
                   riwayat_penyakit="tidak ada", riwayat_merokok="tidak", 
                   aspek_psikologis="tenang"):
    return fuzzy_diagnosis_enhanced(age, gender, bmi, sistolik, diastolik, symptoms,
                                   riwayat_penyakit, riwayat_merokok, aspek_psikologis)