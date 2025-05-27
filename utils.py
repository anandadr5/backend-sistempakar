import math

def calculate_bmi(weight, height):
    """Menghitung BMI dari berat badan dan tinggi badan"""
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

def gaussian_membership(x, mean, std):
    """Fungsi keanggotaan Gaussian"""
    return math.exp(-0.5 * ((x - mean) / std) ** 2)

def normalize_symptoms(symptoms):
    """Normalisasi input gejala ke format lowercase"""
    return {k.lower(): v.lower() for k, v in symptoms.items()}

def get_active_symptoms(gejala_fuzzy):
    """Mendapatkan daftar gejala yang aktif"""
    return [k for k, v in gejala_fuzzy.items() if v > 0]

def format_diagnosis_result(centroid_score):
    """Format hasil diagnosis berdasarkan centroid score"""
    if centroid_score == 0:
        return {
            'diagnosis': "Tidak Terdeteksi",
            'risiko': "-",
            'saran': "🧘‍♂️ Jaga kesehatan dan pola hidup sehat ya! Jangan lupa olahraga rutin dan makan bergizi."
        }
    else:
        diagnosis = "Terdeteksi"
        if centroid_score < 35:
            risiko = "Risiko Rendah" 
            saran = "🧘‍♂️ Jaga kesehatan dan pola hidup sehat ya! Jangan lupa olahraga rutin dan makan bergizi."
        elif centroid_score < 65:
            risiko = "Risiko Sedang"
            saran = "⚠️ Segera kunjungi fasilitas kesehatan terdekat untuk pemeriksaan lebih lanjut."
        else:
            risiko = "Risiko Tinggi"
            saran = "🚨 Penting! Segera kunjungi fasilitas kesehatan terdekat dan ikuti anjuran medis dengan serius."
        
        return {
            'diagnosis': diagnosis,
            'risiko': risiko, 
            'saran': saran
        }

def print_debug_info(stage, data, description=""):
    """Helper function untuk debug output"""
    print(f"=== {stage} ===")
    if description:
        print(description)
    print(data)
    print()