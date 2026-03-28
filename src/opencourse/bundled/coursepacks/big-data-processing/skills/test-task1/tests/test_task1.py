from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_solution_module():
    skill_dir = Path(__file__).resolve().parents[1]
    pack_root = skill_dir.parents[1]
    solution_path = pack_root / "assessments" / "task1" / "solution.py"
    spec = importlib.util.spec_from_file_location("task1_solution", solution_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_total_units():
    mod = _load_solution_module()
    rows = [
        {"units": "3"},
        {"units": "5"},
        {"units": "2"},
    ]
    assert mod.total_units(rows) == 10
