# social-lab/backend/app/api/strategy.py
# 2026/07/01
# StrategyAgent V2.1 Guidance preview API。
# Endpoint:
#   POST /api/session/strategy
#
# 此接口只预览目标人物的内部 Response Guidance，不执行最终人物决策。

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.agents.strategy_agent import StrategyAgent
from app.llm.client import LLMClientError
from app.schemas.strategy import (
    TargetResponseGuidance,
    TargetResponseStrategyRequest,
)

router = APIRouter(prefix="/api/session", tags=["strategy"])

strategy_agent = StrategyAgent(mode="shadow")

@router.post("/strategy", response_model=TargetResponseGuidance)
async def create_strategy(request: TargetResponseStrategyRequest):
    try:
        return await strategy_agent.run(request)

    except LLMClientError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"StrategyAgent V2 调用 LLM 失败：{exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"StrategyAgent V2 处理失败：{exc}",
        ) from exc
