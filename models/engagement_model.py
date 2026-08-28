# ==========================================
# ENGAGEMENT MODEL
# ==========================================

from database import get_db_connection
from datetime import datetime

class EngagementModel:
    @staticmethod
    def calculate_engagement_score(student_id):
        """Calculate engagement score for a student"""
        conn = get_db_connection()
        if not conn:
            return 0
        
        cursor = conn.cursor(dictionary=True)
        
        # Get attendance percentage
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'present' THEN 1 END) as present,
                COUNT(*) as total
            FROM attendance
            WHERE student_id = %s
        """, (student_id,))
        attendance = cursor.fetchone()
        
        # Get assignment submissions
        cursor.execute("""
            SELECT 
                assignments_submitted,
                total_assignments
            FROM student_profiles
            WHERE user_id = (SELECT user_id FROM student_profiles WHERE id = %s)
        """, (student_id,))
        profile = cursor.fetchone()
        
        # Get mentor notes count (participation)
        cursor.execute("""
            SELECT COUNT(*) as notes
            FROM mentor_notes
            WHERE student_id = %s
        """, (student_id,))
        notes = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Calculate scores
        attendance_score = (attendance['present'] / attendance['total'] * 50) if attendance and attendance['total'] > 0 else 0
        assignment_score = (profile['assignments_submitted'] / profile['total_assignments'] * 30) if profile and profile['total_assignments'] > 0 else 0
        participation_score = min(notes['notes'] * 5, 20) if notes else 0
        
        total_score = attendance_score + assignment_score + participation_score
        
        return round(min(total_score, 100), 2)
    
    @staticmethod
    def get_engagement_level(score):
        """Get engagement level based on score"""
        if score >= 80:
            return 'high', '🔵 High Engagement'
        elif score >= 60:
            return 'medium', '🟡 Medium Engagement'
        elif score >= 40:
            return 'low', '🟠 Low Engagement'
        else:
            return 'critical', '🔴 Critical Engagement'
    
    @staticmethod
    def save_engagement_score(student_id, score):
        """Save engagement score"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO engagement_scores (student_id, score, calculated_at)
            VALUES (%s, %s, NOW())
            ON DUPLICATE KEY UPDATE score = %s, calculated_at = NOW()
        """, (student_id, score, score))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
    @staticmethod
    def get_all_engagement_scores():
        """Get all engagement scores with student info"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT es.*, u.name, u.email, sp.roll_number
            FROM engagement_scores es
            JOIN student_profiles sp ON es.student_id = sp.id
            JOIN users u ON sp.user_id = u.id
            ORDER BY es.score DESC
        """)
        scores = cursor.fetchall()
        cursor.close()
        conn.close()
        return scores