# AnalysisAgent V3：逐句对话过程分析

## 1. 目标

AnalysisAgent V3 将报告拆成两个严格隔离的区域：

```text
AnalysisAgent
负责观察、状态归因和评价
不提供改进意见

RewriteAgent
负责逐句改写、综合话术、下一步和避免表达
```

逐句分析中不会出现：

```text
fix_direction
improvement_action
suggested_rewrite
next_step
```

## 2. 为什么句级状态变化采用“归因”而不是“直接测量”

当前 StateAgent 在每轮结束时只输出：

```text
relationship_delta
dynamics_delta
```

它没有为用户消息中的每个句子分别调用一次状态评估。

因此，系统不能声称某句话的状态变化是 StateAgent 独立测得的。

V3 的处理方法是：

1. StateAgent 提供该轮真实总增量；
2. AnalysisAgent 为每句话输出各指标的语义方向和强度；
3. SentenceAnalysisAllocator 使用 largest-remainder 算法分配整数增量；
4. 每个指标的所有句级增量之和严格等于整轮真实增量；
5. 报告明确标记为 `turn_delta_attribution`。

例如：

```text
整轮信任变化：-3

句 1 归因：+1
句 2 归因：-4

合计：-3
```

如果前端没有保存 ConversationTurnTrace，系统只展示语义评价，
不会伪造句级状态数值。

## 3. 逐句展示内容

每个用户句子输出：

```text
原句
沟通功能
表达意图
目标人物可能理解
目标人物可能感受
评价标签
评价分数
对目标的影响
评价依据
关系状态变化归因
Dynamics 变化归因
```

不包含任何“怎么改”或“下一步”。

## 4. 用户对话评价指标

报告输出六个分项和一个总分：

| 指标 | 含义 |
|---|---|
| clarity | 背景、请求、时间和方案是否清楚 |
| responsiveness | 是否回应目标人物已经表达的顾虑 |
| respect_and_boundary | 是否尊重选择权、拒绝权和关系距离 |
| responsibility | 是否承担自身责任并提供可执行承诺 |
| emotional_safety | 是否降低防御、羞耻、威胁和被迫感 |
| goal_alignment | 每句话是否服务于最初沟通目标 |
| overall | 综合评价 |

这些分数属于模拟对话评价，不是人格评价。

## 5. 数据流

```text
SessionMessageResponse
    ├─ relationship_before
    ├─ relationship_delta
    ├─ relationship_after
    ├─ dynamics_before
    ├─ dynamics_delta
    └─ dynamics_after
            ↓
前端保存 ConversationTurnTrace
            ↓
ReportRequest.turn_traces
            ↓
AnalysisAgent 逐句语义信号
            ↓
SentenceAnalysisAllocator
            ↓
ConversationProcessAnalysis
            ↓
报告的逐句过程区域
```

## 6. Agent 执行顺序

PredictionAgent 与 AnalysisAgent 互不依赖，因此并行执行：

```text
             ┌─ PredictionAgent ─┐
ReportRequest                    ├─ RewriteAgent ─ ReportAssembler
             └─ AnalysisAgent ───┘
```

RewriteAgent 等待两者完成后执行。

## 7. 规模限制

默认最多分析：

```text
20 个用户轮次
100 个用户句子
```

超过限制时，`coverage.complete` 为 false，报告会显示实际覆盖数量。

## 8. 安全和职责隔离

AnalysisAgent 的 prompt 和 schema 同时禁止改进字段。

后处理还会清除包含以下指令性词语的句段：

```text
建议
下一步
应该
应当
最好
不妨
可以改为
可改成
需要改成
改写为
```

所有改进只进入 RewriteAgent。
