"""Repository compliance tests protecting intentional v2 design constraints."""

import ast
import json
from pathlib import Path
from typing import Final


REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[2]

PRIMARY_WORKFLOW_NAME: Final[str] = "pr-container-intelligence.yml"
APPROVED_WORKFLOW_NAMES: Final[set[str]] = {PRIMARY_WORKFLOW_NAME}
REQUIRED_COPILOT_ASSETS: Final[set[Path]] = {
    Path("agents/container-review.agent.md"),
    Path("instructions/container-engineering-standards.instructions.md"),
    Path("skills/container-analysis/SKILL.md"),
}
FORBIDDEN_SOURCE_PATHS: Final[set[Path]] = {
    Path("src/ai_container_intelligence/github"),
    Path("src/ai_container_intelligence/rules"),
    Path("src/ai_container_intelligence/compliance"),
    Path("src/ai_container_intelligence/policy_engine"),
}
APPROVED_TOP_LEVEL_SOURCE_ENTRIES: Final[set[str]] = {
    "__init__.py",
    "analysis",
    "cli",
    "integrations",
    "models",
    "pipeline.py",
    "policy",
    "reporting",
}
FORBIDDEN_CLI_IMPORT_PREFIXES: Final[tuple[str, ...]] = (
    "ai_container_intelligence.analysis",
    "ai_container_intelligence.integrations",
    "ai_container_intelligence.reporting",
    "ai_container_intelligence.github",
    "ai_container_intelligence.rules",
    "ai_container_intelligence.policy",
)
POLICY_EVALUATION_CALL_ALLOWLIST: Final[set[Path]] = {
    Path("src/ai_container_intelligence/pipeline.py"),
    Path("src/ai_container_intelligence/policy/evaluator.py"),
}
PARSER_METRIC_TEST: Final[Path] = Path("tests/unit/test_parser_accuracy_metric.py")
BLIND_SPOT_TEST: Final[Path] = Path("tests/unit/test_detection_known_blind_spots.py")
CORPUS_CASES_JSON: Final[Path] = Path("tests/fixtures/golden/corpus_cases.json")
PARSER_FIDELITY_CASES_JSON: Final[Path] = Path(
    "tests/fixtures/golden/parser_fidelity_cases.json"
)
GOLDEN_FIXTURES_DIR: Final[Path] = Path("tests/fixtures/golden")
ALLOWED_CLI_IMPORT_TARGETS: Final[set[str]] = {
    "ai_container_intelligence",
    "ai_container_intelligence.pipeline",
}


def _read_primary_workflow() -> str:
    """Load primary workflow as text for policy assertions."""
    workflow_path = REPO_ROOT / ".github" / "workflows" / PRIMARY_WORKFLOW_NAME
    return workflow_path.read_text(encoding="utf-8")


def _read_pre_commit_hook() -> str:
    """Load managed pre-commit hook for policy assertions."""
    hook_path = REPO_ROOT / ".githooks" / "pre-commit"
    return hook_path.read_text(encoding="utf-8")


def _load_corpus_cases() -> list[dict[str, object]]:
    """Load shared corpus case definitions.

    Returns:
        Parsed list of corpus case definitions.
    """
    cases_path = REPO_ROOT / CORPUS_CASES_JSON
    payload = json.loads(cases_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise AssertionError("Corpus case definitions must be a list in corpus_cases.json")
    return [item for item in payload if isinstance(item, dict)]


def _load_dockerfile_rule_ids_from_source() -> tuple[str, ...]:
    """Extract Dockerfile analyzer rule IDs from source to avoid runtime imports.

    Returns:
        Tuple of configured Dockerfile analyzer rule IDs.
    """
    analyzer_path = (
        REPO_ROOT
        / "src"
        / "ai_container_intelligence"
        / "analysis"
        / "dockerfile_review.py"
    )
    source = analyzer_path.read_text(encoding="utf-8")
    module = ast.parse(source)

    def _extract_tuple(value: ast.expr) -> tuple[str, ...] | None:
        if not isinstance(value, ast.Tuple):
            return None
        extracted = tuple(
            item.value
            for item in value.elts
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        )
        return extracted if extracted else None

    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "DOCKERFILE_REVIEW_RULE_IDS"
                ):
                    extracted = _extract_tuple(node.value)
                    if extracted:
                        return extracted
        if isinstance(node, ast.AnnAssign):
            target = node.target
            if (
                isinstance(target, ast.Name)
                and target.id == "DOCKERFILE_REVIEW_RULE_IDS"
                and node.value is not None
            ):
                extracted = _extract_tuple(node.value)
                if extracted:
                    return extracted

    raise AssertionError(
        "Could not extract DOCKERFILE_REVIEW_RULE_IDS from "
        "src/ai_container_intelligence/analysis/dockerfile_review.py"
    )


def test_github_actions_workflow_minimality() -> None:
    """Ensure repository keeps exactly one approved GitHub Actions workflow."""
    workflows_dir = REPO_ROOT / ".github" / "workflows"
    discovered = {
        path.name
        for path in workflows_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".yml", ".yaml"}
    }
    assert discovered == APPROVED_WORKFLOW_NAMES, (
        "Workflow minimality violation: expected exactly "
        f"{sorted(APPROVED_WORKFLOW_NAMES)}, found {sorted(discovered)}"
    )


