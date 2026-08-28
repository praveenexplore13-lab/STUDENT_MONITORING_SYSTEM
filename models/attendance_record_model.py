# ==========================================
# ATTENDANCE RECORD MODEL
# ==========================================

from database import get_db_connection

class AttendanceRecordModel:
    @staticmethod
    def mark_attendance(session_id, student_id, status='present'):
        """Mark attendance for a student"""
        conn = get_db_connection()
        if not conn:
            return False
        
        # Check if already marked
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id FROM attendance_records 
            WHERE session_id = %s AND student_id = %s
        """, (session_id, student_id))
        existing = cursor.fetchone()
        
        if existing:
            cursor.close()
            conn.close()
            return False
        
        # Mark attendance
        cursor.execute("""
            INSERT INTO attendance_records (session_id, student_id, status)
            VALUES (%s, %s, %s)
        """, (session_id, student_id, status))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
    @staticmethod
    def get_records_by_session(session_id):
        """Get all attendance records for a session"""
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
    
    @staticmethod
    def get_records_by_student(student_id):
        """Get all attendance records for a student"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT ar.*, s.subject, s.class_time, s.location
            FROM attendance_records ar
            JOIN attendance_sessions a_s ON ar.session_id = a_s.id
            JOIN classes s ON a_s.class_id = s.id
            WHERE ar.student_id = %s
            ORDER BY ar.marked_at DESC
        """, (student_id,))
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        return records
    
    @staticmethod
    def get_attendance_percentage(student_id):
        """Calculate attendance percentage for a student"""
        conn = get_db_connection()
        if not conn:
            return 0
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'present' THEN 1 END) as present,
                COUNT(*) as total
            FROM attendance_records
            WHERE student_id = %s
        """, (student_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result['total'] > 0:
            return round((result['present'] / result['total']) * 100, 2)
        return 0