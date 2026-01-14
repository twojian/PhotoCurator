from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPixmap
from PyQt6.QtCore import Qt, QRect
import os

class ImageItem(QWidget):
    def __init__(self, image_id: str):
        super().__init__()
        self.image_id = image_id
        self.state = "PENDING"  # PENDING / RUNNING / DONE
        self.setMinimumSize(150, 150)
        self.setMaximumWidth(180)
        self.pixmap = None

        # 尝试加载图片
        if os.path.exists(image_id):
            self.pixmap = QPixmap(image_id).scaled(
                150, 150,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

    def set_state(self, state: str):
        self.state = state
        self.update()  # 触发重绘

    def _state_color(self):
        if self.state == "PENDING":
            return QColor(160, 160, 160)
        if self.state == "RUNNING":
            return QColor(70, 130, 255)
        if self.state == "DONE":
            return QColor(80, 180, 120)
        return QColor(0, 0, 0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 背景
        painter.fillRect(self.rect(), QColor(230, 230, 230))

        # 绘制图片或占位
        rect = self.rect().adjusted(5, 5, -5, -5)
        if self.pixmap:
            painter.drawPixmap(rect, self.pixmap)
        else:
            painter.fillRect(rect, QColor(200, 200, 200))

        # 左上角状态圆点
        r = 10
        margin = 8
        circle_rect = QRect(margin, margin, r, r)
        painter.setBrush(self._state_color())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(circle_rect)

        # 文件名文本
        filename = os.path.basename(self.image_id)
        painter.setPen(QColor(80, 80, 80))
        painter.drawText(
            self.rect().adjusted(5, self.height()-20, -5, -5),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
            filename
        )
