from __future__ import annotations


def mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def count_by_key(rows: list[dict], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        k = str(row.get(key, ""))
        out[k] = out.get(k, 0) + 1
    return out
