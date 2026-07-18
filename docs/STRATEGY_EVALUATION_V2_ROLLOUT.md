# StrategyAgent & EvaluationAgent V2 分阶段优化记录

## 阶段 0：建立模拟质量基线 — 已完成

- 建立 36 个固定测试案例，覆盖 12 类核心场景。
- 复用 Simulation V2 的三类固定 Persona 和既有质量维度。
- 增加跨版本统一结果结构和汇总统计工具。
- 保存优化前的 Simulation V2 离线能力快照。
- 固化 Strategy、Simulation、Evaluation、Coach 的职责边界。
- 明确现有 Turn Decision Engine 与 Consistency Evaluator 的后续合并路线，避免重复功能并行。

## 阶段 1：重构 StrategyAgent Schema — 已完成

- 删除 `next_move`、`recommended_tone`、`candidate_message`、`alternative_messages`、`focus_points`、`avoid` 和 `risk_reminders`。
- 新增 `TargetResponseStrategyRequest`，只接收 Persona snapshot、关系状态、Session Memory、最近最多 6 条消息、用户最新发言和可选会话修正。
- 新增 `TargetInterpretation`、`ToneProfile` 和 `TargetResponsePolicy`。
- 支持 answer、acknowledge、clarification、accept、conditional accept、partial accept、refuse、challenge、boundary、defer、no reply 和 end conversation 共 12 类目标人物动作。
- Strategy Prompt 已改为目标人物视角，禁止用户建议、表达改写、候选话术和最终目标人物回复。
- Persona 和 Memory evidence refs 会和真实输入核对；不存在的引用会被移除并降低可解释性置信。
- `no_reply` 和 `end_conversation` 需要置信度不低于 0.8，并同时具有 Persona 和 Memory 证据；否则自动降级为 defer 或 set boundary。
- `/api/session/strategy` 保留原路径，但响应已替换为内部 Target Response Policy。
- 当前固定为 Shadow Mode，只生成安全元数据日志，不接入 Simulation 主回复。
- 阶段 1 新增 10 项专项测试；完成后全量后端测试为 75 项全部通过，前端生产构建通过。

### 阶段 1 去重说明

阶段 1 中新 Strategy Policy 与现有 Turn Decision Engine 的 Policy 仍同时存在于代码中，但不会同时驱动一轮回复：新 Strategy 只在独立 Shadow API 中运行，Simulation 主链路仍使用原 Decision Engine。阶段 2 接入时会迁移唯一 Policy 所有权，避免长期双决策。

### 阶段 1 仍需线上测量

离线测试已经验证 Schema、上下文差异、证据门槛、无 Coach 泄露和极端动作保护。Persona 差异敏感度、关系状态差异敏感度和极端 Action 误触发率仍需在预发布模型上使用阶段 0 的 36 个固定案例测量。

## 阶段 2：StrategyAgent 接入 SimulationAgent — 已完成

- V2 主链路已切换为 `StrategyAgent → Simulation Response Generator`。
- StrategyAgent 是唯一 Response Policy 决策者；SimulationAgentV2 已移除 Turn Decision Engine 依赖。
- 12 种 Strategy 动作通过一个显式适配层映射到现有 9 种 Simulation 可见行为。
- SessionMessageRequest 新增可选 `response_policy`；为空时内部运行 Strategy，提供时直接执行并跳过重复 Strategy 调用。
- Strategy 的 interpretation、action 和 confidence 通过保守规则生成状态变化，普通回合每项仍限制在 ±0.15，避免为状态更新增加第三次 LLM 调用。
- Simulation Generator 会接收 policy id、strategy action、required/forbidden content、tone profile 和 evidence refs。
- 拒绝动作若生成接受表达会自动纠正；clarification 最多一个问题；boundary 最长 100 字；no reply 强制空文本；short/brief 最长 60 字。
- Session 响应新增安全的 `strategy_meta`，可追踪 policy id、Strategy action、Simulation action、confidence、evidence refs、prompt version 和 fallback 状态。
- Strategy 失败时使用保守 acknowledge Policy，保持上一版状态不变并记录 fallback；Generator 仍最多重试一次。
- 阶段 2 的五类 Policy 执行契约离线通过率为 100%，高于 85% 验收线。
- 阶段 2 完成后全量后端测试为 80 项全部通过，前端生产构建通过。

