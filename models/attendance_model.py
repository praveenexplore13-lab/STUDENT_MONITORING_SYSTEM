# ==========================================
# ATTENDANCE MODEL - COMPLETE
# ==========================================

from database import get_db_connection
from datetime import datetime

class AttendanceModel:
    
    # ==========================================
    # MARK ATTENDANCE
    # ==========================================
    
    @staticmethod
    def mark_attendance(student_id, class_id, status='present', method='otp'):
        """Mark student attendance"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO attendance (student_id, class_id, status, method, marked_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (student_id, class_id, status, method))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
    # ==========================================
    # GET BY STUDENT (FIXED)
    # ==========================================
    
    @staticmethod
    def get_by_student(student_id):
        """Get attendance for a student"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, c.subject, c.class_time, c.location
            FROM attendance a
            JOIN classes c ON a.class_id = c.id
            WHERE a.student_id = %s
            ORDER BY a.marked_at DESC
        """, (student_id,))
        attendance = cursor.fetchall()
        cursor.close()
        conn.close()
        return attendance
    
    # ==========================================
    # GET BY CLASS
    # ==========================================
    
    @staticmethod
    def get_by_class(class_id):
        """Get attendance for a class"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, u.name as student_name, u.email
            FROM attendance a
            JOIN student_profiles sp ON a.student_id = sp.id
            JOIN users u ON sp.user_id = u.id
            WHERE a.class_id = %s
            ORDER BY a.marked_at DESC
        """, (class_id,))
        attendance = cursor.fetchall()
        cursor.close()
        conn.close()
        return attendance
    
    # ==========================================
    # GET ATTENDANCE PERCENTAGE
    # ==========================================
    
    @staticmethod
    def get_attendance_percentage(student_id):
        """Get attendance percentage for a student"""
        conn = get_db_connection()
        if not conn:
            return 0
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'present' THEN 1 END) as present,
                COUNT(*) as total
            FROM attendance
            WHERE student_id = %s
        """, (student_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result['total'] > 0:
            return round((result['present'] / result['total']) * 100, 2)
        return 0
    
    # ==========================================
    # GET ATTENDANCE BY SESSION (for OTP)
    # ==========================================
    
    @staticmethod
    def get_by_session(session_id):
        """Get attendance records for a session"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT ar.*, u.name, u.email, sp.roll_number
            FROM attendance_records ar
            JOIN student_profiles sp ON ar.student_id = sp.id
            JOIN users u ON sp.user_id = u.id
            WHERE ar.session_id = %s
            ORDER BY ar.status DESC, ar.marked_at ASC
        """, (session_id,))
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        return records
    
    # ==========================================
    # GET ALL ATTENDANCE RECORDS
    # ==========================================
    
    @staticmethod
    def get_all():
        """Get all attendance records"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, u.name as student_name, u.email, c.subject
            FROM attendance a
            JOIN student_profiles sp ON a.student_id = sp.id
            JOIN users u ON sp.user_id = u.id
            JOIN classes c ON a.class_id = c.id
            ORDER BY a.marked_at DESC
        """)
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        return records