"""Markdown report rendering."""

from typing import Final

from ai_container_intelligence.models.findings import Finding, FindingLocation
from ai_container_intelligence.models.report import AnalysisReport, MarkdownReport


POLICY_PASS: Final[str] = "PASS"
POLICY_WARN: Final[str] = "WARN"
POLICY_FAIL: Final[str] = "FAIL"


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
    lines = [
        f"{index}. [{finding.severity.value.upper()}] {finding.rule_id} - {finding.title}",
        f"   - Policy: {finding.disposition.value.upper()}",
        f"   - Source: {finding.source}",
        f"   - Location: {location_label}",
        f"   - Why this is risky: {finding.detail}",
        f"   - How to fix it: {finding.remediation}",
    ]
    if finding.evidence:
        lines.append("   - Evidence:")
        for key in sorted(finding.evidence):
            lines.append(f"      - {key}: {finding.evidence[key]}")
    return "\n".join(lines)


def _resolve_policy_profile_label(report: AnalysisReport) -> str | None:
    """Resolve explicit policy profile label when available.

    Args:
        report: Normalized analysis report.

    Returns:
        Explicit policy profile label or None when unknown.
    """
    if report.policy_summary is None:
        return None
    return report.policy_summary.policy_profile_label


def _format_core_evidence(finding: Finding) -> str:
    """Create one compact evidence line for decision trace output.

    Args:
        finding: Finding being rendered.

    Returns:
        Compact evidence summary string.
    """
    if finding.evidence:
        pairs = [f"{key}={finding.evidence[key]}" for key in sorted(finding.evidence)]
        return ", ".join(pairs)

    location_label = _format_location(finding.location)
    return f"source={finding.source}, location={location_label}"


def _format_blocking_decision_trace(report: AnalysisReport, finding: Finding) -> str:
    """Format concise policy decision trace for one blocking finding.

    Args:
        report: Normalized analysis report.
        finding: Blocking finding.

    Returns:
        Multiline markdown trace block.
    """
    lines = [
        "   - Decision trace:",
        f"      - rule ID: {finding.rule_id}",
        f"      - severity: {finding.severity.value.upper()}",
    ]
    profile_label = _resolve_policy_profile_label(report)
    if profile_label is not None:
        lines.append(f"      - policy profile: {profile_label}")
    lines.extend(
        [
            "      - blocking status: blocking",
            f"      - core evidence: {_format_core_evidence(finding)}",
            f"      - why this failed: {finding.detail}",
            f"      - how to fix it: {finding.remediation}",
        ]
    )
    return "\n".join(lines)


def _determine_policy_outcome(report: AnalysisReport) -> str:
    """Determine policy outcome label for CI-facing summary.

    Args:
        report: Normalized analysis report.

    Returns:
        PASS, WARN, or FAIL outcome label.
    """
    if report.policy_summary is not None:
        if report.policy_summary.should_fail:
            return POLICY_FAIL
        if report.policy_summary.advisory > 0:
            return POLICY_WARN
        return POLICY_PASS

    if report.findings:
        return POLICY_WARN
    return POLICY_PASS


def _build_findings_section(
    title: str,
    findings: list[Finding],
    report: AnalysisReport,
) -> list[str]:
    """Build a grouped finding section.

    Args:
        title: Section title.
        findings: Findings to render.

    Returns:
        Markdown lines for grouped findings.
    """
    lines = [title]
    if not findings:
        lines.append("None.")
        return lines

    for index, finding in enumerate(findings, start=1):
        lines.append(_format_finding_row(index=index, finding=finding))
        if finding.disposition.value == "blocking":
            lines.append(_format_blocking_decision_trace(report=report, finding=finding))
    return lines


def render_markdown_report(report: AnalysisReport) -> MarkdownReport:
    """Render normalized analysis report into markdown.

    Args:
        report: Normalized internal analysis report.

    Returns:
        Markdown report object.
    """
    header = f"# {report.title}"
    policy_outcome = _determine_policy_outcome(report)
    summary_lines = [
        "## Summary",
        f"- Total findings: {len(report.findings)}",
        f"- Info: {report.summary.info}",
        f"- Critical: {report.summary.critical}",
        f"- High: {report.summary.high}",
        f"- Medium: {report.summary.medium}",
        f"- Low: {report.summary.low}",
    ]
    policy_outcome_lines = [
        "## Policy Outcome Summary",
        f"- Outcome: {policy_outcome}",
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

    blocking_findings = [
        item for item in report.findings if item.disposition.value == "blocking"
    ]
    advisory_findings = [
        item for item in report.findings if item.disposition.value == "advisory"
    ]

    blocking_section = _build_findings_section(
        "## Blocking Findings",
        blocking_findings,
        report,
    )
    advisory_section = _build_findings_section(
        "## Advisory Findings",
        advisory_findings,
        report,
    )

    sections = [header, "\n".join(summary_lines), "\n".join(policy_outcome_lines)]
    if policy_lines:
        sections.append("\n".join(policy_lines))
    sections.append("\n".join(blocking_section))
    sections.append("\n".join(advisory_section))

    content = "\n\n".join(sections) + "\n"
    return MarkdownReport(title=report.title, content=content)
