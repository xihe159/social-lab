from __future__ import annotations

from collections import deque
from threading import RLock

from app.schemas.simulation_turn import SimulationTurnRecord


class SimulationTurnStore:
    """Bounded metadata-only turn store; raw user/target text is never retained."""

    def __init__(self, *, max_records: int = 2000) -> None:
        self._records: deque[SimulationTurnRecord] = deque(maxlen=max(1, max_records))
        self._lock = RLock()

    def append(self, record: SimulationTurnRecord) -> None:
        with self._lock:
            self._records.append(record.model_copy(deep=True))

    def list_for_session(self, session_id: str) -> list[SimulationTurnRecord]:
        with self._lock:
            return [
                record.model_copy(deep=True)
                for record in self._records
                if record.session_id == session_id
            ]

    def clear(self) -> None:
        with self._lock:
            self._records.clear()


simulation_turn_store = SimulationTurnStore()

