import math

def calculate_bmi(weight, height):
    """Menghitung BMI dari berat badan (kg) dan tinggi badan (cm)"""
    weight = float(weight)
    height = float(height) / 100
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
    
def klasifikasi_tekanan_darah(sistolik, diastolik):
    """Klasifikasi tekanan darah berdasarkan nilai sistolik dan diastolik."""
    sistolik = int(sistolik)
    diastolik = int(diastolik)

    if sistolik >= 180 or diastolik >= 110:
        return "Hipertensi Darurat"
    elif 160 <= sistolik <= 179 or 100 <= diastolik <= 109:
        return "Hipertensi Tingkat 2"
    elif 140 <= sistolik <= 159 or 90 <= diastolik <= 99:
        return "Hipertensi Tingkat 1"
    elif 121 <= sistolik <= 139 or 81 <= diastolik <= 89:
        return "Prehipertensi"
    elif 90 <= sistolik <= 120 and 60 <= diastolik <= 80:
        return "Normal"
    elif sistolik < 90 or diastolik < 60:
        return "Hipotensi"
    else:
        return "Normal cenderung tinggi"
    
def get_skor_tekanan_darah(sistolik, diastolik, usia, gender_str):
    """
    Menghitung skor deviasi dari tekanan darah normal berdasarkan usia dan gender.
    """
    sistolik = int(sistolik)
    diastolik = int(diastolik)
    usia = int(usia)
    gender = gender_str.lower()

    if gender == 'wanita':
        if 18 <= usia <= 39: ideal_sistolik, ideal_diastolik = 110, 68
        elif 40 <= usia <= 59: ideal_sistolik, ideal_diastolik = 122, 74
        else: ideal_sistolik, ideal_diastolik = 139, 68
    else: # Pria
        if 18 <= usia <= 39: ideal_sistolik, ideal_diastolik = 119, 70
        elif 40 <= usia <= 59: ideal_sistolik, ideal_diastolik = 124, 77
        else: ideal_sistolik, ideal_diastolik = 133, 69

    if usia < 18:
        ideal_sistolik, ideal_diastolik = 110, 70

    deviasi_sistolik = ((sistolik - ideal_sistolik) / ideal_sistolik) * 100
    deviasi_diastolik = ((diastolik - ideal_diastolik) / ideal_diastolik) * 100
    
    skor_total = (0.6 * deviasi_sistolik) + (0.4 * deviasi_diastolik)
    return skor_total

def gaussian_membership(x, mean, std):
    """Fungsi keanggotaan Gaussian"""
    return math.exp(-0.5 * ((x - mean) / std) ** 2)

def format_diagnosis_result(centroid_score):
    """Format hasil diagnosis berdasarkan centroid score"""
    if centroid_score < 15:
        return {
            'diagnosis': "Tidak Terdeteksi",
            'risiko': "Sangat Rendah",
            'saran': "🎉 Selamat! Kondisi jantung Anda prima! Pertahankan dengan olahraga teratur, makan bergizi seimbang, tidur cukup 7-8 jam, hindari rokok/alkohol, dan kelola stress dengan baik. Lakukan medical check-up rutin setiap tahun."
        }
    else:
        diagnosis = "Terdeteksi Potensi Masalah Jantung"
        if centroid_score < 40:
            risiko = "Risiko Rendah"
            saran = "💡 Ada indikator yang perlu diperhatikan tapi masih terkendali. Mulai olahraga ringan 3x/minggu, konsumsi omega-3, kurangi garam, monitor tekanan darah berkala, dan jadwalkan pemeriksaan jantung dalam 3-6 bulan. Pencegahan adalah kunci!"
        elif centroid_score < 70:
            risiko = "Risiko Sedang"
            saran = "⚠️ Kondisi memerlukan tindak lanjut segera! Konsultasi dokter spesialis jantung dalam 1-2 minggu, lakukan pemeriksaan EKG/Echo, patuhi pengobatan. STOP merokok, diet jantung sehat, turunkan berat badan, kelola stress. Jangan tunda!"
        else:
            risiko = "Risiko Tinggi"
            saran = "🚨 URGENT! SEGERA kunjungi IGD/dokter spesialis jantung dalam 24-48 jam. Simpan nomor emergency, beri tahu keluarga, siapkan riwayat kesehatan. Minum obat disiplin, berhenti total rokok/alkohol, batasi aktivitas berat, monitor tekanan darah harian."
        return {
            'diagnosis': diagnosis,
            'risiko': risiko,
            'saran': saran
        }