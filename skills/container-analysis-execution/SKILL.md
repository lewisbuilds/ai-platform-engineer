---
name: container-analysis-execution
description: Run consistent local container analysis for this repository. Use when asked to review Dockerfiles, run container findings, generate markdown reports, validate CLI behavior, or troubleshoot analysis results from `aci`.
license: Complete terms in LICENSE.txt
---

# Container Analysis Execution

This skill standardizes how container analysis is executed in AI Container Intelligence v1.

## When to Use This Skill

- Review a Dockerfile and generate findings.
- Run local analysis and save markdown report output.
- Validate CLI behavior and exit-code handling.
- Reproduce a reported container analysis issue.

## Prerequisites

- Python 3.10+
- Project installed locally (`pip install -e .`)
- Dockerfile path available

## Standard Workflow

Follow [workflow.md](./references/workflow.md).

## Commands

Run analysis to stdout:

```bash
aci --dockerfile examples/dockerfiles/minimal-secure.Dockerfile
```

Run analysis and write report:

```bash
aci --dockerfile examples/dockerfiles/minimal-secure.Dockerfile --output examples/reports/sample-pr-report.md
```

Run targeted validation tests:

```bash
pytest tests/unit/test_dockerfile_review.py tests/unit/test_pipeline.py tests/integration/test_cli_local.py
```
