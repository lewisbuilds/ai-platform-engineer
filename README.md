# AI Container Intelligence

## Problem This Project Solves
Teams often have Dockerfile checks spread across ad-hoc scripts, local habits, and CI snippets. The result is inconsistent policy outcomes and hard-to-explain failures.

This project provides one minimal, deterministic path for container policy analysis:
- analyze Dockerfiles,
- evaluate policy centrally,
- generate a clear markdown report,
- enforce the same behavior locally and in CI.

## Why Container Policy Analysis Matters
Container images are part of the deployment boundary. Weak Dockerfile practices can introduce avoidable risk before runtime.

Policy analysis gives an auditable decision point before merge:
- identify risky build/runtime patterns early,
- classify findings as advisory or blocking,
- make CI outcomes explainable to reviewers,
- reduce production surprises caused by image hardening gaps.

## Minimal, Explainable Design
The architecture is intentionally small so each responsibility is obvious.

```text
CLI (thin)
  -> Pipeline orchestrator
      -> Analysis + Providers
          -> Policy evaluation
              -> Markdown report
```

Key properties:
- one CLI entrypoint,
- one orchestrator,
- provider integration behind typed seams,
- one policy evaluator as decision source,
- deterministic report output.

See [docs/architecture.md](docs/architecture.md) for full details.

## CI Enforcement Model
Primary workflow: [.github/workflows/pr-container-intelligence.yml](.github/workflows/pr-container-intelligence.yml)

For relevant pull requests, CI:
1. installs and validates the project,
2. runs security and test gates,
3. runs parser fidelity gates before full suite,
4. analyzes changed Dockerfiles (or all tracked Dockerfiles when policy files change),
5. publishes markdown report artifacts,
6. fails when policy blocking conditions are met (`--fail-on-policy`, exit code `3`).

This keeps enforcement deterministic and reviewable.

## Detection Credibility: Golden Corpus
Detection quality is guarded by curated fixtures and expected outcomes in [tests/fixtures/golden/corpus_cases.json](tests/fixtures/golden/corpus_cases.json).

The corpus ensures credibility by requiring:
- expected findings for positive cases,
- expected non-findings for clean cases,
- real-world style fixtures (not only synthetic examples),
- explicit coverage checks linking implemented rule IDs to corpus evidence.

This prevents “rule exists but no proof” drift.

## Detection Quality Guard: Parser Accuracy Governance
Parser behavior is governed separately from policy outcome rendering.

Inputs and checks:
- parser fidelity dataset: [tests/fixtures/golden/parser_fidelity_cases.json](tests/fixtures/golden/parser_fidelity_cases.json)
- metric test: [tests/unit/test_parser_accuracy_metric.py](tests/unit/test_parser_accuracy_metric.py)
- known blind spots (explicitly tracked): [tests/unit/test_detection_known_blind_spots.py](tests/unit/test_detection_known_blind_spots.py)

CI runs parser fidelity checks before the full suite to keep parser regressions visible and measurable.

## Quick Start
Requirements:
- Python 3.10+

Install and validate:
```bash
python -m pip install -e .
pytest
```

Analyze one Dockerfile:
```bash
aci --dockerfile examples/dockerfiles/minimal-secure.Dockerfile
```

Write report to file:
```bash
aci --dockerfile examples/dockerfiles/minimal-secure.Dockerfile --output examples/reports/sample-pr-report.md
```

Enable policy gate:
```bash
aci --dockerfile examples/dockerfiles/minimal-secure.Dockerfile --fail-on-policy
```

## Repository Map
- [src/ai_container_intelligence](src/ai_container_intelligence): analysis, pipeline, policy, reporting, CLI
- [tests](tests): unit, integration, governance, golden corpus checks
- [docs](docs): architecture and developer workflow
- [examples](examples): sample Dockerfiles and reports

