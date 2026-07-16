import os
from typing import Type, TypeVar

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel
from app.llm.structured_output import (
    StructuredOutputRepairError,
    validate_with_single_repair,
)


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

#G 20260629
def _make_strict_json_schema(schema: dict) -> dict:
    """
    将 Pydantic 生成的 JSON Schema 调整为 strict structured output 更容易接受的形式。

    主要处理：
    1. 所有 object 都显式 additionalProperties=false
    2. 所有 object 的 required 都包含 properties 中的全部字段
    3. 删除 default，避免部分兼容 OpenAI 的模型服务拒绝 schema
    4. 如果出现 $ref，则移除 description/title 等兄弟字段
    5. 递归处理 $defs、properties、items、anyOf、oneOf、allOf
    """

    if not isinstance(schema, dict):
        return schema

    # 关键修复：
    # 某些兼容 OpenAI 的服务不允许 $ref 与 description/title/default 等字段并存。
    # 例如：
    # {"$ref": "#/$defs/StateDelta", "description": "..."}
    # 会报错：$ref cannot have keywords {'description'}
    if "$ref" in schema:
        ref = schema["$ref"]
        schema.clear()
        schema["$ref"] = ref
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
#G 20260629 #

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

    async def repair_once(malformed_content: str) -> str:
        # Phase 8 reliability contract: exactly one structured JSON repair.
        # The malformed content is sent back to the same configured provider but
        # is never included in application logs or the final exception message.
        repair_prompt = (
            "请修复下面的模型输出，使其严格符合指定 JSON Schema。"
            "不得增加解释、Markdown 或 Schema 外字段，只返回修复后的 JSON。\n\n"
            f"待修复输出：\n{malformed_content}"
        )
        try:
            repaired_response = await client.chat.completions.create(
                model=LLM_MODEL_ID,
                messages=[
                    {
                        "role": "system",
                        "content": "你是结构化 JSON 修复器，只修复格式和字段合法性。",
                    },
                    {"role": "user", "content": repair_prompt},
                ],
                temperature=0,
                response_format=_build_json_schema_response_format(output_model),
            )
        except OpenAIError as repair_error:
            raise LLMClientError("LLM JSON repair 请求失败。") from repair_error

        repaired_content = repaired_response.choices[0].message.content
        if not repaired_content:
            raise LLMClientError("LLM JSON repair 返回内容为空。")
        return repaired_content

    try:
        return await validate_with_single_repair(
            content=content,
            output_model=output_model,
            repair=repair_once,
        )
    except StructuredOutputRepairError as exc:
        raise LLMClientError("LLM 结构化输出在一次 JSON repair 后仍未通过校验。") from exc