### 阶段 2 去重结果

Turn Decision Engine 文件只作为旧版本回归参考保留，不再被 SimulationAgentV2 导入、实例化或调用。Policy 决策由 StrategyAgent 唯一负责；Simulation 只负责策略执行、具体措辞和状态落地。

### 阶段 2 仍需线上测量

离线约束可以阻止明显的拒绝反转、过长边界回复、多问题追问和错误静默文本。完整语义一致率仍需在预发布模型上运行阶段 0 的 36 个固定案例确认。

## 阶段 3：重构 EvaluationAgent — 已完成

- `/api/session/evaluate` 保留独立调用方式，不进入用户消息主链路，也不会增加普通聊天延迟。
- 输入升级为 `SimulationEvaluationRequest`，固定携带 trace/session/turn ID、Persona V2、评测前关系状态、Session Memory、最近消息、用户本轮发言、唯一 Strategy Policy、Simulation 结果及三个 Agent 的 Prompt 版本。
- Simulation 结果新增 `policy_id` 和 `used_evidence_refs`；若结果的 policy id 与本轮 Strategy Policy 不一致，Strategy Adherence 自动归零并阻止通过。
- 评价目标统一为“SimulationAgent 是否成功还原目标人物在当前情境下最合理、最一致的反应”，不再评估用户是否说服对方。
- 启用 Persona Fidelity 20%、Dyadic Consistency 15%、State Continuity 15%、Strategy Adherence 15%、Reaction Plausibility 15%、Style Fidelity 10%、Evidence Grounding 10% 七个维度。
- 综合分由后端按权重重新计算，不信任模型自行汇总的总分；无聊天记录时 Style 与 Evidence 权重各降至 5%，同时降低 Evaluation confidence。
- 删除 `pedagogical_value`、`responsiveness` 和面向用户的 `suggested_fixes`；改用 `critical_issues`、两类内部 correction、`session_learning_signals` 与 `evaluator_notes`。
- 新增 accept、accept_with_feedback、revise_simulation、replan_and_regenerate、insufficient_evidence 五类判定，以及 strategy、simulation execution、context gap、mixed 四类失败归因。
- 固化硬规则：Persona Fidelity 低于 60 不得接受；Strategy Adherence 低于 55 至少重生成；凭空创造人物特征时总分上限 59；明显上下文不足且 confidence 低于 0.6 时返回 insufficient evidence。
- correction 会按失败归因只路由给 Strategy 或 Simulation；Context Gap 不产生 correction，也不会自动修改 Persona。
- Prompt 和后处理共同阻止 Coach 泄露，不生成用户下一句、候选话术或目标人物最终回复。
- 阶段 3 新增 13 项专项测试；完成后全量后端测试为 93 项全部通过，前端生产构建通过。

### 阶段 3 去重结果

EvaluationAgent V2 已吸收旧 Consistency Evaluator 的 Persona、双人关系、状态/情绪连续性、风格、证据和反应比例判断，并扩展为统一七维质量模型。独立 Evaluation API 不调用旧 Consistency Evaluator，因此同一次评测只有一个评审者。阶段 4 已由 EvaluationAgent V2 替换在线旧一致性评审；旧实现仅保留为历史回归参考，不再被主链路导入、实例化或调用。

### 阶段 3 仍需线上测量

离线测试已验证 Schema、带权汇总、证据降权、硬性分数上限、失败归因、correction 路由、Policy 追踪和职责隔离。真实模型上的七维评分稳定性、归因准确率和跨 Prompt 版本漂移仍需使用阶段 0 的 36 个固定案例持续测量。

## 阶段 4：接入有限反馈循环 — 已完成

