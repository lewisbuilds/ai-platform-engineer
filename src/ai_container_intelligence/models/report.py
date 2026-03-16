"""Report model types."""

from dataclasses import dataclass

from ai_container_intelligence.models.findings import Finding, Severity, finding_sort_key


@dataclass(frozen=True)
class ReportSection:
    """A markdown report section.

    Args:
        title: Section heading.
        body: Section body in markdown-safe text.
    """

    title: str
    body: str


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
        low: Count of low findings.
        medium: Count of medium findings.
        high: Count of high findings.
        critical: Count of critical findings.
    """

    low: int
    medium: int
    high: int
    critical: int


@dataclass(frozen=True)
class AnalysisReport:
    """Normalized internal report model.

    Args:
        title: Report title.
        findings: Deterministically sorted findings.
        summary: Severity count summary.
    """

    title: str
    findings: list[Finding]
    summary: SeveritySummary


def summarize_findings(findings: list[Finding]) -> SeveritySummary:
    """Create severity summary for a finding collection.

    Args:
        findings: Findings to summarize.

    Returns:
        Severity summary counts.
    """
    return SeveritySummary(
        low=sum(1 for item in findings if item.severity == Severity.LOW),
        medium=sum(1 for item in findings if item.severity == Severity.MEDIUM),
        high=sum(1 for item in findings if item.severity == Severity.HIGH),
        critical=sum(1 for item in findings if item.severity == Severity.CRITICAL),
    )


def create_analysis_report(title: str, findings: list[Finding]) -> AnalysisReport:
    """Create normalized report with deterministic ordering.

    Args:
        title: Report title.
        findings: Unordered finding list.

    Returns:
        Analysis report with sorted findings and summary.
    """
    ordered = sorted(findings, key=finding_sort_key)
    summary = summarize_findings(ordered)
    return AnalysisReport(title=title, findings=ordered, summary=summary)
