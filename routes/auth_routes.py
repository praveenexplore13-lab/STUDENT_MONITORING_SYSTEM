from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from config import Config  # ADD THIS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import timedelta
import re
from google.oauth2 import id_token
from google.auth.transport import requests

# ==========================================
# CREATE BLUEPRINT
# ==========================================

auth_bp = Blueprint('auth', __name__)

# ==========================================
# GMAIL CONFIGURATION (FROM CONFIG)
# ==========================================

GMAIL_EMAIL = Config.GMAIL_EMAIL
GMAIL_APP_PASSWORD = Config.GMAIL_APP_PASSWORD

# ==========================================
# GOOGLE CLIENT ID (FROM CONFIG)
# ==========================================

CLIENT_ID = Config.GOOGLE_CLIENT_ID

# ==========================================
# MYSQL DATABASE CONFIGURATION (FROM CONFIG)
# ==========================================

db_config = {
    "host": Config.DB_HOST,
    "user": Config.DB_USER,
    "password": Config.DB_PASSWORD,
    "database": Config.DB_NAME
}
# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db_connection():
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as e:
        print(f"❌ Database connection error: {e}")
        return None

# ==========================================
# GENERATE 6 DIGIT OTP
# ==========================================

def generate_otp():
    return str(random.randint(100000, 999999))

# ==========================================
# VALIDATE EMAIL
# ==========================================

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email)

# ==========================================
# SEND OTP EMAIL
# ==========================================

