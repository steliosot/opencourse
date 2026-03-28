from __future__ import annotations

from pathlib import Path

from opencourse.coursepacks.validator import validate_coursepack


def test_bundled_coursepack_is_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    pack = root / "src" / "opencourse" / "bundled" / "coursepacks" / "big-data-processing"

    ok, errors = validate_coursepack(pack)

    assert ok is True
    assert errors == []


def test_invalid_coursepack_reports_errors(tmp_path: Path) -> None:
    pack = tmp_path / "broken"
    pack.mkdir()
    (pack / "course.yaml").write_text("id: broken\n", encoding="utf-8")

    ok, errors = validate_coursepack(pack)

    assert ok is False
    assert any("weeks" in e for e in errors)
