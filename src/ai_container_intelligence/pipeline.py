"""Pipeline orchestration for local and CI execution."""

from dataclasses import dataclass
from typing import Literal

from ai_container_intelligence.analysis.dockerfile_review import review_dockerfile
from ai_container_intelligence.integrations.layer_analysis_provider import (
    LayerAnalysisProvider,
)
from ai_container_intelligence.integrations.provider_selection import select_providers
from ai_container_intelligence.integrations.sbom_provider import (
    SbomProvider,
)
from ai_container_intelligence.integrations.vuln_scan_provider import (
    VulnerabilityScanProvider,
)
from ai_container_intelligence.models.report import (
    AnalysisReport,
    MarkdownReport,
    create_analysis_report,
)
from ai_container_intelligence.policy import (
    PolicyProfile,
    evaluate_findings_policy,
    resolve_policy_config,
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
    provider_profile: Literal["real", "noop"] = "real",
    policy_profile: PolicyProfile = "strict",
    layer_provider: LayerAnalysisProvider | None = None,
    sbom_provider: SbomProvider | None = None,
    vulnerability_provider: VulnerabilityScanProvider | None = None,
) -> PipelineResult:
    """Run pipeline by composing analyzers and replaceable integrations.

    Args:
        dockerfile_path: Path to the Dockerfile input.
        image_tar_path: Optional path to image tarball input.
        image_ref: Optional image reference for SBOM and vulnerability providers.
        provider_profile: Provider profile used when explicit providers are not injected.
        policy_profile: Built-in policy profile for blocking/advisory decisions.
        layer_provider: Layer analysis provider.
        sbom_provider: SBOM provider.
        vulnerability_provider: Vulnerability scan provider.

    Returns:
        Pipeline result with normalized report and markdown render.
    """
    selected = select_providers(
        profile=provider_profile,
        layer_provider=layer_provider,
        sbom_provider=sbom_provider,
        vulnerability_provider=vulnerability_provider,
    )

    findings = review_dockerfile(dockerfile_path)

    if image_tar_path:
        findings.extend(selected.layer_provider.analyze(image_tar_path))

    if image_ref:
        findings.extend(selected.sbom_provider.generate(image_ref))
        findings.extend(selected.vulnerability_provider.scan(image_ref))

    policy_evaluation = evaluate_findings_policy(
        findings,
        policy=resolve_policy_config(policy_profile),
    )

    analysis_report = create_analysis_report(
        title="AI Container Intelligence Report",
        findings=policy_evaluation.findings,
        policy_summary=policy_evaluation.summary,
    )
    markdown_report = render_markdown_report(analysis_report)
    return PipelineResult(analysis_report=analysis_report, report=markdown_report)
