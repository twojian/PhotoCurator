from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QLineEdit, QPlainTextEdit
from PyQt6.QtCore import Qt, pyqtSignal
import json
import os
import logging

logger = logging.getLogger(__name__)

_CONFIG_PATH = os.path.join(os.getcwd(), "photocurator_config.json")


class ToolPanel(QWidget):
    """
    人类意图层（Human Intent）
    
    不是"工具箱"，而是对 AI 的"耳语"。
    所有控件都应回答：我想让系统更在意什么？
    """
    
    viewportBoostChanged = pyqtSignal(int)
    intentBoostChanged = pyqtSignal(int)
    userNoteChanged = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("个人意图")
        title.setStyleSheet("字体粗细：粗体；字体大小：12pt;")
        layout.addWidget(title)

        # Viewport Boost - 哲学化描述
        self.viewport_label = QLabel("焦点：我正看着这里")
        self.viewport_label.setStyleSheet("字体样式：斜体；颜色：#666；字号：10pt;")
        self.viewport_slider = QSlider(Qt.Orientation.Horizontal)
        self.viewport_slider.setRange(1, 50)
        self.viewport_slider.setValue(10)
        layout.addWidget(self.viewport_label)
        layout.addWidget(self.viewport_slider)

        # Intent Boost - 哲学化描述
        self.intent_label = QLabel("权重：我标记了这些图片很重要")
        self.intent_label.setStyleSheet("字体样式：斜体；颜色：#666；字号：10pt;")
        self.intent_slider = QSlider(Qt.Orientation.Horizontal)
        self.intent_slider.setRange(10, 200)
        self.intent_slider.setValue(100)
        layout.addWidget(self.intent_label)
        layout.addWidget(self.intent_slider)

        # 尝试从配置恢复
        try:
            if os.path.exists(_CONFIG_PATH):
                with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                vb = int(cfg.get('视口增强', 10))
                ib = int(cfg.get('意图增强', 100))
                self.viewport_slider.setValue(vb)
                self.intent_slider.setValue(ib)
        except Exception as e:
            logger.warning(f"配置文件加载失败: {e}")

        # 未来预留：对话式调度（Dialogue-based Scheduling）
        # 这是一个 placeholder，为将来的自然语言意图解析留下空间
        hint_label = QLabel("💭 未来：自然语言提示")
        hint_label.setStyleSheet("字号：9pt；颜色：#AAA；")
        layout.addWidget(hint_label)
        
        self.hint_input = QLineEdit()
        self.hint_input.setPlaceholderText("e.g., “优先处理景观”（未来功能）")
        self.hint_input.setStyleSheet("背景颜色：#F5F5F5；边框：1像素实线 #DDD；")
        self.hint_input.setEnabled(False)  # 暂未启用
        layout.addWidget(self.hint_input)

        # 用户标记反馈
        marked_label = QLabel("📌 标记的图片")
        marked_label.setStyleSheet("字体粗细：粗体；字号：10pt;")
        layout.addWidget(marked_label)
        
        self.marked_count_label = QLabel("0 张图片被标记为重要")
        self.marked_count_label.setStyleSheet("字号：9pt；颜色：#888;")
        layout.addWidget(self.marked_count_label)

        layout.addStretch()

        # 信号绑定
        self.viewport_slider.valueChanged.connect(self._on_viewport_changed)
        self.intent_slider.valueChanged.connect(self._on_intent_changed)

    def _on_viewport_changed(self, value):
        """更新 Viewport Boost 时的描述与信号。"""
        descriptions = {
            1: "焦点：几乎不关注这个区域",
            10: "焦点：我正看着这里",
            25: "焦点：强烈关注可见区域",
            50: "焦点：只关注可见部分"
        }
        # 找最接近的描述
        closest_key = min(descriptions.keys(), key=lambda k: abs(k - value))
        self.viewport_label.setText(descriptions[closest_key])
        
        self.viewportBoostChanged.emit(value)
        self._save_config()

    def _on_intent_changed(self, value):
        """更新 Intent Boost 时的描述与信号。"""
        descriptions = {
            10: "权重：我的标记只是提示",
            100: "权重：我标记了这些图片很重要",
            150: "权重：非常重要 - 我选择了这些图片",
            200: "权重：关键 - 只有我的选择才重要"
        }
        closest_key = min(descriptions.keys(), key=lambda k: abs(k - value))
        self.intent_label.setText(descriptions[closest_key])
        
        self.intentBoostChanged.emit(value)
        self._save_config()

    def update_marked_count(self, count: int):
        """更新用户标记的图片数。"""
        self.marked_count_label.setText(f"{count} 张图片被标记为重要")

    def _save_config(self):
        """保存配置到文件。"""
        try:
            cfg = {
                '视口增强': self.viewport_slider.value(),
                '意图增强': self.intent_slider.value()
            }
            with open(_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(cfg, f)
        except Exception as e:
            logger.warning(f"配置保存失败: {e}")