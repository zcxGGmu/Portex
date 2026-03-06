from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_validate_path_accepts_path_within_allowed_root(tmp_path: Path) -> None:
    from infra.exec.security import validate_path

    allowed_root = tmp_path / "allowed"
    safe_path = allowed_root / "group-a"
    safe_path.mkdir(parents=True)

    assert validate_path(str(safe_path), [str(allowed_root)]) is True


def test_validate_path_rejects_symlink_escape(tmp_path: Path) -> None:
    from infra.exec.security import validate_path

    allowed_root = tmp_path / "allowed"
    outside_root = tmp_path / "outside"
    allowed_root.mkdir()
    outside_root.mkdir()

    symlink_path = allowed_root / "escape-link"
    symlink_path.symlink_to(outside_root, target_is_directory=True)

    assert validate_path(str(symlink_path), [str(allowed_root)]) is False
