# Development Guide (v2)

This guide focuses on the engineering workflow for detection quality and policy credibility.

## Setup
Requirements:
- Python 3.10+

Install:
```bash
python -m pip install -e .
```

## 1) Running Parser Fidelity Checks
Run parser governance checks first to catch parsing regressions early.

```bash
pytest tests/unit/test_parser_accuracy_metric.py tests/unit/test_detection_known_blind_spots.py
```

What this verifies:
- parser accuracy metric remains above the enforced threshold,
- known parser blind spots are explicitly tracked,
- parser behavior changes are visible before full-suite noise.

Data source:
- [tests/fixtures/golden/parser_fidelity_cases.json](tests/fixtures/golden/parser_fidelity_cases.json)

## 2) Running Corpus Regression Tests
Run corpus regression to validate detection behavior against curated expected outcomes.

```bash
pytest tests/unit/test_detection_golden_corpus.py tests/unit/test_detection_corpus_governance.py
```

What this verifies:
- expected findings still trigger,
- expected non-findings remain clean,
- corpus remains balanced and realistic.

Core corpus file:
- [tests/fixtures/golden/corpus_cases.json](tests/fixtures/golden/corpus_cases.json)

## 3) Adding New Rules with Required Corpus Evidence
When adding or changing a Dockerfile rule, update code and evidence together.

Required workflow:
1. implement or modify rule logic in [src/ai_container_intelligence/analysis/dockerfile_review.py](src/ai_container_intelligence/analysis/dockerfile_review.py),
2. add at least one expected-finding case in [tests/fixtures/golden/corpus_cases.json](tests/fixtures/golden/corpus_cases.json),
3. add at least one expected non-finding case,
4. run parser fidelity and corpus regression tests,
5. run full suite.

Mandatory guard:
- repository compliance tests enforce that every implemented Dockerfile rule ID is represented in corpus expected findings.

## 4) Parser Fidelity Sprint Contract
Use this contract when sprint scope is parser quality.

Objective:
- improve parser correctness on real-world Dockerfile authoring patterns.

Scope constraints:
- do not expand architecture,
- avoid adding new rules unless parser correctness requires it,
- keep blind-spot tracking explicit.

Acceptance criteria:
- parser fidelity checks pass,
- full suite passes,
- blind-spot count does not increase,
- parser accuracy metric remains enforced in CI,
- any retired blind spot is moved from expected-failure to normal passing coverage.

## Recommended Local Sequence

```text
1) Parser fidelity checks
2) Corpus regression checks
3) Full test suite
4) Local CLI run for changed Dockerfile(s)
```

Commands:
```bash
pytest tests/unit/test_parser_accuracy_metric.py tests/unit/test_detection_known_blind_spots.py
pytest tests/unit/test_detection_golden_corpus.py tests/unit/test_detection_corpus_governance.py
pytest
aci --dockerfile path/to/changed.Dockerfile --fail-on-policy
```

## CI Execution Order
Primary workflow: [.github/workflows/pr-container-intelligence.yml](.github/workflows/pr-container-intelligence.yml)

CI follows this order:
1. parser fidelity checks,
2. full test suite,
3. changed-file analysis and report artifact upload.

This order keeps detection-quality regressions visible and explainable.
