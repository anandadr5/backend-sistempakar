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
frontend_url = os.environ.get('FRONTEND_URL', "https://frontend-sistempakar.vercel.app/")
CORS(app, resources={r"/api/*": {"origins": frontend_url}})

# Konfigurasi Database
DATABASE_URL_FROM_ENV = os.environ.get('DATABASE_URL')
if DATABASE_URL_FROM_ENV:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL_FROM_ENV.replace("mysql://", "mysql+pymysql://", 1)
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/db_sistempakar'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Konfigurasi Secret Key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_dev_secret_key_please_change_in_prod')
app.logger.info(f"INFO: Secret key configured.")

app.logger.info("INFO: Initializing SQLAlchemy...")
try:
    db = SQLAlchemy(app)
    app.logger.info("INFO: SQLAlchemy initialized.")
except Exception as e:
    app.logger.error(f"ERROR: Failed during SQLAlchemy initialization: {e}", exc_info=True)
    raise

# MODEL

class Diagnosa(db.Model):
    __tablename__ = 'diagnosa'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100))
    usia = db.Column(db.Integer)
    jenis_kelamin = db.Column(db.String(20))
    berat_badan = db.Column(db.Float)
    tinggi_badan = db.Column(db.Float)
    bmi = db.Column(db.Float)
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
    nama = db.Column(db.String(100))
    email = db.Column(db.String(100))
    pesan = db.Column(db.Text)

# Inisialisasi Database
app.logger.info("INFO: Attempting to create all tables with app_context...")
try:
    with app.app_context():
        db.create_all()
    app.logger.info("INFO: db.create_all() completed successfully or tables already exist.")
except Exception as e:
    app.logger.error(f"ERROR: Failed during db.create_all(): {e}", exc_info=True)
    raise

app.logger.info("INFO: Application initialization finished. Routes will be defined now.")

@app.route('/')
def health_check():
    app.logger.info("INFO: Health check route / called successfully.")
    return "Backend is healthy and running!", 200

# ENDPOINT DIAGNOSIS

@app.route("/api/diagnosis", methods=["POST"])
def diagnosis():
    data = request.get_json()

    name = data["nama"]
    age = int(data["usia"])
    gender_str = data["gender"]  # "Laki-laki" atau "Perempuan"
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

# ENDPOINT STATISTIK HARIAN

@app.route("/api/statistik-harian", methods=["GET"])
def statistik_harian():
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

# DATA MASYARAKAT (DIAGNOSIS)

@app.route("/api/data-masyarakat", methods=["GET"])
def get_all_diagnosis():
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

@app.route("/api/data-masyarakat/<int:id>", methods=["GET"])
def get_diagnosis_detail(id):
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

@app.route("/api/data-masyarakat/<int:id>", methods=["DELETE"])
def delete_data(id):
    data = Diagnosa.query.get(id)
    if data:
        db.session.delete(data)
        db.session.commit()
        return jsonify({"message": "Berhasil dihapus"})
    return jsonify({"message": "Data tidak ditemukan"}), 404

# FEEDBACK

@app.route("/api/feedback", methods=["POST"])
def create_feedback():
    data = request.get_json()
    feedback = Feedback(nama=data["nama"], email=data["email"], pesan=data["pesan"])
    db.session.add(feedback)
    db.session.commit()
    return jsonify({"message": "Feedback berhasil disimpan"})

@app.route("/api/feedback", methods=["GET"])
def get_feedback():
    feedbacks = Feedback.query.order_by(Feedback.id.asc()).all()
    result = [{"id": f.id, "nama": f.nama, "email": f.email, "pesan": f.pesan} for f in feedbacks]
    return jsonify(result)

@app.route("/api/feedback/<int:id>", methods=["DELETE"])
def delete_feedback(id):
    feedback = Feedback.query.get(id)
    if feedback:
        db.session.delete(feedback)
        db.session.commit()
        return jsonify({"message": "Feedback berhasil dihapus"})
    return jsonify({"message": "Feedback tidak ditemukan"}), 404

# RUN APP

if __name__ == '_main_':
    local_port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=local_port)