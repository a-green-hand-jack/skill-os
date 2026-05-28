# ml-research-skills Current Status

> Cross-session working memory. Re-verify git state before acting.

## Current Focus

- Summary: The repository is at 74 skills (69 leaf/utility + 4 domain routers + 1 root router `ml-research-router`). A profile-first skill-matrix layer now sits above the ML research bundle: `profiles/profile-index.yaml` records the active `ml-research` and `global-bootstrap` profiles plus draft `core-ops`, `paper-reading`, `research-distillation`, and `automation` extraction targets. `schemas/skill-kernel/` defines the minimum portable kernel schema with checked `core-ops`, `paper-reading`, and `research-distillation` examples plus `runtime-adapter-contracts.json`; `scripts/export_skill_kernel_adapters.py` now dry-runs non-installable Codex/Claude Code/Cursor/generic-agent adapter metadata, generates preview-only runtime-like `SKILL.md` fixture roots, writes review-gated prototype installable manifests from those projections, and exercises those manifests into temporary session-only runtime-like roots without modifying global installs. `schemas/skill-kernel/runtime-trigger-capture-2026-05-27.json` records the first prompt-surface capture, `schemas/skill-kernel/core-ops-runtime-semantics-2026-05-27.json` resolves `core-ops` as a profile-first entrypoint that delegates to mature owner skills in full shared roots, `schemas/skill-kernel/manifest-exercise-runtime-capture-2026-05-27.json` records Codex/Claude prompt-surface behavior from manifest-exercised session-only roots, `schemas/skill-kernel/install-handoff-contract-2026-05-27.json` defines the reviewed install/repo-split handoff boundary before any real installer, and `scripts/validate_install_handoff_plan.py` now validates install/repo-split plans against that contract plus generated manifest indexes without writing files. `tests/profile-routing-evals.json` records profile-selection examples before leaf-skill routing, `scripts/score_profile_routing.py` scores actual runtime/agent predictions, and `profiles/research-distillation/` now contains the first profile-local artifact loop plus two real public-source agent+RL trials: ByteDance UI-TARS and Alibaba / Tongyi DeepResearch. The combined `agent-workflow-contract-planner` proposal now has a reusable workflow-contract template, lane-routing fixtures, and two filled real-task trials; the trials defer standalone skill scaffolding and treat the contract as a portable schema/preflight artifact for now. `docs/design/skill-matrix.md` records the multi-repo Skill OS design, profile contract, migration order, self-evolution loop, minimum kernel schema, and adapter/manifest/exercise/capture/handoff/plan-validation boundary. Global installs still default to the thin `ml-research-bootstrap` entry point, while the full bundle is project-local to initialized ML research projects or maintainer/debug validation.
- Active milestone: maintain 74-skill collection and first profile registry, keep both validators passing, reinstall after skill changes.
- Current phase: `maintenance`.
- Active gate: choose the smallest safe commit path; keep README/AGENTS/CLAUDE, skill inventory, tests, and memory aligned before push when affected; skill-kernel manifest-exercise/runtime-capture, install-handoff contract, and install-plan validator work requires focused adapter/schema/validator tests plus smoke commands.
- Last updated: 2026-05-27.

## Latest Reliable State

