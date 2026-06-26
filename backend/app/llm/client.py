import os
import json
from typing import Type, TypeVar

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel, ValidationError


load_dotenv()

T = TypeVar("T", bound=BaseModel)


LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL_ID = os.getenv("LLM_MODEL_ID", "gpt-4.1-mini")


class LLMClientError(RuntimeError):
    """LLM 客户端统一异常。"""


def get_async_client() -> AsyncOpenAI:
    if not LLM_API_KEY:
        raise LLMClientError(
            "缺少环境变量 LLM_API_KEY，请在 backend/.env 中配置。"
        )

    return AsyncOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL or None,
        timeout=60,
        max_retries=1,
    )


def _ensure_additional_properties_false(schema: dict) -> dict:
    """
    OpenAI / 兼容 OpenAI 的 structured output 严格模式要求：
    每一个 object 类型的 JSON Schema 都必须显式声明 additionalProperties: false。

    这个函数会递归处理：
    - 根对象
    - properties 中的嵌套对象
    - $defs 中的复用对象
    - items 中的数组元素对象
    """

    if not isinstance(schema, dict):
        return schema

    if schema.get("type") == "object":
        schema.setdefault("additionalProperties", False)

    properties = schema.get("properties")
    if isinstance(properties, dict):
        for value in properties.values():
            _ensure_additional_properties_false(value)

    defs = schema.get("$defs")
    if isinstance(defs, dict):
        for value in defs.values():
            _ensure_additional_properties_false(value)

    definitions = schema.get("definitions")
    if isinstance(definitions, dict):
        for value in definitions.values():
            _ensure_additional_properties_false(value)

    items = schema.get("items")
    if isinstance(items, dict):
        _ensure_additional_properties_false(items)

    for key in ("anyOf", "oneOf", "allOf"):
        values = schema.get(key)
        if isinstance(values, list):
            for value in values:
                _ensure_additional_properties_false(value)

    return schema


def _make_strict_json_schema(schema: dict) -> dict:
    """
    将 Pydantic 生成的 JSON Schema 调整为 strict structured output 更容易接受的形式。

    主要处理：
    1. 所有 object 都显式 additionalProperties=false
    2. 所有 object 的 required 都包含 properties 中的全部字段
    3. 删除 default，避免部分兼容 OpenAI 的模型服务拒绝 schema
    4. 递归处理 $defs、properties、items、anyOf、oneOf、allOf
    """

    if not isinstance(schema, dict):
        return schema

    schema.pop("default", None)

    if schema.get("type") == "object":
        properties = schema.get("properties")

        schema["additionalProperties"] = False

        if isinstance(properties, dict):
            schema["required"] = list(properties.keys())

    properties = schema.get("properties")
    if isinstance(properties, dict):
        for value in properties.values():
            _make_strict_json_schema(value)

    defs = schema.get("$defs")
    if isinstance(defs, dict):
        for value in defs.values():
            _make_strict_json_schema(value)

    definitions = schema.get("definitions")
    if isinstance(definitions, dict):
        for value in definitions.values():
            _make_strict_json_schema(value)

    items = schema.get("items")
    if isinstance(items, dict):
        _make_strict_json_schema(items)

    for key in ("anyOf", "oneOf", "allOf"):
        values = schema.get(key)
        if isinstance(values, list):
            for value in values:
                _make_strict_json_schema(value)

    return schema


def _build_json_schema_response_format(output_model: Type[BaseModel]) -> dict:
    schema = output_model.model_json_schema()
    schema = _make_strict_json_schema(schema)

    return {
        "type": "json_schema",
        "json_schema": {
            "name": output_model.__name__,
            "strict": True,
            "schema": schema,
        },
    }


async def generate_text(
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.4,
) -> str:
    """
    普通文本生成接口。
    适用于后续不要求结构化输出的场景。
    """

    client = get_async_client()

    try:
        response = await client.chat.completions.create(
            model=LLM_MODEL_ID,
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
    except OpenAIError as exc:
        raise LLMClientError(f"LLM 请求失败：{exc}") from exc

    content = response.choices[0].message.content

    if not content:
        raise LLMClientError("LLM 返回内容为空。")

    return content


async def generate_structured(
    *,
    system_prompt: str,
    user_prompt: str,
    output_model: Type[T],
    temperature: float = 0.3,
) -> T:
    """
    结构化生成接口。

    所有 Agent 推荐优先使用这个函数：
    - PersonaAgent 返回 PersonaCreateResponse
    - SimulationAgent 返回 SimulationReply
    - CoachAgent 返回 ReportResponse

    该函数会：
    1. 使用 json_schema 约束模型输出
    2. 获取模型返回的 JSON 字符串
    3. 使用 Pydantic 再次校验
    4. 返回稳定的 Pydantic 对象
    """

    client = get_async_client()

    try:
        response = await client.chat.completions.create(
            model=LLM_MODEL_ID,
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
            response_format=_build_json_schema_response_format(output_model),
        )
    except OpenAIError as exc:
        raise LLMClientError(f"LLM 结构化请求失败：{exc}") from exc

    content = response.choices[0].message.content

    if not content:
        raise LLMClientError("LLM 结构化返回内容为空。")

    try:
        return output_model.model_validate_json(content)
    except ValidationError as exc:
        raise LLMClientError(
            f"LLM 返回内容未通过 Pydantic 校验：{exc}\n原始返回：{content}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise LLMClientError(
            f"LLM 返回内容不是合法 JSON：{exc}\n原始返回：{content}"
        ) from exc
