"""Pipeline orchestration for local and CI execution."""

from dataclasses import dataclass

from ai_container_intelligence.analysis.dockerfile_review import review_dockerfile
from ai_container_intelligence.integrations.layer_analysis_provider import (
    LayerAnalysisProvider,
    NoopLayerAnalysisProvider,
)
from ai_container_intelligence.integrations.sbom_provider import NoopSbomProvider, SbomProvider
from ai_container_intelligence.integrations.vuln_scan_provider import (
    NoopVulnerabilityScanProvider,
    VulnerabilityScanProvider,
)
from ai_container_intelligence.models.findings import Finding
from ai_container_intelligence.models.report import (
    AnalysisReport,
    MarkdownReport,
    create_analysis_report,
)
from ai_container_intelligence.reporting.markdown_report import render_markdown_report


@dataclass(frozen=True)
class PipelineResult:
    """Output envelope for the analysis pipeline.

    Args:
        analysis_report: Normalized analysis report.
        report: Rendered markdown report.
    """

    analysis_report: AnalysisReport
    report: MarkdownReport


def run_pipeline(
    dockerfile_path: str,
    image_tar_path: str | None = None,
    image_ref: str | None = None,
    layer_provider: LayerAnalysisProvider | None = None,
    sbom_provider: SbomProvider | None = None,
    vulnerability_provider: VulnerabilityScanProvider | None = None,
) -> PipelineResult:
    """Run pipeline by composing analyzers and replaceable integrations.

    Args:
        dockerfile_path: Path to the Dockerfile input.
        image_tar_path: Optional path to image tarball input.
        image_ref: Optional image reference for SBOM and vulnerability providers.
        layer_provider: Layer analysis provider.
        sbom_provider: SBOM provider.
        vulnerability_provider: Vulnerability scan provider.

    Returns:
        Pipeline result with normalized report and markdown render.
    """
    selected_layer_provider = layer_provider or NoopLayerAnalysisProvider()
    selected_sbom_provider = sbom_provider or NoopSbomProvider()
    selected_vulnerability_provider = vulnerability_provider or NoopVulnerabilityScanProvider()

    findings: list[Finding] = []
    findings.extend(review_dockerfile(dockerfile_path))

    if image_tar_path:
        layer_result = selected_layer_provider.analyze(image_tar_path)
        findings.extend(layer_result.findings)

    if image_ref:
        sbom_result = selected_sbom_provider.generate(image_ref)
        findings.extend(sbom_result.findings)
        vulnerability_result = selected_vulnerability_provider.scan(image_ref)
        findings.extend(vulnerability_result.findings)

    analysis_report = create_analysis_report(
        title="AI Container Intelligence Report",
        findings=findings,
    )
    markdown_report = render_markdown_report(analysis_report)
    return PipelineResult(analysis_report=analysis_report, report=markdown_report)
