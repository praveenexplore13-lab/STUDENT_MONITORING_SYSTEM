# ==========================================
# ATTENDANCE OTP ROUTES (WITH DATE/TIME)
# ==========================================

from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from models.class_model import ClassModel
from models.attendance_session_model import AttendanceSessionModel
from models.attendance_record_model import AttendanceRecordModel
from models.student_model import StudentModel
from models.risk_flag_model import RiskFlagModel
from utils.helpers import is_admin, is_mentor, is_student
from database import get_db_connection
from datetime import datetime, date
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
    
    students = StudentModel.get_all()
    
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
        
        # Get present/absent counts for active session
        if active_session:
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'present' THEN 1 END) as present_count,
                    COUNT(CASE WHEN status = 'absent' THEN 1 END) as absent_count
                FROM attendance_records
                WHERE session_id = %s
            """, (active_session['id'],))
            counts = cursor.fetchone()
            active_session['total_present'] = counts['present_count'] if counts else 0
            active_session['total_absent'] = counts['absent_count'] if counts else 0
        
        cursor.close()
        conn.close()
    
    return render_template('mentor/mentor_attendance_otp.html',
                         name=session.get('user_name'),
                         students=students,
                         active_session=active_session,
                         today=datetime.now().strftime('%A, %d-%m-%Y'))


@attendance_otp_bp.route('/mentor/start', methods=['POST'])
def mentor_start_attendance():
    """Mentor starts attendance and generates OTP (auto-cleans stuck sessions)"""
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
        
        # Check if class exists
        cursor.execute("SELECT id FROM classes LIMIT 1")
        class_data = cursor.fetchone()
        
        if not class_data:
            cursor.close()
            conn.close()
            return jsonify({'error': 'No class found. Please create a class first.'}), 400
        
        cursor.execute("SELECT id FROM classes WHERE id = %s", (class_id,))
        exists = cursor.fetchone()
        if not exists:
            class_id = class_data['id']
        
        # Check for active session and AUTO-CLOSE it
        cursor.execute("""
            SELECT id FROM attendance_sessions 
            WHERE class_id = %s AND status = 'active'
        """, (class_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Auto-close the stuck session
            cursor.execute("""
                UPDATE attendance_sessions 
                SET status = 'closed', closed_at = NOW() 
                WHERE id = %s
            """, (existing['id'],))
            conn.commit()
            print(f"Auto-closed stuck session ID: {existing['id']}")
        
        # Generate OTP
        otp = str(random.randint(1000, 9999))
        
        now = datetime.now()
        session_date = now.date()
        session_time = now.time()
        expires_at = now.replace(hour=now.hour + 1)
        
        cursor.execute("""
            INSERT INTO attendance_sessions 
            (class_id, mentor_id, otp, status, expires_at, session_date, session_time)
            VALUES (%s, %s, %s, 'active', %s, %s, %s)
        """, (class_id, session['user_id'], otp, expires_at, session_date, session_time))
        
        session_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        # Convert ALL datetime objects to strings for JSON
        return jsonify({
            'success': True,
            'session_id': session_id,
            'otp': otp,
            'date': session_date.strftime('%A, %d-%m-%Y'),
            'time': session_time.strftime('%H:%M'),
            'expires_at': expires_at.strftime('%H:%M:%S'),
            'message': f'OTP Generated: {otp}'
        })
        
    except Exception as e:
        print(f"Start attendance error: {e}")
        return jsonify({'error': str(e)}), 500


@attendance_otp_bp.route('/mentor/close/<int:session_id>', methods=['POST'])
def close_attendance(session_id):
    """Mentor closes attendance - marks absent students and stores final list"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    email = session.get('user_email', '')
    if not is_mentor(email):
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # 1. Get ALL students
        students = StudentModel.get_all()
        
        # 2. Get students who already marked PRESENT for this session
        cursor.execute("""
            SELECT student_id, status
            FROM attendance_records 
            WHERE session_id = %s AND status = 'present'
        """, (session_id,))
        marked_students = cursor.fetchall()
        marked_ids = [m['student_id'] for m in marked_students]
        
        # 3. Mark ALL unmarked students as ABSENT with today's date
        today = date.today()
        current_time = datetime.now().time()
        
        present_count = len(marked_students)
        absent_count = 0
        
        for student in students:
            if student['id'] not in marked_ids:
                cursor.execute("""
                    INSERT INTO attendance_records 
                    (student_id, session_id, status, record_date, record_time)
                    VALUES (%s, %s, 'absent', %s, %s)
                """, (student['id'], session_id, today, current_time))
                absent_count += 1
        
        # 4. Update session status and counts
        cursor.execute("""
            UPDATE attendance_sessions 
            SET status = 'closed', 
                total_present = %s, 
                total_absent = %s,
                closed_at = NOW()
            WHERE id = %s
        """, (present_count, absent_count, session_id))
        
        conn.commit()
        
        # 5. Get FINAL attendance records with student details
        cursor.execute("""
            SELECT 
                ar.student_id,
                u.name as student_name,
                sp.roll_number,
                sp.department,
                ar.status,
                ar.record_date,
                ar.record_time
            FROM attendance_records ar
            JOIN student_profiles sp ON ar.student_id = sp.id
            JOIN users u ON sp.user_id = u.id
            WHERE ar.session_id = %s
            ORDER BY ar.status DESC, u.name ASC
        """, (session_id,))
        
        final_records = cursor.fetchall()
        
        # 6. Convert datetime objects to strings for JSON
        for record in final_records:
            if record.get('record_date'):
                record['record_date'] = record['record_date'].strftime('%Y-%m-%d') if isinstance(record['record_date'], date) else str(record['record_date'])
            if record.get('record_time'):
                record['record_time'] = record['record_time'].strftime('%H:%M:%S') if hasattr(record['record_time'], 'strftime') else str(record['record_time'])
        
        # 7. Separate Present and Absent lists
        present_students = [r for r in final_records if r['status'] == 'present']
        absent_students = [r for r in final_records if r['status'] == 'absent']
        
        cursor.close()
        conn.close()
        
        # 8. Return success with full data
        return jsonify({
            'success': True,
            'message': 'Attendance closed successfully!',
            'date': today.strftime('%A, %d-%m-%Y'),
            'total_present': present_count,
            'total_absent': absent_count,
            'total_students': len(students),
            'present_students': present_students,
            'absent_students': absent_students,
            'all_records': final_records,
            'session_id': session_id
        })
        
    except Exception as e:
        print(f"Close attendance error: {e}")
        return jsonify({'error': str(e)}), 500


