from flask import Blueprint, jsonify
from sqlalchemy import func
from database.models import DetectTask, DetectItem
from database.db import db
import datetime

stats_bp = Blueprint("stats_bp", __name__)

@stats_bp.route("/summary")
def get_summary():
    try:
        tasks = DetectTask.query.filter(
            DetectTask.latitude.isnot(None), 
            DetectTask.longitude.isnot(None)
        ).all()

        locations = []
        for t in tasks:
            locations.append({
                "lat": t.latitude,
                "lng": t.longitude,
                "label": f"任务 #{t.id}: 发现 {len(t.items)} 处垃圾"
            })

        # 1. 饼图数据
        label_counts = db.session.query(
            DetectItem.label, func.count(DetectItem.id)
        ).group_by(DetectItem.label).all()
        pie_data = [{"name": row[0], "value": row[1]} for row in label_counts]

        # 2. 折线图数据
        seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        trend_counts = db.session.query(
            func.date(DetectTask.created_at).label('date'),
            func.count(DetectTask.id)
        ).filter(DetectTask.created_at >= seven_days_ago)\
         .group_by('date').order_by('date').all()

        line_data = {
            "labels": [str(row[0]) for row in trend_counts],
            "values": [row[1] for row in trend_counts]
        }

        return jsonify({
            "ok": True, 
            "pie_data": pie_data, 
            "line_data": line_data, 
            "locations": locations
        })
    except Exception as e:
        print(f"Stats Error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500