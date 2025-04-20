from flask_dance.contrib.google import make_google_blueprint, google
import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
import pickle
import numpy as np

# ✅ Import models from models.py
from models import db, User, PatientUpload, HelpTicket

app = Flask(__name__)
app.secret_key = "your_very_secret_key"

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # Remove for production

google_bp = make_google_blueprint(
    client_id="592108696610-q341ngj2vqk0g72iqvk52l14s843gi7s.apps.googleusercontent.com",
    client_secret="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YOUR_GOOGLE_CLIENT_SECRET",
    scope=["profile", "email"],
    redirect_url="/login/google/authorized"
)
app.register_blueprint(google_bp, url_prefix="/login")

app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(days=7)

# ✅ Initialize DB from imported `db`
db.init_app(app)

# ✅ Load your ML model
model = pickle.load(open('model.pkl', 'rb'))

# ------------------ ROUTES ------------------ #

@app.route('/login/doctor')
def login_doctor_page():
    return render_template('doctor_login.html')

@app.route('/login/patient')
def login_patient_page():
    return render_template('patient_login.html')

@app.route("/login/google/authorized")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    user_info = resp.json()
    email = user_info["email"]
    username = user_info.get("name", email.split('@')[0])

    # Check if user exists in DB, if not, create them as patient
    existing_user = User.query.filter_by(email=email).first()
    if not existing_user:
        new_user = User(username=username, email=email, password="", role="patient")
        db.session.add(new_user)
        db.session.commit()

    session['user'] = username
    session['role'] = 'patient'  # Google login is defaulted to patient
    return redirect('/dashboard')


@app.route('/')
def intro():
    return render_template('intro.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    int_features = [int(x) for x in request.form.values()]
    final_features = [np.array(int_features)]
    prediction = model.predict(final_features)
    output = 'ASD Detected' if prediction[0] == 1 else 'ASD Not Detected'
    return render_template('result.html', prediction=output)

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['fullname']
    email = request.form['email']
    password = request.form['password']
    role = 'doctor' if 'license' in request.form else 'patient'
    doctor_id = request.form.get('license')

    user = User(username=username, email=email, password=password, role=role, doctor_id=doctor_id)
    db.session.add(user)
    db.session.commit()
    return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    session.permanent = 'remember' in request.form
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username, password=password).first()

    if user:
        session['user'] = user.username
        session['role'] = user.role
        return redirect('/dashboard')
    return "Invalid credentials"

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    
    user = session['user']
    role = session['role']
    
    if role == 'doctor':
        uploads = PatientUpload.query.all()
        return render_template('doctor_dashboard.html', user=user, uploads=uploads, random_welcome="Welcome back, Doctor!", random_quote="Healing hearts, one child at a time.")
    elif role == 'patient':
        my_uploads = PatientUpload.query.filter_by(username=user).all()
        return render_template('patient_dashboard.html', user=user, uploads=my_uploads)
    return redirect('/')

@app.route('/upload', methods=['POST'])
def upload():
    if 'user' not in session or session['role'] != 'patient':
        return redirect('/')

    username = session['user']
    description = request.form['description']
    
    video = request.files.get('video')
    image = request.files.get('image')
    
    video_filename = image_filename = None

    if video:
        video_filename = f"video_{username}.mp4"
        video.save(f"uploads/{video_filename}")
    if image:
        image_filename = f"image_{username}.jpg"
        image.save(f"uploads/{image_filename}")
    
    upload = PatientUpload(
        username=username,
        description=description,
        video_filename=video_filename,
        image_filename=image_filename
    )
    db.session.add(upload)
    db.session.commit()

    return redirect('/dashboard')

@app.route('/help', methods=['GET', 'POST'])
def help():
    if request.method == 'POST':
        user = session.get('user', 'guest')
        role = session.get('role', 'unknown')
        message = request.form['message']

        ticket = HelpTicket(user=user, role=role, message=message)
        db.session.add(ticket)
        db.session.commit()
        return redirect('/dashboard')
    return render_template('help.html')

@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):
    upload = PatientUpload.query.get_or_404(id)
    upload.status = request.form['status']
    upload.doctor_response = request.form.get('doctor_response')
    db.session.commit()
    return redirect('/dashboard')

# ✅ This line creates the DB when you run the app
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
