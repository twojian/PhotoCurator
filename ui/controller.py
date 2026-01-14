from PyQt6.QtCore import QThread, pyqtSignal
from core.engine import load_and_vectorize

class InferenceWorker(QThread):
    task_started = pyqtSignal(str)
    result_ready = pyqtSignal(str, object)

    def __init__(self, scheduler):
        super().__init__()
        self.scheduler = scheduler

    def run(self):
        while not self.isInterruptionRequested():
            task = self.scheduler.get_next_task()
            if task is None:
                self.msleep(50)
                continue

            self.task_started.emit(task.image_id)
            embedding = None
            try:
                x = load_and_vectorize(task.image_id)
                embedding = self.scheduler.engine.infer(x)
            except Exception as e:
                print(f"[ERROR] 推理失败 {task.image_id}: {e}")

            self.result_ready.emit(task.image_id, embedding)

class UIController:
    def __init__(self, scheduler, db, gallery, status_panel, tool_panel):
        self.scheduler = scheduler
        self.db = db
        self.gallery = gallery
        self.status_panel = status_panel
        self.tool_panel = tool_panel

        # ---------- V1.2：绑定 ToolPanel 信号 ----------
        self.tool_panel.viewportBoostChanged.connect(self._on_viewport_changed)
        self.tool_panel.intentBoostChanged.connect(self._on_intent_changed)

    # ---------- 信号处理函数 ----------
    def _on_viewport_changed(self, value: int):
        self.scheduler.set_viewport_boost(value)

    def _on_intent_changed(self, value: int):
        self.scheduler.set_intent_boost(value)

    def submit_image(self, image_id):
        self.db.add(image_id)
        self.scheduler.add_task(image_id)

    def on_task_started(self, image_id):
        self.db.set_state(image_id, "RUNNING")
        self.gallery.set_state(image_id, "RUNNING")
        self._update_status_panel()

    def on_task_finished(self, image_id, embedding):
        self.db.set_embedding(image_id, embedding)
        self.gallery.set_state(image_id, "DONE")
        self._update_status_panel()

    def on_scroll_stopped(self, visible_ids):
        self.scheduler.bump_to_front_batch(visible_ids)

    def _update_status_panel(self):
        total = len(self.db.images)
        pending = sum(1 for r in self.db.images.values() if r.state == "PENDING")
        running = sum(1 for r in self.db.images.values() if r.state == "RUNNING")
        done = sum(1 for r in self.db.images.values() if r.state == "DONE")

        # debug log
        print(f"[DEBUG] Status: total={total}, pending={pending}, running={running}, done={done}")

        self.status_panel.update_counts(
            total, pending, running, done
        )