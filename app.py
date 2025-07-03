from flask import Flask, render_template, request, session, redirect , url_for, session, request, flash, jsonify
from functools import wraps
import smtplib
import logging
from email.mime.text import MIMEText
from datetime import datetime
from werkzeug.exceptions import BadRequest
from werkzeug.security import generate_password_hash, check_password_hash
import os
import boto3
import uuid
from botocore.exceptions import ClientError

# -------------------- Config --------------------
app = Flask(__name__)
app.secret_key = 'supersecret'

# Dummy user store
users = {
    "user@example.com": {"password": "1234", "role": "patient"}
}
# AWS configuration
region = 'ap-south-1'  # Change if needed

# -------------------- AWS Setup --------------------
dynamodb = boto3.resource('dynamodb', region_name=region)

# Email settings
EMAIL_HOST = 'smtp.@gmail.com'
EMAIL_PORT = 587
EMAIL_USER = '@gmail.com'
EMAIL_PASSWORD = ""


# -------------------- Logger Setup --------------------

log_folder = 'logs'
log_file = os.path.join(log_folder, 'app.log')

if os.path.exists(log_folder):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

logger = logging.getLogger(__name__)

# SNS Setup
sns = boto3.client('sns', region_name=region)
 
 # -------------------- Helper Functions --------------------

def send_appointments_email(to_email, appointments_summary):
    try:
        msg = MIMEText(appointments_summary)
        msg['Subject'] = 'Your appointment Confirmation'
        msg['From'] = EMAIL_USER
        msg['To'] = to_email

        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info("appointment email sent to %s", to_email)
    except Exception as e:
        logger.error("Failed to send email: %s", e)
def save_appointment_to_dynamodb(appointments_data):
    try:
        appointments_table.put_item(Item=appointments_data)
        logger.info("appointments saved to DynamoDB: %s", appointments_data['appointments_id'])
    except Exception as e:
        logger.error("DynamoDB error: %s", e)

def send_sns_notification(message, phone_number=None, topic_arn=None):
    try:
        if phone_number:
            sns.publish(PhoneNumber=phone_number, Message=message)
            logger.info(f"SNS SMS sent to {phone_number}")
        elif topic_arn:
            sns.publish(TopicArn=topic_arn, Message=message)
            logger.info(f"SNS message published to topic {topic_arn}")
        else:
            logger.info("SNS notification skipped (no phone number or topic)")
    except Exception as e:
        logger.error("SNS send failed: %s", e)

# DynamoDB tables
appointments_table = dynamodb.Table('Appointments')
patient_appointments_table = dynamodb.Table('PatientAppointments')
 
  # Simple in-memory user storage
users = {}

# Store reviews and contacts in files
APPOINTMENTS_FILE = 'Appointments.txt'
PATINETAPPOINTMNETS_FILE = 'patientAppointments.txt' 

@app.route('/', methods=['GET', 'POST'])
def home():
    page = request.args.get('page', 'login')

    if request.method == 'POST':
        if page == 'login':
            email = request.form['email']
            password = request.form['password']
            user = users.get(email)
            if user and user['password'] == password:
                session['user'] = email
                return redirect('/dashboard')
            return "Invalid login. <a href='/?page=login'>Try again</a>"

        elif page == 'signup':
            email = request.form['email']
            password = request.form['password']
            confirm = request.form['confirm_password']
            user_type = request.form['user_type']
            if password != confirm:
                return "Passwords don't match. <a href='/?page=signup'>Try again</a>"
            users[email] = {"password": password, "role": user_type}
            return redirect('/?page=login')

    if page == 'signup':
        return render_template('signup.html')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/?page=login')
    return render_template('dashboard.html')

@app.route('/about')
def about():
    if 'user' not in session:
        return redirect('/?page=login')
    return render_template('about.html')

@app.route('/doctors')
def doctors():
    if 'user' not in session:
        return redirect('/?page=login')
    return render_template('doctors.html')

@app.route('/services')
def services():
    if 'user' not in session:
        return redirect('/?page=login')
    return render_template('services.html')

@app.route('/doctor-profile/<int:doctor_id>')
def doctor_profile(doctor_id):
    if 'user' not in session:
        return redirect('/?page=login')

    doctors = {
        1: {"name": "Dr. Sarah Johnson", "specialty": "Cardiologist", "experience": "15 years", "university": "Harvard"},
        2: {"name": "Dr. Michael Chen", "specialty": "Neurologist", "experience": "12 years", "university": "Johns Hopkins"},
        3: {"name": "Dr. Emily Rodriguez", "specialty": "Pediatrician", "experience": "10 years", "university": "Stanford"},
        4: {"name": "Dr. David Wilson", "specialty": "Orthopedic Surgeon", "experience": "18 years", "university": "Mayo Clinic"}
    }

    doctor = doctors.get(doctor_id)
    if not doctor:
        return "Doctor not found", 404

    return render_template('doctor_profile.html', doctor=doctor)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if 'user' not in session:
        return redirect('/?page=login')

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        print(f"Contact - Name: {name}, Email: {email}, Subject: {subject}, Message: {message}")
        return "Thanks for contacting us! <a href='/dashboard'>Go back</a>"

    return render_template('contact.html')

@app.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    if 'user' not in session:
        return redirect('/?page=login')

    success = False
    if request.method == 'POST':
        try:
            appointments_table.put_item(
                Item={
                    'email': request.form['email'],
                    'name': request.form['name'],
                    'phone': request.form['phone'],
                    'date': request.form['date'],
                    'time': request.form['time'],
                    'doctor': request.form['doctor'],
                    'notes': request.form['notes']
                }
            )
            success = True
        except ClientError as e:
            print("Error saving to DynamoDB:", e)

    return render_template('appointment.html', success=success)

@app.route('/patient_appointment', methods=['GET', 'POST'])
def patient_appointment():
    if 'user' not in session:
        return redirect('/?page=login')
    success = False

    if request.method == 'POST':
        try:
            patient_appointments_table.put_item(
                Item={
                    'contact': request.form['contact'],
                    'name': request.form['patient_name'],
                    'age': request.form['age'],
                    'gender': request.form['gender'],
                    'appointment_date': request.form['appointment_date'],
                    'appointment_time': request.form['appointment_time'],
                    'doctor': request.form['doctor'],
                    'problem': request.form['problem']
                }
            )
            success = True
        except ClientError as e:
            print("Error saving to DynamoDB:", e)

    return render_template('patient_appointment.html', success=success)

@app.route('/patient_phase')
def patient_phase():
    if 'user' not in session:
        return redirect('/?page=login')
    return render_template('patient_phase.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/?page=login')

if __name__ == '__main__':
    app.run(debug=True , host="0.0.0.0", port=5000)
