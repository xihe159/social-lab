# social-lab/backend/app/api/strategy.py
# 2026/07/01
# StrategyAgent V2 Shadow Mode API。
# Endpoint:
#   POST /api/session/strategy
#
# 此接口只返回目标人物的内部 Response Policy，不影响 Simulation 主链路。

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.agents.strategy_agent import StrategyAgent
from app.llm.client import LLMClientError
from app.schemas.strategy import (
    TargetResponsePolicy,
    TargetResponseStrategyRequest,
)

router = APIRouter(prefix="/api/session", tags=["strategy"])

strategy_agent = StrategyAgent(mode="shadow")

@router.post("/strategy", response_model=TargetResponsePolicy)
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
