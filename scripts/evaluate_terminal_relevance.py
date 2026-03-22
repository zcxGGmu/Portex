#!/usr/bin/env python3
"""Run offline terminal relevance baseline evaluation against fixed fixtures."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.terminal_sessions import TerminalSessionService  # noqa: E402

DEFAULT_FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "terminal_relevance_baseline.json"


@dataclass(frozen=True, slots=True)
class FixtureEntry:
    id: str
    output: str


@dataclass(frozen=True, slots=True)
class FixtureCase:
    id: str
    query: str
    entries: tuple[FixtureEntry, ...]
    expected_order: tuple[str, ...]
    limit: int
    offset: int


@dataclass(frozen=True, slots=True)
class FixtureFile:
    version: int
    cases: tuple[FixtureCase, ...]


@dataclass(frozen=True, slots=True)
class CaseEvaluation:
    case_id: str
    passed: bool
    expected_order: tuple[str, ...]
    actual_order: tuple[str, ...]
    reciprocal_rank: float
    top1_correct: bool


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    case_count: int
    pass_count: int
    pass_rate: float
    top1_accuracy: float
    mrr: float
    cases: tuple[CaseEvaluation, ...]


class _BenchmarkBridge:
    def __init__(self) -> None:
        self._event_handler = None

    async def start(self, on_event) -> None:
        self._event_handler = on_event

    async def send_input(self, data: str) -> None:
        del data

    async def resize(self, *, cols: int, rows: int) -> None:
        del cols, rows

    async def close(self) -> None:
        return None

    async def emit_output(self, data: str) -> None:
        if self._event_handler is None:
            raise RuntimeError("bridge has not been started")
        await self._event_handler({"type": "output", "data": data})


def _parse_entry(data: object, *, case_id: str, entry_ids: set[str]) -> FixtureEntry:
    if not isinstance(data, dict):
        raise ValueError(f"case '{case_id}' entry must be an object")

    entry_id = data.get("id")
    output = data.get("output")
    if not isinstance(entry_id, str) or not entry_id:
        raise ValueError(f"case '{case_id}' entry id must be a non-empty string")
    if entry_id in entry_ids:
        raise ValueError(f"case '{case_id}' has duplicate entry id '{entry_id}'")
    if not isinstance(output, str):
        raise ValueError(f"case '{case_id}' entry '{entry_id}' output must be a string")

    entry_ids.add(entry_id)
    return FixtureEntry(id=entry_id, output=output)


def _parse_case(data: object, *, seen_case_ids: set[str]) -> FixtureCase:
    if not isinstance(data, dict):
        raise ValueError("fixture case must be an object")

    case_id = data.get("id")
    query = data.get("query")
    raw_entries = data.get("entries")
    raw_expected = data.get("expected_order")
    raw_limit = data.get("limit")
    raw_offset = data.get("offset")

    if not isinstance(case_id, str) or not case_id:
        raise ValueError("fixture case id must be a non-empty string")
    if case_id in seen_case_ids:
        raise ValueError(f"duplicate case id '{case_id}'")
    if not isinstance(query, str) or not query:
        raise ValueError(f"case '{case_id}' query must be a non-empty string")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise ValueError(f"case '{case_id}' entries must be a non-empty list")
    if not isinstance(raw_expected, list) or not raw_expected:
        raise ValueError(f"case '{case_id}' expected_order must be a non-empty list")

    seen_case_ids.add(case_id)

    entry_ids: set[str] = set()
    entries = tuple(_parse_entry(item, case_id=case_id, entry_ids=entry_ids) for item in raw_entries)

    expected: list[str] = []
    for value in raw_expected:
        if not isinstance(value, str) or not value:
            raise ValueError(f"case '{case_id}' expected_order values must be non-empty strings")
        expected.append(value)

    expected_order = tuple(expected)
    if len(set(expected_order)) != len(expected_order):
        raise ValueError(f"case '{case_id}' expected_order has duplicate ids")
    if set(expected_order) != entry_ids:
        raise ValueError(
            f"case '{case_id}' expected_order must contain every entry id exactly once"
        )

    if raw_limit is None:
        limit = len(entries)
    elif isinstance(raw_limit, int) and raw_limit > 0:
        limit = raw_limit
    else:
        raise ValueError(f"case '{case_id}' limit must be a positive integer when provided")

    if raw_offset is None:
        offset = 0
    elif isinstance(raw_offset, int) and raw_offset >= 0:
        offset = raw_offset
    else:
        raise ValueError(f"case '{case_id}' offset must be a non-negative integer when provided")

    return FixtureCase(
        id=case_id,
        query=query,
        entries=entries,
        expected_order=expected_order,
        limit=limit,
        offset=offset,
    )


def load_fixture(path: Path | str) -> FixtureFile:
    fixture_path = Path(path)
    try:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid fixture json: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("fixture root must be an object")
    version = payload.get("version")
    raw_cases = payload.get("cases")
    if not isinstance(version, int):
        raise ValueError("fixture version must be an integer")
    if version != 1:
        raise ValueError(f"unsupported fixture version: {version}")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("fixture cases must be a non-empty list")

    seen_case_ids: set[str] = set()
    cases = tuple(_parse_case(item, seen_case_ids=seen_case_ids) for item in raw_cases)
    return FixtureFile(version=version, cases=cases)


def _slice_order(order: tuple[str, ...], *, limit: int, offset: int) -> tuple[str, ...]:
    return order[offset : offset + limit]


async def _evaluate_case(
    case: FixtureCase,
    *,
    persist_root: Path,
) -> CaseEvaluation:
    created_bridges: list[_BenchmarkBridge] = []
    current_time = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def bridge_factory(**_: object) -> _BenchmarkBridge:
        bridge = _BenchmarkBridge()
        created_bridges.append(bridge)
        return bridge

    def now_func() -> datetime:
        nonlocal current_time
        value = current_time
        current_time = current_time + timedelta(seconds=1)
        return value

    service = TerminalSessionService(
        bridge_factory=bridge_factory,
        reconnect_timeout_seconds=10.0,
        history_persist_root=persist_root / case.id,
        now_func=now_func,
    )

    entry_ids_by_session_id: dict[str, str] = {}

    for index, entry in enumerate(case.entries):
        session = await service.create_session(
            group_id=case.id,
            group_folder=case.id,
            owner_user_id="benchmark",
            requested_mode="container",
        )
        _record, queue = await service.attach_session(
            session.session_id,
            owner_user_id="benchmark",
        )
        await created_bridges[index].emit_output(entry.output)
        await asyncio.wait_for(queue.get(), timeout=0.5)
        await service.close_session(session.session_id, owner_user_id="benchmark")
        entry_ids_by_session_id[session.session_id] = entry.id

    page = await service.search_history_by_group(
        case.id,
        query=case.query,
        limit=max(len(case.entries), 1),
        offset=0,
    )
    actual_full_order = tuple(
        entry_ids_by_session_id[item.record.session_id]
        for item in page.items
        if item.record.session_id in entry_ids_by_session_id
    )
    expected_page = _slice_order(case.expected_order, limit=case.limit, offset=case.offset)
    actual_page = _slice_order(actual_full_order, limit=case.limit, offset=case.offset)
    passed = actual_page == expected_page

    expected_top = case.expected_order[0]
    if expected_top in actual_full_order:
        reciprocal_rank = 1.0 / (actual_full_order.index(expected_top) + 1)
    else:
        reciprocal_rank = 0.0
    top1_correct = bool(actual_full_order) and actual_full_order[0] == expected_top

    return CaseEvaluation(
        case_id=case.id,
        passed=passed,
        expected_order=expected_page,
        actual_order=actual_page,
        reciprocal_rank=reciprocal_rank,
        top1_correct=top1_correct,
    )


async def _evaluate_fixture_async(fixture: FixtureFile) -> EvaluationReport:
    with tempfile.TemporaryDirectory(prefix="terminal-relevance-benchmark-") as temp_dir:
        persist_root = Path(temp_dir)
        case_reports_list: list[CaseEvaluation] = []
        for case in fixture.cases:
            case_reports_list.append(await _evaluate_case(case, persist_root=persist_root))
        case_reports = tuple(case_reports_list)

    case_count = len(case_reports)
    pass_count = sum(1 for case in case_reports if case.passed)
    top1_count = sum(1 for case in case_reports if case.top1_correct)
    mrr_total = sum(case.reciprocal_rank for case in case_reports)

    return EvaluationReport(
        case_count=case_count,
        pass_count=pass_count,
        pass_rate=(pass_count / case_count) if case_count else 0.0,
        top1_accuracy=(top1_count / case_count) if case_count else 0.0,
        mrr=(mrr_total / case_count) if case_count else 0.0,
        cases=case_reports,
    )


def evaluate_fixture(fixture: FixtureFile) -> EvaluationReport:
    return asyncio.run(_evaluate_fixture_async(fixture))


def _format_text_report(report: EvaluationReport) -> str:
    lines = [
        f"case_count: {report.case_count}",
        f"pass_count: {report.pass_count}",
        f"pass_rate: {report.pass_rate:.3f}",
        f"top1_accuracy: {report.top1_accuracy:.3f}",
        f"mrr: {report.mrr:.3f}",
        "",
    ]
    for case in report.cases:
        status = "PASS" if case.passed else "FAIL"
        lines.append(
            f"[{status}] {case.case_id} expected={list(case.expected_order)} actual={list(case.actual_order)}"
        )
    return "\n".join(lines)


def _format_json_report(report: EvaluationReport) -> str:
    return json.dumps(asdict(report), ensure_ascii=False, indent=2, sort_keys=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture",
        type=Path,
        default=DEFAULT_FIXTURE_PATH,
        help="Path to baseline fixture json.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        fixture = load_fixture(args.fixture)
        report = evaluate_fixture(fixture)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    if args.format == "json":
        print(_format_json_report(report))
    else:
        print(_format_text_report(report))
    return 0 if report.pass_count == report.case_count else 1


if __name__ == "__main__":
    raise SystemExit(main())
