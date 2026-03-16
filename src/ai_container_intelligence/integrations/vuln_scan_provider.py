"""Vulnerability scan provider abstraction."""

from dataclasses import dataclass
from typing import Protocol

from ai_container_intelligence.models.findings import Finding


@dataclass(frozen=True)
class VulnerabilityScanResult:
    """Vulnerability scan result metadata.

    Args:
        provider_name: Integration provider name.
        success: Whether scan succeeded.
        findings: Normalized findings from scan.
    """

    provider_name: str
    success: bool
    findings: list[Finding]


class VulnerabilityScanProvider(Protocol):
    """Protocol for vulnerability scan integrations."""

    def scan(self, image_ref: str) -> VulnerabilityScanResult:
        """Run vulnerability scan for an image reference.

        Args:
            image_ref: Image reference or artifact identifier.

        Returns:
            Vulnerability scan metadata.
        """


class NoopVulnerabilityScanProvider:
    """Fallback provider used by the scaffold."""

    def scan(self, image_ref: str) -> VulnerabilityScanResult:
        """Return a deterministic stub result.

        Args:
            image_ref: Image reference or artifact identifier.

        Returns:
            Stub scan result.
        """
        _ = image_ref
        return VulnerabilityScanResult(
            provider_name="noop-vuln",
            success=False,
            findings=[],
        )
