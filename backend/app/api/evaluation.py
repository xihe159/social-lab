# social-lab/backend/app/api/evaluation.py
# 2026/07/01
#
# 新增内容：
# 1. POST /api/session/evaluate
# 2. 用于独立调用 EvaluationAgent 评估模拟质量
#
# 设计说明：
# - 先不把 EvaluationAgent 放入 /api/session/message 主链路。
# - 避免每次聊天额外增加一次 LLM 调用。
# - 前端或开发者可以在需要时按需调用本接口。

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.agents.evaluation_agent import EvaluationAgent
from app.llm.client import LLMClientError
from app.schemas.evaluation import EvaluationRequest, EvaluationResponse


router = APIRouter(prefix="/api/session", tags=["evaluation"])


@router.post(
    "/evaluate",
    response_model=EvaluationResponse,
    operation_id="evaluate_session_quality",
)
async def evaluate_session(request: EvaluationRequest):
    try:
        agent = EvaluationAgent()
        return await agent.run(request)

    except LLMClientError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"EvaluationAgent 调用 LLM 失败：{exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"EvaluationAgent 处理失败：{exc}",
        ) from exc
