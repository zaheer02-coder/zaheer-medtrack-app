from flask import Flask, render_template, request, session, redirect , url_for, session, request, flash
from functools import wraps
from werkzeug.exceptions import BadRequest
import os
import boto3
import uuid
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = 'supersecret'

# Dummy user store
users = {
    "user@example.com": {"password": "1234", "role": "patient"}
}
# AWS configuration
region = 'ap-south-1'  # Change if needed

dynamodb = boto3.resource('dynamodb', region_name=region)
sns = boto3.client('sns', region_name=region)

# DynamoDB tables
appointments_table = dynamodb.Table('Appointments')
patient_appointments_table = dynamodb.Table('PatientAppointments')

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
