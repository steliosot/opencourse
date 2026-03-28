from __future__ import annotations

import csv
from pathlib import Path


def load_sales(path: str | Path) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def total_units(rows: list[dict[str, str]]) -> int:
    return sum(int(row["units"]) for row in rows)
