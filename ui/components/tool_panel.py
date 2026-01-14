from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider
from PyQt6.QtCore import Qt, pyqtSignal

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