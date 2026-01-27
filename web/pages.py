from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from database.models import DetectTask, DetectItem

web_bp = Blueprint("web_bp", __name__)

@web_bp.route('/')
@login_required
def index():

    return render_template('index.html', username=current_user.username, role=current_user.role)

@web_bp.route('/upload')
@login_required
def upload():

    return render_template('upload.html', username=current_user.username, role=current_user.role)

@web_bp.route('/stats')
@login_required
def stats_page():

    return render_template('stats.html')

@web_bp.route("/result")
@login_required
def result():
    page = int(request.args.get("page", 1))
    pagination = DetectTask.query.order_by(DetectTask.id.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template("result.html", tasks=pagination.items, pagination=pagination)

@web_bp.route("/task")
@login_required
def task():
    task_id = request.args.get("task_id")

@web_bp.route("/forget")
def forget():
    return render_template("forget.html")