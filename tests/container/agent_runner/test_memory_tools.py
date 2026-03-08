from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNNER_ROOT = PROJECT_ROOT / "container" / "agent-runner"
if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))


def test_memory_append_tool_creates_todays_markdown_file(tmp_path: Path, monkeypatch) -> None:
    from src.tools import memory as memory_module

    memory_dir = tmp_path / "memory"
    monkeypatch.setattr(memory_module, "MEMORY_DIR", memory_dir, raising=False)
    expected_name = f"{datetime.utcnow().date().isoformat()}.md"

    result = memory_module.memory_append_tool("first entry")

    target = memory_dir / expected_name
    assert result == f"memory appended: {expected_name}"
    assert target.exists()
    assert target.read_text(encoding="utf-8") == "\nfirst entry\n"


def test_memory_append_tool_preserves_order_on_multiple_writes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from src.tools import memory as memory_module

    memory_dir = tmp_path / "memory"
    monkeypatch.setattr(memory_module, "MEMORY_DIR", memory_dir, raising=False)
    expected_name = f"{datetime.utcnow().date().isoformat()}.md"

    memory_module.memory_append_tool("first entry")
    memory_module.memory_append_tool("second entry")

    target = memory_dir / expected_name
    assert target.read_text(encoding="utf-8") == "\nfirst entry\n\nsecond entry\n"


def test_memory_search_tool_returns_relative_markdown_paths(tmp_path: Path, monkeypatch) -> None:
    from src.tools import memory as memory_module

    memory_dir = tmp_path / "memory"
    nested = memory_dir / "nested"
    nested.mkdir(parents=True, exist_ok=True)
    (memory_dir / "2026-03-08.md").write_text("Alpha keyword", encoding="utf-8")
    (nested / "extra.md").write_text("alpha in nested file", encoding="utf-8")
    (memory_dir / "ignored.txt").write_text("alpha but wrong extension", encoding="utf-8")
    monkeypatch.setattr(memory_module, "MEMORY_DIR", memory_dir, raising=False)

    results = memory_module.memory_search_tool("alpha")

    assert results == ["2026-03-08.md", "nested/extra.md"]


def test_memory_search_tool_is_case_insensitive(tmp_path: Path, monkeypatch) -> None:
    from src.tools import memory as memory_module

    memory_dir = tmp_path / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / "2026-03-08.md").write_text("Remember Launch Checklist", encoding="utf-8")
    monkeypatch.setattr(memory_module, "MEMORY_DIR", memory_dir, raising=False)

    assert memory_module.memory_search_tool("launch") == ["2026-03-08.md"]


def test_memory_search_tool_returns_empty_list_for_blank_query(tmp_path: Path, monkeypatch) -> None:
    from src.tools import memory as memory_module

    memory_dir = tmp_path / "memory"
    monkeypatch.setattr(memory_module, "MEMORY_DIR", memory_dir, raising=False)

    assert memory_module.memory_search_tool("") == []
    assert memory_module.memory_search_tool("   ") == []


def test_build_default_tools_includes_memory_wrappers() -> None:
    from src.tools import build_default_tools

    tool_names = [tool.name for tool in build_default_tools()]

    assert "memory_append" in tool_names
    assert "memory_search" in tool_names
