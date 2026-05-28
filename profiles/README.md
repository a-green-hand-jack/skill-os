# Skill OS Profiles (matrix registry)

This directory holds the **authoritative full matrix registry** for the
Skill OS matrix. Pack repos each carry a sliced copy with just their own
profile entry; this one carries them all.

## Files

- `profile-index.yaml` — the full matrix registry. For every profile:
  `status`, `scope`, `future_repo`, `github_url`, `depends_on`,
  `entrypoints`, `routers`, `skills`, `include_all_repo_skills`,
  `install_policy`.

## Matrix as deployed (2026-05-28)

| Profile | Status | Pack repo | depends_on |
|---|---|---|---|
| `core-ops` | active | [core-ops-skills](https://github.com/a-green-hand-jack/core-ops-skills) | — |
| `automation` | active | [automation-skills](https://github.com/a-green-hand-jack/automation-skills) | core-ops |
| `paper-reading` | active | [paper-reading-skills](https://github.com/a-green-hand-jack/paper-reading-skills) | core-ops |
| `research-distillation` | active | [research-distillation-skills](https://github.com/a-green-hand-jack/research-distillation-skills) | core-ops |
| `quick-experiment` | active | [quick-experiment-skills](https://github.com/a-green-hand-jack/quick-experiment-skills) | core-ops + automation |
| `ml-research` | active | [ml-research-skills](https://github.com/a-green-hand-jack/ml-research-skills) | all 5 above |
| `global-bootstrap` | active | (inside ml-research-skills) | — |

`repo_matrix` at the top of `profile-index.yaml` lists each pack repo with
its `github_url` and current role.

## How to read the graph

Profiles should be selected before individual skills. The expected routing
shape is:

```text
project scenario -> profile -> router / entrypoint -> leaf skill
```

Typical examples:

| Scenario | Profile | Router / entrypoint |
|---|---|---|
| Generic project memory, git, docs, sidecars | `core-ops` | `project-ops-router` |
| Remote jobs, clusters, runbooks, scheduler probes | `automation` | `project-ops-router` |
| Paper reading, source cards, literature comparison | `paper-reading` | `discovery-router` |
| Distilling reusable practices from papers, repos, or agent sessions | `research-distillation` | `discovery-router` |
| Scratch experiments, reproduction runs, debug sessions | `quick-experiment` | `experiment-evidence-router` |
| Paper-grade ML research from idea through release | `ml-research` | `ml-research-router`, `paper-writing-router` |

Use the smallest profile that fits the project. Promote from
`quick-experiment` to `ml-research` when an experiment starts carrying
paper-grade claims, evidence boards, writing, review, rebuttal, or artifact
release requirements.

See `../docs/usage/profile-selection-guide.md` for the full scenario map.

## Why profiles exist

Three boundaries:

- **Install boundary** — what may be global, what must be project-local,
  what is maintainer/debug-only
- **Routing boundary** — which router or entry skill owns the project type
- **Dependency boundary** — `depends_on` declares which sibling packs must
  be installed alongside; the chain installer
  (`scripts/install_profile_chain.py`) resolves it automatically

## Editing rules

- Edit profile entries HERE first; sliced copies in pack repos are
  derived. After editing here, regenerate the sliced copy in the affected
  pack via the repo-split scaffolder OR by hand.
- Keep profile names lowercase and hyphenated.
- Every skill reference must be real; use `gaps` for capabilities that
  don't yet exist.
- After any profile edit run:
  ```bash
  python3 scripts/validate_matrix.py --pack-search-path <parent-of-cloned-packs>
  uv run scripts/validate_skill_taxonomy.py --pack-search-path <parent-of-cloned-packs>
  python3 -m unittest discover tests
  ```

## Sliced profile-index in each pack

Each sibling pack repo carries a `profiles/profile-index.yaml` containing
only its own profile entry. Examples:

- `core-ops-skills/profiles/profile-index.yaml` — just the `core-ops` entry
- `ml-research-skills/profiles/profile-index.yaml` — just the `ml-research`
  entry (with `depends_on: [core-ops, automation, paper-reading,
  research-distillation, quick-experiment]`)

The sliced copies are derived artifacts. Edit the full registry here,
then re-slice. The repo-split scaffolder writes the slice automatically
when scaffolding a pack repo from this hub.

## Design rules (still valid)

- Treat agent-specific metadata as an adapter layer. Markdown / YAML /
  JSON schemas, templates, scripts, validators, and routing evals are the
  portable source of truth.
- Use `schemas/skill-kernel/skill-kernel.schema.json` before adding a new
  profile or splitting a pack into a separate repo.
- Keep `schemas/skill-kernel/runtime-adapter-contracts.json` aligned with
  observed runtime install surfaces; do not turn dry-run adapter output
  into the workflow source of truth.
- Treat the install handoff contract as the gate before any real install
  or repo split. The active 2026-05-28 contract is
  `reviewed-execute-enabled`; the 2026-05-27 frozen version is preserved
  for refusal regression.
- Treat `core-ops` as the substrate every other profile depends on.
  `automation`, `paper-reading`, `research-distillation`, and
  `quick-experiment` all declare `depends_on: [core-ops]`.
- Treat `quick-experiment` and `ml-research` as the multi-dependency
  profiles (depend on multiple siblings). The chain installer must
  resolve them dependency-first.
