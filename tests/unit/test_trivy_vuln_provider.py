"""Unit tests for Trivy vulnerability scan provider adapter."""

from __future__ import annotations

import json
import subprocess
from typing import Any

from pytest import MonkeyPatch

from ai_container_intelligence.integrations.vuln_scan_provider import (
    TrivyVulnerabilityScanProvider,
)
from ai_container_intelligence.models.findings import Severity


def test_trivy_provider_handles_missing_executable(monkeypatch: MonkeyPatch) -> None:
    """Return deterministic finding when Trivy is not installed."""
    monkeypatch.setattr("ai_container_intelligence.integrations.vuln_scan_provider.shutil.which", lambda _: None)

    provider = TrivyVulnerabilityScanProvider()
    result = provider.scan("example:image")

    assert result.provider_name == "trivy"
    assert result.success is False
    assert [item.rule_id for item in result.findings] == ["VULN001"]


def test_trivy_provider_normalizes_vulnerabilities(monkeypatch: MonkeyPatch) -> None:
    """Map Trivy vulnerabilities to normalized internal findings."""
    payload = {
        "Results": [
            {
                "Target": "example:image",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2026-0001",
                        "Title": "openssl issue",
                        "PkgName": "openssl",
                        "Severity": "CRITICAL",
                        "Description": "Critical vulnerability in openssl.",
                        "FixedVersion": "3.0.0",
                    },
                    {
                        "VulnerabilityID": "CVE-2026-0002",
                        "Title": "curl issue",
                        "PkgName": "curl",
                        "Severity": "LOW",
                        "Description": "Low severity issue.",
                    },
                ],
            }
        ]
    }

    def _fake_run(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr("ai_container_intelligence.integrations.vuln_scan_provider.shutil.which", lambda _: "trivy")
    monkeypatch.setattr("ai_container_intelligence.integrations.vuln_scan_provider.subprocess.run", _fake_run)

    provider = TrivyVulnerabilityScanProvider()
    result = provider.scan("example:image")

    assert result.success is True
    assert len(result.findings) == 2
    by_id = {item.rule_id: item for item in result.findings}
    assert by_id["VULN-CVE-2026-0001"].severity is Severity.CRITICAL
    assert by_id["VULN-CVE-2026-0001"].remediation == "Upgrade to fixed version 3.0.0."
    assert by_id["VULN-CVE-2026-0002"].severity is Severity.LOW


def test_trivy_provider_returns_no_vuln_summary(monkeypatch: MonkeyPatch) -> None:
    """Return stable informational finding when no vulnerabilities are present."""
    payload = {"Results": [{"Target": "example:image", "Vulnerabilities": []}]}

    def _fake_run(*_args: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr("ai_container_intelligence.integrations.vuln_scan_provider.shutil.which", lambda _: "trivy")
    monkeypatch.setattr("ai_container_intelligence.integrations.vuln_scan_provider.subprocess.run", _fake_run)

    provider = TrivyVulnerabilityScanProvider()
    result = provider.scan("example:image")

    assert result.success is True
    assert [item.rule_id for item in result.findings] == ["VULN005"]