def test_parser_metric_test_exists_and_is_referenced_in_workflow() -> None:
    """Ensure parser fidelity metric is explicitly enforced by CI."""
    parser_metric_path = REPO_ROOT / PARSER_METRIC_TEST
    blind_spot_path = REPO_ROOT / BLIND_SPOT_TEST
    assert parser_metric_path.is_file(), (
        "Parser metric enforcement missing: expected "
        f"{PARSER_METRIC_TEST} to exist."
    )
    assert blind_spot_path.is_file(), (
        "Parser blind-spot tracker missing: expected "
        f"{BLIND_SPOT_TEST} to exist."
    )

    workflow_text = _read_primary_workflow()
    assert "Run parser fidelity checks" in workflow_text, (
        "Parser fidelity CI step missing in primary workflow."
    )
    assert str(PARSER_METRIC_TEST).replace("\\", "/") in workflow_text, (
        "Primary workflow does not reference parser metric test."
    )


def test_corpus_governance_assets_exist_and_include_realworld_cases() -> None:
    """Ensure corpus governance files and realistic fixtures remain present."""
    corpus_cases_path = REPO_ROOT / CORPUS_CASES_JSON
    parser_fidelity_path = REPO_ROOT / PARSER_FIDELITY_CASES_JSON

    assert corpus_cases_path.is_file(), (
        "Corpus governance missing: expected tests/fixtures/golden/corpus_cases.json"
    )
    assert parser_fidelity_path.is_file(), (
        "Parser fidelity governance missing: expected "
        "tests/fixtures/golden/parser_fidelity_cases.json"
    )

    realworld_fixtures = sorted(
        path.name
        for path in (REPO_ROOT / GOLDEN_FIXTURES_DIR).glob("realworld-*.Dockerfile")
    )
    assert len(realworld_fixtures) >= 3, (
        "Corpus representativeness violation: expected at least 3 realworld fixtures, "
        f"found {len(realworld_fixtures)} ({realworld_fixtures})"
    )


def test_every_dockerfile_rule_has_expected_finding_evidence() -> None:
    """Ensure implemented Dockerfile rules are demonstrated by corpus expected findings."""
    dockerfile_rule_ids = tuple(_load_dockerfile_rule_ids_from_source())
    expected_finding_rule_ids: set[str] = set()
    for case in _load_corpus_cases():
        expected_rules = case.get("expected_rules")
        if isinstance(expected_rules, list):
            expected_finding_rule_ids.update(
                str(rule_id) for rule_id in expected_rules
            )

    missing = sorted(
        rule_id
        for rule_id in dockerfile_rule_ids
        if rule_id not in expected_finding_rule_ids
    )
    assert not missing, (
        "Rule IDs missing expected-finding corpus coverage: " + ", ".join(missing)
    )


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


def test_core_package_boundaries_match_approved_v2_set() -> None:
    """Ensure top-level package layout stays within approved v2 boundaries."""

    package_root = REPO_ROOT / "src" / "ai_container_intelligence"
    discovered = {
        path.name
        for path in package_root.iterdir()
        if path.name != "__pycache__"
    }
    assert discovered == APPROVED_TOP_LEVEL_SOURCE_ENTRIES


def test_provider_implementations_stay_within_integrations_package() -> None:
    """Ensure provider implementation modules remain scoped to integrations package."""
    source_root = REPO_ROOT / "src" / "ai_container_intelligence"
    provider_files = {
        path.relative_to(REPO_ROOT)
        for path in source_root.rglob("*_provider.py")
    }

    outside_integrations = sorted(
        str(path)
        for path in provider_files
        if path.parts[:3] != ("src", "ai_container_intelligence", "integrations")
    )
    assert not outside_integrations, (
        "Provider implementation modules must stay under integrations/: "
        f"{outside_integrations}"
    )


def test_policy_evaluation_remains_centralized() -> None:
    """Ensure policy evaluation is defined centrally and only invoked from pipeline."""
    source_root = REPO_ROOT / "src" / "ai_container_intelligence"
    occurrences: set[Path] = set()

    for path in source_root.rglob("*.py"):
        relative = path.relative_to(REPO_ROOT)
        text = path.read_text(encoding="utf-8")
        if "evaluate_findings_policy(" in text:
            occurrences.add(relative)

    assert occurrences == POLICY_EVALUATION_CALL_ALLOWLIST


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


def test_cli_imports_only_pipeline_entrypoints() -> None:
    """Ensure CLI imports only approved package-level entrypoints."""
    cli_path = REPO_ROOT / "src" / "ai_container_intelligence" / "cli" / "main.py"
    content = cli_path.read_text(encoding="utf-8")
    import_lines = [
        line.strip()
        for line in content.splitlines()
        if line.strip().startswith("import ") or line.strip().startswith("from ")
    ]

    internal_imports = [
        line
        for line in import_lines
        if "ai_container_intelligence" in line
    ]
    unexpected = [
        line
        for line in internal_imports
        if not any(
            (
                line.startswith(f"from {allowed} import")
                or line.startswith(f"import {allowed}")
            )
            for allowed in ALLOWED_CLI_IMPORT_TARGETS
        )
    ]

    assert not unexpected, (
        "CLI thinness violation: unexpected internal imports found: "
        f"{unexpected}"
    )
