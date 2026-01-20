from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
import logging

logger = logging.getLogger(__name__)


class StatusPanel(QWidget):
    """
    系统意识层（System Consciousness）
    
    展示 AI 的内部状态与"情绪"，让用户了解系统正在想什么。
    - 情绪指示：冷启动(紧张) / 稳定(放松) / 阻塞(焦虑)
    - 推理时间轴：可视化推理流程
    - 策略描述：用自然语言描述当前调度策略而非参数
    """

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 标题：系统意图
        title = QLabel("系统意图")
        title.setStyleSheet("字体粗细：粗体；字体大小：12pt;")
        layout.addWidget(title)

        # 情绪指示（System Mood）- 心跳脉搏
        mood_layout = QHBoxLayout()
        self.mood_label = QLabel("● 预热中...")
        self.mood_label.setStyleSheet("颜色: #FF6B6B; 字体粗细：粗体;")
        mood_layout.addWidget(self.mood_label)
        mood_layout.addStretch()
        layout.addLayout(mood_layout)

        # 推理时间轴（Inference Timeline）- 可视化推理流程
        timeline_layout = QHBoxLayout()
        self.timeline_label = QLabel("⊙加载中 → ⊙排队中 → ⊙推理中→ ⊙写入")
        self.timeline_label.setStyleSheet("字体样式: 等宽字体; 字号: 9pt; 颜色: #666;")
        timeline_layout.addWidget(self.timeline_label)
        layout.addLayout(timeline_layout)

        # 策略描述（Strategy Personification）
        self.strategy_label = QLabel("策略：遵循队列顺序...")
        self.strategy_label.setStyleSheet("字体样式：斜体；颜色：#888；字号：10pt；")
        self.strategy_label.setWordWrap(True)
        layout.addWidget(self.strategy_label)

        # 数值统计（Stats）
        self.stats_label = QLabel("总计: 0  |  待定: 0  |  运行中: 0  |  完成: 0")
        self.stats_label.setStyleSheet("字体样式: 等宽字体; 字号: 9pt; 颜色: #555;")
        layout.addWidget(self.stats_label)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        layout.addStretch()
        
        self._last_mood_icon = "●"
        self._mood_timer = QTimer()
        self._mood_timer.timeout.connect(self._update_mood_animation)
        self._mood_timer.start(500)

    def update_counts(self, total, pending, running, done):
        """更新统计数据并推断系统情绪。"""
        self.stats_label.setText(
            f"总计: {total}  |  待定: {pending}  |  运行中: {running}  |  完成: {done}"
        )
        
        # 情绪推断逻辑
        if total == 0:
            mood = "● 闲置"
            mood_color = "#999999"
        elif done == total and total > 0:
            mood = "● 休闲"
            mood_color = "#4CAF50"
        elif running > 0 and pending > 0:
            mood = "● 焦虑"
            mood_color = "#FFA500"
        elif running == 0 and pending > 0:
            mood = "● 紧张"
            mood_color = "#FF6B6B"
        else:
            mood = "● 专注"
            mood_color = "#2196F3"
        
        self.mood_label.setText(mood)
        self.mood_label.setStyleSheet(f"颜色: {mood_color}; 字体粗细：粗体;")
        self.update()

    def update_strategy(self, strategy_name: str):
        """根据调度器策略更新描述。"""
        strategies = {
            "passive": "策略：遵循队列顺序，循序渐进。",
            "aggressive": "策略：优先处理你看到的内容。意图很重要。",
            "explorer": "战略：探索未知领域，追求多样性."
        }
        desc = strategies.get(strategy_name, "策略：未知模式...")
        self.strategy_label.setText(desc)

    def _update_mood_animation(self):
        """为心跳符号添加简单的闪烁动画。"""
        text = self.mood_label.text()
        if "●" in text or "◐" in text:
            icon = "◐" if self._last_mood_icon == "●" else "●"
            new_text = text.replace("●", icon).replace("◐", icon)
            self.mood_label.setText(new_text)
            self._last_mood_icon = icon