# social-lab-app.tsx 接入步骤

后端、API 和报告组件替换后，还需要在：

```text
components/social-lab/social-lab-app.tsx
```

保存 Dynamics 和 ConversationTurnTrace。

## 1. 修改 import

从 `@/lib/social-lab-api` 增加：

```ts
import {
  appendTurnTrace,
  buildDynamicsSnapshot,
  createPersona,
  createSimulationReport,
  sendSessionMessage,
} from "@/lib/social-lab-api";

import type {
  ConversationDynamics,
  ConversationDynamicsSnapshot,
} from "@/lib/social-lab-api";
```

从 `@/lib/social-lab-types` 增加：

```ts
import type {
  ChatMessage,
  ConversationTurnTrace,
  FormData,
  Persona,
  ScenarioKey,
  SimulationReport,
} from "@/lib/social-lab-types";
```

## 2. 增加状态

在组件其他 `useState` 附近增加：

```ts
const [currentDynamics, setCurrentDynamics] =
  useState<ConversationDynamics | null>(null);

const [dynamicsHistory, setDynamicsHistory] =
  useState<ConversationDynamicsSnapshot[]>([]);

const [turnTraces, setTurnTraces] =
  useState<ConversationTurnTrace[]>([]);

const [sessionMemory, setSessionMemory] =
  useState<Record<string, unknown> | null>(null);
```

## 3. 修改 sendSessionMessage 调用

原调用：

```ts
const result = await sendSessionMessage(
  scenario,
  form,
  persona,
  messages,
  text,
  simulationContext,
  personaV2,
);
```

替换为：

```ts
const result = await sendSessionMessage(
  scenario,
  form,
  persona,
  messages,
  text,
  simulationContext,
  personaV2,
  {
    currentDynamics,
    history: dynamicsHistory,
    turnTraces,
    memory: sessionMemory,
  },
);
```

## 4. 保存本轮轨迹

在成功获得 `result` 后增加：

```ts
setCurrentDynamics(result.currentDynamics);
setSessionMemory(result.updatedMemory);

if (
  result.currentDynamics &&
  result.turnTrace
) {
  setDynamicsHistory((current) => [
    ...current,
    buildDynamicsSnapshot(
      result.currentDynamics,
      result.turnTrace.turnIndex,
    ),
  ].slice(-10));
}

if (result.turnTrace) {
  setTurnTraces((current) =>
    appendTurnTrace(
      current,
      result.turnTrace,
      20,
    ),
  );
}
```

## 5. 修改报告请求

原调用：

```ts
const nextReport = await createSimulationReport(
  scenario,
  form,
  persona,
  messages,
);
```

替换为：

```ts
const nextReport = await createSimulationReport(
  scenario,
  form,
  persona,
  messages,
  {
    currentDynamics,
    history: dynamicsHistory,
    turnTraces,
    memory: sessionMemory,
  },
);
```

## 6. 重置会话时清空轨迹

在以下流程中都增加清空操作：

- 切换场景；
- 重新生成 Persona；
- 重新开始对话。

```ts
setCurrentDynamics(null);
setDynamicsHistory([]);
setTurnTraces([]);
setSessionMemory(null);
```

## 7. 注意 React 状态时序

`sendSessionMessage` 返回的 `turnTrace` 已经包含：

```text
用户消息
目标人物回复
关系状态 before / delta / after
Dynamics before / delta / after
risk_flags
```

不要在页面中重新计算这些增量，只需要保存后回传。

## 8. 验证

完成后，在浏览器 Network 中检查 `/api/session/report` 请求：

```json
{
  "current_dynamics": {},
  "dynamics_history": [],
  "turn_traces": [
    {
      "turn_index": 1,
      "user_message": "...",
      "target_reply": "...",
      "relationship_before": {},
      "relationship_delta": {},
      "relationship_after": {},
      "dynamics_before": null,
      "dynamics_delta": {},
      "dynamics_after": {},
      "risk_flags": []
    }
  ]
}
```

若 `turn_traces` 为空，报告仍能显示逐句语义分析，
但句级状态区域会显示“无轨迹”，不会生成虚假数值。
