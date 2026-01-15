from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPixmap
from PyQt6.QtCore import Qt, QRect
import os
import hashlib
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ImageItem(QWidget):
    THUMB_SIZE = (150, 150)
    TEXT_HEIGHT = 24
    PADDING = 6

    def __init__(self, image_id: str):
        super().__init__()
        self.image_id = image_id
        self.state = "PENDING"  # PENDING / RUNNING / DONE
        self.setMinimumSize(150, 150)
        self.setMaximumWidth(180)
        self.pixmap = None

        # 延迟加载：不在构造器中读取图片，避免大量同步 IO
        self._loaded = False

    def set_state(self, state: str):
        self.state = state
        self.update()  # 触发重绘

    def ensure_loaded(self):
        """确保缩略图已载入；有缓存则直接读取，否则从源文件生成并缓存。"""
        if self._loaded:
            return

        path = self.image_id
        if not os.path.exists(path):
            self._loaded = True
            return

        try:
            # 缓存文件名基于路径哈希
            cache_dir = os.path.join(os.getcwd(), "data", "thumb_cache")
            os.makedirs(cache_dir, exist_ok=True)
            key = hashlib.sha1(path.encode("utf-8")).hexdigest()
            thumb_path = os.path.join(cache_dir, f"{key}.png")

            if os.path.exists(thumb_path):
                self.pixmap = QPixmap(thumb_path)
            else:
                # 使用 PIL 以兼容更多格式（例如 HEIC via pillow-heif）
                try:
                    img = Image.open(path)
                    img.thumbnail(self.THUMB_SIZE, Image.Resampling.LANCZOS)
                    img.save(thumb_path, format="PNG")
                    self.pixmap = QPixmap(thumb_path)
                except Exception as e:
                    # 如果 PIL 打开失败，尝试使用 Qt 的 QPixmap 直接加载（对部分格式有更好兼容性）
                    logger.debug(f"PIL failed for {path}, trying QPixmap.load fallback: {e}")
                    try:
                        qp = QPixmap()
                        ok = qp.load(path)
                        if ok:
                            # 保存到缓存以便下次直接读取
                            qp_scaled = qp.scaled(
                                self.THUMB_SIZE[0], self.THUMB_SIZE[1],
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation
                            )
                            qp_scaled.save(thumb_path, "PNG")
                            self.pixmap = qp_scaled
                        else:
                            self.pixmap = None
                    except Exception as e2:
                        logger.warning(f"QPixmap fallback failed for {path}: {e2}")
                        self.pixmap = None

            # 额外缩放以适配当前项（若未通过 QPixmap 缩放）
            if self.pixmap is not None:
                self.pixmap = self.pixmap.scaled(
                    self.THUMB_SIZE[0], self.THUMB_SIZE[1],
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

        except Exception as e:
            logger.warning(f"Failed to load thumbnail for {path}: {e}")
            self.pixmap = None

        self._loaded = True

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
        
        #Item 的最小高度
        self.setMinimumSize(
        self.THUMB_SIZE[0] + self.PADDING * 2,
        self.THUMB_SIZE[1] + self.TEXT_HEIGHT + self.PADDING * 2
        )
        self.setMaximumWidth(180)

        # 背景
        rect = self.rect()
        painter.fillRect(rect, QColor(230, 230, 230))
        # ---------- 区域划分 ----------
        img_area = QRect(
            0,
            0,
            rect.width(),
            self.THUMB_SIZE[1] + self.PADDING * 2
        )

        text_area = QRect(
            self.PADDING,
            img_area.bottom(),
            rect.width() - self.PADDING * 2,
            self.TEXT_HEIGHT
        )

        # 绘制图片或占位
        if not self._loaded:
            painter.fillRect(
                img_area.adjusted(
                    self.PADDING,
                    self.PADDING,
                    -self.PADDING,
                    -self.PADDING
                ),
                QColor(200, 200, 200)
            )
        elif self.pixmap:
            pix = self.pixmap
            x = (img_area.width() - pix.width()) // 2
            y = self.PADDING + (self.THUMB_SIZE[1] - pix.height()) // 2
            painter.drawPixmap(x, y, pix)
        else:
            painter.fillRect(
                img_area.adjusted(
                    self.PADDING,
                    self.PADDING,
                    -self.PADDING,
                    -self.PADDING
                ),
                QColor(200, 200, 200)
            )

        # 左上角状态圆点
        r = 10
        margin = 6
        circle_rect = QRect(margin, margin, r, r)
        painter.setBrush(self._state_color())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(circle_rect)

        # 文件名文本
        painter.setPen(QColor(60, 60, 60))
        painter.drawText(
            text_area,
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            os.path.basename(self.image_id)
        )
