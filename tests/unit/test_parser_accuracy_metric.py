"""Parser fidelity metric test for curated Dockerfile corpus cases."""

import json
from pathlib import Path
from typing import Any, Final, cast

from ai_container_intelligence.analysis.dockerfile_review import (
    ParsedDockerfile,
    parse_dockerfile,
)


FIXTURES_DIR: Final[Path] = Path(__file__).resolve().parents[1] / "fixtures" / "golden"
PARSER_CASES_FILE: Final[Path] = FIXTURES_DIR / "parser_fidelity_cases.json"


def _load_parser_cases() -> dict[str, Any]:
    payload = json.loads(PARSER_CASES_FILE.read_text(encoding="utf-8"))
    return cast(dict[str, Any], payload)


def _evaluate_assertion(parsed: ParsedDockerfile, assertion: dict[str, Any]) -> bool:
    assertion_type = str(assertion.get("type", ""))

    if assertion_type == "instruction_count":
        return len(parsed.instructions) == int(assertion["equals"])

    if assertion_type == "opcode_count":
        opcode = str(assertion["opcode"]).upper()
        expected = int(assertion["equals"])
        actual = sum(1 for item in parsed.instructions if item.opcode == opcode)
        return actual == expected

    if assertion_type == "opcode_at_index":
        index = int(assertion["index"])
        expected_opcode = str(assertion["equals"]).upper()
        if index < 0 or index >= len(parsed.instructions):
            return False
        actual_opcode = str(parsed.instructions[index].opcode)
        return actual_opcode == expected_opcode

    raise ValueError(f"Unsupported parser assertion type: {assertion_type}")


def test_parser_accuracy_metric_meets_baseline_threshold() -> None:
    """Enforce parser-structure accuracy ratio against stored baseline threshold."""
    payload = _load_parser_cases()
    threshold = float(payload["threshold"])
    cases = list(payload["cases"])

    total_assertions = 0
    passed_assertions = 0
    failed_assertions: list[str] = []

    for case in cases:
        fixture_name = str(case["fixture_name"])
        fixture_path = FIXTURES_DIR / fixture_name
        parsed = parse_dockerfile(
            content=fixture_path.read_text(encoding="utf-8"),
            path=str(fixture_path),
        )

        for assertion in case["assertions"]:
            total_assertions += 1
            if _evaluate_assertion(parsed, assertion):
                passed_assertions += 1
            else:
                failed_assertions.append(f"{fixture_name}: {assertion}")

    accuracy_ratio = passed_assertions / total_assertions if total_assertions else 0.0

    assert accuracy_ratio >= threshold, (
        "Parser accuracy ratio below baseline threshold. "
        f"ratio={accuracy_ratio:.3f}, threshold={threshold:.3f}, "
        f"passed={passed_assertions}, total={total_assertions}, "
        f"failed_assertions={failed_assertions}"
    )
