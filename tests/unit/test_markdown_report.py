"""Unit tests for markdown report rendering."""

from ai_container_intelligence.models.findings import (
    Finding,
    FindingDisposition,
    FindingLocation,
    Severity,
)
from ai_container_intelligence.models.report import create_analysis_report
from ai_container_intelligence.policy.evaluator import evaluate_findings_policy
from ai_container_intelligence.reporting.markdown_report import render_markdown_report


def test_render_markdown_report_renders_policy_outcome_pass() -> None:
    """Render PASS policy outcome when no blocking or advisory findings exist."""
    policy_evaluation = evaluate_findings_policy([])
    internal_report = create_analysis_report(
        "AI Container Intelligence Report",
        policy_evaluation.findings,
        policy_summary=policy_evaluation.summary,
    )

    markdown = render_markdown_report(internal_report)
    assert "## Policy Outcome Summary" in markdown.content
    assert "- Outcome: PASS" in markdown.content
    assert "## Blocking Findings" in markdown.content
    assert "## Advisory Findings" in markdown.content
    assert "None." in markdown.content


def test_render_markdown_report_renders_policy_outcome_warn() -> None:
    """Render WARN policy outcome when advisory findings exist without blockers."""
    findings = [
        Finding(
            rule_id="DF099",
            title="Informational policy note",
            severity=Severity.LOW,
            source="dockerfile-review",
            detail="A non-blocking condition was detected.",
            remediation="Apply optional hardening improvement.",
            location=FindingLocation(path="Dockerfile", line=5),
        )
    ]
    policy_evaluation = evaluate_findings_policy(findings)
    internal_report = create_analysis_report(
        "AI Container Intelligence Report",
        policy_evaluation.findings,
        policy_summary=policy_evaluation.summary,
    )

    markdown = render_markdown_report(internal_report)
    assert "- Outcome: WARN" in markdown.content
    assert "Blocking findings: 0" in markdown.content
    assert "Advisory findings: 1" in markdown.content


def test_render_markdown_report_renders_policy_outcome_fail() -> None:
    """Render FAIL policy outcome when policy summary indicates blocking findings."""
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
    assert "- Outcome: FAIL" in markdown.content
    assert "CI recommendation: FAIL" in markdown.content
    assert "Blocking rule IDs: DF004" in markdown.content
    assert "- policy profile: strict" not in markdown.content


def test_render_markdown_report_groups_blocking_and_advisory_findings() -> None:
    """Render findings under distinct blocking and advisory sections."""
    findings = [
        Finding(
            rule_id="DF004",
            title="Container configured to run as root",
            severity=Severity.HIGH,
            source="dockerfile-review",
            detail="Running as root increases attack surface.",
            remediation="Use a non-root runtime user.",
            location=FindingLocation(path="Dockerfile", line=3),
            disposition=FindingDisposition.BLOCKING,
        ),
        Finding(
            rule_id="DF005",
            title="ADD instruction used",
            severity=Severity.MEDIUM,
            source="dockerfile-review",
            detail="ADD introduces implicit copy behavior.",
            remediation="Use COPY unless ADD-specific behavior is required.",
            location=FindingLocation(path="Dockerfile", line=6),
            disposition=FindingDisposition.ADVISORY,
        ),
    ]
    internal_report = create_analysis_report("AI Container Intelligence Report", findings)

    markdown = render_markdown_report(internal_report)

    assert "## Blocking Findings" in markdown.content
    assert "DF004 - Container configured to run as root" in markdown.content
    assert "- Decision trace:" in markdown.content
    assert "- rule ID: DF004" in markdown.content
    assert "- severity: HIGH" in markdown.content
    assert "- blocking status: blocking" in markdown.content
    assert "- why this failed:" in markdown.content
    assert "- how to fix it:" in markdown.content
    assert "## Advisory Findings" in markdown.content
    assert "DF005 - ADD instruction used" in markdown.content
    assert "Why this is risky:" in markdown.content
    assert "How to fix it:" in markdown.content


def test_render_markdown_report_keeps_advisory_finding_compact() -> None:
    """Ensure advisory findings do not include verbose decision traces."""
    findings = [
        Finding(
            rule_id="DF005",
            title="ADD instruction used",
            severity=Severity.MEDIUM,
            source="dockerfile-review",
            detail="ADD introduces implicit copy behavior.",
            remediation="Use COPY unless ADD-specific behavior is required.",
            location=FindingLocation(path="Dockerfile", line=6),
            disposition=FindingDisposition.ADVISORY,
        ),
    ]
    internal_report = create_analysis_report("AI Container Intelligence Report", findings)

    markdown = render_markdown_report(internal_report)

    assert "## Advisory Findings" in markdown.content
    assert "DF005 - ADD instruction used" in markdown.content
    assert "Decision trace" not in markdown.content


