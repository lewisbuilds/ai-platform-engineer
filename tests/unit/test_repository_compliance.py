"""Repository compliance tests protecting intentional v1 design constraints."""

from pathlib import Path
from typing import Final


REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[2]

PRIMARY_WORKFLOW_NAME: Final[str] = "pr-container-intelligence.yml"
REQUIRED_COPILOT_ASSETS: Final[set[Path]] = {
    Path("agents/container-review.agent.md"),
    Path("instructions/container-engineering-standards.instructions.md"),
    Path("skills/container-analysis/SKILL.md"),
}
FORBIDDEN_SOURCE_PATHS: Final[set[Path]] = {
    Path("src/ai_container_intelligence/github"),
    Path("src/ai_container_intelligence/rules"),
}
APPROVED_TOP_LEVEL_SOURCE_ENTRIES: Final[set[str]] = {
    "__init__.py",
    "analysis",
    "cli",
    "integrations",
    "models",
    "pipeline.py",
    "reporting",
}
FORBIDDEN_CLI_IMPORT_PREFIXES: Final[tuple[str, ...]] = (
    "ai_container_intelligence.analysis",
    "ai_container_intelligence.integrations",
    "ai_container_intelligence.reporting",
    "ai_container_intelligence.github",
    "ai_container_intelligence.rules",
)


def _read_primary_workflow() -> str:
    """Load primary workflow as text for policy assertions."""
    workflow_path = REPO_ROOT / ".github" / "workflows" / PRIMARY_WORKFLOW_NAME
    return workflow_path.read_text(encoding="utf-8")


def _read_pre_commit_hook() -> str:
    """Load managed pre-commit hook for policy assertions."""
    hook_path = REPO_ROOT / ".githooks" / "pre-commit"
    return hook_path.read_text(encoding="utf-8")


def test_github_actions_workflow_minimality() -> None:
    """Ensure version 1 keeps a single primary GitHub Actions workflow."""
    workflows_dir = REPO_ROOT / ".github" / "workflows"
    discovered = {
        path.name
        for path in workflows_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".yml", ".yaml"}
    }
    assert discovered == {PRIMARY_WORKFLOW_NAME}


def test_github_actions_permissions_are_least_privilege() -> None:
    """Ensure workflow uses read-only repository permissions by default."""
    workflow_text = _read_primary_workflow()
    assert "permissions:" in workflow_text
    assert "contents: read" in workflow_text


def test_github_actions_includes_security_checks() -> None:
    """Ensure workflow keeps mandatory security scanning steps."""
    workflow_text = _read_primary_workflow()
    assert "bandit -q -r src/ai_container_intelligence" in workflow_text
    assert "Potential secret-like material detected in repository." in workflow_text


def test_github_actions_targets_changed_container_files() -> None:
    """Ensure workflow keeps PR changed-target analysis behavior."""
    workflow_text = _read_primary_workflow()
    assert "git diff --name-only \"$BASE_SHA\" \"$HEAD_SHA\"" in workflow_text
    assert "CHANGED_DOCKERFILES" in workflow_text
    assert "CHANGED_POLICY_FILES" in workflow_text
    assert "changed-targets-summary.md" in workflow_text
    assert ".hadolint.yaml" in workflow_text
    assert ".dockerignore" in workflow_text
    assert "instructions/container-engineering-standards.instructions.md" in workflow_text
    assert "skills/container-analysis/SKILL.md" in workflow_text


def test_pre_commit_security_hook_exists_and_has_required_checks() -> None:
    """Ensure managed pre-commit hook enforces local security checks."""
    hook_path = REPO_ROOT / ".githooks" / "pre-commit"
    assert hook_path.is_file()

    hook_text = _read_pre_commit_hook()
    assert "python -m bandit -q -r src/ai_container_intelligence" in hook_text
    assert "Potential secret-like material detected in staged files." in hook_text


def test_required_copilot_assets_exist() -> None:
    """Ensure required Copilot customization assets are present."""
    missing = sorted(
        str(path)
        for path in REQUIRED_COPILOT_ASSETS
        if not (REPO_ROOT / path).is_file()
    )
    assert not missing, f"Missing required Copilot assets: {missing}"


def test_forbidden_speculative_modules_do_not_exist() -> None:
    """Ensure removed speculative source modules are not reintroduced."""
    present = sorted(
        str(path)
        for path in FORBIDDEN_SOURCE_PATHS
        if (REPO_ROOT / path).exists()
    )
    assert not present, f"Forbidden speculative source paths found: {present}"


def test_core_package_boundaries_match_approved_v1_set() -> None:
    """Ensure top-level package layout stays within approved v1 boundaries."""
    package_root = REPO_ROOT / "src" / "ai_container_intelligence"
    discovered = {
        path.name
        for path in package_root.iterdir()
        if path.name != "__pycache__"
    }
    assert discovered == APPROVED_TOP_LEVEL_SOURCE_ENTRIES


def test_cli_module_stays_thin_and_pipeline_oriented() -> None:
    """Ensure CLI entrypoint keeps thin orchestration-only import boundaries."""
    cli_path = REPO_ROOT / "src" / "ai_container_intelligence" / "cli" / "main.py"
    content = cli_path.read_text(encoding="utf-8")
    import_lines = [
        line.strip()
        for line in content.splitlines()
        if line.strip().startswith("import ") or line.strip().startswith("from ")
    ]

    assert "from ai_container_intelligence.pipeline import run_pipeline" in content
    assert "run_pipeline(" in content

    for prefix in FORBIDDEN_CLI_IMPORT_PREFIXES:
        assert all(
            f"from {prefix} import" not in line and f"import {prefix}" not in line
            for line in import_lines
        )
