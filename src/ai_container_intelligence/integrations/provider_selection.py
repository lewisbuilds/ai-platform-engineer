"""Minimal provider selection for local pipeline execution."""

from dataclasses import dataclass
from typing import Literal

from ai_container_intelligence.integrations.layer_analysis_provider import (
    LayerAnalysisProvider,
    NoopLayerAnalysisProvider,
    TarLayerAnalysisProvider,
)
from ai_container_intelligence.integrations.sbom_provider import (
    NoopSbomProvider,
    SbomProvider,
    SyftSbomProvider,
)
from ai_container_intelligence.integrations.vuln_scan_provider import (
    NoopVulnerabilityScanProvider,
    TrivyVulnerabilityScanProvider,
    VulnerabilityScanProvider,
)


ProviderProfile = Literal["real", "noop"]


@dataclass(frozen=True)
class ProviderSelection:
    """Selected provider set used by pipeline orchestration."""

    layer_provider: LayerAnalysisProvider
    sbom_provider: SbomProvider
    vulnerability_provider: VulnerabilityScanProvider


def select_providers(
    profile: ProviderProfile = "real",
    layer_provider: LayerAnalysisProvider | None = None,
    sbom_provider: SbomProvider | None = None,
    vulnerability_provider: VulnerabilityScanProvider | None = None,
) -> ProviderSelection:
    """Select providers in one centralized location.

    Args:
        profile: Selection profile. "real" uses local adapters and "noop" uses
            deterministic stub providers.
        layer_provider: Optional explicit override for layer provider.
        sbom_provider: Optional explicit override for SBOM provider.
        vulnerability_provider: Optional explicit override for vulnerability provider.

    Returns:
        Concrete provider selection bundle.

    Raises:
        ValueError: If profile is not recognized.
    """
    if profile == "real":
        default_layer: LayerAnalysisProvider = TarLayerAnalysisProvider()
        default_sbom: SbomProvider = SyftSbomProvider()
        default_vulnerability: VulnerabilityScanProvider = TrivyVulnerabilityScanProvider()
    elif profile == "noop":
        default_layer = NoopLayerAnalysisProvider()
        default_sbom = NoopSbomProvider()
        default_vulnerability = NoopVulnerabilityScanProvider()
    else:
        raise ValueError(f"Unsupported provider profile: {profile}")

    return ProviderSelection(
        layer_provider=layer_provider or default_layer,
        sbom_provider=sbom_provider or default_sbom,
        vulnerability_provider=vulnerability_provider or default_vulnerability,
    )
