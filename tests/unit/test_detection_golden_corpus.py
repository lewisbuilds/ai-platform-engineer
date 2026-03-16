"""Golden corpus tests for detection-quality baselining."""

import json
from pathlib import Path
from typing import Final

import pytest

from ai_container_intelligence.analysis.dockerfile_review import review_dockerfile


FIXTURES_DIR: Final[Path] = Path(__file__).resolve().parents[1] / "fixtures" / "golden"
CASES_FILE: Final[Path] = FIXTURES_DIR / "corpus_cases.json"


def _load_detection_cases() -> list[tuple[str, set[str], set[str]]]:
    payload = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    return [
        (
            item["fixture_name"],
            set(item["expected_rules"]),
            set(item["unexpected_rules"]),
        )
        for item in payload
    ]


@pytest.mark.parametrize(
    ("fixture_name", "expected_rules", "unexpected_rules"),
    _load_detection_cases(),
)
def test_detection_golden_corpus(
    fixture_name: str,
    expected_rules: set[str],
    unexpected_rules: set[str],
) -> None:
    """Assert expected and non-expected rule behavior over curated fixtures."""
    fixture_path = FIXTURES_DIR / fixture_name
    findings = review_dockerfile(str(fixture_path))
    rule_ids = {item.rule_id for item in findings}

    missing = expected_rules - rule_ids
    unexpected = rule_ids & unexpected_rules

    assert not missing, f"Missing expected rules for {fixture_name}: {sorted(missing)}"
    assert not unexpected, (
        f"Unexpected rules for {fixture_name}: {sorted(unexpected)}"
    )
