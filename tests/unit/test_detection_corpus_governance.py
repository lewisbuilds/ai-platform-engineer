"""Governance checks for keeping the detection corpus representative."""

import json
from pathlib import Path
from typing import Final

from ai_container_intelligence.analysis import DOCKERFILE_REVIEW_RULE_IDS
from ai_container_intelligence.analysis.dockerfile_review import review_dockerfile


FIXTURES_DIR: Final[Path] = Path(__file__).resolve().parents[1] / "fixtures" / "golden"
CASES_FILE: Final[Path] = FIXTURES_DIR / "corpus_cases.json"
BASELINE_RULES: Final[set[str]] = set(DOCKERFILE_REVIEW_RULE_IDS)


def _load_detection_cases() -> list[dict[str, object]]:
    payload = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    return list(payload)


def _expected_rules(case: dict[str, object]) -> list[str]:
    raw = case.get("expected_rules", [])
    return [str(item) for item in raw] if isinstance(raw, list) else []


def _fixture_names() -> list[str]:
    return sorted(path.name for path in FIXTURES_DIR.glob("*.Dockerfile"))


def test_corpus_has_balanced_case_types() -> None:
    """Require curated good/bad/realworld fixture coverage."""
    names = _fixture_names()
    assert any(name.startswith("good-") for name in names)
    assert any(name.startswith("bad-") for name in names)
    assert sum(1 for name in names if name.startswith("realworld-")) >= 3


def test_corpus_exercises_baseline_rule_surface() -> None:
    """Ensure corpus can still trigger the baseline Dockerfile rule set."""
    triggered_rules: set[str] = set()
    for fixture in FIXTURES_DIR.glob("*.Dockerfile"):
        findings = review_dockerfile(str(fixture))
        triggered_rules.update(item.rule_id for item in findings)

    missing = BASELINE_RULES - triggered_rules
    assert not missing, f"Corpus no longer exercises baseline rules: {sorted(missing)}"


def test_corpus_includes_clean_and_dirty_samples() -> None:
    """Ensure corpus includes both no-finding and multi-finding examples."""
    finding_counts = [
        len(review_dockerfile(str(fixture)))
        for fixture in FIXTURES_DIR.glob("*.Dockerfile")
    ]
    assert any(count == 0 for count in finding_counts)
    assert any(count >= 2 for count in finding_counts)


def test_every_dockerfile_rule_has_expected_finding_corpus_coverage() -> None:
    """Require each implemented Dockerfile rule to appear in expected-finding corpus cases."""
    expected_finding_rule_ids = {
        rule_id
        for item in _load_detection_cases()
        for rule_id in _expected_rules(item)
    }

    missing = set(DOCKERFILE_REVIEW_RULE_IDS) - expected_finding_rule_ids
    assert not missing, (
        "Rule IDs missing expected-finding corpus coverage: "
        + ", ".join(sorted(missing))
    )
