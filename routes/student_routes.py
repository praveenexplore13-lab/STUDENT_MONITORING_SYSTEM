# ==========================================
# STUDENT ROUTES
# ==========================================

from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from utils.helpers import is_student
from models.student_model import StudentModel
from models.mentor_note_model import MentorNoteModel
from models.risk_flag_model import RiskFlagModel
from models.notification_model import NotificationModel
from models.user_model import UserModel
from utils.helpers import save_profile_image

student_bp = Blueprint('student', __name__, url_prefix='/student')


# ==========================================
# STUDENT DASHBOARD
# ==========================================

@student_bp.route('/dashboard')
def student_dashboard():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_student(email):
        flash('❌ Access denied. Student only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    user_id = session.get('user_id')
    student = StudentModel.get_by_user_id(user_id)
    
    # If no profile, show message to complete profile
    if not student:
        return render_template('student/student_dashboard.html',
                             name=session.get('user_name'),
                             student=None,
                             notes=[],
                             notifications=[])
    
    # Get risk info
    risk = RiskFlagModel.get_by_student(student['id'])
    if not risk:
        RiskFlagModel.save_risk_flags(student['id'])
        risk = RiskFlagModel.get_by_student(student['id'])
    student['risk'] = risk
    
    # Get mentor notes
    notes = MentorNoteModel.get_by_student(student['id'])
    
    # Get notifications
    notifications = NotificationModel.get_student_notifications(user_id)
    
    return render_template('student/student_dashboard.html',
                         name=session.get('user_name'),
                         student=student,
                         notes=notes,
                         notifications=notifications)


# ==========================================
# STUDENT - PROFILE (FIXED)
# ==========================================

@student_bp.route('/profile')
def student_profile():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_student(email):
        flash('❌ Access denied. Student only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    user_id = session.get('user_id')
    student = StudentModel.get_by_user_id(user_id)
    
    if not student:
        flash('⚠️ Please complete your profile first.', 'warning')
        return redirect(url_for('student.student_edit_profile'))
    
    # Get risk info
    try:
        risk = RiskFlagModel.get_by_student(student['id'])
        student['risk'] = risk
    except Exception as e:
        print(f"❌ Error getting risk: {e}")
        student['risk'] = None
    
    return render_template('student/student_profile.html',
                         name=session.get('user_name'),
                         student=student)


# ==========================================
# STUDENT - EDIT PROFILE (FIXED)
# ==========================================

@student_bp.route('/profile/edit', methods=['GET', 'POST'])
def student_edit_profile():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_student(email):
        flash('❌ Access denied. Student only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    user_id = session.get('user_id')
    student = StudentModel.get_by_user_id(user_id)
    
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
            'profile_image': student.get('profile_image') if student else None
        }
        
        # Handle image upload
        if 'profile_image' in request.files and request.files['profile_image'].filename:
            image_path = save_profile_image(request.files['profile_image'])
            if image_path:
                data['profile_image'] = image_path
        
        profile_id = StudentModel.create_or_update(user_id, data)
        
        if profile_id:
            # Calculate and save risk
            try:
                RiskFlagModel.save_risk_flags(profile_id)
            except Exception as e:
                print(f"❌ Error saving risk: {e}")
            flash('✅ Profile updated successfully!', 'success')
        else:
            flash('❌ Failed to update profile.', 'error')
        
        return redirect(url_for('student.student_profile'))
    
    return render_template('student/student_edit_profile.html',
                         name=session.get('user_name'),
                         student=student)


# ==========================================
# STUDENT - NOTES (FIXED)
# ==========================================

@student_bp.route('/notes')
def student_notes():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_student(email):
        flash('❌ Access denied. Student only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    user_id = session.get('user_id')
    student = StudentModel.get_by_user_id(user_id)
    
    if not student:
        flash('⚠️ Please complete your profile first.', 'warning')
        return redirect(url_for('student.student_edit_profile'))
    
    # Get mentor notes
    try:
        notes = MentorNoteModel.get_by_student(student['id'])
    except Exception as e:
        print(f"❌ Error getting notes: {e}")
        notes = []
    
    return render_template('student/student_notes.html',
                         name=session.get('user_name'),
                         notes=notes)


# ==========================================
# STUDENT - NOTIFICATIONS
# ==========================================

@student_bp.route('/notifications')
def student_notifications():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_student(email):
        flash('❌ Access denied. Student only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    user_id = session.get('user_id')
    
    try:
        notifications = NotificationModel.get_student_notifications(user_id)
    except Exception as e:
        print(f"❌ Error getting notifications: {e}")
        notifications = []
    
    return render_template('student/student_notifications.html',
                         name=session.get('user_name'),
                         notifications=notifications)


# ==========================================
# STUDENT - MARK NOTIFICATION READ
# ==========================================

@student_bp.route('/notification/read/<int:notification_id>')
def mark_notification_read(notification_id):
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_student(email):
        flash('❌ Access denied. Student only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    user_id = session.get('user_id')
    student = StudentModel.get_by_user_id(user_id)
    
    if student:
        try:
            NotificationModel.mark_read(student['id'], notification_id)
        except Exception as e:
            print(f"❌ Error marking notification read: {e}")
    
    return redirect(url_for('student.student_notifications'))

# ==========================================
# STUDENT - OD REQUEST
# ==========================================

from models.od_model import ODModel  # Add this import at top

@student_bp.route('/od/request', methods=['GET', 'POST'])
def student_od_request():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_student(email):
        flash('❌ Access denied. Student only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    user_id = session.get('user_id')
    student = StudentModel.get_by_user_id(user_id)
    
    if not student:
        flash('⚠️ Please complete your profile first.', 'warning')
        return redirect(url_for('student.student_edit_profile'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        od_date = request.form.get('od_date')
        
        if not title or not description or not od_date:
            flash('⚠️ Please fill all fields.', 'error')
            return redirect(url_for('student.student_od_request'))
        
        # Handle image upload
        proof_image = None
        if 'proof_image' in request.files and request.files['proof_image'].filename:
            from utils.file_utils import save_od_image
            proof_image = save_od_image(request.files['proof_image'])
        
        # Create request
        request_id = ODModel.create_request(student['id'], title, description, od_date, proof_image)
        
        if request_id:
            flash('✅ OD Request submitted successfully!', 'success')
            
            # Send email notification to Mentor
            from utils.email_utils import send_notification_email
            from models.user_model import UserModel
            from config import Config
            
            # Get mentor email
            mentor = UserModel.get_user_by_email(Config.MENTOR_EMAIL)
            if mentor:
                email_body = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                        .container {{ max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .header {{ background: #f59e0b; color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center; }}
                        .content {{ padding: 20px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header"><h2>📋 New OD Request</h2></div>
                        <div class="content">
                            <p><strong>Student:</strong> {session.get('user_name')}</p>
                            <p><strong>Title:</strong> {title}</p>
                            <p><strong>Description:</strong> {description}</p>
                            <p><strong>Date:</strong> {od_date}</p>
                            <p><a href="http://localhost:5000/mentor/od-requests" style="background: #6366f1; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none;">View Request</a></p>
                        </div>
                    </div>
                </body>
                </html>
                """
                send_notification_email('📋 New OD Request from Student', email_body, [Config.MENTOR_EMAIL])
        else:
            flash('❌ Failed to submit request.', 'error')
        
        return redirect(url_for('student.student_od_status'))
    
    return render_template('student/student_od_request.html',
                         name=session.get('user_name'),
                         student=student)


@student_bp.route('/od/status')
def student_od_status():
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_email', '')
    if not is_student(email):
        flash('❌ Access denied. Student only.', 'error')
        return redirect(url_for('auth.dashboard'))
    
    user_id = session.get('user_id')
    student = StudentModel.get_by_user_id(user_id)
    
    if not student:
        flash('⚠️ Please complete your profile first.', 'warning')
        return redirect(url_for('student.student_edit_profile'))
    
    requests = ODModel.get_by_student(student['id'])
    
    return render_template('student/student_od_status.html',
                         name=session.get('user_name'),
                         requests=requests)