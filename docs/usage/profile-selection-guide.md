# Profile Selection Guide

Use the smallest profile that matches the project. A profile is selected before
individual skills:

```text
project scenario -> profile -> router / entrypoint -> leaf skill
```

## Quick Decision Tree

```text
Only reading papers, notes, or source bundles?
  -> paper-reading

Reproducing or running a small experiment?
  -> quick-experiment

Managing remote machines, clusters, jobs, storage, or automation runbooks?
  -> automation

Maintaining a generic project with memory, git, docs, validation, or sidecars?
  -> core-ops

Distilling reusable practices from papers, repos, courses, or agent sessions?
  -> research-distillation

Building a paper-grade ML project with claims, evidence, writing, review,
rebuttal, submission, or artifact release?
  -> ml-research
```

## Common Scenarios

| Scenario | Start with | Typical route |
|---|---|---|
| Read one paper | `paper-reading` | `discovery-router` -> `reference-reading-summarizer` |
| Compare a folder of papers | `paper-reading` | `discovery-router` -> `reference-corpus-analyzer` |
| Run a focused literature review | `paper-reading` | `discovery-router` -> `literature-review-sprint` |
| Reproduce a paper's code or experiments | `paper-reading` + `quick-experiment` | understand with `reference-reading-summarizer`; run with `experiment-evidence-router` -> `run-experiment` |
| Debug a training failure | `quick-experiment` | `experiment-evidence-router` -> `experiment-debugger` |
| Estimate GPU cost | `quick-experiment` | `experiment-evidence-router` -> `compute-budget-planner` |
| Check an existing remote job | `automation` | `project-ops-router` -> `run-status-monitor` |
| Coordinate remote project state | `automation` | `project-ops-router` -> `remote-project-control` |
| Maintain project memory and git closeout | `core-ops` | `project-ops-router` -> `research-project-memory` / `safe-git-ops` |
| Turn repeated private lessons into public reusable practice | `research-distillation` | `discovery-router` -> `memory-publication-auditor` / `skill-system-auditor` |
| Validate a new ML research idea | `ml-research` | `ml-research-router` -> `research-idea-validator` |
| Design a method | `ml-research` | `ml-research-router` -> `algorithm-design-planner` |
| Write or revise a paper | `ml-research` | `paper-writing-router` -> `paper-writing-assistant` |
| Prepare rebuttal or camera-ready artifacts | `ml-research` | `ml-research-router` -> `rebuttal-strategist` / `camera-ready-finalizer` |

## Promotion Rules

Start with `quick-experiment` for scratch or reproduction work. Promote to
`ml-research` when the project starts carrying:

- paper-grade claims or contribution framing
- formal evidence tracking or paper tables/figures
- method, experiment, and writing plans that must stay synchronized
- reviewer simulation, rebuttal, submission, camera-ready, or artifact release

Start with `paper-reading` for source intake. Promote to `ml-research` when the
reading directly changes project claims, baselines, paper positioning, or
experiment design.

Start with `research-distillation` only when the goal is reusable practice or
future skill creation. Ordinary literature review belongs in `paper-reading`.

## Install Chains

| Profile | Chain includes |
|---|---|
| `core-ops` | `core-ops` |
| `automation` | `core-ops` + `automation` |
| `paper-reading` | `core-ops` + `paper-reading` |
| `research-distillation` | `core-ops` + `research-distillation` |
| `quick-experiment` | `core-ops` + `automation` + `quick-experiment` |
| `ml-research` | `core-ops` + `automation` + `paper-reading` + `research-distillation` + `quick-experiment` + `ml-research` |
