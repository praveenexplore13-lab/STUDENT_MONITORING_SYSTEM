from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from utils.helpers import is_admin
from models.student_model import StudentModel
from models.mentor_note_model import MentorNoteModel
from models.risk_flag_model import RiskFlagModel
from models.notification_model import NotificationModel
from models.user_model import UserModel
from utils.email_utils import send_notification_email, format_notification_email
from utils.helpers import get_student_emails, save_profile_image
from utils.voice_utils import get_voice_welcome
from database import get_db_connection

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
def admin_dashboard():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_admin(email):
        flash('❌ Access denied. Admin only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    students = StudentModel.get_all()
    
    for student in students:
        risk = RiskFlagModel.get_by_student(student['id'])
        if not risk:
            RiskFlagModel.save_risk_flags(student['id'])
            risk = RiskFlagModel.get_by_student(student['id'])
        student['risk'] = risk
    
    voice_message = get_voice_welcome('admin')
    
    return render_template('admin/admin_dashboard.html',
                         name=session.get('user_name'),
                         students=students,
                         voice_message=voice_message)


@admin_bp.route('/students')
def admin_students():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_admin(email):
        flash('❌ Access denied. Admin only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    students = StudentModel.get_all()
    
    for student in students:
        risk = RiskFlagModel.get_by_student(student['id'])
        if risk:
            student['risk_level'] = risk.get('risk_level', 'low')
        else:
            student['risk_level'] = 'low'
    
    return render_template('admin/admin_students.html',
                         name=session.get('user_name'),
                         students=students)


@admin_bp.route('/student/<int:student_id>')
def admin_student_detail(student_id):
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_admin(email):
        flash('❌ Access denied. Admin only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    student = StudentModel.get_by_id(student_id)
    if not student:
        flash('❌ Student not found.', 'error')
        return redirect(url_for('admin.admin_students'))
    
    user = UserModel.get_user_by_id(student['user_id'])
    if user:
        student['name'] = user.get('name')
        student['email'] = user.get('email')
    
    risk = RiskFlagModel.get_by_student(student_id)
    if not risk:
        RiskFlagModel.save_risk_flags(student_id)
        risk = RiskFlagModel.get_by_student(student_id)
    student['risk'] = risk
    
    notes = MentorNoteModel.get_by_student(student_id)
    
    return render_template('admin/admin_student_detail.html',
                         name=session.get('user_name'),
                         student=student,
                         notes=notes)


@admin_bp.route('/student/edit/<int:student_id>', methods=['GET', 'POST'])
def admin_edit_student(student_id):
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_admin(email):
        flash('❌ Access denied. Admin only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    student = StudentModel.get_by_id(student_id)
    if not student:
        flash('❌ Student not found.', 'error')
        return redirect(url_for('admin.admin_students'))
    
    if request.method == 'POST':
        data = {
            'roll_number': request.form.get('roll_number'),
            'department': request.form.get('department'),
            'year': request.form.get('year'),
            'semester': request.form.get('semester'),
            'cgpa': request.form.get('cgpa'),
            'attendance_percentage': request.form.get('attendance_percentage'),
            'internal_marks': request.form.get('internal_marks'),
            'assignments_submitted': request.form.get('assignments_submitted'),
            'total_assignments': request.form.get('total_assignments'),
            'disciplinary_notes': request.form.get('disciplinary_notes'),
            'extracurricular': request.form.get('extracurricular'),
            'profile_image': student.get('profile_image')
        }
        
        if 'profile_image' in request.files and request.files['profile_image'].filename:
            image_path = save_profile_image(request.files['profile_image'])
            if image_path:
                data['profile_image'] = image_path
        
        StudentModel.create_or_update(student['user_id'], data)
        RiskFlagModel.save_risk_flags(student_id)
        
        flash('✅ Student updated successfully!', 'success')
        return redirect(url_for('admin.admin_student_detail', student_id=student_id))
    
    return render_template('admin/admin_edit_student.html',
                         name=session.get('user_name'),
                         student=student)


@admin_bp.route('/student/delete/<int:student_id>', methods=['POST'])
def admin_delete_student(student_id):
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_admin(email):
        flash('❌ Access denied. Admin only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    if StudentModel.delete(student_id):
        flash('✅ Student deleted successfully!', 'success')
    else:
        flash('❌ Failed to delete student.', 'error')
    
    return redirect(url_for('admin.admin_students'))


# ==========================================
# ADMIN - DELETE MENTOR NOTE
# ==========================================

@admin_bp.route('/mentor/note/delete/<int:note_id>', methods=['POST'])
def admin_delete_mentor_note(note_id):
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_admin(email):
        flash('❌ Access denied. Admin only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    conn = get_db_connection()
    if not conn:
        flash('❌ Database connection failed.', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    
    cursor = conn.cursor(dictionary=True)
    
    # Get student_id before deleting
    cursor.execute("SELECT student_id FROM mentor_notes WHERE id = %s", (note_id,))
    note = cursor.fetchone()
    
    if not note:
        cursor.close()
        conn.close()
        flash('❌ Note not found.', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    
    student_id = note['student_id']
    
    # Delete the note
    cursor.execute("DELETE FROM mentor_notes WHERE id = %s", (note_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('✅ Note deleted successfully!', 'success')
    return redirect(url_for('admin.admin_student_detail', student_id=student_id))


@admin_bp.route('/reports')
def admin_reports():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_admin(email):
        flash('❌ Access denied. Admin only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    students = StudentModel.get_all()
    
    total_students = len(students)
    high_risk = 0
    medium_risk = 0
    low_risk = 0
    avg_attendance = 0
    avg_cgpa = 0
    
    for student in students:
        risk = RiskFlagModel.get_by_student(student['id'])
        if risk:
            if risk.get('risk_level') == 'high':
                high_risk += 1
            elif risk.get('risk_level') == 'medium':
                medium_risk += 1
            else:
                low_risk += 1
        
        avg_attendance += float(student.get('attendance_percentage', 0) or 0)
        avg_cgpa += float(student.get('cgpa', 0) or 0)
    
    if total_students > 0:
        avg_attendance = round(avg_attendance / total_students, 2)
        avg_cgpa = round(avg_cgpa / total_students, 2)
    
    stats = {
        'total': total_students,
        'high_risk': high_risk,
        'medium_risk': medium_risk,
        'low_risk': low_risk,
        'avg_attendance': avg_attendance,
        'avg_cgpa': avg_cgpa
    }
    
    return render_template('admin/admin_reports.html',
                         name=session.get('user_name'),
                         stats=stats)


@admin_bp.route('/notifications', methods=['GET', 'POST'])
def admin_notifications():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_admin(email):
        flash('❌ Access denied. Admin only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        if not subject or not message:
            flash('⚠️ Please fill all fields.', 'error')
            return redirect(url_for('admin.admin_notifications'))
        
        notification_id = NotificationModel.create_notification(
            session['user_id'], 'admin', subject, message
        )
        
        if notification_id:
            student_emails = get_student_emails()
            
            if student_emails:
                email_body = format_notification_email(
                    subject, message, session.get('user_name'), 'Admin'
                )
                send_notification_email(subject, email_body, student_emails)
                
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor()
                    for student in student_emails:
                        cursor.execute("""
                            SELECT sp.id FROM student_profiles sp
                            JOIN users u ON sp.user_id = u.id
                            WHERE u.email = %s
                        """, (student,))
                        profile = cursor.fetchone()
                        if profile:
                            cursor.execute("""
                                INSERT INTO student_notifications (notification_id, student_id)
                                VALUES (%s, %s)
                            """, (notification_id, profile[0]))
                    conn.commit()
                    cursor.close()
                    conn.close()
                
                flash(f'✅ Notification sent to {len(student_emails)} students!', 'success')
            else:
                flash('⚠️ No students found to send notification.', 'warning')
        else:
            flash('❌ Failed to create notification.', 'error')
        
        return redirect(url_for('admin.admin_notifications'))
    
    notifications = NotificationModel.get_all_notifications()
    
    return render_template('admin/admin_notifications.html',
                         name=session.get('user_name'),
                         notifications=notifications)


# ==========================================
# ADMIN - DELETE NOTIFICATION
# ==========================================

@admin_bp.route('/notification/delete/<int:notification_id>', methods=['POST'])
def admin_delete_notification(notification_id):
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_admin(email):
        flash('❌ Access denied. Admin only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    conn = get_db_connection()
    if not conn:
        flash('❌ Database connection failed.', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    
    cursor = conn.cursor()
    
    # Delete notification (cascade will delete student_notifications)
    cursor.execute("DELETE FROM notifications WHERE id = %s", (notification_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('✅ Notification deleted successfully!', 'success')
    return redirect(url_for('admin.admin_notifications'))


@admin_bp.route('/profile')
def admin_profile():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_admin(email):
        flash('❌ Access denied. Admin only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    return render_template('admin/admin_profile.html',
                         name=session.get('user_name'),
                         email=session.get('user_email'))

# ==========================================
# ADMIN - OD REQUESTS
# ==========================================

from models.od_model import ODModel  # Add this import at top

@admin_bp.route('/od-requests')
def admin_od_requests():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_admin(email):
        flash('❌ Access denied. Admin only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    requests = ODModel.get_all_pending()
    
    return render_template('admin/admin_od_requests.html',
                         name=session.get('user_name'),
                         requests=requests)


@admin_bp.route('/od-request/<int:request_id>', methods=['GET', 'POST'])
def admin_od_detail(request_id):
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_admin(email):
        flash('❌ Access denied. Admin only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    od_request = ODModel.get_by_id(request_id)
    if not od_request:
        flash('❌ Request not found.', 'error')
        return redirect(url_for('admin.admin_od_requests'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        comment = request.form.get('comment')
        
        if action == 'approve':
            ODModel.approve_admin(request_id, comment)
            flash('✅ OD Request finally approved!', 'success')
            
            # Send email to student
            from utils.email_utils import send_notification_email
            from models.user_model import UserModel
            
            student_user = UserModel.get_user_by_id(od_request['user_id'])
            if student_user:
                email_body = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                        .container {{ max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .header {{ background: #10b981; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                        .content {{ padding: 20px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header"><h2>✅ OD Request FINALLY Approved!</h2></div>
                        <div class="content">
                            <p><strong>Congratulations! Your OD Request has been FINALLY approved!</strong></p>
                            <p><strong>Title:</strong> {od_request['title']}</p>
                            <p><strong>Admin Comment:</strong> {comment or 'No comment'}</p>
                            <p>You are now granted OD permission. Enjoy your event! 🎉</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                send_notification_email('✅ OD Request Approved - Final', email_body, [student_user['email']])
                
        elif action == 'deny':
            ODModel.deny_admin(request_id, comment)
            flash('❌ OD Request finally denied.', 'error')
            
            # Send email to student
            from utils.email_utils import send_notification_email
            from models.user_model import UserModel
            
            student_user = UserModel.get_user_by_id(od_request['user_id'])
            if student_user:
                email_body = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                        .container {{ max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .header {{ background: #ef4444; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                        .content {{ padding: 20px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header"><h2>❌ OD Request Finally Denied</h2></div>
                        <div class="content">
                            <p><strong>Your OD Request has been finally denied.</strong></p>
                            <p><strong>Title:</strong> {od_request['title']}</p>
                            <p><strong>Admin Comment:</strong> {comment or 'No comment'}</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                send_notification_email('❌ OD Request Denied - Final', email_body, [student_user['email']])
        
        return redirect(url_for('admin.admin_od_requests'))
    
    return render_template('admin/admin_od_detail.html',
                         name=session.get('user_name'),
                         request=od_request)