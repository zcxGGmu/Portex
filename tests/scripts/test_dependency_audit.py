from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_build_dependency_audit_command_uses_project_path() -> None:
    from scripts import dependency_audit

    command = dependency_audit.build_dependency_audit_command()

    assert command == [
        sys.executable,
        "-m",
        "pip_audit",
        "--ignore-vuln",
        "CVE-2024-23342",
        ".",
    ]


def test_main_returns_subprocess_exit_code(monkeypatch) -> None:
    from scripts import dependency_audit

    captured: dict[str, object] = {}

    class CompletedProcess:
        returncode = 5

    def fake_run(command, *, cwd, check):
        captured["command"] = command
        captured["cwd"] = cwd
        captured["check"] = check
        return CompletedProcess()

    monkeypatch.setattr(dependency_audit.subprocess, "run", fake_run)

    exit_code = dependency_audit.main([])

    assert exit_code == 5
    assert captured["command"] == dependency_audit.build_dependency_audit_command()
    assert captured["cwd"] == dependency_audit.PROJECT_ROOT
    assert captured["check"] is False
