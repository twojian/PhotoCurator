import heapq
import time
import threading
import itertools


class Task:
    def __init__(self, image_id: str, priority=0):
        self.image_id = image_id
        self.priority = priority
        self.timestamp = time.time()

    def score(self):
        # 年龄衰减 + 优先级
        age = time.time() - self.timestamp
        return -(self.priority + age * 0.1)


class PriorityScheduler:
    def __init__(
        self,
        engine,
        viewport_boost: int = 10,
        intent_boost: int = 100,
        decay_factor: float = 0.95
    ):
        self.engine = engine
        self.lock = threading.Lock()

        # ✅ V1.2：调度参数实例化
        self.viewport_boost = viewport_boost
        self.intent_boost = intent_boost
        self.decay_factor = decay_factor

        self.task_map = {}   # image_id -> Task
        self.heap = []       # (score, counter, task)
        self._counter = itertools.count()

    # ---------- 参数 setter（V1.2 新增） ----------
    def set_viewport_boost(self, value: int):
        with self.lock:
            self.viewport_boost = value

    def set_intent_boost(self, value: int):
        with self.lock:
            self.intent_boost = value

    def set_decay_factor(self, value: float):
        with self.lock:
            self.decay_factor = value

    # ---------- 调度逻辑 ----------

    def add_task(self, image_id):
        with self.lock:
            if image_id in self.task_map:
                return # 去重：已在队列中，忽略

            task = Task(image_id)
            self.task_map[image_id] = task

            heapq.heappush(
                self.heap,
                (task.score(), next(self._counter), task)
            )

    def bump_to_front_batch(self, image_ids):
        with self.lock:
            for img_id in image_ids:
                if img_id in self.task_map:
                    self.task_map[img_id].priority += self.viewport_boost
            self._rebuild_heap()

    def promote(self, image_id):
        with self.lock:
            if image_id in self.task_map:
                self.task_map[image_id].priority += self.intent_boost
                self._rebuild_heap()

    def get_next_task(self):
        with self.lock:
            while self.heap:
                _, _, task = heapq.heappop(self.heap)
                # DONE 任务直接跳过
                if task.image_id not in self.task_map:
                    continue
                # 出队后，从 map 移除，避免重复
                self.task_map.pop(task.image_id)
                return task
            return None

    def get_next_batch(self, max_items: int = 8):
        """ V1.3 一次性出队多个任务，减少调度器锁竞争与 Worker 的频繁唤醒。"""
        out = []
        with self.lock:
            while self.heap and len(out) < max_items:
                _, _, task = heapq.heappop(self.heap)
                if task.image_id not in self.task_map:
                    continue
                self.task_map.pop(task.image_id)
                out.append(task)
        return out

    def decay(self):
        with self.lock:
            for task in self.task_map.values():
                task.priority *= self.decay_factor
            self._rebuild_heap()

    def _rebuild_heap(self):
        self.heap.clear()
        for task in self.task_map.values():
            self.heap.append(
                (task.score(), next(self._counter), task)
            )
        heapq.heapify(self.heap)