# Skill Profiles

This directory is the first profile layer for the larger skill-matrix design.
It does not replace `skills/`; it describes which skills belong together for a
project type and which parts should later move into separate skill-pack repos.

## Why Profiles Exist

The repository started as one ML research lifecycle bundle. That is still a
valid domain pack, but the broader system should support many project types:
paper reading, ML research, research distillation, automation, and future
personal or professional domains. A project should declare a profile first, and
the agent should load the relevant pack instead of searching a flat global list.

Profiles make three boundaries explicit:

- **Install boundary**: what may be global, what must be project-local, and what
  is maintainer/debug-only.
- **Routing boundary**: which router or entry skill owns the project type.
- **Extraction boundary**: which skills are likely candidates for a future
  repo, such as `core-ops-skills` or `automation-skills`.

## Files

- `profile-index.yaml` is the canonical profile registry for this repo.
- `../schemas/skill-kernel/` defines the minimum portable kernel schema for
  profile identity, routing, lane contracts, validation, memory, adapters, and
  promotion gates before repo extraction; current examples cover `core-ops`,
  `paper-reading`, and `research-distillation`.
- `research-distillation/` contains the first profile-local artifact loop:
  distillation-run, pattern-card, and skill-proposal templates plus examples,
  including UI-TARS and Tongyi DeepResearch public-source trials and a combined
  agent workflow contract proposal with template and lane-routing fixtures.
- `../docs/design/skill-matrix.md` explains the broader multi-repo Skill OS
  direction and migration order.
- `../tests/profile-routing-evals.json` records profile-selection regression
  examples before leaf-skill routing starts.
- `../scripts/score_profile_routing.py` scores actual runtime/agent profile
  predictions against those evals and can generate blank or gold prediction
  files.
- `../schemas/skill-kernel/runtime-adapter-contracts.json` records the observed
  Codex/Claude dry-run adapter surface.
- `../schemas/skill-kernel/runtime-trigger-capture-2026-05-27.json` records the
  first Codex/Claude prompt-surface capture for preview skill roots.
- `../schemas/skill-kernel/core-ops-runtime-semantics-2026-05-27.json` records
  the follow-up Codex routing capture that resolves `core-ops` as a
  profile-first entrypoint with full-root delegation to mature owner skills.
- `../schemas/skill-kernel/manifest-exercise-runtime-capture-2026-05-27.json`
  records Codex/Claude prompt-surface capture from session-only
  manifest-exercised roots.
- `../schemas/skill-kernel/install-handoff-contract-2026-05-27.json` records
  the reviewed install/repo-split boundary before any real runtime write or
  destination-repo scaffold is allowed.
- `../schemas/skill-kernel/install-plan.schema.json` and
  `../scripts/validate_install_handoff_plan.py` define and check reviewed
  install/repo-split plans without writing runtime files.
- `../scripts/export_skill_kernel_adapters.py --preview-skill-root ...` writes
  temporary runtime-like `SKILL.md` fixtures from those adapter projections and
  smoke-checks them without making them installable.
- `../scripts/export_skill_kernel_adapters.py --installable-manifest-root ...`
  writes review-gated prototype installable manifests that preserve kernel
  source truth and require manual review before any real runtime install.
- `../scripts/export_skill_kernel_adapters.py --exercise-skill-root ...`
  exercises those manifests into a temporary session-only skill root without
  modifying global installs.
- `scripts/validate_skill_taxonomy.py` checks that profile skill references
  point to real skills, profile schema fields are valid, and profile eval
  targets reference real profiles and entrypoint skills.

## Current Status

The active production profile is still `ml-research`. The other profiles are
drafts that identify reusable subsets already present in this repo and guide
future extraction into a multi-repo skill matrix.

## Design Rules

- Keep profile names lowercase and hyphenated.
- Keep every skill reference real; use `gaps` for capabilities that do not exist
  yet instead of naming future skills as if they were implemented.
- Register profile-local docs, templates, and examples under `artifacts` in
  `profile-index.yaml`; keep those files under `profiles/<profile-name>/`.
- Keep `entrypoints`, `routers`, `skills.required`, `skills.optional`, and
  `install_policy` schema-valid; run `uv run scripts/validate_skill_taxonomy.py`
  after every profile edit.
- Use profile membership to make install and routing decisions; do not rely on a
  giant global skill list.
- Use `python3 scripts/score_profile_routing.py --write-template <path>` to
  capture actual runtime choices, then score them with
  `--predictions <path>`.
- Treat agent-specific metadata as an adapter layer. Markdown instructions,
  profile YAML, JSON schemas, templates, scripts, validators, and routing evals are the
  portable source of truth.
- Treat filled profile-local trials as promotion gates. A useful template should
  not become a standalone skill until real tasks show ownership that mature
  routers and skills cannot already cover.
- Use `schemas/skill-kernel/skill-kernel.schema.json` before splitting a
  profile into a separate repo or runtime-specific adapter.
- Keep `schemas/skill-kernel/runtime-adapter-contracts.json` aligned with
  observed runtime install surfaces; do not turn dry-run adapter output into the
  workflow source of truth.
- Use preview skill roots to test generated `SKILL.md` shape before any
  real runtime install or repo split.
- Use installable manifest prototypes to inspect runtime install targets and
  review gates; do not treat them as automatic installers.
- Use session-only manifest exercises before any real install automation; the
  exercise summary must record `global_install_modified: false`.
- Treat manifest-exercised runtime capture as the gate before real install
  automation or repo split scaffolding.
- Treat the install handoff contract as the next gate after capture: real
  installers and repo splits remain disabled until a reviewed plan names target
  root, profile, runtime, source truth, validation, privacy audit, and rollback.
- Run the non-mutating install-plan validator on any candidate install or
  repo-split plan before adding a command that writes runtime files or scaffolds
  a destination repo.
- Treat `core-ops` as a profile-first entrypoint: it should be selected in
  isolated/profile-first installs, and may intentionally delegate to mature
  leaf/router skills when the full shared skill root is visible.
