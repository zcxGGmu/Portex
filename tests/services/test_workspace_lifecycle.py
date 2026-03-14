from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _slot_workspace_key(group_folder: str, slot_id: str = "main") -> str:
    return f"{group_folder}#slot:{slot_id}"


def test_workspace_session_store_reuses_committed_session_and_preserves_fresh_preview() -> None:
    from services.workspace_lifecycle import WorkspaceSessionStore

    store = WorkspaceSessionStore(
        new_session_id_factory=lambda workspace_key: f"{workspace_key}:fresh"
    )

    workspace_key = _slot_workspace_key("group-a")
    first = store.preview_session_id(workspace_key, backend="openai_runtime")
    assert first == workspace_key
    assert store.get_state(workspace_key).session_id is None

    store.commit_success(workspace_key, backend="openai_runtime", session_id=first)

    assert store.get_state(workspace_key).session_id == workspace_key
    assert store.preview_session_id(workspace_key, backend="openai_runtime") == workspace_key
    assert store.preview_session_id(
        workspace_key,
        backend="openai_runtime",
        fresh_session=True,
    ) == f"{workspace_key}:fresh"
    assert store.get_state(workspace_key).session_id == workspace_key


def test_workspace_session_store_invalidates_current_session_before_allocating_next_one() -> None:
    from services.workspace_lifecycle import WorkspaceSessionStore

    store = WorkspaceSessionStore(
        new_session_id_factory=lambda workspace_key: f"{workspace_key}:fresh"
    )
    workspace_key = _slot_workspace_key("group-a")
    store.commit_success(workspace_key, backend="openai_runtime", session_id=workspace_key)

    store.invalidate(workspace_key, reason="resume_failed")

    state = store.get_state(workspace_key)
    assert state.session_id is None
    assert state.backend is None
    assert store.preview_session_id(workspace_key, backend="openai_runtime") == f"{workspace_key}:fresh"


def test_group_folder_workspace_resolver_builds_slot_aware_workspace_keys() -> None:
    from services.workspace_lifecycle import GroupFolderWorkspaceResolver

    resolver = GroupFolderWorkspaceResolver()

    assert resolver.resolve_workspace_key("project-alpha") == _slot_workspace_key("project-alpha")
    assert resolver.resolve_workspace_key("project-alpha", slot_id="draft") == _slot_workspace_key(
        "project-alpha",
        "draft",
    )
