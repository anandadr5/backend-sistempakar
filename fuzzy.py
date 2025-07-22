import numpy as np
from utils import gaussian_membership, normalize_symptoms, get_active_symptoms, format_diagnosis_result, print_debug_info

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

GEJALA_WEIGHTS = {
    'nyeri_dada': 0.9,
    'sesak_napas': 0.85,
    'pusing': 0.4,
    'lemas': 0.5,
    'jantung_berdebar': 0.75,
    'mudah_lelah': 0.6,
    'bengkak_kaki': 0.7,
    'keringat_dingin': 0.8
}

def fuzzifikasi_gejala(symptoms):
    # Fuzzifikasi gejala
    symptoms_norm = normalize_symptoms(symptoms)
    base_fuzzy = {
        'nyeri_dada': 1.0 if symptoms_norm.get("nyeri dada", "tidak") == "ya" else 0.0,
        'sesak_napas': 1.0 if symptoms_norm.get("sesak napas", "tidak") == "ya" else 0.0,
        'pusing': 1.0 if symptoms_norm.get("pusing", "tidak") == "ya" else 0.0,
        'lemas': 1.0 if symptoms_norm.get("lemas", "tidak") == "ya" else 0.0,
        'jantung_berdebar': 1.0 if symptoms_norm.get("jantung berdebar", "tidak") == "ya" else 0.0,
        'mudah_lelah': 1.0 if symptoms_norm.get("mudah lelah", "tidak") == "ya" else 0.0,
        'bengkak_kaki': 1.0 if symptoms_norm.get("bengkak pada kaki", "tidak") == "ya" else 0.0,
        'keringat_dingin': 1.0 if symptoms_norm.get("keringat dingin", "tidak") == "ya" else 0.0
    }
    fuzzy_weighted = {key: base_fuzzy[key] * GEJALA_WEIGHTS[key] for key in base_fuzzy}
    return fuzzy_weighted

def inference_mamdani(age_fuzzy, bmi_fuzzy, gejala_fuzzy):
    rules = []
    total_gejala = sum(gejala_fuzzy.values())
    gejala_berat = max(
        gejala_fuzzy['nyeri_dada'],
        gejala_fuzzy['sesak_napas'],
        gejala_fuzzy['jantung_berdebar'],
        gejala_fuzzy['keringat_dingin']
    )

    # Tidak ada gejala sama sekali
    if total_gejala == 0:
        return [('tidak_terdeteksi', 1.0)]

    # Rule 1: Lansia + nyeri dada → Risiko Tinggi
    rule1 = min(age_fuzzy['lansia'], gejala_fuzzy['nyeri_dada'])
    if rule1 > 0.1: rules.append(('tinggi', rule1))

    # Rule 2: Nyeri dada + keringat dingin + sesak napas → Risiko Tinggi
    rule2 = min(gejala_fuzzy['nyeri_dada'], gejala_fuzzy['keringat_dingin'], gejala_fuzzy['sesak_napas'])
    if rule2 > 0.1: rules.append(('tinggi', rule2))

    # Rule 3: Obesitas + bengkak kaki + mudah lelah → Risiko Tinggi
    rule3 = min(bmi_fuzzy['obese'], gejala_fuzzy['bengkak_kaki'], gejala_fuzzy['mudah_lelah'])
    if rule3 > 0.1: rules.append(('tinggi', rule3))

    # Rule 4: Nyeri dada + jantung berdebar + sesak napas → Risiko Tinggi
    rule4 = min(gejala_fuzzy['nyeri_dada'], gejala_fuzzy['jantung_berdebar'], gejala_fuzzy['sesak_napas'])
    if rule4 > 0.1: rules.append(('tinggi', rule4))

    # Rule 5: Bayi/anak + keringat dingin + sesak napas → Risiko Tinggi
    usia_kecil = max(age_fuzzy['bayi'], age_fuzzy['anak'])
    rule5 = min(usia_kecil, gejala_fuzzy['keringat_dingin'], gejala_fuzzy['sesak_napas'])
    if rule5 > 0.1: rules.append(('tinggi', rule5))

    # Rule 6: Dewasa + overweight/obese + mudah lelah → Risiko Sedang
    rule6 = min(age_fuzzy['dewasa'], max(bmi_fuzzy['overweight'], bmi_fuzzy['obese']), gejala_fuzzy['mudah_lelah'])
    if rule6 > 0.1: rules.append(('sedang', rule6))

    # Rule 7: Nyeri dada ringan + jantung berdebar tanpa keringat dingin → Risiko Sedang
    rule7 = min(gejala_fuzzy['nyeri_dada'], gejala_fuzzy['jantung_berdebar'], 1 - gejala_fuzzy['keringat_dingin'])
    if rule7 > 0.1: rules.append(('sedang', rule7))

    # Rule 8: Sesak napas + mudah lelah + BMI tinggi → Risiko Sedang
    rule8 = min(gejala_fuzzy['sesak_napas'], gejala_fuzzy['mudah_lelah'], max(bmi_fuzzy['overweight'], bmi_fuzzy['obese']))
    if rule8 > 0.1: rules.append(('sedang', rule8))

    # Rule 9: ≥4 gejala aktif tanpa nyeri dada → Risiko Sedang
    if total_gejala >= 4 and gejala_fuzzy['nyeri_dada'] == 0:
        rule9 = min(0.9, total_gejala / 8)
        rules.append(('sedang', rule9))

    # Rule 10: Usia remaja/dewasa + BMI normal + gejala ringan → Risiko Rendah
    gejala_ringan = max(gejala_fuzzy['lemas'], gejala_fuzzy['pusing'], gejala_fuzzy['mudah_lelah'])
    rule10 = min(max(age_fuzzy['remaja'], age_fuzzy['dewasa']), bmi_fuzzy['normal'], gejala_ringan)
    if rule10 > 0.1 and gejala_berat == 0:
        rules.append(('rendah', rule10))

    # Rule 11: 2–3 gejala ringan tanpa gejala berat → Risiko Rendah
    if 2 <= total_gejala <= 3 and gejala_berat == 0:
        rule11 = min(0.7, total_gejala / 8)
        rules.append(('rendah', rule11))

    # Rule 12: Nyeri dada tunggal pada usia muda dan BMI normal → Risiko Rendah
    if gejala_fuzzy['nyeri_dada'] > 0 and total_gejala == 1:
        usia_muda = max(age_fuzzy['remaja'], age_fuzzy['dewasa'])
        rule12 = min(usia_muda, bmi_fuzzy['normal'], gejala_fuzzy['nyeri_dada'])
        if rule12 > 0.1:
            rules.append(('rendah', rule12))

    # Kriteria "tidak terdeteksi" untuk gejala ringan + usia normal + BMI normal/overweight
    if len(rules) == 0:
        gejala_ringan_only = (
            gejala_berat == 0 and
            max(gejala_fuzzy['lemas'], gejala_fuzzy['pusing'], gejala_fuzzy['mudah_lelah']) > 0 and
            max(age_fuzzy['remaja'], age_fuzzy['dewasa']) > 0 and
            max(bmi_fuzzy['normal'], bmi_fuzzy['overweight']) > 0
        )
        if gejala_ringan_only:
            rules.append(('tidak_terdeteksi', 1.0))
        else:
            rules.append(('tidak_terdeteksi', 1.0))  # fallback

    return rules


