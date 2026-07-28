# backend/app/core/config.py

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# config.py 位于 backend/app/core/config.py
# parents[0] = core
# parents[1] = app
# parents[2] = backend
BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """
    Social Lab 后端统一配置。

    配置来源优先级：
    1. 操作系统环境变量
    2. backend/.env
    3. 本文件中的默认值
    """

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # 应用基础配置
    # ------------------------------------------------------------------

    app_name: str = "Social Lab Agent API"
    app_version: str = "0.2.0"
    app_description: str = "Social Lab 后端 Agent 稳定服务层 API"

    app_env: Literal[
        "development",
        "test",
        "staging",
        "production",
    ] = "development"

    # ------------------------------------------------------------------
    # 日志配置
    # ------------------------------------------------------------------

    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = "INFO"

    # ------------------------------------------------------------------
    # Debug 接口配置
    # ------------------------------------------------------------------

    # 默认关闭，开发环境通过 .env 显式打开
    debug_endpoints_enabled: bool = False

    # ------------------------------------------------------------------
    # CORS 配置
    # ------------------------------------------------------------------

    # 使用逗号分隔，便于在 .env、Render、Docker 等环境中配置
    cors_origins: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "https://xihe159.github.io"
    )

    cors_allow_credentials: bool = True
    cors_allow_methods: str = "*"
    cors_allow_headers: str = "*"

    # ------------------------------------------------------------------
    # LLM 配置
    # ------------------------------------------------------------------

    # SecretStr 能降低 API Key 被日志或 repr 意外打印的风险
    llm_api_key: SecretStr | None = None

    # 留空时使用 OpenAI SDK 默认地址
    llm_base_url: str | None = None

    llm_model_id: str = Field(
        default="gpt-4.1-mini",
        min_length=1,
    )

    llm_timeout_seconds: float = Field(
        default=60.0,
        gt=0,
        le=600,
    )

    llm_max_retries: int = Field(
        default=1,
        ge=0,
        le=10,
    )

    # ------------------------------------------------------------------
    # Agent 功能开关
    # ------------------------------------------------------------------

    simulation_agent_version: Literal["v1", "v2"] = "v1"

    # 暂时保留为字符串，兼容项目现有执行模式
    evaluation_execution_mode: str = "development_sync"

    # ------------------------------------------------------------------
    # 字段规范化
    # ------------------------------------------------------------------

    @field_validator("app_env", mode="before")
    @classmethod
    def normalize_app_env(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("llm_base_url", mode="before")
    @classmethod
    def normalize_llm_base_url(cls, value: object) -> object:
        """
        允许在 .env 中使用：

        LLM_BASE_URL=

        空字符串会被转换为 None。
        """

        if value is None:
            return None

        normalized = str(value).strip()
        return normalized or None

    @field_validator("llm_model_id", mode="before")
    @classmethod
    def normalize_llm_model_id(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    # ------------------------------------------------------------------
    # CORS 辅助属性
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_csv(value: str) -> list[str]:
        return [
            item.strip()
            for item in value.split(",")
            if item.strip()
        ]

    @property
    def cors_origin_list(self) -> list[str]:
        """
        将逗号分隔的 Origin 转成 CORSMiddleware 所需的列表。

        Origin 不能带末尾的 /，因此这里统一清理。
        """

        return [
            origin.rstrip("/")
            for origin in self._parse_csv(self.cors_origins)
        ]

    @property
    def cors_method_list(self) -> list[str]:
        methods = self._parse_csv(self.cors_allow_methods)

        return [
            method if method == "*" else method.upper()
            for method in methods
        ]

    @property
    def cors_header_list(self) -> list[str]:
        return self._parse_csv(self.cors_allow_headers)

    # ------------------------------------------------------------------
    # LLM 辅助方法
    # ------------------------------------------------------------------

    def get_llm_api_key(self) -> str:
        """
        返回真实 API Key。

        只有在真正调用 LLM 时才检查，避免没有配置模型时
        整个 FastAPI 应用无法启动。
        """

        if self.llm_api_key is None:
            raise ValueError(
                "缺少环境变量 LLM_API_KEY，请在 backend/.env 中配置。"
            )

        api_key = self.llm_api_key.get_secret_value().strip()

        if not api_key:
            raise ValueError(
                "环境变量 LLM_API_KEY 不能为空。"
            )

        return api_key


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    每个 Python 进程只创建一个 Settings 实例。

    修改 .env 后需要重启后端进程。
    """

    return Settings()