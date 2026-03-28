from __future__ import annotations

from pathlib import Path

import pytest

from opencourse.module_registry import validate_module_repo


def _write_minimal_module(root: Path) -> None:
    (root / "coursepacks" / "bda" / "weeks" / "week-01").mkdir(parents=True)
    (root / "coursepacks" / "bda" / "skills").mkdir(parents=True)
    (root / "opencourse-module.yaml").write_text(
        "id: bda\n"
        "title: Big Data\n"
        "version: 0.1.0\n"
        "spec_version: \"1\"\n"
        "entry_coursepack: bda\n"
        "openclaw_compatible: true\n",
        encoding="utf-8",
    )
    (root / "coursepacks" / "bda" / "course.yaml").write_text(
        "id: bda\n"
        "title: Big Data\n"
        "module: bda\n"
        "version: 0.1.0\n",
        encoding="utf-8",
    )


def test_validate_module_repo_passes(tmp_path: Path) -> None:
    _write_minimal_module(tmp_path)

    manifest = validate_module_repo(tmp_path)

    assert manifest.id == "bda"
    assert manifest.entry_coursepack == "bda"


def test_validate_module_repo_requires_manifest(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        validate_module_repo(tmp_path)
