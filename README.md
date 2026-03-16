# AI Container Intelligence

## 1) Project Overview
AI Container Intelligence is a local-first Python toolchain for reviewing Dockerfiles and producing deterministic markdown reports suitable for pull-request workflows.

This repository is intentionally minimal v2: one clear analysis path, one thin CLI entrypoint, one primary CI workflow, centralized policy evaluation, and enforced repository boundaries.

## 2) Why This Exists
Container checks often start as ad-hoc scripts and then become hard to maintain. This project exists to show a practical baseline that is:
- easy to run locally,
- easy to enforce in CI,
- easy to extend through typed integration seams,
- hard to overgrow accidentally.

The design favors the smallest useful architecture over broad feature coverage.

## 3) Core Capabilities in v2
- Dockerfile-focused static review with deterministic findings.
- Normalized report model and markdown PR-style rendering.
- Thin CLI (`aci`) for local and CI execution.
- Multi-target execution from one command (`--dockerfile` accepts one or more paths).
- Pipeline orchestration with centralized policy-backed severity evaluation.
- Integration points (contracts + real/no-op providers) for:
	- image layer analysis,
	- SBOM generation,
	- vulnerability scanning.
- Built-in policy profiles:
	- `strict`: blocks `critical` findings and explicit `DF004` root-runtime violations.
	- `relaxed`: blocks `critical` findings only.
- Optional CI/local policy gate via `--fail-on-policy` (exit code `3` on blocking findings).
- Minimal PR GitHub Actions automation with test and security gates.
- Compliance tests that enforce maintainable architectural boundaries.

## 4) Architecture Summary
Runtime flow:
1. CLI validates inputs.
2. Pipeline runs Dockerfile analysis.
3. Integration providers are selected by profile (`real|noop`) and invoked through typed seams.
4. Findings are normalized into a shared report model.
5. Centralized policy evaluation assigns advisory/blocking dispositions.
6. Markdown report is rendered and written to stdout or file.

Key files:
- Pipeline orchestration: [src/ai_container_intelligence/pipeline.py](src/ai_container_intelligence/pipeline.py)
- CLI entrypoint: [src/ai_container_intelligence/cli/main.py](src/ai_container_intelligence/cli/main.py)
- Dockerfile review logic: [src/ai_container_intelligence/analysis/dockerfile_review.py](src/ai_container_intelligence/analysis/dockerfile_review.py)
- Markdown rendering: [src/ai_container_intelligence/reporting/markdown_report.py](src/ai_container_intelligence/reporting/markdown_report.py)

For deeper detail, see [docs/architecture.md](docs/architecture.md).

## 5) Repo Structure
- [src/ai_container_intelligence](src/ai_container_intelligence): production package
	- `analysis/`: Dockerfile analysis logic
	- `integrations/`: provider contracts and real/no-op adapters
	- `models/`: typed contracts (findings, report)
	- `reporting/`: output rendering
	- `cli/`: thin command surface
	- `pipeline.py`: orchestration
- [tests](tests): unit and integration tests, including repository compliance checks
- [examples](examples): sample Dockerfiles and generated reports
- [docs](docs): architecture, development, and Copilot customization docs
- [agents](agents), [instructions](instructions), [skills](skills): Copilot customization assets used in this repo

## 6) Local Usage
Requirements:
- Python 3.10+

Install and verify:
```bash
python -m pip install -e .
pytest
```

Run analysis to stdout:
```bash
aci --dockerfile examples/dockerfiles/minimal-secure.Dockerfile
```

Run analysis for multiple Dockerfiles in one invocation:
```bash
aci --dockerfile examples/dockerfiles/minimal-secure.Dockerfile path/to/another.Dockerfile
```

Write markdown report to file:
```bash
aci --dockerfile examples/dockerfiles/minimal-secure.Dockerfile --output examples/reports/sample-pr-report.md
```

CLI notes:
- `--dockerfile` is required and accepts one or more paths.
- `--image-tar` is optional and used only for integration provider paths.
- `--provider-profile` supports `real` and `noop`.
- `--policy-profile` supports `strict` and `relaxed`.
- `--fail-on-policy` enables explicit blocking exit behavior (exit code `3`).
- `--output` is optional; without it, report content is printed to stdout.

## 7) Example Analysis Flow
Realistic local flow for a PR candidate Dockerfile:
1. Edit or add a Dockerfile.
2. Run:
	 ```bash
	 aci --dockerfile path/to/Dockerfile --output artifacts/report.md
	 ```
3. Review the markdown findings in `artifacts/report.md`.
4. Iterate on Dockerfile changes and rerun until findings are acceptable.
5. Commit with local checks enabled (see [docs/development.md](docs/development.md) for managed hook setup).

This mirrors CI behavior while keeping feedback fast on a developer workstation.

## 8) GitHub Actions Workflow Behavior
Primary workflow: [\.github/workflows/pr-container-intelligence.yml](.github/workflows/pr-container-intelligence.yml)

On relevant pull request changes, it:
1. checks out code and sets up Python 3.10,
2. installs the package,
3. runs security checks (Bandit + secret-pattern scan),
4. runs `pytest`,
5. analyzes changed Dockerfiles with `aci` (or all Dockerfiles when policy files change; sample fallback for non-PR manual runs),
6. uploads markdown reports as artifacts,
7. writes a concise run summary.

## 9) Copilot Customizations Included
This repository includes minimal Copilot customization assets to keep AI-assisted changes aligned with project boundaries:
- Agent definition: [agents/container-review.agent.md](agents/container-review.agent.md)
- Repository instruction: [instructions/container-engineering-standards.instructions.md](instructions/container-engineering-standards.instructions.md)
- Skill entrypoint: [skills/container-analysis/SKILL.md](skills/container-analysis/SKILL.md)

See [docs/copilot-customizations.md](docs/copilot-customizations.md) for context.

## 10) Design Choices That Reduce Tech Debt
- Single orchestration path in `pipeline.py` avoids duplicated business logic.
- Thin CLI prevents command-surface bloat and keeps test scope focused.
- Typed contracts in `models/` and `integrations/` stabilize interfaces.
- Deterministic markdown output keeps CI and review behavior predictable.
- One primary workflow reduces CI sprawl.
- Compliance tests enforce boundaries so architectural drift fails fast.

## 11) Out of Scope for v2
Intentionally excluded in this repository version:
- database persistence,
- web UI,
- Kubernetes-native automation,
- release/publishing automation,
- dynamic plugin loading,
- remote scanner orchestration frameworks.

These are excluded to keep v2 small, understandable, and maintainable.

