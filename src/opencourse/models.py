from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class SkillMetadata(BaseModel):
    name: str
    description: str = ""
    version: str = "0.1.0"
    tags: list[str] = Field(default_factory=list)
    module: str = "general"
    week: int | None = None
    session: int | None = 1
    skill_type: str = "guided-lab"
    runtime: dict[str, Any] = Field(default_factory=dict)


class Skill(BaseModel):
    metadata: SkillMetadata
    path: Path
    source: str
    enabled: bool = True


class WeekEntry(BaseModel):
    week: int
    title: str
    summary: str = ""
    skills: list[str] = Field(default_factory=list)


class CoursePack(BaseModel):
    id: str
    title: str
    description: str
    module: str
    version: str
    weeks: list[WeekEntry] = Field(default_factory=list)
    path: Path


class ProgressState(BaseModel):
    module_id: str = "big-data-processing"
    current_week: int = 1
    current_session: int = 1
    completed_skills: dict[str, datetime] = Field(default_factory=dict)
    last_skill: str | None = None

    def mark_complete(self, skill_name: str) -> None:
        self.completed_skills[skill_name] = datetime.utcnow()
        self.last_skill = skill_name
