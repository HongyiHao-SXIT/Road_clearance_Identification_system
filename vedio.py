import cv2
from ultralytics import YOLO

def main():
    model = YOLO(r"best.pt")

    resize_width = 320
    resize_height = 240

    cap = cv2.VideoCapture(0)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, resize_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resize_height)

    if not cap.isOpened():
        print("无法打开摄像头！")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法读取摄像头画面！")
            break

        resized_frame = cv2.resize(frame, (resize_width, resize_height))

        results = model(resized_frame)

        annotated_frame = results[0].plot()

        display_frame = cv2.resize(annotated_frame, (960, 720))

        cv2.imshow("YOLO11 Real-time Detection", display_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
