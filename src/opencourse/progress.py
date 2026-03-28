from __future__ import annotations

import json
from pathlib import Path

from .models import ProgressState


class ProgressStore:
    def __init__(self, workspace: Path) -> None:
        self.path = workspace / ".opencourse-progress.json"

    def load(self) -> ProgressState:
        if not self.path.exists():
            return ProgressState()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return ProgressState.model_validate(data)

    def save(self, state: ProgressState) -> None:
        self.path.write_text(
            state.model_dump_json(indent=2),
            encoding="utf-8",
        )
