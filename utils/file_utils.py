# ==========================================
# FILE UTILITIES
# ==========================================

import os
import time
from werkzeug.utils import secure_filename
from config import Config

def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_od_image(file):
    """Save OD proof image and return filename"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to prevent duplicate names
        name, ext = os.path.splitext(filename)
        filename = f"od_{int(time.time())}_{name}{ext}"
        
        # Ensure directory exists
        upload_folder = os.path.join('static', 'uploads', 'od_proofs')
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        return f"uploads/od_proofs/{filename}"
    return None

def delete_file(filepath):
    """Delete a file from server"""
    if filepath:
        full_path = os.path.join('static', filepath)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    return False