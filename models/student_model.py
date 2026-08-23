# ==========================================
# STUDENT PROFILE MODEL
# ==========================================

from database import get_db_connection

class StudentModel:
    @staticmethod
    def create_or_update(user_id, data):
        """Create or update student profile"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor(dictionary=True)
        
        # Convert empty strings to None for integer fields
        def clean_value(value):
            if value == '' or value is None:
                return None
            return value
        
        # Clean all data
        cleaned_data = {
            'roll_number': data.get('roll_number'),
            'department': data.get('department'),
            'year': clean_value(data.get('year')),
            'semester': clean_value(data.get('semester')),
            'cgpa': clean_value(data.get('cgpa')),
            'attendance_percentage': clean_value(data.get('attendance_percentage')),
            'internal_marks': clean_value(data.get('internal_marks')),
            'assignments_submitted': clean_value(data.get('assignments_submitted')),
            'total_assignments': clean_value(data.get('total_assignments')),
            'disciplinary_notes': data.get('disciplinary_notes'),
            'extracurricular': data.get('extracurricular'),
            'profile_image': data.get('profile_image')
        }
        
        # Check if profile exists
        cursor.execute("SELECT id FROM student_profiles WHERE user_id = %s", (user_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing profile
            cursor.execute("""
                UPDATE student_profiles SET
                    roll_number = %s,
                    department = %s,
                    year = %s,
                    semester = %s,
                    cgpa = %s,
                    attendance_percentage = %s,
                    internal_marks = %s,
                    assignments_submitted = %s,
                    total_assignments = %s,
                    disciplinary_notes = %s,
                    extracurricular = %s,
                    profile_image = %s
                WHERE user_id = %s
            """, (
                cleaned_data['roll_number'],
                cleaned_data['department'],
                cleaned_data['year'],
                cleaned_data['semester'],
                cleaned_data['cgpa'],
                cleaned_data['attendance_percentage'],
                cleaned_data['internal_marks'],
                cleaned_data['assignments_submitted'],
                cleaned_data['total_assignments'],
                cleaned_data['disciplinary_notes'],
                cleaned_data['extracurricular'],
                cleaned_data['profile_image'],
                user_id
            ))
            profile_id = existing['id']
        else:
            # Create new profile
            cursor.execute("""
                INSERT INTO student_profiles (
                    user_id, roll_number, department, year, semester,
                    cgpa, attendance_percentage, internal_marks,
                    assignments_submitted, total_assignments,
                    disciplinary_notes, extracurricular, profile_image
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                cleaned_data['roll_number'],
                cleaned_data['department'],
                cleaned_data['year'],
                cleaned_data['semester'],
                cleaned_data['cgpa'],
                cleaned_data['attendance_percentage'],
                cleaned_data['internal_marks'],
                cleaned_data['assignments_submitted'],
                cleaned_data['total_assignments'],
                cleaned_data['disciplinary_notes'],
                cleaned_data['extracurricular'],
                cleaned_data['profile_image']
            ))
            profile_id = cursor.lastrowid
        
        conn.commit()
        cursor.close()
        conn.close()
        return profile_id
    
    @staticmethod
    def get_by_user_id(user_id):
        """Get student profile by user_id"""
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM student_profiles WHERE user_id = %s", (user_id,))
        profile = cursor.fetchone()
        cursor.close()
        conn.close()
        return profile
    
    @staticmethod
    def get_by_id(profile_id):
        """Get student profile by ID"""
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM student_profiles WHERE id = %s", (profile_id,))
        profile = cursor.fetchone()
        cursor.close()
        conn.close()
        return profile
    
    @staticmethod
    def get_all():
        """Get all student profiles with user info"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT sp.*, u.name, u.email 
            FROM student_profiles sp
            JOIN users u ON sp.user_id = u.id
            ORDER BY sp.id DESC
        """)
        profiles = cursor.fetchall()
        cursor.close()
        conn.close()
        return profiles
    
    @staticmethod
    def delete(profile_id):
        """Delete student profile"""
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM student_profiles WHERE id = %s", (profile_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True