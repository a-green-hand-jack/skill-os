# Skill Kernel Schema

This directory defines the minimum portable schema for the broader skill-matrix
system. It is intentionally smaller than a full skill repository. The kernel
records the contract that must survive when skills move between repos or agent
runtimes.

## Files

- `skill-kernel.schema.json` is the JSON Schema for one portable skill-pack
  kernel.
- `install-handoff-contract.schema.json` defines the reviewed install and
  repo-split handoff contract shape.
- `install-handoff-contract-2026-05-28.json` is the active contract. It
  authorizes the real reviewed-plan installer and repo-split scaffolder for
  `project-local-profile-install` and `repo-split-handoff` modes through
  reviewed plans; `global-bootstrap-install` and
  `maintainer-debug-global-install` remain disabled by default.
- `install-handoff-contract-2026-05-27.json` is the frozen pre-revision
  contract preserved as a refusal regression artifact. It is `status:
  superseded` and is still referenced by tests that exercise the
  refusal-when-not-authorized path.
- `install-plan.schema.json` defines the reviewed install/repo-split plan shape
  consumed by the non-mutating validator.
- `examples/core-ops.kernel.json` instantiates the action/combined-heavy
  cross-project operations profile.
- `examples/paper-reading.kernel.json` instantiates an evidence-heavy
  reading-only profile.
- `examples/research-distillation-workflow-contract.kernel.json` is derived from
  the current `research-distillation` workflow-contract trials.
- `runtime-adapter-contracts.json` records the observed dry-run contract for
  Codex and Claude Code skill directories, plus draft/fallback contracts for
  other runtimes.
- `runtime-trigger-capture-2026-05-27.json` records the first real Codex and
  Claude Code prompt-surface capture from generated preview skill roots.
- `core-ops-runtime-semantics-2026-05-27.json` records the follow-up Codex
  routing capture that resolves `core-ops` as a profile-first entrypoint with
  explicit full-root delegation semantics.
- `manifest-exercise-runtime-capture-2026-05-27.json` records the Codex and
  Claude Code prompt-surface capture from session-only manifest-exercised roots.
- `../../scripts/export_skill_kernel_adapters.py` generates dry-run runtime
  adapter metadata, preview `SKILL.md` fixtures, and review-gated prototype
  installable manifests from the checked examples without making adapter output
  authoritative.
- `../../scripts/validate_install_handoff_plan.py` validates a plan against the
  active handoff contract and generated manifest index without writing runtime
  skill files.

## Minimum Kernel

A valid kernel records:

- identity: schema version, kernel id, owner repo, and source paths
- profile: name, status, scope, intent, and optional future repo
- routing: entrypoints, routers, and handoff policy
- install policy: global vs project-local recommendation and full-bundle gate
- skill membership: required and optional skills
- workflow contract: action/evidence/combined/no-contract lanes
- validation: required checks and acceptance checks
- memory: required reads, writeback targets, and privacy boundary
- adapters: runtime metadata targets without moving source truth into them
  plus selection semantics that distinguish direct entrypoints, profile-first
  entrypoints, substrate/delegators, and schema-only contracts
- promotion: gates and rejection checks before extracting a new skill or repo

## Non-Goals

The kernel is not:

- a replacement for `SKILL.md`
- a runtime-specific manifest
- a private-memory store
- a full JSON representation of every reference document

Runtimes such as Codex or Claude Code should generate thin adapter metadata from
this schema and the underlying Markdown/YAML artifacts.

## Adapter Dry Run

Use the exporter to check whether a kernel can become runtime-shaped metadata
without moving workflow truth into that metadata:

```bash
python3 scripts/export_skill_kernel_adapters.py --runtime codex --check
python3 scripts/export_skill_kernel_adapters.py --runtime all --output-dir /tmp/kernel-adapters
python3 scripts/export_skill_kernel_adapters.py --runtime all --preview-skill-root /tmp/kernel-preview-skills
python3 scripts/export_skill_kernel_adapters.py --runtime all --installable-manifest-root /tmp/kernel-installable-manifests
python3 scripts/export_skill_kernel_adapters.py --runtime all --installable-manifest-root /tmp/kernel-installable-manifests --exercise-skill-root /tmp/kernel-manifest-exercise
```

Generated adapters are marked `dry_run: true`, `installable: false`, and
`source_of_truth: kernel`. Each adapter also includes:

- `runtime_contract`: the observed or draft runtime surface, such as `SKILL.md`
  frontmatter requirements and optional bundled resources
