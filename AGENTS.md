# AGENTS.md

This file provides guidance to agent-neutral runtimes (Codex CLI, Claude Code,
Cursor, future agents) when working with code in this repository.

For the full guidance see [CLAUDE.md](CLAUDE.md). Key points:

- **skill-os** is the framework / hub. Skills live in per-profile pack repos
  (see README.md for the matrix).
- The active install/repo-split handoff contract is
  `schemas/skill-kernel/install-handoff-contract-2026-05-28.json`. It is
  `reviewed-execute-enabled` — the real installer and scaffolder can write
  reviewed plans to a project-local target, but global skill roots remain
  blocked and require `--execute`.
- Kernel schema, contract, plan schema, and write-actions schema are
  authoritative here. Skill files are authoritative in pack repos.
- Phase B1 (current): kernel infrastructure migrated; skill-dependent tests
  remain in `ml-research-skills`. Phase B2 (future): synthetic-fixture tests
  + slim `ml-research-skills`.

## Working in this repo

- Dry-run adapter export and the schema-independent tests must always pass:
  ```
  python3 scripts/export_skill_kernel_adapters.py --runtime all --check
  python3 -m unittest -v tests.test_skill_kernel_adapter_export tests.test_profile_routing_harness
  ```
- Do not commit anything that would let an installer touch global skill roots
  by default. The two dangerous switches in the contract
  (`may_write_runtime_files_without_review`,
  `may_write_global_roots_without_explicit_user_request`) must always be
  false.
