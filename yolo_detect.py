import os
from ultralytics import YOLO

def main():
    print("=== YOLO 垃圾识别程序 ===")

    # 1. 模型路径（字符串）
    model_path = r"best.pt"
    if not os.path.exists(model_path):
        print("❌ 模型文件不存在！")
        return

    # 2. 输入图片路径
    img_path = input("请输入要识别的图片路径: ").strip()
    if not os.path.exists(img_path):
        print("❌ 图片文件不存在！")
        return

    # 3. 加载模型
    print("正在加载模型...")
    model = YOLO(model_path)

    # 4. 推理
    print("正在识别，请稍候...")
    results = model(img_path)

    # 5. 保存结果
    save_dir = os.path.dirname(img_path)
    save_path = os.path.join(save_dir, "detected_" + os.path.basename(img_path))
    results[0].save(filename=save_path)

    print("🎉 识别完成！")
    print(f"已输出标注图片: {save_path}")


if __name__ == "__main__":
    main()
