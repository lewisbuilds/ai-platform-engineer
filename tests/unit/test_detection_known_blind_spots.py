"""Known detection blind-spot tests tracked as expected failures."""

from pathlib import Path
from typing import Final

import pytest

from ai_container_intelligence.analysis.dockerfile_review import review_dockerfile


FIXTURES_DIR: Final[Path] = Path(__file__).resolve().parents[1] / "fixtures" / "golden"


@pytest.mark.xfail(
    reason=(
        "Current parser is line-based and does not compose multiline RUN commands; "
        "DF006 may false-positive when apt cleanup appears on subsequent continuation lines."
    ),
    strict=False,
)
def test_multiline_run_with_cleanup_should_not_trigger_df006() -> None:
    """Document current false-positive risk for multiline RUN sequences."""
    fixture_path = FIXTURES_DIR / "realworld-multiline-run-cleanup.Dockerfile"
    findings = review_dockerfile(str(fixture_path))
    assert "DF006" not in {item.rule_id for item in findings}
