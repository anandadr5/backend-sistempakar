import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import func

from fuzzy import fuzzy_diagnosis_enhanced, validate_input_data
from utils import (calculate_bmi, get_bmi_category, get_blood_pressure_category,
                  get_risk_factors_summary, generate_recommendations, calculate_target_values)

app = Flask(__name__)

# Konfigurasi CORS
frontend_url = os.environ.get('FRONTEND_URL', "https://frontend-sistempakar.vercel.app")
CORS(app, resources={r"/api/*": {"origins": [frontend_url, "http://localhost:5173"]}})

# Konfigurasi Database
DATABASE_URL_FROM_ENV = os.environ.get('DATABASE_URL')
if DATABASE_URL_FROM_ENV:
    if DATABASE_URL_FROM_ENV.startswith("mysql://"):
        DATABASE_URL_FROM_ENV = DATABASE_URL_FROM_ENV.replace("mysql://", "mysql+pymysql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL_FROM_ENV
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/db_sistempakar'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Konfigurasi Secret Key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_dev_secret_key_please_change_in_prod')

db = SQLAlchemy(app)

# MODEL
class Diagnosa(db.Model):
    __tablename__ = 'diagnosa'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    usia = db.Column(db.Integer, nullable=False)
    jenis_kelamin = db.Column(db.String(20), nullable=False)
    berat_badan = db.Column(db.Float, nullable=False)
    tinggi_badan = db.Column(db.Float, nullable=False)
    bmi = db.Column(db.Float, nullable=False)
    kategori_bmi = db.Column(db.String(20))
    
    # Data tekanan darah
    sistolik = db.Column(db.Float, nullable=True)
    diastolik = db.Column(db.Float, nullable=True)
    kategori_tekanan_darah = db.Column(db.String(30))
    
    # Data tambahan
    riwayat_penyakit = db.Column(db.String(20))
    riwayat_merokok = db.Column(db.String(20))
    aspek_psikologis = db.Column(db.String(50))
    
    # Hasil diagnosis
    diagnosis = db.Column(db.String(50))
    persentase = db.Column(db.Float)
    risiko = db.Column(db.String(50))
    saran = db.Column(db.Text)
    gejala = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    risk_score = db.Column(db.Float)  # Skor risiko kardiovaskular

