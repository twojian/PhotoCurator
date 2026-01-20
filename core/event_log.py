"""
事件日志系统（Event Log System）

这是系统自我叙事的基础。
所有事件都代表"事实发生"，而不是"日志行"。

事件的最小词汇表（Minimal Vocabulary）：
- CREATED: 被发现、被索引
- ENQUEUED: 进入调度队列
- DEQUEUED: 被调度器选中
- INFER_START: 推理开始
- INFER_END: 推理完成
- WRITE_BACK: 结果写入
- VISIBLE_ENTER: 进入 Attention Window
- VISIBLE_LEAVE: 离开 Attention Window
- USER_MARK: 被用户标记
- STRATEGY_CHANGED: 调度策略变更

事件是不可变的、有序的、可重放的。
"""

import json
import time
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型枚举。"""
    CREATED = "CREATED"  # 图片被发现
    ENQUEUED = "ENQUEUED"  # 进入队列
    DEQUEUED = "DEQUEUED"  # 被调度器选中
    INFER_START = "INFER_START"  # 推理开始
    INFER_END = "INFER_END"  # 推理完成
    WRITE_BACK = "WRITE_BACK"  # 结果写入
    VISIBLE_ENTER = "VISIBLE_ENTER"  # 进入可见范围
    VISIBLE_LEAVE = "VISIBLE_LEAVE"  # 离开可见范围
    USER_MARK = "USER_MARK"  # 用户标记
    STRATEGY_CHANGED = "STRATEGY_CHANGED"  # 策略变更


@dataclass
class Event:
    """
    不可变事件对象。
    
    每个事件都是一个完整的陈述：
    "Image#42 在 timestamp 因为 context 发生了 type"
    """
    
    event_type: EventType
    image_id: str  # 主体（可以扩展为支持其他主体）
    timestamp: float  # 单调递增的时间戳
    context: Dict[str, Any]  # 原因上下文
    
    def to_dict(self) -> Dict[str, Any]:
        """转为可序列化的字典。"""
        return {
            'type': self.event_type.value,
            'image_id': self.image_id,
            'timestamp': self.timestamp,
            'context': self.context
        }
    
    def to_narrative(self) -> str:
        """转为自然语言描述（便于理解系统叙事）。"""
        narratives = {
            EventType.CREATED: f"图片 {self.image_id} 被发现（索引）",
            EventType.ENQUEUED: f"图片 {self.image_id} 进入调度队列",
            EventType.DEQUEUED: f"图片 {self.image_id} 被选中推理（策略：{self.context.get('strategy', '未知')}）",
            EventType.INFER_START: f"推理开始：{self.image_id}",
            EventType.INFER_END: f"推理完成：{self.image_id}",
            EventType.WRITE_BACK: f"结果已写入：{self.image_id}",
            EventType.VISIBLE_ENTER: f"图片 {self.image_id} 进入用户视窗（关注焦点）",
            EventType.VISIBLE_LEAVE: f"图片 {self.image_id} 离开用户视窗",
            EventType.USER_MARK: f"用户标记 {self.image_id} 为『重要』",
            EventType.STRATEGY_CHANGED: f"调度策略变更为：{self.context.get('new_strategy', '未知')}"
        }
        return narratives.get(self.event_type, "未知事件")


class EventLog:
    """
    事件日志系统。
    
    设计原则：
    - 所有事件都是不可变的
    - 事件按时间顺序严格递增
    - 支持查询、重放和分析
    - 为"为什么是它"和"时间回溯"功能奠定基础
    """
    
    def __init__(self):
        self.events: List[Event] = []
        self._lock = None  # 可选的线程锁，留给后续多线程环境
    
    def append(self, event_type: EventType, image_id: str, context: Optional[Dict[str, Any]] = None) -> Event:
        """
        追加一个新事件。
        
        Args:
            event_type: 事件类型
            image_id: 图片标识
            context: 事件上下文（原因、参数等）
        
        Returns:
            创建的事件对象（不可修改）
        """
        if context is None:
            context = {}
        
        # 确保时间戳单调递增
        timestamp = time.time()
        if self.events:
            last_ts = self.events[-1].timestamp
            if timestamp <= last_ts:
                timestamp = last_ts + 0.0001  # 微小增量保证单调性
        
        event = Event(
            event_type=event_type,
            image_id=image_id,
            timestamp=timestamp,
            context=context
        )
        self.events.append(event)
        logger.debug(f"事件记录：{event.to_narrative()}")
        return event
    
    def get_events_by_image(self, image_id: str) -> List[Event]:
        """获取某个图片的所有事件。"""
        return [e for e in self.events if e.image_id == image_id]
    
    def get_events_by_type(self, event_type: EventType) -> List[Event]:
        """获取某类事件。"""
        return [e for e in self.events if e.event_type == event_type]
    
    def get_lifecycle(self, image_id: str) -> List[str]:
        """
        获取某个图片的生命周期叙述。
        
        返回按时间顺序的自然语言事件序列。
        这是"为什么是它"功能的基础。
        """
        events = self.get_events_by_image(image_id)
        return [e.to_narrative() for e in events]
    
    def export_json(self, filepath: str):
        """导出事件日志为 JSON（用于回放和分析）。"""
        try:
            data = [e.to_dict() for e in self.events]
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"事件日志已导出到 {filepath}")
        except Exception as e:
            logger.error(f"导出事件日志失败：{e}")
    
    def replay(self, strategy_name: str = None):
        """
        时间回溯：重新演绎系统决策。
        
        如果 strategy_name 指定，可用于对比不同策略下的行为差异。
        （未来实现）
        """
        # 占位符：用于未来的对比分析
        pass
    
    def get_narrative_summary(self) -> str:
        """
        生成系统叙事总结（便于调试）。
        
        示例输出：
        - 图片 1 的生命周期：被发现 → 排队 → 推理 → 完成
        - 图片 2 的生命周期：被发现 → 用户标记 → 排队（优先级提升）→ 推理 → 完成
        """
        summary = []
        # 获取所有出现过的图片
        image_ids = set(e.image_id for e in self.events)
        for img_id in sorted(image_ids):
            lifecycle = self.get_lifecycle(img_id)
            summary.append(f"\n{img_id}:")
            for narrative in lifecycle:
                summary.append(f"  → {narrative}")
        return "\n".join(summary)


# 全局事件日志实例
_global_event_log = EventLog()


def get_event_log() -> EventLog:
    """获取全局事件日志。"""
    return _global_event_log
