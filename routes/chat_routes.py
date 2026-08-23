# ==========================================
# AI CHATBOT ROUTES (UPDATED WITH ROLE PAGES)
# ==========================================

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from models.student_model import StudentModel
from models.risk_flag_model import RiskFlagModel
from models.user_model import UserModel
from models.mentor_note_model import MentorNoteModel
from utils.file_utils import save_od_image
import ollama
import os
import re

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')


# ==========================================
# ROLE-SPECIFIC CHAT PAGES
# ==========================================

@chat_bp.route('/student')
def student_chat():
    """Student AI Chat Page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    student = StudentModel.get_by_user_id(user_id)
    
    if student:
        risk = RiskFlagModel.get_by_student(student['id'])
        if risk:
            student['risk'] = risk
    
    return render_template('student/student_chat.html',
                         name=session.get('user_name'),
                         student=student)


@chat_bp.route('/mentor')
def mentor_chat():
    """Mentor AI Chat Page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Get all students for sidebar
    all_students = StudentModel.get_all()
    for student in all_students:
        risk = RiskFlagModel.get_by_student(student['id'])
        if risk:
            student['risk_level'] = risk.get('risk_level', 'low')
        else:
            student['risk_level'] = 'low'
    
    return render_template('mentor/mentor_chat.html',
                         name=session.get('user_name'),
                         all_students=all_students)


@chat_bp.route('/admin')
def admin_chat():
    """Admin AI Chat Page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Get all students for sidebar
    all_students = StudentModel.get_all()
    for student in all_students:
        risk = RiskFlagModel.get_by_student(student['id'])
        if risk:
            student['risk_level'] = risk.get('risk_level', 'low')
        else:
            student['risk_level'] = 'low'
    
    return render_template('admin/admin_chat.html',
                         name=session.get('user_name'),
                         all_students=all_students)


# ==========================================
# CHAT API (UNCHANGED - WORKS FOR ALL ROLES)
# ==========================================

@chat_bp.route('/api', methods=['POST'])
def chat_api():
    """AI Chat API"""
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
    
    user_id = session.get('user_id')
    email = session.get('user_email', '')
    role = get_user_role(email)
    
    message = request.form.get('message', '').strip()
    file = request.files.get('file')
    file_info = None
    
    if file and file.filename:
        file_path = save_od_image(file)
        if file_path:
            file_info = {
                'name': file.filename,
                'path': file_path,
                'size': file.content_length
            }
    
    if not message and not file_info:
        return jsonify({'reply': 'Please ask something or upload a file!'})
    
    try:
        # ==========================================
        # STUDENT: Only their own data
        # ==========================================
        if role == 'student':
            student = StudentModel.get_by_user_id(user_id)
            if not student:
                return jsonify({'reply': "⚠️ Please complete your profile first."})
            
            risk = RiskFlagModel.get_by_student(student['id'])
            data_str = build_student_data_string(student, risk)
            
            # Check if asking about profile/risk
            if is_profile_query(message):
                return jsonify({'reply': generate_student_response(student, risk)})
            
            # General question
            reply = get_ollama_response(message, role, data_str, file_info)
            return jsonify({'reply': reply})
        
        # ==========================================
        # MENTOR / ADMIN: Can see ALL students
        # ==========================================
        elif role in ['admin', 'mentor']:
            # Check if asking about high risk students
            if 'high risk' in message.lower() or 'which student' in message.lower():
                return jsonify({'reply': get_high_risk_students()})
            
            # Check if asking about low attendance
            if 'low attendance' in message.lower():
                return jsonify({'reply': get_low_attendance_students()})
            
            # Check if asking about a specific student
            student_name = extract_student_name(message)
            if student_name:
                return jsonify({'reply': analyze_specific_student(student_name)})
            
            # Check if asking about summary
            if 'summary' in message.lower() or 'overview' in message.lower():
                return jsonify({'reply': get_summary_report()})
            
            # General question with all student data context
            all_students_data = get_all_students_data_string()
            reply = get_ollama_response(message, role, all_students_data, file_info)
            return jsonify({'reply': reply})
        
        # ==========================================
        # FALLBACK
        # ==========================================
        else:
            return jsonify({'reply': "I'm not sure how to help with that."})
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return jsonify({'reply': f"⚠️ Error: {str(e)}. Please try again."})


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_user_role(email):
    from config import Config
    if email == Config.ADMIN_EMAIL:
        return 'admin'
    elif email == Config.MENTOR_EMAIL:
        return 'mentor'
    else:
        return 'student'


def is_profile_query(message):
    keywords = ['my risk', 'my profile', 'my cgpa', 'my attendance', 
                'my marks', 'my grade', 'am i at risk', 'my performance',
                'tell me about myself', 'my details', 'why i have']
    return any(keyword in message.lower() for keyword in keywords)


def extract_student_name(message):
    patterns = [
        r'(?:about\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'(?:student\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'(?:tell me about\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'(?:who is\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'
    ]
    if 'which student' in message.lower():
        return None
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            name = match.group(1)
            if name.lower() not in ['student', 'high', 'low', 'risk']:
                return name
    return None


def build_student_data_string(student, risk):
    data = f"""
