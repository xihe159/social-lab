import asyncio
from pydantic import BaseModel, Field, ConfigDict

from app.llm.client import generate_structured


class TestResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(description="一句简短回复")
    score: int = Field(ge=0, le=100, description="测试分数")


async def main():
    result = await generate_structured(
        system_prompt="你是一个严格返回结构化 JSON 的测试助手。",
        user_prompt="请返回一句问候语，并给出 80 分左右的测试分数。",
        output_model=TestResult,
    )

    print(result)


if __name__ == "__main__":
    asyncio.run(main())
