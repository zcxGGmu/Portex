from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_build_security_scan_command_uses_expected_targets() -> None:
    from scripts import security_scan

    command = security_scan.build_security_scan_command()

    assert command[:6] == [sys.executable, "-m", "ruff", "check", "--select", "S"]
    assert command[6:] == list(security_scan.SECURITY_SCAN_TARGETS)


def test_main_returns_subprocess_exit_code(monkeypatch) -> None:
    from scripts import security_scan

    captured: dict[str, object] = {}

    class CompletedProcess:
        returncode = 3

    def fake_run(command, *, cwd, check):
        captured["command"] = command
        captured["cwd"] = cwd
        captured["check"] = check
        return CompletedProcess()

    monkeypatch.setattr(security_scan.subprocess, "run", fake_run)

    exit_code = security_scan.main([])

    assert exit_code == 3
    assert captured["command"] == security_scan.build_security_scan_command()
    assert captured["cwd"] == security_scan.PROJECT_ROOT
    assert captured["check"] is False
