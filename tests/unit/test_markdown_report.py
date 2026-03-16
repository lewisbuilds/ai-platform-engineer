"""Unit tests for markdown report rendering."""

from ai_container_intelligence.models.findings import Finding, FindingLocation, Severity
from ai_container_intelligence.models.report import create_analysis_report
from ai_container_intelligence.policy.evaluator import evaluate_findings_policy
from ai_container_intelligence.reporting.markdown_report import render_markdown_report


def test_render_markdown_report_contains_title() -> None:
    """Ensure report renderer includes top-level title."""
    internal_report = create_analysis_report("AI Container Intelligence Report", [])
    markdown = render_markdown_report(internal_report)
    assert "AI Container Intelligence Report" in markdown.content
    assert "Total findings: 0" in markdown.content
    assert "Info: 0" in markdown.content
    assert "Policy Impact" not in markdown.content


def test_render_markdown_report_includes_policy_impact_and_disposition() -> None:
    """Ensure report shows policy summary and per-finding policy disposition."""
    findings = [
        Finding(
            rule_id="DF004",
            title="Container configured to run as root",
            severity=Severity.HIGH,
            source="dockerfile-review",
            detail="Running as root increases attack surface.",
            remediation="Use a non-root runtime user.",
            location=FindingLocation(path="Dockerfile", line=1),
        )
    ]
    policy_evaluation = evaluate_findings_policy(findings)
    internal_report = create_analysis_report(
        "AI Container Intelligence Report",
        policy_evaluation.findings,
        policy_summary=policy_evaluation.summary,
    )

    markdown = render_markdown_report(internal_report)

    assert "## Policy Impact" in markdown.content
    assert "Blocking findings: 1" in markdown.content
    assert "CI recommendation: FAIL" in markdown.content
    assert "Blocking rule IDs: DF004" in markdown.content
    assert "Policy: BLOCKING" in markdown.content
