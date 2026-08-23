# ==========================================
# GLOBAL SEARCH ROUTES
# ==========================================

from flask import Blueprint, render_template, session, request, jsonify, redirect, url_for
from models.student_model import StudentModel
from models.user_model import UserModel
from models.mentor_note_model import MentorNoteModel

search_bp = Blueprint('search', __name__, url_prefix='/search')


@search_bp.route('/')
def search_page():
    """Search page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    query = request.args.get('q', '').strip()
    results = []
    
    if query:
        # Search in students
        students = StudentModel.get_all()
        for student in students:
            if (query.lower() in student.get('name', '').lower() or
                query.lower() in student.get('roll_number', '').lower() or
                query.lower() in student.get('department', '').lower() or
                query.lower() in student.get('email', '').lower()):
                results.append({
                    'type': 'student',
                    'id': student.get('id'),
                    'name': student.get('name'),
                    'roll_number': student.get('roll_number'),
                    'department': student.get('department'),
                    'email': student.get('email')
                })
        
        # Search in mentor notes
        notes = MentorNoteModel.get_all()
        for note in notes:
            if query.lower() in note.get('note', '').lower():
                results.append({
                    'type': 'note',
                    'id': note.get('id'),
                    'student_name': note.get('student_name') or 'Unknown',
                    'mentor_name': note.get('mentor_name') or 'Unknown',
                    'note': note.get('note'),
                    'date': note.get('note_date')
                })
    
    return render_template('search_results.html',
                         name=session.get('user_name'),
                         query=query,
                         results=results)


@search_bp.route('/api')
def search_api():
    """API endpoint for live search"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    query = request.args.get('q', '').strip()
    results = []
    
    if query:
        students = StudentModel.get_all()
        for student in students:
            if (query.lower() in student.get('name', '').lower() or
                query.lower() in student.get('roll_number', '').lower()):
                results.append({
                    'id': student.get('id'),
                    'name': student.get('name'),
                    'roll_number': student.get('roll_number'),
                    'department': student.get('department'),
                    'type': 'student'
                })
    
    return jsonify({'results': results[:10]})