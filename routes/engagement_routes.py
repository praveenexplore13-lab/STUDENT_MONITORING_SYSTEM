# ==========================================
# ENGAGEMENT ROUTES
# ==========================================

from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from models.engagement_model import EngagementModel
from models.student_model import StudentModel
from models.attendance_model import AttendanceModel
from utils.engagement_calculator import calculate_student_engagement, get_engagement_prediction

engagement_bp = Blueprint('engagement', __name__, url_prefix='/engagement')


@engagement_bp.route('/dashboard')
def engagement_dashboard():
    """Engagement analytics dashboard"""
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    user_id = session.get('user_id')
    student = StudentModel.get_by_user_id(user_id)
    
    if not student:
        flash('⚠️ Complete your profile first.', 'warning')
        return redirect(url_for('student.student_edit_profile'))
    
    # Calculate engagement
    engagement = calculate_student_engagement(student['id'])
    prediction = get_engagement_prediction(student['id'])
    
    return render_template('engagement/engagement_dashboard.html',
                         name=session.get('user_name'),
                         engagement=engagement,
                         prediction=prediction)


@engagement_bp.route('/leaderboard')
def engagement_leaderboard():
    """Engagement leaderboard"""
    if 'user_id' not in session:
        flash('⚠️ Please login first.', 'error')
        return redirect(url_for('auth.login'))
    
    scores = EngagementModel.get_all_engagement_scores()
    
    return render_template('engagement/leaderboard.html',
                         name=session.get('user_name'),
                         scores=scores)


@engagement_bp.route('/api/update/<int:student_id>', methods=['POST'])
def update_engagement_score(student_id):
    """Update engagement score for a student"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Recalculate engagement
    score = EngagementModel.calculate_engagement_score(student_id)
    EngagementModel.save_engagement_score(student_id, score)
    
    return jsonify({
        'success': True,
        'student_id': student_id,
        'score': score
    })


@engagement_bp.route('/api/all-scores')
def get_all_scores():
    """Get all engagement scores"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    scores = EngagementModel.get_all_engagement_scores()
    return jsonify({'scores': scores})