- `runtime_projection`: the preview mapping into a runtime skill directory,
  including the candidate `SKILL.md` frontmatter and docs-only field classes
- `selection_semantics`: how the runtime should interpret direct selection,
  profile-first selection, and delegation to mature owner skills

When `--preview-skill-root` is used, the exporter writes temporary runtime-like
skill directories under `<root>/<runtime>/<skill-name>/`, emits a
`preview-manifest.json`, and smoke-checks each generated `SKILL.md` for
frontmatter, directory-name alignment, runtime description length, preview-only
body markers, and optional interface metadata files. This still is not an
installed-runtime test.

They are inspection artifacts only; edit the kernel examples and source
Markdown/YAML/JSON instead of editing adapter output.

When `--installable-manifest-root` is used, the exporter writes
`adapter-manifest.json` files under `<root>/<runtime>/<skill-name>/` plus an
`installable-manifest-index.json`. These manifests are still prototypes:
`safe_to_install_automatically: false`, `manual_review_required: true`, and
`source_of_truth: kernel`. They preserve `selection_semantics`, candidate
runtime files, frontmatter, required/optional files, and source paths, while
keeping workflow, validation, memory, install policy, and promotion as
non-authoritative kernel fields instead of top-level manifest truth.

When `--exercise-skill-root` is combined with `--installable-manifest-root`, the
exporter re-reads the generated manifest index and writes session-only
runtime-like skill directories under `<root>/<runtime>/<skill-name>/`. The
exercise root records `global_install_modified: false`, refuses known global
skill roots, and smoke-checks that generated `SKILL.md` files preserve
frontmatter, manual-review gates, non-auto-install status, source-of-truth
markers, and `selection_semantics`.

The manifest-exercise runtime capture confirms that these session-only roots
reach Codex and Claude Code prompt surfaces. In an empty isolated Codex workdir,
`core-ops` is selected for operational closeout, `paper-reading` is selected for
reading-only work, and `research-distillation-workflow-contract` is selected for
public workflow distillation. In the full repo root, existing project guidance
and mature owner skills still route maintenance work through `project-ops-router`
and leaf skills. Claude Code loads the session-only plugin skills and shows all
three in the skill prompt, but local CLI auth still blocks model-choice capture.

## Install Handoff Contract

`install-handoff-contract-2026-05-28.json` is the active gate between behavior
capture and real runtime writes. It is `reviewed-execute-enabled`: the real
installer and repo-split scaffolder may execute reviewed plans for the
`project-local-profile-install` and `repo-split-handoff` modes, but
`may_write_runtime_files_without_review` and
`may_write_global_roots_without_explicit_user_request` remain false, and the
two global-root modes stay disabled by default.

The contract separates five target modes:

- `session-only-exercise`: allowed; temporary roots only, must keep
  `global_install_modified: false`.
- `project-local-profile-install`: allowed with a reviewed plan that names the
  target root, profile, runtime, generated files, validation checks, and
  rollback record.
- `global-bootstrap-install`: still manual-existing-command-only; the thin
  `global-bootstrap` profile only.
- `maintainer-debug-global-install`: still requires explicit user request and
  per-invocation rollback; never the default.
- `repo-split-handoff`: allowed with a reviewed plan, passing source
  inventory, and privacy audit `status: passed`.

The 2026-05-27 contract is preserved on disk as the frozen pre-revision
artifact (`install-handoff-contract-2026-05-27.json`, `status: superseded`)
so refusal regression tests can keep exercising the
`automation_policy.real_installer_authorized = false` path explicitly.

## Install Plan Validator

Use:

```bash
python3 scripts/validate_install_handoff_plan.py /path/to/plan.json --manifest-index /tmp/kernel-installable-manifests/installable-manifest-index.json
```

A valid plan must declare the target mode, profile, runtime, target root,
requested manifests, review gates, source-of-truth paths, validation commands,
privacy audit, rollback record, and forbidden-action acknowledgements. The
validator rejects unreviewed global-root targets, missing contract gates,
manifest/profile mismatches, missing acceptance checks, and any plan that asks
the validator itself to write files.

### Install Plan Fixtures

Checked-in concrete fixtures under
`schemas/skill-kernel/examples/install-plans/` exercise the validator on real
`core-ops` review paths without writing runtime files:

- `core-ops-project-local-install.plan.json` — passing project-local Codex
  install plan; under the active 2026-05-28 contract `mode_allowed_now` is now
  true and the plan is executable through `apply_install_plan.py`.
