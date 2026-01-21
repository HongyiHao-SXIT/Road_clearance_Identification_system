from flask import Blueprint, jsonify
from sqlalchemy import func
from database.models import DetectTask, DetectItem
from database.db import db
import datetime

# 注意：如果在 app.py 注册时用了 url_prefix="/api/stats"
# 那么这里的 route 只需要写 "/summary"
stats_bp = Blueprint("stats_bp", __name__)

@stats_bp.route("/summary") # 实际访问路径取决于蓝图注册时的前缀
def get_summary():
    try:
        # 1. 统计各类垃圾分布 (饼图数据)
        label_counts = db.session.query(
            DetectItem.label, func.count(DetectItem.id)
        ).group_by(DetectItem.label).all()
        
        pie_data = [{"name": row[0], "value": row[1]} for row in label_counts]

        # 2. 统计近 7 天检测趋势 (折线图数据)
        # 获取 7 天前的时间点
        seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        
        trend_counts = db.session.query(
            func.date(DetectTask.created_at).label('date'),
            func.count(DetectTask.id)
        ).filter(DetectTask.created_at >= seven_days_ago)\
         .group_by('date')\
         .order_by('date').all()

        line_labels = [str(row[0]) for row in trend_counts]
        line_values = [row[1] for row in trend_counts]

        # 返回 JSON
        return jsonify({
            "ok": True,  # 你的前端 JS 习惯检查这个字段
            "pie_data": pie_data,
            "line_data": {
                "labels": line_labels,
                "values": line_values
            }
        })
    except Exception as e:
        # 如果数据库还没数据或者查询出错，返回错误信息
        print(f"统计接口报错: {str(e)}")
        return jsonify({
            "ok": False,
            "error": str(e),
            "pie_data": [],
            "line_data": {"labels": [], "values": []}
        }), 500