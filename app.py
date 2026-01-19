from flask import Flask
from config import Config
from database.db import db

from api.auth_api import auth_bp, login_manager
from api.main import main_bp
from api.detect_api import detect_bp  # 你已有的检测上传接口
from web.pages import web_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # session 需要 secret key
    app.secret_key = "change-this-to-a-random-secret"

    db.init_app(app)

    # Flask-Login
    login_manager.init_app(app)

    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)
    app.register_blueprint(detect_bp, url_prefix="/api")
    app.register_blueprint(web_bp)


    @app.route("/health")
    def health():
        return {"ok": True}

    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        from database import models  # noqa: F401
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