def send_otp_email(email, otp, purpose):
    if purpose == "register":
        subject = "Verify Your Registration"
        message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ max-width: 500px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .otp {{ background: #2563eb; color: white; font-size: 32px; padding: 15px; text-align: center; border-radius: 8px; letter-spacing: 8px; font-weight: bold; }}
                .footer {{ margin-top: 20px; color: #666; font-size: 12px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2 style="color: #2563eb;">🔐 Email Verification</h2>
                <p>Hello!</p>
                <p>Your registration OTP is:</p>
                <div class="otp">{otp}</div>
                <p style="margin-top: 20px;">Please enter this OTP to complete your registration.</p>
                <p>⏰ This OTP is valid for <strong>5 minutes</strong>.</p>
                <hr>
                <div class="footer">If you didn't request this, please ignore this email.</div>
            </div>
        </body>
        </html>
        """

    elif purpose == "reset":
        subject = "Reset Your Password"
        message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ max-width: 500px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .otp {{ background: #dc2626; color: white; font-size: 32px; padding: 15px; text-align: center; border-radius: 8px; letter-spacing: 8px; font-weight: bold; }}
                .footer {{ margin-top: 20px; color: #666; font-size: 12px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2 style="color: #dc2626;">🔐 Password Reset</h2>
                <p>Hello!</p>
                <p>Your password reset OTP is:</p>
                <div class="otp">{otp}</div>
                <p style="margin-top: 20px;">Please enter this OTP to reset your password.</p>
                <p>⏰ This OTP is valid for <strong>5 minutes</strong>.</p>
                <hr>
                <div class="footer">If you didn't request this, please ignore this email.</div>
            </div>
        </body>
        </html>
        """

    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_EMAIL
        msg["To"] = email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_EMAIL, email, msg.as_string())
        server.quit()

        print(f"✅ OTP email sent to {email}")
        return True

    except Exception as e:
        print("❌ EMAIL ERROR:", e)
        return False

# ==========================================
# HOME / DEFAULT PAGE
# ==========================================

@auth_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("auth.dashboard"))
    return redirect(url_for("auth.login"))

# ==========================================
# LOGIN
# ==========================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("auth.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        print(f"🔍 Login attempt for: {email}")

        if not email or not password:
            flash("⚠️ Please fill all fields.", "error")
            return redirect(url_for("auth.login"))

        try:
            conn = get_db_connection()
            if not conn:
                flash("❌ Database connection failed.", "error")
                return redirect(url_for("auth.login"))
                
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user:
                if user["password"] is None:
                    flash("❌ This email uses Google Login. Please sign in with Google.", "error")
                    return redirect(url_for("auth.login"))
                
                if check_password_hash(user["password"], password):
                    session.permanent = True
                    session["user_id"] = user["id"]
                    session["user_name"] = user["name"]
                    session["user_email"] = user["email"]

                    flash("✅ Login successful! Welcome, " + user["name"] + "!", "success")
                    return redirect(url_for("auth.dashboard"))
                else:
                    flash("❌ Invalid email or password.", "error")
                    return redirect(url_for("auth.login"))
            else:
                flash("❌ Invalid email or password.", "error")
                return redirect(url_for("auth.login"))

        except Exception as e:
            print("❌ LOGIN ERROR:", e)
            flash("❌ Something went wrong: " + str(e), "error")
            return redirect(url_for("auth.login"))

    return render_template("login.html", client_id=CLIENT_ID)

# ==========================================
# DASHBOARD - ROLE BASED REDIRECT
# ==========================================

@auth_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("⚠️ Please login first.", "error")
        return redirect(url_for("auth.login"))
    
    email = session.get("user_email", "")
    
    # Check role based on email
    from utils.helpers import get_role
    role = get_role(email)
    
    if role == 'admin':
        return redirect(url_for('admin.admin_dashboard'))
    elif role == 'mentor':
        return redirect(url_for('mentor.mentor_dashboard'))
    else:
        return redirect(url_for('student.student_dashboard'))

# ==========================================
# REGISTER
# ==========================================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            flash("⚠️ All fields are required.", "error")
            return redirect(url_for("auth.register"))

        if not is_valid_email(email):
            flash("⚠️ Please enter a valid email address.", "error")
            return redirect(url_for("auth.register"))

        if len(password) < 6:
            flash("⚠️ Password must be at least 6 characters.", "error")
            return redirect(url_for("auth.register"))

        try:
            conn = get_db_connection()
            if not conn:
                flash("❌ Database connection failed.", "error")
                return redirect(url_for("auth.register"))
                
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()
            cursor.close()
            conn.close()

            if existing_user:
                flash("❌ This email is already registered.", "error")
                return redirect(url_for("auth.register"))

            otp = generate_otp()
            session["register_name"] = name
            session["register_email"] = email
            session["register_password"] = password
            session["register_otp"] = otp

            if send_otp_email(email, otp, "register"):
                flash("✅ OTP sent to your email.", "success")
                return redirect(url_for("auth.verify_register"))
            else:
                flash("❌ Could not send OTP. Try again.", "error")
                return redirect(url_for("auth.register"))

        except Exception as e:
            print("❌ REGISTER ERROR:", e)
            flash("❌ Something went wrong. Please try again.", "error")
            return redirect(url_for("auth.register"))

    return render_template("register.html")

# ==========================================
# VERIFY REGISTRATION OTP
# ==========================================

@auth_bp.route("/verify-register", methods=["GET", "POST"])
def verify_register():
    if "register_email" not in session:
        flash("⚠️ Please register first.", "error")
        return redirect(url_for("auth.register"))

    if request.method == "POST":
        user_otp = request.form["otp"].strip()

        if not user_otp:
            flash("⚠️ Please enter the OTP.", "error")
            return redirect(url_for("auth.verify_register"))

        if user_otp == session.get("register_otp"):
            name = session["register_name"]
            email = session["register_email"]
            password = session["register_password"]

            hashed_password = generate_password_hash(password)

            try:
                conn = get_db_connection()
                if not conn:
                    flash("❌ Database connection failed.", "error")
                    return redirect(url_for("auth.register"))
                    
                cursor = conn.cursor()

                cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                    (name, email, hashed_password)
                )
                conn.commit()
                cursor.close()
                conn.close()

                session.pop("register_name", None)
                session.pop("register_email", None)
                session.pop("register_password", None)
                session.pop("register_otp", None)

                flash("✅ Registration successful! Please login.", "success")
                return redirect(url_for("auth.login"))

            except Exception as e:
                print("❌ DATABASE ERROR:", e)
                flash("❌ Registration failed. Please try again.", "error")
                return redirect(url_for("auth.register"))
        else:
            flash("❌ Invalid OTP. Please try again.", "error")
            return redirect(url_for("auth.verify_register"))

    return render_template("register_otp.html", email=session.get("register_email"))

# ==========================================
# GOOGLE LOGIN
# ==========================================

@auth_bp.route("/google-login", methods=["POST"])
def google_login():
    try:
        data = request.get_json()
        token = data.get("credential")

        if not token:
            return jsonify({
                "success": False,
                "message": "Google token missing"
            }), 400

        user_info = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            CLIENT_ID
        )

        name = user_info.get("name")
        email = user_info["email"]

        conn = get_db_connection()
        if not conn:
            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500
            
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user is None:
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (%s, %s, NULL)",
                (name, email)
            )
            conn.commit()
            user_id = cursor.lastrowid
        else:
            user_id = user["id"]
            if user["name"] != name:
                cursor.execute(
                    "UPDATE users SET name = %s WHERE id = %s",
                    (name, user_id)
                )
                conn.commit()

        cursor.close()
        conn.close()

        session.permanent = True
        session["user_id"] = user_id
        session["user_name"] = name
        session["user_email"] = email

        return jsonify({
            "success": True,
            "message": "Google login successful",
            "name": name,
            "email": email
        })

    except Exception as e:
        print("❌ Google Login Error:", e)
        return jsonify({
            "success": False,
            "message": "Google login failed"
        }), 401

