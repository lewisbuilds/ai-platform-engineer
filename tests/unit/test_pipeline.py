"""Unit tests for pipeline orchestration stub."""

from pathlib import Path

from pytest import MonkeyPatch

from ai_container_intelligence.integrations.layer_analysis_provider import LayerAnalysisResult
from ai_container_intelligence.models.findings import Finding, FindingLocation, Severity
from ai_container_intelligence.pipeline import run_pipeline


class _StaticLayerProvider:
    """Deterministic layer provider for pipeline tests."""

    def analyze(self, image_tar_path: str) -> LayerAnalysisResult:
        """Return one stable finding for image tar path.

        Args:
            image_tar_path: Path to image tarball.

        Returns:
            Layer analysis result with one low-severity finding.
        """
        _ = image_tar_path
        return LayerAnalysisResult(
            provider_name="test-layer",
            findings=[
                Finding(
                    rule_id="L001",
                    title="Layer metadata note",
                    severity=Severity.LOW,
                    source="test-layer",
                    detail="Layer provider path is exercised.",
                    remediation="No action required for test.",
                    location=FindingLocation(path="image.tar", line=1),
                )
            ],
        )


def test_run_pipeline_returns_expected_shapes() -> None:
    """Ensure pipeline returns findings list and report object."""
    result = run_pipeline(dockerfile_path="tests/fixtures/Dockerfile.good")
    assert isinstance(result.analysis_report.findings, list)
    assert result.report.title == "AI Container Intelligence Report"


def test_run_pipeline_includes_layer_provider_findings_for_image_tar() -> None:
    """Ensure image tar path triggers layer provider integration boundary."""
    result = run_pipeline(
        dockerfile_path="tests/fixtures/Dockerfile.good",
        image_tar_path="tests/fixtures/sample-image.tar",
        layer_provider=_StaticLayerProvider(),
    )
    assert any(item.rule_id == "L001" for item in result.analysis_report.findings)


def test_run_pipeline_report_ordering_is_deterministic(tmp_path: Path) -> None:
    """Ensure report findings are deterministically sorted by normalized model rules."""
    dockerfile_path = tmp_path / "Dockerfile"
    dockerfile_path.write_text(
        "\n".join(
            [
                "FROM python:latest",
                "USER root",
                "RUN apt-get update",
                "ADD . /app",
                "CMD python -V",
            ]
        ),
        encoding="utf-8",
    )
    first = run_pipeline(dockerfile_path=str(dockerfile_path))
    second = run_pipeline(dockerfile_path=str(dockerfile_path))
    first_rule_ids = [item.rule_id for item in first.analysis_report.findings]
    second_rule_ids = [item.rule_id for item in second.analysis_report.findings]
    assert first_rule_ids == second_rule_ids


def test_run_pipeline_defaults_to_real_tool_providers(monkeypatch: MonkeyPatch) -> None:
    """Ensure default provider wiring uses Syft and Trivy adapters via pipeline."""
    monkeypatch.setattr("ai_container_intelligence.integrations.sbom_provider.shutil.which", lambda _: None)
    monkeypatch.setattr(
        "ai_container_intelligence.integrations.vuln_scan_provider.shutil.which",
        lambda _: None,
    )

    result = run_pipeline(
        dockerfile_path="tests/fixtures/Dockerfile.good",
        image_ref="example:image",
    )

    rule_ids = {item.rule_id for item in result.analysis_report.findings}
    assert "SBOM001" in rule_ids
    assert "VULN001" in rule_ids


def test_run_pipeline_noop_profile_uses_noop_providers() -> None:
    """Ensure noop profile avoids real adapter findings and remains deterministic."""
    result = run_pipeline(
        dockerfile_path="tests/fixtures/Dockerfile.good",
        image_ref="example:image",
        provider_profile="noop",
    )
    rule_ids = {item.rule_id for item in result.analysis_report.findings}
    assert "SBOM001" not in rule_ids
    assert "VULN001" not in rule_ids
