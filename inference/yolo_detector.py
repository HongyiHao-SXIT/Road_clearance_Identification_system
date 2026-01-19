import os
import random
from datetime import datetime

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

YOLO_CLASS_NAMES = [
    "Plastic Bottle",
    "Face Mask",
    "PaperBag",
    "Plastic Cup",
    "Paper Cup",
    "Cardboard",
    "Peel",
    "Cans",
    "Plastic Wrapper",
    "Paperboard",
    "Styrofoam",
    "Tetra Pack",
    "Colored Glass Bottles",
    "Plastic Bag",
    "Rags",
    "Pile of Leaves",
    "Glass Bottle",
]


class YOLODetector:
    """
    支持两种模式：
    1. real  -> 使用 best.pt
    2. mock  -> 无模型，随机生成检测结果
    """
    def __init__(self, model_path=None):
        self.model_path = model_path
        self.mode = "mock"

        if model_path and os.path.exists(model_path) and YOLO is not None:
            self.mode = "real"
            self.model = YOLO(model_path)
            print("[YOLO] Real model loaded")
        else:
            print("[YOLO] Using MOCK detector")

    def detect(self, image_path, conf=0.25):
        if self.mode == "real":
            return self._detect_real(image_path, conf)
        return self._detect_mock(image_path)

    def _detect_real(self, image_path, conf):
        results = self.model(image_path, conf=conf)
        detections = []

        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                cls_id = int(box.cls[0])
                detections.append({
                    "label": self.model.names[cls_id],
                    "confidence": float(box.conf[0]),
                    "bbox": [x1, y1, x2, y2],
                })
        return detections

    def _detect_mock(self, image_path):
        labels = ["plastic", "paper", "can", "cigarette", "bottle"]
        detections = []

        for _ in range(random.randint(1, 4)):
            x1 = random.randint(50, 200)
            y1 = random.randint(50, 200)
            x2 = x1 + random.randint(30, 120)
            y2 = y1 + random.randint(30, 120)

            detections.append({
                "label": random.choice(labels),
                "confidence": round(random.uniform(0.6, 0.95), 3),
                "bbox": [x1, y1, x2, y2],
                "mock": True,
                "ts": datetime.utcnow().isoformat()
            })
        return detections
