from ultralytics import YOLO
yolo = YOLO("./yolov8n.pt", task="detect")
result = yolo(source=r"C:\Users\Lanyi\Desktop\Project\Road_clearance_Identification_system\ultralytics-main\ultralytics\assets\bus.jpg", save=True)