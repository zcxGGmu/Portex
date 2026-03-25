from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_load_fixture_reads_version_and_cases() -> None:
    from scripts import evaluate_terminal_relevance

    fixture = evaluate_terminal_relevance.load_fixture(
        PROJECT_ROOT / "tests" / "fixtures" / "terminal_relevance_baseline.json"
    )

    assert fixture.version == 1
    assert len(fixture.cases) == 70
    assert fixture.cases[0].id == "raw-marker-priority"
    assert {
        "non-square-wrapper-marker-family-ladder",
        "single-space-separator-quality-ladder",
        "exact-tag-punctuation-noise-cleanliness",
        "m8-5-49-other-leading-whitespace-offset-pagination",
        "payloadless-separator-quality",
        "tab-prefixed-payload-offset-pagination",
        "multi-space-payload-offset-pagination",
        "space-prefixed-mixed-whitespace-offset-pagination",
        "exact-tag-colon-marker-pagination",
        "square-bracket-dash-marker-pagination",
        "square-bracket-exact-tag-pagination",
        "paren-plain-wrapper-pagination",
        "exact-tag-colon-marker-offset-tie-break",
        "square-bracket-dash-marker-offset-tie-break",
        "paren-plain-wrapper-offset-tie-break",
        "square-bracket-plain-exact-tag-offset-tie-break",
        "non-square-colon-marker-pagination",
        "non-square-colon-marker-offset-tie-break",
        "non-square-dash-marker-pagination",
        "non-square-dash-marker-offset-tie-break",
        "brace-wrapper-marker-pagination",
        "brace-wrapper-marker-offset-tie-break",
        "brace-plain-exact-tag-pagination",
        "angle-plain-exact-tag-offset-pagination",
        "brace-plain-exact-tag-offset-tie-break",
        "angle-plain-exact-tag-pagination",
        "no-brace-wrapper-marker-fallback",
        "no-angle-plain-exact-tag-fallback",
        "brace-wrapper-marker-pairwise",
        "brace-plain-exact-tag-pairwise",
        "no-brace-plain-exact-tag-fallback",
        "angle-plain-exact-tag-offset-tie-break",
        "no-whole-word-fallback-to-m8-5-17",
        "no-line-start-whole-word-fallback-to-m8-5-18",
        "exact-tag-wrapper-delimiter-quality",
        "raw-marker-delimiter-quality",
        "whole-word-priority",
        "whole-word-offset-tie-break",
        "line-start-whole-word-priority",
        "line-start-whole-word-offset-tie-break",
        "no-exact-tag-wrapper-fallback",
        "whole-word-pagination",
        "line-boundary-pagination",
        "line-start-quality-pagination",
        "log-marker-pagination",
        "punctuation-wrap-pagination",
        "exact-tag-pagination",
        "exact-tag-marker-pagination",
        "delimited-log-marker-pagination",
        "exact-tag-punctuation-noise-pagination",
        "single-space-plain-exact-tag-pagination",
        "separator-noise-pagination",
        "payloadless-plain-exact-tag-separator-pagination",
        "payloadless-offset-tie-break-pagination",
        "tab-prefixed-payload-pagination",
        "square-bracket-plain-exact-tag-offset-pagination",
        "multi-space-payload-pagination",
        "space-prefixed-mixed-whitespace-payload-pagination",
        "tab-prefixed-payload-no-single-space-fallback",
        "multi-space-payload-no-single-space-fallback",
        "space-prefixed-mixed-whitespace-no-single-space-fallback",
        "other-leading-whitespace-no-single-space-fallback",
    }.issubset({case.id for case in fixture.cases})


def test_evaluate_fixture_returns_expected_summary_metrics() -> None:
    from scripts import evaluate_terminal_relevance

    fixture = evaluate_terminal_relevance.load_fixture(
        PROJECT_ROOT / "tests" / "fixtures" / "terminal_relevance_baseline.json"
    )
    report = evaluate_terminal_relevance.evaluate_fixture(fixture)

    assert report.case_count == 70
    assert report.pass_count == 70
    assert report.pass_rate == 1.0
    assert report.top1_accuracy == 1.0
    assert report.mrr == 1.0
    assert all(case.passed for case in report.cases)


def test_main_returns_non_zero_when_fixture_expectations_fail(tmp_path: Path) -> None:
    from scripts import evaluate_terminal_relevance

    fixture_path = tmp_path / "bad-baseline.json"
    fixture_path.write_text(
        json.dumps(
            {
                "version": 1,
                "cases": [
                    {
                        "id": "intentionally-wrong-order",
                        "query": "error",
                        "entries": [
                            {"id": "raw-marker", "output": "error: startup failed\n"},
                            {"id": "plain-exact-tag", "output": "[error] startup failed\n"},
                        ],
                        "expected_order": ["plain-exact-tag", "raw-marker"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    exit_code = evaluate_terminal_relevance.main(
        ["--fixture", str(fixture_path), "--format", "json"]
    )

    assert exit_code == 1
