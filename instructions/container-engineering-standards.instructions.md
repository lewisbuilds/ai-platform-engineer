---
description: 'Repository-wide container engineering standards for AI Container Intelligence v1.'
applyTo: '**/*'
---

# Container Engineering Standards (v1)

These standards apply to all work in this repository.

## Scope Boundaries

- Keep v1 local-first and deterministic.
- Keep one package architecture under `src/ai_container_intelligence/`.
- Do not add non-v1 scope:
  - no database
  - no web UI
  - no Kubernetes logic
  - no dynamic plugin loader
  - no remote registry fetch pipeline

## Container Review Standards

- Dockerfile findings must be deterministic and normalized through model types in `models/`.
- Avoid duplicate checks across modules; one rule should exist in one place.
- Keep parsing/review logic in `analysis/` and orchestration in `pipeline.py`.
- Keep integrations behind protocol boundaries in `integrations/`.
- Keep reporting formatting centralized in `reporting/markdown_report.py`.
- Keep CLI thin: parse/validate inputs, call pipeline, map errors to exit codes.

## Required Validation

When container-related behavior changes, run:

```bash
pytest tests/unit/test_dockerfile_review.py tests/unit/test_pipeline.py tests/integration/test_cli_local.py
```

When model contracts change, also run:

```bash
pytest
```

## Safety and Security

- Never hardcode secrets, tokens, credentials, or private endpoints.
- Treat Dockerfile content and file input paths as untrusted input.
- Prefer secure defaults (least privilege, pinned base image guidance, non-root runtime guidance).
- Do not suppress or hide critical or high-severity findings.

## Docker Build Standards

- Use multi-stage builds for all production Dockerfiles.
- Use explicit, pinned base image tags (do not use `latest`).
- Order layers to maximize cache reuse (dependency install before source copy where possible).
- Combine package manager operations and cleanup in the same layer to avoid leftover cache files.
- Use a `.dockerignore` file to keep build context minimal and prevent leaking local artifacts.
- Copy only required runtime artifacts into the final stage.
- Run containers with a non-root user whenever runtime requirements allow it.
- Use exec-form `CMD`/`ENTRYPOINT` for correct signal handling.
- Use environment variables for runtime configuration; never bake secrets into images.
- Add `HEALTHCHECK` for long-running services when an in-container health probe is available.

### Runtime Base Image Policy

- The final runtime stage must use the smallest secure base that is appropriate for the runtime.
- `FROM scratch` is preferred when the workload is a statically linked binary.
- For interpreted runtimes (for example Python), use a pinned minimal runtime base (for example `python:<version>-slim`) instead of `latest`.
- Runtime base choices must preserve least-privilege execution and reproducibility requirements.

## Output Quality

- Findings must include actionable remediation guidance.
- Output ordering must be stable across runs.
- Changes must preserve typed interfaces and unit-test coverage.