- `core-ops-repo-split.plan.json` — passing repo-split plan that targets a
  hypothetical `skill-kernel-core-ops` destination repo through the
  `generic-agent` portable adapter.
- `core-ops-rejected-repo-split-missing-leakage-gate.plan.json` — intentional
  negative fixture that drops the `no-credential-or-private-path-leakage` gate
  and must be rejected.

`tests/test_install_plan_fixtures.py` re-runs the validator against each
fixture with a freshly generated manifest index and asserts the expected
pass/reject behavior. The fixtures are the next gate after the contract and
validator: they prove the review shape works on concrete plans before any real
installer or repo split is implemented.

## Install Writer Preview

`scripts/preview_install_writer.py` is the next read-only step before a real
installer. It consumes a passing install plan plus the generated manifest
index, re-runs the plan through `validate_install_handoff_plan.py`, and (only
if the plan passes) enumerates the exact list of file writes a future
installer would emit:

```bash
python3 scripts/preview_install_writer.py \
  schemas/skill-kernel/examples/install-plans/core-ops-project-local-install.plan.json \
  --manifest-index /tmp/kernel-installable-manifests/installable-manifest-index.json
```

The preview supports only `project-local-profile-install` for now. Session-only
exercise has its own generator under `--exercise-skill-root`; repo-split
scaffolding is structurally different and is intentionally out of scope here.
The preview is read-only — it never writes under `target_root` — and emits
content sha256 hashes plus byte counts for each candidate file so the future
installer can later reuse the same shape for a real write plus rollback record.
The output schema lives at `schemas/skill-kernel/write-actions.schema.json`.
`tests/test_install_writer_preview.py` covers the supported mode, unsupported
modes, plan rejections, and the no-write contract.

## Profile Repo-Split Inventory And Privacy Audit

`scripts/inventory_profile_for_split.py` walks a profile's kernel example,
kernel source paths, profile-index entry, and every required/optional skill
directory to produce two read-only artifacts:

- A source inventory (`schemas/skill-kernel/repo-split-inventory.schema.json`)
  listing every file a reviewed repo-split scaffolder would copy, with class
  (`kernel` / `kernel-source` / `skill-required` / `skill-optional`), sha256,
  byte count, owning skill, proposed destination path, and a registered
  exclusion list (sidecar artifacts, project memory, OS metadata, bytecode).
- A privacy audit
  (`schemas/skill-kernel/repo-split-privacy-audit.schema.json`) that scans every
  included file for absolute home paths, sidecar artifact paths with a
  concrete task id, SSH private key blocks, AWS / GitHub / Anthropic token
  shapes, and personal institutional emails. Status is `passed` only when no
  hits exist.

Checked-in artifacts for the `core-ops` profile live under
`schemas/skill-kernel/repo-split/`:

- `core-ops-source-inventory-2026-05-27.json`
- `core-ops-privacy-audit-2026-05-27.json`

`tests/test_repo_split_inventory.py` regenerates both artifacts and asserts the
checked-in copies still match the live profile state.

## Repo-Split Writer Preview

`scripts/preview_repo_split_writer.py` is the repo-split counterpart of the
install writer preview. It consumes a passing `repo-split-handoff` plan plus
the generated manifest index, auto-locates the profile's source inventory and
privacy audit under `schemas/skill-kernel/repo-split/`, and emits a
write-actions document covering:

- `create-directory` actions for the destination repo and every required
  subdirectory.
- `copy-file` actions for every file the inventory marks
  `include_in_split: true`, with source sha256 and byte count.
- `write-profile-index-slice` action describing the minimal profile-index slice
  the scaffolder must compose for the destination repo.
- `post-write-check` actions listing the validators a real scaffolder must run
  in the destination repo after copies finish (`validate_skills.py`,
  `validate_skill_taxonomy.py`, exporter `--check`, focused unittests).

```bash
python3 scripts/preview_repo_split_writer.py \
  schemas/skill-kernel/examples/install-plans/core-ops-repo-split.plan.json \
  --manifest-index /tmp/kernel-installable-manifests/installable-manifest-index.json
```

The preview refuses non-`repo-split-handoff` modes, plans the validator
rejects, and profiles whose privacy audit is not `status: passed`. It never
writes under `target_root`. `tests/test_repo_split_writer_preview.py` covers
the passing path, unsupported modes, plan rejections, missing-inventory paths,
and the no-write contract.

## Real Installer And Repo-Split Scaffolder (Authorization-Gated)

