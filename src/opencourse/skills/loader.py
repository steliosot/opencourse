from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from ..config import OpenCourseConfig
from ..models import Skill, SkillMetadata

FRONTMATTER_PATTERN = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


class SkillLoader:
    def __init__(self, workspace: Path, config: OpenCourseConfig | None = None) -> None:
        self.workspace = workspace
        self.config = config or OpenCourseConfig()
        self.config.ensure_dirs()
        self.bundled_root = Path(__file__).resolve().parent.parent / "bundled"

    def skill_roots(self, include_coursepack: Path | None = None) -> list[tuple[str, Path]]:
        roots = [
            ("workspace", self.workspace / "skills"),
            ("agents", self.workspace / ".agents" / "skills"),
            ("user", self.config.user_skills_dir),
        ]
        if include_coursepack is not None:
            roots.append(("coursepack", include_coursepack / "skills"))
        roots.append(("bundled", self.bundled_root / "skills"))
        return roots

    def load_disabled(self) -> set[str]:
        file = self.config.disabled_skills_file
        if not file.exists():
            return set()
        data = json.loads(file.read_text(encoding="utf-8"))
        return set(data.get("disabled", []))

    def save_disabled(self, disabled: set[str]) -> None:
        self.config.disabled_skills_file.write_text(
            json.dumps({"disabled": sorted(disabled)}, indent=2),
            encoding="utf-8",
        )

    def enable_skill(self, name: str) -> None:
        disabled = self.load_disabled()
        if name in disabled:
            disabled.remove(name)
            self.save_disabled(disabled)

    def disable_skill(self, name: str) -> None:
        disabled = self.load_disabled()
        disabled.add(name)
        self.save_disabled(disabled)

    def load_skills(self, include_coursepack: Path | None = None) -> dict[str, Skill]:
        loaded: dict[str, Skill] = {}
        disabled = self.load_disabled()
        for source, root in self.skill_roots(include_coursepack=include_coursepack):
            if not root.exists():
                continue
            for child in sorted(root.iterdir()):
                if not child.is_dir():
                    continue
                skill_md = child / "SKILL.md"
                if not skill_md.exists():
                    continue
                skill = self._read_skill(source=source, skill_dir=child)
                if skill.metadata.name in loaded:
                    continue
                if skill.metadata.name in disabled:
                    skill.enabled = False
                loaded[skill.metadata.name] = skill
        return loaded

    def _read_skill(self, source: str, skill_dir: Path) -> Skill:
        raw = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        metadata_raw, _body = self._split_frontmatter(raw)
        metadata = SkillMetadata.model_validate(metadata_raw)
        return Skill(metadata=metadata, path=skill_dir, source=source)

    @staticmethod
    def _split_frontmatter(content: str) -> tuple[dict, str]:
        match = FRONTMATTER_PATTERN.match(content)
        if not match:
            return {}, content
        yaml_blob, body = match.groups()
        parsed = yaml.safe_load(yaml_blob) or {}
        return parsed, body

    @staticmethod
    def validate_skill_dir(skill_dir: Path) -> list[str]:
        errors: list[str] = []
        if not skill_dir.is_dir():
            return [f"{skill_dir} is not a directory"]
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            errors.append("Missing SKILL.md")
            return errors
        content = skill_md.read_text(encoding="utf-8")
        metadata, _ = SkillLoader._split_frontmatter(content)
        required = ["name", "description", "module", "skill_type"]
        for field in required:
            if field not in metadata:
                errors.append(f"SKILL.md frontmatter missing '{field}'")
        return errors
