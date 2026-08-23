# ==========================================
# RISK CALCULATOR UTILITIES
# ==========================================

def calculate_risk_level(attendance, cgpa):
    """
    Calculate risk level based on attendance and CGPA
    
    Args:
        attendance: Attendance percentage (0-100)
        cgpa: CGPA (0-10)
    
    Returns:
        dict: Risk level and factors
    """
    risk_factors = []
    
    # Attendance risk
    if attendance < 75:
        risk_factors.append("Low attendance (<75%)")
        attendance_risk = True
    elif attendance < 85:
        risk_factors.append("Moderate attendance (75-85%)")
        attendance_risk = False
    else:
        attendance_risk = False
    
    # Grade risk
    if cgpa < 5.0:
        risk_factors.append("Very low CGPA (<5.0)")
        grade_risk = True
    elif cgpa < 6.0:
        risk_factors.append("Low CGPA (5.0-6.0)")
        grade_risk = True
    elif cgpa < 7.0:
        risk_factors.append("Moderate CGPA (6.0-7.0)")
        grade_risk = False
    else:
        grade_risk = False
    
    # Overall risk level
    if len(risk_factors) >= 2:
        risk_level = "high"
        risk_color = "🔴"
    elif len(risk_factors) == 1:
        risk_level = "medium"
        risk_color = "🟡"
    else:
        risk_level = "low"
        risk_color = "🟢"
    
    return {
        'level': risk_level,
        'color': risk_color,
        'factors': risk_factors if risk_factors else ["Good standing"],
        'attendance_risk': attendance_risk,
        'grade_risk': grade_risk
    }

def get_risk_color(risk_level):
    """Get color for risk level"""
    colors = {
        'high': '🔴',
        'medium': '🟡',
        'low': '🟢'
    }
    return colors.get(risk_level, '🟢')