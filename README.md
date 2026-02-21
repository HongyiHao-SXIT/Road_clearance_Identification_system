# TrashDet-YOLO11
"""
# TrashDet-YOLO11

**项目简介**
- **名称**: TrashDet-YOLO11 — 垃圾检测与机器人集成演示平台。
- **用途**: 提供图像上传（Web 表单或 API）、基于 YOLO 模型的垃圾检测、带标注图片保存与检测元数据记录，提供统计与可视化，并对接基础的机器人管理与控制接口（用于与 `Clean_Robot` 集成）。

**快速开始**
- 克隆仓库并进入项目根目录。

```bash
conda activate trashdet   # 或激活你的 Python 环境
pip install -r requirements.txt
```

- 启动开发服务器：

```bash
python app.py
# 访问 http://localhost:5000
```

**主要特性**
- 支持通过 Web 界面或 API 上传图片并运行垃圾检测。
- 将带标注的检测结果保存到结果目录，并在数据库中记录任务与检测项。
- 提供统计端点用于生成饼图/折线图数据与地图点位数据。
- 提供机器人注册、心跳、控制与导航接口，便于 `Clean_Robot` 集成。

**仓库结构（概要）**
- `app.py`：Flask 应用工厂与入口脚本。
- `config.py`：配置项（根据环境调整）。
- `requirements.txt`：依赖清单。
- `best.pt`：示例/训练好的 YOLO 权重（可替换）。
- `inference/`：推理相关代码，核心为 `inference/yolo_detector.py`。
- `api/`：REST API（`api/detect_api.py`、`api/robot_api.py`、`api/stats_api.py`）。
- `web/`：页面路由（`web/pages.py`）。
- `templates/`、`static/`：前端模板与静态资源。
- `database/`：数据库初始化与模型定义（`database/models.py`）。
- `Clean_Robot/`：机器人端固件与集成示例。

**配置与环境**
- 推荐 Python 版本：3.8 及以上。
- 依赖见 `requirements.txt`。
- 在 `config.py` 中检查并根据需要修改 `UPLOAD_DIR`、`RESULT_DIR`、数据库 URI 等。
- 默认使用 SQLite，若需使用其他 RDBMS，请修改 `config.py` 中的数据库连接 URI。

**运行说明**
- 启动命令：`python app.py`。默认绑定 `0.0.0.0:5000`，开发模式下 `debug=True`。
- 首次运行会自动创建数据库表（启动时调用 `db.create_all()`）。
- 通过页面 `/upload` 上传或通过 API 调用进行检测。

**重要 API（摘要）**
- `POST /api/detect`：上传图片并运行检测。
  - 接受 `multipart/form-data`，字段示例：`image` 或 `file`（文件），可选 `latitude`、`longitude`。
  - 返回：检测列表、带标注图像路径与任务信息。实现见 `api/detect_api.py`。
- `GET /api/stats/summary`：返回地图点位、饼图数据、折线趋势与机器人状态（见 `api/stats_api.py`）。
- 机器人相关端点位于 `/api/robot/*`：心跳 `/api/robot/heartbeat`、注册 `/api/robot/register`、控制 `/api/robot/control`、导航 `/api/robot/navigate`、列表 `/api/robot/list` 等（见 `api/robot_api.py`）。

**推理（YOLO）**
- 推理入口：`inference/yolo_detector.py`，使用 `ultralytics.YOLO`（如已安装）。
- 模型权重：仓库根目录的 `best.pt`（若存在）；`YOLODetector` 会尝试加载给定路径。
- 输出：每个检测项包含 `label`、`confidence`、`bbox`，并支持保存带标注图片到结果目录。

**数据库结构（核心表）**
- `DetectTask`：记录一次上传/检测任务（源路径、结果路径、状态、经纬度、创建时间等）。
- `DetectItem`：图片内的单个检测项（类别、置信度、bbox、面积等）。
- `Robot`：机器人信息与运行状态（device_id、位置、电量、心跳时间、下发命令等）。详见 `database/models.py`。

**前端页面**
- 页面路由由 `web/pages.py` 提供：`/`、`/upload`、`/stats`、`/result`、`/robot`。
- 模板位于 `templates/`，静态资源在 `static/`（JS 在 `static/js/`，CSS 在 `static/css/`）。

**Clean_Robot 集成**
- `Clean_Robot/` 目录包含机器人端示例固件与集成说明（`README_Integration.md`）。
- 机器人通过 HTTP POST 向 `/api/robot/heartbeat` 或 `/api/robot/status_update` 上报，后端会返回 `command` 与 `target` 字段，机器人据此执行动作。

**测试**
- 项目包含基础测试示例（见 `test/`），可扩展以覆盖端到端流程。

**常见问题与建议**
- 若模型加载失败，请确认已安装 `ultralytics` 或提供兼容的 `best.pt`。
- 地址反向解析使用 OpenStreetMap Nominatim 服务；若被限流或失败，后端会回退到返回坐标文本描述。

**贡献与许可**
- 欢迎通过 issue 与 PR 参与贡献，请保持代码风格一致。
- 本项目采用 MIT 许可证，详见 [LICENSE](LICENSE)。

**联系方式 / 致谢**
- 维护者：Lanyi_adict
- 合作者：Meco_Joyang
- 参考：ultralytics/YOLO、OpenStreetMap Nominatim

"""
