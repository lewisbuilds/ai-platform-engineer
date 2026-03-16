"""Command-line entry point for AI Container Intelligence."""

import argparse
from pathlib import Path
import sys
from typing import Final

from ai_container_intelligence.pipeline import run_pipeline


EXIT_SUCCESS: Final[int] = 0
EXIT_RUNTIME_ERROR: Final[int] = 1
EXIT_INVALID_INPUT: Final[int] = 2


def _validate_input_path(path: str, label: str) -> None:
    """Validate that an input path points to an existing file.

    Args:
        path: Input path value.
        label: Human-readable input label.

    Raises:
        ValueError: If the path does not exist or is not a file.
    """
    resolved = Path(path)
    if not resolved.exists():
        raise ValueError(f"{label} does not exist: {path}")
    if not resolved.is_file():
        raise ValueError(f"{label} must be a file: {path}")


def _validate_output_path(path: str) -> None:
    """Validate output path location.

    Args:
        path: Output path value.

    Raises:
        ValueError: If output path is a directory or parent directory is missing.
    """
    resolved = Path(path)
    if resolved.exists() and resolved.is_dir():
        raise ValueError(f"Output path must be a file, not a directory: {path}")

    parent = resolved.parent
    if str(parent) not in {"", "."} and not parent.exists():
        raise ValueError(f"Output directory does not exist: {parent}")


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for local execution.

    Returns:
        Configured argument parser.
    """
    parser = argparse.ArgumentParser(description="Run AI Container Intelligence pipeline")
    parser.add_argument("--dockerfile", required=True, help="Path to Dockerfile")
    parser.add_argument("--image-tar", required=False, help="Optional path to image tarball")
    parser.add_argument(
        "--output-format",
        default="markdown",
        choices=["markdown"],
        help="Output format. Version 1 supports markdown.",
    )
    parser.add_argument(
        "--output",
        required=False,
        help="Optional output file path. If omitted, output is written to stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run CLI workflow.

    Args:
        argv: Optional argv list for testing and embedding.

    Returns:
        Process exit code.
    """
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else EXIT_INVALID_INPUT
        return code

    try:
        _validate_input_path(args.dockerfile, "Dockerfile path")
        if args.image_tar:
            _validate_input_path(args.image_tar, "Image tarball path")
        if args.output:
            _validate_output_path(args.output)
    except ValueError as exc:
        print(f"Input validation error: {exc}", file=sys.stderr)
        return EXIT_INVALID_INPUT

    try:
        result = run_pipeline(
            dockerfile_path=args.dockerfile,
            image_tar_path=args.image_tar,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Execution error: {exc}", file=sys.stderr)
        return EXIT_RUNTIME_ERROR

    output_text = result.report.content
    if args.output:
        Path(args.output).write_text(output_text, encoding="utf-8")
    else:
        print(output_text)

    return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
