"""
图片数据库与生命周期追踪。

ImageRecord 不仅存储状态，还记录完整的生命周期事件。
这使得系统可以回答"为什么是它"等问题。
"""

import time
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ImageRecord:
    """
    图片记录对象。
    
    完整的生命周期信息：
    - 文件路径和基本元数据
    - 推理状态：PENDING / QUEUED / RUNNING / DONE
    - 用户交互：标记、点击等
    - 时间戳：各阶段的时间记录
    - 事件链：可追溯的完整历史（通过 event_log）
    """
    
    def __init__(self, path: str):
        self.path = path
        self.embedding = None
        self.state = "PENDING"  # PENDING / QUEUED / RUNNING / DONE
        
        # 生命周期时间戳
        self.created_at = time.time()  # 被发现的时间
        self.enqueued_at: Optional[float] = None  # 进入队列的时间
        self.dequeued_at: Optional[float] = None  # 被选中的时间
        self.infer_start_at: Optional[float] = None  # 推理开始的时间
        self.infer_end_at: Optional[float] = None  # 推理完成的时间
        self.write_back_at: Optional[float] = None  # 写入结果的时间
        
        # 用户交互
        self.is_marked = False  # 是否被用户标记为重要
        self.marked_at: Optional[float] = None  # 标记的时间
        
        # 可见性跟踪
        self.visible_times: List[tuple] = []  # [(enter_time, leave_time), ...]
        self.currently_visible = False
        self.last_visible_enter_time: Optional[float] = None
        
        # 调度上下文（用于后续分析"为什么是它"）
        self.selection_context: Dict[str, Any] = {}  # 被选中时的上下文
    
    @property
    def queue_age(self) -> float:
        """在队列中的年龄（秒）。"""
        if self.enqueued_at is None:
            return 0.0
        current_time = time.time()
        return current_time - self.enqueued_at
    
    @property
    def infer_duration(self) -> Optional[float]:
        """推理耗时（秒）。"""
        if self.infer_start_at is None or self.infer_end_at is None:
            return None
        return self.infer_end_at - self.infer_start_at
    
    @property
    def total_duration(self) -> float:
        """从创建到完成的总耗时（秒）。"""
        end_time = self.write_back_at or self.infer_end_at or self.dequeued_at or time.time()
        return end_time - self.created_at
    
    def mark_as_important(self):
        """标记为用户关注对象。"""
        self.is_marked = True
        self.marked_at = time.time()
    
    def unmark(self):
        """取消标记。"""
        self.is_marked = False
        self.marked_at = None
    
    def set_state(self, state: str):
        """更新状态。"""
        self.state = state
    
    def set_embedding(self, emb, inference_duration: Optional[float] = None):
        """设置推理结果并更新时间戳。"""
        self.embedding = emb
        self.state = "DONE"
        if self.infer_end_at is None:
            self.infer_end_at = time.time()
        self.write_back_at = time.time()
    
    def enter_viewport(self):
        """进入用户可见范围。"""
        if not self.currently_visible:
            self.currently_visible = True
            self.last_visible_enter_time = time.time()
    
    def leave_viewport(self):
        """离开用户可见范围。"""
        if self.currently_visible:
            self.currently_visible = False
            if self.last_visible_enter_time:
                self.visible_times.append((
                    self.last_visible_enter_time,
                    time.time()
                ))
    
    def get_visibility_duration(self) -> float:
        """计算总可见时长（秒）。"""
        duration = sum(end - start for start, end in self.visible_times)
        if self.currently_visible and self.last_visible_enter_time:
            duration += time.time() - self.last_visible_enter_time
        return duration
    
    def to_dict(self) -> Dict[str, Any]:
        """转为字典（便于序列化和调试）。"""
        return {
            'path': self.path,
            'state': self.state,
            'is_marked': self.is_marked,
            'created_at': self.created_at,
            'enqueued_at': self.enqueued_at,
            'dequeued_at': self.dequeued_at,
            'infer_start_at': self.infer_start_at,
            'infer_end_at': self.infer_end_at,
            'write_back_at': self.write_back_at,
            'queue_age': self.queue_age,
            'infer_duration': self.infer_duration,
            'total_duration': self.total_duration,
            'visibility_duration': self.get_visibility_duration(),
        }


class ImageDatabase:
    """图片数据库。"""
    
    def __init__(self):
        self.records = {}  # path -> ImageRecord
    
    def add(self, path: str) -> ImageRecord:
        """添加一条新记录。"""
        if path not in self.records:
            self.records[path] = ImageRecord(path)
            logger.debug(f"创建新记录：{path}")
        return self.records[path]
    
    def get(self, path: str) -> Optional[ImageRecord]:
        """获取记录。"""
        return self.records.get(path)
    
    def set_state(self, path: str, state: str):
        """设置状态。"""
        if path in self.records:
            self.records[path].set_state(state)
    
    def set_embedding(self, path: str, emb, inference_duration: Optional[float] = None):
        """设置推理结果。"""
        if path in self.records:
            self.records[path].set_embedding(emb, inference_duration)
    
    def mark_image(self, path: str):
        """标记图片。"""
        if path in self.records:
            self.records[path].mark_as_important()
    
    def unmark_image(self, path: str):
        """取消标记。"""
        if path in self.records:
            self.records[path].unmark()
    
    @property
    def images(self) -> Dict[str, 'ImageRecord']:
        """属性代理：兼容 Controller 中 self.db.images 访问。"""
        return self.records
    
    def get_marked_images(self) -> List[str]:
        """获取所有被标记的图片。"""
        return [path for path, record in self.records.items() if record.is_marked]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息（便于 StatusPanel 显示）。"""
        return {
            'total': len(self.records),
            'pending': sum(1 for r in self.records.values() if r.state == 'PENDING'),
            'queued': sum(1 for r in self.records.values() if r.state == 'QUEUED'),
            'running': sum(1 for r in self.records.values() if r.state == 'RUNNING'),
            'done': sum(1 for r in self.records.values() if r.state == 'DONE'),
            'marked': sum(1 for r in self.records.values() if r.is_marked),
        }
