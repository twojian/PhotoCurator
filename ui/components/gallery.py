import os
from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QGridLayout
)
from ui.components.image_item import ImageItem
from concurrent.futures import ThreadPoolExecutor


class Gallery(QScrollArea):
    def __init__(self):
        super().__init__()
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(12)

        self.items = {}  # image_id -> ImageItem
        self.items_order = []

        self.setWidget(self.container)
        self.setWidgetResizable(True)

    def set_images(self, image_ids):
        cols = 4  # V1.1 固定列数
        # V1.3 清空旧内容 
        for item in self.items.values():
            item.setParent(None)

        self.items.clear()
        self.items_order.clear()  

        # V1.3 过滤不存在的文件路径
        image_ids = [p for p in image_ids if os.path.exists(p)]

        # V1.3 保持顺序列表以便计算可见性；ImageItem 采用延迟加载，不会立即读取文件
        self.items_order = list(image_ids)
        for idx, image_id in enumerate(self.items_order):
            item = ImageItem(image_id)
            self.items[image_id] = item
            row = idx // cols
            col = idx % cols
            self.grid.addWidget(item, row, col)

        # 首屏并行预热前两行缩略图，减轻后续实时加载压力
        self.preheat_thumbnails(rows=2)

    def preheat_thumbnails(self, rows: int = 2, max_workers: int = 4):
        """在后台并行生成并加载首屏缩略图（默认前两行）。"""
        if not self.items_order:
            return

        cols = 4
        end_idx = min(len(self.items_order), rows * cols)
        indices = range(0, end_idx)

        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = []
            for idx in indices:
                image_id = self.items_order[idx]
                item = self.items.get(image_id)
                if item:
                    futures.append(ex.submit(item.ensure_loaded))

            # 可选择等待完成以保证首屏显示已准备好
            for f in futures:
                try:
                    f.result(timeout=5)
                except Exception:
                    pass

    def set_state(self, image_id, state):
        if image_id in self.items:
            self.items[image_id].set_state(state)

    def get_visible_images(self):
        # V1.3 计算当前视窗可见的图片（基于垂直滚动值与固定行高估算）
        if not self.items_order:
            return []

        cols = 4
        viewport_height = self.viewport().height()
        vsb = self.verticalScrollBar()
        top = vsb.value()
        bottom = top + viewport_height

        # 估算行高（与 ImageItem.THUMB_SIZE 高度 + spacing 匹配）
        try:
            item_h = ImageItem.THUMB_SIZE[1] + self.grid.spacing()
        except Exception:
            item_h = 162

        first_row = max(0, top // item_h)
        last_row = bottom // item_h

        visible = []
        start_idx = first_row * cols
        end_idx = min(len(self.items_order), (last_row + 1) * cols)
        for idx in range(start_idx, end_idx):
            image_id = self.items_order[idx]
            visible.append(image_id)
            # 触发该项的延迟加载
            item = self.items.get(image_id)
            if item:
                item.ensure_loaded()

        return visible
