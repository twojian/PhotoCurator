import sys
import os
from PyQt6.QtWidgets import QApplication
from core.engine import InferenceEngine
from core.scheduler import PriorityScheduler
from data.database import ImageDatabase
from data.weight_loader import load_weights
from ui.controller import InferenceWorker, UIController
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    # -------------------- 获取真实图片路径 --------------------
    test_photo_dir = os.path.join("data", "test_photo")
    if not os.path.exists(test_photo_dir):
        print(f"[WARN] 测试图片文件夹不存在: {test_photo_dir}")
        image_paths = []
    else:
        image_paths = [
            os.path.join(test_photo_dir, f)
            for f in os.listdir(test_photo_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
    print(f"[INFO] 找到 {len(image_paths)} 张测试图片")

    # 如果有真实图片，覆盖 fake images
    if image_paths:
        window.gallery.set_images(image_paths)

    # -------------------- Core --------------------
    weights = load_weights("weights.bin")
    engine = InferenceEngine(weights)
    scheduler = PriorityScheduler(engine)
    db = ImageDatabase()

    controller = UIController(
        scheduler,
        db,
        window.gallery,
        window.status_panel,
        window.tool_panel
    )

    # 自动提交所有图片到调度器
    for img_path in image_paths or [f"image_{i}.jpg" for i in range(30)]:
        controller.submit_image(img_path)

    # -------------------- Worker --------------------
    worker = InferenceWorker(scheduler)
    worker.task_started.connect(controller.on_task_started)
    worker.result_ready.connect(controller.on_task_finished)
    worker.start()

    # ⛔ 安全退出
    def on_exit():
        worker.requestInterruption()
        worker.wait(3000)

    app.aboutToQuit.connect(on_exit)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
