# social-lab/backend/app/agents/evaluation_agent.py
# 2026/07/01
#
# 新增内容：
# 1. EvaluationAgent：用于评估模拟质量
# 2. 支持 single_turn / whole_session 两种模式
# 3. LLM 失败时不在本 Agent 内吞异常，由 API 层统一返回 502
#
# 设计说明：
# - EvaluationAgent 不参与 /api/session/message 主链路，避免增加聊天接口延迟。
# - 建议通过 POST /api/session/evaluate 独立调用。
# - 它主要服务开发调试、prompt 迭代和后续“模拟质量评分”展示。

from __future__ import annotations

from typing import List

from app.agents.prompts import EVALUATION_SYSTEM_PROMPT, build_evaluation_user_prompt
from app.llm.client import generate_structured
from app.schemas.evaluation import EvaluationRequest, EvaluationResponse, EvaluationScoreItem


class EvaluationAgent:
    async def run(self, request: EvaluationRequest) -> EvaluationResponse:
        payload = request.model_dump()

        result = await generate_structured(
            system_prompt=EVALUATION_SYSTEM_PROMPT,
            user_prompt=build_evaluation_user_prompt(payload),
            output_model=EvaluationResponse,
            temperature=0.2,
        )

        return self.post_process(result)

    def post_process(self, result: EvaluationResponse) -> EvaluationResponse:
        """
        对 LLM 输出做轻量稳定化处理。
        """

        result.persona_consistency = self._normalize_score_item(result.persona_consistency)
        result.relationship_consistency = self._normalize_score_item(result.relationship_consistency)
        result.role_play_quality = self._normalize_score_item(result.role_play_quality)
        result.realism = self._normalize_score_item(result.realism)
        result.responsiveness = self._normalize_score_item(result.responsiveness)
        result.safety_score = self._normalize_score_item(result.safety_score)
        result.pedagogical_value = self._normalize_score_item(result.pedagogical_value)

        result.major_problems = self._clean_list(result.major_problems)
        result.suggested_fixes = self._clean_list(result.suggested_fixes)
        result.debug_notes = self._clean_list(result.debug_notes)

        result.overall_score = self._clamp_score(result.overall_score)

        if result.overall_score == 0:
            result.overall_score = self._average_scores(
                [
                    result.persona_consistency.score,
                    result.relationship_consistency.score,
                    result.role_play_quality.score,
                    result.realism.score,
                    result.responsiveness.score,
                    result.safety_score.score,
                    result.pedagogical_value.score,
                ]
            )

        if not result.major_problems:
            result.major_problems = ["未发现明显问题，建议继续进行多场景测试。"]

        if not result.suggested_fixes:
            result.suggested_fixes = ["保持当前输出结构，继续观察多轮对话中的一致性。"]

        if not result.debug_notes:
            result.debug_notes = ["EvaluationAgent 未返回额外调试备注。"]

        return result

    def _normalize_score_item(self, item: EvaluationScoreItem) -> EvaluationScoreItem:
        item.score = self._clamp_score(item.score)
        item.reason = self._clean_text(item.reason) or "未提供评分原因。"
        item.evidence = self._clean_list(item.evidence)

        if not item.evidence:
            item.evidence = ["未提供明确证据。"]

        return item

    def _clamp_score(self, value: int) -> int:
        try:
            score = int(value)
        except Exception:
            return 0

        return max(0, min(100, score))

    def _average_scores(self, scores: List[int]) -> int:
        clean_scores = [self._clamp_score(score) for score in scores]

        if not clean_scores:
            return 0

        return round(sum(clean_scores) / len(clean_scores))

    def _clean_text(self, value: str) -> str:
        if value is None:
            return ""

        return str(value).strip()

    def _clean_list(self, values: List[str]) -> List[str]:
        if not values:
            return []

        result: List[str] = []
        seen = set()

        for value in values:
            text = self._clean_text(value)

            if not text:
                continue

            if text in seen:
                continue

            seen.add(text)
            result.append(text)

        return result[:8]
