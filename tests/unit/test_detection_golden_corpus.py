"""Golden corpus tests for detection-quality baselining."""

from pathlib import Path
from typing import Final

import pytest

from ai_container_intelligence.analysis.dockerfile_review import review_dockerfile


FIXTURES_DIR: Final[Path] = Path(__file__).resolve().parents[1] / "fixtures" / "golden"


@pytest.mark.parametrize(
    ("fixture_name", "expected_rules", "unexpected_rules"),
    [
        ("good-pinned-nonroot.Dockerfile", set(), {"DF001", "DF002", "DF003", "DF004", "DF005", "DF006", "DF007"}),
        ("bad-latest-root.Dockerfile", {"DF002", "DF004"}, set()),
        ("bad-missing-from.Dockerfile", {"DF001", "DF003"}, set()),
        ("bad-missing-user.Dockerfile", {"DF003"}, {"DF002", "DF004"}),
        ("bad-add-apt-cache.Dockerfile", {"DF005", "DF006"}, set()),
        ("bad-remote-pipe.Dockerfile", {"DF007"}, set()),
    ],
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
