"""Artifact model types."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DockerfileArtifact:
    """Input metadata for Dockerfile analysis.

    Args:
        path: Path to the Dockerfile under analysis.
        content: Full Dockerfile content.
    """

    path: str
    content: str


@dataclass(frozen=True)
class ImageTarArtifact:
    """Input metadata for image tarball analysis.

    Args:
        path: Path to image tarball.
        size_bytes: Tarball size in bytes.
    """

    path: str
    size_bytes: int


@dataclass(frozen=True)
class AnalysisInput:
    """Unified analysis input for orchestration.

    Args:
        dockerfile: Dockerfile artifact to review.
        image_tar: Optional image tar artifact for layer and scan workflows.
        image_ref: Optional image reference for integration providers.
    """

    dockerfile: DockerfileArtifact
    image_tar: ImageTarArtifact | None = None
    image_ref: str | None = None
