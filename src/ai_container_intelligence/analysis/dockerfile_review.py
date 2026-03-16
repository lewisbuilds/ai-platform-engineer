"""Dockerfile parsing and review entry points."""

from dataclasses import dataclass
from pathlib import Path

from ai_container_intelligence.models.findings import (
    Finding,
    FindingLocation,
    Severity,
    finding_sort_key,
)


@dataclass(frozen=True)
class DockerInstruction:
    """Represents one parsed Dockerfile instruction.

    Args:
        line: 1-based line number.
        opcode: Upper-cased instruction opcode.
        argument: Raw instruction argument.
    """

    line: int
    opcode: str
    argument: str


@dataclass(frozen=True)
class ParsedDockerfile:
    """Parsed Dockerfile representation.

    Args:
        path: Input path.
        instructions: Parsed instructions in file order.
    """

    path: str
    instructions: list[DockerInstruction]


def parse_dockerfile(content: str, path: str) -> ParsedDockerfile:
    """Parse Dockerfile content into normalized instructions.

    Args:
        content: Dockerfile content.
        path: Logical path for location metadata.

    Returns:
        Parsed Dockerfile model.
    """
    instructions: list[DockerInstruction] = []
    for index, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        opcode = parts[0].upper()
        argument = parts[1] if len(parts) > 1 else ""
        instructions.append(DockerInstruction(line=index, opcode=opcode, argument=argument))
    return ParsedDockerfile(path=path, instructions=instructions)


def review_parsed_dockerfile(parsed: ParsedDockerfile) -> list[Finding]:
    """Review parsed Dockerfile against practical baseline rules.

    Args:
        parsed: Parsed Dockerfile data.

    Returns:
        Deterministically sorted findings.
    """
    findings: list[Finding] = []

    from_instructions = [item for item in parsed.instructions if item.opcode == "FROM"]
    if not from_instructions:
        findings.append(
            Finding(
                rule_id="DF001",
                title="Missing FROM instruction",
                severity=Severity.CRITICAL,
                source="dockerfile-review",
                detail="Dockerfile must declare at least one base image.",
                remediation="Add a pinned and trusted FROM image.",
                location=FindingLocation(path=parsed.path, line=None),
            )
        )

    for item in from_instructions:
        lower_arg = item.argument.lower()
        if ":latest" in lower_arg:
            findings.append(
                Finding(
                    rule_id="DF002",
                    title="Unpinned base image tag",
                    severity=Severity.HIGH,
                    source="dockerfile-review",
                    detail="Using :latest makes builds non-reproducible.",
                    remediation="Pin a specific immutable image tag.",
                    location=FindingLocation(path=parsed.path, line=item.line),
                )
            )

    user_instructions = [item for item in parsed.instructions if item.opcode == "USER"]
    if not user_instructions:
        findings.append(
            Finding(
                rule_id="DF003",
                title="Missing USER instruction",
                severity=Severity.HIGH,
                source="dockerfile-review",
                detail="Container may run as root by default.",
                remediation="Set USER to a non-root user for runtime.",
                location=FindingLocation(path=parsed.path, line=None),
            )
        )
    else:
        for item in user_instructions:
            user_value = item.argument.strip().lower()
            if user_value in {"root", "0"}:
                findings.append(
                    Finding(
                        rule_id="DF004",
                        title="Container configured to run as root",
                        severity=Severity.HIGH,
                        source="dockerfile-review",
                        detail="Running as root increases container attack surface.",
                        remediation="Use a non-root runtime user.",
                        location=FindingLocation(path=parsed.path, line=item.line),
                    )
                )

    for item in parsed.instructions:
        lower_arg = item.argument.lower()
        if item.opcode == "ADD":
            findings.append(
                Finding(
                    rule_id="DF005",
                    title="ADD instruction used",
                    severity=Severity.MEDIUM,
                    source="dockerfile-review",
                    detail="ADD can have implicit behaviors that reduce clarity.",
                    remediation="Prefer COPY unless ADD-specific behavior is required.",
                    location=FindingLocation(path=parsed.path, line=item.line),
                )
            )
        if item.opcode == "RUN" and "apt-get update" in lower_arg and "rm -rf /var/lib/apt/lists" not in lower_arg:
            findings.append(
                Finding(
                    rule_id="DF006",
                    title="apt cache not cleaned in RUN layer",
                    severity=Severity.MEDIUM,
                    source="dockerfile-review",
                    detail="apt cache cleanup missing after apt-get update/install.",
                    remediation="Combine install and cleanup in the same RUN layer.",
                    location=FindingLocation(path=parsed.path, line=item.line),
                )
            )
        if item.opcode == "RUN" and ("curl" in lower_arg and "|" in lower_arg):
            findings.append(
                Finding(
                    rule_id="DF007",
                    title="Piped remote script execution",
                    severity=Severity.HIGH,
                    source="dockerfile-review",
                    detail="RUN uses a piped command that may execute unverified remote content.",
                    remediation="Download, verify checksum/signature, then execute explicitly.",
                    location=FindingLocation(path=parsed.path, line=item.line),
                )
            )

    return sorted(findings, key=finding_sort_key)


def review_dockerfile(path: str) -> list[Finding]:
    """Read and analyze a Dockerfile at the given path.

    Args:
        path: Path to Dockerfile.

    Returns:
        Deterministically sorted findings.
    """
    content = Path(path).read_text(encoding="utf-8")
    parsed = parse_dockerfile(content=content, path=path)
    return review_parsed_dockerfile(parsed)
