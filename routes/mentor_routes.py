# ==========================================
# MENTOR ROUTES
# ==========================================

from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from utils.helpers import is_mentor, get_role
from models.student_model import StudentModel
from models.mentor_note_model import MentorNoteModel
from models.risk_flag_model import RiskFlagModel
from models.notification_model import NotificationModel
from models.user_model import UserModel
from utils.email_utils import send_notification_email, format_notification_email
from utils.helpers import get_student_emails, save_profile_image
from utils.voice_utils import get_voice_welcome
from database import get_db_connection
import datetime

mentor_bp = Blueprint('mentor', __name__, url_prefix='/mentor')


# ==========================================
# MENTOR DASHBOARD
# ==========================================

@mentor_bp.route('/dashboard')
def mentor_dashboard():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_mentor(email):
        flash('❌ Access denied. Mentor only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    students = StudentModel.get_all()
    
    for student in students:
        risk = RiskFlagModel.get_by_student(student['id'])
        if not risk:
            RiskFlagModel.save_risk_flags(student['id'])
            risk = RiskFlagModel.get_by_student(student['id'])
        student['risk'] = risk
    
    voice_message = get_voice_welcome('mentor')
    
    return render_template('mentor/mentor_dashboard.html',
                         name=session.get('user_name'),
                         students=students,
                         voice_message=voice_message)


# ==========================================
# MENTOR - VIEW ALL STUDENTS
# ==========================================

@mentor_bp.route('/students')
def mentor_students():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_mentor(email):
        flash('❌ Access denied. Mentor only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    students = StudentModel.get_all()
    
    for student in students:
        risk = RiskFlagModel.get_by_student(student['id'])
        if risk:
            student['risk_level'] = risk.get('risk_level', 'low')
        else:
            student['risk_level'] = 'low'
    
    return render_template('mentor/mentor_students.html',
                         name=session.get('user_name'),
                         students=students)


# ==========================================
# MENTOR - VIEW STUDENT DETAIL
# ==========================================

@mentor_bp.route('/student/<int:student_id>')
def mentor_student_detail(student_id):
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_mentor(email):
        flash('❌ Access denied. Mentor only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    student = StudentModel.get_by_id(student_id)
    if not student:
        flash('❌ Student not found.', 'error')
        return redirect(url_for('mentor.mentor_students'))
    
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
    
    return render_template('mentor/mentor_student_detail.html',
                         name=session.get('user_name'),
                         student=student,
                         notes=notes)


# ==========================================
# MENTOR - EDIT STUDENT
# ==========================================

@mentor_bp.route('/student/edit/<int:student_id>', methods=['GET', 'POST'])
def mentor_edit_student(student_id):
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_mentor(email):
        flash('❌ Access denied. Mentor only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    student = StudentModel.get_by_id(student_id)
    if not student:
        flash('❌ Student not found.', 'error')
        return redirect(url_for('mentor.mentor_students'))
    
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
        return redirect(url_for('mentor.mentor_student_detail', student_id=student_id))
    
    return render_template('mentor/mentor_edit_student.html',
                         name=session.get('user_name'),
                         student=student)


# ==========================================
# MENTOR - ADD NOTE (WITH EMAIL)
# ==========================================

@mentor_bp.route('/student/note/<int:student_id>', methods=['GET', 'POST'])
def mentor_add_note(student_id):
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_mentor(email):
        flash('❌ Access denied. Mentor only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    student = StudentModel.get_by_id(student_id)
    if not student:
        flash('❌ Student not found.', 'error')
        return redirect(url_for('mentor.mentor_students'))
    
    # Get student user info
    user = UserModel.get_user_by_id(student['user_id'])
    if user:
        student['name'] = user.get('name')
        student['email'] = user.get('email')
    
    if request.method == 'POST':
        note = request.form.get('note')
        note_date = request.form.get('note_date')
        
        if not note:
            flash('⚠️ Please enter a note.', 'error')
            return redirect(url_for('mentor.mentor_add_note', student_id=student_id))
        
        # Add note to database
        if MentorNoteModel.add_note(student_id, session['user_id'], note, note_date):
            flash('✅ Note added successfully!', 'success')
            
            # ==========================================
            # SEND EMAIL TO STUDENT
            # ==========================================
            try:
                # Get mentor name
                mentor = UserModel.get_user_by_id(session['user_id'])
                mentor_name = mentor.get('name') if mentor else session.get('user_name')
                
                # Format email
                email_subject = f"📝 New Counseling Note from {mentor_name}"
                email_body = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                        .container {{ max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .header {{ background: #6366f1; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                        .content {{ padding: 20px; }}
                        .footer {{ margin-top: 20px; color: #666; font-size: 12px; text-align: center; border-top: 1px solid #eee; padding-top: 20px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>📝 New Counseling Note</h2>
                        </div>
                        <div class="content">
                            <p><strong>Dear {student['name']},</strong></p>
                            <p>Your mentor <strong>{mentor_name}</strong> has added a new counseling note for you.</p>
                            <hr>
                            <p><strong>Note:</strong></p>
                            <p style="background: #f8fafc; padding: 15px; border-radius: 8px;">{note}</p>
                            <p><small>Date: {note_date or 'Today'}</small></p>
                            <hr>
                            <p><small>This is an automated notification from the Student Monitoring System.</small></p>
                        </div>
                        <div class="footer">
                            <p>© 2026 Student Monitoring System</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                # Send email to student
                if student.get('email'):
                    send_notification_email(email_subject, email_body, [student['email']])
                    print(f"✅ Note email sent to {student['name']} ({student['email']})")
                else:
                    print(f"⚠️ No email for student {student['name']}")
                
            except Exception as e:
                print(f"❌ Failed to send note email: {e}")
                # Don't flash error here - note was saved successfully
        else:
            flash('❌ Failed to add note.', 'error')
        
        return redirect(url_for('mentor.mentor_student_detail', student_id=student_id))
    
    return render_template('mentor/mentor_add_note.html',
                         name=session.get('user_name'),
                         student=student)


# ==========================================
# MENTOR - DELETE NOTE (OWN ONLY)
# ==========================================

@mentor_bp.route('/student/note/delete/<int:note_id>', methods=['POST'])
def mentor_delete_note(note_id):
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_mentor(email):
        flash('❌ Access denied. Mentor only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    conn = get_db_connection()
    if not conn:
        flash('❌ Database connection failed.', 'error')
        return redirect(url_for('mentor.mentor_dashboard'))
    
    cursor = conn.cursor(dictionary=True)
    
    # Check if note exists and belongs to this mentor
    cursor.execute("SELECT student_id, mentor_id FROM mentor_notes WHERE id = %s", (note_id,))
    note = cursor.fetchone()
    
    if not note:
        cursor.close()
        conn.close()
        flash('❌ Note not found.', 'error')
        return redirect(url_for('mentor.mentor_dashboard'))
    
    # Only allow mentor to delete their own notes
    if note['mentor_id'] != session['user_id']:
        cursor.close()
        conn.close()
        flash('❌ You can only delete your own notes.', 'error')
        return redirect(url_for('mentor.mentor_student_detail', student_id=note['student_id']))
    
    # Delete the note
    cursor.execute("DELETE FROM mentor_notes WHERE id = %s", (note_id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('✅ Note deleted successfully!', 'success')
    return redirect(url_for('mentor.mentor_student_detail', student_id=note['student_id']))


# ==========================================
# MENTOR - NOTIFICATIONS
# ==========================================

@mentor_bp.route('/notifications', methods=['GET', 'POST'])
def mentor_notifications():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_mentor(email):
        flash('❌ Access denied. Mentor only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        if not subject or not message:
            flash('⚠️ Please fill all fields.', 'error')
            return redirect(url_for('mentor.mentor_notifications'))
        
        notification_id = NotificationModel.create_notification(
            session['user_id'], 'mentor', subject, message
        )
        
        if notification_id:
            student_emails = get_student_emails()
            
            if student_emails:
                email_body = format_notification_email(
                    subject, message, session.get('user_name'), 'Mentor'
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
                flash('⚠️ No students found.', 'warning')
        else:
            flash('❌ Failed to create notification.', 'error')
        
        return redirect(url_for('mentor.mentor_notifications'))
    
    notifications = NotificationModel.get_all_notifications()
    
    return render_template('mentor/mentor_notifications.html',
                         name=session.get('user_name'),
                         notifications=notifications)


# ==========================================
# MENTOR - PROFILE
# ==========================================

@mentor_bp.route('/profile')
def mentor_profile():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_mentor(email):
        flash('❌ Access denied. Mentor only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    return render_template('mentor/mentor_profile.html',
                         name=session.get('user_name'),
                         email=session.get('user_email'))

# ==========================================
# MENTOR - OD REQUESTS
# ==========================================

from models.od_model import ODModel  # Add this import at top

@mentor_bp.route('/od-requests')
def mentor_od_requests():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_mentor(email):
        flash('❌ Access denied. Mentor only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    requests = ODModel.get_all_mentor_pending()
    
    return render_template('mentor/mentor_od_requests.html',
                         name=session.get('user_name'),
                         requests=requests)


@mentor_bp.route('/od-request/<int:request_id>', methods=['GET', 'POST'])
def mentor_od_detail(request_id):
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_mentor(email):
        flash('❌ Access denied. Mentor only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    od_request = ODModel.get_by_id(request_id)
    if not od_request:
        flash('❌ Request not found.', 'error')
        return redirect(url_for('mentor.mentor_od_requests'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        comment = request.form.get('comment')
        
        if action == 'approve':
            ODModel.approve_mentor(request_id, comment)
            flash('✅ OD Request approved!', 'success')
            
            # Send email to student
            from utils.email_utils import send_notification_email
            from models.user_model import UserModel
            from config import Config
            
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
                        <div class="header"><h2>✅ OD Request Approved by Mentor</h2></div>
                        <div class="content">
                            <p><strong>Your OD Request has been approved by the Mentor!</strong></p>
                            <p><strong>Title:</strong> {od_request['title']}</p>
                            <p><strong>Comment:</strong> {comment or 'No comment'}</p>
                            <p><em>Waiting for Admin approval...</em></p>
                        </div>
                    </div>
                </body>
                </html>
                """
                send_notification_email('✅ OD Request Approved by Mentor', email_body, [student_user['email']])
                
        elif action == 'deny':
            ODModel.deny_mentor(request_id, comment)
            flash('❌ OD Request denied.', 'error')
            
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
                        <div class="header"><h2>❌ OD Request Denied by Mentor</h2></div>
                        <div class="content">
                            <p><strong>Your OD Request has been denied by the Mentor.</strong></p>
                            <p><strong>Title:</strong> {od_request['title']}</p>
                            <p><strong>Comment:</strong> {comment or 'No comment'}</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                send_notification_email('❌ OD Request Denied by Mentor', email_body, [student_user['email']])
        
        return redirect(url_for('mentor.mentor_od_requests'))
    
    return render_template('mentor/mentor_od_detail.html',
                         name=session.get('user_name'),
                         request=od_request)