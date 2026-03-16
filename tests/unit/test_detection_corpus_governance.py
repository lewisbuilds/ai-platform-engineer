"""Governance checks for keeping the detection corpus representative."""

from pathlib import Path
from typing import Final

from ai_container_intelligence.analysis.dockerfile_review import review_dockerfile


FIXTURES_DIR: Final[Path] = Path(__file__).resolve().parents[1] / "fixtures" / "golden"
BASELINE_RULES: Final[set[str]] = {"DF001", "DF002", "DF003", "DF004", "DF005", "DF006", "DF007"}


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
