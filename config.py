# ==========================================
# CONFIGURATION SETTINGS
# ==========================================

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    # ==========================================
    # FLASK SETTINGS
    # ==========================================
    SECRET_KEY = os.getenv('SECRET_KEY', 'my_super_secret_key_12345')

    # ==========================================
    # DATABASE SETTINGS
    # ==========================================
    # Local MySQL defaults are used when running
    # on your computer. Render environment variables
    # will override these values after deployment.
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'Praveen2007')
    DB_NAME = os.getenv('DB_NAME', 'login_otp_db')

    # ==========================================
    # GMAIL SETTINGS (FOR NOTIFICATIONS)
    # ==========================================
    GMAIL_EMAIL = os.getenv('GMAIL_EMAIL', 'praveencpk2007@gmail.com')
    GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', '')

    # ==========================================
    # GOOGLE CLIENT ID
    # ==========================================
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')

    # ==========================================
    # OLLAMA CONFIGURATION
    # ==========================================
    OLLAMA_URL = os.getenv(
        'OLLAMA_URL',
        'http://localhost:11434/api/generate'
    )
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:1b')

    # ==========================================
    # UPLOAD SETTINGS
    # ==========================================
    UPLOAD_FOLDER = "static/uploads/profiles"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # ==========================================
    # ADMIN & MENTOR CREDENTIALS
    # ==========================================
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@gmail.com')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

    MENTOR_EMAIL = os.getenv('MENTOR_EMAIL', 'mentor@gmail.com')
    MENTOR_PASSWORD = os.getenv('MENTOR_PASSWORD', 'mentor123')