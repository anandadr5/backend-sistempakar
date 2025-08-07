import math

def calculate_bmi(weight, height):
    """Menghitung BMI dari berat badan (kg) dan tinggi badan (m)"""
    weight = float(weight)
    height = float(height)
    return round(weight / (height ** 2), 2)

def get_bmi_category(bmi):
    """Kategori BMI sesuai standar WHO"""
    if bmi < 18.5:
        return "Underweight"
    elif 18.5 <= bmi < 25.0:
        return "Normal"
    elif 25.0 <= bmi < 30.0:
        return "Overweight"
    else:
        return "Obese"

def get_age_category(age):
    """Kategori usia sesuai permintaan"""
    if age < 5:
        return "Bayi"
    elif age <= 9:
        return "Anak-anak"
    elif age <= 18:
        return "Remaja"
    elif age < 60:
        return "Dewasa"
    else:
        return "Lansia"
    
def get_blood_pressure_category(sistolik, diastolik):
    """Klasifikasi tekanan darah berdasarkan standar medis"""
    if sistolik < 90 or diastolik < 60:
        return "Hipotensi"
    elif sistolik <= 120 and diastolik <= 80:
        return "Normal"
    elif sistolik <= 139 or diastolik <= 89:
        return "Prehipertensi"
    elif sistolik <= 159 or diastolik <= 99:
        return "Hipertensi Tingkat 1"
    elif sistolik <= 179 or diastolik <= 109:
        return "Hipertensi Tingkat 2"
    else:
        return "Hipertensi Darurat"
    
def get_normal_blood_pressure(age, gender):
    """Mendapatkan tekanan darah normal berdasarkan usia dan jenis kelamin"""
    # gender: 0 = Perempuan, 1 = Laki-laki
    if gender == 0:  # Perempuan
        if 18 <= age <= 39:
            return {"sistolik": 110, "diastolik": 68}
        elif 40 <= age <= 59:
            return {"sistolik": 122, "diastolik": 74}
        else:  # >= 60
            return {"sistolik": 139, "diastolik": 68}
    else:  # Laki-laki
        if 18 <= age <= 39:
            return {"sistolik": 119, "diastolik": 70}
        elif 40 <= age <= 59:
            return {"sistolik": 124, "diastolik": 77}
        else:  # >= 60
            return {"sistolik": 133, "diastolik": 69}

def gaussian_membership(x, mean, std):
    """Fungsi keanggotaan Gaussian"""
    return math.exp(-0.5 * ((x - mean) / std) ** 2)

def normalize_symptoms(symptoms):
    """Normalisasi input gejala ke format yang konsisten"""
    return {k.lower().replace(" ", "_"): v.lower() for k, v in symptoms.items()}

def get_active_symptoms(gejala_fuzzy):
    """Mendapatkan daftar gejala yang aktif (memiliki nilai > 0)"""
    return [k for k, v in gejala_fuzzy.items() if v > 0]

def calculate_cardiovascular_risk_score(age, gender, bmi, sistolik, diastolik, 
                                       riwayat_penyakit, riwayat_merokok, 
                                       aspek_psikologis, gejala_count):
    """
    Menghitung skor risiko kardiovaskular berdasarkan faktor-faktor risiko.
    Menggunakan pendekatan scoring yang disederhanakan dari Framingham Risk Score.
    """
    risk_score = 0
    
    # Faktor usia dan jenis kelamin
    if gender == 1:  # Laki-laki
        if age >= 45:
            risk_score += 2
        if age >= 55:
            risk_score += 1
        if age >= 65:
            risk_score += 2
    else:  # Perempuan
        if age >= 55:
            risk_score += 2
        if age >= 65:
            risk_score += 2
    
    # Faktor BMI
    if bmi >= 30:  # Obesitas
        risk_score += 2
    elif bmi >= 25:  # Overweight
        risk_score += 1
    
    # Faktor tekanan darah
    bp_category = get_blood_pressure_category(sistolik, diastolik)
    if bp_category == "Hipertensi Darurat":
        risk_score += 4
    elif bp_category == "Hipertensi Tingkat 2":
        risk_score += 3
    elif bp_category == "Hipertensi Tingkat 1":
        risk_score += 2
    elif bp_category == "Prehipertensi":
        risk_score += 1
    elif bp_category == "Hipotensi":
        risk_score += 1
    
    # Faktor riwayat penyakit
    if riwayat_penyakit.lower() in ['ada', 'ya', '1']:
        risk_score += 3
    
    # Faktor riwayat merokok
    if riwayat_merokok.lower() in ['ya', 'iya', '1']:
        risk_score += 2
    
    # Faktor psikologis (stres dapat meningkatkan risiko kardiovaskular)
    if aspek_psikologis.lower() in ['depresi', 'cemas', 'kecenderungan bunuh diri']:
        risk_score += 2
    elif aspek_psikologis.lower() in ['marah', 'takut']:
        risk_score += 1
    
    # Faktor jumlah gejala
    if gejala_count >= 5:
        risk_score += 3
    elif gejala_count >= 3:
        risk_score += 2
    elif gejala_count >= 1:
        risk_score += 1
    
    return min(risk_score, 20)

def format_diagnosis_result(centroid_score):
    """Format hasil diagnosis berdasarkan centroid score dengan kategori yang lebih detail"""
    if centroid_score == 0:
        return {
            'diagnosis': "Tidak Terdeteksi",
            'risiko': "Tidak Ada Risiko",
            'saran': "🟢 Kondisi Anda dalam batas normal. Tetap jaga pola hidup sehat dengan olahraga rutin, diet seimbang, dan hindari stres berlebihan."
        }
    elif centroid_score < 25:
        return {
            'diagnosis': "Terdeteksi",
            'risiko': "Risiko Rendah",
            'saran': "🟡 Risiko rendah. Lakukan pemeriksaan kesehatan rutin tahunan dan pertahankan gaya hidup sehat. Konsultasi dengan dokter jika gejala memburuk."
        }
    elif centroid_score < 50:
        return {
            'diagnosis': "Terdeteksi", 
            'risiko': "Risiko Sedang",
            'saran': "🟠 Risiko sedang. Disarankan untuk berkonsultasi dengan dokter dalam 2-4 minggu. Lakukan perubahan gaya hidup seperti mengurangi garam, olahraga teratur, dan kelola stres."
        }
    elif centroid_score < 75:
        return {
            'diagnosis': "Terdeteksi",
            'risiko': "Risiko Tinggi", 
            'saran': "🔴 Risiko tinggi. Segera konsultasi dengan dokter spesialis jantung dalam 1-2 minggu. Diperlukan pemeriksaan lebih lanjut seperti EKG, echocardiogram, atau tes laboratorium."
        }
    else:
        return {
            'diagnosis': "Terdeteksi",
            'risiko': "Risiko Sangat Tinggi",
            'saran': "🚨 DARURAT! Risiko sangat tinggi. Segera kunjungi IGD atau dokter spesialis jantung hari ini. Kondisi ini memerlukan penanganan medis segera."
        }