- 74 skills are present in `skills/`; `python3 scripts/validate_skills.py`, `uv run scripts/validate_skill_taxonomy.py`, targeted skill-kernel/profile tests, install-plan validator tests, adapter dry-run check, preview-root smoke, installable-manifest smoke, manifest-exercise smoke, install-handoff contract checks, and `git diff --check` pass as of 2026-05-27.
- `profiles/profile-index.yaml` is the first agent-neutral profile registry for the broader skill matrix. Active profiles: `global-bootstrap` and `ml-research`. Draft profiles: `core-ops`, `paper-reading`, `research-distillation`, and `automation`. `research-distillation` now registers profile-local docs/templates/examples under `artifacts`: distillation-run, pattern-card, skill-proposal, and workflow-contract templates; two synthetic examples; a ByteDance UI-TARS agent+RL trial; an Alibaba / Tongyi DeepResearch agent+RL trial; their direct comparison; the combined `agent-workflow-contract-planner` proposal; `workflow-contract-routing-evals.json` fixtures covering action-only, evidence-only, combined, and no-contract prompts; and filled workflow-contract trials for automation and research-distillation tasks. `schemas/skill-kernel/` adds a checked portable kernel schema plus `core-ops`, `paper-reading`, and `research-distillation` examples that now include `selection_semantics` without profile-specific schema fields. `schemas/skill-kernel/runtime-adapter-contracts.json` records observed Codex/Claude `SKILL.md` expectations, and `scripts/export_skill_kernel_adapters.py` generates dry-run adapter bundles, per-runtime JSON files, temporary preview skill roots under `<root>/<runtime>/<skill-name>/` with smoke-checked `SKILL.md` fixtures, review-gated prototype installable manifests under `<root>/<runtime>/<skill-name>/adapter-manifest.json` plus `installable-manifest-index.json`, and session-only manifest exercise roots under `<root>/<runtime>/<skill-name>/` with `manifest-exercise-summary.json`; `schemas/skill-kernel/runtime-trigger-capture-2026-05-27.json` records actual Codex/Claude prompt visibility and Codex route-choice results for preview skills; `schemas/skill-kernel/core-ops-runtime-semantics-2026-05-27.json` records that `core-ops` is selected in isolated/profile-first contexts and delegates in full shared roots; `schemas/skill-kernel/manifest-exercise-runtime-capture-2026-05-27.json` records that Codex sees and selects manifest-exercised skills in isolated session-only contexts, while full-root maintenance still delegates to mature owner skills, and Claude Code shows all three exercised skills in a session-only plugin prompt. `schemas/skill-kernel/install-handoff-contract-2026-05-27.json` now blocks real installers and repo splits until a reviewed plan names target root, profile/runtime, source-truth files, validation, privacy audit, selection semantics, and rollback. `schemas/skill-kernel/install-plan.schema.json` plus `scripts/validate_install_handoff_plan.py` check that plan boundary without writing files; focused tests cover pass/fail and no-write behavior. `tests/test_skill_kernel_adapter_export.py` checks source-truth preservation, projection contracts, preview fixture generation, installable manifest generation, session-only manifest exercise, trigger-capture summary, core-ops semantics capture, and manifest-exercise runtime capture. `tests/test_skill_kernel_schema.py` checks the install handoff contract and plan schema. `tests/test_install_handoff_plan_validator.py` checks the plan validator. `tests/profile-routing-evals.json` has 8 profile-selection fixtures. `scripts/score_profile_routing.py` can generate blank/gold prediction files and score actual agent/runtime choices for profile and entrypoint accuracy. `uv run scripts/validate_skill_taxonomy.py` validates profile schema fields, profile artifacts, profile skill references, skill-kernel schema/examples, install handoff contract paths, install-plan schema path, and profile eval targets.
- Hierarchical routing system (Batches 1–5 plus bootstrap distribution and profile hardening): 5 routers (ml-research-router root + 4 domain), negative-boundary descriptions on confusable leaf skills, 27 routing evals with `expected_path`, 8 profile routing evals, `taxonomy/skill-index.yaml` (role/domain/lifecycle taxonomy), `profiles/profile-index.yaml` (profile registry), `schemas/skill-kernel/` (portable profile/kernel schema, examples, runtime adapter contract fixture, preview skill-root smoke path, installable manifest prototype, session-only manifest exercise path, runtime trigger capture, core-ops selection semantics, manifest-exercise runtime capture, install/repo-split handoff contract, and install-plan schema), `scripts/export_skill_kernel_adapters.py` (dry-run adapter exporter with runtime projections, preview `SKILL.md` fixture generation, review-gated manifest generation, and session-only manifest exercise generation), `scripts/validate_install_handoff_plan.py` (non-mutating handoff-plan validator), `profiles/research-distillation/` (first profile-local artifact loop plus UI-TARS and Tongyi DeepResearch trials plus workflow-contract proposal/template/evals/filled trials), `scripts/score_profile_routing.py` (profile-choice scoring harness), `scripts/validate_skill_taxonomy.py` (taxonomy/profile/kernel/handoff/plan-schema checks), memory reliability layer (fact-index.yaml, memory-revision.json rev 32, 4 memory contracts, memory_bootstrap.py with --check-stale). `ml-research-router` has `references/skill-index.md` so unknown-skill requests can route despite leaf description truncation.
- Distribution boundary: default global install is `ml-research-bootstrap`; full global installs are maintainer/debug-only. Full bundle install belongs inside initialized ML research projects.
- Installed runtime copies were refreshed for the new bootstrap policy with `npx skills add . -g -a codex claude-code -s ml-research-bootstrap -y` on 2026-05-25. `project-init` was also installed globally as the optional new-project initializer. The full bundle was intentionally not installed globally.
- Root startup memory now includes `memory/project-conventions.md` and `memory/hot-results.md`, closing the gap where templates existed but session-start protocol files were missing from `memory/`.
- `memory/hot-results.md` is intentionally empty of experiment entries because this repository is a skill collection, not an experiment project.
- 57 skills were present and installable after adding `run-status-monitor`; this historical count was superseded by the 69-leaf/74-skill state above.
- Skill listing budgets were confirmed sufficient on both platforms at the then-current 57-skill audit point (DEC-027, RSK-020 mitigated): Claude Code raised to 2% of context window via `skillListingBudgetFraction: 0.02` in `~/.claude/settings.json` (~16k chars for 200k context); Codex gpt-5.5 has a 265k-token context → 2% budget ≈ 21k chars; both exceeded the 57-skill total of ~12,225 chars. All descriptions were ≤ 373 chars and front-loaded, satisfying Codex's 500-char per-skill hard limit. Re-audit when skill count exceeds ~80.
- `run-status-monitor` probes local logs/processes, project wrapper commands, SLURM, and RunAI to produce short `docs/ops/runs/<run-id>-status.md` artifacts without copying raw logs or scheduler output into chat.
- `remote-project-control` now ships `remote-cmd` and `remote-bash` helper scripts plus SSH quoting guidance so agents avoid fragile double-quoted one-liners that expand remote variables locally.
- `remote-project-control` routing metadata and generated project templates now explicitly mention raw SSH one-liners, SSH quoting issues, `remote-cmd`, and `remote-bash`, because wrapper scripts alone did not reliably stop stale sessions from composing fragile SSH commands.
- `safe-git-ops` now ships `project-push` so routine network pushes use one stable command shape instead of drifting among equivalent `git push` variants; root `AGENTS.md`/`CLAUDE.md`, README project-structure guidance, `project-init`, and `init-python-project` templates now surface the same rule outside the skill body.
- `run-experiment`, `remote-project-control`, and `run-status-monitor` now encode resource-aware launch: classify smoke/debug/formal work, inspect server resource and pending state when practical, use the fastest compatible allocation for smoke/debug, and preserve formal-job contracts.
- Server experiment skills now treat Python environment creation as a cost: reuse project/stage uv environments by default, avoid deriving `UV_PROJECT_ENVIRONMENT` from each job name, and require a concrete dependency/isolation/sync-race reason for job-specific envs.
- Project-control-root code worktrees now share one uv environment by default: use absolute `UV_PROJECT_ENVIRONMENT=<ProjectRoot>/.uv-envs/code` and `uv run` from the active worktree for `<ProjectRoot>/code/` and sibling `code-worktrees/*`; create stage/worktree envs only for dependency/stack changes, destructive package tests, or real concurrent sync risk.
- Server experiment skills now treat long image pulls, `ContainerCreating`, and GPU-generation/CUDA compatibility as scheduling inputs, so lower-wait pools are not chosen blindly for smoke/debug work.
- Server experiment skills now distinguish resource inventory from job occupancy: agents should understand available/allocated GPUs, workload parallelization shape, actual active GPU use, and write feedback when jobs underutilize requested resources.
- `run-status-monitor` and `remote-project-control` now stop repeated scheduler API probes after OAuth/session refresh failure, switch to filesystem/project-wrapper fallback when available, and record one login-refresh action.
- `run-status-monitor` now treats repeated progress tracking as artifact work: the main agent should not run long-lived `sleep`/poll/log-watch loops, and multi-check monitoring should be handled by a project wrapper, sidecar, or bounded background monitor that writes a short status artifact.
- `skill-system-auditor` now includes agent-regression hardening guidance: when a skill exists but agents keep regressing, promote the lesson into routing triggers, core contracts, references, templates, wrappers, memory, reinstall, and installed-copy checks.
- `sidecar-task-runner` exists and was installed globally for Codex and Claude Code on 2026-05-05.
- `personalization-memory` defines a non-interrupting preference writeback protocol, and `sidecar-task-runner` provides a `personalization-scanner` preset for low-cost candidate extraction.
- `memory-publication-auditor` audits private skills, memories, notes, or logs before converting them into public skills, docs, templates, or reusable patterns.
- `reference-library-manager`, `reference-reading-summarizer`, and `reference-project-synthesizer` now treat papers, collaborator docs, Markdown notes, BibTeX files, scripts, specs, and source bundles as project sources that become source cards and project-use notes.
- `code-reviewer` supports Spark pre-review plus strong isolated review.
- `token-usage-auditor` supports Codex, Claude Code, and repo-local sidecar metadata.
- `add-git-tag` can use read-only sidecar proposal generation while preserving human gates for tag creation and push.
- `asset/` images are tracked with semantic file names; README embeds `current-system-overview-2026-05-12.png` as the current top-level overview, plus execution loop, project anatomy, memory bus, workspace architecture, infra/audit layer, and detailed workflow panels.
- `asset/README.md` indexes each public diagram's role, README placement, and maintenance rules.
- Local `.agent/sidecars/` artifacts are private/local and excluded from this repo's tracked files.
- `submit-paper` now includes a screenshot/page/object-first LaTeX layout debugging protocol, with short pointers from camera-ready, figure review, and table review skills.
- `submit-paper` and `table-results-review` now include a specific `wraptable` / `wrapfig` right-side object protocol: tune `[N]`, avoid nested floating `table`, use compact inline caption/label handling, and adjust width/font/spacing locally.
- `latex-layout-issue-bundler` now creates `.agent/layout-issues/` bundles so PDF layout problems can be handed to agents without manual screenshots.
- `safe-git-ops` now uses Fast / Skill / Code / Risk commit paths, and `sidecar-task-runner` has a read-only `precommit-classifier` preset to recommend minimal validation and reinstall scope.
- `figure-results-review` and `paper-result-asset-builder` now support evolvable style memory: lessons can become preferences, project contracts, and eventually reusable skill rules.
- Writing skills now treat paper editing as layered work: layout, fluency, argument, technical consistency, style consistency, venue adaptation, and final polish each have different permissions and protected invariants.
- Writing skills now include public AI-paper writing heuristics distilled from hzwer/WritingAIPaper: core idea as insight/performance/capability, reader-facing story over research chronology, readability gates, evidence-integrity checks, and figure/table proximity rules.

