import os

class Config:
    # ====== MySQL 配置（按你自己的改）======
    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "123456")
    MYSQL_DB = os.getenv("MYSQL_DB", "trashdet")

    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
        "?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 时区/连接池（可选）
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
    RESULT_DIR = os.path.join(BASE_DIR, "static", "results")

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
