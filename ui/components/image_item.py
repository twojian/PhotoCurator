from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import Qt, QRect


class ImageItem(QWidget):
    def __init__(self, image_id: str):
        super().__init__()
        self.image_id = image_id
        self.state = "PENDING"
        self.setMinimumSize(150, 150)
        self.setMaximumWidth(180)

    def set_state(self, state: str):
        self.state = state
        self.update()  # 触发重绘

    def _state_color(self):
        if self.state == "PENDING":
            return QColor(160, 160, 160)  # 灰
        if self.state == "RUNNING":
            return QColor(70, 130, 255)   # 蓝
        if self.state == "DONE":
            return QColor(80, 180, 120)   # 绿
        return QColor(0, 0, 0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 背景（图片占位）
        painter.fillRect(self.rect(), QColor(230, 230, 230))

        # 左上角状态圆点
        r = 10
        margin = 8
        circle_rect = QRect(margin, margin, r, r)
        painter.setBrush(self._state_color())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(circle_rect)

        # 图片 ID 文本（调试用）
        painter.setPen(QColor(80, 80, 80))
        painter.drawText(
            self.rect().adjusted(5, 30, -5, -5),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            self.image_id
        )
