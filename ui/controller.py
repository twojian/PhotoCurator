from PyQt6.QtCore import QThread, pyqtSignal
import time

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
            embedding = self.scheduler.engine.infer(task.image_id)
            self.result_ready.emit(task.image_id, embedding)

class UIController:
    def __init__(self, scheduler, db, gallery, status_panel, tool_panel):
        self.scheduler = scheduler
        self.db = db
        self.gallery = gallery
        self.status_panel = status_panel
        self.tool_panel = tool_panel

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
        pending = sum(1 for v in self.db.states.values() if v == "PENDING")
        running = sum(1 for v in self.db.states.values() if v == "RUNNING")
        done = sum(1 for v in self.db.states.values() if v == "DONE")

        self.status_panel.update_counts(
            total, pending, running, done
        )