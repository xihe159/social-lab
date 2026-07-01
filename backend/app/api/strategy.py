# social-lab/backend/app/api/strategy.py
# 2026/07/01
# 新增内容：StrategyAgent API 路由。
# Endpoint:
#   POST /api/session/strategy

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.agents.strategy_agent import StrategyAgent
from app.llm.client import LLMClientError
from app.schemas.strategy import StrategyAdviceRequest, StrategyAdviceResponse

router = APIRouter(prefix="/api/session", tags=["strategy"])


@router.post("/strategy", response_model=StrategyAdviceResponse)
async def create_strategy(request: StrategyAdviceRequest):
    try:
        agent = StrategyAgent()
        return await agent.run(request)

    except LLMClientError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"StrategyAgent 调用 LLM 失败：{exc}",
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"StrategyAgent 处理失败：{exc}",
        ) from exc
