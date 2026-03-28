from __future__ import annotations

from pathlib import Path

import yaml

from ..models import CoursePack, WeekEntry


class CoursePackLoader:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.bundled_root = Path(__file__).resolve().parent.parent / "bundled" / "coursepacks"

    def discover(self) -> dict[str, CoursePack]:
        packs: dict[str, CoursePack] = {}
        roots = [self.workspace / "coursepacks", self.bundled_root]
        for root in roots:
            if not root.exists():
                continue
            for pack_dir in sorted(root.iterdir()):
                if not pack_dir.is_dir():
                    continue
                course_file = pack_dir / "course.yaml"
                if not course_file.exists():
                    continue
                pack = self._load_pack(pack_dir)
                if pack.id not in packs:
                    packs[pack.id] = pack
        return packs

    def _load_pack(self, pack_dir: Path) -> CoursePack:
        data = yaml.safe_load((pack_dir / "course.yaml").read_text(encoding="utf-8"))
        weeks: list[WeekEntry] = []
        for week_dir in sorted((pack_dir / "weeks").glob("week-*")):
            week_file = week_dir / "week.yaml"
            if not week_file.exists():
                continue
            week_data = yaml.safe_load(week_file.read_text(encoding="utf-8"))
            weeks.append(WeekEntry.model_validate(week_data))
        return CoursePack(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            module=data.get("module", data["id"]),
            version=data.get("version", "0.1.0"),
            weeks=weeks,
            path=pack_dir,
        )
