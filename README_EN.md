# TrashDet-YOLO11

**Project Overview**
- **Name**: TrashDet-YOLO11 — a demo platform for trash detection and robot integration.
- **Purpose**: Accept image uploads (via web form or API), run object detection using a YOLO model, save annotated results and detection metadata, provide statistics and visualization, and expose basic robot management and control endpoints for integration with the `Clean_Robot` firmware.

**Quick Start**
- Clone the repository and change into the project root.

```bash
conda activate trashdet   # or activate your preferred Python environment
pip install -r requirements.txt
```

- Start the development server:

```bash
python app.py
# Open http://localhost:5000
```

**Key Features**
- Upload images via web UI or API and run trash detection using YOLO.
- Save annotated images to the results directory and record tasks/items in the database.
- Provide statistical endpoints for pie/line charts and map point data.
- Basic robot endpoints for registration, heartbeat, control and navigation to integrate with `Clean_Robot`.

**Repository Layout (high level)**
- `app.py` — Flask application factory and entrypoint.
- `config.py` — configuration values (adjust for your environment).
- `requirements.txt` — Python dependencies.
- `best.pt` — example/trained YOLO model weights (replace with your model as needed).
- `inference/` — inference code; see `inference/yolo_detector.py` for the detector.
- `api/` — backend REST API endpoints (`api/detect_api.py`, `api/robot_api.py`, `api/stats_api.py`).
- `web/` — server-side page routes (`web/pages.py`).
- `templates/`, `static/` — front-end templates and static assets (JS/CSS/images).
- `database/` — database initialization and models (`database/models.py`).
- `Clean_Robot/` — robot firmware and integration examples.

**Configuration & Environment**
- Recommended Python: 3.8+.
- Dependencies are listed in `requirements.txt`.
- Check and modify `config.py` for `UPLOAD_DIR`, `RESULT_DIR`, database URI, and other settings.
- Default storage uses SQLite; change the database URI in `config.py` to use another RDBMS if needed.

**Running (notes)**
- Launch: `python app.py`. By default the app binds to `0.0.0.0:5000` with `debug=True` (development mode).
- On first run the app will create database tables (`db.create_all()` is executed on startup).
- Upload via the web UI (`/upload`) or call the API.

**Important API Endpoints (summary)**
- `POST /api/detect` — upload an image and run detection.
  - Accepts `multipart/form-data` with fields like `image` or `file` (file), and optional `latitude` and `longitude`.
  - Returns detection list, annotated image path and task metadata. Implementation: `api/detect_api.py`.
- `GET /api/stats/summary` — returns locations, pie chart data, line trend and robot list. Implementation: `api/stats_api.py`.
- Robot endpoints under `/api/robot/*`: heartbeat (`/api/robot/heartbeat`), register (`/api/robot/register`), control (`/api/robot/control`), navigate (`/api/robot/navigate`), list (`/api/robot/list`), etc. Implementation: `api/robot_api.py`.

**Inference (YOLO)**
- Detector: `inference/yolo_detector.py` uses `ultralytics.YOLO` if available.
- Model weights: `best.pt` at repository root (if present). The detector will attempt to load the provided model path.
- Output: detection entries include `label`, `confidence`, and `bbox`. Annotated images can be saved to the configured results directory.

**Database Schema (core tables)**
- `DetectTask` — records an upload/detection task (source/result path, status, coordinates, created_at, etc.).
- `DetectItem` — per-image detection items (label, confidence, bbox, area, handle_state, etc.).
- `Robot` — robot records and runtime status (device_id, location, battery, last_heartbeat, next_command, etc.).
  See `database/models.py` for full definitions.

**Front-end**
- Page routes in `web/pages.py`: `/`, `/upload`, `/stats`, `/result`, `/robot`.
- Templates are in `templates/`, static assets in `static/` (JS under `static/js/`, CSS under `static/css/`).

**Clean_Robot Integration**
- The `Clean_Robot/` directory contains example firmware and integration notes (`README_Integration.md`).
- Robots should POST heartbeat or status updates to `/api/robot/heartbeat` or `/api/robot/status_update`. The server returns `command` and `target` fields which robots should act upon.

**Testing**
- Basic test examples exist in the `test/` directory. Extend or run those tests as needed.

**Troubleshooting & Notes**
- If model loading fails, ensure `ultralytics` is installed or place a compatible `best.pt` file in the project root.
- External address reverse-geocoding uses OpenStreetMap Nominatim; if requests are rate-limited or fail, the server will fallback to returning coordinates as a textual description.

**Contributing & License**
- Contributions via issues and pull requests are welcome. Please keep code style consistent with existing project formatting.
- This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

**Acknowledgements / Contact**
- Maintainer: see repository history for authorship.
- References: ultralytics/YOLO, OpenStreetMap Nominatim.
