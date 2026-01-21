import os
import uuid
from datetime import datetime
from flask import Blueprint, current_app, request, jsonify
from database.db import db
from database.models import DetectTask, DetectItem
from inference.yolo_detector import YOLODetector

detect_bp = Blueprint("detect_bp", __name__)

def _ensure_dirs():
    upload_dir = current_app.config.get("UPLOAD_DIR", "static/uploads")
    result_dir = current_app.config.get("RESULT_DIR", "static/results")
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(result_dir, exist_ok=True)

@detect_bp.route("/detect", methods=["POST"])
def detect_upload():
    _ensure_dirs()
    
    f = request.files.get("image") or request.files.get("file")
    if not f:
        return jsonify({"ok": False, "message": "未收到文件"}), 400

    # 1. 处理文件名和路径
    ext = os.path.splitext(f.filename)[1].lower()
    save_name = f"{uuid.uuid4().hex}{ext}"
    
    # 原图路径 (uploads)
    original_abs_path = os.path.join(current_app.config["UPLOAD_DIR"], save_name)
    source_rel_path = f"static/uploads/{save_name}"
    
    # 结果图路径 (results)
    result_abs_path = os.path.join(current_app.config["RESULT_DIR"], save_name) # 修正拼写 jon -> join
    result_rel_path = f"static/results/{save_name}" # 修正缺失的 /

    # 保存上传的原图
    f.save(original_abs_path)

    # 2. 创建任务记录
    task = DetectTask(
        source_type="image", 
        source_path=source_rel_path,
        result_path=result_rel_path, # 修正重复字段和赋值逻辑
        status="PENDING",
        created_at=datetime.now()
    )
    db.session.add(task)
    db.session.commit()

    try:
        # 3. 初始化检测器
        project_root = os.path.dirname(current_app.root_path)
        model_path = os.path.join(project_root, "best.pt")
        detector = YOLODetector(model_path=model_path if os.path.exists(model_path) else None)

        # 执行推理并保存带框图片
        detections = detector.detect(original_abs_path, save_result=True, result_path=result_abs_path)
        
        result_list = []
        for d in detections:
            item = DetectItem(
                task_id=task.id,
                label=d["label"],
                confidence=float(d["confidence"]),
                x1=int(d["bbox"][0]), y1=int(d["bbox"][1]), 
                x2=int(d["bbox"][2]), y2=int(d["bbox"][3]),
                area=int((d["bbox"][2]-d["bbox"][0])*(d["bbox"][3]-d["bbox"][1])),
                handle_state='NEW'
            )
            db.session.add(item)
            
            # 为了前端显示列表，构造数据
            result_list.append({
                "class_name": d["label"],
                "confidence": f"{d['confidence']*100:.2f}%",
                "bbox": [int(x1) for x1 in d["bbox"]]
            })
        
        task.status = "DONE"
        db.session.commit()

        # 4. 返回结果
        return jsonify({
            "ok": True,
            "status": "success",
            "result": result_list,
            "annotated_image_path": result_rel_path,
            "task": task.to_dict() if hasattr(task, 'to_dict') else {"id": task.id}
        })

    except Exception as e:
        db.session.rollback()
        print(f"!!! 后端错误详情: {str(e)}")
        return jsonify({"ok": False, "message": str(e)}), 500