# ==========================================
# MENTOR NOTES MODEL
# ==========================================

from database import get_db_connection
import datetime

class MentorNoteModel:
    @staticmethod
    def add_note(student_id, mentor_id, note, note_date=None):
        """Add a counseling note"""
        if not note_date:
            note_date = datetime.date.today()
        
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO mentor_notes (student_id, mentor_id, note, note_date)
            VALUES (%s, %s, %s, %s)
        """, (student_id, mentor_id, note, note_date))
        conn.commit()
        note_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return note_id
    
    @staticmethod
    def get_by_student(student_id):
        """Get all notes for a student"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT mn.*, u.name as mentor_name
                FROM mentor_notes mn
                JOIN users u ON mn.mentor_id = u.id
                WHERE mn.student_id = %s
                ORDER BY mn.created_at DESC
            """, (student_id,))
            notes = cursor.fetchall()
        except Exception as e:
            print(f"❌ Error fetching mentor notes: {e}")
            notes = []
        finally:
            cursor.close()
            conn.close()
        return notes
    
    @staticmethod
    def get_all():
        """Get all mentor notes"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT mn.*, u.name as mentor_name, sp.user_id
                FROM mentor_notes mn
                JOIN users u ON mn.mentor_id = u.id
                JOIN student_profiles sp ON mn.student_id = sp.id
                ORDER BY mn.created_at DESC
            """)
            notes = cursor.fetchall()
        except Exception as e:
            print(f"❌ Error fetching all mentor notes: {e}")
            notes = []
        finally:
            cursor.close()
            conn.close()
        return notes