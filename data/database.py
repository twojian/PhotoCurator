class ImageRecord:
    def __init__(self, path):
        self.path = path
        self.embedding = None
        self.state = "PENDING"  # PENDING / QUEUED / RUNNING / DONE

class ImageDatabase:
    def __init__(self):
        self.records = {}

    def add(self, path):
        self.records[path] = ImageRecord(path)

    def set_state(self, path, state):
        self.records[path].state = state

    def set_embedding(self, path, emb):
        self.records[path].embedding = emb
        self.records[path].state = "DONE"