def agregasi_output(rules):
    # Agregasi output
    aggregated = {'rendah': 0, 'sedang': 0, 'tinggi': 0}
    for kategori, strength in rules:
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
            kategori_membership = np.array([gaussian_membership(x, **risiko_params[kategori]) for x in x_range])
            clipped = np.minimum(kategori_membership, strength)
            output_membership = np.maximum(output_membership, clipped)
    if np.sum(output_membership) == 0:
        return 0
    numerator = np.sum(x_range * output_membership)
    denominator = np.sum(output_membership)
    return numerator / denominator

def fuzzy_diagnosis(age, gender, bmi, symptoms):
    # Fuzzifikasi
    age_fuzzy = fuzzifikasi_usia(age)
    bmi_fuzzy = fuzzifikasi_bmi(bmi)
    gejala_fuzzy = fuzzifikasi_gejala(symptoms)

    # Inferensi
    rules_output = inference_mamdani(age_fuzzy, bmi_fuzzy, gejala_fuzzy)

    # Agregasi
    aggregated = agregasi_output(rules_output)

    # Defuzzifikasi
    centroid_score = defuzzifikasi_centroid(aggregated)

    # Format hasil
    result = format_diagnosis_result(centroid_score)
    result_score = round(centroid_score, 2)

    return result['diagnosis'], result_score, result['risiko'], result['saran']

def fuzzy_diagnosis_debug(age, gender, bmi, symptoms):
    print_debug_info("Fuzzifikasi usia", "")
    age_fuzzy = fuzzifikasi_usia(age)
    bmi_fuzzy = fuzzifikasi_bmi(bmi)
    gejala_fuzzy = fuzzifikasi_gejala(symptoms)
    print(f"Usia {age} -> {age_fuzzy}")
    print(f"BMI {bmi} -> {bmi_fuzzy}")
    print(f"Gejala aktif: {get_active_symptoms(gejala_fuzzy)}")

    print_debug_info("Inferensi Mamdani", "")
    rules_output = inference_mamdani(age_fuzzy, bmi_fuzzy, gejala_fuzzy)
    print(f"Rules aktif: {rules_output}")

    print_debug_info("Agregasi output", "")
    aggregated = agregasi_output(rules_output)
    print(f"Agregasi: {aggregated}")

    print_debug_info("Defuzzifikasi centroid", "")
    centroid_score = defuzzifikasi_centroid(aggregated)
    print(f"Centroid: {centroid_score}")

    print_debug_info("Hasil akhir diagnosis", "")
    diagnosis, result_score, risiko, saran = fuzzy_diagnosis(age, gender, bmi, symptoms)
    print(f"Diagnosis: {diagnosis}")
    print(f"Skor: {result_score}%")
    print(f"Risiko: {risiko}")
    print(f"Saran: {saran}")

    return diagnosis, result_score, risiko, saran
