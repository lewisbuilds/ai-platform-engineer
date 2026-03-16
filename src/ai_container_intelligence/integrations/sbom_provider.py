"""SBOM provider abstraction."""

import json
import shutil
import subprocess  # nosec B404 - Required for invoking trusted local Syft CLI.
from typing import Protocol

from ai_container_intelligence.models.findings import Finding, FindingLocation, Severity


class SbomProvider(Protocol):
    """Protocol for SBOM generation integrations."""

    def generate(self, image_ref: str) -> list[Finding]:
        """Generate SBOM for an image reference.

        Args:
            image_ref: Image reference or artifact identifier.

        Returns:
            SBOM generation result metadata.
        """
        raise NotImplementedError


class NoopSbomProvider:
    """Fallback provider used by the scaffold."""

    def generate(self, image_ref: str) -> list[Finding]:
        """Return a deterministic stub result.

        Args:
            image_ref: Image reference or artifact identifier.

        Returns:
            Stub SBOM result.
        """
        _ = image_ref
        return []


class SyftSbomProvider:
    """Syft-based SBOM provider adapter for local execution."""

    _PROVIDER_NAME = "syft"

    def __init__(self, executable: str = "syft", timeout_seconds: int = 120) -> None:
        self._executable = executable
        self._timeout_seconds = timeout_seconds

    def generate(self, image_ref: str) -> list[Finding]:
        """Generate CycloneDX JSON SBOM findings using Syft.

        Args:
            image_ref: Image reference or artifact identifier.

        Returns:
            Normalized SBOM provider result.
        """
        if shutil.which(self._executable) is None:
            return [
                Finding(
                    rule_id="SBOM001",
                    title="Syft not available",
                    severity=Severity.MEDIUM,
                    source=self._PROVIDER_NAME,
                    detail="Syft executable is not installed or not on PATH.",
                    remediation="Install Syft and ensure it is available on PATH.",
                )
            ]

        command = [self._executable, image_ref, "-o", "cyclonedx-json"]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=self._timeout_seconds,
            )  # nosec B603 - shell=False and argument list prevent shell injection.
        except subprocess.TimeoutExpired:
            return [
                Finding(
                    rule_id="SBOM008",
                    title="Syft execution timed out",
                    severity=Severity.MEDIUM,
                    source=self._PROVIDER_NAME,
                    detail=f"Syft did not complete within {self._timeout_seconds} seconds.",
                    remediation="Increase timeout for large images or verify Syft runtime/network health.",
                    location=FindingLocation(path=image_ref),
                )
            ]
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or "Syft failed without stderr output."
            return [
                Finding(
                    rule_id="SBOM002",
                    title="Syft execution failed",
                    severity=Severity.MEDIUM,
                    source=self._PROVIDER_NAME,
                    detail=stderr,
                    remediation="Verify the image reference and Syft runtime configuration.",
                    location=FindingLocation(path=image_ref),
                )
            ]

        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            return [
                Finding(
                    rule_id="SBOM003",
                    title="Invalid Syft JSON output",
                    severity=Severity.MEDIUM,
                    source=self._PROVIDER_NAME,
                    detail=f"Unable to parse Syft output: {exc}",
                    remediation="Ensure Syft returns valid cyclonedx-json output.",
                    location=FindingLocation(path=image_ref),
                )
            ]

        return self._normalize_findings(payload=payload, image_ref=image_ref)

    def _normalize_findings(self, payload: object, image_ref: str) -> list[Finding]:
        if not isinstance(payload, dict):
            return [
                Finding(
                    rule_id="SBOM004",
                    title="Unexpected Syft payload",
                    severity=Severity.MEDIUM,
                    source=self._PROVIDER_NAME,
                    detail="Syft output root is not a JSON object.",
                    remediation="Verify Syft output format selection.",
                    location=FindingLocation(path=image_ref),
                )
            ]

        metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata", {}), dict) else {}
        tools = payload.get("tools", {}) if isinstance(payload.get("tools", {}), dict) else {}
        components = payload.get("components", []) if isinstance(payload.get("components", []), list) else []

        tool_names: list[str] = []
        components_tools = tools.get("components", []) if isinstance(tools.get("components", []), list) else []
        for item in components_tools:
            if isinstance(item, dict):
                name = item.get("name")
                if isinstance(name, str) and name:
                    tool_names.append(name)

        serial_number = payload.get("serialNumber")
        findings: list[Finding] = [
            Finding(
                rule_id="SBOM005",
                title="SBOM generated",
                severity=Severity.LOW,
                source=self._PROVIDER_NAME,
                detail=(
                    f"Generated SBOM with {len(components)} component(s)"
                    + (f" and serial {serial_number}." if isinstance(serial_number, str) else ".")
                ),
                remediation="Use this SBOM as input for compliance and vulnerability workflows.",
                location=FindingLocation(path=image_ref),
            )
        ]

        if tool_names:
            findings.append(
                Finding(
                    rule_id="SBOM006",
                    title="SBOM tool metadata",
                    severity=Severity.LOW,
                    source=self._PROVIDER_NAME,
                    detail=f"Toolchain reported by SBOM: {', '.join(sorted(tool_names))}.",
                    remediation="Record tool metadata for reproducibility audits.",
                    location=FindingLocation(path=image_ref),
                )
            )

        if metadata and not components:
            findings.append(
                Finding(
                    rule_id="SBOM007",
                    title="SBOM has no components",
                    severity=Severity.MEDIUM,
                    source=self._PROVIDER_NAME,
                    detail="SBOM metadata exists but component list is empty.",
                    remediation="Verify scan target and package extraction configuration.",
                    location=FindingLocation(path=image_ref),
                )
            )

        return findings