STUDENT PROFILE:
- Name: {student.get('name', 'Not set')}
- Roll Number: {student.get('roll_number', 'Not set')}
- Department: {student.get('department', 'Not set')}
- CGPA: {student.get('cgpa', 'Not set')}
- Attendance: {student.get('attendance_percentage', 'Not set')}%
- Internal Marks: {student.get('internal_marks', 'Not set')}
- Assignments: {student.get('assignments_submitted', '0')}/{student.get('total_assignments', '0')}
"""
    if risk:
        data += f"- Risk Level: {risk.get('risk_level', 'Not set').upper()}\n"
        data += f"- Risk Factors: {risk.get('risk_factors', 'No risk factors')}\n"
    return data


def get_all_students_data_string():
    students = StudentModel.get_all()
    if not students:
        return "No students in the system."
    data = "ALL STUDENTS DATA:\n\n"
    for i, student in enumerate(students, 1):
        risk = RiskFlagModel.get_by_student(student['id'])
        data += f"{i}. {student.get('name', 'Unknown')} (Roll: {student.get('roll_number', 'N/A')})\n"
        data += f"   - CGPA: {student.get('cgpa', 'N/A')}\n"
        data += f"   - Attendance: {student.get('attendance_percentage', 'N/A')}%\n"
        if risk:
            data += f"   - Risk: {risk.get('risk_level', 'N/A').upper()}\n"
        data += "\n"
    return data


def get_ollama_response(message, role, data_context, file_info=None):
    try:
        role_prompt = {
            'student': "You are a helpful AI assistant for a student. Use their data to help them.",
            'mentor': "You are a helpful AI assistant for a mentor. Provide professional insights.",
            'admin': "You are a helpful AI assistant for an administrator. Provide detailed overviews."
        }
        
        prompt = f"""
{role_prompt.get(role, 'You are a helpful AI assistant.')}

DATA:
{data_context}

USER QUESTION: {message}

INSTRUCTIONS:
1. If the question is about the student's data, use the data above.
2. If the question is general, answer it naturally.
3. Be friendly, helpful, and professional.
4. For mentors/admin: If asked about students, use the data above.

