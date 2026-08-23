# ==========================================
# RISK FLAG MODEL
# ==========================================

from database import get_db_connection

class RiskFlagModel:
    @staticmethod
    def calculate_risk(student_profile):
        """Calculate risk level based on student data"""
        risk_factors = []
        
        # Attendance risk
        attendance = float(student_profile.get('attendance_percentage', 0) or 0)
        if attendance < 75:
            risk_factors.append("Low attendance")
            attendance_risk = True
        else:
            attendance_risk = False
        
        # Grade risk
        cgpa = float(student_profile.get('cgpa', 0) or 0)
        if cgpa < 6.0:
            risk_factors.append("Low CGPA")
            grade_risk = True
        else:
            grade_risk = False
        
        # Determine overall risk level
        if len(risk_factors) >= 2:
            risk_level = "high"
        elif len(risk_factors) == 1:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            'risk_level': risk_level,
            'risk_factors': ', '.join(risk_factors) if risk_factors else 'No risk factors',
            'attendance_risk': attendance_risk,
            'grade_risk': grade_risk
        }
    
    @staticmethod
    def save_risk_flags(student_id):
        """Calculate and save risk flags for a student"""
        from models.student_model import StudentModel
        
        profile = StudentModel.get_by_id(student_id)
        if not profile:
            return False
        
        risk_data = RiskFlagModel.calculate_risk(profile)
        
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Check if risk flag exists
        cursor.execute("SELECT id FROM risk_flags WHERE student_id = %s", (student_id,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE risk_flags SET
                    risk_level = %s,
                    risk_factors = %s,
                    attendance_risk = %s,
                    grade_risk = %s,
                    calculated_at = CURRENT_TIMESTAMP
                WHERE student_id = %s
            """, (risk_data['risk_level'], risk_data['risk_factors'], 
                  risk_data['attendance_risk'], risk_data['grade_risk'], student_id))
        else:
            cursor.execute("""
                INSERT INTO risk_flags (student_id, risk_level, risk_factors, attendance_risk, grade_risk)
                VALUES (%s, %s, %s, %s, %s)
            """, (student_id, risk_data['risk_level'], risk_data['risk_factors'],
                  risk_data['attendance_risk'], risk_data['grade_risk']))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    
    @staticmethod
    def get_by_student(student_id):
        """Get risk flags for a student"""
        conn = get_db_connection()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM risk_flags WHERE student_id = %s", (student_id,))
        risk = cursor.fetchone()
        cursor.close()
        conn.close()
        return risk
    
    @staticmethod
    def get_all_with_students():
        """Get all risk flags with student info"""
        conn = get_db_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT rf.*, sp.user_id, u.name, u.email, sp.roll_number, sp.department
            FROM risk_flags rf
            JOIN student_profiles sp ON rf.student_id = sp.id
            JOIN users u ON sp.user_id = u.id
            ORDER BY 
                CASE rf.risk_level
                    WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'low' THEN 3
                END
        """)
        risks = cursor.fetchall()
        cursor.close()
        conn.close()
        return risks






























        