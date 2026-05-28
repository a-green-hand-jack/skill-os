# Install Handoff Contract Revision (2026-05-28, APPLIED)

> **Status:** applied 2026-05-28 with explicit user authorization. The active
> contract is now
> `schemas/skill-kernel/install-handoff-contract-2026-05-28.json`. The
> previous contract at
> `schemas/skill-kernel/install-handoff-contract-2026-05-27.json` is preserved
> as `status: superseded` and is used by the apply-time refusal regression
> tests.

## Goal

Authorize the real installer (`scripts/apply_install_plan.py`) for
`project-local-profile-install` mode and the real scaffolder
(`scripts/apply_repo_split.py`) for `repo-split-handoff` mode, while keeping
every other review gate intact and continuing to refuse global-root writes
without explicit user request.

## What Changes

Apply the following minimal edits to the active contract JSON:

```diff
   "automation_policy": {
-    "real_installer_authorized": false,
+    "real_installer_authorized": true,
     "may_write_runtime_files_without_review": false,
     "may_write_global_roots_without_explicit_user_request": false,
-    "next_safe_step": "Build a non-mutating install-plan validator that consumes this contract and generated manifest indexes before any runtime write command is added."
+    "next_safe_step": "Use scripts/apply_install_plan.py and scripts/apply_repo_split.py only against passing plans with --execute; do not edit global skill roots."
   },
```

```diff
   "target_modes": [
     ...
     {
       "id": "project-local-profile-install",
-      "status": "requires-reviewed-plan",
-      "allowed_now": false,
+      "status": "allowed-with-reviewed-plan",
+      "allowed_now": true,
       ...
     },
     ...
     {
       "id": "repo-split-handoff",
-      "status": "design-only-until-reviewed-plan",
-      "allowed_now": false,
+      "status": "allowed-with-reviewed-plan-and-passing-audit",
+      "allowed_now": true,
       ...
     }
   ],
```

Modes `global-bootstrap-install` and `maintainer-debug-global-install` remain
`allowed_now: false`. The applier scripts also independently refuse to write
under any known global skill root, so flipping `real_installer_authorized`
does not silently authorize global mutations.

## What Stays The Same

- All 9 review gates remain in force; the validator still rejects plans
  missing any gate.
- All 5 forbidden actions stay listed and acknowledged-by-plan is still
  required.
- `safe_to_install_automatically: false` on every generated manifest stays
  unchanged; manual review of the plan is still the contract precondition.
- The scaffolder still requires a passing inventory and a privacy audit with
  `status: passed`.

## Authorization Required From The User

Before applying this revision the user should confirm:

1. They want to authorize real runtime writes for project-local profile
   installs through reviewed plans.
2. They want to authorize real repo-split scaffolding under the same review
   chain.
3. They acknowledge that global-root writes remain unauthorized by default,
   and that the maintainer/debug-global-install path still requires explicit
   per-invocation user request.
4. They understand the rollback record is the only safety net after a real
   apply, and they will keep `--rollback-record <path>` set for any real run.

## Rollback Plan For The Contract Revision Itself

If the revision causes problems, revert via:

```
git revert <commit-applying-this-proposal>
```

Or, manually re-edit the contract JSON to set `real_installer_authorized: false`
and `allowed_now: false` on both modes. The validator, preview, and applier
will all immediately refuse writes again.

## Acceptance Checks

After applying the revision, the following must still pass:

- `python3 scripts/validate_skills.py`
- `uv run scripts/validate_skill_taxonomy.py`
- `python3 -m unittest tests.test_skill_kernel_schema tests.test_skill_kernel_adapter_export tests.test_install_handoff_plan_validator tests.test_install_plan_fixtures tests.test_install_writer_preview tests.test_repo_split_inventory tests.test_repo_split_writer_preview tests.test_apply_install_plan`
- `python3 scripts/export_skill_kernel_adapters.py --runtime all --check`

`tests/test_apply_install_plan.py` is the regression boundary: the
`*_refuses_under_active_contract` tests will start to fail once the active
contract is flipped, which is the intended signal that the gate has moved.
Those tests should be re-keyed to a separately-checked "frozen pre-revision
contract" fixture so the refusal path continues to be exercised even after
the active contract authorizes writes.

## Why This Is The Right Boundary To Cross

Every prior step in the chain — kernel schema, adapter export, runtime
captures, selection semantics, installable manifests, session-only exercises,
handoff contract, install-plan validator, plan fixtures, install writer
preview, source inventory + privacy audit for all draft profiles, repo-split
writer preview, real installer and scaffolder code with refusal-when-not-
authorized tests — has been built read-only or under a contract that refuses
writes. Authorizing project-local installs and repo-split scaffolding through
reviewed plans is the smallest additional authorization that ships the goal,
and it leaves the dangerous global-root paths blocked.