ANSWER:
"""
        if file_info:
            prompt += f"\nThe user uploaded a file: {file_info['name']}. Acknowledge it."

        response = ollama.chat(
            model='llama3.2:1b',
            messages=[
                {'role': 'system', 'content': "You are a helpful AI assistant. Answer questions using the provided data when relevant."},
                {'role': 'user', 'content': prompt}
            ]
        )
        return response['message']['content']
    except Exception as e:
        print(f"❌ Ollama error: {e}")
        return "🤖 I'm having trouble connecting. Please try again!"


def generate_student_response(student, risk):
    response = "📊 **Your Profile Analysis:**\n\n"
    response += f"📋 **Student:** {student.get('name', 'Unknown')}\n"
    response += f"🎓 **Roll Number:** {student.get('roll_number', 'Not set')}\n"
    response += f"🏫 **Department:** {student.get('department', 'Not set')}\n"
    response += f"📊 **CGPA:** {student.get('cgpa', 'Not set')}\n"
    response += f"📈 **Attendance:** {student.get('attendance_percentage', 'Not set')}%\n"
    response += f"📝 **Internal Marks:** {student.get('internal_marks', 'Not set')}\n"
    response += f"📎 **Assignments:** {student.get('assignments_submitted', '0')}/{student.get('total_assignments', '0')}\n\n"
    
    if risk:
        response += f"⚠️ **Risk Level:** {risk.get('risk_level', 'Not set').upper()}\n"
        response += f"📝 **Risk Factors:** {risk.get('risk_factors', 'No risk factors')}\n\n"
        if risk.get('risk_level') == 'high':
            response += "💡 **Advice:** 🔴 You are at HIGH risk. Meet your mentor immediately."
        elif risk.get('risk_level') == 'medium':
            response += "💡 **Advice:** 🟡 You are at MEDIUM risk. Monitor your progress."
        else:
            response += "💡 **Advice:** 🟢 You are doing great! Keep it up! 🎉"
    else:
        response += "📝 Complete your profile to get risk analysis."
    
    return response


def get_high_risk_students():
    students = StudentModel.get_all()
    high_risk = []
    for student in students:
        risk = RiskFlagModel.get_by_student(student['id'])
        if risk and risk['risk_level'] == 'high':
            high_risk.append(student)
    if not high_risk:
        return "🎉 No students are currently at HIGH risk!"
    response = "📊 **HIGH RISK STUDENTS:**\n\n"
    for i, s in enumerate(high_risk, 1):
        response += f"{i}. 🔴 **{s.get('name', 'Unknown')}** (Roll: {s.get('roll_number', 'N/A')})\n"
        response += f"   - CGPA: {s.get('cgpa', 'N/A')}\n"
        response += f"   - Attendance: {s.get('attendance_percentage', 'N/A')}%\n"
        response += f"   ⚠️ Needs immediate attention!\n\n"
    return response


def get_low_attendance_students():
    students = StudentModel.get_all()
    low_attendance = []
    for student in students:
        att = student.get('attendance_percentage', 100)
        if att < 75:
            low_attendance.append(student)
    if not low_attendance:
        return "🎉 All students have good attendance!"
    response = "📊 **STUDENTS WITH LOW ATTENDANCE (<75%):**\n\n"
    for i, s in enumerate(low_attendance, 1):
        response += f"{i}. **{s.get('name', 'Unknown')}** (Roll: {s.get('roll_number', 'N/A')})\n"
        response += f"   - Attendance: {s.get('attendance_percentage', 'N/A')}%\n"
        response += f"   ⚠️ Needs improvement!\n\n"
    return response


def analyze_specific_student(student_name):
    students = StudentModel.get_all()
    found = None
    for s in students:
        if student_name.lower() in s.get('name', '').lower():
            found = s
            break
    if not found:
        return f"👤 I couldn't find a student named '{student_name}'."
    risk = RiskFlagModel.get_by_student(found['id'])
    response = f"👤 **Student Profile: {found['name']}**\n\n"
    response += f"📋 **Roll Number:** {found.get('roll_number', 'Not set')}\n"
    response += f"🏫 **Department:** {found.get('department', 'Not set')}\n"
    response += f"📊 **CGPA:** {found.get('cgpa', 'Not set')}\n"
    response += f"📈 **Attendance:** {found.get('attendance_percentage', 'Not set')}%\n"
    if risk:
        response += f"\n⚠️ **Risk Level:** {risk.get('risk_level', 'Not set').upper()}\n"
        response += f"📝 **Risk Factors:** {risk.get('risk_factors', 'None')}"
    return response


def get_summary_report():
    students = StudentModel.get_all()
    total = len(students)
    if total == 0:
        return "📊 No students in the system yet."
    high = medium = low = 0
    for student in students:
        risk = RiskFlagModel.get_by_student(student['id'])
        if risk:
            if risk['risk_level'] == 'high':
                high += 1
            elif risk['risk_level'] == 'medium':
                medium += 1
            else:
                low += 1
    response = f"📊 **STUDENT SUMMARY**\n\n"
    response += f"👥 **Total:** {total}\n"
    response += f"🔴 **High Risk:** {high}\n"
    response += f"🟡 **Medium Risk:** {medium}\n"
    response += f"🟢 **Low Risk:** {low}\n"
    if high > 0:
        response += f"\n⚠️ **Alert:** {high} students need immediate attention!"
    return response