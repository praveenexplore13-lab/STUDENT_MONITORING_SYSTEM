# ==========================================
# ATTENDANCE SESSION MODEL
# ==========================================

from database import get_db_connection
from datetime import datetime, timedelta
import random

class AttendanceSessionModel:
    @staticmethod
    def generate_otp():
        """Generate 4-digit OTP"""
        return str(random.randint(1000, 9999))
    
    @staticmethod
    def create_session(class_id, mentor_id):
        """Create a new attendance session with OTP"""
        conn = get_db_connection()
        if not conn:
            return False
        
        otp = AttendanceSessionModel.generate_otp()
        expires_at = datetime.now() + timedelta(minutes=5)
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO attendance_sessions 
            (class_id, mentor_id, otp, status, created_at, expires_at)
            VALUES (%s, %s, %s, 'active', NOW(), %s)
        """, (class_id, mentor_id, otp, expires_at))
        
        session_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return session_id, otp
    
    @staticmethod
    def get_active_session(class_id):
        """Get active session for a class"""
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM attendance_sessions 
            WHERE class_id = %s AND status = 'active'
            ORDER BY id DESC LIMIT 1
        """, (class_id,))
        session = cursor.fetchone()
        cursor.close()
        conn.close()
        return session
    
    @staticmethod
    def get_session(session_id):
        """Get session by ID"""
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.*, c.subject, c.location, u.name as mentor_name
            FROM attendance_sessions s
            JOIN classes c ON s.class_id = c.id
            JOIN users u ON s.mentor_id = u.id
            WHERE s.id = %s
        """, (session_id,))
        session = cursor.fetchone()
        cursor.close()
        conn.close()
        return session
    
    @staticmethod
    def validate_otp(session_id, otp):
        """Validate OTP for a session"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, otp, status, expires_at 
            FROM attendance_sessions 
            WHERE id = %s AND status = 'active'
        """, (session_id,))
        session = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not session:
            return False
        
        # Check if OTP matches
        if session['otp'] != otp:
            return False
        
        # Check if expired
        if datetime.now() > session['expires_at']:
            return False
        
        return True
    
    @staticmethod
    def close_session(session_id):
        """Close an attendance session"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE attendance_sessions 
            SET status = 'closed', closed_at = NOW()
            WHERE id = %s
        """, (session_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
    @staticmethod
    def update_counts(session_id):
        """Update present/absent counts for a session"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'present' THEN 1 END) as present,
                COUNT(CASE WHEN status = 'absent' THEN 1 END) as absent
            FROM attendance_records
            WHERE session_id = %s
        """, (session_id,))
        result = cursor.fetchone()
        
        if result:
            cursor.execute("""
                UPDATE attendance_sessions 
                SET total_present = %s, total_absent = %s
                WHERE id = %s
            """, (result[0], result[1], session_id))
            conn.commit()
        
        cursor.close()
        conn.close()
        return True
    
    @staticmethod
    def get_all_sessions():
        """Get all sessions for admin"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.*, c.subject, u.name as mentor_name
            FROM attendance_sessions s
            JOIN classes c ON s.class_id = c.id
            JOIN users u ON s.mentor_id = u.id
            ORDER BY s.created_at DESC
        """)
        sessions = cursor.fetchall()
        cursor.close()
        conn.close()
        return sessions