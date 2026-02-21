from flask import Blueprint, request, jsonify
from database.models import Robot
from database.db import db
from datetime import datetime

robot_bp = Blueprint('robot_bp', __name__)

# timeout in seconds after which a robot is considered offline
HEARTBEAT_TIMEOUT = 15

# 1. 心跳同步：仅允许手动注册过的设备更新
@robot_bp.route('/heartbeat', methods=['POST'])
def robot_heartbeat():
    data = request.json
    did = data.get('device_id')
    
    # 查找机器人，如果不存在则返回错误（因为你要求手动注册）
    robot = Robot.query.filter_by(device_id=did).first()
    if not robot:
        return jsonify({"ok": False, "msg": "设备未注册"}), 403
    
    # 更新动态数据
    robot.current_lat = data.get('lat')
    robot.current_lng = data.get('lng')
    # record battery if provided
    if data.get('battery') is not None:
        try:
            robot.battery = int(data.get('battery'))
        except Exception:
            pass
    robot.status = data.get('status', 'ONLINE')
    # detect ip from headers (useful when robots connect over wifi)
    ip = request.headers.get('X-Real-IP') or request.headers.get('X-Forwarded-For') or request.remote_addr
    if ip:
        robot.ip_address = ip
    robot.last_heartbeat = datetime.now()
    # grab pending command then clear it so it won't be re-delivered
    cmd = robot.next_command or "IDLE"
    robot.next_command = None
    db.session.commit()

    # 返回指令给机器人上位机
    return jsonify({
        "ok": True,
        "command": cmd,
        "target": {
            "lat": robot.target_lat,
            "lng": robot.target_lng
        }
    })


# 更丰富的实时状态上报（可由机器人通过 wifi 定期 POST）
@robot_bp.route('/status_update', methods=['POST'])
def update_robot_status():
    data = request.json or {}
    did = data.get('device_id')
    robot = Robot.query.filter_by(device_id=did).first()
    if not robot:
        return jsonify({"ok": False, "msg": "设备未注册"}), 403

    # 更新位置、电量、状态
    if 'lat' in data and 'lng' in data:
        robot.current_lat = data.get('lat')
        robot.current_lng = data.get('lng')
    if 'battery' in data:
        try:
            robot.battery = int(data.get('battery'))
        except Exception:
            pass
    if 'status' in data:
        robot.status = data.get('status')

    # ip address from request
    ip = request.headers.get('X-Real-IP') or request.headers.get('X-Forwarded-For') or request.remote_addr
    if ip:
        robot.ip_address = ip

    # optional config/sensors matrix: when provided merge into config text
    if data.get('config'):
        try:
            # store as plain text JSON string (existing `config` column is Text)
            robot.config = data.get('config')
        except Exception:
            pass

    robot.last_heartbeat = datetime.now()
    # grab pending command then clear it so it won't be re-delivered
    cmd = robot.next_command or "IDLE"
    robot.next_command = None
    db.session.commit()

    # Respond with any pending command and target
    return jsonify({
        "ok": True,
        "command": cmd,
        "target": {"lat": robot.target_lat, "lng": robot.target_lng}
    })

# 2. 手动注册机器人
@robot_bp.route('/register', methods=['POST'])
def register_robot():
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
@robot_bp.route('/delete/<int:robot_id>', methods=['POST'])
def delete_robot(robot_id):
    robot = Robot.query.get(robot_id)
    if robot:
        db.session.delete(robot)
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False, "msg": "未找到设备"})

# 4. 路径规划
@robot_bp.route('/navigate', methods=['POST'])
def navigate_robot():
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
def control_robot():
    data = request.json
    robot = Robot.query.get(data.get('id'))
    if robot:
        robot.next_command = data.get('command')
        db.session.commit()
        return jsonify({"ok": True})
    return jsonify({"ok": False})


# 6. 列表查询（前端用于显示实时位置、状态）
@robot_bp.route('/list', methods=['GET'])
def list_robots():
    robots = Robot.query.all()
    out = []
    now = datetime.now()
    to_update = []
    for r in robots:
        resp_status = r.status
        # evaluate offline by last_heartbeat
        if r.last_heartbeat:
            age = (now - r.last_heartbeat).total_seconds()
            if age > HEARTBEAT_TIMEOUT:
                resp_status = 'OFFLINE'
                if r.status != 'OFFLINE':
                    r.status = 'OFFLINE'
                    to_update.append(r)
        else:
            # never heartbeated -> treat as offline
            resp_status = 'OFFLINE'
            if r.status != 'OFFLINE':
                r.status = 'OFFLINE'
                to_update.append(r)

        out.append({
            "id": r.id,
            "device_id": r.device_id,
            "name": r.name,
            "status": resp_status,
            "lat": getattr(r, 'current_lat', None),
            "lng": getattr(r, 'current_lng', None),
            "battery": getattr(r, 'battery', None),
            "ip_address": r.ip_address,
            "last_heartbeat": (r.last_heartbeat.isoformat() if r.last_heartbeat else None),
            "next_command": r.next_command,
            "target": {"lat": r.target_lat, "lng": r.target_lng}
        })

    # persist any status changes
    if to_update:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    return jsonify({"ok": True, "robots": out})


# 管理端修改机器人信息（名称/配置/状态等）
@robot_bp.route('/update', methods=['POST'])
def update_robot():
    data = request.json or {}
    rid = data.get('id')
    robot = Robot.query.get(rid)
    if not robot:
        return jsonify({"ok": False, "msg": "机器人不存在"}), 404

    if 'name' in data:
        robot.name = data.get('name')
    if 'status' in data:
        robot.status = data.get('status')
    if 'target_lat' in data and 'target_lng' in data:
        robot.target_lat = data.get('target_lat')
        robot.target_lng = data.get('target_lng')
    if 'next_command' in data:
        robot.next_command = data.get('next_command')
    if 'config' in data:
        robot.config = data.get('config')

    db.session.commit()
    return jsonify({"ok": True})