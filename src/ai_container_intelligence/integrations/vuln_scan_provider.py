"""Vulnerability scan provider abstraction."""

import json
import shutil
import subprocess
from typing import Protocol

from ai_container_intelligence.models.findings import Finding, FindingLocation, Severity


class VulnerabilityScanProvider(Protocol):
    """Protocol for vulnerability scan integrations."""

    def scan(self, image_ref: str) -> list[Finding]:
        """Run vulnerability scan for an image reference.

        Args:
            image_ref: Image reference or artifact identifier.

        Returns:
            Vulnerability scan metadata.
        """
        raise NotImplementedError


class NoopVulnerabilityScanProvider:
    """Fallback provider used by the scaffold."""

    def scan(self, image_ref: str) -> list[Finding]:
        """Return a deterministic stub result.

        Args:
            image_ref: Image reference or artifact identifier.

        Returns:
            Stub scan result.
        """
        _ = image_ref
        return []


class TrivyVulnerabilityScanProvider:
    """Trivy-based vulnerability scan adapter for local execution."""

    _PROVIDER_NAME = "trivy"
    _SEVERITY_MAP = {
        "UNKNOWN": Severity.LOW,
        "LOW": Severity.LOW,
        "MEDIUM": Severity.MEDIUM,
        "HIGH": Severity.HIGH,
        "CRITICAL": Severity.CRITICAL,
    }

    def __init__(self, executable: str = "trivy") -> None:
        self._executable = executable

    def scan(self, image_ref: str) -> list[Finding]:
        """Run Trivy JSON scan and normalize findings.

        Args:
            image_ref: Image reference or artifact identifier.

        Returns:
            Normalized vulnerability scan result.
        """
        if shutil.which(self._executable) is None:
            return [
                Finding(
                    rule_id="VULN001",
                    title="Trivy not available",
                    severity=Severity.MEDIUM,
                    source=self._PROVIDER_NAME,
                    detail="Trivy executable is not installed or not on PATH.",
                    remediation="Install Trivy and ensure it is available on PATH.",
                )
            ]

        command = [self._executable, "image", "--format", "json", image_ref]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip() or "Trivy failed without stderr output."
            return [
                Finding(
                    rule_id="VULN002",
                    title="Trivy execution failed",
                    severity=Severity.MEDIUM,
                    source=self._PROVIDER_NAME,
                    detail=stderr,
                    remediation="Verify image reference and local Trivy configuration.",
                    location=FindingLocation(path=image_ref),
                )
            ]

        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            return [
                Finding(
                    rule_id="VULN003",
                    title="Invalid Trivy JSON output",
                    severity=Severity.MEDIUM,
                    source=self._PROVIDER_NAME,
                    detail=f"Unable to parse Trivy output: {exc}",
                    remediation="Ensure Trivy is executed with --format json.",
                    location=FindingLocation(path=image_ref),
                )
            ]

        return self._normalize_findings(payload=payload, image_ref=image_ref)

    def _normalize_findings(self, payload: object, image_ref: str) -> list[Finding]:
        if not isinstance(payload, dict):
            return [
                Finding(
                    rule_id="VULN004",
                    title="Unexpected Trivy payload",
                    severity=Severity.MEDIUM,
                    source=self._PROVIDER_NAME,
                    detail="Trivy output root is not a JSON object.",
                    remediation="Verify scan output format and Trivy version compatibility.",
                    location=FindingLocation(path=image_ref),
                )
            ]

        results = payload.get("Results", []) if isinstance(payload.get("Results", []), list) else []
        findings: list[Finding] = []

        for result in results:
            if not isinstance(result, dict):
                continue
            target_value = result.get("Target")
            target = target_value if isinstance(target_value, str) and target_value else image_ref
            vulnerabilities = (
                result.get("Vulnerabilities", [])
                if isinstance(result.get("Vulnerabilities", []), list)
                else []
            )

            for vulnerability in vulnerabilities:
                if not isinstance(vulnerability, dict):
                    continue
                vuln_id = vulnerability.get("VulnerabilityID")
                title = vulnerability.get("Title")
                pkg_name = vulnerability.get("PkgName")
                severity = vulnerability.get("Severity")
                description = vulnerability.get("Description")
                fixed_version = vulnerability.get("FixedVersion")

                normalized_severity = self._SEVERITY_MAP.get(str(severity).upper(), Severity.MEDIUM)
                rule_id = f"VULN-{vuln_id}" if isinstance(vuln_id, str) and vuln_id else "VULN-UNKNOWN"
                finding_title = (
                    title
                    if isinstance(title, str) and title
                    else f"Vulnerability {vuln_id}" if isinstance(vuln_id, str) and vuln_id else "Vulnerability detected"
                )
                package_segment = f"Package: {pkg_name}. " if isinstance(pkg_name, str) and pkg_name else ""
                detail = (
                    f"{package_segment}{description}" if isinstance(description, str) and description else f"Vulnerability found in {target}."
                )
                remediation = (
                    f"Upgrade to fixed version {fixed_version}."
                    if isinstance(fixed_version, str) and fixed_version
                    else "Review dependency and update to a non-vulnerable version."
                )

                findings.append(
                    Finding(
                        rule_id=rule_id,
                        title=finding_title,
                        severity=normalized_severity,
                        source=self._PROVIDER_NAME,
                        detail=detail,
                        remediation=remediation,
                        location=FindingLocation(path=target),
                    )
                )

        if not findings:
            return [
                Finding(
                    rule_id="VULN005",
                    title="No vulnerabilities reported",
                    severity=Severity.LOW,
                    source=self._PROVIDER_NAME,
                    detail="Trivy scan completed with no reported vulnerabilities.",
                    remediation="Continue regular scanning as part of pull request validation.",
                    location=FindingLocation(path=image_ref),
                )
            ]

        return findings
