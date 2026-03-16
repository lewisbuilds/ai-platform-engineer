"""SBOM provider abstraction."""

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import subprocess
from typing import Protocol

from ai_container_intelligence.models.findings import Finding, FindingLocation, Severity


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
        raise NotImplementedError


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


class SyftSbomProvider:
    """Syft-based SBOM provider adapter for local execution."""

    _PROVIDER_NAME = "syft"

    def __init__(self, executable: str = "syft") -> None:
        self._executable = executable

    def generate(self, image_ref: str) -> SbomResult:
        """Generate CycloneDX JSON SBOM findings using Syft.

        Args:
            image_ref: Image reference or artifact identifier.

        Returns:
            Normalized SBOM provider result.
        """
        if shutil.which(self._executable) is None:
            return SbomResult(
                provider_name=self._PROVIDER_NAME,
                success=False,
                output_path=None,
                findings=[
                    Finding(
                        rule_id="SBOM001",
                        title="Syft not available",
                        severity=Severity.MEDIUM,
                        source=self._PROVIDER_NAME,
                        detail="Syft executable is not installed or not on PATH.",
                        remediation="Install Syft and ensure it is available on PATH.",
                    )
                ],
            )

        command = [self._executable, image_ref, "-o", "cyclonedx-json"]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or "Syft failed without stderr output."
            return SbomResult(
                provider_name=self._PROVIDER_NAME,
                success=False,
                output_path=None,
                findings=[
                    Finding(
                        rule_id="SBOM002",
                        title="Syft execution failed",
                        severity=Severity.MEDIUM,
                        source=self._PROVIDER_NAME,
                        detail=stderr,
                        remediation="Verify the image reference and Syft runtime configuration.",
                        location=FindingLocation(path=image_ref),
                    )
                ],
            )

        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            return SbomResult(
                provider_name=self._PROVIDER_NAME,
                success=False,
                output_path=None,
                findings=[
                    Finding(
                        rule_id="SBOM003",
                        title="Invalid Syft JSON output",
                        severity=Severity.MEDIUM,
                        source=self._PROVIDER_NAME,
                        detail=f"Unable to parse Syft output: {exc}",
                        remediation="Ensure Syft returns valid cyclonedx-json output.",
                        location=FindingLocation(path=image_ref),
                    )
                ],
            )

        findings = self._normalize_findings(payload=payload, image_ref=image_ref)
        return SbomResult(
            provider_name=self._PROVIDER_NAME,
            success=True,
            output_path=str(Path(f"{image_ref}.syft.cdx.json")),
            findings=findings,
        )

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
