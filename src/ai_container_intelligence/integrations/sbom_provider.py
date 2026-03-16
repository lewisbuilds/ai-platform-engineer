"""SBOM provider abstraction."""

from dataclasses import dataclass
from typing import Protocol

from ai_container_intelligence.models.findings import Finding


@dataclass(frozen=True)
class SbomResult:
    """SBOM generation result metadata.

    Args:
        provider_name: Integration provider name.
        success: Whether SBOM generation succeeded.
        output_path: Optional generated SBOM path.
        findings: Normalized findings from SBOM validation.
    """

    provider_name: str
    success: bool
    output_path: str | None
    findings: list[Finding]


class SbomProvider(Protocol):
    """Protocol for SBOM generation integrations."""

    def generate(self, image_ref: str) -> SbomResult:
        """Generate SBOM for an image reference.

        Args:
            image_ref: Image reference or artifact identifier.

        Returns:
            SBOM generation result metadata.
        """


class NoopSbomProvider:
    """Fallback provider used by the scaffold."""

    def generate(self, image_ref: str) -> SbomResult:
        """Return a deterministic stub result.

        Args:
            image_ref: Image reference or artifact identifier.

        Returns:
            Stub SBOM result.
        """
        _ = image_ref
        return SbomResult(
            provider_name="noop-sbom",
            success=False,
            output_path=None,
            findings=[],
        )
