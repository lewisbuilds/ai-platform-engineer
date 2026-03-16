"""Unit tests for integration provider interfaces."""

from ai_container_intelligence.integrations.layer_analysis_provider import (
    NoopLayerAnalysisProvider,
)
from ai_container_intelligence.integrations.sbom_provider import NoopSbomProvider
from ai_container_intelligence.integrations.vuln_scan_provider import (
    NoopVulnerabilityScanProvider,
)


def test_noop_layer_provider_is_deterministic() -> None:
    """Ensure layer noop provider returns stable empty findings."""
    provider = NoopLayerAnalysisProvider()
    result = provider.analyze("tests/fixtures/sample-image.tar")
    assert result == []


def test_noop_sbom_provider_is_deterministic() -> None:
    """Ensure SBOM noop provider returns stable empty findings."""
    provider = NoopSbomProvider()
    result = provider.generate("example:image")
    assert result == []


def test_noop_vulnerability_provider_is_deterministic() -> None:
    """Ensure vulnerability noop provider returns stable empty findings."""
    provider = NoopVulnerabilityScanProvider()
    result = provider.scan("example:image")
    assert result == []
