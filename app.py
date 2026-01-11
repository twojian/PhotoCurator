import sys
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

    # Core
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

    worker = InferenceWorker(scheduler)
    worker.task_started.connect(controller.on_task_started)
    worker.result_ready.connect(controller.on_task_finished)
    worker.start()

    # ⛔ 关键：应用退出时，安全关闭线程
    def on_exit():
        worker.requestInterruption()
        worker.quit()
        worker.wait(2000)

    app.aboutToQuit.connect(on_exit)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