@attendance_otp_bp.route('/mentor/force-close', methods=['POST'])
def force_close_attendance():
    """Force close ALL active attendance sessions"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    email = session.get('user_email', '')
    if not is_mentor(email):
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Get all active sessions
        cursor.execute("SELECT id FROM attendance_sessions WHERE status = 'active'")
        active_sessions = cursor.fetchall()
        
        if not active_sessions:
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'message': 'No active sessions found'})
        
        # Get all students
        students = StudentModel.get_all()
        today = date.today()
        current_time = datetime.now().time()
        
        closed_count = 0
        for session_item in active_sessions:
            # Get students who marked present
            cursor.execute("""
                SELECT student_id FROM attendance_records 
                WHERE session_id = %s AND status = 'present'
            """, (session_item['id'],))
            marked = cursor.fetchall()
            marked_ids = [m['student_id'] for m in marked]
            
            # Mark unmarked as absent
            for student in students:
                if student['id'] not in marked_ids:
                    cursor.execute("""
                        INSERT INTO attendance_records 
                        (student_id, session_id, status, record_date, record_time)
                        VALUES (%s, %s, 'absent', %s, %s)
                    """, (student['id'], session_item['id'], today, current_time))
            
            # Close session
            cursor.execute("""
                UPDATE attendance_sessions 
                SET status = 'closed', 
                    total_present = %s, 
                    total_absent = %s,
                    closed_at = NOW()
                WHERE id = %s
            """, (len(marked), len(students) - len(marked), session_item['id']))
            closed_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Closed {closed_count} active session(s)',
            'closed_count': closed_count
        })
        
    except Exception as e:
        print(f"Force close error: {e}")
        return jsonify({'error': str(e)}), 500


@attendance_otp_bp.route('/mentor/live/<int:session_id>')
def mentor_live_attendance(session_id):
    """Get live attendance data with date/time"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
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
        
        students = StudentModel.get_all()
        
        cursor.execute("""
            SELECT student_id, status
            FROM attendance_records 
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
            status = student_status.get(student['id'], 'waiting')
            if status == 'present':
                present_count += 1
            elif status == 'absent':
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
        print(f"Live attendance error: {e}")
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
            INSERT INTO attendance_records (session_id, student_id, status, record_date, record_time)
            VALUES (%s, %s, 'present', CURDATE(), CURTIME())
        """, (session_data['id'], student['id']))
        conn.commit()
        cursor.close()
        conn.close()
        
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
            'message': 'Attendance marked successfully!',
            'attendance_percentage': percentage,
            'date': datetime.now().strftime('%A, %d-%m-%Y'),
            'time': datetime.now().strftime('%H:%M:%S')
        })
        
    except Exception as e:
        print(f"Mark attendance error: {e}")
        return jsonify({'error': str(e)}), 500


