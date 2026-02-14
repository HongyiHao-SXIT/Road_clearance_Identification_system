from flask import Blueprint, render_template, request
from database.models import DetectTask, DetectItem
from database.db import db

web_bp = Blueprint("web_bp", __name__)

@web_bp.route('/')
def index():
    return render_template('index.html')

@web_bp.route('/upload')
def upload():
    return render_template('upload.html')

@web_bp.route('/stats')
def stats_page():
    return render_template('stats.html')

@web_bp.route("/result")
def result():
    page = int(request.args.get("page", 1))
    pagination = DetectTask.query.order_by(DetectTask.id.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    return render_template("result.html", tasks=pagination.items, pagination=pagination)

@web_bp.route('/result/<int:task_id>')
def result_detail(task_id):
    task = DetectTask.query.get_or_404(task_id)
    
    items = DetectItem.query.filter_by(task_id=task_id).all()
    
    return render_template('detail.html', task=task, items=items)

# forget/login/register pages removed

@web_bp.route('/robot')
def robot_admin():
    from database.models import Robot
    robots = Robot.query.all()
    return render_template('robot_admin.html', robots=robots)


@web_bp.route('/robot/<int:id>')
def robot_control(id):
    from database.models import Robot
    robot = Robot.query.get_or_404(id)
    return render_template('robot_control.html', robot=robot)