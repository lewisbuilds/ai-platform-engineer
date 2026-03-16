"""Unit tests for Syft SBOM provider adapter."""

from __future__ import annotations

import json
import subprocess
from typing import Any

from pytest import MonkeyPatch

from ai_container_intelligence.integrations.sbom_provider import SyftSbomProvider


def test_syft_provider_handles_missing_executable(monkeypatch: MonkeyPatch) -> None:
    """Return deterministic finding when Syft is not installed."""
    monkeypatch.setattr("ai_container_intelligence.integrations.sbom_provider.shutil.which", lambda _: None)

    provider = SyftSbomProvider()
    result = provider.generate("example:image")

    assert result.provider_name == "syft"
    assert result.success is False
    assert result.output_path is None
    assert [item.rule_id for item in result.findings] == ["SBOM001"]


def test_syft_provider_normalizes_successful_json(monkeypatch: MonkeyPatch) -> None:
    """Normalize component count and metadata from Syft JSON output."""
    payload = {
        "serialNumber": "urn:uuid:test-serial",
        "metadata": {"component": {"name": "example"}},
        "tools": {"components": [{"name": "syft"}]},
        "components": [{"name": "openssl"}, {"name": "libc"}],
    }

    def _fake_run(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr("ai_container_intelligence.integrations.sbom_provider.shutil.which", lambda _: "syft")
    monkeypatch.setattr("ai_container_intelligence.integrations.sbom_provider.subprocess.run", _fake_run)

    provider = SyftSbomProvider()
    result = provider.generate("example:image")

    assert result.success is True
    assert result.output_path == "example:image.syft.cdx.json"
    assert {item.rule_id for item in result.findings} == {"SBOM005", "SBOM006"}


def test_syft_provider_handles_invalid_json(monkeypatch: MonkeyPatch) -> None:
    """Return deterministic parse failure finding for invalid JSON output."""

    def _fake_run(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="not-json", stderr="")

    monkeypatch.setattr("ai_container_intelligence.integrations.sbom_provider.shutil.which", lambda _: "syft")
    monkeypatch.setattr("ai_container_intelligence.integrations.sbom_provider.subprocess.run", _fake_run)

    provider = SyftSbomProvider()
    result = provider.generate("example:image")

    assert result.success is False
    assert [item.rule_id for item in result.findings] == ["SBOM003"]
