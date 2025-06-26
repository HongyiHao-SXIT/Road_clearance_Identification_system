from ultralytics import YOLO

if __name__ == '__main__':
    # Create model from YAML config (not pre-trained weights)
    model = YOLO(r'C:/Users/Lanyi/Desktop/Project/Road_clearance_Identification_system/ultralytics-main/ultralytics/cfg/models/11/yolo11.yaml')

    # Train the model
    model.train(
        cfg=r'C:/Users/Lanyi/Desktop/Project/Road_clearance_Identification_system/ultralytics-main/ultralytics/cfg/default.yaml',
        data=r'C:/Users/Lanyi/Desktop/Project/Road_clearance_Identification_system/data.yaml',
        optimizer='SGD',
        epochs=200,
        project=r'C:/Users/Lanyi/Desktop/Project/Road_clearance_Identification_system/runs',
        name='train-200epoch-v11n',
        batch=24,
        workers=8,
        split='val'
    )

    # #恢复中断的训练
    # Load a model
    # model = YOLO(r"E:\knowledge\YOLO-v8\ultralytics-main\runs\detected\Packages\train-200epoch-v8s\weights\last.pt")  # load a partially trained model
    # # Resume training
    # result = model.train(resume=True,
    #                      data=r"E:\knowledge\YOLO-v8\ultralytics-main\runs\detected\Packages\train-200epoch-v8s\weights\last.pt"
    #                      )

    # # 模型验证
    # model = YOLO(r"D:\Dataset\All\CarDetection\Udacity Self Driving Car.v2-fixed-large\PedestrianAndVehicles-13146\YOLO-v8-GhostNetV2\runs\detect\train-300epoch-GhostNetV2\weights\best.pt")
    # model.val( data= r"D:\Dataset\All\CarDetection\Udacity Self Driving Car.v2-fixed-large\PedestrianAndVehicles-13146\YOLO-v8-GhostNetV2\runs\detect\train-300epoch-GhostNetV2\weights\best.pt",
    #            cfg = 'ultralytics/cfg/default.yaml',
    #            split = 'val',
    #            project=r"D:\Dataset\All\CarDetection\Udacity Self Driving Car.v2-fixed-large\PedestrianAndVehicles-13146\YOLO-v8-GhostNetV2\runs\detect",
    #            name='val_GhostNetV2')

    # # 模型推理
    # model = YOLO(r"/workspace/YOLO11/yolo11n.pt")
    # model.predict(source=r"/workspace/YOLO11/ultralytics/assets",
    #               save=True,
    #               project=r"/workspace/YOLO11/runs",
    #               name='predict'
    #               )

    # # 模型转换
    # # Load a model
    # model = YOLO(r"E:\knowledge\YOLO-v8\ultralytics-main\best.pt")  # load a custom trained model
    # model.export(device='cuda', format="onnx", dynamic=False, simplify=True, opset=11)