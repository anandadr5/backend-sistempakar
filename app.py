import os

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import func

from fuzzy import fuzzy_diagnosis
from utils import calculate_bmi, get_bmi_category

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
    diagnosis = db.Column(db.String(50))
    persentase = db.Column(db.Float)
    risiko = db.Column(db.String(50))
    saran = db.Column(db.Text)
    gejala = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
            
        name = data["nama"]
        age = int(data["usia"])
        gender_str = data["gender"]
        weight = float(data["weight"])
        height = float(data["height"])
        symptoms = data["gejala"]
        gender = 1 if gender_str.lower() == "laki-laki" else 0
        bmi = calculate_bmi(weight, height / 100)
        kategori_bmi = get_bmi_category(bmi)
        diagnosis_result, percentage, risiko, saran = fuzzy_diagnosis(age, gender, bmi, symptoms)

        gejala_aktif = [key for key, val in symptoms.items() if val.lower() == "ya"]
        gejala_aktif_display = ", ".join(gejala_aktif) if gejala_aktif else "Tidak ada gejala yang dipilih"

        diagnosa = Diagnosa(
            nama=name,
            usia=age,
            jenis_kelamin=gender_str,
            berat_badan=weight,
            tinggi_badan=height,
            bmi=bmi,
            kategori_bmi=kategori_bmi,
            diagnosis=diagnosis_result,
            persentase=percentage,
            risiko=risiko,
            saran=saran,
            gejala=gejala_aktif_display
            )

        db.session.add(diagnosa)
        db.session.commit()

        return jsonify({
            "nama": name,
            "usia": age,
            "gender": gender_str,
            "weight": weight,
            "height": height,
            "bmi": bmi,
            "kategori_bmi": kategori_bmi,
            "diagnosis": diagnosis_result,
            "persentase": percentage,
            "risiko": risiko,
            "gejala": gejala_aktif_display,
            "saran": saran
        })
    
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
            func.count(Diagnosa.id)
            ).filter(
            Diagnosa.created_at >= start_date
            ).group_by(
            func.date(Diagnosa.created_at)
        ).all()

        data = []
        for i in range(7):
            tanggal = start_date + timedelta(days=i)
            count = next((c for t, c in results if t == tanggal), 0)
            data.append({
                "day": tanggal.strftime('%d-%m'),
                "diagnosis": count
            })

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# DATA MASYARAKAT (DIAGNOSIS)
@app.route("/api/data-masyarakat", methods=["GET"])
def get_all_diagnosis():
    try:
        data = Diagnosa.query.order_by(Diagnosa.id.desc()).all()
        result = [
            {
                "id": d.id,
                "nama": d.nama,
                "usia": d.usia,
                "jenis_kelamin": d.jenis_kelamin,
                "diagnosis": d.diagnosis
            } for d in data
        ]
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
                "diagnosis": data.diagnosis,
                "persentase": data.persentase,
                "risiko": data.risiko,
                "saran": data.saran,
                "gejala": data.gejala
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
            return jsonify({"message": "Berhasil dihapus"})
        return jsonify({"message": "Data tidak ditemukan"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# FEEDBACK
@app.route("/api/feedback", methods=["POST"])
def create_feedback():
    try:
        data = request.get_json()
        print("✅ DITERIMA:", data)

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
        result = [{"id": f.id, "nama": f.nama, "email": f.email, "pesan": f.pesan} for f in feedbacks]
        return jsonify(result)
    
    except Exception as e:
        print("❌ ERROR:", str(e))
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
            print("Database tables created successfully")

    except Exception as e:
        print(f"Error creating database tables: {e}")

# Inisialisasi database saat aplikasi dimuat
init_db()

# RUN APP
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    print(f"🚀 Starting Flask app on port {port}, debug={debug_mode}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)