# social-lab/backend/app/main.py
# 2026/07/28

from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.api.evaluation import router as evaluation_router
from app.api.persona import router as persona_router
from app.api.report import router as report_router
from app.api.session import router as session_router
from app.api.strategy import router as strategy_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.llm.client import close_async_client, generate_text


logger = logging.getLogger(__name__)


class DebugChatRequest(BaseModel):
    system_prompt: str = Field(
        default="你是 Social Lab 的测试助手，请自然、灵活、具体地回答用户问题。",
        description="系统提示词",
    )

    user_message: str = Field(
        min_length=1,
        description="用户输入",
    )

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
    Debug 专用普通文本调用。

    统一使用 app.llm.client.generate_text，
    不再维护旧客户端兼容分支。
    """

    return await generate_text(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
    )


def create_app(
    settings_override: Settings | None = None,
) -> FastAPI:
    """
    创建 FastAPI 应用。

    settings_override 主要用于测试：
    测试代码可以直接传入一份临时配置，
    不需要修改真实的 backend/.env。
    """

    settings = settings_override or get_settings()

    # 日志必须尽量早配置
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info(
            "application_started",
            extra={
                "app_name": settings.app_name,
                "app_version": settings.app_version,
                "app_env": settings.app_env,
                "log_level": settings.log_level,
                "llm_model_id": settings.llm_model_id,
                "simulation_agent_version": (
                    settings.simulation_agent_version
                ),
                "debug_endpoints_enabled": (
                    settings.debug_endpoints_enabled
                ),
            },
        )

        try:
            yield
        finally:
            # 关闭共享的 OpenAI/httpx 客户端
            await close_async_client()

            logger.info(
                "application_stopped",
                extra={
                    "app_name": settings.app_name,
                    "app_env": settings.app_env,
                },
            )

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        lifespan=lifespan,
    )

    # 方便依赖、测试和调试代码读取配置
    app.state.settings = settings

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_method_list,
        allow_headers=settings.cors_header_list,
    )

    # ------------------------------------------------------------------
    # 业务路由
    # ------------------------------------------------------------------

    app.include_router(persona_router)
    app.include_router(session_router)
    app.include_router(report_router)
    app.include_router(strategy_router)
    app.include_router(evaluation_router)

    # ------------------------------------------------------------------
    # 基础接口
    # ------------------------------------------------------------------

    @app.get("/")
    async def root():
        return {
            "message": f"{settings.app_name} is running",
            "version": settings.app_version,
            "environment": settings.app_env,
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "service": "social-lab-agent-api",
            "version": settings.app_version,
            "environment": settings.app_env,
        }

    # ------------------------------------------------------------------
    # Debug 接口
    # ------------------------------------------------------------------

    if settings.debug_endpoints_enabled:

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
                    "model": settings.llm_model_id,
                    "content": content,
                }

            except Exception as exc:
                logger.exception(
                    "debug_llm_call_failed",
                    extra={
                        "error_type": exc.__class__.__name__,
                        "llm_model_id": settings.llm_model_id,
                    },
                )

                # 不再把 str(exc) 直接返回给前端
                raise HTTPException(
                    status_code=502,
                    detail="LLM 调用失败，请查看后端日志。",
                ) from exc

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
                    "model": settings.llm_model_id,
                    "content": content,
                }

            except Exception as exc:
                logger.exception(
                    "debug_chat_call_failed",
                    extra={
                        "error_type": exc.__class__.__name__,
                        "llm_model_id": settings.llm_model_id,
                    },
                )

                raise HTTPException(
                    status_code=502,
                    detail="LLM 调用失败，请查看后端日志。",
                ) from exc

    return app


app = create_app()
