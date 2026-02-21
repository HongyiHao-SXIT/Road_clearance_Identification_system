from datetime import datetime
from database.db import db
from flask_login import UserMixin
import werkzeug.security as security

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    security_code = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')

    def set_password(self, password):
        self.password_hash = security.generate_password_hash(password)

    def check_password(self, password):
        return security.check_password_hash(self.password_hash, password)
    
    def set_security_code(self, security_code):
        """Set security code hash (PEP8-compliant name)."""
        self.security_code = security.generate_password_hash(security_code)

    def check_security_code(self, security_code):
        """Check security code against stored hash (PEP8-compliant name)."""
        return security.check_password_hash(self.security_code, security_code)

    # Backwards-compatible aliases for old method names
    def set_securitycode(self, security_code):
        return self.set_security_code(security_code)

    def check_securitycode(self, security_code):
        return self.check_security_code(security_code)


class DetectTask(db.Model):
    __tablename__ = 'detect_task'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    source_type = db.Column(db.String(20))
    source_path = db.Column(db.String(255))
    result_path = db.Column(db.String(255), nullable=True)
    device_id = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='PENDING')
    error_msg = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    items = db.relationship('DetectItem', backref='task', lazy=True)


class DetectItem(db.Model):
    __tablename__ = 'detect_item'
    __table_args__ = {'extend_existing': True}
    
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


class OpsLog(db.Model):
    __tablename__ = 'ops_log'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    action = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)


class Robot(db.Model):
    __tablename__ = 'robot'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100))
    status = db.Column(db.String(20), default='OFFLINE')
    ip_address = db.Column(db.String(50))

    current_lat = db.Column(db.Float, nullable=True)
    current_lng = db.Column(db.Float, nullable=True)

    target_lat = db.Column(db.Float, nullable=True)
    target_lng = db.Column(db.Float, nullable=True)
    
    last_heartbeat = db.Column(db.DateTime, default=datetime.now)
    next_command = db.Column(db.String(100), default='IDLE')

    battery = db.Column(db.Integer, default=100)
    config = db.Column(db.Text, default='{"confidence_threshold": 0.5, "active": true}')
    created_at = db.Column(db.DateTime, default=datetime.now)