# ==========================================
# FORGOT PASSWORD
# ==========================================

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"].strip().lower()

        if not email:
            flash("⚠️ Please enter your email.", "error")
            return redirect(url_for("auth.forgot_password"))

        if not is_valid_email(email):
            flash("⚠️ Please enter a valid email.", "error")
            return redirect(url_for("auth.forgot_password"))

        try:
            conn = get_db_connection()
            if not conn:
                flash("❌ Database connection failed.", "error")
                return redirect(url_for("auth.forgot_password"))
                
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT id, password FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if not user:
                flash("❌ This email is not registered.", "error")
                return redirect(url_for("auth.forgot_password"))

            if user["password"] is None:
                flash("❌ This email uses Google Login. Please sign in with Google.", "error")
                return redirect(url_for("auth.forgot_password"))

            otp = generate_otp()
            session["reset_email"] = email
            session["reset_otp"] = otp

            if send_otp_email(email, otp, "reset"):
                flash("✅ OTP sent to your registered email.", "success")
                return redirect(url_for("auth.verify_reset"))
            else:
                flash("❌ Could not send OTP. Try again.", "error")
                return redirect(url_for("auth.forgot_password"))

        except Exception as e:
            print("❌ FORGOT PASSWORD ERROR:", e)
            flash("❌ Something went wrong.", "error")
            return redirect(url_for("auth.forgot_password"))

    return render_template("forgot_password.html")

# ==========================================
# VERIFY RESET OTP
# ==========================================

@auth_bp.route("/verify-reset", methods=["GET", "POST"])
def verify_reset():
    if "reset_email" not in session:
        flash("⚠️ Please request password reset first.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        user_otp = request.form["otp"].strip()

        if not user_otp:
            flash("⚠️ Please enter the OTP.", "error")
            return redirect(url_for("auth.verify_reset"))

        if user_otp == session.get("reset_otp"):
            session["reset_verified"] = True
            flash("✅ OTP verified successfully.", "success")
            return redirect(url_for("auth.reset_password"))
        else:
            flash("❌ Invalid OTP. Try again.", "error")
            return redirect(url_for("auth.verify_reset"))

    return render_template("verify_reset.html")

# ==========================================
# RESET PASSWORD
# ==========================================

@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if not session.get("reset_verified"):
        flash("⚠️ Please verify your OTP first.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("❌ Passwords do not match.", "error")
            return redirect(url_for("auth.reset_password"))

        if len(password) < 6:
            flash("⚠️ Password must contain at least 6 characters.", "error")
            return redirect(url_for("auth.reset_password"))

        email = session["reset_email"]
        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            if not conn:
                flash("❌ Database connection failed.", "error")
                return redirect(url_for("auth.reset_password"))
                
            cursor = conn.cursor()

            cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
            conn.commit()
            cursor.close()
            conn.close()

            session.pop("reset_email", None)
            session.pop("reset_otp", None)
            session.pop("reset_verified", None)

            flash("✅ Password changed successfully! Please login.", "success")
            return redirect(url_for("auth.login"))

        except Exception as e:
            print("❌ RESET PASSWORD ERROR:", e)
            flash("❌ Could not update password.", "error")
            return redirect(url_for("auth.reset_password"))

    return render_template("reset_password.html")

# ==========================================
# LOGOUT
# ==========================================

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("👋 Logged out successfully.", "success")
    return redirect(url_for("auth.login") + "?logout=true")