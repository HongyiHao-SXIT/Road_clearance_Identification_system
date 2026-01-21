from datetime import datetime
from database.db import db
from flask_login import UserMixin
import werkzeug.security as security

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')

    def set_password(self, password):
        self.password_hash = security.generate_password_hash(password)

    def check_password(self, password):
        return security.check_password_hash(self.password_hash, password)

class DetectTask(db.Model):
    __tablename__ = 'detect_task'
    id = db.Column(db.Integer, primary_key=True)
    source_type = db.Column(db.String(20))  # image / video
    source_path = db.Column(db.String(255))
    result_path = db.Column(db.String(255), nullable=True)
    device_id = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='PENDING') # PENDING, DONE, FAILED
    error_msg = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    items = db.relationship('DetectItem', backref='task', lazy=True)

    def to_dict(self, with_items=False):
        data = {
            "id": self.id,
            "source_path": self.source_path,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "location": self.location
        }
        if with_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data


class DetectItem(db.Model):
    __tablename__ = 'detect_item'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('detect_task.id'))
    label = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    x1 = db.Column(db.Integer)
    y1 = db.Column(db.Integer)
    x2 = db.Column(db.Integer)
    y2 = db.Column(db.Integer)
    area = db.Column(db.Integer)
    handle_state = db.Column(db.String(20), default='NEW')

    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "label": self.label,
            "confidence": self.confidence,
            "bbox": [self.x1, self.y1, self.x2, self.y2],
            "handle_state": self.handle_state
        }
    
class OpsLog(db.Model):
    __tablename__ = 'ops_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    action = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)