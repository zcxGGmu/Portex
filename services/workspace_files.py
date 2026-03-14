"""Workspace-scoped file management helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import mimetypes
from pathlib import Path
import shutil

from infra.exec.security import validate_path

DEFAULT_DATA_ROOT = Path("data")
MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024
MAX_TEXT_FILE_SIZE_BYTES = 1 * 1024 * 1024
TEXT_FILE_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".css",
    ".html",
    ".sh",
}
SAFE_INLINE_MIME_TYPES = {
    "application/pdf",
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/webp",
    "text/plain",
}


@dataclass(frozen=True, slots=True)
class WorkspaceFileEntry:
    name: str
    path: str
    type: str
    size: int
    modified_at: datetime


@dataclass(frozen=True, slots=True)
class WorkspaceFileListing:
    current_path: str
    entries: list[WorkspaceFileEntry]


@dataclass(frozen=True, slots=True)
class WorkspaceTextFile:
    path: str
    content: str
    size: int


@dataclass(frozen=True, slots=True)
class WorkspaceResolvedFile:
    path: str
    absolute_path: Path
    media_type: str


class WorkspaceFileService:
    """Perform safe file operations inside one workspace root."""

    def __init__(
        self,
        *,
        data_root: str | Path | None = None,
        max_upload_size_bytes: int = MAX_UPLOAD_SIZE_BYTES,
        max_text_file_size_bytes: int = MAX_TEXT_FILE_SIZE_BYTES,
    ) -> None:
        self._data_root = Path(data_root or DEFAULT_DATA_ROOT).expanduser().resolve()
        self._groups_root = (self._data_root / "groups").resolve()
        self._groups_root.mkdir(parents=True, exist_ok=True)
        self._max_upload_size_bytes = max_upload_size_bytes
        self._max_text_file_size_bytes = max_text_file_size_bytes

    def list_entries(self, group_folder: str, current_path: str = "") -> WorkspaceFileListing:
        workspace_root = self._workspace_root(group_folder)
        target = self._resolve_candidate(workspace_root, current_path)
        if not target.exists():
            raise FileNotFoundError("path not found")
        if not target.is_dir():
            raise NotADirectoryError("path is not a directory")

        entries = []
        for child in sorted(target.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
            stats = child.stat()
            relative_path = child.relative_to(workspace_root).as_posix()
            entries.append(
                WorkspaceFileEntry(
                    name=child.name,
                    path=relative_path,
                    type="directory" if child.is_dir() else "file",
                    size=stats.st_size,
                    modified_at=datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc),
                )
            )
        return WorkspaceFileListing(current_path=_normalize_current_path(current_path), entries=entries)

    def save_upload(
        self,
        group_folder: str,
        current_path: str,
        file_name: str,
        content: bytes,
    ) -> WorkspaceFileEntry:
        if len(content) > self._max_upload_size_bytes:
            raise ValueError("file exceeds upload size limit")
        if file_name in {"", ".", ".."} or Path(file_name).name != file_name:
            raise ValueError("invalid file name")

        workspace_root = self._workspace_root(group_folder)
        target_dir = self._resolve_candidate(workspace_root, current_path)
        target_dir.mkdir(parents=True, exist_ok=True)
        if not target_dir.is_dir():
            raise NotADirectoryError("upload target is not a directory")

        target_file = self._resolve_candidate(workspace_root, (_normalize_current_path(current_path) + "/" + file_name).strip("/"))
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_bytes(content)
        stats = target_file.stat()
        return WorkspaceFileEntry(
            name=target_file.name,
            path=target_file.relative_to(workspace_root).as_posix(),
            type="file",
            size=stats.st_size,
            modified_at=datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc),
        )

    def resolve_download_file(self, group_folder: str, file_path: str) -> WorkspaceResolvedFile:
        target = self._resolve_existing_file(group_folder, file_path)
        return WorkspaceResolvedFile(
            path=target.relative_to(self._workspace_root(group_folder)).as_posix(),
            absolute_path=target,
            media_type="application/octet-stream",
        )

    def resolve_preview_file(self, group_folder: str, file_path: str) -> WorkspaceResolvedFile:
        target = self._resolve_existing_file(group_folder, file_path)
        media_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if media_type not in SAFE_INLINE_MIME_TYPES:
            raise ValueError("file type not supported for preview")
        return WorkspaceResolvedFile(
            path=target.relative_to(self._workspace_root(group_folder)).as_posix(),
            absolute_path=target,
            media_type=media_type,
        )

    def read_text_content(self, group_folder: str, file_path: str) -> WorkspaceTextFile:
        target = self._resolve_existing_file(group_folder, file_path)
        self._ensure_text_file(target)
        size = target.stat().st_size
        if size > self._max_text_file_size_bytes:
            raise ValueError("text file exceeds size limit")
        return WorkspaceTextFile(
            path=target.relative_to(self._workspace_root(group_folder)).as_posix(),
            content=target.read_text(encoding="utf-8"),
            size=size,
        )

    def write_text_content(self, group_folder: str, file_path: str, content: str) -> WorkspaceTextFile:
        target = self._resolve_existing_file(group_folder, file_path)
        self._ensure_text_file(target)
        encoded = content.encode("utf-8")
        if len(encoded) > self._max_text_file_size_bytes:
            raise ValueError("text content exceeds size limit")
        temp_path = target.with_suffix(target.suffix + ".tmp")
        temp_path.write_bytes(encoded)
        temp_path.replace(target)
        return WorkspaceTextFile(
            path=target.relative_to(self._workspace_root(group_folder)).as_posix(),
            content=content,
            size=len(encoded),
        )

    def delete_path(self, group_folder: str, file_path: str) -> None:
        workspace_root = self._workspace_root(group_folder)
        normalized = _normalize_current_path(file_path)
        if normalized == "":
            raise ValueError("cannot delete workspace root")
        target = self._resolve_candidate(workspace_root, normalized)
        if not target.exists():
            raise FileNotFoundError("path not found")
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

    def _workspace_root(self, group_folder: str) -> Path:
        candidate = (self._groups_root / group_folder).resolve()
        if not validate_path(candidate, [self._groups_root]):
            raise ValueError("invalid workspace root")
        candidate.mkdir(parents=True, exist_ok=True)
        return candidate

    def _resolve_existing_file(self, group_folder: str, file_path: str) -> Path:
        workspace_root = self._workspace_root(group_folder)
        target = self._resolve_candidate(workspace_root, file_path)
        if not target.exists():
            raise FileNotFoundError("file not found")
        if target.is_dir():
            raise IsADirectoryError("path is a directory")
        return target

    def _resolve_candidate(self, workspace_root: Path, relative_path: str) -> Path:
        normalized = _normalize_current_path(relative_path)
        candidate = workspace_root / normalized
        resolved_candidate = candidate.resolve(strict=False)
        if not validate_path(resolved_candidate, [workspace_root]):
            if ".." in Path(relative_path).parts:
                raise ValueError("path traversal detected")
            raise ValueError("symlink traversal detected")
        return candidate

    def _ensure_text_file(self, target: Path) -> None:
        if target.suffix.lower() not in TEXT_FILE_EXTENSIONS:
            raise ValueError("file type not supported for text content")


def _normalize_current_path(relative_path: str) -> str:
    normalized = (relative_path or "").strip().strip("/")
    if normalized in {"", "."}:
        return ""
    return Path(normalized).as_posix()


__all__ = [
    "MAX_TEXT_FILE_SIZE_BYTES",
    "MAX_UPLOAD_SIZE_BYTES",
    "SAFE_INLINE_MIME_TYPES",
    "TEXT_FILE_EXTENSIONS",
    "WorkspaceFileEntry",
    "WorkspaceFileListing",
    "WorkspaceFileService",
    "WorkspaceResolvedFile",
    "WorkspaceTextFile",
]
