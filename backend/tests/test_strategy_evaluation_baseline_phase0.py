from __future__ import annotations

import unittest

from evaluation.strategy_evaluation_baseline import (
    BaselineObservation,
    load_baseline_catalog,
    summarize_observations,
)


class StrategyEvaluationBaselinePhase0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_baseline_catalog()

    def test_fixed_catalog_has_36_cases_and_full_prd_coverage(self) -> None:
        self.assertEqual(len(self.catalog.cases), 36)
        self.assertEqual(
            {item.category for item in self.catalog.cases},
            set(self.catalog.required_categories),
        )
        self.assertEqual(
            {item.persona_id for item in self.catalog.cases},
            set(self.catalog.personas),
        )

    def test_cases_use_semantic_expectations_not_coach_advice(self) -> None:
        forbidden_phrases = (
            "你可以这样说",
            "推荐话术",
            "候选话术",
            "温和版",
            "坚定版",
        )
        serialized = self.catalog.model_dump_json()
        self.assertFalse(any(item in serialized for item in forbidden_phrases))

    def test_silent_cases_only_allow_silent_capable_current_actions(self) -> None:
        silent_actions = {"DEFER_REPLY", "READ_NO_REPLY"}
        silent_cases = [item for item in self.catalog.cases if item.expected.silent]
        self.assertGreaterEqual(len(silent_cases), 4)
        for case in silent_cases:
            self.assertTrue(
                silent_actions.intersection(case.expected.allowed_current_actions),
                case.case_id,
            )

    def test_extreme_actions_require_high_conflict_or_repeated_pressure(self) -> None:
        extreme_cases = [
            item for item in self.catalog.cases if item.expected.extreme_action_allowed
        ]
        self.assertGreaterEqual(len(extreme_cases), 4)
        for case in extreme_cases:
            self.assertTrue(
                case.relationship.conflict_tier == "high"
                or case.relationship.repeated_pressure,
                case.case_id,
            )

    def test_all_key_decisions_require_evidence_refs(self) -> None:
        self.assertTrue(
            all(item.expected.requires_evidence_refs for item in self.catalog.cases)
        )

    def test_summary_requires_same_complete_case_set(self) -> None:
        observations = [
            BaselineObservation(
                case_id=case.case_id,
                system_version="simulation-v2-phase0",
                reply="" if case.expected.silent else "基线回复",
                selected_action=case.expected.allowed_current_actions[0],
                persona_consistency=80,
                relationship_continuity=82,
                style_consistency=78,
                human_overall=80,
                latency_ms=100 + index,
                evidence_refs=["baseline_evidence"],
            )
            for index, case in enumerate(self.catalog.cases)
        ]

        summary = summarize_observations(observations, catalog=self.catalog)
        self.assertEqual(summary.case_count, 36)
        self.assertEqual(summary.action_contract_rate, 1.0)
        self.assertEqual(summary.silent_contract_rate, 1.0)
        self.assertEqual(summary.evidence_contract_rate, 1.0)
        self.assertEqual(summary.persona_consistency, 80.0)
        self.assertEqual(summary.relationship_continuity, 82.0)
        self.assertEqual(summary.style_consistency, 78.0)
        self.assertEqual(summary.human_overall, 80.0)

        with self.assertRaises(ValueError):
            summarize_observations(observations[:-1], catalog=self.catalog)


if __name__ == "__main__":
    unittest.main()
