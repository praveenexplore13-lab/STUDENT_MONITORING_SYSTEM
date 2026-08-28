# ==========================================
# ATTENDANCE ROUTES
# ==========================================

from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from utils.qr_utils import generate_qr_code, decode_qr_data
from models.class_model import ClassModel
from models.attendance_model import AttendanceModel
from models.student_model import StudentModel
from models.risk_flag_model import RiskFlagModel
from models.user_model import UserModel
from database import get_db_connection
from datetime import datetime
import json

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')


# ==========================================
# ADMIN - View All Attendance
# ==========================================

@attendance_bp.route('/admin')
def admin_attendance():
    """Admin view all attendance records"""
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    from utils.helpers import is_admin
    if not is_admin(email):
        flash('❌ Access denied. Admin only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    # Get all classes
    classes = ClassModel.get_all_classes()
    
    # Get all attendance records
    all_attendance = []
    for class_item in classes:
        records = AttendanceModel.get_attendance_by_class(class_item['id'])
        all_attendance.extend(records)
    
    return render_template('admin/admin_attendance.html',
                         name=session.get('user_name'),
                         classes=classes,
                         attendance=all_attendance)


# ==========================================
# ADMIN - Generate QR for Class
# ==========================================

@attendance_bp.route('/admin/qr/generate/<int:class_id>', methods=['POST'])
def admin_generate_qr(class_id):
    """Admin generates QR for a class"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    email = session.get('user_email', '')
    from utils.helpers import is_admin
    if not is_admin(email):
        return jsonify({'error': 'Access denied'}), 403
    
    class_data = ClassModel.get_class(class_id)
    if not class_data:
        return jsonify({'error': 'Class not found'}), 404
    
    # Generate QR data
    qr_data = f"CLASS:{class_id}:{class_data['subject']}:{class_data['class_time']}"
    qr_path = generate_qr_code(qr_data)
    
    # Update class with QR path
    ClassModel.update_qr_code(class_id, qr_path)
    
    return jsonify({
        'success': True,
        'qr_path': url_for('static', filename=qr_path),
        'qr_data': qr_data
    })


# ==========================================
# ADMIN - Create New Class
# ==========================================

@attendance_bp.route('/admin/create-class', methods=['POST'])
def admin_create_class():
    """Admin creates a new class"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    email = session.get('user_email', '')
    from utils.helpers import is_admin
    if not is_admin(email):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    subject = data.get('subject')
    class_time = data.get('class_time')
    duration = data.get('duration', 60)
    location = data.get('location', '')
    
    if not subject or not class_time:
        return jsonify({'error': 'Subject and time are required'}), 400
    
    class_id = ClassModel.create_class(subject, session['user_id'], class_time, duration, location)
    
    if class_id:
        return jsonify({'success': True, 'class_id': class_id})
    return jsonify({'error': 'Failed to create class'}), 500


# ==========================================
# MENTOR - View Attendance
# ==========================================

@attendance_bp.route('/mentor')
def mentor_attendance():
    """Mentor view attendance records"""
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    from utils.helpers import is_mentor
    if not is_mentor(email):
        flash('❌ Access denied. Mentor only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    # Get all students with attendance
    students = StudentModel.get_all()
    for student in students:
        student['attendance_percentage'] = AttendanceModel.get_attendance_percentage(student['id'])
    
    return render_template('mentor/mentor_attendance.html',
                         name=session.get('user_name'),
                         students=students)


# ==========================================
# STUDENT - Scan QR
# ==========================================

@attendance_bp.route('/student/scan')
def student_scan():
    """Student scans QR code"""
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('student/student_scan.html',
                         name=session.get('user_name'))


# ==========================================
# STUDENT - Mark Attendance via QR
# ==========================================

@attendance_bp.route('/student/mark', methods=['POST'])
def mark_attendance():
    """Mark attendance via QR scan"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    qr_data = data.get('qr_data')
    
    if not qr_data:
        return jsonify({'error': 'No QR data provided'}), 400
    
    # Decode QR
    decoded = decode_qr_data(qr_data)
    if not decoded:
        return jsonify({'error': 'Invalid QR code'}), 400
    
    class_id = decoded['class_id']
    
    # Get student profile
    user_id = session.get('user_id')
    student = StudentModel.get_by_user_id(user_id)
    
    if not student:
        return jsonify({'error': 'Student profile not found'}), 404
    
    # Mark attendance
    if AttendanceModel.mark_attendance(student['id'], class_id):
        # Update attendance percentage
        new_percentage = AttendanceModel.get_attendance_percentage(student['id'])
        
        # Update student profile attendance
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE student_profiles 
                SET attendance_percentage = %s 
                WHERE id = %s
            """, (new_percentage, student['id']))
            conn.commit()
            cursor.close()
            conn.close()
        
        # Recalculate risk
        RiskFlagModel.save_risk_flags(student['id'])
        
        return jsonify({
            'success': True,
            'message': 'Attendance marked successfully!',
            'attendance_percentage': new_percentage
        })
    
    return jsonify({'error': 'Failed to mark attendance'}), 500


# ==========================================
# STUDENT - View Attendance Report
# ==========================================

@attendance_bp.route('/student/report')
def student_attendance_report():
    """Student view attendance report"""
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    student = StudentModel.get_by_user_id(user_id)
    
    if not student:
        flash('⚠️ Complete your profile first.', 'warning')
        return redirect(url_for('student.student_edit_profile'))
    
    attendance = AttendanceModel.get_by_student(student['id'])
    percentage = AttendanceModel.get_attendance_percentage(student['id'])
    
    return render_template('student/student_attendance_report.html',
                         name=session.get('user_name'),
                         attendance=attendance,
                         percentage=percentage)


# ==========================================
# STUDENT - View Engagement
# ==========================================

@attendance_bp.route('/student/engagement')
def student_engagement():
    """Student view engagement score"""
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    student = StudentModel.get_by_user_id(user_id)
    
    if not student:
        flash('⚠️ Complete your profile first.', 'warning')
        return redirect(url_for('student.student_edit_profile'))
    
    from utils.engagement_calculator import calculate_student_engagement, get_engagement_prediction
    engagement = calculate_student_engagement(student['id'])
    prediction = get_engagement_prediction(student['id'])
    
    return render_template('student/student_engagement.html',
                         name=session.get('user_name'),
                         engagement=engagement,
                         prediction=prediction)


# ==========================================
# ADMIN - Engagement Dashboard
# ==========================================

@attendance_bp.route('/admin/engagement')
def admin_engagement():
    """Admin view engagement dashboard"""
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    from utils.helpers import is_admin
    if not is_admin(email):
        flash('❌ Access denied. Admin only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    from models.engagement_model import EngagementModel
    scores = EngagementModel.get_all_engagement_scores()
    
    return render_template('admin/admin_engagement.html',
                         name=session.get('user_name'),
                         scores=scores)


# ==========================================
# MENTOR - Engagement Dashboard
# ==========================================

@attendance_bp.route('/mentor/engagement')
def mentor_engagement():
    """Mentor view engagement dashboard"""
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    from utils.helpers import is_mentor
    if not is_mentor(email):
        flash('❌ Access denied. Mentor only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    from models.engagement_model import EngagementModel
    scores = EngagementModel.get_all_engagement_scores()
    
    return render_template('mentor/mentor_engagement.html',
                         name=session.get('user_name'),
                         scores=scores)