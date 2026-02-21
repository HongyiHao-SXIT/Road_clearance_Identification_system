import logging
from flask import Flask, jsonify
from config import Config
from database.db import db
from api.detect_api import detect_bp
from web.pages import web_bp
from api.stats_api import stats_bp
from api.robot_api import robot_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # configure basic logging for the app
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    app.logger.handlers = logging.getLogger().handlers

    app.secret_key = "change-this-to-a-random-secret"

    db.init_app(app)

    app.register_blueprint(detect_bp, url_prefix="/api")
    app.register_blueprint(web_bp)
    app.register_blueprint(stats_bp, url_prefix="/api/stats")
    app.register_blueprint(robot_bp, url_prefix="/api/robot")

    # Note: stats endpoints are provided by `api/stats_api.py` (registered at /api/stats).
    # The previous inline summary route was removed to avoid duplicate routing.
    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)