"""Unit tests for tar archive layer analysis provider."""

from __future__ import annotations

import io
import json
from pathlib import Path
import tarfile

from ai_container_intelligence.integrations.layer_analysis_provider import (
    TarLayerAnalysisProvider,
)


def _add_text_member(archive: tarfile.TarFile, name: str, content: str) -> None:
    payload = content.encode("utf-8")
    info = tarfile.TarInfo(name=name)
    info.size = len(payload)
    archive.addfile(info, io.BytesIO(payload))


def test_tar_layer_provider_detects_manifest_and_layer_summary(tmp_path: Path) -> None:
    """Create a valid archive and assert deterministic summary findings."""
    archive_path = tmp_path / "image.tar"
    with tarfile.open(archive_path, mode="w") as archive:
        manifest = [{"Config": "config.json", "Layers": ["layer1.tar", "layer2.tar"]}]
        config = {"history": [{"created_by": "RUN apt-get update"}]}
        _add_text_member(archive, "manifest.json", json.dumps(manifest))
        _add_text_member(archive, "config.json", json.dumps(config))
        _add_text_member(archive, "layer1.tar", "layer-one")
        _add_text_member(archive, "layer2.tar", "layer-two")

    provider = TarLayerAnalysisProvider()
    result = provider.analyze(str(archive_path))

    assert any(item.rule_id == "LAY005" for item in result)
    assert not any(item.rule_id in {"LAY001", "LAY002", "LAY003", "LAY004"} for item in result)


def test_tar_layer_provider_handles_missing_manifest(tmp_path: Path) -> None:
    """Return deterministic finding when manifest.json is missing."""
    archive_path = tmp_path / "invalid-image.tar"
    with tarfile.open(archive_path, mode="w") as archive:
        _add_text_member(archive, "config.json", json.dumps({"history": []}))

    provider = TarLayerAnalysisProvider()
    result = provider.analyze(str(archive_path))

    assert [item.rule_id for item in result] == ["LAY002"]
