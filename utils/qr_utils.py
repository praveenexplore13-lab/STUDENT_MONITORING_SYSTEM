# ==========================================
# QR CODE UTILITIES
# ==========================================

import qrcode
import uuid
from PIL import Image
import os

def generate_qr_code(data, filename=None):
    """Generate QR code image"""
    if not filename:
        filename = f"qr_{uuid.uuid4().hex[:8]}.png"
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to static/qr_codes/
    path = os.path.join('static', 'qr_codes', filename)
    img.save(path)
    
    return f"qr_codes/{filename}"

def generate_class_qr(class_id, class_data):
    """Generate QR for a class"""
    data = f"CLASS:{class_id}:{class_data['subject']}:{class_data['class_time']}"
    return generate_qr_code(data)

def decode_qr_data(qr_data):
    """Decode QR data"""
    try:
        parts = qr_data.split(':')
        if parts[0] == 'CLASS':
            return {
                'class_id': int(parts[1]),
                'subject': parts[2],
                'class_time': parts[3]
            }
    except:
        pass
    return None