from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class AISettings(BaseModel):
    enabled: bool = False
    provider: str = "ollama"
    model: str = "llama3.2:3b"
    endpoint: str = "http://localhost:11434"


class OpenCourseAIConfig(BaseModel):
    ai: AISettings = Field(default_factory=AISettings)


def default_config_path() -> Path:
    return Path.home() / ".opencourse" / "config.yaml"


def load_config(path: Path | None = None) -> OpenCourseAIConfig:
    cfg_path = path or default_config_path()
    if not cfg_path.exists():
        return OpenCourseAIConfig()
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    return OpenCourseAIConfig.model_validate(data)


def save_config(config: OpenCourseAIConfig, path: Path | None = None) -> Path:
    cfg_path = path or default_config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(yaml.safe_dump(config.model_dump(), sort_keys=False), encoding="utf-8")
    return cfg_path
