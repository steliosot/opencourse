from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field


class OpenCourseConfig(BaseModel):
    user_home: Path = Field(default_factory=lambda: Path(os.environ.get("OPENCOURSE_HOME", Path.home() / ".opencourse")))

    @property
    def user_skills_dir(self) -> Path:
        return self.user_home / "skills"

    @property
    def state_dir(self) -> Path:
        return self.user_home / "state"

    @property
    def disabled_skills_file(self) -> Path:
        return self.state_dir / "disabled_skills.json"

    def ensure_dirs(self) -> None:
        self.user_skills_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
