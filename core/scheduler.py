import heapq
import time
import threading
import itertools

VIEWPORT_BOOST = 10
INTENT_BOOST = 100
DECAY_FACTOR = 0.95


class Task:
    def __init__(self, image_id: str, priority=0):
        self.image_id = image_id
        self.priority = priority
        self.timestamp = time.time()

    def score(self):
        age = time.time() - self.timestamp
        return -(self.priority + age * 0.1)


class PriorityScheduler:
    def __init__(self, engine):
        self.engine = engine
        self.lock = threading.Lock()

        self.task_map = {}   # image_id -> Task
        self.heap = []       # (score, counter, task)
        self._counter = itertools.count()    # 全局递增，保证可比较性

    def add_task(self, image_id):
        with self.lock:
            if image_id in self.task_map:
                return

            task = Task(image_id)
            self.task_map[image_id] = task

            heapq.heappush(
                self.heap,
                (-task.priority, next(self._counter), task)
            )

    def bump_to_front_batch(self, image_ids):
        with self.lock:
            for img_id in image_ids:
                if img_id in self.task_map:
                    self.task_map[img_id].priority += VIEWPORT_BOOST
            self._rebuild_heap()

    def promote(self, image_id):
        with self.lock:
            if image_id in self.task_map:
                self.task_map[image_id].priority += INTENT_BOOST
                self._rebuild_heap()

    def get_next_task(self):
        with self.lock:
            if not self.heap:
                return None

            _, _, task = heapq.heappop(self.heap)
            # 任务出队后，从 map 中移除
            self.task_map.pop(task.image_id, None)
            return task

    def decay(self):
        with self.lock:
            for task in self.task_map.values():
                task.priority *= DECAY_FACTOR
            self._rebuild_heap()

    def _rebuild_heap(self):
        self.heap.clear()
        for task in self.task_map.values():
            self.heap.append(
                (task.score(), next(self._counter), task)
            )
        heapq.heapify(self.heap)