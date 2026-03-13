from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_workspace_session_store_reuses_committed_session_and_preserves_fresh_preview() -> None:
    from services.workspace_lifecycle import WorkspaceSessionStore

    store = WorkspaceSessionStore(
        new_session_id_factory=lambda workspace_key: f"{workspace_key}:fresh"
    )

    first = store.preview_session_id("group-a", backend="openai_runtime")
    assert first == "group-a"
    assert store.get_state("group-a").session_id is None

    store.commit_success("group-a", backend="openai_runtime", session_id=first)

    assert store.get_state("group-a").session_id == "group-a"
    assert store.preview_session_id("group-a", backend="openai_runtime") == "group-a"
    assert store.preview_session_id(
        "group-a",
        backend="openai_runtime",
        fresh_session=True,
    ) == "group-a:fresh"
    assert store.get_state("group-a").session_id == "group-a"


def test_workspace_session_store_invalidates_current_session_before_allocating_next_one() -> None:
    from services.workspace_lifecycle import WorkspaceSessionStore

    store = WorkspaceSessionStore(
        new_session_id_factory=lambda workspace_key: f"{workspace_key}:fresh"
    )
    store.commit_success("group-a", backend="openai_runtime", session_id="group-a")

    store.invalidate("group-a", reason="resume_failed")

    state = store.get_state("group-a")
    assert state.session_id is None
    assert state.backend is None
    assert store.preview_session_id("group-a", backend="openai_runtime") == "group-a:fresh"
