# ==========================================
# NOTIFICATION MODEL
# ==========================================

from database import get_db_connection
from models.student_model import StudentModel

class NotificationModel:
    @staticmethod
    def create_notification(sender_id, sender_role, subject, message):
        """Create a new notification"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notifications (sender_id, sender_role, subject, message)
            VALUES (%s, %s, %s, %s)
        """, (sender_id, sender_role, subject, message))
        notification_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return notification_id
    
    @staticmethod
    def mark_read(student_id, notification_id):
        """Mark a notification as read"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE student_notifications 
            SET read_status = TRUE, read_at = CURRENT_TIMESTAMP
            WHERE student_id = %s AND notification_id = %s
        """, (student_id, notification_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
    @staticmethod
    def get_student_notifications(user_id):
        """Get all notifications for a student"""
        conn = get_db_connection()
        if not conn:
            return []
        
        # Get student profile
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM student_profiles WHERE user_id = %s", (user_id,))
        profile = cursor.fetchone()
        
        if not profile:
            cursor.close()
            conn.close()
            return []
        
        student_id = profile['id']
        
        cursor.execute("""
            SELECT n.*, sn.read_status, sn.read_at, u.name as sender_name
            FROM notifications n
            JOIN student_notifications sn ON n.id = sn.notification_id
            JOIN users u ON n.sender_id = u.id
            WHERE sn.student_id = %s
            ORDER BY n.created_at DESC
        """, (student_id,))
        notifications = cursor.fetchall()
        cursor.close()
        conn.close()
        return notifications
    
    @staticmethod
    def get_all_notifications():
        """Get all notifications"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT n.*, u.name as sender_name
            FROM notifications n
            JOIN users u ON n.sender_id = u.id
            ORDER BY n.created_at DESC
        """)
        notifications = cursor.fetchall()
        cursor.close()
        conn.close()
        return notifications