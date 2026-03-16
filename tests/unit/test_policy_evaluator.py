"""Unit tests for centralized finding policy evaluation."""

import pytest

from ai_container_intelligence.models.findings import (
    Finding,
    FindingDisposition,
    FindingLocation,
    Severity,
)
from ai_container_intelligence.policy.evaluator import (
    PolicyConfig,
    evaluate_findings_policy,
    resolve_policy_config,
)


def _finding(rule_id: str, severity: Severity) -> Finding:
    """Create a deterministic finding for policy tests."""
    return Finding(
        rule_id=rule_id,
        title=f"{rule_id} title",
        severity=severity,
        source="test",
        detail="detail",
        remediation="fix",
        location=FindingLocation(path="Dockerfile", line=1),
    )


def test_policy_evaluator_overrides_severity_by_rule_id() -> None:
    """Ensure policy can centrally re-assign finding severity by rule ID."""
    findings = [_finding("DF005", Severity.MEDIUM)]
    policy = PolicyConfig(
        severity_overrides={"DF005": Severity.INFO},
        blocking_rule_ids=set(),
        blocking_severities={Severity.HIGH, Severity.CRITICAL},
    )

    result = evaluate_findings_policy(findings=findings, policy=policy)

    assert result.findings[0].severity is Severity.INFO
    assert result.findings[0].disposition is FindingDisposition.ADVISORY
    assert result.summary.advisory == 1
    assert result.summary.blocking == 0
    assert result.summary.blocking_rule_ids == ()
    assert result.summary.should_fail is False


def test_policy_evaluator_marks_blocking_for_threshold_and_rule_override() -> None:
    """Ensure blocking can come from severity threshold or explicit blocking rule IDs."""
    findings = [
        _finding("DF002", Severity.HIGH),
        _finding("DF005", Severity.LOW),
    ]
    policy = PolicyConfig(
        severity_overrides={},
        blocking_rule_ids={"DF005"},
        blocking_severities={Severity.HIGH, Severity.CRITICAL},
    )

    result = evaluate_findings_policy(findings=findings, policy=policy)

    by_id = {item.rule_id: item for item in result.findings}
    assert by_id["DF002"].disposition is FindingDisposition.BLOCKING
    assert by_id["DF005"].disposition is FindingDisposition.BLOCKING
    assert result.summary.blocking == 2
    assert result.summary.advisory == 0
    assert result.summary.blocking_rule_ids == ("DF002", "DF005")
    assert result.summary.should_fail is True


def test_resolve_policy_config_strict_and_relaxed_thresholds() -> None:
    """Ensure built-in policy profiles map to expected blocking thresholds."""
    strict_policy = resolve_policy_config("strict")
    relaxed_policy = resolve_policy_config("relaxed")

    assert Severity.HIGH not in strict_policy.blocking_severities
    assert Severity.CRITICAL in strict_policy.blocking_severities
    assert Severity.HIGH not in relaxed_policy.blocking_severities
    assert Severity.CRITICAL in relaxed_policy.blocking_severities
    assert "DF004" in strict_policy.blocking_rule_ids
    assert not relaxed_policy.blocking_rule_ids


def test_policy_evaluator_strict_marks_root_runtime_rule_blocking() -> None:
    """Ensure strict policy blocks explicit root-runtime finding even without critical severity."""
    findings = [_finding("DF004", Severity.HIGH)]

    result = evaluate_findings_policy(findings=findings, policy=resolve_policy_config("strict"))

    assert result.findings[0].disposition is FindingDisposition.BLOCKING
    assert result.summary.should_fail is True


def test_policy_evaluator_strict_keeps_high_severity_advisory_when_not_rule_blocked() -> None:
    """Ensure strict profile keeps non-rule-blocked HIGH findings advisory."""
    findings = [_finding("DF002", Severity.HIGH)]

    result = evaluate_findings_policy(findings=findings, policy=resolve_policy_config("strict"))

    assert result.findings[0].disposition is FindingDisposition.ADVISORY
    assert result.summary.should_fail is False


def test_resolve_policy_config_rejects_unsupported_profile() -> None:
    """Ensure unsupported policy profiles fail fast with explicit error context."""
    with pytest.raises(ValueError, match="Unsupported policy profile"):
        resolve_policy_config("custom")
