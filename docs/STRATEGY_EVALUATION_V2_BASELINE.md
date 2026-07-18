# StrategyAgent & EvaluationAgent V2 — 阶段 0 质量基线

## 本阶段结果

阶段 0 固定了 36 个可重复测试案例，覆盖 PRD 要求的 12 类场景：正常回应、用户请求、用户道歉、推卸责任、不礼貌、连续施压、高信任、低信任、接受、拒绝、设置边界和暂不回复。

案例继续复用 Simulation Agent V2 已有的三类固定人物：直接且责任导向的导师、高回避的温和朋友、敏感的亲密伴侣。没有新建第二套 Persona 测试数据。

机器可读案例位于 `backend/evaluation/strategy_evaluation_baseline_cases.json`。统计工具位于 `backend/evaluation/strategy_evaluation_baseline.py`。每个后续版本必须使用完整的同一组 case id，不能只选择表现较好的案例。

## 固定记录字段

每个案例的版本结果统一记录：

1. 目标人物回复内容；
2. 选定的反应动作；
3. Persona 一致性；
4. 关系连续性；
5. 风格一致性；
6. 人工总评；
7. 单轮延迟；
8. 使用的证据引用；
9. 评审备注。

汇总结果统一计算平均 Persona 一致性、平均关系连续性、平均风格一致性、平均人工总评、平均延迟、p95 延迟、动作契约通过率、静默动作通过率和证据引用通过率。

## 当前版本快照

阶段 0 的起点是提交 `5f1703c` 中已经完成的 Simulation Agent V2。当前可确定的离线能力包括：9 种回复动作、6 组固定回归套件、普通状态变化上限 0.15、重大事件上限 0.25、生成最多重试一次，以及不持久化原始敏感文本。

这些离线结果不能代替真实模型表现和人工评分。当前 live model 分数在 `backend/evaluation/strategy_evaluation_phase0_snapshot.json` 中明确标记为 `pending_staging_run_and_human_review`，避免用自动化分数冒充人工结论。上线前必须用同一批 36 个案例补齐真实回复、人工评分和延迟。

本阶段完成后，全量后端自动化测试为 65 项全部通过，前端生产构建通过。

## 职责去重基线

后续阶段遵循以下唯一职责归属：

- Strategy Agent：唯一负责目标人物的本轮理解、动作、反应目标、内容边界和语气范围。
- Simulation Agent：唯一负责把已确定的 Policy 变成目标人物的具体语言，并输出状态变化。
- Evaluation Agent：唯一负责完整模拟质量评分、失败归因和修正路由。
- Existing Consistency Evaluator：不作为第二套评审器长期并存；其关键轮触发和一致性检查能力将合并进 Evaluation Agent V2。
- Existing Turn Decision Engine：不再长期持有 Response Policy 决策权；阶段 2 接入时迁移该职责，保留必要的状态计算工具。
- Coach Agent：不修改，继续负责用户沟通表现和建议，不进入人物模拟评分。

## 阶段 0 验收

- 固定案例不少于 30 个：已完成，当前为 36 个。
- 覆盖 PRD 的全部 12 类场景：已完成。
- 同一案例集可供所有后续版本运行：已完成。
- 无用户候选话术、沟通建议或 Coach 字段：已完成。
- 极端动作只在高冲突或重复施压案例中允许：已完成。
- 关键决策要求 evidence refs：已完成。
