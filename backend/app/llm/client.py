import os
from typing import Type, TypeVar

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel

load_dotenv()

T = TypeVar("T", bound=BaseModel)

LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL") or "https://api.openai.com/v1"
LLM_MODEL = os.getenv("LLM_MODEL_ID", "gpt-4.1-mini")

if not LLM_API_KEY:
    raise RuntimeError(
        "没有读取到 LLM_API_KEY。请在 backend/.env 中配置："
        "LLM_API_KEY=你的API_KEY"
    )

client = AsyncOpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
)


async def generate_structured(
    *,
    system_prompt: str,
    user_prompt: str,
    output_model: Type[T],
) -> T:
    schema = output_model.model_json_schema()

    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    user_prompt
                    + "\n\n你必须输出严格 JSON，符合下面 JSON Schema：\n"
                    + str(schema)
                ),
            },
        ],
        temperature=0.2,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": output_model.__name__,
                "schema": schema,
                "strict": True,
            },
        },
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("LLM returned empty content")

    return output_model.model_validate_json(content)