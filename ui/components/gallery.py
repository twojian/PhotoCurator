from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QGridLayout
)
from ui.components.image_item import ImageItem


class Gallery(QScrollArea):
    def __init__(self):
        super().__init__()
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(12)

        self.items = {}  # image_id -> ImageItem

        self.setWidget(self.container)
        self.setWidgetResizable(True)

    def set_images(self, image_ids):
        cols = 4  # V1.1 固定列数
        for idx, image_id in enumerate(image_ids):
            item = ImageItem(image_id)
            self.items[image_id] = item
            row = idx // cols
            col = idx % cols
            self.grid.addWidget(item, row, col)

    def set_state(self, image_id, state):
        if image_id in self.items:
            self.items[image_id].set_state(state)

    def get_visible_images(self):
        # V1.1 简化：认为全部可见
        return list(self.items.keys())
