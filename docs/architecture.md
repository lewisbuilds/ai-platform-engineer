# Architecture (v1)

## What This Repository Does

Version 1 provides a deterministic, local-first container analysis flow centered
on Dockerfile review and markdown report output.

The system is designed to be executable from both:
- local development via `aci`
- CI via GitHub Actions

## Architectural Principles

- single Python package
- composition over inheritance
- strict separation between analysis, orchestration, rendering, and execution
- deterministic output for stable CI and tests
- extension points through typed protocols, not dynamic runtime frameworks

## Package Layout

`src/ai_container_intelligence/`

- `analysis/`
  - pure analysis logic
  - current concrete implementation: Dockerfile review
- `integrations/`
  - protocol interfaces and noop providers
  - reserved for adapter implementations later
- `models/`
  - shared typed contracts (`Finding`, `AnalysisReport`, etc.)
  - canonical normalization point for output shape
- `reporting/`
  - markdown rendering only
- `cli/`
  - input validation + argument handling + exit code mapping
  - delegates to pipeline, no business logic
- `pipeline.py`
  - orchestration layer
  - gathers analysis results and renders final report

## Runtime Flow

1. CLI validates input arguments and paths.
2. Pipeline runs Dockerfile analysis.
3. Pipeline optionally invokes provider interfaces when inputs are present.
4. Findings are normalized and ordered deterministically.
5. Markdown report is rendered.
6. CLI writes output to stdout or file.

## GitHub Actions Integration

Workflow file:
- `.github/workflows/pr-container-intelligence.yml`

Integration model:
- workflow calls `aci` directly
- no duplicated analysis logic in YAML
- changed Dockerfiles are discovered with `git diff`
- reports are uploaded as artifacts

## Version 1 Boundaries

Intentionally excluded:
- database persistence
- API/service layer
- web UI
- Kubernetes-native automation
- dynamic plugin loading
- release publishing automation

These are excluded to keep v1 small, testable, and maintainable.

## Extension Points (Without Premature Expansion)

Use only when there is a concrete need:

1. `integrations/*_provider.py`
   - add real adapters behind existing protocols
   - keep pipeline contract stable
2. `analysis/`
   - add new rules in focused modules
   - avoid duplicate checks across files
3. `reporting/`
   - add additional output renderer only after a proven consumer exists
4. CLI options
   - add arguments only when supported end-to-end by tests and workflow

Extension should follow existing contracts first, then add new contracts only if
current ones are insufficient.
