from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from database.db import db
from database.models import DetectTask, DetectItem, OpsLog

web_bp = Blueprint("web_bp", __name__)

# 可用状态（页面下拉框用）
HANDLE_STATES = ["NEW", "CONFIRMED", "CLEANED", "IGNORED"]


@web_bp.route("/")
@login_required
def home():
    return redirect(url_for("web_bp.tasks"))


@web_bp.route("/tasks")
@login_required
def tasks():
    """
    检测任务列表
    支持简单筛选：status
    """
    status = request.args.get("status", "").strip()
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))

    q = DetectTask.query.order_by(DetectTask.id.desc())
    if status:
        q = q.filter(DetectTask.status == status)

    pagination = q.paginate(page=page, per_page=page_size, error_out=False)

    return render_template(
        "tasks.html",
        tasks=pagination.items,
        pagination=pagination,
        status=status
    )


@web_bp.route("/tasks/<int:task_id>")
@login_required
def task_detail(task_id: int):
    """
    某个任务详情 + 该任务下所有垃圾 item 管理
    """
    task = DetectTask.query.get_or_404(task_id)
    items = DetectItem.query.filter_by(task_id=task_id).order_by(DetectItem.id.desc()).all()

    return render_template(
        "task_detail.html",
        task=task,
        items=items,
        handle_states=HANDLE_STATES
    )


@web_bp.route("/items/<int:item_id>/update", methods=["POST"])
@login_required
def update_item(item_id: int):
    """
    更新垃圾条目状态：确认/清理/忽略/备注
    """
    item = DetectItem.query.get_or_404(item_id)

    # 来自表单
    handle_state = request.form.get("handle_state", "").strip()
    is_valid_raw = request.form.get("is_valid", "").strip()  # "", "1", "0"
    note = (request.form.get("note") or "").strip()

    if handle_state and handle_state not in HANDLE_STATES:
        flash("无效的 handle_state")
        return redirect(url_for("web_bp.task_detail", task_id=item.task_id))

    # 解析 is_valid
    is_valid = None
    if is_valid_raw == "1":
        is_valid = True
    elif is_valid_raw == "0":
        is_valid = False

    # 记录变更前状态（用于日志 detail）
    before = {
        "handle_state": item.handle_state,
        "is_valid": item.is_valid,
        "note": item.note,
    }

    # 应用更新
    if handle_state:
        item.handle_state = handle_state
    item.is_valid = is_valid
    item.note = note

    # 写操作日志
    after = {
        "handle_state": item.handle_state,
        "is_valid": item.is_valid,
        "note": item.note,
    }

    log = OpsLog(
        item_id=item.id,
        action="update_item",
        operator=getattr(current_user, "username", None),
        detail=f"before={before} after={after}"[:250]
    )
    db.session.add(log)
    db.session.commit()

    flash("更新成功")
    return redirect(url_for("web_bp.task_detail", task_id=item.task_id))
