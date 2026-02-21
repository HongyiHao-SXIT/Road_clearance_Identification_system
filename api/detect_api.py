import os
import uuid
import requests
import logging
from datetime import datetime
from flask import Blueprint, current_app, request, jsonify
from database.db import db
from database.models import DetectTask, DetectItem
from inference.yolo_detector import YOLODetector

detect_bp = Blueprint("detect_bp", __name__)
logger = logging.getLogger(__name__)

def _ensure_dirs():
    upload_dir = current_app.config.get("UPLOAD_DIR", "static/uploads")
    result_dir = current_app.config.get("RESULT_DIR", "static/results")
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(result_dir, exist_ok=True)

@detect_bp.route("/detect", methods=["POST"])
def run_detection():
    _ensure_dirs()
    
    lat = request.form.get("latitude")
    lng = request.form.get("longitude")

    f = request.files.get("image") or request.files.get("file")

    address_str = "未知地点"
    if lat and lng:
        address_str = resolve_address_from_coords(lat, lng)

    if not f:
        return jsonify({"ok": False, "message": "未收到文件"}), 400

    ext = os.path.splitext(f.filename)[1].lower()
    save_name = f"{uuid.uuid4().hex}{ext}"
    

    original_abs_path = os.path.join(current_app.config["UPLOAD_DIR"], save_name)
    source_rel_path = f"static/uploads/{save_name}"
    
    result_abs_path = os.path.join(current_app.config["RESULT_DIR"], save_name)
    result_rel_path = f"static/results/{save_name}"

    f.save(original_abs_path)


    task = DetectTask(
        source_type="image", 
        source_path=source_rel_path,
        result_path=result_rel_path,
        status="PENDING",
        latitude=float(lat) if lat else None,
        longitude=float(lng) if lng else None,
        location=address_str,
        created_at=datetime.now()
    )
    db.session.add(task)
    db.session.commit()

    try:
        project_root = os.path.dirname(current_app.root_path)
        model_path = os.path.join(project_root, "best.pt")
        detector = YOLODetector(model_path=model_path if os.path.exists(model_path) else None)

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
            
            result_list.append({
                "class_name": d["label"],
                "confidence": f"{d['confidence']*100:.2f}%",
                "bbox": [int(x1) for x1 in d["bbox"]]
            })
        
        task.status = "DONE"
        db.session.commit()

        return jsonify({
            "ok": True,
            "status": "success",
            "result": result_list,
            "annotated_image_path": result_rel_path,
            "task": task.to_dict() if hasattr(task, 'to_dict') else {"id": task.id}
        })

    except Exception as e:
        db.session.rollback()
        logger.exception("检测处理失败")
        return jsonify({"ok": False, "message": str(e)}), 500
    
def resolve_address_from_coords(lat, lng):
    if not lat or not lng:
        return "未知地点"
    
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&zoom=10&addressdetails=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; DetectApp/1.0; +http://yourdomain.com/)"
        }

        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            address = data.get("display_name", "未知地点")
            return address
        else:
            return f"坐标： {lat}, {lng} (无法解析地址)"
        
    except Exception as e:
        logger.exception("地址解析失败")
        return f"坐标： {lat}, {lng} (解析地址失败)"
