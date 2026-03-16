# Development Guide (v1)

## Setup

Requirements:
- Python 3.10+

Install and verify:

```bash
python -m pip install -e .
pytest
```

## Local CLI Usage

Show options:

```bash
aci --help
```

Run against sample Dockerfile:

```bash
aci --dockerfile examples/dockerfiles/minimal-secure.Dockerfile
```

Write report to file:

```bash
aci --dockerfile examples/dockerfiles/minimal-secure.Dockerfile --output examples/reports/sample-pr-report.md
```

Current CLI contract:
- required input: `--dockerfile`
- optional input: `--image-tar`
- output format: `markdown` (v1)
- output destination: stdout or `--output <file>`

## Testing

Run all tests:

```bash
pytest
```

Targeted tests for container logic:

```bash
pytest tests/unit/test_dockerfile_review.py tests/unit/test_pipeline.py tests/integration/test_cli_local.py
```

## Security Checks

Run static security scan locally:

```bash
python -m pip install bandit
bandit -q -r src/ai_container_intelligence
```

Enable the managed pre-commit hook for local commits:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
```

The hook runs:
- Bandit scan for `src/ai_container_intelligence`
- Secret-pattern scan on staged files

## Dockerfile Linting

Run hadolint locally with the same config used in CI:

```bash
docker run --rm -i -v "$PWD/.hadolint.yaml:/work/.hadolint.yaml:ro" hadolint/hadolint --config /work/.hadolint.yaml - < examples/dockerfiles/minimal-secure.Dockerfile
```

## GitHub Actions Behavior

Workflow:
- `.github/workflows/pr-container-intelligence.yml`

What it does:
1. triggers for pull requests touching Dockerfiles or relevant analysis code
2. installs Python and project dependencies
3. runs security checks (Bandit + secret-pattern guard)
4. runs test suite
5. executes `aci` for changed Dockerfiles
6. uploads markdown reports as artifacts
7. posts analyzed file list to run summary

If no Dockerfile changed, workflow analyzes:
- `examples/dockerfiles/minimal-secure.Dockerfile`

## Contribution Rules for v1

- Keep CLI thin; do not move business logic into workflow YAML.
- Keep deterministic ordering of findings.
- Keep model contracts stable unless required by concrete behavior.
- Prefer adding tests with each behavior change.
- Avoid adding new systems (DB/UI/k8s) in v1.

## Practical Extension Guidance

Allowed with justification:
- implement one real integration adapter behind existing protocol
- add one focused Dockerfile rule with tests
- improve report clarity while preserving deterministic output

Do not add by default:
- plugin runtime framework
- multiple CI workflows for same purpose
- release or publish automation
