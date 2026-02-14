from flask import Flask, jsonify
from config import Config
from database.db import db
# auth/login removed
from api.detect_api import detect_bp
from web.pages import web_bp
from api.stats_api import stats_bp
from api.robot_api import robot_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.secret_key = "change-this-to-a-random-secret"

    db.init_app(app)

    # auth/login blueprints removed
    app.register_blueprint(detect_bp, url_prefix="/api")
    app.register_blueprint(web_bp)
    app.register_blueprint(stats_bp, url_prefix="/api/stats")
    app.register_blueprint(robot_bp, url_prefix="/api/robot")

    @app.route('/api/stats/summary')
    def get_summary():
        return jsonify({
            "ok": True,
            "pie_data": [{"name": "塑料瓶", "value": 30}, {"name": "纸张", "value": 20}],
            "line_data": {"labels": ["周一", "周二", "周三", "周四", "周五"], "values": [10, 20, 15, 25, 30]},
            "locations": [{"id": 1, "lat": 25.04, "lng": 102.71, "trash_types": "塑料瓶"}]
        })


    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)