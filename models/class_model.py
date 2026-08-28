# ==========================================
# CLASS MODEL
# ==========================================

from database import get_db_connection
from datetime import datetime

class ClassModel:
    @staticmethod
    def create_class(subject, teacher_id, class_time, duration, location):
        """Create a new class session"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO classes (subject, teacher_id, class_time, duration, location, qr_code)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (subject, teacher_id, class_time, duration, location, ''))
        
        class_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return class_id
    
    @staticmethod
    def get_class(class_id):
        """Get class by ID"""
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.*, u.name as teacher_name
            FROM classes c
            JOIN users u ON c.teacher_id = u.id
            WHERE c.id = %s
        """, (class_id,))
        class_data = cursor.fetchone()
        cursor.close()
        conn.close()
        return class_data
    
    @staticmethod
    def get_all_classes():
        """Get all classes"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT c.*, u.name as teacher_name
            FROM classes c
            JOIN users u ON c.teacher_id = u.id
            ORDER BY c.class_time DESC
        """)
        classes = cursor.fetchall()
        cursor.close()
        conn.close()
        return classes
    
    @staticmethod
    def update_qr_code(class_id, qr_data):
        """Update QR code for class"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE classes SET qr_code = %s WHERE id = %s
        """, (qr_data, class_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True