from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_solution_module():
    skill_dir = Path(__file__).resolve().parents[1]
    pack_root = skill_dir.parents[1]
    solution_path = pack_root / "assessments" / "task2" / "solution.py"
    spec = importlib.util.spec_from_file_location("task2_solution", solution_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_mean():
    mod = _load_solution_module()
    assert round(mod.mean([1.0, 2.0, 3.0]), 3) == 2.0


def test_count_by_key():
    mod = _load_solution_module()
    rows = [{"event": "view"}, {"event": "view"}, {"event": "click"}]
    assert mod.count_by_key(rows, "event") == {"view": 2, "click": 1}
