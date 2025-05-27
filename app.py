import os
from flask import Flask
# from flask_cors import CORS # Sementara dikomentari
# from flask_sqlalchemy import SQLAlchemy # Sementara dikomentari
# from datetime import datetime, timedelta # Sementara dikomentari
# from sqlalchemy import func # Sementara dikomentari

# from fuzzy import fuzzy_diagnosis # SEMENTARA DIKOMENTARI
# from utils import calculate_bmi, get_bmi_category # SEMENTARA DIKOMENTARI

app = Flask(__name__)
app.logger.info("--- TEST LOG 1: Flask app object CREATED ---") # Logger paling awal

# # Konfigurasi CORS (Sementara dikomentari)
# frontend_url = os.environ.get('FRONTEND_URL', "https://frontend-sistempakar.vercel.app/")
# CORS(app, resources={r"/api/*": {"origins": frontend_url}})
# app.logger.info(f"INFO: CORS configured for origin: {frontend_url}")

# # Konfigurasi Database (Sementara dikomentari)
# DATABASE_URL_FROM_ENV = os.environ.get('DATABASE_URL')
# if DATABASE_URL_FROM_ENV:
#     app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL_FROM_ENV.replace("mysql://", "mysql+pymysql://", 1)
# else:
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/db_sistempakar'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.logger.info(f"INFO: Database URI configured.")

# # Konfigurasi Secret Key (Sementara dikomentari)
# app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_dev_secret_key_please_change_in_prod')
# app.logger.info(f"INFO: Secret key configured.")

# # SQLAlchemy Initialization (Sementara dikomentari)
# db = SQLAlchemy(app)
# app.logger.info("INFO: SQLAlchemy object created (but not initialized with app yet).")


# # MODEL (Sementara dikomentari semua)
# # class Diagnosa(db.Model): ...
# # class Feedback(db.Model): ...

# # Inisialisasi Database (Sementara dikomentari)
# # app.logger.info("INFO: Attempting to create all tables with app_context...")
# # try:
# #     with app.app_context():
# #         db.create_all()
# #     app.logger.info("INFO: db.create_all() completed successfully or tables already exist.")
# # except Exception as e:
# #     app.logger.error(f"ERROR: Failed during db.create_all(): {e}", exc_info=True)
# #     raise

app.logger.info("--- TEST LOG 2: Basic app initialization FINISHED, defining routes ---")

@app.route('/')
def health_check():
    app.logger.info("--- TEST LOG 3: Health check route / CALLED ---")
    return "Minimal app for Railway is ALIVE!", 200

# # ENDPOINT LAIN SEMENTARA DIKOMENTARI SEMUA ...

if __name__ == '__main__':
    local_port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=local_port)