# AGENTS.md

Agent-neutral guidance for working with this repository (Codex CLI, Claude
Code, Cursor, future agents). Full guidance is in [CLAUDE.md](CLAUDE.md);
key points below.

## Repository Purpose

**skill-os** is the framework / hub of the [Skill OS matrix](https://github.com/a-green-hand-jack/skill-os).
Pack repos own skills; skill-os owns the rules:

- Kernel schema, install/repo-split handoff contracts, install-plan schema,
  write-actions schema, repo-split inventory + privacy-audit schemas
- Hub scripts: validator, exporter, installer (`apply_install_plan.py`),
  scaffolder (`apply_repo_split.py`), chain installer
  (`install_profile_chain.py`), resolver (`resolve_profile_dependencies.py`),
  inventory generator, preview tools
- Matrix registry (`profiles/profile-index.yaml`) with `github_url` +
  `depends_on` for every pack
- Reference kernel examples + plan fixtures + repo-split inventories

## What This Repo Does NOT Have

- Skill files (`SKILL.md`) — they live in the 6 pack repos
- `skills/` content (only an empty `.gitkeep`)
- A `project-push` wrapper — that lives in `core-ops-skills`
- A `validate_skill_taxonomy` run against a real `skills/` tree — runs
  trivially since there's nothing here

## Active Contract Status

- Active contract: `schemas/skill-kernel/install-handoff-contract-2026-05-28.json`
- `implementation_status: reviewed-execute-enabled`
- `automation_policy.real_installer_authorized: true`
- `may_write_runtime_files_without_review: false` (must stay false)
- `may_write_global_roots_without_explicit_user_request: false` (must stay false)
- Modes `project-local-profile-install` + `repo-split-handoff` are
  `allowed_now: true`
- Modes `global-bootstrap-install` + `maintainer-debug-global-install` are
  `allowed_now: false` (require explicit per-invocation user request)
- Frozen pre-revision `2026-05-27.json` preserved for refusal regression

## Working In This Repo

Tests + validators that must always pass:

```bash
python3 -m unittest discover tests
python3 scripts/export_skill_kernel_adapters.py --runtime all --check
uv run scripts/validate_skill_taxonomy.py
```

54 tests across 8 files. The synthetic-fixture pack under
`tests/fixtures/synthetic-pack/` (and a depends_on variant under
`tests/fixtures/synthetic-pack-pdf/`) lets the operational tests run
without depending on any real pack repo. The matrix-wide leaf-routing
regression fixture is `tests/routing-evals.json` with
`tests/test_routing_evals.py` enforcing structural well-formedness.

## Operating The Installer For Real Projects

```bash
# Install one profile's chain into a project folder
python3 scripts/install_profile_chain.py <profile> \
  --target-parent <project>/.agents/skills \
  --pack-search-path <parent-of-cloned-packs> \
  --execute
```

The chain installer resolves `depends_on` recursively and runs
`apply_install_plan.py` per step. Each step has its own plan + rollback
record under `<target-parent>/.skill-os-install-state/`.

Direct single-profile install (skip the chain):

```bash
python3 scripts/apply_install_plan.py <plan>.json \
  --manifest-index <index>.json \
  --source-root <pack-path> \
  --rollback-record <rollback-path>.json \
  --execute
```

Cross-repo support via `--source-root` (or `SKILL_OS_SOURCE_ROOT` env var):
the validator and applier resolve `kernel_source_paths` and
`source_of_truth_paths` against both `REPO_ROOT` (here) and `source_root`
(the sibling pack), so plan files that reference paths in either repo work.

## Hard Rules

1. Never set `may_write_runtime_files_without_review` or
   `may_write_global_roots_without_explicit_user_request` to `true` in the
   active contract.
2. Never write to `~/.codex/skills`, `~/.agents/skills`, or
   `~/.claude/skills` from any installer in this repo.
3. Kernel schema, contract, and profile-index changes must update the
   matching tests + validator outputs in the same commit.
4. Pack-specific changes belong in the pack repo, not here.
