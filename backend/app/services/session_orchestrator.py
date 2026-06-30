# social-lab/backend/app/services/session_orchestrator.py
# 2026/06/29

from __future__ import annotations

from app.agents.memory_agent import MemoryAgent
from app.agents.simulation_agent import SimulationAgent, apply_state_delta
from app.agents.state_agent import StateAgent
from app.llm.client import LLMClientError
from app.schemas.memory import MemoryUpdateRequest
from app.schemas.session import SessionMessageRequest, SessionMessageResponse
from app.schemas.state import StateEvaluateRequest


class SessionOrchestrator:
    def __init__(self):
        self.simulation_agent = SimulationAgent()
        self.state_agent = StateAgent()
        self.memory_agent = MemoryAgent()

    async def handle_message(
        self,
        request: SessionMessageRequest,
    ) -> SessionMessageResponse:
        print("[SessionOrchestrator] Start SimulationAgent")

        simulation_response = await self.simulation_agent.run(request)

        print("[SessionOrchestrator] SimulationAgent success")
        print("[SessionOrchestrator] Start StateAgent")

        state_delta = simulation_response.simulation.state_delta
        risk_flags = simulation_response.simulation.risk_flags

        try:
            state_request = StateEvaluateRequest(
                scenario=request.scenario,
                goal=request.goal,
                outcome=request.outcome,
                persona=request.persona,
                messages=request.messages,
                user_message=request.user_message,
                target_reply=simulation_response.target_message.content,
                current_state=request.persona.state,
                simulation_attitude=simulation_response.simulation.attitude,
                simulation_emotion=simulation_response.simulation.emotion,
                perceived_user_tone=simulation_response.simulation.perceived_user_tone,
            )

            state_evaluation = await self.state_agent.run(state_request)

            print("[SessionOrchestrator] StateAgent success")
            print(
                "[SessionOrchestrator] StateAgent evaluation:",
                state_evaluation.model_dump(),
            )

            state_delta = state_evaluation.state_delta
            risk_flags = state_evaluation.risk_flags

            simulation_response.simulation.state_delta = state_delta
            simulation_response.simulation.risk_flags = risk_flags
            simulation_response.updated_state = apply_state_delta(
                state=request.persona.state,
                delta=state_delta,
            )

        except LLMClientError as exc:
            print(
                "[SessionOrchestrator] StateAgent LLM failed, "
                "fallback to SimulationAgent result"
            )
            print("[SessionOrchestrator] StateAgent LLM error:", str(exc))

        except Exception as exc:
            print(
                "[SessionOrchestrator] StateAgent unexpected failed, "
                "fallback to SimulationAgent result"
            )
            print("[SessionOrchestrator] StateAgent error type:", exc.__class__.__name__)
            print("[SessionOrchestrator] StateAgent error:", repr(exc))

        print("[SessionOrchestrator] Start MemoryAgent")

        try:
            memory_request = MemoryUpdateRequest(
                scenario=request.scenario,
                goal=request.goal,
                outcome=request.outcome,
                persona=request.persona,
                messages=request.messages,
                user_message=request.user_message,
                target_reply=simulation_response.target_message.content,
                state_delta=state_delta,
                risk_flags=risk_flags,
                current_memory=request.memory,
            )

            memory_response = await self.memory_agent.run(memory_request)

            print("[SessionOrchestrator] MemoryAgent success")
            print(
                "[SessionOrchestrator] MemoryAgent memory:",
                memory_response.memory.model_dump(),
            )
            print("[SessionOrchestrator] MemoryAgent reason:", memory_response.memory_reason)

            simulation_response.updated_memory = memory_response.memory

        except LLMClientError as exc:
            print(
                "[SessionOrchestrator] MemoryAgent LLM failed, "
                "fallback to previous memory"
            )
            print("[SessionOrchestrator] MemoryAgent LLM error:", str(exc))
            simulation_response.updated_memory = request.memory

        except Exception as exc:
            print(
                "[SessionOrchestrator] MemoryAgent unexpected failed, "
                "fallback to previous memory"
            )
            print("[SessionOrchestrator] MemoryAgent error type:", exc.__class__.__name__)
            print("[SessionOrchestrator] MemoryAgent error:", repr(exc))
            simulation_response.updated_memory = request.memory

        return simulation_response