- V2 主链路升级为 `Strategy → Simulation candidate → Evaluation → 最多一次修正 → final response`，阶段 4 暂时采用每轮同步 Evaluation；普通轮异步优化留到阶段 6。
- `simulation_execution_error / revise_simulation` 保持原 Strategy Policy，只把 `correction_for_simulation` 传给 Response Generator 重生成一次。
- `strategy_error / replan_and_regenerate` 把 `correction_for_strategy` 传回 StrategyAgent，得到新 Policy 后再生成；Mixed 情况可在同一重规划周期把 Simulation correction 一并交给生成器。
- Strategy 与 Simulation 共享唯一 `InternalCorrection` 结构：`keep / change / must_not`，不再维护两套自由文本修正协议。
- 新增独立 `SimulationFeedbackLoop` 路由器，`MAX_FEEDBACK_CORRECTIONS = 1`；修正后的最终 Evaluation 即使仍低分，也只记录结果，不会启动第二轮反馈。
- 首次候选和修正候选采用事务式切换。修正调用失败时使用与最终 Policy 对齐的安全回退，不回退到已被 Evaluation 拒绝的候选。
- Evaluation 请求会携带实际 Policy ID、证据 refs、状态 delta 和三个 Prompt 版本；首次和最终评测使用不含原文的不同 candidate digest ID。
- Session 返回安全评测元数据：首次/最终分数、分差、判定、失败归因、反馈动作和一次重试统计；内部 correction 不暴露给用户主接口。
- Turn Store 只保存最终候选摘要，并新增初始/最终评分、反馈动作和丢弃标记；原始候选文本仍不落盘。
- MemoryAgent 只在整个反馈循环完成后运行并接收最终 target reply；被拒绝的首次候选不会进入 Memory。
- 在线旧 Consistency Evaluator 已从 SimulationAgentV2 移除，EvaluationAgent V2 是主链路唯一语义质量评审者。
- 阶段 4 新增 6 项专项测试；完成后全量后端测试为 99 项全部通过。

### 阶段 4 验收状态

- 单轮最大反馈次数、Strategy/Simulation 分流、失败候选隔离、最终候选 Memory 写入和无无限循环均已通过离线测试。
- 已记录 `initial_score`、`final_score`、`score_delta` 和 `feedback_retry_count`，可直接统计“修正后评分是否提升”和“总重试率”。
- “平均修正分明显高于首次输出”与“线上总重试率低于 15%”属于真实模型流量指标；需在预发布环境运行阶段 0 的 36 个固定案例和真实抽样后确认，不以单元测试伪造达标结论。

## 阶段 5：实现会话内学习 — 已完成

- 新增独立 `SimulationAdjustmentProfile`，只保存会话 ID、风格修正、策略修正、来源 Evaluation ID 和有效轮数；不复用 Persona、Memory 或聊天事实结构。
- EvaluationAgent 的 `session_learning_signals` 改为四类受控标识：回复过长、过度安慰、标点不匹配和过度配合；任意自由文本不会直接成为控制指令。
- 同一种受控问题必须在 3 个连续、置信度不低于 0.6 且非 Context Gap 的最终评估中出现，才会压缩成短期调整档案。
- 单次误判、未知信号、低置信度结果、Context Gap、Evaluation 调用失败或连续性中断都会清空当前累计，不修改 Persona。
- 调整档案只在激活后的 3 个回合生效，随后自动过期；过期后如需再次生效，必须重新满足连续 3 次条件。
- StrategyAgent 与 Simulation Response Generator 在同一回合读取同一份 typed profile：Strategy 负责限制默认配合和扩大承诺，Generator 负责长度、安慰、解释和标点等表达收紧。
- “回复过长”除 Prompt 约束外增加确定性的最多两句后处理，确保该类重复问题在激活后直接下降。
- 一次反馈修正后的会话学习只读取最终 Evaluation；最终评估失败时不会使用已被拒绝的首次候选信号学习。
- Session API 只返回是否应用、是否本轮激活、两类调整数量和剩余轮数，不暴露内部修正文本；Turn Store 同样只保存这些安全计数。
- 阶段 5 新增 4 项专项测试；完成后全量后端测试为 103 项全部通过，前端生产构建通过。

### 阶段 5 去重与数据边界

