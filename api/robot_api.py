from flask import Blueprint, request, jsonify
from database.models import Robot
from database.db import db
from datetime import datetime

robot_bp = Blueprint('robot_bp', __name__)

# 1. 心跳同步：仅允许手动注册过的设备更新
@robot_bp.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    did = data.get('device_id')
    
    # 查找机器人，如果不存在则返回错误（因为你要求手动注册）
    robot = Robot.query.filter_by(device_id=did).first()
    if not robot:
        return jsonify({"ok": False, "msg": "设备未注册"}), 403
    
    # 更新动态数据
    robot.current_lat = data.get('lat')
    robot.current_lng = data.get('lng')
    robot.status = 'ONLINE'
    robot.last_heartbeat = datetime.now() # 建议加上最后活跃时间
    db.session.commit()
    
    # 返回指令给机器人上位机
    return jsonify({
        "ok": True,
        "command": robot.next_command or "IDLE",
        "target": {
            "lat": robot.target_lat, 
            "lng": robot.target_lng
        }
    })

# 2. 手动注册机器人
@robot_bp.route('/register', methods=['POST'])
def manual_register():
    data = request.json
    device_id = data.get('device_id')
    name = data.get('name')
    
    if not device_id or not name:
        return jsonify({"ok": False, "msg": "信息不完整"})

    if Robot.query.filter_by(device_id=device_id).first():
        return jsonify({"ok": False, "msg": "该设备 ID 已存在"})
    
    # 初始位置可以设为地图默认中心
    new_robot = Robot(device_id=device_id, name=name, status='OFFLINE')
    db.session.add(new_robot)
    db.session.commit()
    return jsonify({"ok": True})

# 3. 删除机器人
@robot_bp.route('/delete/<int:id>', methods=['POST'])
def delete_robot(id):
    robot = Robot.query.get(id)
    if robot:
        db.session.delete(robot)
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False, "msg": "未找到设备"})

# 4. 路径规划
@robot_bp.route('/navigate', methods=['POST'])
def navigate_to():
    data = request.json
    robot = Robot.query.get(data.get('id'))
    if not robot:
        return jsonify({"ok": False, "msg": "机器人不存在"})

    robot.target_lat = data.get('lat')
    robot.target_lng = data.get('lng')
    robot.next_command = "NAVIGATE" 
    db.session.commit()
    return jsonify({"ok": True, "msg": "目标已锁定"})

# 5. 远程控制 (抓取、复位、停机)
@robot_bp.route('/control', methods=['POST'])
def send_control():
    data = request.json
    robot = Robot.query.get(data.get('id'))
    if robot:
        robot.next_command = data.get('command')
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False})