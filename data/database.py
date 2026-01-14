class ImageRecord:
    def __init__(self, path):
        self.path = path
        self.embedding = None
        self.state = "PENDING"  # PENDING / QUEUED / RUNNING / DONE

class ImageDatabase:
    def __init__(self):
        self.records = {}  # image_id/path -> ImageRecord

    def add(self, path):
        self.records[path] = ImageRecord(path)

    def set_state(self, path, state):
        if path in self.records:
            self.records[path].state = state

    def set_embedding(self, path, emb):
        if path in self.records:
            self.records[path].embedding = emb
            self.records[path].state = "DONE"

    @property
    def images(self):
        """
        属性代理：兼容 Controller 中 self.db.images 访问
        返回当前所有记录字典
        """
        return self.records
