# ==========================================
# VOICE WELCOME UTILITIES
# ==========================================

def get_voice_welcome(role, name=None):
    """
    Get voice welcome message based on role
    
    Args:
        role: 'admin', 'mentor', or 'student'
        name: Student name (only for student role)
    
    Returns:
        str: Welcome message to speak
    """
    if role == 'admin':
        return "Welcome to Admin Page"
    elif role == 'mentor':
        return "Welcome to Mentor Page"
    elif role == 'student' and name:
        return f"Welcome back, {name}"
    else:
        return "Welcome"