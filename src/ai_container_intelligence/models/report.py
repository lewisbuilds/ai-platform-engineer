"""Report model types."""

from dataclasses import dataclass

from ai_container_intelligence.models.findings import Finding, Severity, finding_sort_key


@dataclass(frozen=True)
class MarkdownReport:
    """Complete markdown report output.

    Args:
        title: Report title.
        content: Full markdown content.
    """

    title: str
    content: str


@dataclass(frozen=True)
class SeveritySummary:
    """Count summary by severity.

    Args:
        info: Count of info findings.
        low: Count of low findings.
        medium: Count of medium findings.
        high: Count of high findings.
        critical: Count of critical findings.
    """

    info: int
    low: int
    medium: int
    high: int
    critical: int


@dataclass(frozen=True)
class PolicyImpactSummary:
    """Policy impact summary for CI decisions.

    Args:
        advisory: Count of advisory findings.
        blocking: Count of blocking findings.
        blocking_rule_ids: Deterministic set of blocking rule identifiers.
        blocking_threshold: Human-readable threshold label.
        should_fail: Whether CI should fail for this report.
    """

    advisory: int
    blocking: int
    blocking_rule_ids: tuple[str, ...]
    blocking_threshold: str
    should_fail: bool


@dataclass(frozen=True)
class AnalysisReport:
    """Normalized internal report model.

    Args:
        title: Report title.
        findings: Deterministically sorted findings.
        summary: Severity count summary.
        policy_summary: Optional policy impact summary.
    """

    title: str
    findings: list[Finding]
    summary: SeveritySummary
    policy_summary: PolicyImpactSummary | None = None


def summarize_findings(findings: list[Finding]) -> SeveritySummary:
    """Create severity summary for a finding collection.

    Args:
        findings: Findings to summarize.

    Returns:
        Severity summary counts.
    """
    return SeveritySummary(
        info=sum(1 for item in findings if item.severity == Severity.INFO),
        low=sum(1 for item in findings if item.severity == Severity.LOW),
        medium=sum(1 for item in findings if item.severity == Severity.MEDIUM),
        high=sum(1 for item in findings if item.severity == Severity.HIGH),
        critical=sum(1 for item in findings if item.severity == Severity.CRITICAL),
    )


def create_analysis_report(
    title: str,
    findings: list[Finding],
    policy_summary: PolicyImpactSummary | None = None,
) -> AnalysisReport:
    """Create normalized report with deterministic ordering.

    Args:
        title: Report title.
        findings: Unordered finding list.

    Returns:
        Analysis report with sorted findings and summary.
    """
    ordered = sorted(findings, key=finding_sort_key)
    summary = summarize_findings(ordered)
    return AnalysisReport(
        title=title,
        findings=ordered,
        summary=summary,
        policy_summary=policy_summary,
    )
