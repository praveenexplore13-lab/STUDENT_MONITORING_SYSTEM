# ==========================================
# OD REQUEST MODEL
# ==========================================

from database import get_db_connection
from datetime import datetime

class ODModel:
    @staticmethod
    def create_request(student_id, title, description, od_date, proof_image=None):
        """Create a new OD request"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO od_requests 
            (student_id, title, description, od_date, proof_image) 
            VALUES (%s, %s, %s, %s, %s)
        """, (student_id, title, description, od_date, proof_image))
        
        request_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return request_id
    
    @staticmethod
    def get_by_student(student_id):
        """Get all OD requests for a student"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM od_requests 
            WHERE student_id = %s 
            ORDER BY created_at DESC
        """, (student_id,))
        requests = cursor.fetchall()
        cursor.close()
        conn.close()
        return requests
    
    @staticmethod
    def get_by_id(request_id):
        """Get OD request by ID with student info"""
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT o.*, u.id as user_id, u.name as student_name, u.email as student_email,
                   sp.roll_number, sp.department
            FROM od_requests o
            JOIN student_profiles sp ON o.student_id = sp.id
            JOIN users u ON sp.user_id = u.id
            WHERE o.id = %s
        """, (request_id,))
        request = cursor.fetchone()
        cursor.close()
        conn.close()
        return request
    
    @staticmethod
    def get_all_pending():
        """Get all pending OD requests"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT o.*, u.id as user_id, u.name as student_name, u.email as student_email,
                   sp.roll_number, sp.department
            FROM od_requests o
            JOIN student_profiles sp ON o.student_id = sp.id
            JOIN users u ON sp.user_id = u.id
            WHERE o.admin_status = 'pending'
            ORDER BY o.created_at ASC
        """)
        requests = cursor.fetchall()
        cursor.close()
        conn.close()
        return requests
    
    @staticmethod
    def get_all_mentor_pending():
        """Get all OD requests pending mentor approval"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT o.*, u.id as user_id, u.name as student_name, u.email as student_email,
                   sp.roll_number, sp.department
            FROM od_requests o
            JOIN student_profiles sp ON o.student_id = sp.id
            JOIN users u ON sp.user_id = u.id
            WHERE o.mentor_status = 'pending'
            ORDER BY o.created_at ASC
        """)
        requests = cursor.fetchall()
        cursor.close()
        conn.close()
        return requests
    
    @staticmethod
    def get_all_by_mentor():
        """Get all OD requests with mentor status"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT o.*, u.id as user_id, u.name as student_name, u.email as student_email,
                   sp.roll_number, sp.department
            FROM od_requests o
            JOIN student_profiles sp ON o.student_id = sp.id
            JOIN users u ON sp.user_id = u.id
            ORDER BY o.created_at DESC
        """)
        requests = cursor.fetchall()
        cursor.close()
        conn.close()
        return requests
    
    @staticmethod
    def approve_mentor(request_id, comment=None):
        """Mentor approves OD request"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE od_requests 
            SET mentor_status = 'approved', 
                mentor_comment = %s,
                mentor_approved_at = NOW()
            WHERE id = %s
        """, (comment, request_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
    @staticmethod
    def deny_mentor(request_id, comment=None):
        """Mentor denies OD request"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE od_requests 
            SET mentor_status = 'denied', 
                mentor_comment = %s
            WHERE id = %s
        """, (comment, request_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
    @staticmethod
    def approve_admin(request_id, comment=None):
        """Admin approves OD request (final approval)"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE od_requests 
            SET admin_status = 'approved', 
                admin_comment = %s,
                admin_approved_at = NOW()
            WHERE id = %s
        """, (comment, request_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
    @staticmethod
    def deny_admin(request_id, comment=None):
        """Admin denies OD request (final denial)"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE od_requests 
            SET admin_status = 'denied', 
                admin_comment = %s
            WHERE id = %s
        """, (comment, request_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
    @staticmethod
    def get_status_text(request):
        """Get status text based on mentor and admin status"""
        if request['admin_status'] == 'approved':
            return '✅ Approved (Final)'
        elif request['admin_status'] == 'denied':
            return '❌ Denied by Admin'
        elif request['mentor_status'] == 'denied':
            return '❌ Denied by Mentor'
        elif request['mentor_status'] == 'approved' and request['admin_status'] == 'pending':
            return '⏳ Waiting for Admin Approval'
        else:
            return '⏳ Pending'
    
    @staticmethod
    def get_status_color(request):
        """Get status color for display"""
        if request['admin_status'] == 'approved':
            return 'green'
        elif request['admin_status'] == 'denied':
            return 'red'
        elif request['mentor_status'] == 'denied':
            return 'red'
        elif request['mentor_status'] == 'approved' and request['admin_status'] == 'pending':
            return 'yellow'
        else:
            return 'yellow'