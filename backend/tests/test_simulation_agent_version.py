from __future__ import annotations

import os
import sys
import types
import unittest
from unittest.mock import patch


# These tests exercise version selection only. Stub the LLM boundary so the
# suite can run without provider SDKs or credentials installed.
llm_client_stub = types.ModuleType("app.llm.client")
async def _unused_generate_structured(**kwargs):  # pragma: no cover
    raise AssertionError("LLM should not be called by version-selection tests")


llm_client_stub.generate_structured = _unused_generate_structured
sys.modules.setdefault("app.llm.client", llm_client_stub)

from app.agents.simulation_agent import SimulationAgentV1
from app.agents.simulation_agent_factory import (
    create_simulation_agent,
    resolve_simulation_agent_version,
)
from app.agents.simulation_agent_v2 import SimulationAgentV2


class SimulationAgentVersionTests(unittest.TestCase):
    def test_defaults_to_v1(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            version, agent = create_simulation_agent()

        self.assertEqual(version, "v1")
        self.assertIsInstance(agent, SimulationAgentV1)

    def test_v2_can_be_enabled_by_environment(self) -> None:
        with patch.dict(os.environ, {"SIMULATION_AGENT_VERSION": "v2"}, clear=True):
            version, agent = create_simulation_agent()

        self.assertEqual(version, "v2")
        self.assertIsInstance(agent, SimulationAgentV2)

    def test_version_value_is_normalized(self) -> None:
        self.assertEqual(resolve_simulation_agent_version(" V2 "), "v2")

    def test_invalid_value_falls_back_to_v1(self) -> None:
        version, agent = create_simulation_agent("future")

        self.assertEqual(version, "v1")
        self.assertIsInstance(agent, SimulationAgentV1)
if __name__ == "__main__":
    unittest.main()
