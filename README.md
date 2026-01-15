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
│
├─ app.py                 # 程序入口，初始化 UI / Core / Database / Worker
├─ export_weights.py      # PyTorch 模型权重导出为二进制
│
├─ core/                  # 核心推理与调度逻辑
│   ├─ engine.py          # 推理引擎（InferenceEngine）
│   ├─ operators.py       # 基础算子（linear, relu, l2_normalize）
│   └─ scheduler.py       # 优先级调度器（PriorityScheduler）
├─ data/                  # 数据管理
│   ├─ database.py        # 图片记录与状态管理（ImageDatabase）
│   └─ weight_loader.py   # 权重加载（load_weights）
│   └── test_photo/        # 测试图片
├── requirements.txt
└─ ui/                    # 界面相关
    ├─ main_window.py     # 主窗口 MainWindow
    ├─ controller.py      # UIController + InferenceWorker
    └─ components/        # UI 组件
        ├─ gallery.py     # 瀑布流/网格图片展示
        ├─ image_item.py  # 单个图片项绘制
        ├─ status_panel.py# 系统状态面板（总数/Pending/Running/Done）
        └─ tool_panel.py  # 调度器参数控制面板（viewport / intent）
```

---