## Top Open Risks

- `RSK-001`: Skill inventory drift between `skills/`, README, AGENTS, CLAUDE, and installed runtime copies.
- `RSK-002`: Sidecar output could be over-trusted for high-risk design or final review decisions.
- `RSK-003`: Private local facts or agent session logs could leak into public shared memory.
- `RSK-004`: Memory could become stale if not updated after skill behavior changes.
- `RSK-006`: Automatic personalization scans could over-promote noisy or private trajectory details if scope and confidence gates are ignored.
- `RSK-007`: Raw sources or reading trajectories could leak copyrighted/private text into public project memory if source cards are not used as the compression layer.
- `RSK-008`: Private memory publication audits could accidentally reproduce sensitive evidence if reports are not redacted and local/private by default.
- `RSK-009`: Run-status monitors could leak raw logs or overstate ETA if probe artifacts are not kept short and uncertainty-aware.
- `RSK-017`: Main agents could still become long-lived run observers, wasting tokens and crowding the context window, if polling is not pushed into artifacts, wrappers, or sidecars.
- `RSK-019`: Jobs can be running but underutilize allocated GPUs if agents do not model workload shape and actual resource occupancy.
- `RSK-021`: Agents may run bare `uv sync` in sibling code worktrees and create one `.venv` per worktree instead of the shared project-code env.
- `RSK-023`: Profile registries can drift from actual skills, docs, or future split repos if treated as prose instead of validated architecture.
- `RSK-010`: SSH wrappers can hide shell semantics if agents use `remote-cmd` for commands that actually require shell pipelines or variable expansion.
- `RSK-011`: Stable push wrappers could be used without ordinary preflight if agents treat them as replacing Git state checks.
- `RSK-012`: Already-open sessions and existing project guidance may keep stale SSH habits until skills are reinstalled or reread.