会话学习没有并入 PersonaAgent 或 MemoryAgent：Persona 继续只保存有证据支持的人物事实，Memory 继续只接收最终可见回复和会话事件；Adjustment Manager 只保存经过白名单压缩的临时控制信息。Strategy 决定行为，Simulation 执行语言表达，Evaluation 只负责产生评估信号，因此没有新增第二个决策者或第二个长期记忆源。

### 阶段 5 验收状态

- 连续 3 次触发、非连续问题重置、低置信度/Context Gap 阻断、未知指令过滤、后续 3 轮生效和自动过期均已通过离线测试。
- 已验证激活后的同一 Profile 同时进入 Strategy 与 Simulation，且原 Persona 对象和 Persona snapshot 不包含 adjustment 字段。
- “回复过长”已具备确定性两句限制；过度安慰、标点不匹配和过度配合的真实发生率下降幅度仍需在预发布环境使用阶段 0 固定案例和多轮真实模型样本测量。

## 阶段 6：异步评估与性能优化 — 已完成

- 未新增 FastEvaluator；同步与异步路径继续使用同一个 EvaluationAgent V2 和同一套七维评估标准。
- 新增 `EvaluationExecutionPolicy`。开发环境默认 `development_sync`，保留每轮同步评估和有限反馈循环；生产环境通过 `APP_ENV=production` 自动使用 `production_hybrid`，也可用 `EVALUATION_EXECUTION_MODE` 显式覆盖。
- 生产普通轮只执行 Strategy 与 Simulation 主回复链路，使用 FastAPI BackgroundTasks 在响应返回后运行 Evaluation；本轮回复不会等待后台评分，也不会被后台结果撤回。
- 以下关键条件继续在展示前同步 Evaluation：Strategy confidence 低于 0.70；refuse、set boundary、no reply、end conversation；状态变化达到大幅阈值；用户明显冒犯、威胁或强烈施压；Evaluation 已连续两轮指出同一受控问题。
- 关键轮仍沿用阶段 4 的最多一次修正；普通轮后台 Evaluation 只把学习信号写入后续 `SimulationAdjustmentProfile`，不修改已经返回的回复。
- Adjustment Manager 新增按会话回合排序的后台结果缓冲。即使多个后台 Evaluation 乱序完成，也会按原回合顺序更新连续问题计数；失败结果会以空观察结束该回合，避免永久等待或错误串联。
- Session Evaluation 元数据新增 execution mode、background scheduled 和 critical reasons；Turn Store 同步记录这些安全字段，不保存 Evaluation correction 或原始聊天内容。
- 新增 bounded `AgentRuntimeMetricsStore`，独立记录 StrategyAgent、Simulation Response Generator、EvaluationAgent 和 SimulationAgentV2 的版本、执行方式、耗时、成功状态、修正状态和评分变化。
- 新增 `GET /api/session/metrics` 聚合接口，返回每个 Agent/版本/执行方式的调用数、成功率、平均耗时、p95、修正次数和修正后提升次数，不返回 session/trace 明细。
- 阶段 6 新增 7 项专项测试；完成后全量后端测试为 110 项全部通过。

### 阶段 6 去重与运行边界

EvaluationAgent 仍是唯一语义质量评审者；Execution Policy 只决定运行时机，不评分、不生成 correction，也不修改 Policy。Strategy 仍是唯一行为决策者，Simulation 仍只执行策略。因此异步优化没有引入第二套快速评审器或重复决策层。

### 阶段 6 验收状态

- 已离线验证普通轮在 Evaluation 调用前返回候选、关键轮同步等待、后台成功率可聚合、连续问题触发关键轮、乱序后台结果正确回写、p95 计算和修正效果统计。
- 开发同步模式已通过全部旧阶段回归，行为与阶段 4/5 保持兼容。
- “普通轮用户感知延迟接近 Strategy + Simulation”和“线上 p95 在可接受范围”必须在预发布/生产真实模型与实际网络环境中读取 metrics 后确认；本阶段只完成调用路径和可观测能力，不用单元测试伪造线上延迟达标。
