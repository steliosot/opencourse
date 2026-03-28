from __future__ import annotations

import re
from pathlib import Path

TEXT_EXTENSIONS = {".md", ".txt", ".py", ".yaml", ".yml", ".csv", ".json"}
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules"}


def _tokenize(text: str) -> set[str]:
    return {tok for tok in re.findall(r"[a-zA-Z0-9_]{3,}", text.lower())}


def _chunk_text(text: str, chunk_size: int = 900) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    length = 0
    for line in text.splitlines():
        current.append(line)
        length += len(line) + 1
        if length >= chunk_size:
            chunks.append("\n".join(current).strip())
            current = []
            length = 0
    if current:
        chunks.append("\n".join(current).strip())
    return [c for c in chunks if c]


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            if path.stat().st_size > 300_000:
                continue
        except OSError:
            continue
        files.append(path)
    return files


def retrieve_context(question: str, root: Path, top_k: int = 4) -> str:
    q_tokens = _tokenize(question)
    if not q_tokens:
        return ""

    scored: list[tuple[int, str, Path]] = []
    for file in _iter_files(root):
        try:
            content = file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for chunk in _chunk_text(content):
            c_tokens = _tokenize(chunk)
            if not c_tokens:
                continue
            score = len(q_tokens & c_tokens)
            if score <= 0:
                continue
            scored.append((score, chunk, file))

    if not scored:
        return ""
    scored.sort(key=lambda x: x[0], reverse=True)

    context_blocks: list[str] = []
    for score, chunk, file in scored[:top_k]:
        snippet = chunk[:700]
        context_blocks.append(f"Source: {file}\nRelevance: {score}\n{snippet}")
    return "\n\n---\n\n".join(context_blocks)
