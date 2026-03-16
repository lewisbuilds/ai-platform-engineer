"""Minimal policy evaluator for finding severity and CI impact."""

from dataclasses import dataclass
from typing import Literal

from ai_container_intelligence.models.findings import (
    Finding,
    FindingDisposition,
    Severity,
)
from ai_container_intelligence.models.report import PolicyImpactSummary


@dataclass(frozen=True)
class PolicyConfig:
    """In-process policy configuration.

    Args:
        severity_overrides: Rule-based severity overrides.
        blocking_rule_ids: Rule IDs that always block CI.
        blocking_severities: Severities that block CI.
    """

    severity_overrides: dict[str, Severity]
    blocking_rule_ids: set[str]
    blocking_severities: set[Severity]


@dataclass(frozen=True)
class PolicyEvaluation:
    """Policy evaluation result for a finding collection."""

    findings: list[Finding]
    summary: PolicyImpactSummary


PolicyProfile = Literal["strict", "relaxed"]
POLICY_PROFILES: tuple[PolicyProfile, ...] = ("strict", "relaxed")


STRICT_POLICY = PolicyConfig(
    severity_overrides={},
    blocking_rule_ids={"DF004"},
    blocking_severities={Severity.CRITICAL},
)

RELAXED_POLICY = PolicyConfig(
    severity_overrides={},
    blocking_rule_ids=set(),
    blocking_severities={Severity.CRITICAL},
)

DEFAULT_POLICY = STRICT_POLICY


def resolve_policy_config(profile: str = "strict") -> PolicyConfig:
    """Resolve built-in policy profile to concrete policy configuration.

    Args:
        profile: Built-in policy profile.

    Returns:
        Policy configuration for evaluation.

    Raises:
        ValueError: If profile is not a supported built-in profile.
    """
    if profile not in POLICY_PROFILES:
        supported = ", ".join(POLICY_PROFILES)
        raise ValueError(f"Unsupported policy profile: {profile}. Supported profiles: {supported}")

    if profile == "relaxed":
        return RELAXED_POLICY
    return STRICT_POLICY


def _replace_finding(
    finding: Finding,
    severity: Severity,
    disposition: FindingDisposition,
) -> Finding:
    """Create a copy of finding with policy-evaluated fields."""
    return Finding(
        rule_id=finding.rule_id,
        title=finding.title,
        severity=severity,
        source=finding.source,
        detail=finding.detail,
        remediation=finding.remediation,
        evidence=finding.evidence,
        location=finding.location,
        disposition=disposition,
    )


def evaluate_findings_policy(
    findings: list[Finding],
    policy: PolicyConfig = DEFAULT_POLICY,
    profile_label: str | None = None,
) -> PolicyEvaluation:
    """Apply policy-backed severity and blocking decisions.

    Args:
        findings: Findings to evaluate.
        policy: Policy configuration.
        profile_label: Optional explicit policy profile label for report rendering.

    Returns:
        Evaluated findings and policy impact summary.
    """
    evaluated: list[Finding] = []
    advisory_count = 0
    blocking_count = 0
    blocking_rule_ids: set[str] = set()

    for finding in findings:
        resolved_severity = policy.severity_overrides.get(finding.rule_id, finding.severity)
        is_blocking = (
            finding.rule_id in policy.blocking_rule_ids
            or resolved_severity in policy.blocking_severities
        )
        disposition = (
            FindingDisposition.BLOCKING if is_blocking else FindingDisposition.ADVISORY
        )
        if is_blocking:
            blocking_count += 1
            blocking_rule_ids.add(finding.rule_id)
        else:
            advisory_count += 1

        evaluated.append(
            _replace_finding(
                finding=finding,
                severity=resolved_severity,
                disposition=disposition,
            )
        )

    blocking_threshold = ", ".join(
        sorted(item.value.upper() for item in policy.blocking_severities)
    )
    summary = PolicyImpactSummary(
        advisory=advisory_count,
        blocking=blocking_count,
        blocking_rule_ids=tuple(sorted(blocking_rule_ids)),
        blocking_threshold=blocking_threshold,
        should_fail=blocking_count > 0,
        policy_profile_label=profile_label,
    )
    return PolicyEvaluation(findings=evaluated, summary=summary)
