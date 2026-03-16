"""Integration tests for CLI behavior."""

from pathlib import Path

import pytest

from ai_container_intelligence.cli import main as cli_main


def test_build_parser_defaults() -> None:
    """Ensure parser defaults are stable for version 1."""
    parser = cli_main.build_parser()
    args = parser.parse_args(["--dockerfile", "tests/fixtures/Dockerfile.good"])
    assert args.output_format == "markdown"
    assert args.provider_profile == "real"
    assert args.policy_profile == "strict"
    assert args.image_tar is None
    assert args.output is None
    assert args.dockerfile == ["tests/fixtures/Dockerfile.good"]


def test_main_success_prints_markdown(capsys: pytest.CaptureFixture[str]) -> None:
    """Ensure CLI prints markdown report on success when no output file is set."""
    code = cli_main.main(["--dockerfile", "tests/fixtures/Dockerfile.good"])
    out = capsys.readouterr()
    assert code == cli_main.EXIT_SUCCESS
    assert "# AI Container Intelligence Report" in out.out


def test_main_writes_output_file(tmp_path: Path) -> None:
    """Ensure CLI writes report to file when output path is provided."""
    output_file = tmp_path / "report.md"
    code = cli_main.main(
        [
            "--dockerfile",
            "tests/fixtures/Dockerfile.good",
            "--output",
            str(output_file),
        ]
    )
    assert code == cli_main.EXIT_SUCCESS
    assert output_file.exists()
    assert "# AI Container Intelligence Report" in output_file.read_text(encoding="utf-8")


def test_main_invalid_dockerfile_returns_invalid_input(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Ensure missing Dockerfile path returns invalid input exit code."""
    code = cli_main.main(["--dockerfile", "tests/fixtures/missing.Dockerfile"])
    err = capsys.readouterr().err
    assert code == cli_main.EXIT_INVALID_INPUT
    assert "Input validation error:" in err


def test_main_runtime_error_returns_runtime_exit_code(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Ensure runtime pipeline failures produce user-friendly runtime error."""

    def _raise_runtime_error(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(cli_main, "run_pipeline", _raise_runtime_error)
    code = cli_main.main(["--dockerfile", "tests/fixtures/Dockerfile.good"])
    err = capsys.readouterr().err
    assert code == cli_main.EXIT_RUNTIME_ERROR
    assert "Execution error:" in err


def test_main_passes_provider_profile_to_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure CLI forwards provider profile without adding orchestration logic."""
    captured: dict[str, str] = {}

    def _capture_pipeline(*_args: object, **kwargs: object) -> object:
        profile = kwargs.get("provider_profile")
        if isinstance(profile, str):
            captured["provider_profile"] = profile
        policy_profile = kwargs.get("policy_profile")
        if isinstance(policy_profile, str):
            captured["policy_profile"] = policy_profile

        class _Result:
            report = type("_Report", (), {"content": "# AI Container Intelligence Report"})()

        return _Result()

    monkeypatch.setattr(cli_main, "run_pipeline", _capture_pipeline)
    code = cli_main.main(
        [
            "--dockerfile",
            "tests/fixtures/Dockerfile.good",
            "--provider-profile",
            "noop",
            "--policy-profile",
            "relaxed",
        ]
    )

    assert code == cli_main.EXIT_SUCCESS
    assert captured["provider_profile"] == "noop"
    assert captured["policy_profile"] == "relaxed"


def test_main_runs_pipeline_for_each_dockerfile_target(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Ensure CLI executes pipeline once per Dockerfile target in input order."""
    captured_paths: list[str] = []

    def _capture_pipeline(*_args: object, **kwargs: object) -> object:
        dockerfile_path = kwargs.get("dockerfile_path")
        if isinstance(dockerfile_path, str):
            captured_paths.append(dockerfile_path)

        class _Result:
            report = type(
                "_Report",
                (),
                {"content": f"# AI Container Intelligence Report\n\nPath: {dockerfile_path}"},
            )()

        return _Result()

    monkeypatch.setattr(cli_main, "run_pipeline", _capture_pipeline)

    code = cli_main.main(
        [
            "--dockerfile",
            "tests/fixtures/Dockerfile.good",
            "tests/fixtures/Dockerfile.good",
        ]
    )

    out = capsys.readouterr().out
    assert code == cli_main.EXIT_SUCCESS
    assert captured_paths == [
        "tests/fixtures/Dockerfile.good",
        "tests/fixtures/Dockerfile.good",
    ]
    assert out.count("## Target:") == 2
    assert "---" in out
