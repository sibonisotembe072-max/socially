from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import timedelta

app = Flask(__name__)

# Secret key for sessions
app.secret_key = "my-super-secret-key-123"

# Keep login for 7 days
app.permanent_session_lifetime = timedelta(days=7)

USER_DB = "users.db"
CHAT_DB = "chats.db"


# =========================
# DATABASES
# =========================

def create_databases():

    # Users database
    conn = sqlite3.connect(USER_DB)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

    # Chats database
    conn = sqlite3.connect(CHAT_DB)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


create_databases()


# =========================
# HOME
# =========================

@app.route("/")
def home():

    # If already logged in
    if "username" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        try:

            conn = sqlite3.connect(USER_DB)
            c = conn.cursor()

            c.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )

            conn.commit()
            conn.close()

            flash("Profile created successfully. Please login.", "success")

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            flash("Username already exists.", "error")

    return render_template("account.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = sqlite3.connect(USER_DB)
        c = conn.cursor()

        c.execute(
            "SELECT id, username, password FROM users WHERE username = ?",
            (username,)
        )

        user = c.fetchone()

        conn.close()

        # Check username and password
        if user and check_password_hash(user[2], password):

            # Clear old session
            session.clear()

            # Store logged-in user
            session["username"] = user[1]

            # Remember login
            session.permanent = True

            flash("Login successful!", "success")

            return redirect(url_for("dashboard"))

        else:

            flash("Invalid username or password.", "error")

    return render_template("login.html")


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    # User MUST be logged in
    if "username" not in session:

        flash("Please login first.", "error")

        return redirect(url_for("login"))

    # Get messages
    conn = sqlite3.connect(CHAT_DB)
    c = conn.cursor()

    c.execute("""
        SELECT username, message, time
        FROM chats
        ORDER BY id DESC
    """)

    info = c.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        info=info
    )


# =========================
# SUBMIT MESSAGE
# =========================

@app.route("/submit", methods=["POST"])
def submit():

    # User MUST be logged in
    if "username" not in session:

        flash("Please login first.", "error")

        return redirect(url_for("login"))

    message = request.form.get("message", "").strip()

    if message:

        conn = sqlite3.connect(CHAT_DB)
        c = conn.cursor()

        c.execute(
            """
            INSERT INTO chats (username, message)
            VALUES (?, ?)
            """,
            (session["username"], message)
        )

        conn.commit()
        conn.close()

    return redirect(url_for("dashboard"))


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.", "success")

    return redirect(url_for("login"))


# =========================
# RUN APP
# =========================

if __name__ == "__main__":
    app.run(debug=True)