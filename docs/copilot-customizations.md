# Copilot Customizations (v2)

This repository includes a minimal set of GitHub Copilot customization assets.

## Goals

- keep review behavior consistent for Docker-related changes
- encode repo standards once and reuse them
- provide one repeatable execution skill for container analysis
- avoid overlapping agents and ceremonial assets

## Assets in This Repository

### Agent

File:
- `agents/container-review.agent.md`

Purpose:
- specialized review mode for Docker and container-analysis changes
- directs checks to relevant paths only
- enforces severity-ordered findings and targeted test execution

Why only one agent:
- avoids overlapping responsibility
- keeps maintenance overhead low

### Instruction

File:
- `instructions/container-engineering-standards.instructions.md`

Purpose:
- repository-wide rules for v2 boundaries and implementation standards
- defines required validation commands
- enforces deterministic and maintainable container analysis patterns

### Skill

Files:
- `skills/container-analysis/SKILL.md`
- `skills/container-analysis-execution/SKILL.md`
- `skills/container-analysis-execution/references/workflow.md`

Purpose:
- preserves a stable compatibility skill path (`container-analysis`)
- standardizes local analysis execution with `container-analysis-execution`
- gives a stable command sequence for contributors and agent usage

## Plugin Files in v2

Current state:
- no plugin bundle files are active in the repository for v2

Rationale:
- v2 does not implement dynamic plugin loading
- introducing plugin bundles now would create maintenance overhead without runtime value

When to add plugin files later:
- only after a concrete integration requires a checked-in, executable plugin contract
- only if tests and workflow consume that contract end-to-end

## Maintenance Rules

- keep asset names specific and responsibility-focused
- avoid duplicate behavior between agent and skill
- keep instructions scoped to standards, not implementation details
- update docs when customization behavior changes