def test_render_markdown_report_renders_structured_evidence_when_present() -> None:
    """Render structured evidence under finding details when available."""
    findings = [
        Finding(
            rule_id="VULN-CVE-2026-0001",
            title="Critical package vulnerability",
            severity=Severity.CRITICAL,
            source="trivy",
            detail="Package is affected by a known critical vulnerability.",
            remediation="Upgrade package to fixed version.",
            location=FindingLocation(path="image:example"),
            evidence={
                "package": "openssl",
                "fixed_version": "3.0.0",
                "cvss": 9.8,
                "exploit_available": True,
            },
            disposition=FindingDisposition.BLOCKING,
        )
    ]
    internal_report = create_analysis_report("AI Container Intelligence Report", findings)

    markdown = render_markdown_report(internal_report)

    assert "- Evidence:" in markdown.content
    assert "- package: openssl" in markdown.content
    assert "- fixed_version: 3.0.0" in markdown.content
    assert "- cvss: 9.8" in markdown.content
    assert "- exploit_available: True" in markdown.content
    assert "- core evidence: cvss=9.8, exploit_available=True, fixed_version=3.0.0, package=openssl" in markdown.content


def test_render_markdown_report_policy_outcome_stays_easy_to_scan() -> None:
    """Ensure policy outcome section remains compact and easy to scan."""
    findings = [
        Finding(
            rule_id="DF004",
            title="Container configured to run as root",
            severity=Severity.HIGH,
            source="dockerfile-review",
            detail="Running as root increases attack surface.",
            remediation="Use a non-root runtime user.",
            location=FindingLocation(path="Dockerfile", line=3),
        )
    ]
    policy_evaluation = evaluate_findings_policy(findings)
    internal_report = create_analysis_report(
        "AI Container Intelligence Report",
        policy_evaluation.findings,
        policy_summary=policy_evaluation.summary,
    )

    markdown = render_markdown_report(internal_report)

    assert "## Policy Outcome Summary" in markdown.content
    assert "- Outcome: FAIL" in markdown.content
    assert "## Policy Impact" in markdown.content
    assert "- CI recommendation: FAIL" in markdown.content


def test_render_markdown_report_shows_explicit_policy_profile_in_decision_trace() -> None:
    """Render policy profile line only when it is explicitly carried in policy summary."""
    findings = [
        Finding(
            rule_id="DF004",
            title="Container configured to run as root",
            severity=Severity.HIGH,
            source="dockerfile-review",
            detail="Running as root increases attack surface.",
            remediation="Use a non-root runtime user.",
            location=FindingLocation(path="Dockerfile", line=3),
        )
    ]
    policy_evaluation = evaluate_findings_policy(findings, profile_label="strict")
    internal_report = create_analysis_report(
        "AI Container Intelligence Report",
        policy_evaluation.findings,
        policy_summary=policy_evaluation.summary,
    )

    markdown = render_markdown_report(internal_report)

    assert "- policy profile: strict" in markdown.content


def test_render_markdown_report_preserves_evidence_after_policy_evaluation() -> None:
    """Ensure policy evaluation does not drop structured evidence before rendering."""
    findings = [
        Finding(
            rule_id="VULN-CVE-2026-9999",
            title="Critical library vulnerability",
            severity=Severity.CRITICAL,
            source="trivy",
            detail="Known critical CVE detected in runtime dependency.",
            remediation="Upgrade to a fixed version and rebuild image.",
            location=FindingLocation(path="image:example"),
            evidence={
                "package": "libssl",
                "cvss": 9.9,
                "fixed_version": "3.0.1",
            },
        )
    ]
    policy_evaluation = evaluate_findings_policy(findings)
    internal_report = create_analysis_report(
        "AI Container Intelligence Report",
        policy_evaluation.findings,
        policy_summary=policy_evaluation.summary,
    )

    markdown = render_markdown_report(internal_report)

    assert "## Blocking Findings" in markdown.content
    assert "VULN-CVE-2026-9999 - Critical library vulnerability" in markdown.content
    assert "- Evidence:" in markdown.content
    assert "- package: libssl" in markdown.content
    assert "- cvss: 9.9" in markdown.content
    assert "- fixed_version: 3.0.1" in markdown.content
    assert "- core evidence: cvss=9.9, fixed_version=3.0.1, package=libssl" in markdown.content