@attendance_otp_bp.route('/student')
def student_attendance():
    """Student attendance marking page"""
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_student(email):
        flash('Access denied. Student only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    user_id = session.get('user_id')
    student = StudentModel.get_by_user_id(user_id)
    
    attendance_percentage = 0
    if student:
        from models.attendance_model import AttendanceModel
        attendance_percentage = AttendanceModel.get_attendance_percentage(student['id'])
    
    today_status = None
    if student:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT status
                FROM attendance_records 
                WHERE student_id = %s AND record_date = CURDATE()
                ORDER BY id DESC LIMIT 1
            """, (student['id'],))
            today_status = cursor.fetchone()
            cursor.close()
            conn.close()
    
    return render_template('student/student_attendance_otp.html',
                         name=session.get('user_name'),
                         attendance_percentage=attendance_percentage,
                         today_status=today_status,
                         today=datetime.now().strftime('%A, %d-%m-%Y'))


@attendance_otp_bp.route('/mentor/history')
def mentor_attendance_history():
    """Mentor view attendance history by date"""
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_mentor(email):
        flash('Access denied. Mentor only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    # Get date from query param, default to today
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed.', 'error')
        return redirect(url_for('mentor.mentor_dashboard'))
    
    cursor = conn.cursor(dictionary=True)
    
    # Get ALL students with their attendance status for the selected date
    cursor.execute("""
        SELECT 
            sp.id as student_id,
            u.name as student_name,
            sp.roll_number,
            sp.department,
            COALESCE(ar.status, 'not_marked') as status,
            ar.record_date,
            ar.record_time
        FROM student_profiles sp
        JOIN users u ON sp.user_id = u.id
        LEFT JOIN attendance_records ar ON sp.id = ar.student_id AND ar.record_date = %s
        ORDER BY 
            CASE 
                WHEN ar.status = 'present' THEN 1
                WHEN ar.status = 'absent' THEN 2
                ELSE 3
            END,
            u.name ASC
    """, (selected_date,))
    
    records = cursor.fetchall()
    
    # Convert datetime objects to strings for display
    for record in records:
        if record.get('record_date'):
            record['record_date'] = record['record_date'].strftime('%Y-%m-%d') if hasattr(record['record_date'], 'strftime') else str(record['record_date'])
        if record.get('record_time'):
            record['record_time'] = record['record_time'].strftime('%H:%M:%S') if hasattr(record['record_time'], 'strftime') else str(record['record_time'])
        if record.get('status') == 'not_marked':
            record['status_display'] = 'Not Marked'
        elif record.get('status') == 'present':
            record['status_display'] = 'Present'
        elif record.get('status') == 'absent':
            record['status_display'] = 'Absent'
        else:
            record['status_display'] = 'Unknown'
    
    total_students = len(records)
    present_count = len([r for r in records if r['status'] == 'present'])
    absent_count = len([r for r in records if r['status'] == 'absent'])
    not_marked_count = len([r for r in records if r['status'] == 'not_marked'])
    
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
@attendance_otp_bp.route('/admin/reports')
def admin_reports():
    """Admin view all attendance reports with date/time"""
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_admin(email):
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    try:
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed.', 'error')
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
                             stats=stats,
                             today=datetime.now().strftime('%A, %d-%m-%Y'))
                             
    except Exception as e:
        print(f"Admin reports error: {e}")
        flash('Error loading reports.', 'error')
        return redirect(url_for('admin.admin_dashboard'))