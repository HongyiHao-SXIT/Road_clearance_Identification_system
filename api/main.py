from flask import Blueprint, render_template
from flask_login import login_required, current_user

main_bp = Blueprint("main_bp", __name__)

@main_bp.route("/")
@login_required
def index():
    return render_template("index.html", username=current_user.username, role=current_user.role)
