# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Repository Purpose

**skill-os** — the framework / hub of the portable agent **Skill OS** matrix
for AI research workflows. Owns kernel schema, install/repo-split handoff
contract, installer + scaffolder + chain installer + validators, and the
matrix registry. Pack repos own the actual skills:

- [core-ops-skills](https://github.com/a-green-hand-jack/core-ops-skills) — 12 skills, shared substrate
- [automation-skills](https://github.com/a-green-hand-jack/automation-skills) — 6 skills, depends_on core-ops
- [paper-reading-skills](https://github.com/a-green-hand-jack/paper-reading-skills) — 11 skills, depends_on core-ops
- [research-distillation-skills](https://github.com/a-green-hand-jack/research-distillation-skills) — 13 skills, depends_on core-ops
- [quick-experiment-skills](https://github.com/a-green-hand-jack/quick-experiment-skills) — 9 skills, depends_on core-ops + automation
- [ml-research-skills](https://github.com/a-green-hand-jack/ml-research-skills) — 46 skills (after 2026-05-28 hard-slim), depends_on all five above

The matrix is deployed: 7 GitHub repos under `a-green-hand-jack/*` (this one
plus the 6 packs). Skill OS Phase B2 is complete as of 2026-05-28 — hub
migration (ACT-079), synthetic-fixture test refactor (ACT-080), chain
installer (ACT-081), cross-repo validator (ACT-082), and the hard-slim of
ml-research-skills (ACT-083) all done.

## Testing Changes

Run the full skill-os test suite:

```bash
python3 -m unittest discover tests
```

69 tests across 11 files. Coverage:

- `test_skill_kernel_adapter_export.py` (16) — kernel → adapter dry-run
- `test_profile_routing_harness.py` (6) — profile-routing eval fixtures
- `test_resolve_profile_dependencies.py` (8) — depends_on resolver + router metadata
- `test_synthetic_install_chain.py` (7) — single-profile install chain on synthetic fixture
- `test_synthetic_repo_split_chain.py` (2) — repo-split chain on synthetic fixture
- `test_synthetic_cross_repo_install.py` (5) — cross-repo install via --source-root
- `test_synthetic_chain_install.py` (6) — multi-profile chain installer + leaf staging + dedup
- `test_routing_evals.py` (7) — matrix-wide leaf-routing eval regression (`tests/routing-evals.json`)
- `test_verify_pack_pins.py` (4) — sibling-pack commit pin verifier
- `test_taxonomy_matrix_aware.py` (4) — `--pack-search-path` / `--pack` flag handling
- `test_validate_matrix.py` (4) — full matrix validation wrapper and pack override normalization

Dry-run adapter export must always pass:

```bash
python3 scripts/export_skill_kernel_adapters.py --runtime all --check
```

Deep taxonomy + profile + kernel schema consistency:

```bash
uv run scripts/validate_skill_taxonomy.py --pack-search-path <parent-of-cloned-packs>
```

One-command matrix validation across the hub plus sibling packs:

```bash
python3 scripts/validate_matrix.py --pack-search-path <parent-of-cloned-packs>
```

Skill sanity (validates `SKILL.md` frontmatter — there are no skills in
this repo, so this passes trivially):

```bash
python3 scripts/validate_skills.py
```

## Operating The Installer And Scaffolder

`scripts/apply_install_plan.py` and `scripts/apply_repo_split.py` execute
reviewed install plans against the active 2026-05-28 contract
(`reviewed-execute-enabled`). They:

- Refuse known global skill roots regardless of contract state
- Refuse to write until `--execute` is passed
- Refuse to write unless `automation_policy.real_installer_authorized:
  true` AND the plan's mode is `allowed_now: true`
- Emit a rollback record artifact when `--rollback-record <path>` is set
- Accept `--source-root <pack-path>` (or `SKILL_OS_SOURCE_ROOT` env) for
  cross-repo installs from a sibling pack

For multi-profile installs use the chain installer:

```bash
python3 scripts/install_profile_chain.py <profile> \
  --target-parent <project>/.agents/skills \
  --pack-search-path <parent-of-cloned-packs> \
  --execute
```

The chain installer resolves the profile's `depends_on` chain via
`scripts/resolve_profile_dependencies.py` and runs `apply_install_plan.py`
per step in dependency-first order. Each step gets its own
`plan-<profile>.json`, manifest index, and rollback record under
`<target-parent>/.skill-os-install-state/`.

### Two-layer install layout

After a successful `--execute` chain install of profile `P` with `depends_on
[Q, R, ...]`, the target directory contains:

- **One profile-level adapter per pack**: `<target-parent>/<pack-profile>/SKILL.md`
  (e.g. `core-ops/SKILL.md`, `automation/SKILL.md`, ..., `ml-research/SKILL.md`).
  Generated from each pack's kernel example; describes the profile.
- **One flat leaf-skill dir per unique skill**: `<target-parent>/<skill-name>/SKILL.md`
  + bundled assets (`references/`, `scripts/`, `templates/`, etc.). Matches the
  runtime convention (Codex / Claude Code read `<root>/<name>/SKILL.md`).

Cross-pack dedup uses **first-wins by `depends_on` order**: foundational
packs (`core-ops`) get their `research-project-memory` honored over the same
name in `automation`, `paper-reading`, etc. The reporting JSON includes
`leaf_skills_staged_unique`, `leaf_skills_unique_count`, and per-step
`leaf_skills.staged` / `leaf_skills.skipped_dedup` for audit.

Use `--no-leaf-skills` to keep only the profile-level adapters (kernel-only
mode; runtime sees 6 profiles, not 74 leaves).

## Sibling Pack Pin Verification

Each pack in `profiles/profile-index.yaml` `repo_matrix` carries a
`pinned_commit` + `pinned_at`. Verify the local clones match before running a
reproducible install:

```bash
python3 scripts/verify_pack_pins.py --pack-search-path <parent-of-cloned-packs>
```

Use `--pack <name>=<path>` to override the path for one pack (e.g. when the
local checkout lives under a different name). The script is read-only — it
never checks out the pinned commit. Exit code is non-zero on any mismatch or
missing pack.

For a full cross-repo check, prefer:

```bash
python3 scripts/validate_matrix.py --pack-search-path <parent-of-cloned-packs>
```

It runs unit tests, adapter export, matrix-aware taxonomy validation, and pack
pin verification with one shared pack-discovery configuration. It is also
read-only and accepts `--pack <profile-or-repo>=<path>` overrides.

Update pins with the helper one-liner after a sibling-pack commit lands:

```bash
# inspect current HEADs
for r in core-ops-skills automation-skills paper-reading-skills \
         research-distillation-skills quick-experiment-skills ml-research-skills; do
  echo "$r: $(git -C <parent>/$r log -1 --format=%H)"
done
# then edit profile-index.yaml repo_matrix.<name>.pinned_commit
```

## Memory

Project memory (`memory/BRIEFING.md`, `memory/decision-log.md`, etc.) tracks
the OS-evolution history and current skill-os state. Always start a session
by reading `memory/BRIEFING.md`. OS-level decisions belong here; pack-specific
work belongs in the pack's own memory.

## Source-of-truth rules

- **Kernel schema** is authoritative here (`schemas/skill-kernel/skill-kernel.schema.json`).
- **Active + frozen handoff contracts** are authoritative here.
- **Matrix profile-index** (`profiles/profile-index.yaml`) is authoritative here.
- **Skill files** (`SKILL.md` and bundled resources) are authoritative in the
  pack repos.
- The kernel examples under `schemas/skill-kernel/examples/` are reference
  copies; the authoritative kernel for a profile lives inside that profile's
  pack repo.

## Empty `skills/`

`skills/.gitkeep` exists because the active handoff contract lists `skills`
as an authoritative source path. skill-os does not own skill files; pack
repos do. The placeholder is so the validator's path-existence check
resolves without complaint when running from inside skill-os.

## Git closeout

Use `git push` directly here. No `project-push` wrapper in skill-os — that
wrapper lives in core-ops-skills as a user-level installable script.

## Adding a New Pack Repo To The Matrix

1. Build the new pack's kernel example, profile-index slice, and skill files.
2. Add the new profile entry to `profiles/profile-index.yaml` here (full
   matrix registry).
3. Add a copy of the kernel example under `schemas/skill-kernel/examples/` (reference).
4. Generate inventory + privacy audit + plan fixtures under
   `schemas/skill-kernel/repo-split/` and `schemas/skill-kernel/examples/install-plans/`.
5. Run validators + tests; commit + push.
6. Push the new pack repo to GitHub.
7. Update README.md + this file's matrix table.