`scripts/apply_install_plan.py` and `scripts/apply_repo_split.py` are the
real installer and scaffolder. They re-run the validator, re-use the matching
preview, then — **only if** the active handoff contract sets
`automation_policy.real_installer_authorized: true`, the plan's mode is
`allowed_now: true`, and the caller passes `--execute` — perform the writes
and record a rollback artifact. Under the active 2026-05-28 contract both
modes are authorized for reviewed plans; under the frozen 2026-05-27
pre-revision contract both scripts still refuse, write nothing, and exit
non-zero. They also refuse any target under `~/.codex/skills`,
`~/.agents/skills`, or `~/.claude/skills` regardless of contract state.

```bash
python3 scripts/apply_install_plan.py PLAN.json \
  --manifest-index /tmp/kernel-installable-manifests/installable-manifest-index.json \
  --rollback-record /tmp/install-rollback.json \
  --execute

python3 scripts/apply_repo_split.py PLAN.json \
  --manifest-index /tmp/kernel-installable-manifests/installable-manifest-index.json \
  --rollback-record /tmp/split-rollback.json \
  --execute
```

`tests/test_apply_install_plan.py` covers refusal under the frozen
pre-revision contract, refusal when `--execute` is missing, refusal of
global-root targets even under a synthetic authorized contract, the happy
path under a synthetic authorized contract (writes to a tmp dir, rollback
record written), and the happy path against the live active 2026-05-28
contract.

The drafted-and-applied contract revision proposal that authorized the
2026-05-27 → 2026-05-28 flip lives at
`schemas/skill-kernel/proposed-revisions/install-handoff-contract-2026-05-28.proposal.md`.

## Current Finding

The `core-ops`, `paper-reading`, and `research-distillation` examples all fit
the same schema without introducing profile-specific fields. That suggests the
current kernel is a reasonable split-preflight schema, and the dry-run exporter
can preserve profile, routing, lane, validation, memory, and promotion fields
across Codex, Claude Code, Cursor, and generic-agent target metadata. The
Codex/Claude projections are grounded in observed local skill-directory
surfaces: `SKILL.md` with `name` and `description` frontmatter is the required
runtime-facing surface, while workflow, validation, memory, and promotion remain
docs-only adapter fields. Generated preview fixtures now pass isolated
runtime-like skill-root smoke checks. The first runtime capture found that
Codex sees all three preview skills and selects `paper-reading` plus
`research-distillation-workflow-contract` for matching prompts, but routes a
general core-ops maintenance prompt to mature leaf skills instead. The follow-up
core-ops semantics capture resolves this as intended behavior: `core-ops` is a
profile-first entrypoint when installed as the only operational profile or when
a runtime enforces profile-first selection, and otherwise may delegate to mature
owner skills in a full shared root. The exporter now prototypes installable
manifest files and can exercise them into session-only runtime-like skill roots
while preserving that selection contract and keeping all generated outputs
review-gated rather than auto-installable. The manifest-exercise runtime capture
confirms the same last-mile shape: Codex selects the exercised skills in
isolated session-only contexts, while full-root maintenance still delegates to
mature project-local owner skills; Claude Code loads the exercised skills through
a session-only plugin and includes them in the skill prompt, but auth-enabled
model-choice capture remains blocked by local CLI login state. The install
handoff contract and non-mutating plan validator now record and enforce the
reviewed boundary before any real installer or repo split can consume those
manifests.

## Validation

Run:

```bash
uv run scripts/validate_skill_taxonomy.py
python3 -m unittest -v tests.test_skill_kernel_schema tests.test_skill_kernel_adapter_export
python3 -m unittest -v tests.test_install_handoff_plan_validator
python3 -m unittest -v tests.test_install_plan_fixtures
python3 -m unittest -v tests.test_install_writer_preview
python3 -m unittest -v tests.test_repo_split_inventory
python3 -m unittest -v tests.test_repo_split_writer_preview
python3 -m unittest -v tests.test_apply_install_plan
python3 scripts/export_skill_kernel_adapters.py --runtime all --check
python3 scripts/export_skill_kernel_adapters.py --runtime all --preview-skill-root /tmp/kernel-preview-skills
python3 scripts/export_skill_kernel_adapters.py --runtime all --installable-manifest-root /tmp/kernel-installable-manifests
python3 scripts/export_skill_kernel_adapters.py --runtime all --installable-manifest-root /tmp/kernel-installable-manifests --exercise-skill-root /tmp/kernel-manifest-exercise
```
