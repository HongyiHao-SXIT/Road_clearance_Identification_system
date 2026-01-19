import os
import uuid
from flask import Blueprint, current_app, request, jsonify

from database.db import db
from database.models import DetectTask, DetectItem
from inference.yolo_detector import YOLODetector

detect_bp = Blueprint("detect_bp", __name__)

ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _ensure_dirs():
    os.makedirs(current_app.config["UPLOAD_DIR"], exist_ok=True)
    os.makedirs(current_app.config["RESULT_DIR"], exist_ok=True)


def _allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename.lower())[1]
    return ext in ALLOWED_EXTS


def _bbox_area(x1, y1, x2, y2) -> int:
    w = max(0, x2 - x1)
    h = max(0, y2 - y1)
    return w * h


@detect_bp.route("/detect", methods=["POST"])
def detect_upload():
    """
    POST /api/detect
    form-data:
      - image: file
      - device_id: optional
      - location: optional
      - conf: optional (float)
    """
    _ensure_dirs()

    if "image" not in request.files:
        return jsonify({"ok": False, "error": "Missing file field 'image'"}), 400

    f = request.files["image"]
    if not f or not f.filename:
        return jsonify({"ok": False, "error": "Empty filename"}), 400

    if not _allowed_file(f.filename):
        return jsonify({"ok": False, "error": f"Unsupported file type. Allowed: {sorted(ALLOWED_EXTS)}"}), 400

    device_id = request.form.get("device_id")
    location = request.form.get("location")
    conf = request.form.get("conf", type=float)  # 可不传

    # 生成唯一文件名
    ext = os.path.splitext(f.filename)[1].lower()
    file_id = uuid.uuid4().hex
    save_name = f"{file_id}{ext}"

    # 物理路径
    abs_upload_path = os.path.join(current_app.config["UPLOAD_DIR"], save_name)

    # 数据库里建议存“相对路径”（方便迁移）
    rel_upload_path = os.path.join("static", "uploads", save_name).replace("\\", "/")

    # 保存文件
    f.save(abs_upload_path)

    # 先建 task（PENDING）
    task = DetectTask(
        source_type="image",
        source_path=rel_upload_path,
        result_path=None,
        device_id=device_id,
        location=location,
        status="PENDING",
        error_msg=None,
    )
    db.session.add(task)
    db.session.flush()  # 获取 task.id（不提交也能拿到）

    # 调检测器（有 best.pt 就 real，没有就 mock）
    # 这里不强依赖模型存在
    model_path = os.path.join(os.path.dirname(current_app.root_path), "Detection_system", "models", "best.pt")
    detector = YOLODetector(model_path=model_path if os.path.exists(model_path) else None)

    try:
        detections = detector.detect(abs_upload_path, conf=conf if conf else 0.25)

        items = []
        for d in detections:
            x1, y1, x2, y2 = d["bbox"]
            item = DetectItem(
                task_id=task.id,
                label=d["label"],
                confidence=float(d["confidence"]),
                x1=int(x1),
                y1=int(y1),
                x2=int(x2),
                y2=int(y2),
                area=_bbox_area(int(x1), int(y1), int(x2), int(y2)),
                is_valid=None,
                handle_state="NEW",
                note=None,
            )
            items.append(item)

        db.session.add_all(items)

        task.status = "DONE"
        db.session.commit()

        return jsonify({
            "ok": True,
            "task": task.to_dict(with_items=True),
        })

    except Exception as e:
        db.session.rollback()
        task.status = "FAILED"
        task.error_msg = str(e)[:500]
        db.session.add(task)
        db.session.commit()

        return jsonify({
            "ok": False,
            "error": str(e),
            "task_id": task.id,
        }), 500
