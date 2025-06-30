from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# In-memory user data (temporary)
users = {}

# Routes
@app.route('/')
def home():
    return render_template('indexpg.html')

@app.route('/about')
def about():
    return render_template('aboutus.html')

@app.route('/doctors')
def doctors():
    return render_template('doctor_phase.html')

@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    if request.method == 'POST':
        data = request.form
        print("Appointment Data:", data)
        flash("Appointment booked successfully!", "success")
        return render_template('appointment.html')
    return render_template('appointment.html')

@app.route('/patient_appointment', methods=['GET', 'POST'])
def patient_appointment():
    if request.method == 'POST':
        data = request.form
        print("Patient Appointment Data:", data)
        flash("Patient appointment submitted!", "success")
        return render_template('patient_appointment.html')
    return render_template('patient_appointment.html')

@app.route('/treatment')
def treatment():
    return render_template('patient_phase.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        data = request.form
        print("Contact Form:", data)
        flash("Thank you for contacting us!", "info")
        return render_template('contact.html')
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and users[username] == password:
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials.", "error")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        if password == confirm:
            users[email] = password
            flash("Account created successfully!", "success")
            return redirect(url_for('login'))
        else:
            flash("Passwords do not match!", "error")
    return render_template('signup.html')

if __name__ == '__main__':
    app.run(debug=True)
