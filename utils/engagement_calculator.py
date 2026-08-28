# ==========================================
# ENGAGEMENT CALCULATOR
# ==========================================

from models.attendance_model import AttendanceModel
from models.student_model import StudentModel
from models.mentor_note_model import MentorNoteModel
from models.engagement_model import EngagementModel

def calculate_student_engagement(student_id):
    """Calculate full engagement analysis for a student"""
    
    # Get attendance
    attendance = AttendanceModel.get_attendance_percentage(student_id)
    
    # Get profile
    student = StudentModel.get_by_id(student_id)
    
    # Get notes
    notes = MentorNoteModel.get_by_student(student_id)
    
    # Calculate engagement score
    engagement_score = EngagementModel.calculate_engagement_score(student_id)
    engagement_level, engagement_text = EngagementModel.get_engagement_level(engagement_score)
    
    # Generate analysis
    analysis = {
        'score': engagement_score,
        'level': engagement_level,
        'level_text': engagement_text,
        'attendance': attendance,
        'notes_count': len(notes),
        'assignments': {
            'submitted': student.get('assignments_submitted', 0),
            'total': student.get('total_assignments', 0)
        },
        'recommendations': generate_recommendations(engagement_score, attendance, len(notes))
    }
    
    return analysis

def generate_recommendations(score, attendance, notes_count):
    """Generate personalized recommendations"""
    recommendations = []
    
    if score < 40:
        recommendations.append("🔴 **Urgent:** Schedule meeting with mentor immediately")
    if attendance < 75:
        recommendations.append("📚 **Improve Attendance:** Try to attend at least 75% of classes")
    if score < 60 and attendance < 75:
        recommendations.append("📝 **Study Plan:** Create a structured study schedule")
    if notes_count == 0:
        recommendations.append("📋 **Connect:** Schedule a counseling session with your mentor")
    if score >= 80:
        recommendations.append("🎉 **Excellent:** Keep up the great work!")
    
    if not recommendations:
        recommendations.append("📌 **Keep Going:** You're on the right track!")
    
    return recommendations

def get_engagement_prediction(student_id):
    """AI-based engagement prediction"""
    student = StudentModel.get_by_id(student_id)
    current_score = EngagementModel.calculate_engagement_score(student_id)
    
    # Simple prediction logic
    if current_score >= 80:
        prediction = "📈 **Trend:** High engagement likely to continue"
        risk = "low"
    elif current_score >= 60:
        prediction = "📊 **Trend:** Stable engagement, potential for growth"
        risk = "low"
    elif current_score >= 40:
        prediction = "⚠️ **Trend:** Declining engagement. Needs attention"
        risk = "medium"
    else:
        prediction = "🔴 **Alert:** Critical engagement level. Immediate intervention needed!"
        risk = "high"
    
    return {
        'current_score': current_score,
        'prediction': prediction,
        'risk': risk
    }