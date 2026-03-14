from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def service(tmp_path: Path):
    from services.workspace_files import WorkspaceFileService

    return WorkspaceFileService(data_root=tmp_path / "data")


def test_list_directory_returns_directories_before_files(service, tmp_path: Path) -> None:
    workspace_root = tmp_path / "data" / "groups" / "project-alpha"
    (workspace_root / "zeta.txt").parent.mkdir(parents=True, exist_ok=True)
    (workspace_root / "zeta.txt").write_text("zeta", encoding="utf-8")
    (workspace_root / "alpha").mkdir()
    (workspace_root / "alpha.txt").write_text("alpha", encoding="utf-8")

    listing = service.list_entries("project-alpha")

    assert listing.current_path == ""
    assert [(entry.name, entry.type) for entry in listing.entries] == [
        ("alpha", "directory"),
        ("alpha.txt", "file"),
        ("zeta.txt", "file"),
    ]


def test_list_directory_rejects_path_traversal(service) -> None:
    with pytest.raises(ValueError, match="path traversal detected"):
        service.list_entries("project-alpha", "../escape")


def test_list_directory_rejects_symlink_escape(service, tmp_path: Path) -> None:
    workspace_root = tmp_path / "data" / "groups" / "project-alpha"
    outside_root = tmp_path / "outside"
    outside_root.mkdir()
    workspace_root.mkdir(parents=True)
    (workspace_root / "link").symlink_to(outside_root, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink traversal detected"):
        service.list_entries("project-alpha", "link")


def test_save_upload_creates_file_under_workspace_root(service) -> None:
    saved = service.save_upload(
        "project-alpha",
        "",
        "notes.txt",
        b"hello workspace",
    )

    assert saved.path == "notes.txt"
    assert saved.size == len(b"hello workspace")


def test_save_upload_rejects_invalid_filename(service) -> None:
    with pytest.raises(ValueError, match="invalid file name"):
        service.save_upload("project-alpha", "", "../notes.txt", b"x")


def test_read_and_write_text_content_round_trip(service, tmp_path: Path) -> None:
    workspace_root = tmp_path / "data" / "groups" / "project-alpha"
    workspace_root.mkdir(parents=True, exist_ok=True)
    file_path = workspace_root / "notes.txt"
    file_path.write_text("before", encoding="utf-8")

    original = service.read_text_content("project-alpha", "notes.txt")
    assert original.content == "before"

    updated = service.write_text_content("project-alpha", "notes.txt", "after")
    assert updated.size == len("after".encode("utf-8"))
    assert file_path.read_text(encoding="utf-8") == "after"


def test_read_text_content_rejects_unsupported_type(service, tmp_path: Path) -> None:
    workspace_root = tmp_path / "data" / "groups" / "project-alpha"
    workspace_root.mkdir(parents=True, exist_ok=True)
    (workspace_root / "archive.bin").write_bytes(b"\x00\x01")

    with pytest.raises(ValueError, match="file type not supported for text content"):
        service.read_text_content("project-alpha", "archive.bin")


def test_delete_path_rejects_workspace_root(service) -> None:
    with pytest.raises(ValueError, match="cannot delete workspace root"):
        service.delete_path("project-alpha", "")


def test_resolve_preview_file_rejects_unsupported_preview_type(service, tmp_path: Path) -> None:
    workspace_root = tmp_path / "data" / "groups" / "project-alpha"
    workspace_root.mkdir(parents=True, exist_ok=True)
    (workspace_root / "archive.bin").write_bytes(b"\x00\x01")

    with pytest.raises(ValueError, match="file type not supported for preview"):
        service.resolve_preview_file("project-alpha", "archive.bin")
