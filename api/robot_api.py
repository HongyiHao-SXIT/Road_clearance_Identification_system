from flask import Blueprint, request, jsonify
from database.models import Robot
from database.db import db
import json

robot_bp = Blueprint('robot_bp', __name__)

# 机器人端调用：上报心跳和当前位置
@robot_bp.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    did = data.get('device_id')
    pos = data.get('position') # 传入的字符串地址或坐标
    
    robot = Robot.query.filter_by(device_id=did).first()
    if not robot:
        # 自动注册新设备
        robot = Robot(device_id=did, name=f"新机器人_{did[-4:]}")
        db.session.add(robot)
    
    robot.status = 'ONLINE'
    robot.robot_position = pos
    robot.last_heartbeat = db.func.now()
    db.session.commit()
    
    # 返回当前的配置给机器人（实现配置下发）
    return jsonify({"ok": True, "config": json.loads(robot.config)})

# 后台调用：更新机器人配置（远程控制）
@robot_bp.route('/update_config', methods=['POST'])
def update_config():
    data = request.json
    rid = data.get('id')
    new_conf = data.get('config') # 比如 {"active": false} 停止机器人
    
    robot = Robot.query.get(rid)
    if robot:
        robot.config = json.dumps(new_conf)
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False, "message": "未找到设备"}), 404