## Active Actions

- `ACT-001`: Keep project memory current after meaningful workflow or skill-system decisions.
- `ACT-002`: Add sidecar execution contracts gradually to high-value mechanical skills.
- `ACT-003`: Periodically run `skill-system-auditor` against this repo.
- `ACT-004`: Keep token telemetry tied to artifacts and outcomes, not treated as quality by itself.
- `ACT-006`: Keep LaTeX layout debugging guidance aligned across paper submission, camera-ready, figure, and table review skills.
- `ACT-007`: Keep README visual panels aligned with renamed `asset/` files.
- `ACT-008`: Use `asset/README.md` as the entry point before changing public diagram assets.
- `ACT-009`: Use `latex-layout-issue-bundler` before screenshot-based LaTeX layout debugging when a rendered PDF is available.
- `ACT-010`: Reuse wraptable/wrapfig right-side object guidance during local paper layout tuning.
- `ACT-011`: Use sidecar-assisted risk-tiered commit closeout to avoid full validation/reinstall on low-risk changes.
- `ACT-012`: Use visual-style and plot-style contracts before generating or reviewing paper figures.
- `ACT-013`: Use active writing layer and protected invariants before nontrivial paper prose edits.
- `ACT-014`: Use personalization scans after substantial sessions to extract candidate preferences without interrupting the user.
- `ACT-015`: Use the reference skill trio to turn `reference/` sources into cards and project-use notes before project-memory writeback.
- `ACT-016`: Keep the generalized source-centric reference workflow compatible with old paper/PDF projects while supporting initial project seed bundles.
- `ACT-017`: Use `memory-publication-auditor` before extracting public skills or docs from private memories, private skills, notes, or operational logs.
- `ACT-018`: Use `run-status-monitor` for lightweight active-run questions before pulling raw logs into the main agent context.
- `ACT-019`: Use `remote-cmd` for simple server commands and `remote-bash` plus project `scripts/ops/` wrappers for complex SSH logic.
- `ACT-020`: Use `project-push <repo> <remote> <branch>` for routine post-commit network pushes after safe-git preflight.
- `ACT-021`: Strengthen SSH wrapper routing and project templates, then reinstall changed skills.
- `ACT-022`: Use resource-aware launch for experiments: choose low-wait compatible resources for smoke/debug, preserve formal job resource contracts, and diagnose pending jobs by scheduler/resource cause.
- `ACT-023`: Reuse project/stage uv environments by default for server jobs; create job-specific uv envs only for dependency, isolation, or real sync-race reasons.
- `ACT-024`: Treat image pull / `ContainerCreating` and GPU-generation compatibility as smoke/debug routing inputs; avoid free-but-cold or incompatible pools.
- `ACT-025`: Use scheduler API auth circuit breakers: stop repeated API probes after OAuth/session refresh failure and use filesystem fallback plus one login-refresh action.
- `ACT-026`: Use artifact-bounded progress tracking: one bounded main-agent probe is acceptable, but repeated checks should update a short status artifact outside the main transcript.
- `ACT-027`: Use agent-regression hardening during skill maintenance: do not leave repeated mistakes as chat-only lessons or buried prose.
- `ACT-028`: Use utilization-aware resource feedback: track allocation vs active GPU use and update project status/memory when the next launch policy should change.
- `ACT-041`: Use shared project-code uv envs for sibling worktrees: `UV_PROJECT_ENVIRONMENT=<ProjectRoot>/.uv-envs/code` plus `uv run` from the active worktree by default, with recorded exceptions for dependency/stack changes or real sync risks.
- `ACT-042`: Keep root skill discovery budget-resilient: project-local unknown-skill ML research workflows start at `ml-research-router`, which reads `references/skill-index.md` before guessing leaf skills.
- `ACT-043`: Keep skill distribution project-local: global installs default to `ml-research-bootstrap`; full bundle installs are project-local or maintainer/debug only.
- `ACT-044`: Keep profile registry aligned with future skill-matrix splits: update `profiles/profile-index.yaml`, docs, memory, and taxonomy validation together.
- `ACT-045`: Keep the skill-matrix design doc and stricter profile schema aligned with future pack-splitting work.
- `ACT-046`: Keep profile-level routing evals aligned with profile registry changes before adding runtime profile adapters.
- `ACT-047`: Use `scripts/score_profile_routing.py` when evaluating actual profile selections from Codex, Claude Code, or future runtime adapters.
- `ACT-048`: Use `profiles/research-distillation/` templates for the first real public-source distillation run before creating a standalone skill.
- `ACT-049`: Use the UI-TARS trial outputs as the action-contract half of the broader workflow-contract proposal.
- `ACT-050`: Use the Tongyi DeepResearch comparison as the second real agent+RL trial before promoting any new agent-contract skill.
- `ACT-051`: Use the combined `agent-workflow-contract-planner` proposal as the gate before creating any standalone workflow-contract skill.
- `ACT-052`: Use the workflow-contract template and lane-routing evals as the schema gate before any standalone workflow-contract skill.
- `ACT-053` (done): Exercise `workflow-contract.md` on one real automation task and one real research-distillation task before deciding whether a new skill is justified.
- `ACT-054` (done): Define the minimum `skill-kernel` schema needed to carry profile identity, lane contracts, validation gates, and adapter-neutral runtime metadata across future skill repos.
- `ACT-055` (done): Instantiate the skill-kernel schema for `core-ops` and one non-ML/research-distillation profile before splitting repos.
- `ACT-056` (done): Add a dry-run adapter/export step from skill-kernel examples into Codex/Claude/runtime metadata without moving workflow truth out of Markdown/YAML/JSON sources.
- `ACT-057` (done): Compare dry-run adapter output against real Codex/Claude install metadata expectations before creating installable adapters or splitting repos.
- `ACT-058` (done): Prototype generated `SKILL.md` preview fixtures from runtime projections and smoke-test them in an isolated runtime-like skill root before installable adapters.
- `ACT-059` (done): Capture actual Codex/Claude runtime trigger behavior from generated preview skill roots before creating installable adapter manifests.
- `ACT-060` (done): Resolve `core-ops` profile-first adapter semantics before creating installable adapter manifests.
- `ACT-061` (done): Prototype installable adapter manifests from the skill-kernel dry-run projections.
- `ACT-062` (done): Exercise installable manifest prototypes in a temporary runtime/session-only skill root without modifying global installs.
- `ACT-063` (done): Capture actual Codex/Claude prompt-surface behavior from manifest-exercised session-only roots before real install automation or repo split.
- `ACT-064` (done): Define the reviewed install or repo-split handoff contract from the manifest-exercise runtime capture before writing any real installer.
- `ACT-065` (done): Implement a non-mutating install-plan validator that consumes the handoff contract and generated manifest indexes before any runtime write command is added.
- `ACT-066`: Exercise the install-plan validator on concrete `core-ops` project-local install and repo-split plan fixtures before any writer is implemented.
- `ACT-029`: Use public writing heuristics during paper skill work: classify the core sell, check logical strength/defensibility/confusion time/information density, and surface comparison-affecting protocol details before final prose.
- `ACT-030` (done): `data-pipeline-manager` — dataset acquisition, split design, quality audit, contamination check, versioning.
- `ACT-031` (done): `experiment-debugger` — NaN/gradient, OOM, slow training, metric errors, repro failures.
- `ACT-032` (done): `compute-budget-planner` — GPU-hour estimation, smoke test sizing, ablation costing.
- `ACT-033` (done): `feedback-synthesizer` — inbound advisor/collaborator feedback → triaged claim/risk/action items.
- `ACT-034` (done): `appendix-organizer` — appendix structure, claim boundaries, venue checklist filling.
- `ACT-035` (done): `project-pivot-planner` — narrow/angle/new-direction/kill framework for mid-project failures.
- `ACT-036` (done): `model-card-writer` — model cards, datasheets, reproducibility statements, artifact READMEs.
- `ACT-037` (done): `statistical-analysis-planner` — significance tests, effect sizes, CIs, seed variance, multiple-comparison corrections.
- `ACT-040` (done): Materialize root `project-conventions.md` and `hot-results.md` so startup protocol reads real files, not just templates.

