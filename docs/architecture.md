# Architecture (v2)

## Design Goals
- simplicity: minimum moving parts for policy analysis,
- minimal architecture: one execution path, one policy decision layer,
- explainable design: each layer has one clear responsibility.

## System Shape

```text
CLI (thin)
  -> Pipeline orchestrator
      -> Analysis + Providers (isolated)
          -> Policy evaluation layer
              -> Reporting layer
```

## Thin CLI
Location: [src/ai_container_intelligence/cli/main.py](src/ai_container_intelligence/cli/main.py)

Responsibilities:
- parse and validate arguments,
- call pipeline entrypoint,
- map policy gate outcomes to exit codes.

Non-responsibilities:
- no rule evaluation logic,
- no provider business logic,
- no report formatting logic.

Why this matters:
- command surface stays stable,
- tests for orchestration and policy remain focused,
- CI and local execution stay consistent.

## Pipeline Orchestrator
Location: [src/ai_container_intelligence/pipeline.py](src/ai_container_intelligence/pipeline.py)

Responsibilities:
- execute analysis flow for one or more Dockerfiles,
- select provider implementations by profile,
- collect and normalize findings,
- invoke policy evaluator,
- pass evaluated findings to report renderer.

The orchestrator is the only place where layer composition happens.

## Provider Isolation
Location: [src/ai_container_intelligence/integrations](src/ai_container_intelligence/integrations)

Pattern:
- typed provider interfaces,
- concrete adapters for `real` and `noop` profiles,
- no provider-specific behavior leaked into CLI.

Why isolation exists:
- deterministic tests can use noop providers,
- runtime adapters can evolve without changing pipeline contract,
- integration complexity stays outside policy and reporting layers.

## Policy Evaluation Layer
Location: [src/ai_container_intelligence/policy/evaluator.py](src/ai_container_intelligence/policy/evaluator.py)

Responsibilities:
- convert raw findings into policy outcomes,
- apply selected profile (`strict|relaxed`),
- classify findings as advisory or blocking,
- generate policy summary used by CLI and reports.

Design rule:
- policy decisions are centralized; no duplicate policy logic in CLI, workflow, or renderer.

## Reporting Layer
Location: [src/ai_container_intelligence/reporting/markdown_report.py](src/ai_container_intelligence/reporting/markdown_report.py)

Responsibilities:
- render deterministic markdown,
- show policy outcome summary (PASS/WARN/FAIL),
- group findings by blocking/advisory disposition,
- present evidence and remediation text consistently.

Non-responsibility:
- no policy decision making.

## Governance Testing Strategy
Governance tests protect architecture and detection quality, not only feature behavior.

Key enforcement areas:
- repository compliance boundaries (thin CLI, allowed package imports, workflow minimality),
- corpus governance (fixture quality and representativeness),
- rule-to-evidence linkage (every implemented rule appears in corpus expected findings),
- parser fidelity governance (metric threshold + explicit blind-spot tracking).

Core files:
- [tests/unit/test_repository_compliance.py](tests/unit/test_repository_compliance.py)
- [tests/unit/test_detection_corpus_governance.py](tests/unit/test_detection_corpus_governance.py)
- [tests/unit/test_parser_accuracy_metric.py](tests/unit/test_parser_accuracy_metric.py)
- [tests/unit/test_detection_known_blind_spots.py](tests/unit/test_detection_known_blind_spots.py)

## Runtime and CI Consistency
Primary workflow: [.github/workflows/pr-container-intelligence.yml](.github/workflows/pr-container-intelligence.yml)

Workflow model:
1. run parser fidelity checks,
2. run full test suite,
3. analyze changed Dockerfiles,
4. publish report artifacts.

This preserves one explainable path from local command to CI enforcement.
