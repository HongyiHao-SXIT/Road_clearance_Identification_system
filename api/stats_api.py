from flask import Blueprint, jsonify
from sqlalchemy import func
from database.models import DetectTask, DetectItem, Robot
from database.db import db
from datetime import datetime, timedelta

stats_bp = Blueprint("stats_bp", __name__)

@stats_bp.route("/summary")
def get_stats_summary():
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

        # 3. 近期捡拾数量趋势
        seven_days_ago = datetime.now() - timedelta(days=7)
        trend_counts = db.session.query(
            func.date(DetectTask.created_at).label('date'),
            func.count(DetectTask.id)
        ).filter(DetectTask.created_at >= seven_days_ago)\
         .group_by('date').order_by('date').all()
        
        line_data = {
            "labels": [str(row[0]) for row in trend_counts],
            "values": [row[1] for row in trend_counts]
        }

        # 4. 机器人状态与电量（动态评估 online/offline）
        robots = Robot.query.all()
        robot_list = []
        now = datetime.now()
        to_update = []
        TIMEOUT = 3
        for r in robots:
            resp_status = r.status
            if r.last_heartbeat:
                age = (now - r.last_heartbeat).total_seconds()
                if age > TIMEOUT:
                    resp_status = 'OFFLINE'
                    if r.status != 'OFFLINE':
                        r.status = 'OFFLINE'
                        to_update.append(r)
            else:
                resp_status = 'OFFLINE'
                if r.status != 'OFFLINE':
                    r.status = 'OFFLINE'
                    to_update.append(r)

            robot_list.append({
                "device_id": r.device_id,
                "name": r.name,
                "status": resp_status,
                "battery": getattr(r, 'battery', 75),
                "lat": getattr(r, 'current_lat', None),
                "lng": getattr(r, 'current_lng', None),
                "ip_address": r.ip_address,
                "last_heartbeat": (r.last_heartbeat.isoformat() if r.last_heartbeat else None)
            })

        if to_update:
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

        return jsonify({
            "ok": True,
            "locations": locations,
            "pie_data": pie_data,
            "line_data": line_data,
            "robot_list": robot_list
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})