class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    pesan = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ENDPOINT DIAGNOSIS
@app.route("/api/diagnosis", methods=["POST"])
def diagnosis():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validasi input
        required_fields = ["nama", "usia", "gender", "weight", "height", "gejala"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

       # Extract data dengan default values
        name = data["nama"]
        age = int(data["usia"])
        gender_str = data["gender"]
        weight = float(data["weight"])
        height = float(data["height"])
        symptoms = data["gejala"]
        
        # Data tambahan dengan default values
        sistolik = float(data.get("sistolik", 120))
        diastolik = float(data.get("diastolik", 80))
        riwayat_penyakit = data.get("riwayat_penyakit", "Tidak Ada")
        riwayat_merokok = data.get("riwayat_merokok", "Tidak")
        aspek_psikologis = data.get("aspek_psikologis", "Tenang")

        # Konversi gender ke format numerik
        gender = 1 if gender_str.lower() == "laki-laki" else 0

        # Hitung BMI (height dalam meter)
        bmi = calculate_bmi(weight, height / 100)
        kategori_bmi = get_bmi_category(bmi)
        kategori_td = get_blood_pressure_category(sistolik, diastolik)

        # Validasi data input
        validation_errors = validate_input_data(
            age, gender, bmi, sistolik, diastolik, symptoms,
            riwayat_penyakit, riwayat_merokok, aspek_psikologis
        )
        
        if validation_errors:
            return jsonify({"error": "Validation failed", "details": validation_errors}), 400

        # Proses diagnosis menggunakan sistem fuzzy
        diagnosis_result, percentage, risiko, saran = fuzzy_diagnosis_enhanced(
            age, gender, bmi, sistolik, diastolik, symptoms,
            riwayat_penyakit, riwayat_merokok, aspek_psikologis
        )

        # Hitung faktor risiko dan rekomendasi
        gejala_aktif = [key for key, val in symptoms.items() if val.lower() == "ya"]
        gejala_aktif_display = ", ".join(gejala_aktif) if gejala_aktif else "Tidak ada gejala yang dipilih"
        
        risk_factors = get_risk_factors_summary(
            age, gender, bmi, sistolik, diastolik,
            riwayat_penyakit, riwayat_merokok, aspek_psikologis
        )
        
        recommendations = generate_recommendations(
            age, gender, bmi, kategori_td, risk_factors, risiko
        )
        
        targets = calculate_target_values(age, gender, bmi, {"sistolik": sistolik, "diastolik": diastolik})

        # Simpan ke database
        diagnosa = Diagnosa(
            nama=name,
            usia=age,
            jenis_kelamin=gender_str,
            berat_badan=weight,
            tinggi_badan=height,
            bmi=bmi,
            kategori_bmi=kategori_bmi,
            sistolik=sistolik,
            diastolik=diastolik,
            kategori_tekanan_darah=kategori_td,
            riwayat_penyakit=riwayat_penyakit,
            riwayat_merokok=riwayat_merokok,
            aspek_psikologis=aspek_psikologis,
            diagnosis=diagnosis_result,
            persentase=percentage,
            risiko=risiko,
            saran=saran,
            gejala=gejala_aktif_display,
            risk_score=percentage
        )

        db.session.add(diagnosa)
        db.session.commit()

        # Response
        response_data = {
            "nama": name,
            "usia": age,
            "gender": gender_str,
            "weight": weight,
            "height": height,
            "bmi": bmi,
            "kategori_bmi": kategori_bmi,
            "sistolik": sistolik,
            "diastolik": diastolik,
            "kategori_tekanan_darah": kategori_td,
            "riwayat_penyakit": riwayat_penyakit,
            "riwayat_merokok": riwayat_merokok,
            "aspek_psikologis": aspek_psikologis,
            "diagnosis": diagnosis_result,
            "persentase": percentage,
            "risiko": risiko,
            "gejala": gejala_aktif_display,
            "saran": saran,
            "risk_factors": risk_factors,
            "recommendations": recommendations[:5],
            "targets": targets
        }

        return jsonify(response_data)
    
    except ValueError as e:
        return jsonify({"error": f"Invalid data format: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ENDPOINT STATISTIK HARIAN
@app.route("/api/statistik-harian", methods=["GET"])
def statistik_harian():
    try:
        today = datetime.utcnow().date()
        start_date = today - timedelta(days=6)

        results = db.session.query(
            func.date(Diagnosa.created_at).label('tanggal'),
            func.count(Diagnosa.id).label('total'),
            func.sum(func.case([(Diagnosa.risiko.like('%Tinggi%'), 1)], else_=0)).label('risiko_tinggi'),
            func.sum(func.case([(Diagnosa.risiko.like('%Sedang%'), 1)], else_=0)).label('risiko_sedang'),
            func.sum(func.case([(Diagnosa.risiko.like('%Rendah%'), 1)], else_=0)).label('risiko_rendah')
        ).filter(
            Diagnosa.created_at >= start_date
        ).group_by(
            func.date(Diagnosa.created_at)
        ).all()

        data = []
        for i in range(7):
            tanggal = start_date + timedelta(days=i)
            stats = next((r for r in results if r.tanggal == tanggal), None)
            
            if stats:
                data.append({
                    "day": tanggal.strftime('%d-%m'),
                    "diagnosis": stats.total,
                    "risiko_tinggi": stats.risiko_tinggi or 0,
                    "risiko_sedang": stats.risiko_sedang or 0,
                    "risiko_rendah": stats.risiko_rendah or 0
                })
            else:
                data.append({
                    "day": tanggal.strftime('%d-%m'),
                    "diagnosis": 0,
                    "risiko_tinggi": 0,
                    "risiko_sedang": 0,
                    "risiko_rendah": 0
                })

        return jsonify(data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ENDPOINT STATISTIK RISIKO
@app.route("/api/statistik-risiko", methods=["GET"])
def statistik_risiko():
    try:
        # Statistik berdasarkan kategori risiko
        risiko_stats = db.session.query(
            Diagnosa.risiko,
            func.count(Diagnosa.id).label('count')
        ).group_by(Diagnosa.risiko).all()
        
        # Statistik berdasarkan usia
        usia_stats = db.session.query(
            func.case([
                (Diagnosa.usia < 30, 'Muda'),
                (Diagnosa.usia < 50, 'Dewasa'),
                (Diagnosa.usia < 70, 'Setengah Baya'),
                (Diagnosa.usia >= 70, 'Lansia')
            ]).label('kategori_usia'),
            func.avg(Diagnosa.persentase).label('avg_risk_score'),
            func.count(Diagnosa.id).label('count')
        ).group_by('kategori_usia').all()
        
        # Statistik berdasarkan jenis kelamin
        gender_stats = db.session.query(
            Diagnosa.jenis_kelamin,
            func.avg(Diagnosa.persentase).label('avg_risk_score'),
            func.count(Diagnosa.id).label('count')
        ).group_by(Diagnosa.jenis_kelamin).all()

        return jsonify({
            "risiko_distribution": [{"kategori": r.risiko, "count": r.count} for r in risiko_stats],
            "usia_analysis": [{"kategori": r.kategori_usia, "avg_score": float(r.avg_risk_score or 0), "count": r.count} for r in usia_stats],
            "gender_analysis": [{"gender": r.jenis_kelamin, "avg_score": float(r.avg_risk_score or 0), "count": r.count} for r in gender_stats]
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# DATA MASYARAKAT (DIAGNOSIS)
@app.route("/api/data-masyarakat", methods=["GET"])
def get_all_diagnosis():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        pagination = Diagnosa.query.order_by(Diagnosa.id.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = {
            "data": [{
                "id": d.id,
                "nama": d.nama,
                "usia": d.usia,
                "jenis_kelamin": d.jenis_kelamin,
                "diagnosis": d.diagnosis,
                "risiko": d.risiko,
                "persentase": d.persentase,
                "created_at": d.created_at.strftime('%Y-%m-%d %H:%M:%S')
            } for d in pagination.items],
            "pagination": {
                "page": page,
                "pages": pagination.pages,
                "per_page": per_page,
                "total": pagination.total,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            }
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/data-masyarakat/<int:id>", methods=["GET"])
def get_diagnosis_detail(id):
    try:
        data = Diagnosa.query.get(id)
        if data:
            result = {
                "id": data.id,
                "nama": data.nama,
                "usia": data.usia,
                "jenis_kelamin": data.jenis_kelamin,
                "berat_badan": data.berat_badan,
                "tinggi_badan": data.tinggi_badan,
                "bmi": data.bmi,
                "kategori_bmi": data.kategori_bmi,
                "sistolik": data.sistolik,
                "diastolik": data.diastolik,
                "kategori_tekanan_darah": data.kategori_tekanan_darah,
                "riwayat_penyakit": data.riwayat_penyakit,
                "riwayat_merokok": data.riwayat_merokok,
                "aspek_psikologis": data.aspek_psikologis,
                "diagnosis": data.diagnosis,
                "persentase": data.persentase,
                "risiko": data.risiko,
                "saran": data.saran,
                "gejala": data.gejala,
                "risk_score": data.risk_score,
                "created_at": data.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            return jsonify(result)
        return jsonify({"message": "Data tidak ditemukan"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/data-masyarakat/<int:id>", methods=["DELETE"])
def delete_data(id):
    try:
        data = Diagnosa.query.get(id)
        if data:
            db.session.delete(data)
            db.session.commit()
            return jsonify({"message": "Data berhasil dihapus"})
        return jsonify({"message": "Data tidak ditemukan"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# FEEDBACK
@app.route("/api/feedback", methods=["POST"])
def create_feedback():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        required_fields = ["nama", "email", "pesan"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        feedback = Feedback(nama=data["nama"], email=data["email"], pesan=data["pesan"])
        db.session.add(feedback)
        db.session.commit()
        return jsonify({"message": "Feedback berhasil disimpan"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/feedback", methods=["GET"])
def get_feedback():
    try:
        feedbacks = Feedback.query.order_by(Feedback.id.desc()).all()
        result = [{"id": f.id, "nama": f.nama, "email": f.email, "pesan": f.pesan, "created_at": f.created_at.strftime('%Y-%m-%d %H:%M:%S')} for f in feedbacks]
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/feedback/<int:id>", methods=["DELETE"])
def delete_feedback(id):
    try:
        feedback = Feedback.query.get(id)
        if feedback:
            db.session.delete(feedback)
            db.session.commit()
            return jsonify({"message": "Feedback berhasil dihapus"})
        return jsonify({"message": "Feedback tidak ditemukan"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check endpoint
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "version": "2.0",
        "features": ["enhanced_fuzzy", "blood_pressure", "risk_factors", "recommendations"],
        "timestamp": datetime.utcnow().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# Inisialisasi Database
def init_db():
    try:
        with app.app_context():
            db.create_all()
            print("✅ Database tables created successfully")
            print("✅ Enhanced cardiovascular diagnosis system ready")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")

# Inisialisasi database saat aplikasi dimulai
init_db()

# RUN APP
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)