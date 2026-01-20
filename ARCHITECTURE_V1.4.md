"""
PhotoCurator 架构与设计说明
V1.4 - 自我叙事的透明系统

=============================================================================
核心架构演进
=============================================================================

从 V1.0-V1.3 的逐步优化，我们已实现了一个"可被观察、可被干预、可被理解"的 AI 系统。
V1.4 的关键突破是：从"黑箱有窗口"升级到"自我叙事的透明体"。

核心创新：
1. 事件日志系统（Event Log） - 系统自我叙事的基础
2. 策略对象化（Strategy Personification） - 价值观成为一等公民
3. 自洽性测试（Narrative Consistency Tests） - 验证系统的"诚实性"

=============================================================================
一、事件日志系统（core/event_log.py）
=============================================================================

概念：
- 不是"日志行"，而是"事实记录"
- 每个事件都是一个完整的陈述：事件类型 + 主体 + 时间戳 + 原因上下文
- 事件是不可变的、有序的、可重放的

最小事件词汇表：
  CREATED         - 图片被发现、被索引
  ENQUEUED        - 进入调度队列
  DEQUEUED        - 被调度器选中
  INFER_START     - 推理开始
  INFER_END       - 推理完成
  WRITE_BACK      - 结果写入
  VISIBLE_ENTER   - 进入用户可见范围（Attention Window）
  VISIBLE_LEAVE   - 离开用户可见范围
  USER_MARK       - 被用户标记为重要
  STRATEGY_CHANGED - 调度策略变更

设计原则：
1. 不在 UI 层生成事件
2. 不在 Scheduler/Engine 内硬编码 UI 语义
3. 所有事件由 Controller（边界层）产生

用法示例：
  from core.event_log import get_event_log, EventType
  
  log = get_event_log()
  log.append(EventType.CREATED, "photo_1.jpg")
  log.append(EventType.USER_MARK, "photo_1.jpg", {
      'reason': '用户点击了标记按钮'
  })
  
  # 获取某图片的完整生命周期
  lifecycle = log.get_lifecycle("photo_1.jpg")
  for narrative in lifecycle:
      print(narrative)  # 自然语言描述

=============================================================================
二、策略对象化系统（core/strategy.py）
=============================================================================

概念：
- 策略不再是参数组合（viewport_boost=10, intent_boost=100）
- 策略是代表价值观的一等公民对象
- 三种基础策略：Conservative（保守）/ Aggressive（激进）/ Explorer（探索）

设计思想：
每个策略都实现相同接口，但体现不同的"人格"：

  ConservativeStrategy
    └─ 价值观：公平、可预测、无偏好
    └─ 行为：完全遵循队列顺序，忽略用户标记
    
  AggressiveStrategy
    └─ 价值观：用户意图至上
    └─ 行为：优先标记项和可见范围内的图片
    
  ExploratoryStrategy
    └─ 价值观：平衡探索与用户意图
    └─ 行为：在三者间平衡，加入轻微随机性

用法示例：
  from core.strategy import StrategyManager, StrategyType
  
  # 获取当前策略
  current = StrategyManager.get_current_strategy()
  print(current.description)  # "我遵循队列顺序，每张图片都会被公平对待。"
  
  # 切换策略
  StrategyManager.set_strategy(StrategyType.AGGRESSIVE)
  print(StrategyManager.get_current_strategy().description)
  # "我现在更关心你正在看的和标记的照片。你的意图很重要。"

关键特性：
1. 策略切换本身是一个 STRATEGY_CHANGED 事件
2. 未来可对比"如果当时没有切策略，会怎样"
3. ToolPanel 可显示当前策略的自然语言描述

=============================================================================
三、数据库与生命周期追踪（data/database.py）
=============================================================================

扩展的 ImageRecord：
  created_at         - 被发现时的时间戳
  enqueued_at        - 进入队列时的时间戳
  dequeued_at        - 被选中时的时间戳
  infer_start_at     - 推理开始时的时间戳
  infer_end_at       - 推理完成时的时间戳
  write_back_at      - 结果写入时的时间戳
  marked_at          - 被标记时的时间戳
  
  visible_times      - 可见时段列表 [(enter, leave), ...]
  selection_context  - 被选中时的上下文（用于"为什么是它"）

计算属性：
  queue_age          - 在队列中的年龄（秒）
  infer_duration     - 推理耗时（秒）
  total_duration     - 从创建到完成的总耗时（秒）
  get_visibility_duration() - 总可见时长（秒）

用法示例：
  db = ImageDatabase()
  record = db.add("photo.jpg")
  
  # 自动跟踪生命周期
  record.enqueued_at = time.time()
  record.mark_as_important()
  
  print(f"队列中已等待 {record.queue_age} 秒")
  print(f"被可见 {record.get_visibility_duration()} 秒")

=============================================================================
四、自洽性测试（tests/test_narrative_consistency.py）
=============================================================================

这不是单元测试，而是"系统有没有对自己撒谎"的测试。

核心问题：
1. UI 上标记图片 → 事件日志中是否有 USER_MARK 事件？
2. Gallery 可见范围变化 → 是否产生 VISIBLE_ENTER/LEAVE 事件？
3. 策略切换 → 是否产生 STRATEGY_CHANGED 事件？
4. 系统"情绪"指示 → 是否真实反映了推理队列状态？
5. 生命周期叙述 → 是否连贯且有因果逻辑？
6. 事件日志 → 是否真的不可变？

运行测试：
  cd d:\Projects\PhotoCurator
  python -m tests.test_narrative_consistency

测试用例覆盖：
  ✓ test_01_user_mark_appears_in_events
  ✓ test_02_attention_window_triggers_event
  ✓ test_03_strategy_change_is_event
  ✓ test_04_mood_reflects_actual_state
  ✓ test_05_lifecycle_narrative_coherence
  ✓ test_06_event_log_immutability

=============================================================================
五、系统集成指南
=============================================================================

当前集成状态：
  ✓ 事件日志系统已实现（core/event_log.py）
  ✓ 策略对象化已实现（core/strategy.py）
  ✓ 数据库生命周期追踪已实现（data/database.py）
  ✓ 自洽性测试已实现（tests/test_narrative_consistency.py）
  ✓ StatusPanel/ToolPanel UI 已调整
  ✓ ImageItem 右键菜单预留了"为什么是它"接口
  
未来集成（可选）：
  □ 在 Scheduler 中使用策略对象计算优先级
  □ 在 Controller 边界层统一产生所有事件
  □ 启用右键菜单的"为什么是它"调试功能
  □ 实现时间回溯模式（对比不同策略下的行为差异）

=============================================================================
六、设计底线（不可违反）
=============================================================================

1. UI 不制造假因果
   → 所有"智能感"都能被追踪到具体的事件链
   → 心跳动画只在系统活跃时跳动（真的有事件产生）

2. 任何智能都可解释
   → 调度顺序可由事件日志回溯
   → 策略选择可通过生命周期叙述说明
   → "为什么是它"必须有数据支持（不是 AI 的黑魔法）

3. 用户行为永远比模型猜测更重要
   → 用户标记 > 视窗优先 > 队列顺序
   → 用户决定是"承诺"，不是"建议"

=============================================================================
七、未来展望
=============================================================================

短期（已预留接口）：
  • "为什么是它"调试面板
    → 右键点击图片
    → 显示完整生命周期和调度决策原因
    
中期（系统就绪）：
  • 时间回溯模式
    → 可重放历史推理过程
    → 对比不同策略下的行为差异
    
长期（高级应用）：
  • 调度策略学习
    → 根据用户反馈自动调整策略参数
    → 学到用户的"隐含偏好"
    
  • 多目标平衡
    → 在"效率"和"公平"间自动权衡
    → 可由用户通过对话调节

=============================================================================
结语

PhotoCurator 已从一个"图片管理器"演化为"自我叙事的 AI 推理系统"。

核心价值：
- 让用户看见系统在想什么（事件日志）
- 让系统有清晰的价值观（策略对象）
- 让一切都可被验证（自洽性测试）

这不是功能堆砌，而是架构思想的一次深化。

下一位维护者会感谢你。
"""
