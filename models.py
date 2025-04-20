from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ------------------ User Model ------------------ #
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'doctor' or 'patient'
    doctor_id = db.Column(db.String(100), nullable=True)  # Only for doctors

# ------------------ Patient Uploads ------------------ #
class PatientUpload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150))
    description = db.Column(db.Text)
    video_filename = db.Column(db.String(200))
    image_filename = db.Column(db.String(200))
    status = db.Column(db.String(50), default='pending')  # accepted/rejected/pending
    doctor_response = db.Column(db.Text, nullable=True)

# ------------------ Help Tickets ------------------ #
class HelpTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100))
    role = db.Column(db.String(50))
    message = db.Column(db.Text)
    status = db.Column(db.String(50), default="open")
