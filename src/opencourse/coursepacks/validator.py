from __future__ import annotations

from pathlib import Path

import yaml


def validate_coursepack(path: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not path.exists() or not path.is_dir():
        return False, [f"Coursepack path does not exist: {path}"]

    course_file = path / "course.yaml"
    if not course_file.exists():
        errors.append("Missing course.yaml")
    else:
        data = yaml.safe_load(course_file.read_text(encoding="utf-8")) or {}
        for key in ["id", "title", "module", "version"]:
            if key not in data:
                errors.append(f"course.yaml missing '{key}'")

    weeks_dir = path / "weeks"
    if not weeks_dir.exists():
        errors.append("Missing weeks/ directory")
    else:
        week_dirs = sorted(weeks_dir.glob("week-*"))
        if not week_dirs:
            errors.append("No week-* directories found")
        for week_dir in week_dirs:
            week_file = week_dir / "week.yaml"
            if not week_file.exists():
                errors.append(f"Missing week.yaml in {week_dir.name}")
                continue
            w = yaml.safe_load(week_file.read_text(encoding="utf-8")) or {}
            for key in ["week", "title", "skills"]:
                if key not in w:
                    errors.append(f"{week_dir.name}/week.yaml missing '{key}'")

    skills_dir = path / "skills"
    if not skills_dir.exists():
        errors.append("Missing skills/ directory")

    return (len(errors) == 0), errors
