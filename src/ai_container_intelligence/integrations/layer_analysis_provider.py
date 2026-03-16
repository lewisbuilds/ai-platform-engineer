"""Layer analysis provider abstraction."""

from dataclasses import dataclass
from typing import Protocol

from ai_container_intelligence.models.findings import Finding


@dataclass(frozen=True)
class LayerAnalysisResult:
    """Layer analysis result container.

    Args:
        provider_name: Integration provider name.
        findings: Normalized findings from provider analysis.
    """

    provider_name: str
    findings: list[Finding]


class LayerAnalysisProvider(Protocol):
    """Protocol for layer metadata analyzers."""

    def analyze(self, image_tar_path: str) -> LayerAnalysisResult:
        """Analyze layer metadata for an image tarball.

        Args:
            image_tar_path: Path to image tarball.

        Returns:
            Layer analysis result.
        """


class NoopLayerAnalysisProvider:
    """Fallback layer analyzer used by the scaffold."""

    def analyze(self, image_tar_path: str) -> LayerAnalysisResult:
        """Return deterministic empty layer analysis.

        Args:
            image_tar_path: Path to image tarball.

        Returns:
            Empty layer analysis result.
        """
        _ = image_tar_path
        return LayerAnalysisResult(provider_name="noop-layer", findings=[])
