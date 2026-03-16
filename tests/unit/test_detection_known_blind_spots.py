"""Known detection blind-spot tests tracked as expected failures."""

from pathlib import Path

import pytest

from ai_container_intelligence.analysis.dockerfile_review import review_dockerfile


@pytest.mark.xfail(
    reason=(
        "Current parser is line-based and does not compose multiline RUN commands; "
        "DF006 may false-positive when apt cleanup appears on subsequent continuation lines."
    ),
    strict=False,
)
def test_multiline_run_with_cleanup_should_not_trigger_df006(tmp_path: Path) -> None:
    """Document current false-positive risk for multiline RUN sequences."""
    dockerfile_path = tmp_path / "Dockerfile"
    dockerfile_path.write_text(
        "\n".join(
            [
                "FROM python:3.11.8-slim",
                "RUN apt-get update && \\",
                "    apt-get install -y curl && \\",
                "    rm -rf /var/lib/apt/lists/*",
                "USER 10001",
            ]
        ),
        encoding="utf-8",
    )

    findings = review_dockerfile(str(dockerfile_path))
    assert "DF006" not in {item.rule_id for item in findings}
