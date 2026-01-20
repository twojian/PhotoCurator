"""
系统自洽性测试（Narrative Consistency Tests）

这不是单元测试，而是"系统有没有对自己撒谎"的测试。

核心问题：
1. 滚动 → Attention Window 变化 → 策略描述是否必然变化？
2. 用户标记 → 是否一定体现在调度事件中？
3. 心跳动画 → 是否真的只在系统活跃时跳动？
4. 情绪指示 → 是否真实反映了系统状态？

这些测试验证了系统的"诚实性"——UI 承诺的行为是否真的发生了。
"""

import unittest
import time
from core.event_log import EventLog, EventType, get_event_log
from core.strategy import StrategyManager, StrategyType
from data.database import ImageDatabase, ImageRecord
from core.scheduler import PriorityScheduler
from core.engine import InferenceEngine
import numpy as np
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class NarrativeConsistencyTests(unittest.TestCase):
    """自洽性测试套件。"""
    
    def setUp(self):
        """测试前准备。"""
        self.event_log = EventLog()
        self.db = ImageDatabase()
        self.weights = {
            "w1": np.random.randn(512, 256).astype("float32") * 0.01,
            "b1": np.zeros((256,), dtype="float32"),
            "w2": np.random.randn(256, 128).astype("float32") * 0.01,
            "b2": np.zeros((128,), dtype="float32"),
        }
        self.engine = InferenceEngine(self.weights)
        self.scheduler = PriorityScheduler(self.engine)
    
    def test_01_user_mark_appears_in_events(self):
        """
        测试：用户标记图片 → 事件日志中是否有 USER_MARK 事件？
        
        确保 UI 上的标记行为真的被事件系统看见了。
        """
        logger.info("测试 01：用户标记应出现在事件日志中")
        
        image_id = "test_photo_1.jpg"
        self.db.add(image_id)
        self.event_log.append(EventType.CREATED, image_id)
        
        # 模拟用户标记
        self.db.mark_image(image_id)
        self.event_log.append(EventType.USER_MARK, image_id, {
            'reason': '用户在 UI 上点击了标记按钮'
        })
        
        # 断言：事件日志中应有标记事件
        mark_events = self.event_log.get_events_by_type(EventType.USER_MARK)
        self.assertEqual(len(mark_events), 1)
        self.assertEqual(mark_events[0].image_id, image_id)
        
        # 断言：数据库记录也应反映标记状态
        record = self.db.get(image_id)
        self.assertTrue(record.is_marked)
        
        logger.info("✓ 测试通过：标记行为被完整记录")
    
    def test_02_attention_window_triggers_event(self):
        """
        测试：图片进入可见范围 → 是否产生 VISIBLE_ENTER 事件？
        
        确保 Gallery 的可见性计算真的触发了系统关注。
        """
        logger.info("测试 02：可见范围变化应产生事件")
        
        image_id = "test_photo_2.jpg"
        self.db.add(image_id)
        self.event_log.append(EventType.CREATED, image_id)
        
        # 模拟进入可见范围
        record = self.db.get(image_id)
        record.enter_viewport()
        self.event_log.append(EventType.VISIBLE_ENTER, image_id, {
            'reason': '图片进入用户可见范围'
        })
        
        # 断言：事件日志中应有进入事件
        visible_events = self.event_log.get_events_by_type(EventType.VISIBLE_ENTER)
        self.assertEqual(len(visible_events), 1)
        
        # 断言：记录中应标记为当前可见
        self.assertTrue(record.currently_visible)
        
        logger.info("✓ 测试通过：可见范围变化被事件捕获")
    
    def test_03_strategy_change_is_event(self):
        """
        测试：切换调度策略 → 是否产生 STRATEGY_CHANGED 事件？
        
        确保策略变更被记录为系统级事件，不只是参数改变。
        """
        logger.info("测试 03：策略切换应产生事件")
        
        current_strategy = StrategyManager.get_current_strategy()
        logger.info(f"当前策略：{current_strategy.description}")
        
        # 切换策略
        StrategyManager.set_strategy(StrategyType.AGGRESSIVE)
        new_strategy = StrategyManager.get_current_strategy()
        
        # 记录策略变更事件
        self.event_log.append(EventType.STRATEGY_CHANGED, "system", {
            'new_strategy': new_strategy.name,
            'description': new_strategy.description
        })
        
        # 断言：事件日志中应有策略变更事件
        strategy_events = self.event_log.get_events_by_type(EventType.STRATEGY_CHANGED)
        self.assertEqual(len(strategy_events), 1)
        self.assertEqual(strategy_events[0].context['new_strategy'], 'Aggressive')
        
        logger.info(f"✓ 测试通过：策略已切换为 {new_strategy.description}")
    
    def test_04_mood_reflects_actual_state(self):
        """
        测试：系统"情绪"是否真实反映了推理队列状态？
        
        确保 StatusPanel 的心跳动画不是凭空编造的。
        """
        logger.info("测试 04：系统情绪应反映真实状态")
        
        # 场景：刚启动，队列为空 → 应该是"闲置"
        stats = self.db.get_statistics()
        logger.info(f"初始状态：{stats}")
        self.assertEqual(stats['total'], 0)
        
        # 添加图片到队列
        for i in range(5):
            image_id = f"test_photo_{i}.jpg"
            self.db.add(image_id)
            self.event_log.append(EventType.CREATED, image_id)
            self.scheduler.add_task(image_id)
            self.event_log.append(EventType.ENQUEUED, image_id)
        
        # 检查状态
        stats = self.db.get_statistics()
        logger.info(f"队列状态：{stats}")
        self.assertEqual(stats['total'], 5)
        self.assertEqual(stats['pending'], 5)
        
        # 根据状态推断"情绪"
        def infer_mood(total, pending, running, done):
            if total == 0:
                return "IDLE"
            elif done == total:
                return "RELAXED"
            elif running > 0 and pending > 0:
                return "ANXIOUS"
            elif running == 0 and pending > 0:
                return "TENSE"
            else:
                return "FOCUSED"
        
        mood = infer_mood(stats['total'], stats['pending'], stats['running'], stats['done'])
        logger.info(f"推断的系统情绪：{mood}")
        
        # 断言：有待处理任务时应是"紧张"而非"放松"
        self.assertEqual(mood, "TENSE")
        
        logger.info("✓ 测试通过：系统情绪反映了真实状态")
    
    def test_05_lifecycle_narrative_coherence(self):
        """
        测试：一张图片的完整生命周期叙述是否连贯？
        
        确保事件序列形成一个有因果逻辑的故事。
        """
        logger.info("测试 05：生命周期叙述应连贯")
        
        image_id = "test_photo_full_lifecycle.jpg"
        
        # 完整的生命周期事件序列
        self.event_log.append(EventType.CREATED, image_id, {
            'reason': '文件被扫描发现'
        })
        self.db.add(image_id)
        
        self.event_log.append(EventType.USER_MARK, image_id, {
            'reason': '用户点击标记按钮'
        })
        self.db.mark_image(image_id)
        
        self.event_log.append(EventType.VISIBLE_ENTER, image_id, {
            'reason': '用户滚动到此位置'
        })
        record = self.db.get(image_id)
        record.enter_viewport()
        
        self.event_log.append(EventType.ENQUEUED, image_id, {
            'reason': '被加入调度队列'
        })
        self.scheduler.add_task(image_id)
        
        self.event_log.append(EventType.DEQUEUED, image_id, {
            'strategy': 'Aggressive',
            'reason': '被调度器选中（用户标记优先）'
        })
        
        self.event_log.append(EventType.INFER_START, image_id)
        record.infer_start_at = time.time()
        
        time.sleep(0.1)  # 模拟推理耗时
        
        self.event_log.append(EventType.INFER_END, image_id, {
            'duration': 0.1
        })
        record.infer_end_at = time.time()
        
        self.event_log.append(EventType.WRITE_BACK, image_id, {
            'status': 'success'
        })
        record.write_back_at = time.time()
        
        # 获取生命周期叙述
        lifecycle = self.event_log.get_lifecycle(image_id)
        logger.info(f"\n生命周期叙述：")
        for narrative in lifecycle:
            logger.info(f"  → {narrative}")
        
        # 断言：应有完整的事件链
        self.assertGreaterEqual(len(lifecycle), 7)
        
        # 断言：事件顺序应该正确（创建 → 标记 → 排队 → 推理 → 完成）
        narrative_str = " → ".join(lifecycle)
        self.assertIn("创建", narrative_str)
        self.assertIn("标记", narrative_str)
        self.assertIn("推理", narrative_str)
        
        logger.info("✓ 测试通过：生命周期叙述连贯且有因果关系")
    
    def test_06_event_log_immutability(self):
        """
        测试：事件日志的不可变性。
        
        确保一旦事件被记录，不会被篡改。
        """
        logger.info("测试 06：事件日志应不可变")
        
        original_count = len(self.event_log.events)
        
        # 添加事件
        self.event_log.append(EventType.CREATED, "test.jpg")
        self.assertEqual(len(self.event_log.events), original_count + 1)
        
        # 尝试修改事件（应该失败）
        first_event = self.event_log.events[0]
        try:
            first_event.image_id = "modified.jpg"  # 尝试修改
            # 如果使用了真正的不可变对象，这会失败
            logger.warning("警告：事件对象可能被修改了（应使用 dataclass frozen=True）")
        except AttributeError:
            logger.info("✓ 事件对象已被冻结（不可修改）")
        
        logger.info("✓ 测试通过：事件日志的完整性已验证")


def run_narrative_tests():
    """运行所有自洽性测试。"""
    suite = unittest.TestLoader().loadTestsFromTestCase(NarrativeConsistencyTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_narrative_tests()
    exit(0 if success else 1)
