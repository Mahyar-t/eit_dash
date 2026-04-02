from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from time import time
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from backend.services.load_service import REPO_ROOT

if TYPE_CHECKING:
    from eitprocessing.datahandling.sequence import Sequence


@dataclass(slots=True)
class SessionStablePeriod:
    sequence: "Sequence"
    dataset_index: int
    period_index: int

    def get_data(self) -> "Sequence":
        return self.sequence

    def get_dataset_index(self) -> int:
        return self.dataset_index

    def get_period_index(self) -> int:
        return self.period_index


@dataclass(slots=True)
class SessionRecord:
    session_id: str
    created_at: float = field(default_factory=time)
    label: str = "Untitled session"
    current_cwd: str = field(default_factory=lambda: str(REPO_ROOT))
    loaded_datasets: list["Sequence"] = field(default_factory=list)
    stable_periods: list[SessionStablePeriod] = field(default_factory=list)
    temp_filtered_periods: list[SessionStablePeriod] = field(default_factory=list)
    saved_filter_params: dict[str, Any] | None = None
    pending_load: Any | None = None
    analyze_eeli_results: dict[int, dict[str, Any]] = field(default_factory=dict)
    selected_analyze_period_index: int | None = None

    def reset_analyze_state(self) -> None:
        self.analyze_eeli_results.clear()
        self.selected_analyze_period_index = None


class SessionStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._sessions: dict[str, SessionRecord] = {}

    def create(self, label: str | None = None) -> SessionRecord:
        with self._lock:
            session_id = uuid4().hex
            record = SessionRecord(session_id=session_id, label=label or "Untitled session")
            self._sessions[session_id] = record
            return record

    def get(self, session_id: str) -> SessionRecord:
        with self._lock:
            try:
                return self._sessions[session_id]
            except KeyError as exc:
                msg = f"Unknown session '{session_id}'"
                raise KeyError(msg) from exc


session_store = SessionStore()
