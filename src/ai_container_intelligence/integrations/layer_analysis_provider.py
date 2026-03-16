"""Layer analysis provider abstraction."""

from contextlib import closing
import json
import tarfile
from typing import Protocol

from ai_container_intelligence.models.findings import Finding, FindingLocation, Severity

class LayerAnalysisProvider(Protocol):
    """Protocol for layer metadata analyzers."""

    def analyze(self, image_tar_path: str) -> list[Finding]:
        """Analyze layer metadata for an image tarball.

        Args:
            image_tar_path: Path to image tarball.

        Returns:
            Layer analysis result.
        """
        raise NotImplementedError


class NoopLayerAnalysisProvider:
    """Fallback layer analyzer used by the scaffold."""

    def analyze(self, image_tar_path: str) -> list[Finding]:
        """Return deterministic empty layer analysis.

        Args:
            image_tar_path: Path to image tarball.

        Returns:
            Empty layer analysis result.
        """
        _ = image_tar_path
        return []


class TarLayerAnalysisProvider:
    """Analyze Docker image tar archives using local metadata files.

    This provider inspects common Docker archive members (`manifest.json` and
    the referenced config JSON blob) and emits normalized findings.
    """

    _PROVIDER_NAME = "tar-layer"

    def analyze(self, image_tar_path: str) -> list[Finding]:
        """Analyze metadata in an image tarball.

        Args:
            image_tar_path: Path to image tarball.

        Returns:
            Layer analysis result with deterministic normalized findings.
        """
        try:
            return self._analyze_archive(image_tar_path)
        except (OSError, tarfile.TarError, json.JSONDecodeError, ValueError) as exc:
            return [
                Finding(
                    rule_id="LAY001",
                    title="Layer archive analysis failed",
                    severity=Severity.MEDIUM,
                    source=self._PROVIDER_NAME,
                    detail=f"Unable to parse image archive: {exc}",
                    remediation="Provide a valid Docker image tar archive with manifest metadata.",
                    location=FindingLocation(path=image_tar_path),
                )
            ]

    def _analyze_archive(self, image_tar_path: str) -> list[Finding]:
        findings: list[Finding] = []

        with tarfile.open(image_tar_path, mode="r") as archive:
            members = {member.name: member for member in archive.getmembers() if member.isfile()}
            if "manifest.json" not in members:
                findings.append(
                    Finding(
                        rule_id="LAY002",
                        title="Missing image manifest",
                        severity=Severity.HIGH,
                        source=self._PROVIDER_NAME,
                        detail="Image archive does not contain manifest.json.",
                        remediation="Create the image archive with a standard Docker-compatible format.",
                        location=FindingLocation(path=image_tar_path),
                    )
                )
                return findings

            manifest_payload = self._extract_json_member(archive, members["manifest.json"])
            manifest_entries = manifest_payload if isinstance(manifest_payload, list) else []
            if not manifest_entries:
                findings.append(
                    Finding(
                        rule_id="LAY003",
                        title="Empty image manifest",
                        severity=Severity.MEDIUM,
                        source=self._PROVIDER_NAME,
                        detail="manifest.json contains no image entries.",
                        remediation="Ensure the archive contains at least one image definition.",
                        location=FindingLocation(path=image_tar_path),
                    )
                )
                return findings

            first_entry = manifest_entries[0]
            layer_paths = first_entry.get("Layers", []) if isinstance(first_entry, dict) else []
            config_path = first_entry.get("Config") if isinstance(first_entry, dict) else None

            if not layer_paths:
                findings.append(
                    Finding(
                        rule_id="LAY004",
                        title="No layers declared",
                        severity=Severity.HIGH,
                        source=self._PROVIDER_NAME,
                        detail="Image manifest does not declare layer tar entries.",
                        remediation="Rebuild the archive and verify layer metadata is included.",
                        location=FindingLocation(path=image_tar_path),
                    )
                )
            else:
                findings.append(
                    Finding(
                        rule_id="LAY005",
                        title="Layer metadata summary",
                        severity=Severity.LOW,
                        source=self._PROVIDER_NAME,
                        detail=f"Image archive declares {len(layer_paths)} layer(s).",
                        remediation="Review layer count during image-size optimization work.",
                        location=FindingLocation(path=image_tar_path),
                    )
                )

            if config_path and config_path in members:
                config_payload = self._extract_json_member(archive, members[config_path])
                history = config_payload.get("history", []) if isinstance(config_payload, dict) else []
                if history and len(history) > len(layer_paths):
                    findings.append(
                        Finding(
                            rule_id="LAY006",
                            title="Metadata-only history entries detected",
                            severity=Severity.LOW,
                            source=self._PROVIDER_NAME,
                            detail=(
                                "Image config history has more entries than concrete layers, "
                                "which can indicate metadata-only build steps."
                            ),
                            remediation="Inspect build history to ensure layer intent is clear.",
                            location=FindingLocation(path=image_tar_path),
                        )
                    )

        return findings

    @staticmethod
    def _extract_json_member(archive: tarfile.TarFile, member: tarfile.TarInfo) -> object:
        file_obj = archive.extractfile(member)
        if file_obj is None:
            raise ValueError(f"Unable to read archive member: {member.name}")
        with closing(file_obj):
            payload = file_obj.read().decode("utf-8")
        return json.loads(payload)
