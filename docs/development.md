# Development Guide (v2)

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
- required input: `--dockerfile` (one or more paths)
- optional input: `--image-tar`
- provider profile: `--provider-profile real|noop` (default `real`)
- policy profile: `--policy-profile strict|relaxed` (default `strict`)
- policy gate: `--fail-on-policy` (returns exit code `3` when blocking findings are present)
- output destination: stdout or `--output <file>`

Analyze multiple Dockerfiles in one run:

```bash
aci --dockerfile path/to/Dockerfile path/to/Dockerfile.prod --output artifacts/reports/combined.md
```

Use relaxed policy profile:

```bash
aci --dockerfile examples/dockerfiles/minimal-secure.Dockerfile --policy-profile relaxed
```

Enable policy gate for CI/local enforcement:

```bash
aci --dockerfile examples/dockerfiles/minimal-secure.Dockerfile --fail-on-policy
```

## Testing

Run all tests:

```bash
pytest
```

Targeted tests for container logic:

```bash
pytest tests/unit/test_dockerfile_review.py tests/unit/test_pipeline.py tests/integration/test_cli_local.py
```

Detection-quality baseline tests (golden corpus + tracked blind spot):

```bash
pytest tests/unit/test_detection_golden_corpus.py tests/unit/test_detection_known_blind_spots.py
```

Notes:
- `test_detection_golden_corpus.py` validates expected and non-expected findings against curated fixture Dockerfiles.
- `test_detection_known_blind_spots.py` tracks parser limitations as expected-failure tests so known gaps stay visible over time.

Current real-world stress cases included in the golden corpus:
- Multi-stage build with non-root runtime user (`realworld-multistage-nonroot.Dockerfile`)
- ARG + FROM pinned base pattern (`realworld-arg-from-pinned.Dockerfile`)
- Multiline RUN chain with apt cleanup (`realworld-multiline-run-cleanup.Dockerfile`, tracked as known parser blind spot via xfail)

Corpus growth discipline:
- For every meaningful rule or parser change, add at least one expected-finding case.
- For every meaningful rule or parser change, add at least one expected non-finding case.
- Add one edge or messy case when the behavior can vary under realistic authoring patterns.
- Keep known gaps visible with explicit expected-failure tests until fixed.

Corpus governance checks:
- `tests/unit/test_detection_corpus_governance.py` enforces balanced fixture types.
- The same governance test ensures the baseline rule surface is still exercised.
- It also verifies the corpus contains both clean and multi-finding samples.

## Parser Fidelity Sprint Contract

Sprint objective:
- Improve whether Dockerfile parsing understands real-world authoring patterns correctly before expanding finding evidence depth.

Scope constraints:
- Do not add new Dockerfile rules unless parser fixes make this strictly necessary.
- Focus on parser correctness, blind-spot retirement, and measurable parser behavior.
- Keep existing architecture boundaries intact (no new top-level source package entries).

Acceptance criteria:
- Full test suite remains green.
- Expected-failure blind-spot count does not increase.
- At least two known parser blind spots are retired from expected-fail to pass.
- Parser accuracy metric is introduced, easy to explain, and enforced in CI.
- No new top-level package boundaries are introduced.

Parser accuracy metric guidance:
- Keep metric simple and transparent.
- Preferred shape: passed parser assertions / total parser assertions.
- Enforce minimum threshold against a documented baseline.
- Parser metric source: `tests/fixtures/golden/parser_fidelity_cases.json`.
- Metric enforcement test: `tests/unit/test_parser_accuracy_metric.py`.

CI order for parser truth signal:
1. Run parser fidelity subset (`test_parser_accuracy_metric.py` + blind-spot tracker).
2. Run full suite.

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
	- if only container policy files changed, it analyzes all tracked Dockerfiles
	- for manual workflow dispatch, it falls back to the sample Dockerfile target
6. uploads markdown reports as artifacts
7. posts analyzed file list to run summary

If no Dockerfile changed:
- PR flow with policy-file changes analyzes all tracked Dockerfiles.
- Manual workflow dispatch analyzes `examples/dockerfiles/minimal-secure.Dockerfile`.

## Contribution Rules for v2

- Keep CLI thin; do not move business logic into workflow YAML.
- Keep deterministic ordering of findings.
- Keep model contracts stable unless required by concrete behavior.
- Keep policy logic centralized in the policy evaluator.
- Prefer adding tests with each behavior change.
- Avoid adding new systems (DB/UI/k8s) in v2.

## Practical Extension Guidance

Allowed with justification:
- implement one real integration adapter behind existing protocol
- add one focused Dockerfile rule with tests
- improve report clarity while preserving deterministic output
- adjust strict/relaxed policy profile behavior with evaluator and test updates

Do not add by default:
- plugin runtime framework
- multiple CI workflows for same purpose
- release or publish automation
