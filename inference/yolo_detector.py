import cv2

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
        self.model = YOLO(model_path if model_path else "best.pt")

    def detect(self, img_path, save_result=False, result_path=None):

        results = self.model(img_path)
        result = results[0]

        if save_result and result_path:
            annotated_frame = result.plot()
            cv2.imwrite(result_path, annotated_frame)

        detections = []
        for box in result.boxes:
            coords = box.xyxy[0].tolist()
            detections.append({
                "label": result.names[int(box.cls[0])],
                "confidence": float(box.conf[0]),
                "bbox": coords
            })
        
        return detections