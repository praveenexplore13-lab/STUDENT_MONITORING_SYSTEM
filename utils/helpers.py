# ==========================================
# HELPER FUNCTIONS
# ==========================================

import os
from werkzeug.utils import secure_filename
from config import Config

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_profile_image(file):
    """Save profile image and return filename"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to prevent duplicate names
        import time
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{int(time.time())}{ext}"
        
        # Ensure directory exists
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        return f"uploads/profiles/{filename}"
    return None

def get_role(email):
    """Determine user role based on email"""
    if email == Config.ADMIN_EMAIL:
        return 'admin'
    elif email == Config.MENTOR_EMAIL:
        return 'mentor'
    else:
        return 'student'

def is_admin(email):
    """Check if user is admin"""
    return email == Config.ADMIN_EMAIL

def is_mentor(email):
    """Check if user is mentor"""
    return email == Config.MENTOR_EMAIL

def is_student(email):
    """Check if user is student"""
    return email != Config.ADMIN_EMAIL and email != Config.MENTOR_EMAIL

def get_student_emails():
    """Get all student emails"""
    from database import get_db_connection
    
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.email 
        FROM users u
        JOIN student_profiles sp ON u.id = sp.user_id
        WHERE u.email NOT IN (%s, %s)
    """, (Config.ADMIN_EMAIL, Config.MENTOR_EMAIL))
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [s['email'] for s in students]