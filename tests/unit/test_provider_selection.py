"""Unit tests for centralized provider selection."""

from ai_container_intelligence.integrations.layer_analysis_provider import (
    NoopLayerAnalysisProvider,
    TarLayerAnalysisProvider,
)
from ai_container_intelligence.integrations.provider_selection import select_providers
from ai_container_intelligence.integrations.sbom_provider import NoopSbomProvider, SyftSbomProvider
from ai_container_intelligence.integrations.vuln_scan_provider import (
    NoopVulnerabilityScanProvider,
    TrivyVulnerabilityScanProvider,
)


def test_select_providers_real_profile_uses_real_adapters() -> None:
    """Select real providers for local adapter execution profile."""
    selected = select_providers(profile="real")
    assert isinstance(selected.layer_provider, TarLayerAnalysisProvider)
    assert isinstance(selected.sbom_provider, SyftSbomProvider)
    assert isinstance(selected.vulnerability_provider, TrivyVulnerabilityScanProvider)


def test_select_providers_noop_profile_uses_noop_adapters() -> None:
    """Select noop providers for deterministic profile."""
    selected = select_providers(profile="noop")
    assert isinstance(selected.layer_provider, NoopLayerAnalysisProvider)
    assert isinstance(selected.sbom_provider, NoopSbomProvider)
    assert isinstance(selected.vulnerability_provider, NoopVulnerabilityScanProvider)


def test_select_providers_explicit_override_takes_precedence() -> None:
    """Honor explicit provider injection regardless of profile defaults."""
    custom_layer = NoopLayerAnalysisProvider()
    selected = select_providers(profile="real", layer_provider=custom_layer)
    assert selected.layer_provider is custom_layer
