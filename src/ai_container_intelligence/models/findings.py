"""Finding model types."""

from dataclasses import dataclass
from enum import Enum
from typing import Final


class Severity(str, Enum):
    """Severity levels used by all findings."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingDisposition(str, Enum):
    """Policy disposition for a finding."""

    ADVISORY = "advisory"
    BLOCKING = "blocking"


SEVERITY_RANK: Final[dict[Severity, int]] = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}


@dataclass(frozen=True)
class FindingLocation:
    """Location metadata for a finding.

    Args:
        path: Artifact path.
        line: Optional 1-based line number.
    """

    path: str
    line: int | None = None


@dataclass(frozen=True)
class Finding:
    """Represents a single issue identified by any analyzer.

    Args:
        rule_id: Stable identifier for the triggered rule.
        title: Human-readable finding title.
        severity: Normalized severity.
        source: Logical source module or integration name.
        detail: Primary finding detail message.
        remediation: Actionable recommendation.
        location: Optional location metadata.
        disposition: Policy decision for CI behavior.
    """

    rule_id: str
    title: str
    severity: Severity
    source: str
    detail: str
    remediation: str
    location: FindingLocation | None = None
    disposition: FindingDisposition = FindingDisposition.ADVISORY


def finding_sort_key(finding: Finding) -> tuple[int, str, str, int]:
    """Create deterministic sort key for findings.

    Args:
        finding: Finding to sort.

    Returns:
        Tuple used for stable ordering.
    """
    line = finding.location.line if finding.location and finding.location.line else 0
    return (
        SEVERITY_RANK[finding.severity],
        finding.rule_id,
        finding.source,
        line,
    )
