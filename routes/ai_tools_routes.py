from flask import Blueprint, render_template

ai_tools_bp = Blueprint("ai_tools", __name__)


@ai_tools_bp.route("/student/ai-tools")
def ai_tools():
    return render_template("student/ai_tools.html")