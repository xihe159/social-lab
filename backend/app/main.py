# social-lab/backend/app/main.py
# 2026/07/04

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.core.logging import configure_logging

from app.api.persona import router as persona_router
from app.api.session import router as session_router
from app.api.report import router as report_router
from app.api.strategy import router as strategy_router
from app.api.evaluation import router as evaluation_router
from app.api.user_data import router as user_data_router

try:
    from app.llm.client import LLMClientError
except ImportError:  # 兼容早期 llm/client.py
    class LLMClientError(RuntimeError):
        pass


try:
    from app.llm.client import LLM_MODEL_ID as ACTIVE_LLM_MODEL
except ImportError:
    try:
        from app.llm.client import LLM_MODEL as ACTIVE_LLM_MODEL
    except ImportError:
        ACTIVE_LLM_MODEL = "unknown"


try:
    from app.llm.client import generate_text
except ImportError:
    generate_text = None


class DebugChatRequest(BaseModel):
    system_prompt: str = Field(
        default="你是 Social Lab 的测试助手，请自然、灵活、具体地回答用户问题。",
        description="系统提示词",
    )
    user_message: str = Field(description="用户输入")
    temperature: float = Field(
        default=0.7,
        ge=0,
        le=1.5,
        description="回答随机性，越高越灵活",
    )


async def _call_debug_llm(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
) -> str:
    """
    Debug 专用的普通文本调用。

    优先使用新版 app.llm.client.generate_text；
    如果当前 llm/client.py 仍然是旧版，则兼容旧的 client + LLM_MODEL 写法。
    """

    if generate_text is not None:
        return await generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
        )

    try:
        from app.llm.client import get_async_client

        llm_client = get_async_client()
    except ImportError:
        from app.llm.client import client as llm_client

    response = await llm_client.chat.completions.create(
        model=ACTIVE_LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=temperature,
    )

    content: Optional[str] = response.choices[0].message.content
    return content or ""


def create_app() -> FastAPI:
    configure_logging("INFO")

    app = FastAPI(
        title="Social Lab Agent API",
        version="0.2.0",
        description="Social Lab 后端 Agent 稳定服务层 API",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://xihe159.github.io",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(persona_router)
    app.include_router(session_router)
    app.include_router(report_router)
    app.include_router(strategy_router)
    app.include_router(evaluation_router)
    app.include_router(user_data_router)

    @app.get("/")
    async def root():
        return {
            "message": "Social Lab Agent API is running",
            "version": "0.2.0",
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "service": "social-lab-agent-api",
        }

    @app.get("/api/debug/llm")
    async def debug_llm():
        try:
            content = await _call_debug_llm(
                system_prompt="你是一个测试助手，只返回一句中文。",
                user_prompt="请回复：LLM 接入成功。",
                temperature=0,
            )
            return {
                "ok": True,
                "model": ACTIVE_LLM_MODEL,
                "content": content,
            }
        except Exception as exc:
            return {
                "ok": False,
                "model": ACTIVE_LLM_MODEL,
                "error_type": exc.__class__.__name__,
                "error": str(exc),
            }

    @app.post("/api/debug/chat")
    async def debug_chat(request: DebugChatRequest):
        try:
            content = await _call_debug_llm(
                system_prompt=request.system_prompt,
                user_prompt=request.user_message,
                temperature=request.temperature,
            )
            return {
                "ok": True,
                "model": ACTIVE_LLM_MODEL,
                "content": content,
            }
        except Exception as exc:
            return {
                "ok": False,
                "model": ACTIVE_LLM_MODEL,
                "error_type": exc.__class__.__name__,
                "error": str(exc),
            }

    return app


app = create_app()
