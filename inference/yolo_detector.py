import os
import random
import cv2
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
    def __init__(self, model_path=None):
        #调用模型
        self.model = YOLO(model_path if model_path else "best.pt")

    def detect(self, img_path, save_result=False, result_path=None):
        # 1. 执行推理
        results = self.model(img_path)
        result = results[0]

        # 2. 如果要求保存结果图
        if save_result and result_path:
            annotated_frame = result.plot()
            cv2.imwrite(result_path, annotated_frame)

        # 3. 解析结果并返回给后端 API
        detections = []
        for box in result.boxes:
            coords = box.xyxy[0].tolist()
            detections.append({
                "label": result.names[int(box.cls[0])],
                "confidence": float(box.conf[0]),
                "bbox": coords
            })
        
        return detections