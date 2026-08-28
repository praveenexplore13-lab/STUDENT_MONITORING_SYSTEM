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
        class_id = data.get('class_id', 1)
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Check if classes exist
        cursor.execute("SELECT id FROM classes LIMIT 1")
        class_data = cursor.fetchone()
        
        if not class_data:
            cursor.close()
            conn.close()
            return jsonify({'error': 'No class found. Please create a class first.'}), 400
        
        # Use first class if class_id doesn't exist
        cursor.execute("SELECT id FROM classes WHERE id = %s", (class_id,))
        exists = cursor.fetchone()
        if not exists:
            class_id = class_data['id']
        
        # Check if active session exists
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


@attendance_otp_bp.route('/mentor/live/<int:session_id>')
def mentor_live_attendance(session_id):
    """Get live attendance data"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM attendance_sessions WHERE id = %s", (session_id,))
        session_data = cursor.fetchone()
        
        if not session_data:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Session not found'}), 404
        
        students = StudentModel.get_all()
        
        cursor.execute("""
            SELECT student_id, status FROM attendance_records 
            WHERE session_id = %s
        """, (session_id,))
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        
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
        
        user_id = session.get('user_id')
        student = StudentModel.get_by_user_id(user_id)
        
        if not student:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Student profile not found'}), 404
        
        cursor.execute("""
            SELECT id FROM attendance_records 
            WHERE session_id = %s AND student_id = %s
        """, (session_data['id'], student['id']))
        existing = cursor.fetchone()
        
        if existing:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Attendance already marked'}), 400
        
        cursor.execute("""
            INSERT INTO attendance_records (session_id, student_id, status)
            VALUES (%s, %s, 'present')
        """, (session_data['id'], student['id']))
        conn.commit()
        cursor.close()
        conn.close()
        
        # Update attendance percentage in student profile
        from models.attendance_model import AttendanceModel
        percentage = AttendanceModel.get_attendance_percentage(student['id'])
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE student_profiles 
                SET attendance_percentage = %s 
                WHERE id = %s
            """, (percentage, student['id']))
            conn.commit()
            cursor.close()
            conn.close()
        
        RiskFlagModel.save_risk_flags(student['id'])
        
        return jsonify({
            'success': True,
            'message': '✅ Attendance marked successfully!',
            'attendance_percentage': percentage
        })
        
    except Exception as e:
        print(f"❌ Mark attendance error: {e}")
        return jsonify({'error': str(e)}), 500


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
    
    user_id = session.get('user_id')
    student = StudentModel.get_by_user_id(user_id)
    
    attendance_percentage = 0
    if student:
        from models.attendance_model import AttendanceModel
        attendance_percentage = AttendanceModel.get_attendance_percentage(student['id'])
    
    return render_template('student/student_attendance_otp.html',
                         name=session.get('user_name'),
                         attendance_percentage=attendance_percentage)


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
        
        total_present = 0
        total_absent = 0
        
        for session_data in sessions:
            total_present += session_data.get('total_present', 0)
            total_absent += session_data.get('total_absent', 0)
        
        stats = {
            'total_sessions': len(sessions),
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


# ==========================================
# MENTOR - ATTENDANCE HISTORY BY DATE
# ==========================================

@attendance_otp_bp.route('/mentor/history')
def mentor_attendance_history():
    """Mentor view attendance history by date"""
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_mentor(email):
        flash('❌ Access denied. Mentor only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    # Get date from query param, default to today
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    conn = get_db_connection()
    if not conn:
        flash('❌ Database connection failed.', 'error')
        return redirect(url_for('mentor.mentor_dashboard'))
    
    cursor = conn.cursor(dictionary=True)
    
    # Get all students with their attendance status for the selected date
    cursor.execute("""
        SELECT 
            sp.id as student_id,
            u.name as student_name,
            sp.roll_number,
            sp.department,
            ar.status,
            ar.record_date,
            DATE_FORMAT(ar.record_time, '%h:%i %p') as record_time,
            s.otp,
            c.subject,
            s.session_time,
            CASE 
                WHEN ar.status = 'present' THEN 'Present'
                WHEN ar.status = 'absent' THEN 'Absent'
                ELSE 'Not Marked'
            END as attendance_status
        FROM student_profiles sp
        JOIN users u ON sp.user_id = u.id
        LEFT JOIN attendance_records ar ON sp.id = ar.student_id AND ar.record_date = %s
        LEFT JOIN attendance_sessions s ON ar.session_id = s.id
        LEFT JOIN classes c ON s.class_id = c.id
        ORDER BY ar.status DESC, u.name ASC
    """, (selected_date,))
    
    records = cursor.fetchall()
    
    # Calculate statistics
    total_students = len(records)
    present_count = len([r for r in records if r['status'] == 'present'])
    absent_count = len([r for r in records if r['status'] == 'absent'])
    not_marked_count = len([r for r in records if r['status'] is None])
    
    cursor.close()
    conn.close()
    
    return render_template('mentor/mentor_attendance_history.html',
                         name=session.get('user_name'),
                         records=records,
                         selected_date=selected_date,
                         total_students=total_students,
                         present_count=present_count,
                         absent_count=absent_count,
                         not_marked_count=not_marked_count,
                         today=datetime.now().date())


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
    
    user_id = session.get('user_id')
    student = StudentModel.get_by_user_id(user_id)
    
    attendance_percentage = 0
    today_status = None
    today_date = datetime.now().date()
    
    if student:
        from models.attendance_model import AttendanceModel
        attendance_percentage = AttendanceModel.get_attendance_percentage(student['id'])
        
        # Check if student marked attendance TODAY
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    status,
                    session_id,
                    DATE_FORMAT(record_time, '%h:%i %p') as record_time,
                    DATE_FORMAT(record_date, '%W, %d-%m-%Y') as record_date
                FROM attendance_records 
                WHERE student_id = %s 
                AND record_date = %s
                ORDER BY id DESC LIMIT 1
            """, (student['id'], today_date))
            today_status = cursor.fetchone()
            cursor.close()
            conn.close()
    
    return render_template('student/student_attendance_otp.html',
                         name=session.get('user_name'),
                         attendance_percentage=attendance_percentage,
                         today_status=today_status,
                         today=today_date.strftime('%A, %d-%m-%Y'))