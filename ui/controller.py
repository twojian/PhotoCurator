from PyQt6.QtCore import QThread, pyqtSignal
from core.engine import load_and_vectorize
import logging

logger = logging.getLogger(__name__)

class InferenceWorker(QThread):
    task_started = pyqtSignal(str)
    result_ready = pyqtSignal(str, object)

    def __init__(self, scheduler):
        super().__init__()
        self.scheduler = scheduler

    def run(self):
        # V1.3 批量拉取任务，减少频繁锁竞争与高并发 IO 峰值
        while not self.isInterruptionRequested():
            batch = []
            try:
                batch = self.scheduler.get_next_batch(8)
            except Exception as e:
                logger.warning(f"Failed to get batch from scheduler: {e}")

            if not batch:
                self.msleep(50)
                continue

            for task in batch:
                try:
                    self.task_started.emit(task.image_id)
                    embedding = None
                    x = load_and_vectorize(task.image_id)
                    embedding = self.scheduler.engine.infer(x)
                    self.result_ready.emit(task.image_id, embedding)
                except Exception as e:
                    logger.error(f"推理失败 {task.image_id}: {e}")

            # V1.3 在处理完一批后短暂休眠，缓解 CPU/IO 峰值
            self.msleep(30)

class UIController:
    def __init__(self, scheduler, db, gallery, status_panel, tool_panel):
        self.scheduler = scheduler
        self.db = db
        self.gallery = gallery
        self.status_panel = status_panel
        self.tool_panel = tool_panel

        # ---------- V1.2：绑定 ToolPanel 信号（防御性绑定，避免 NoneType/AttributeError） ----------
        if self.tool_panel is not None:
            # 信号可能在不同 Qt 版本或 Mock 环境中不可用，故做保护性检测
            if hasattr(self.tool_panel, 'viewportBoostChanged') and hasattr(self.tool_panel, 'intentBoostChanged'):
                try:
                    self.tool_panel.viewportBoostChanged.connect(self._on_viewport_changed)
                    self.tool_panel.intentBoostChanged.connect(self._on_intent_changed)
                except Exception as e:
                    logger.warning(f"Failed to bind tool_panel signals: {e}")
            else:
                logger.warning("tool_panel missing expected signals; scheduler boosts unavailable")
        else:
            logger.warning("tool_panel is None; scheduler boosts unavailable")
        
        # 图片标记事件：当用户右键点击图片时
        if hasattr(self.gallery, 'items'):
            for item in self.gallery.items.values():
                if hasattr(item, 'rightClicked'):
                    item.rightClicked.connect(self._on_image_right_clicked)

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
        # 防御性调用 UI 组件方法
        try:
            if self.gallery is not None:
                self.gallery.set_state(image_id, "RUNNING")
        except Exception:
            logger.warning(f"gallery.set_state failed for {image_id}")

        try:
            self._update_status_panel()
        except Exception:
            logger.warning("status panel update failed on task start")

    def on_task_finished(self, image_id, embedding):
        self.db.set_embedding(image_id, embedding)
        try:
            if self.gallery is not None:
                self.gallery.set_state(image_id, "DONE")
        except Exception:
            logger.warning(f"gallery.set_state failed for {image_id} on finish")

        try:
            self._update_status_panel()
        except Exception:
            logger.warning("status panel update failed on task finish")

    def on_scroll_stopped(self, visible_ids):
        self.scheduler.bump_to_front_batch(visible_ids)

    def _update_status_panel(self):
        total = len(self.db.images)
        pending = sum(1 for r in self.db.images.values() if r.state == "PENDING")
        running = sum(1 for r in self.db.images.values() if r.state == "RUNNING")
        done = sum(1 for r in self.db.images.values() if r.state == "DONE")

        # debug log
        print(f"[DEBUG] Status: total={total}, pending={pending}, running={running}, done={done}")

        self.status_panel.update_counts(total, pending, running, done)
        
        # 根据 Intent Boost 更新调度策略描述
        if self.tool_panel and hasattr(self.tool_panel, 'intent_slider'):
            intent_boost = self.tool_panel.intent_slider.value()
            viewport_boost = self.tool_panel.viewport_slider.value()
            
            # 简单的策略推断
            if viewport_boost > 30:
                strategy = "aggressive"
            elif viewport_boost < 10:
                strategy = "passive"
            else:
                strategy = "passive"  # 默认保守
            
            try:
                self.status_panel.update_strategy(strategy)
            except Exception as e:
                logger.debug(f"Failed to update strategy: {e}")
        
        # 更新用户标记计数
        if self.gallery and hasattr(self.gallery, 'get_marked_images'):
            try:
                marked_count = len(self.gallery.get_marked_images())
                if self.tool_panel and hasattr(self.tool_panel, 'update_marked_count'):
                    self.tool_panel.update_marked_count(marked_count)
            except Exception as e:
                logger.debug(f"Failed to update marked count: {e}")

    def _on_image_right_clicked(self, image_id: str):
        """处理图片右键点击事件，为'为什么是它'功能预留接口。"""
        logger.info(f"Right-clicked on {image_id} - 'Why is it?' feature reserved for future")