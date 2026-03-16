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
        f"   - Policy: {finding.disposition.value.upper()}\n"
        f"   - Source: {finding.source}\n"
        f"   - Location: {location_label}\n"
        f"   - Detail: {finding.detail}\n"
        f"   - Remediation: {finding.remediation}"
    )


def _build_remediation_summary(findings: list[Finding]) -> list[str]:
    """Build concise remediation-oriented summary for PR scanning.

    Args:
        findings: Evaluated findings.

    Returns:
        Markdown lines for remediation summary section.
    """
    if not findings:
        return ["## Remediation Summary", "No remediation actions required."]

    remediation_map: dict[str, dict[str, int | bool]] = {}
    for finding in findings:
        key = finding.remediation
        if key not in remediation_map:
            remediation_map[key] = {"count": 0, "blocking": False}
        remediation_map[key]["count"] = int(remediation_map[key]["count"]) + 1
        if finding.disposition.value == "blocking":
            remediation_map[key]["blocking"] = True

    ordered = sorted(
        remediation_map.items(),
        key=lambda item: (
            0 if bool(item[1]["blocking"]) else 1,
            -int(item[1]["count"]),
            item[0],
        ),
    )

    lines = ["## Remediation Summary"]
    for index, (remediation, stats) in enumerate(ordered[:3], start=1):
        status = "BLOCKING" if bool(stats["blocking"]) else "ADVISORY"
        lines.append(
            f"{index}. [{status}] ({int(stats['count'])} finding(s)) {remediation}"
        )
    return lines


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
        f"- Info: {report.summary.info}",
        f"- Critical: {report.summary.critical}",
        f"- High: {report.summary.high}",
        f"- Medium: {report.summary.medium}",
        f"- Low: {report.summary.low}",
    ]

    policy_lines: list[str] = []
    if report.policy_summary is not None:
        blocking_rule_ids = ", ".join(report.policy_summary.blocking_rule_ids)
        policy_lines = [
            "## Policy Impact",
            f"- Blocking findings: {report.policy_summary.blocking}",
            f"- Advisory findings: {report.policy_summary.advisory}",
            f"- Blocking threshold: {report.policy_summary.blocking_threshold}",
            (
                f"- Blocking rule IDs: {blocking_rule_ids}"
                if blocking_rule_ids
                else "- Blocking rule IDs: none"
            ),
            (
                "- CI recommendation: FAIL"
                if report.policy_summary.should_fail
                else "- CI recommendation: PASS"
            ),
        ]

    if not report.findings:
        findings_block = ["## Findings", "No findings detected."]
    else:
        findings_block = ["## Findings"]
        for index, finding in enumerate(report.findings, start=1):
            findings_block.append(_format_finding_row(index, finding))

    remediation_block = _build_remediation_summary(report.findings)

    sections = [header, "\n".join(summary_lines)]
    if policy_lines:
        sections.append("\n".join(policy_lines))
    sections.append("\n".join(remediation_block))
    sections.append("\n".join(findings_block))

    content = "\n\n".join(sections) + "\n"
    return MarkdownReport(title=report.title, content=content)
