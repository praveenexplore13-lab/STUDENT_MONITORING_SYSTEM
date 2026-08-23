# ==========================================
# CONFIGURATION SETTINGS
# ==========================================

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'my_super_secret_key_12345')
    
    # Database settings
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME', 'login_otp_db')
    
    # Gmail settings (for notifications)
    GMAIL_EMAIL = os.getenv('GMAIL_EMAIL', 'praveencpk2007@gmail.com')
    GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', '')
    
    # Google Client ID
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    
    # Upload settings
    UPLOAD_FOLDER = "static/uploads/profiles"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Admin & Mentor hardcoded credentials
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@gmail.com')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    MENTOR_EMAIL = os.getenv('MENTOR_EMAIL', 'mentor@gmail.com')
    MENTOR_PASSWORD = os.getenv('MENTOR_PASSWORD', 'mentor123')