"""
调度策略对象化系统（Strategy Personification）

策略不再是 if-else 或参数组合，而是一等公民对象。
每个策略都代表一套价值观，决定了调度器如何排序任务。

三种基础策略：
1. ConservativeStrategy：遵循队列顺序，稳定可靠
2. AggressiveStrategy：优先用户关注的区域，反应迅速
3. ExploratoryStrategy：探索多样性，防止局部最优

策略切换本身是一个事件，可用于后续分析"如果当时没有切策略，会怎样"。
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """策略类型。"""
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    EXPLORER = "explorer"


class Strategy(ABC):
    """
    抽象策略基类。
    
    所有策略都应实现这个接口，确保可互换。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称。"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """策略的自然语言描述（用于 StatusPanel）。"""
        pass
    
    @property
    @abstractmethod
    def strategy_type(self) -> StrategyType:
        """策略类型。"""
        pass
    
    @abstractmethod
    def get_priority_boost(self, image_id: str, context: Dict[str, Any]) -> float:
        """
        根据策略计算优先级加成。
        
        Args:
            image_id: 图片 ID
            context: 包含以下信息的上下文：
                - viewport_boost: 用户设置的视窗优先级
                - intent_boost: 用户标记的意图优先级
                - is_visible: 图片是否在可见范围
                - is_marked: 图片是否被用户标记
                - queue_age: 在队列中的年龄
        
        Returns:
            优先级加成值
        """
        pass


class ConservativeStrategy(Strategy):
    """
    保守策略：遵循队列顺序，稳定可靠。
    
    核心理念：公平、可预测、无偏好。
    """
    
    @property
    def name(self) -> str:
        return "Conservative"
    
    @property
    def description(self) -> str:
        return "我遵循队列顺序，每张图片都会被公平对待。"
    
    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.CONSERVATIVE
    
    def get_priority_boost(self, image_id: str, context: Dict[str, Any]) -> float:
        """
        保守策略：完全忽略视窗和用户标记，只看队列年龄。
        越老的任务优先级越高。
        """
        queue_age = context.get('queue_age', 0)
        # 每秒老化加 0.1 分
        return queue_age * 0.1


class AggressiveStrategy(Strategy):
    """
    激进策略：优先用户关注的区域和标记。
    
    核心理念：用户的意图至上，视窗优先。
    """
    
    @property
    def name(self) -> str:
        return "Aggressive"
    
    @property
    def description(self) -> str:
        return "我现在更关心你正在看的和标记的照片。你的意图很重要。"
    
    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.AGGRESSIVE
    
    def get_priority_boost(self, image_id: str, context: Dict[str, Any]) -> float:
        """
        激进策略：用户标记 > 可见范围 > 队列顺序。
        """
        boost = 0.0
        
        # 用户标记：最高优先级 (+100)
        if context.get('is_marked', False):
            boost += context.get('intent_boost', 100)
        
        # 在可见范围内：中优先级 (+30)
        if context.get('is_visible', False):
            boost += context.get('viewport_boost', 30)
        
        # 队列年龄：低优先级 (+0.05)
        queue_age = context.get('queue_age', 0)
        boost += queue_age * 0.05
        
        return boost


class ExploratoryStrategy(Strategy):
    """
    探索策略：寻求多样性，防止局部最优。
    
    核心理念：在用户意图和系统探索之间平衡。
    """
    
    @property
    def name(self) -> str:
        return "Explorer"
    
    @property
    def description(self) -> str:
        return "我在探索多样性和尊重你的意图之间寻找平衡。"
    
    @property
    def strategy_type(self) -> StrategyType:
        return StrategyType.EXPLORER
    
    def get_priority_boost(self, image_id: str, context: Dict[str, Any]) -> float:
        """
        探索策略：平衡用户意图和队列顺序，加入随机因素。
        """
        boost = 0.0
        
        # 用户标记：有影响但不绝对 (+50)
        if context.get('is_marked', False):
            boost += context.get('intent_boost', 100) * 0.5
        
        # 可见范围：较弱影响 (+15)
        if context.get('is_visible', False):
            boost += context.get('viewport_boost', 30) * 0.5
        
        # 队列年龄：平衡影响 (+0.08)
        queue_age = context.get('queue_age', 0)
        boost += queue_age * 0.08
        
        # 加入轻微随机因素防止确定性卡顿
        import random
        boost += random.uniform(0, 10)
        
        return boost


class StrategyManager:
    """
    策略管理器。
    
    负责策略的创建、切换和事件记录。
    """
    
    _strategies = {
        StrategyType.CONSERVATIVE: ConservativeStrategy(),
        StrategyType.AGGRESSIVE: AggressiveStrategy(),
        StrategyType.EXPLORER: ExploratoryStrategy(),
    }
    
    _current_strategy: Strategy = _strategies[StrategyType.CONSERVATIVE]
    
    @classmethod
    def get_current_strategy(cls) -> Strategy:
        """获取当前策略。"""
        return cls._current_strategy
    
    @classmethod
    def set_strategy(cls, strategy_type: StrategyType) -> Strategy:
        """
        切换策略。
        
        注意：策略切换本身应产生一个 STRATEGY_CHANGED 事件。
        这由 Scheduler 或 Controller 负责记录。
        """
        if strategy_type not in cls._strategies:
            logger.warning(f"未知策略类型：{strategy_type}")
            return cls._current_strategy
        
        cls._current_strategy = cls._strategies[strategy_type]
        logger.info(f"策略已切换为：{cls._current_strategy.description}")
        return cls._current_strategy
    
    @classmethod
    def get_all_strategies(cls) -> List[Strategy]:
        """获取所有可用策略。"""
        return list(cls._strategies.values())
    
    @classmethod
    def get_strategy_by_name(cls, name: str) -> Strategy:
        """按名称获取策略。"""
        for strategy in cls._strategies.values():
            if strategy.name.lower() == name.lower():
                return strategy
        return cls._current_strategy