## Planned Skills Roadmap (ACT-030–ACT-037)

| Priority | Skill | Gap Filled |
|---|---|---|
| 1 | `data-pipeline-manager` | Dataset acquisition, preprocessing, split design, quality audit, contamination, versioning — zero current coverage |
| 2 | `experiment-debugger` | Engineering failures: NaN/gradient, GPU OOM, slow training, data loading, metric errors, reproducibility |
| 3 | `compute-budget-planner` | Pre-experiment GPU-hour estimation, smoke sizing, ablation cost, cheaper alternatives |
| 4 | `feedback-synthesizer` | Inbound advisor/collaborator/reviewer feedback → claim updates, risk entries, action items |
| 5 | `appendix-organizer` | Appendix planning, claim boundaries, cross-references, NeurIPS/ICLR checklist sections |
| 6 | `project-pivot-planner` | Mid-project narrowing, angle change, or kill decision on consistent negative results |
| 7 | `model-card-writer` | Model cards, reproducibility checklists, datasheets for venue-required materials |
| 8 | statistical rigor | Significance testing, effect sizes, CIs, seed variance — scope decision needed first |

## Needs Verification Next Session

- `git status --short --branch`
- `python3 scripts/validate_skills.py`
- `uv run scripts/validate_skill_taxonomy.py`
- `python3 -m unittest -v tests.test_profile_routing_harness` after profile-routing harness changes.
- `python3 -m unittest -v tests.test_research_distillation_assets` after research-distillation profile asset changes.
- `python3 -m unittest -v tests.test_skill_kernel_schema` after skill-kernel schema changes.
- `python3 -m unittest -v tests.test_install_handoff_plan_validator` after install-plan validator changes.
- `python3 -m unittest -v tests.test_skill_kernel_schema tests.test_skill_kernel_adapter_export tests.test_install_handoff_plan_validator`, `python3 scripts/export_skill_kernel_adapters.py --runtime all --check`, `python3 scripts/export_skill_kernel_adapters.py --runtime all --preview-skill-root /tmp/kernel-preview-skills`, `python3 scripts/export_skill_kernel_adapters.py --runtime all --installable-manifest-root /tmp/kernel-installable-manifests`, and `python3 scripts/export_skill_kernel_adapters.py --runtime all --installable-manifest-root /tmp/kernel-manifest-exercise --exercise-skill-root /tmp/kernel-exercise-skills` after skill-kernel adapter, trigger-capture, selection-semantics, manifest, manifest-exercise, runtime-capture, install-handoff contract, or install-plan validator changes.
- Profile registry consistency after any future profile or pack-boundary changes.
- Whether repeated live sessions miss workflow-contract lane selection; if not, keep the contract as a profile-local schema/preflight artifact rather than a standalone skill.
- Relevant unit tests for any changed helper scripts.
- Whether installed `~/.agents/skills/` and `~/.claude/skills/` copies need refresh after any future skill changes.
- Whether any project-local full-bundle installs need refresh after this bootstrap distribution change is committed.

## Next Step

- Next profile-design step: exercise the non-mutating install-plan validator on concrete `core-ops` project-local install and repo-split plan fixtures before adding any real runtime write or repo-split writer.
