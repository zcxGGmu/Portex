"""Memory tools backed by the mounted runner memory directory."""

from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path


MEMORY_DIR = Path(os.getenv("PORTEX_MEMORY_DIR", "/workspace/memory"))


def _today() -> date:
    return datetime.utcnow().date()


def _daily_memory_path() -> Path:
    return MEMORY_DIR / f"{_today().isoformat()}.md"


def memory_append_tool(content: str) -> str:
    """Append content to today's memory file in the mounted memory directory."""
    path = _daily_memory_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n{content}\n")
    return f"memory appended: {path.name}"


def memory_search_tool(query: str) -> list[str]:
    """Search markdown files in the mounted memory directory."""
    normalized_query = query.strip().lower()
    if normalized_query == "" or not MEMORY_DIR.exists():
        return []

    matches: list[str] = []
    for path in sorted(MEMORY_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8")
        if normalized_query in content.lower():
            matches.append(str(path.relative_to(MEMORY_DIR)))
    return matches


__all__ = ["MEMORY_DIR", "memory_append_tool", "memory_search_tool"]
