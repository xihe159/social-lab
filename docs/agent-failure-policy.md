# Social Lab Agent Failure Policy

> 基于 2026-08-13 `main` 分支结构整理。目标是让失败语义由调用场景决定，而不是散落在各 Agent 的 `try/except` 中。

## 1. 统一模型

每一次 Agent 调用都声明一种 `AgentFailureMode`：

- `REQUIRED`：没有该结果就不能诚实完成当前工作流，失败必须终止并向 API 暴露稳定错误。
- `DEGRADED`：存在确定性、语义清晰的 fallback；LLM/超时/结构化输出失败时可继续，但必须记录 degradation。
- `BEST_EFFORT`：结果只用于审计、观测、异步学习等辅助能力；失败可跳过，不能改变当前用户结果。

错误统一分类为：

- `llm`
- `timeout`
- `invalid_output`
- `unexpected`

默认情况下，`unexpected` **即使发生在 DEGRADED/BEST_EFFORT 调用中也会升级为失败**，避免把代码 bug 静默伪装成“服务降级”。只有明确允许继续的辅助策略（例如 Strategy advisory、Evaluation audit、Safety LLM enrichment、Generator recovery）才设置 `fallback_on_unexpected=True`。

`asyncio.CancelledError` 永远透传，不得转换成 fallback 成功。

## 2. 当前推荐矩阵

| 调用场景 | 模式 | fallback / 行为 | 原因 |
|---|---|---|---|
| Session Safety 规则层 | REQUIRED | 无 | 本地规则安全底座不能缺失 |
| Safety LLM enrichment | DEGRADED | 规则结果 | LLM 只能补充，不能削弱规则风险 |
| Session Simulation core | REQUIRED | 无 | 没有人物回复就不能伪造成功轮次 |
| StateAgent in Session | DEGRADED | Simulation state_delta | State 是 enrichment，不应拖垮对话 |
| MemoryAgent in Session | DEGRADED | 上一轮 memory | Memory 可延迟更新 |
| V3 Strategy advisory | DEGRADED | neutral guidance | Strategy 不拥有可见回复 |
| V3 Evaluation audit | BEST_EFFORT | skip audit | 当前回复已经固定 |
| V2 Pipeline TurnAnalysis | DEGRADED | neutral turn state | 可以中性保持状态 |
| V2 Pipeline Decision | DEGRADED | guidance-based neutral decision | 保证决策结构存在 |
| V2 Generator 第一次 | BEST_EFFORT | retry once | 第一次失败触发一次受控恢复 |
| V2 Generator 第二次 | DEGRADED | deterministic response template | 最终保持 schema / action 一致 |
| Report PredictionAgent | DEGRADED | deterministic calculator | 成功率仍由确定性 calculator 所有 |
| Report AnalysisAgent | DEGRADED | neutral sentence analysis | 保留逐句结构，不编造语义结论 |
| Report RewriteAgent | DEGRADED | safe default rewrite | 维持报告 schema |
| `/api/session/strategy` | REQUIRED | 502/504/500 | 用户明确请求 Strategy 本身 |
| `/api/session/evaluate` | REQUIRED | 502/504/500 | 用户明确请求 Evaluation 本身 |
| `/api/persona/create` Persona | REQUIRED | 502/504/500 | 用户明确请求 Persona 本身 |

## 3. 调用方拥有失败语义

不要在通用 Agent 内写：

```python
try:
    return await llm()
except Exception:
    return fake_success
```

相同 Agent 在不同上下文中可能有不同语义。比如 Strategy：

- 在 Simulation 内是 advisory：`DEGRADED`；
- `/api/session/strategy` 是直接产品输出：`REQUIRED`。

因此策略集中在 `app/agents/failure_policies.py`，执行集中在 `app/core/agent_failure.py`。

## 4. API 错误契约

`AgentExecutionError` 只向 API 映射安全、稳定信息：

- timeout -> HTTP 504
- llm / invalid_output -> HTTP 502
- unexpected -> HTTP 500

不再把 provider exception message、prompt、用户文本或原始 payload 拼接到 `HTTPException.detail`。

## 5. Report 失败隔离

旧 `CoachAgent` 使用一个裸 `asyncio.gather(Prediction, Analysis)`；任意一个失败会让整个 report 失败。

新实现：

```text
Prediction --DEGRADED--\
                         +--> Rewrite --DEGRADED--> ReportAssembler
Analysis   --DEGRADED--/
```

每个 Agent 有自己的 deterministic fallback；`ReportAssembler` 始终保持确定性。

注意：`unexpected` 默认不会降级，因此代码错误仍会暴露出来，而不是被 neutral report 隐藏。

## 6. Session 失败传播

```text
Safety rule (REQUIRED)
  -> Safety LLM enrichment (DEGRADED)
  -> Simulation (REQUIRED)
  -> State (DEGRADED)
  -> Memory (DEGRADED)
```

`SessionExecutionContext.failures` 保存本轮降级记录，Session 最终日志使用 `success / degraded / blocked` 三种状态。

当前没有修改公开 `SessionMessageResponse` schema 来新增 failure 字段，避免前端/API 破坏性变更。需要前端展示“降级模式”时，下一步可以单独增加可选 `runtime_meta.agent_failures`，并做 schema versioning。

## 7. V3 的统一

主分支 V3 原先自己维护：

- Strategy `try/except + wait_for + fallback`
- Evaluation `try/except + swallow`

本补丁新增 `ResilientSimulationAgentV3`，保持 V3 业务行为不变，但将：

- V1 Simulation core -> REQUIRED
- Strategy -> DEGRADED + 3s timeout
- Evaluation -> BEST_EFFORT

全部路由到 `run_agent_call()`。

## 8. V2 Pipeline 累计修复

上一轮拆分后的 V2 pipeline 引用了 `services.py / runtime.py / utils.py`。本累计补丁补齐这三个文件，并把 TurnAnalysis / Strategy / Decision / Generation / Evaluation 的异常处理接入统一 failure runtime。

生产默认仍保持 `v3`；`v2_pipeline` 只用于开发和对照测试。

## 9. 不在 Agent runtime 重试 LLM

`run_agent_call()` 不做通用重试。原因：LLM client 本身应拥有 provider retry、structured-output repair 等底层策略；编排层再次自动重试会放大：

- 延迟
- token / 调用成本
- 非确定性
- 重复副作用

唯一保留的业务级重试是 V2 `ResponseGenerator` 的“同一 ResponsePolicy 下重生成一次”，因为这是明确的生成恢复策略，而不是通用网络重试。

## 10. 后续建议

下一阶段推荐增加：

1. `AgentFailure` 聚合指标：按 agent / kind / mode / fallback 统计；
2. 可选的 `runtime_meta.agent_failures`，让开发环境 UI 显示降级来源；
3. fault injection tests：模拟 Strategy timeout、State LLM failure、Memory failure、Evaluation background failure；
4. CI 规则：禁止 Agent 新增裸 `except Exception: return fallback`；
5. 将 V3 从 subclass 方式逐步迁入通用 pipeline stage，最终删除版本级重复编排。
