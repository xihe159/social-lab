# SimulationAgent V3

V3 的目标是保留第一版人物模拟的自然度，同时保留 StrategyAgent 和
EvaluationAgent 的分析价值，并彻底取消它们对当轮人物回复的控制权。

## 正式链路

1. SafetyAgent 先完成安全检查。
2. 原始 V1 SimulationAgent 根据 Persona、关系状态、历史和用户输入生成回复。
   若用户上传过真实聊天记录，V1 同时读取其中的沟通风格、高置信行为模式和
   有界证据摘要；这些内容只描述观察特征，不包含动作命令。
3. StrategyAgent 与 Simulation 并行生成非约束性 Guidance；它的标签不会进入
   Simulation 提示词，也不能修改动作、语气、长度或文本。
4. StateAgent 只补充对话 Dynamics 与风险，不覆盖 Simulation 的关系变化。
5. EvaluationAgent 在回复固定后后台审计，只记录人物一致性问题，不重生成当前回复。
6. MemoryAgent 只接收最终已经展示给用户的回复。

人物证据优先级固定为：真实聊天观察与稳定 Persona > 当前关系和真实对话历史
> Session Memory。Memory 只能维护本次会话连续性；AI 模拟生成的目标人物回复
会被标记为 `SIMULATED_TARGET_REPLY`，不得反向升级成稳定人物风格或长期行为证据。

## 版本规则

- `v3`：正式默认版本。
- `v1`：紧急回退版本。
- `v2` / `v2.1`：已退出正式链路；新版后端启动时自动映射到 `v3`。

Render 应设置：

```text
SIMULATION_AGENT_VERSION=v3
APP_ENV=production
```

旧 Render 环境里即使暂时仍是 `v2.1`，部署新版代码后也不会再触发 Pydantic
版本校验失败；但仍建议将变量明确改成 `v3`，避免配置含义不清。
