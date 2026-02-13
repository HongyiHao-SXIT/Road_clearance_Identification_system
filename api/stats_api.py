from flask import Blueprint, jsonify
from sqlalchemy import func
from database.models import DetectTask, DetectItem, Robot
from database.db import db
import datetime

stats_bp = Blueprint("stats_bp", __name__)

@stats_bp.route("/summary")
def get_summary():
    try:
        # 1. 垃圾分布地图点位
        tasks = DetectTask.query.filter(DetectTask.latitude.isnot(None)).all()
        locations = []
        for t in tasks:
            types = list(set([item.label for item in t.items]))
            locations.append({
                "id": t.id,
                "lat": t.latitude,
                "lng": t.longitude,
                "trash_types": ", ".join(types) if types else "未知"
            })

        # 2. 垃圾种类分布 (饼图)
        label_counts = db.session.query(
            DetectItem.label, func.count(DetectItem.id)
        ).group_by(DetectItem.label).all()
        pie_data = [{"name": row[0], "value": row[1]} for row in label_counts]

        # 3. 近期捡拾数量趋势 (折线图 - 最近7天)
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

        # 4. 机器人状态与电量 (列表 & 柱状图)
        robots = Robot.query.all()
        robot_list = []
        for r in robots:
            # 这里的 battery 字段需确保你在 models.py 的 Robot 类中已定义
            # 如果没有，可以使用随机数或默认值模拟：getattr(r, 'battery', 80)
            robot_list.append({
                "device_id": r.device_id,
                "name": r.name,
                "status": r.status,  # ONLINE / OFFLINE
                "battery": getattr(r, 'battery', 75) 
            })

        return jsonify({
            "ok": True,
            "locations": locations,
            "pie_data": pie_data,
            "line_data": line_data,
            "robot_list": robot_list
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})