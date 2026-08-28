# ==========================================
# ATTENDANCE MODEL
# ==========================================

from database import get_db_connection
from datetime import datetime, date, timedelta

class AttendanceModel:
    
    # ==========================================
    # GET WORKING DAY NUMBER FROM TODAY
    # ==========================================
    
    @staticmethod
    def get_working_day_number():
        """Calculate working day number starting from 28-08-2026 as Day 1"""
        start_date = date(2026, 8, 28)  # August 28, 2026
        today = date.today()
        delta = today - start_date
        return delta.days + 1  # Day 1 on 28-08-2026
    
    # ==========================================
    # GET TOTAL WORKING DAYS
    # ==========================================
    
    @staticmethod
    def get_total_working_days():
        """Return total working days (260)"""
        return 260
    
    # ==========================================
    # GET STUDENT ATTENDANCE WITH 5% PER PRESENT
    # ==========================================
    
    @staticmethod
    def get_student_attendance_with_percentage(student_id):
        """Get attendance with 5% per present calculation"""
        conn = get_db_connection()
        if not conn:
            return {
                'total_working_days': 260,
                'working_day': 1,
                'present_count': 0,
                'absent_count': 0,
                'not_marked_count': 0,
                'attendance_percentage': 0,
                'records': []
            }
        
        cursor = conn.cursor(dictionary=True)
        
        # Get total present count from attendance_records table
        cursor.execute("""
            SELECT COUNT(*) as present_count
            FROM attendance_records
            WHERE student_id = %s AND status = 'present'
        """, (student_id,))
        present_result = cursor.fetchone()
        present_count = present_result['present_count'] if present_result else 0
        
        # Get total absent count from attendance_records table
        cursor.execute("""
            SELECT COUNT(*) as absent_count
            FROM attendance_records
            WHERE student_id = %s AND status = 'absent'
        """, (student_id,))
        absent_result = cursor.fetchone()
        absent_count = absent_result['absent_count'] if absent_result else 0
        
        # Get all records with details
        cursor.execute("""
            SELECT 
                ar.id,
                ar.status,
                ar.record_date,
                DATE_FORMAT(ar.record_time, '%%H:%%i') as record_time,
                s.otp,
                c.subject,
                c.location
            FROM attendance_records ar
            LEFT JOIN attendance_sessions s ON ar.session_id = s.id
            LEFT JOIN classes c ON s.class_id = c.id
            WHERE ar.student_id = %s
            ORDER BY ar.record_date DESC, ar.record_time DESC
        """, (student_id,))
        records = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Calculate working day number
        working_day = AttendanceModel.get_working_day_number()
        total_working_days = AttendanceModel.get_total_working_days()
        
        # Calculate percentage: Present × 5% (capped at 100%)
        attendance_percentage = min(present_count * 5, 100)
        
        return {
            'total_working_days': total_working_days,
            'working_day': working_day,
            'present_count': present_count,
            'absent_count': absent_count,
            'not_marked_count': 0,
            'attendance_percentage': attendance_percentage,
            'records': records
        }
    
    # ==========================================
    # MARK ATTENDANCE
    # ==========================================
    
    @staticmethod
    def mark_attendance(student_id, class_id, status='present', method='qr'):
        """Mark student attendance"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Check if already marked
        cursor.execute("""
            SELECT id FROM attendance 
            WHERE student_id = %s AND class_id = %s
        """, (student_id, class_id))
        existing = cursor.fetchone()
        
        if existing:
            cursor.close()
            conn.close()
            return False
        
        # Insert attendance
        cursor.execute("""
            INSERT INTO attendance (student_id, class_id, status, method, marked_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (student_id, class_id, status, method))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
    # ==========================================
    # GET ATTENDANCE BY STUDENT
    # ==========================================
    
    @staticmethod
    def get_by_student(student_id):
        """Get all attendance records for a student"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, 
                   c.subject, 
                   c.class_time, 
                   c.location,
                   c.duration
            FROM attendance a
            JOIN classes c ON a.class_id = c.id
            WHERE a.student_id = %s
            ORDER BY a.marked_at DESC
        """, (student_id,))
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        return records
    
    # ==========================================
    # GET ATTENDANCE BY CLASS
    # ==========================================
    
    @staticmethod
    def get_by_class(class_id):
        """Get all attendance records for a class"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, 
                   u.name as student_name, 
                   u.email,
                   sp.roll_number
            FROM attendance a
            JOIN student_profiles sp ON a.student_id = sp.id
            JOIN users u ON sp.user_id = u.id
            WHERE a.class_id = %s
            ORDER BY a.marked_at DESC
        """, (class_id,))
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        return records
    
    # ==========================================
    # GET ATTENDANCE PERCENTAGE
    # ==========================================
    
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
    # GET ATTENDANCE PERCENTAGE BY CLASS
    # ==========================================
    
    @staticmethod
    def get_class_attendance_percentage(class_id):
        """Calculate attendance percentage for a class"""
        conn = get_db_connection()
        if not conn:
            return 0
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'present' THEN 1 END) as present,
                COUNT(*) as total
            FROM attendance
            WHERE class_id = %s
        """, (class_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result['total'] > 0:
            return round((result['present'] / result['total']) * 100, 2)
        return 0
    
    # ==========================================
    # GET PRESENT COUNT
    # ==========================================
    
    @staticmethod
    def get_present_count(student_id):
        """Get number of present days for a student"""
        conn = get_db_connection()
        if not conn:
            return 0
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT COUNT(*) as present
            FROM attendance
            WHERE student_id = %s AND status = 'present'
        """, (student_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result['present'] if result else 0
    
    # ==========================================
    # GET TOTAL CLASSES
    # ==========================================
    
    @staticmethod
    def get_total_classes(student_id):
        """Get total number of classes for a student"""
        conn = get_db_connection()
        if not conn:
            return 0
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM attendance
            WHERE student_id = %s
        """, (student_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result['total'] if result else 0
    
    # ==========================================
    # GET ATTENDANCE SUMMARY
    # ==========================================
    
    @staticmethod
    def get_attendance_summary(student_id):
        """Get complete attendance summary for a student"""
        conn = get_db_connection()
        if not conn:
            return {
                'total_classes': 0,
                'present': 0,
                'absent': 0,
                'percentage': 0
            }
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                COUNT(*) as total_classes,
                COUNT(CASE WHEN status = 'present' THEN 1 END) as present,
                COUNT(CASE WHEN status = 'absent' THEN 1 END) as absent
            FROM attendance
            WHERE student_id = %s
        """, (student_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result['total_classes'] > 0:
            result['percentage'] = round((result['present'] / result['total_classes']) * 100, 2)
        else:
            result['percentage'] = 0
        
        return result
    
    # ==========================================
    # UPDATE ATTENDANCE STATUS
    # ==========================================
    
    @staticmethod
    def update_attendance_status(attendance_id, status):
        """Update attendance status"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE attendance 
            SET status = %s 
            WHERE id = %s
        """, (status, attendance_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
    # ==========================================
    # DELETE ATTENDANCE RECORD
    # ==========================================
    
    @staticmethod
    def delete_attendance(attendance_id):
        """Delete an attendance record"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM attendance WHERE id = %s", (attendance_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
    # ==========================================
    # GET ATTENDANCE BY DATE RANGE
    # ==========================================
    
    @staticmethod
    def get_by_date_range(student_id, start_date, end_date):
        """Get attendance records between dates"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, c.subject, c.class_time, c.location
            FROM attendance a
            JOIN classes c ON a.class_id = c.id
            WHERE a.student_id = %s 
            AND DATE(a.marked_at) BETWEEN %s AND %s
            ORDER BY a.marked_at DESC
        """, (student_id, start_date, end_date))
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        return records
    
    # ==========================================
    # GET ALL ATTENDANCE RECORDS (ADMIN)
    # ==========================================
    
    @staticmethod
    def get_all():
        """Get all attendance records (for admin)"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, 
                   u.name as student_name, 
                   u.email,
                   sp.roll_number,
                   c.subject as class_subject,
                   c.class_time
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
    
    # ==========================================
    # GET ATTENDANCE STATISTICS
    # ==========================================
    
    @staticmethod
    def get_statistics():
        """Get attendance statistics"""
        conn = get_db_connection()
        if not conn:
            return {
                'total_records': 0,
                'total_present': 0,
                'total_absent': 0,
                'overall_percentage': 0
            }
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN status = 'present' THEN 1 END) as total_present,
                COUNT(CASE WHEN status = 'absent' THEN 1 END) as total_absent
            FROM attendance
        """)
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result['total_records'] > 0:
            result['overall_percentage'] = round((result['total_present'] / result['total_records']) * 100, 2)
        else:
            result['overall_percentage'] = 0
        
        return result