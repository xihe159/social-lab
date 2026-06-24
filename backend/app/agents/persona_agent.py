from app.schemas import PersonaCreateRequest, PersonaCreateResponse
from app.agents.prompts import PERSONA_SYSTEM_PROMPT, build_persona_user_prompt
from app.llm.client import generate_structured


class PersonaAgent:
    async def run(self, request: PersonaCreateRequest) -> PersonaCreateResponse:
        payload = request.model_dump()

        result = await generate_structured(
            system_prompt=PERSONA_SYSTEM_PROMPT,
            user_prompt=build_persona_user_prompt(payload),
            output_model=PersonaCreateResponse,
        )

        return self.post_process(result)

    def post_process(self, result: PersonaCreateResponse) -> PersonaCreateResponse:
        """
        防止模型虽然结构正确，但数值或字段语义不稳定。
        Pydantic 已经做了范围校验，这里可以继续做业务级修正。
        """

        state = result.persona.state

        # 简单业务保护：权威关系不应该完全为 0
        if "导师" in result.persona.title or "领导" in result.persona.title:
            state.authority = max(state.authority, 60)

        # 策略不能为空
        if not result.persona.strategy.strip():
            result.persona.strategy = "先说明背景，再提出具体请求，同时降低对方的行动成本。"

        return result