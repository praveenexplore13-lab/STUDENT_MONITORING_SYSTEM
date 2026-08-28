from flask import Flask, redirect, url_for, session
from config import Config
from database import init_db
from routes.ai_tools_routes import ai_tools_bp

# Import all blueprints
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.mentor_routes import mentor_bp
from routes.student_routes import student_bp
from routes.chat_routes import chat_bp
from routes.search_routes import search_bp
from routes.attendance_routes import attendance_bp
from routes.engagement_routes import engagement_bp
from routes.attendance_otp_routes import attendance_otp_bp

# Create main app
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Initialize database
init_db()

# Register all blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(mentor_bp)
app.register_blueprint(student_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(search_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(engagement_bp)
app.register_blueprint(attendance_otp_bp)
app.register_blueprint(ai_tools_bp)

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("auth.dashboard"))
    return redirect(url_for("auth.login"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
