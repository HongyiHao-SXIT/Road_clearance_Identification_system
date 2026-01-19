from datetime import datetime
from .db import db
from werkzeug.security import generate_password_hash, check_password_hash

class DetectTask(db.Model):
    __tablename__ = "detect_task"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    # image / video / camera
    source_type = db.Column(db.String(20), nullable=False, default="image")

    # 原始图片路径 & 结果图路径（存相对路径更好迁移）
    source_path = db.Column(db.String(512), nullable=False)
    result_path = db.Column(db.String(512), nullable=True)

    # 设备/地点（可空，后面你想加GPS就用这个）
    device_id = db.Column(db.String(64), nullable=True)
    location = db.Column(db.String(128), nullable=True)

    # PENDING / DONE / FAILED
    status = db.Column(db.String(20), nullable=False, default="PENDING")
    error_msg = db.Column(db.String(512), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # 关联：一个 task 对应多个 item
    items = db.relationship(
        "DetectItem",
        backref="task",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self, with_items: bool = False):
        d = {
            "id": self.id,
            "source_type": self.source_type,
            "source_path": self.source_path,
            "result_path": self.result_path,
            "device_id": self.device_id,
            "location": self.location,
            "status": self.status,
            "error_msg": self.error_msg,
            "created_at": self.created_at.isoformat(),
        }
        if with_items:
            d["items"] = [i.to_dict() for i in self.items]
        return d


class DetectItem(db.Model):
    __tablename__ = "detect_item"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    task_id = db.Column(db.BigInteger, db.ForeignKey("detect_task.id"), nullable=False)

    # 模型输出
    label = db.Column(db.String(64), nullable=False)
    confidence = db.Column(db.Float, nullable=False)

    # bbox: x1,y1,x2,y2
    x1 = db.Column(db.Integer, nullable=False)
    y1 = db.Column(db.Integer, nullable=False)
    x2 = db.Column(db.Integer, nullable=False)
    y2 = db.Column(db.Integer, nullable=False)

    # 目标面积（可做过滤/统计）
    area = db.Column(db.Integer, nullable=True)

    # 人工确认：NULL(未标注) / 1(真实垃圾) / 0(误报)
    is_valid = db.Column(db.Boolean, nullable=True)

    # NEW / CONFIRMED / CLEANED / IGNORED
    handle_state = db.Column(db.String(20), nullable=False, default="NEW")

    note = db.Column(db.String(256), nullable=True)

    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    logs = db.relationship(
        "OpsLog",
        backref="item",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "label": self.label,
            "confidence": float(self.confidence),
            "bbox": [self.x1, self.y1, self.x2, self.y2],
            "area": self.area,
            "is_valid": self.is_valid,
            "handle_state": self.handle_state,
            "note": self.note,
            "updated_at": self.updated_at.isoformat(),
        }


class OpsLog(db.Model):
    __tablename__ = "ops_log"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    item_id = db.Column(db.BigInteger, db.ForeignKey("detect_item.id"), nullable=False)

    # confirm / clean / ignore / update_note ...
    action = db.Column(db.String(32), nullable=False)

    operator = db.Column(db.String(64), nullable=True)
    detail = db.Column(db.String(256), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "item_id": self.item_id,
            "action": self.action,
            "operator": self.operator,
            "detail": self.detail,
            "created_at": self.created_at.isoformat(),
        }

class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # 简单权限：admin / user（可选）
    role = db.Column(db.String(20), nullable=False, default="user")

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)