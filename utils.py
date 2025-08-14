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
            'saran': "🎉 Selamat! Jantung Anda dalam kondisi prima! Pertahankan gaya hidup sehat dengan:\n\n" +
                    "✨ Olahraga teratur 30 menit/hari (jalan kaki, bersepeda, atau berenang)\n" +
                    "🥗 Konsumsi makanan bergizi seimbang dengan banyak sayur dan buah\n" +
                    "💤 Tidur berkualitas 7-8 jam per malam\n" +
                    "🚭 Hindari rokok dan alkohol berlebihan\n" +
                    "😌 Kelola stress dengan meditasi atau hobi yang Anda sukai\n\n" +
                    "💡 Tip: Lakukan medical check-up rutin setiap tahun untuk menjaga kesehatan optimal!"
        }
    else:
        diagnosis = "Terdeteksi Potensi Masalah Jantung"
        if centroid_score < 40:
            risiko = "Risiko Rendah"
            saran = "💡 Deteksi Dini: Ada beberapa indikator yang perlu diperhatikan, tapi jangan khawatir!\n\n" +\
                   "🎯 Langkah-langkah pencegahan yang bisa dilakukan:\n" +\
                   "🏃‍♂️ Mulai rutin berolahraga ringan 3x seminggu (jalan cepat 20-30 menit)\n" +\
                   "🍎 Tingkatkan konsumsi omega-3 (ikan salmon, kacang-kacangan, alpukat)\n" +\
                   "🧂 Kurangi asupan garam dan makanan olahan\n" +\
                   "📊 Monitor tekanan darah dan kolesterol secara berkala\n" +\
                   "🩺 Jadwalkan pemeriksaan jantung dalam 3-6 bulan ke depan\n\n" +\
                   "💪 Ingat: Pencegahan adalah investasi terbaik untuk kesehatan jantung Anda!"
        elif centroid_score < 70:
            risiko = "Risiko Sedang"
            saran = "⚠️ Perhatian: Kondisi Anda memerlukan tindak lanjut medis segera!\n\n" +\
                   "🚨 Yang harus dilakukan SEGERA:\n" +\
                   "👨‍⚕️ Konsultasi dengan dokter spesialis jantung dalam 1-2 minggu\n" +\
                   "🔍 Lakukan pemeriksaan EKG, Echo, atau stress test sesuai anjuran dokter\n" +\
                   "💊 Patuhi pengobatan yang diresepkan dokter\n\n" +\
                   "🎯 Perubahan gaya hidup yang WAJIB:\n" +\
                   "🚫 STOP merokok sekarang juga (gunakan nicotine patch jika perlu)\n" +\
                   "🥗 Diet jantung sehat: kurangi lemak jenuh, tingkatkan serat\n" +\
                   "⚖️ Turunkan berat badan jika berlebih (target 0.5-1 kg/minggu)\n" +\
                   "🧘‍♀️ Kelola stress dengan teknik relaksasi atau konseling\n\n" +\
                   "💙 Jangan tunda! Kesehatan jantung adalah prioritas utama."
        else:
            risiko = "Risiko Tinggi"
            saran = "🚨 URGENT - TINDAKAN SEGERA DIPERLUKAN! 🚨\n\n" +\
                   "⛑️ Langkah DARURAT (dalam 24-48 jam):\n" +\
                   "🏥 SEGERA kunjungi IGD atau dokter spesialis jantung\n" +\
                   "📱 Simpan nomor emergency (118/119) di ponsel Anda\n" +\
                   "👥 Beri tahu keluarga tentang kondisi Anda\n" +\
                   "💼 Siapkan riwayat kesehatan lengkap untuk dokter\n\n" +\
                   "⚡ Tindakan KRITIS yang harus dipatuhi:\n" +\
                   "💊 Minum obat sesuai resep dokter dengan DISIPLIN\n" +\
                   "🚫 BERHENTI total merokok dan alkohol\n" +\
                   "🏃‍♂️ Batasi aktivitas fisik berat sampai ada izin dokter\n" +\
                   "📊 Monitor tekanan darah dan nadi harian\n" +\
                   "🍽️ Diet ketat rendah garam, rendah lemak\n\n" +\
                   "❤️ REMEMBER: Kondisi ini bisa diatasi dengan penanganan yang tepat dan cepat!\n" +\
                   "💪 Stay strong dan ikuti semua anjuran medis dengan serius!"
        return {
            'diagnosis': diagnosis,
            'risiko': risiko,
            'saran': saran
        }