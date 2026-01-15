from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider
from PyQt6.QtCore import Qt, pyqtSignal
import json
import os
import logging

logger = logging.getLogger(__name__)

_CONFIG_PATH = os.path.join(os.getcwd(), "photocurator_config.json")

class ToolPanel(QWidget):
    # ✅ V1.2：新增信号
    viewportBoostChanged = pyqtSignal(int)
    intentBoostChanged = pyqtSignal(int)
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        title = QLabel("Scheduler Control")
        title.setStyleSheet("font-weight: bold;")

        self.viewport_label = QLabel("Viewport Boost: 10")
        self.viewport_slider = QSlider(Qt.Orientation.Horizontal)
        self.viewport_slider.setRange(1, 50)
        self.viewport_slider.setValue(10)

        self.intent_label = QLabel("Intent Boost: 100")
        self.intent_slider = QSlider(Qt.Orientation.Horizontal)
        self.intent_slider.setRange(10, 200)
        self.intent_slider.setValue(100)

        # 尝试从配置恢复
        try:
            if os.path.exists(_CONFIG_PATH):
                with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                vb = int(cfg.get('viewportBoost', 10))
                ib = int(cfg.get('intentBoost', 100))
                self.viewport_slider.setValue(vb)
                self.intent_slider.setValue(ib)
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")

        layout.addWidget(title)
        layout.addWidget(self.viewport_label)
        layout.addWidget(self.viewport_slider)
        layout.addWidget(self.intent_label)
        layout.addWidget(self.intent_slider)
        layout.addStretch()
        # ---------- 信号绑定 ----------
        # 保留 label 自动更新
        # UI 内部自更新文本
        self.viewport_slider.valueChanged.connect(
            lambda v: self.viewport_label.setText(f"Viewport Boost: {v}")
        )
        self.intent_slider.valueChanged.connect(
            lambda v: self.intent_label.setText(f"Intent Boost: {v}")
        )
        # ✅ V1.2：发射 Controller 需要的信号
        self.viewport_slider.valueChanged.connect(self.viewportBoostChanged)
        self.intent_slider.valueChanged.connect(self.intentBoostChanged)

        # V1.3 当值变化时保存到配置文件，保证重启后恢复
        def _save_config(_):
            try:
                cfg = {
                    'viewportBoost': self.viewport_slider.value(),
                    'intentBoost': self.intent_slider.value()
                }
                with open(_CONFIG_PATH, 'w', encoding='utf-8') as f:
                    json.dump(cfg, f)
            except Exception as e:
                logger.warning(f"Failed to save config: {e}")

        self.viewport_slider.valueChanged.connect(_save_config)
        self.intent_slider.valueChanged.connect(_save_config)