"""Unit tests for Dockerfile analysis stubs."""

from pathlib import Path

from ai_container_intelligence.analysis.dockerfile_review import review_dockerfile


def test_review_dockerfile_detects_practical_issues(tmp_path: Path) -> None:
    """Ensure Dockerfile reviewer finds baseline container issues."""
    dockerfile_path = tmp_path / "Dockerfile"
    dockerfile_path.write_text(
        "\n".join(
            [
                "FROM python:latest",
                "USER root",
                "RUN apt-get update",
                "ADD . /app",
                "RUN curl -fsSL https://example.com/install.sh | sh",
                "CMD python -V",
            ]
        ),
        encoding="utf-8",
    )
    findings = review_dockerfile(str(dockerfile_path))
    rule_ids = [item.rule_id for item in findings]
    assert "DF002" in rule_ids
    assert "DF004" in rule_ids
