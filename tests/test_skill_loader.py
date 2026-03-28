from __future__ import annotations

from pathlib import Path

from opencourse.config import OpenCourseConfig
from opencourse.skills.loader import SkillLoader


def _write_skill(path: Path, *, name: str, description: str = "desc", skill_type: str = "guided-lab") -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "version: 0.1.0\n"
        "tags: [test]\n"
        "module: big-data-processing\n"
        "week: 1\n"
        f"skill_type: {skill_type}\n"
        "runtime: {}\n"
        "---\n\n"
        "# Skill\n",
        encoding="utf-8",
    )


def test_workspace_skill_precedence_over_bundled(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    _write_skill(workspace / "skills" / "welcome-hint", name="welcome-hint", description="workspace override")

    cfg = OpenCourseConfig(user_home=tmp_path / "home")
    loader = SkillLoader(workspace=workspace, config=cfg)
    skills = loader.load_skills()

    assert "welcome-hint" in skills
    assert skills["welcome-hint"].source == "workspace"
    assert skills["welcome-hint"].metadata.description == "workspace override"


def test_skill_validation_requires_frontmatter_fields(tmp_path: Path) -> None:
    skill_dir = tmp_path / "bad-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")

    errors = SkillLoader.validate_skill_dir(skill_dir)

    assert errors
    assert any("description" in e for e in errors)
