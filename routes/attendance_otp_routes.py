# ==========================================
# ATTENDANCE OTP ROUTES
# ==========================================

from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from models.class_model import ClassModel
from models.attendance_session_model import AttendanceSessionModel
from models.attendance_record_model import AttendanceRecordModel
from models.student_model import StudentModel
from models.risk_flag_model import RiskFlagModel
from utils.helpers import is_admin, is_mentor, is_student
from utils.email_utils import send_notification_email
from database import get_db_connection
from datetime import datetime
import random

attendance_otp_bp = Blueprint('attendance_otp', __name__, url_prefix='/attendance-otp')


# ==========================================
# MENTOR - ATTENDANCE PAGE
# ==========================================

@attendance_otp_bp.route('/mentor')
def mentor_attendance():
    """Mentor attendance management page"""
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_mentor(email):
        flash('❌ Access denied. Mentor only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    # Get all students
    students = StudentModel.get_all()
    
    # Get active session if any
    active_session = None
    # Check if there's an active session (simplified - using first class)
    # We'll use class_id=1 as default or find any active session
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM attendance_sessions 
            WHERE status = 'active' 
            ORDER BY id DESC LIMIT 1
        """)
        active_session = cursor.fetchone()
        cursor.close()
        conn.close()
    
    return render_template('mentor/mentor_attendance_otp.html',
                         name=session.get('user_name'),
                         students=students,
                         active_session=active_session)


# ==========================================
# MENTOR - START ATTENDANCE
# ==========================================

@attendance_otp_bp.route('/mentor/start', methods=['POST'])
def mentor_start_attendance():
    """Mentor starts attendance and generates OTP"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    email = session.get('user_email', '')
    if not is_mentor(email):
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        class_id = data.get('class_id', 1)  # Default class_id if not provided
        
        # Check if active session exists
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id FROM attendance_sessions 
            WHERE class_id = %s AND status = 'active'
        """, (class_id,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Active session already exists'}), 400
        
        # Generate OTP
        otp = str(random.randint(1000, 9999))
        
        # Create session
        cursor.execute("""
            INSERT INTO attendance_sessions 
            (class_id, mentor_id, otp, status, expires_at)
            VALUES (%s, %s, %s, 'active', DATE_ADD(NOW(), INTERVAL 1 HOUR))
        """, (class_id, session['user_id'], otp))
        
        session_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'otp': otp,
            'message': f'OTP Generated: {otp}'
        })
        
    except Exception as e:
        print(f"❌ Start attendance error: {e}")
        return jsonify({'error': str(e)}), 500


# ==========================================
# MENTOR - CLOSE ATTENDANCE
# ==========================================

@attendance_otp_bp.route('/mentor/close/<int:session_id>', methods=['POST'])
def mentor_close_attendance(session_id):
    """Mentor closes attendance session"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    email = session.get('user_email', '')
    if not is_mentor(email):
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE attendance_sessions 
            SET status = 'closed', closed_at = NOW()
            WHERE id = %s AND mentor_id = %s
        """, (session_id, session['user_id']))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Attendance closed successfully'})
        
    except Exception as e:
        print(f"❌ Close attendance error: {e}")
        return jsonify({'error': str(e)}), 500


# ==========================================
# MENTOR - LIVE ATTENDANCE
# ==========================================

@attendance_otp_bp.route('/mentor/live/<int:session_id>')
def mentor_live_attendance(session_id):
    """Get live attendance data"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Get session
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM attendance_sessions WHERE id = %s
        """, (session_id,))
        session_data = cursor.fetchone()
        
        if not session_data:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Session not found'}), 404
        
        # Get all students
        students = StudentModel.get_all()
        
        # Get attendance records
        cursor.execute("""
            SELECT student_id, status FROM attendance_records 
            WHERE session_id = %s
        """, (session_id,))
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Build student list with status
        student_status = {}
        for record in records:
            student_status[record['student_id']] = record['status']
        
        student_list = []
        present_count = 0
        absent_count = 0
        
        for student in students:
            status = student_status.get(student['id'], 'absent')
            if status == 'present':
                present_count += 1
            else:
                absent_count += 1
            student_list.append({
                'id': student['id'],
                'name': student.get('name', 'Unknown'),
                'roll_number': student.get('roll_number', 'N/A'),
                'status': status
            })
        
        return jsonify({
            'success': True,
            'present': present_count,
            'absent': absent_count,
            'total': len(students),
            'students': student_list
        })
        
    except Exception as e:
        print(f"❌ Live attendance error: {e}")
        return jsonify({'error': str(e)}), 500


# ==========================================
# STUDENT - MARK ATTENDANCE
# ==========================================

@attendance_otp_bp.route('/student/mark', methods=['POST'])
def student_mark_attendance():
    """Student marks attendance using OTP"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    email = session.get('user_email', '')
    if not is_student(email):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    otp = data.get('otp', '').strip()
    
    if not otp or len(otp) != 4:
        return jsonify({'error': 'Please enter a valid 4-digit OTP'}), 400
    
    try:
        # Find active session with this OTP
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM attendance_sessions 
            WHERE otp = %s AND status = 'active'
            ORDER BY id DESC LIMIT 1
        """, (otp,))
        session_data = cursor.fetchone()
        
        if not session_data:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Invalid OTP. Please check with your mentor.'}), 400
        
        # Get student profile
        user_id = session.get('user_id')
        student = StudentModel.get_by_user_id(user_id)
        
        if not student:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Student profile not found'}), 404
        
        # Check if already marked
        cursor.execute("""
            SELECT id FROM attendance_records 
            WHERE session_id = %s AND student_id = %s
        """, (session_data['id'], student['id']))
        existing = cursor.fetchone()
        
        if existing:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Attendance already marked'}), 400
        
        # Mark attendance
        cursor.execute("""
            INSERT INTO attendance_records (session_id, student_id, status)
            VALUES (%s, %s, 'present')
        """, (session_data['id'], student['id']))
        conn.commit()
        cursor.close()
        conn.close()
        
        # Get attendance percentage
        percentage = AttendanceRecordModel.get_attendance_percentage(student['id'])
        
        return jsonify({
            'success': True,
            'message': '✅ Attendance marked successfully!',
            'attendance_percentage': percentage
        })
        
    except Exception as e:
        print(f"❌ Mark attendance error: {e}")
        return jsonify({'error': str(e)}), 500


# ==========================================
# STUDENT - ATTENDANCE PAGE
# ==========================================

@attendance_otp_bp.route('/student')
def student_attendance():
    """Student attendance marking page"""
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_student(email):
        flash('❌ Access denied. Student only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    return render_template('student/student_scan.html',
                         name=session.get('user_name'))


# ==========================================
# ADMIN - REPORTS
# ==========================================

@attendance_otp_bp.route('/admin/reports')
def admin_reports():
    """Admin view all attendance reports"""
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_admin(email):
        flash('❌ Access denied. Admin only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    try:
        conn = get_db_connection()
        if not conn:
            flash('❌ Database connection failed.', 'error')
            return redirect(url_for('admin.admin_dashboard'))
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.*, c.subject, u.name as mentor_name
            FROM attendance_sessions s
            JOIN classes c ON s.class_id = c.id
            JOIN users u ON s.mentor_id = u.id
            ORDER BY s.created_at DESC
        """)
        sessions = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Calculate statistics
        total_sessions = len(sessions)
        total_present = 0
        total_absent = 0
        
        for session_data in sessions:
            total_present += session_data.get('total_present', 0)
            total_absent += session_data.get('total_absent', 0)
        
        stats = {
            'total_sessions': total_sessions,
            'total_present': total_present,
            'total_absent': total_absent,
            'total_students': total_present + total_absent
        }
        
        return render_template('admin/admin_attendance_reports.html',
                             name=session.get('user_name'),
                             sessions=sessions,
                             stats=stats)
                             
    except Exception as e:
        print(f"❌ Admin reports error: {e}")
        flash('❌ Error loading reports.', 'error')
        return redirect(url_for('admin.admin_dashboard'))