# ==========================================
# CHAT UTILITIES (GEMINI AI - FIXED)
# ==========================================

import google.generativeai as genai
from config import Config
import base64
import io
from PIL import Image

class GeminiChat:
    def __init__(self):
        """Initialize Gemini AI with API key"""
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('models/gemini-3.6-flash')
            print("✅ Gemini AI initialized successfully!")
        except Exception as e:
            print(f"❌ Gemini AI initialization failed: {e}")
            self.model = None

    def get_response_with_all_students(self, message, all_students_data, image_file=None):
        """Get response with all students data"""
        if not self.model:
            return "⚠️ Gemini AI is not configured."
        
        try:
            prompt = f"""
You are an AI Assistant for a Student Monitoring System.
You have access to ALL student data.

{all_students_data}

USER QUESTION: {message}

IMPORTANT INSTRUCTIONS:
1. Use the student data above to answer accurately.
2. If asked about LOW RISK students, list ONLY LOW risk students with their details.
3. If asked about HIGH RISK students, list ONLY HIGH risk students with their details.
4. If asked about MEDIUM RISK students, list ONLY MEDIUM risk students.
5. Provide clear, structured responses with student names, roll numbers, CGPA, and attendance.
6. Be accurate - only mention students from the data provided.

Answer:
"""
            if image_file and image_file.filename != "":
                image_bytes = image_file.read()
                image = Image.open(io.BytesIO(image_bytes))
                response = self.model.generate_content([prompt, image])
                return response.text
            else:
                response = self.model.generate_content(prompt)
                return response.text
        except Exception as e:
            print(f"❌ Gemini error: {e}")
            return f"⚠️ Error: {str(e)}"

    def get_response(self, message, student_data, image_file=None):
        """Get response for single student"""
        if not self.model:
            return "⚠️ Gemini AI is not configured."
        
        try:
            prompt = self.build_prompt(message, student_data)
            if image_file and image_file.filename != "":
                image_bytes = image_file.read()
                image = Image.open(io.BytesIO(image_bytes))
                response = self.model.generate_content([prompt, image])
                return response.text
            else:
                response = self.model.generate_content(prompt)
                return response.text
        except Exception as e:
            print(f"❌ Gemini error: {e}")
            return f"⚠️ Error: {str(e)}"

    def build_prompt(self, message, student_data):
        """Build prompt for student data"""
        base_prompt = """
You are an AI Assistant for a Student Monitoring System.
Be friendly, professional, and helpful.
"""
        
        if student_data:
            if isinstance(student_data, dict):
                student_prompt = f"""

STUDENT DATA:
- Name: {student_data.get('name', 'Not set')}
- Roll Number: {student_data.get('roll_number', 'Not set')}
- Department: {student_data.get('department', 'Not set')}
- CGPA: {student_data.get('cgpa', 'Not set')}
- Attendance: {student_data.get('attendance_percentage', 'Not set')}%
- Internal Marks: {student_data.get('internal_marks', 'Not set')}
- Assignments: {student_data.get('assignments_submitted', '0')}/{student_data.get('total_assignments', '0')}
"""
                if student_data.get('risk'):
                    risk = student_data['risk']
                    student_prompt += f"""
- Risk Level: {risk.get('risk_level', 'Not set').upper()}
- Risk Factors: {risk.get('risk_factors', 'No risk factors')}
"""
                base_prompt += student_prompt
        
        base_prompt += f"""

USER QUESTION: {message}

Answer naturally and helpfully.
"""
        return base_prompt