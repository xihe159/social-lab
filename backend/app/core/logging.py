# backend/app/core/logging.py

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


_RESERVED_LOG_RECORD_KEYS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
}


def _json_safe(value: Any) -> Any:
    """
    保证 extra 里的复杂对象可以被 json.dumps 序列化。
    """
    try:
        json.dumps(value, ensure_ascii=False)
        return value
    except TypeError:
        return str(value)


class JsonFormatter(logging.Formatter):
    """
    把日志输出成一行 JSON，方便后续在 Render / Docker / 日志平台中检索。
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 把 logger.info(..., extra={...}) 里的字段也写入 JSON
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_RECORD_KEYS and not key.startswith("_"):
                log_data[key] = _json_safe(value)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    """
    全局配置 logging。
    注意：只需要在 FastAPI 应用启动时调用一次。
    """
    root_logger = logging.getLogger()

    # 避免 uvicorn reload 或重复 import 时重复添加 handler
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root_logger.addHandler(handler)
    root_logger.setLevel(level.upper())

    # 可选：降低第三方库日志噪音
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)