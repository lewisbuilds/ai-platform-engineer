"""Markdown report rendering."""

from ai_container_intelligence.models.findings import Finding, FindingLocation
from ai_container_intelligence.models.report import AnalysisReport, MarkdownReport


def _format_location(location: FindingLocation | None) -> str:
    """Format optional location metadata.

    Args:
        location: Optional finding location.

    Returns:
        Deterministic location label.
    """
    if location is None:
        return "n/a"
    if location.line is None:
        return location.path
    return f"{location.path}:{location.line}"


def _format_finding_row(index: int, finding: Finding) -> str:
    """Format one finding row.

    Args:
        index: 1-based finding index.
        finding: Finding to format.

    Returns:
        Markdown row text.
    """
    location_label = _format_location(finding.location)
    return (
        f"{index}. [{finding.severity.value.upper()}] {finding.rule_id} - {finding.title}\n"
        f"   - Source: {finding.source}\n"
        f"   - Location: {location_label}\n"
        f"   - Detail: {finding.detail}\n"
        f"   - Remediation: {finding.remediation}"
    )


def render_markdown_report(report: AnalysisReport) -> MarkdownReport:
    """Render normalized analysis report into markdown.

    Args:
        report: Normalized internal analysis report.

    Returns:
        Markdown report object.
    """
    header = f"# {report.title}"
    summary_lines = [
        "## Summary",
        f"- Total findings: {len(report.findings)}",
        f"- Critical: {report.summary.critical}",
        f"- High: {report.summary.high}",
        f"- Medium: {report.summary.medium}",
        f"- Low: {report.summary.low}",
    ]

    if not report.findings:
        findings_block = ["## Findings", "No findings detected."]
    else:
        findings_block = ["## Findings"]
        for index, finding in enumerate(report.findings, start=1):
            findings_block.append(_format_finding_row(index, finding))

    content = "\n\n".join([header, "\n".join(summary_lines), "\n".join(findings_block)]) + "\n"
    return MarkdownReport(title=report.title, content=content)
