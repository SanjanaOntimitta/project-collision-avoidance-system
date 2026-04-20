from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import re

app = Flask(__name__)
app.secret_key = "secret123"

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ================= VALIDATION =================
def is_valid_email(email):
    return email.endswith("@cvr.ac.in")

def is_valid_password(password):
    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[\W_]).{8,}$'
    return re.match(pattern, password)

# ================= ROUTES =================

@app.route('/')
def login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def handle_login():
    email = request.form['email']
    password = request.form['password']

    conn = sqlite3.connect('users.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    user = cur.fetchone()
    conn.close()

    if user:
        session['user'] = user[3]
        return redirect(url_for('home'))
    else:
        return "Invalid credentials ❌"


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/signup', methods=['POST'])
def handle_signup():
    fname = request.form['first_name']
    lname = request.form['last_name']
    email = request.form['email']
    password = request.form['password']

    if not is_valid_email(email):
        return "Use @cvr.ac.in email ❌"

    if not is_valid_password(password):
        return "Password must be strong ❌"

    try:
        conn = sqlite3.connect('users.db')
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)",
            (fname, lname, email, password)
        )

        conn.commit()
        conn.close()

        return render_template('success.html')

    except sqlite3.IntegrityError:
        return "User already exists ❌"


@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', user=session['user'])


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)