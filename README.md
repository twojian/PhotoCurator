## 项目背景

在真实的摄影工作流中，一次拍摄往往会产生数千张图片。

摄影师需要在有限时间内完成 **快速浏览 → 相似对比 → 人工筛选 → 最终交付** 的完整流程。

现有的 “AI 自动分类/打标签” 工具存在三个问题：

1. **审美主观性强**：好片与否高度依赖个人判断
2. **黑箱决策**：AI 给出结论但无法解释，也无法反驳
3. **工程不稳定**：模型慢、误判或不可用会直接破坏使用体验

本项目并不尝试“让 AI 替摄影师选片”，而是探索一个更克制、也更工程化的问题：

> 在 AI 不完美的前提下，如何设计一个尊重人类决策、且在资源受限环境中依然可靠的图片分类系统？
> 

---

## 设计目标

- **人是决策中心**：AI 只提供参考，不做最终判断
- **本地优先**：不依赖云服务即可完整使用
- **体验可预测**：浏览与人工操作不被 AI 阻塞
- **复杂性可控**：刻意限制功能范围，避免过度设计

---

## 核心设计原则

### 1. 人在回路（Human-in-the-loop）

人工筛选是主流程，AI 永远是旁路。

- AI 结果不会覆盖人工标记
- 人工操作不依赖 AI 是否完成
- AI 失败 ≠ 系统不可用

**工程权衡**：

牺牲部分“自动化程度”，换取系统可控性与信任感。

---

### 2. AI 异步、可失效

AI 分析在后台异步执行：

- 不阻塞 UI
- 结果允许延迟
- 失败可忽略、可重试

**工程权衡**：

接受“智能不即时”，换取稳定的交互体验。

---

### 3. 相似性优先，而非语义分类

V1 中 AI 的核心职责只有一个：

> 发现“看起来相似的图片”，减少人工重复比较的认知成本。
> 

系统刻意避免让 AI 判断“好 / 坏 / 可交付”。

**工程权衡**：

牺牲“看起来很聪明”的结论，换取更符合摄影实际的辅助价值。

---

## 系统架构（V1）

```markdown
UI / Viewer
  ├─ 图片浏览（主流程）
  ├─ 人工标记（保留 / 淘汰 / 待定）
  └─ AI 结果展示（参考）

Core Application
  ├─ 图片索引管理
  ├─ 缓存与内存控制
  └─ 人工决策状态管理

LocalStorage
  ├─ 原始图片（只读）
  ├─ 缩略图缓存
  └─ 图片特征（embedding）

AI Analysis Worker（异步）
  ├─ 特征提取
  ├─ 相似度计算
  └─ 聚类结果生成
```
```markdown
PhotoCurator/
├── app.py
│   # 应用入口
│   # 生命周期装配：UI / Core / Data / Worker
│   # 不含业务逻辑，仅负责编排与启动
│
├── export_weights.py
│   # 离线工具：导出 / 固化模型权重
│
├── weights.bin
│   # 推理权重（二进制，运行期只读加载）
│
├── photocurator_config.json
│   # 用户意图与系统偏好配置（运行期生成/更新）
│
├── core/
│   ├── __init__.py
│   │
│   ├── engine.py
│   │   # InferenceEngine
│   │   # 受控感知管道（Embedding 推理）
│   │   # 明确区分：感知 ≠ 决策 ≠ 价值
│   │
│   ├── operators.py
│   │   # 纯算子层（linear / relu / normalize）
│   │   # 无策略、无状态、无智能
│   │
│   ├── scheduler.py
│   │   # PriorityScheduler
│   │   # 任务选择机制（attention / intent / age）
│   │   # 执行“如何选”，不决定“为什么选”
│   │
│   ├── strategy.py
│   │   # StrategyManager / StrategyType
│   │   # 系统价值立场（调度哲学）
│   │   # 策略切换是系统级事件
│   │
│   └── event_log.py
│       # EventLog / EventType
│       # 系统唯一“事实来源”
│       # 不可变事件 + 生命周期叙述
│
├── data/
│   ├── __init__.py
│   │
│   ├── database.py
│   │   # ImageDatabase / ImageRecord
│   │   # 图片事实状态（存在 / 标记 / 可见 / 推理阶段）
│   │
│   ├── weight_loader.py
│   │   # 权重加载与校验
│   │
│   ├── test_photo/
│   │   # 本地测试图片（开发期）
│   │
│   └── thumb_cache/
│       # 缩略图缓存（运行期生成，可清空）
│
├── ui/
│   ├── __init__.py
│   │
│   ├── main_window.py
│   │   # 主窗口
│   │   # 三栏结构装配（状态 / 画廊 / 工具）
│   │
│   ├── controller.py
│   │   # UIController
│   │   # 人机信号中枢：UI ↔ Scheduler ↔ Database ↔ EventLog
│   │
│   │   # InferenceWorker
│   │   # 后台推理线程（QThread）
│   │
│   └── components/
│       ├── __init__.py
│       │
│       ├── status_panel.py
│       │   # 系统意识层（System Consciousness）
│       │   # 情绪推断 / 心跳动画 / 策略叙述 / 时间轴
│       │
│       ├── gallery.py
│       │   # 世界投影层（World Projection）
│       │   # Attention Window / 可见性计算
│       │
│       ├── image_item.py
│       │   # 单图节点
│       │   # 状态机 + 延迟加载 + 用户交互
│       │
│       └── tool_panel.py
│           # 人类意图层（Human Intent）
│           # Viewport Boost / Intent Boost / 配置持久化
│
├── test/
│   ├── __init__.py
│   │   # 测试套件入口
│   │
│   └── test_narrative_consistency.py
│       # Narrative Consistency Tests
│       # 系统自洽性 / 诚实性 / 不自欺测试
│       # 验证 UI 叙述是否与系统事实一致
│
└── logs/   （可选）
    └── photocurator.log
        # 运行期日志（调试 / 回放 / 审计）
```

---
