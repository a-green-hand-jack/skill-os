# ml-research-skills Decision Log

Use this file for durable project decisions and rationale, not transient status.

## DEC-001 - Treat This Repository As A Project With Its Own Memory

- Date: 2026-05-05
- Decision: Add committed root `memory/` for the skill system itself.
- Why: The repo now contains durable architecture decisions, workflow policies, sidecar routing, reviewer isolation, token telemetry, and public/private boundaries that should survive across sessions.
- Alternatives considered: keep state only in README/AGENTS/CLAUDE and git history.
- Affects: `memory/`, README.md, AGENTS.md, CLAUDE.md.
- Revisit when: memory becomes stale or too heavy for the repo.
- Certainty: user-stated

## DEC-002 - Use Sidecar Agents As Bounded Helper Workers, Not Final Decision Makers

- Date: 2026-05-05
- Decision: Use `gpt-5.3-codex-spark` through `codex exec --ephemeral` for bounded scans, drafts, pre-reviews, and mechanical proposals.
- Why: Fast sidecars reduce main-agent context load and make low-risk helper work auditable through `.agent/sidecars/<task-id>/` artifacts.
- Alternatives considered: let every main agent do all helper work inline; use context-forked subagents.
- Affects: `sidecar-task-runner`, `code-reviewer`, `add-git-tag`, `token-usage-auditor`.
- Revisit when: sidecar output is repeatedly noisy, unavailable, or over-trusted.
- Certainty: observed

## DEC-003 - Keep Code Reviewer Context Isolated From Code Writer Context

- Date: 2026-05-05
- Decision: Fresh review should use artifact bundles and one-shot CLI sessions instead of inheriting writer chat context.
- Why: Shared context can bias review, hide shortcuts, and reduce independence.
- Alternatives considered: normal in-session self-review; GitHub issues as the default handoff.
- Affects: `skills/code-reviewer/`.
- Revisit when: an external review platform becomes more useful than local review artifacts.
- Certainty: observed

## DEC-004 - Token Burn Is Telemetry, Not Quality By Itself

- Date: 2026-05-05
- Decision: Track token usage as attention, friction, cost, and artifact-yield telemetry; do not equate high token burn with good work.
- Why: Token usage can reveal where effort went, but project quality still depends on artifacts, decisions, evidence, tests, and review outcomes.
- Alternatives considered: use token count as a direct productivity or quality metric.
- Affects: `skills/token-usage-auditor/`, `memory/action-board.md`, `memory/evidence-board.md`.
- Revisit when: exact cross-agent accounting improves enough to support better yield models.
- Certainty: user-stated

## DEC-005 - Keep Local Machine Facts Out Of Shared Project Policy

- Date: 2026-05-05
- Decision: Shared skills and project docs should record compile backends and policies, not one user's local installed paths or tools.
- Why: Local paths and installed components are private/runtime facts that drift by workstation.
- Alternatives considered: commit local TeX paths or PDF-reader aliases into public skill docs.
- Affects: `init-latex-project`, `submit-paper`, local private memory.
- Revisit when: a repo intentionally standardizes dev containers or CI images.
- Certainty: user-stated

## DEC-006 - Treat LaTeX Layout Debugging As Local, Visual, Reversible Optimization

- Date: 2026-05-05
- Decision: Encode paper layout correction as a page/object-first workflow: localize the screenshot or affected object, make one small prose/float/page-break change, compile through the configured backend, inspect visually, and avoid broad global tuning unless the whole paper has a documented style issue.
- Why: User experience showed that short lines, floats, page breaks, and prose length interact; one-shot global `\sloppy`, `\emergencystretch`, paragraph, or float spacing changes can destabilize unrelated pages.
- Alternatives considered: treat layout as a global LaTeX parameter problem; treat it as pure writing rather than writing/float/page optimization.
- Affects: `skills/submit-paper/`, `skills/camera-ready-finalizer/`, `skills/figure-results-review/`, `skills/table-results-review/`.
- Revisit when: a project has a deliberate venue-wide layout policy or a class/style file issue that truly requires global tuning.
- Certainty: user-stated

## DEC-007 - Maintain Visual Assets As Indexed Documentation Artifacts

- Date: 2026-05-06
- Decision: Keep public diagrams under `asset/` with semantic filenames and a maintained `asset/README.md` index; update README links and memory figure inventory whenever a diagram is added, replaced, renamed, or materially repurposed.
- Why: The repo now uses several architecture diagrams with different scopes. Without an index, future agents can easily reuse the wrong image, create near-duplicates, or leave README and memory references stale.
- Alternatives considered: rely on file names only; keep visual roles implicit in README placement.
- Affects: `asset/`, README.md, AGENTS.md, CLAUDE.md, `skills/project-init/SKILL.md`, `memory/evidence-board.md`.
- Revisit when: source prompts, editable diagrams, or an automated image optimization pipeline is added.
- Certainty: observed

## DEC-008 - Use Risk-Tiered Commit Paths With Sidecar Precommit Classification

- Date: 2026-05-06
- Decision: Split commit/push closeout into Fast Path, Skill Path, Code Path, and Risk Path, and allow a read-only Spark sidecar to classify non-trivial diffs before the main agent commits.
- Why: Routine text or memory changes should not pay the latency cost of full smoke tests, full skill reinstall, or complete Git risk orientation. Sidecar classification can reduce main-agent decision time while keeping commit, push, reinstall, and final judgment with the main agent.
- Alternatives considered: always run the full validation and reinstall workflow; let sidecars perform commit/push directly.
- Affects: `skills/safe-git-ops/`, `skills/sidecar-task-runner/`, README.md, AGENTS.md, CLAUDE.md, `memory/project.yaml`.
- Revisit when: sidecar classification is slower than direct inspection or misses meaningful high-risk changes.
- Certainty: user-stated

## DEC-009 - Treat Paper Visual Style As Evolvable Memory

- Date: 2026-05-06
- Decision: Manage figure and table style through a promotion ladder: lesson -> preference -> project contract -> reusable skill rule.
- Why: Paper figure typography, line spacing, legend size, axis labels, colors, markers, exports, and wrapper behavior are too detailed and user/project-specific to fully specify upfront, but they still need durable memory so agents stop rediscovering the same fixes.
- Alternatives considered: hard-code one universal figure style; leave all style choices to ad hoc plotting scripts and visual inspection.
- Affects: `skills/figure-results-review/`, `skills/paper-result-asset-builder/`, README.md, AGENTS.md, CLAUDE.md.
- Revisit when: project-local style memories become noisy or are not actually read before figure generation.
- Certainty: user-stated

## DEC-010 - Treat Paper Writing As Layered Engineering

- Date: 2026-05-07
- Decision: Manage writing edits through explicit layers: layout, surface fluency, argument, technical consistency, style consistency, venue adaptation, and final polish.
- Why: Paper edits often look local but can silently change claims, notation, evidence scope, venue positioning, or style. Naming the active layer and protected invariants makes later edits safer and easier to remember.
- Alternatives considered: treat all writing changes as generic polish; rely only on full-draft consistency checks after the fact.
- Affects: `skills/paper-writing-memory-manager/`, `skills/paper-writing-assistant/`, `skills/paper-writing-contract-planner/`, `skills/paper-draft-consistency-editor/`, README.md, AGENTS.md, CLAUDE.md.
- Revisit when: layer labels become overhead without improving edit safety.
- Certainty: user-stated

## DEC-011 - Use Low-Cost Trajectory Scans For Personalization Writeback

- Date: 2026-05-07
- Decision: Add a `personalization-memory` skill and a `sidecar-task-runner` `personalization-scanner` preset so low-cost sidecars can scan sanitized trajectories, logs, diffs, sidecar artifacts, and project memory for reusable preferences.
- Why: The user does not want main agents to interrupt the workflow with memory questions. Many durable preferences emerge from repeated corrections and interaction traces, so the system should propose scoped writeback automatically while keeping raw logs private.
- Alternatives considered: ask the user before every preference update; let the main agent manually inspect all trajectories; write raw transcripts into project memory.
- Affects: `skills/personalization-memory/`, `skills/sidecar-task-runner/`, README.md, AGENTS.md, CLAUDE.md, `memory/`.
- Revisit when: personalization scans are too noisy, too expensive, or create privacy risk.
- Certainty: user-stated

## DEC-012 - Split Project References Into Library, Reading, And Project-Synthesis Layers

- Date: 2026-05-08
- Decision: Add three reference skills: `reference-library-manager` for project-local PDF/index/status management, `reference-reading-summarizer` for paper cards, and `reference-project-synthesizer` for connecting cards to claims, risks, baselines, benchmarks, writing, citations, and project memory.
- Why: Project references serve different roles: writing exemplars, method/theory sources, benchmark sources, baselines, citation support, and reviewer-risk evidence. Splitting management, reading, and project interaction keeps context smaller and allows cheaper models for low-risk scans while preserving stronger reasoning for project-changing implications.
- Alternatives considered: keep reference work inside `literature-review-sprint`; create one monolithic PDF-reading skill.
- Affects: `skills/reference-library-manager/`, `skills/reference-reading-summarizer/`, `skills/reference-project-synthesizer/`, README.md, AGENTS.md, CLAUDE.md, `skills/project-init/`, `memory/`.
- Revisit when: paper cards become too heavy or agents fail to route from cards into project memory.
- Certainty: user-stated

## DEC-013 - Generalize References Into Source-Centric Project Intake

- Date: 2026-05-10
- Decision: Extend the reference skill trio from paper/PDF handling to source-centric project knowledge intake, covering papers, collaborator documents, Markdown notes, BibTeX files, scripts, specs, and manually constructed source bundles.
- Why: Project-relevant information often arrives as collaborator documents, initial idea folders, specs, scripts, notes, or mixed bundles rather than formal papers. Treating all of them as sources lets the system produce source cards and project-use notes before writing durable project memory.
- Alternatives considered: create a separate source-management skill family; keep non-paper artifacts in ad hoc notes; force all upstream material into paper-card templates.
- Affects: `skills/reference-library-manager/`, `skills/reference-reading-summarizer/`, `skills/reference-project-synthesizer/`, README.md, AGENTS.md, CLAUDE.md, `skills/project-init/`, `memory/`.
- Revisit when: generic source cards become too broad or paper-specific workflows lose useful precision.
- Certainty: user-stated

## DEC-014 - Add A Private-To-Public Memory Publication Audit Layer

- Date: 2026-05-10
- Decision: Add `memory-publication-auditor` to scan private skills, memories, notes, and logs before turning them into public skills, docs, templates, or reusable patterns.
- Why: Some personalized or private operational memory contains generalizable engineering methods, but raw memory also contains accounts, paths, hosts, IPs, collaborator context, unpublished project details, and trajectories that must not be copied into public artifacts.
- Alternatives considered: manually inspect private memories ad hoc; extend `personalization-memory`; create public skills directly from private notes without an audit stage.
- Affects: `skills/memory-publication-auditor/`, README.md, AGENTS.md, CLAUDE.md, `tests/test_memory_publication_auditor.py`, `memory/`.
- Revisit when: deterministic scanner findings are too noisy or miss common private patterns.
- Certainty: user-stated

## DEC-015 - Add Context-Safe Active Run Monitoring

- Date: 2026-05-11
- Decision: Add `run-status-monitor` to answer active experiment status questions through short status artifacts rather than raw logs or scheduler dumps.
- Why: During long local, SSH, SLURM, or RunAI experiments, the user often needs progress, intermediate metrics, and ETA without polluting the main coding context. A dedicated probe skill can compress operational state into `docs/ops/runs/<run-id>-status.md` and route failures or surprising metrics to diagnosis.
- Alternatives considered: let the main agent inspect raw logs directly; keep monitoring inside `run-experiment`; rely on manual server checks.
- Affects: `skills/run-status-monitor/`, README.md, AGENTS.md, CLAUDE.md, `tests/test_run_status_monitor.py`, `memory/`.
- Revisit when: run configs become too project-specific or ETA extraction is frequently misleading.
- Certainty: user-stated

## DEC-016 - Add User-Level SSH Command Wrappers

- Date: 2026-05-12
- Decision: Add `remote-cmd` and `remote-bash` helper scripts plus SSH quoting guidance to `remote-project-control`.
- Why: Agents were still composing complex SSH double-quoted one-liners where local shells could expand remote variables such as `$d` before the command reached the server. A stable user/project wrapper pattern makes simple commands argv-style and moves complex logic into project scripts.
- Alternatives considered: rely on agents remembering single-quote rules; keep writing ad hoc SSH one-liners; disable approval prompts broadly.
- Affects: `skills/remote-project-control/`, `skills/run-status-monitor/`, README.md, AGENTS.md, CLAUDE.md, `tests/test_remote_command_wrappers.py`, private local workstation memory.
- Revisit when: wrappers are too restrictive for common scheduler commands or agents misuse `remote-cmd` for shell pipelines.
- Certainty: user-stated

## DEC-017 - Add Stable Project Push Wrapper

- Date: 2026-05-12
- Decision: Add `project-push` to `safe-git-ops` and install it as a user-level private helper so routine closeout pushes use one stable command shape.
- Why: Sandbox/network approval rules often match command prefixes rather than the user's intent. Agents were alternating among `git push`, `git -C <repo> push`, `cd <repo> && git push`, and shell-wrapped variants, causing repeated first-attempt network failures and wasting context.
- Alternatives considered: keep asking for network approval after failures; rely on agents remembering a preferred `git -C` form; approve broad shell-wrapped commands.
- Affects: `skills/safe-git-ops/`, README.md, AGENTS.md, CLAUDE.md, `tests/test_project_push_wrapper.py`, private local workstation memory.
- Revisit when: the wrapper does not reduce push approval churn or needs support for tags, force-with-lease, or non-branch refspecs.
- Certainty: user-stated

## DEC-018 - Move SSH Wrapper Policy Into Routing Metadata And Project Templates

- Date: 2026-05-12
- Decision: Strengthen `remote-project-control` routing metadata and generated project AGENTS/CLAUDE/ops templates so raw SSH one-liners, SSH quoting issues, and `remote-cmd`/`remote-bash` usage trigger the wrapper protocol before agents compose commands.
- Why: Agents continued to use raw SSH double-quoted one-liners even after wrapper scripts existed, because an already-open session or weak skill description could miss the latest wrapper guidance.
- Alternatives considered: rely on users to remind each session to reread the skill; only document the wrapper in `references/ssh-command-wrappers.md`; approve broad raw SSH command patterns.
- Affects: `skills/remote-project-control/`, `skills/init-python-project/templates/common/`, README.md, AGENTS.md, CLAUDE.md.
- Revisit when: agents still prefer raw SSH one-liners after reinstall and project-template refresh.
- Certainty: user-stated

## DEC-019 - Add Resource-Aware Experiment Launch Policy

- Date: 2026-05-13
- Decision: Encode resource-aware experiment launch across `run-experiment`, `remote-project-control`, and `run-status-monitor`.
- Why: For research velocity, agents should understand both available server resources and the task's actual compute needs. Smoke/debug jobs should use the easiest compatible compute that starts quickly, while formal jobs should preserve the intended experimental contract rather than silently changing resources.
- Alternatives considered: always submit to the default or most powerful resource; always wait for an existing pending job; treat pending jobs as generic failures without scheduler-resource diagnosis.
- Affects: `skills/run-experiment/`, `skills/remote-project-control/`, `skills/run-status-monitor/`, README.md, AGENTS.md, CLAUDE.md, private personalization memory.
- Revisit when: resource-aware choices cause provenance confusion, resource downgrades affect formal results, or scheduler-specific guidance needs a public/private split.
- Certainty: user-stated

## DEC-020 - Prefer Reusing Server uv Environments

- Date: 2026-05-13
- Decision: Encode a default policy that server experiments reuse an existing project or stage uv environment instead of creating a new job-specific env for every smoke or run.
- Why: On EPFL RunAI, job-specific uv envs can avoid sync races but add startup latency and clutter persistent storage. Agents were overusing new env creation during smoke runs when dependencies had not changed.
- Alternatives considered: always create job-specific envs for isolation; always share one env even during dependency changes or concurrent syncs; leave env strategy to each generated command.
- Affects: `skills/run-experiment/`, `skills/remote-project-control/`, `skills/run-status-monitor/`, private EPFL memory, private compute workflow preferences.
- Revisit when: project dependency changes become frequent enough that stage-level env naming needs a stronger public template.
- Certainty: user-stated

## DEC-021 - Treat Image Startup And GPU Generation As Scheduling Inputs

- Date: 2026-05-13
- Decision: Extend resource-aware experiment launch to consider container image startup, node image cache state, and GPU-generation/CUDA/software compatibility before rerouting smoke/debug jobs.
- Why: A lower-wait or apparently available GPU pool can still be a poor smoke target if the image is cold on that node family, the pod stays in `ContainerCreating`, or the project stack is not compatible with that GPU generation.
- Alternatives considered: choose any free compatible-memory GPU; wait indefinitely for `ContainerCreating`; treat image pull delays as code failures.
- Affects: `skills/run-experiment/`, `skills/remote-project-control/`, `skills/run-status-monitor/`, private EPFL memory, private compute workflow preferences.
- Revisit when: projects add explicit image prewarm jobs, node-family image-cache metadata, or per-project GPU compatibility matrices.
- Certainty: user-stated

## DEC-022 - Add Scheduler API Auth Circuit Breakers

- Date: 2026-05-13
- Decision: Add monitor circuit-breaker rules for scheduler API OAuth/session refresh failures.
- Why: Repeated `describe`/`logs`/`list` retries after `invalid_grant` do not recover monitoring, waste context, and make the session uncomfortable. The agent should stop API probes after the first auth failure, use SSH filesystem or project-wrapper fallback, and record one login-refresh action.
- Alternatives considered: keep retrying API commands; immediately interrupt the user for login; treat OAuth failures as job failure.
- Affects: `skills/run-status-monitor/`, `skills/remote-project-control/`, private EPFL memory, private compute workflow preferences.
- Revisit when: a stable non-interactive RunAI auth refresh mechanism exists.
- Certainty: user-stated

## DEC-023 - Keep Experiment Progress Tracking Artifact-Bounded

- Date: 2026-05-13
- Decision: Strengthen `run-status-monitor` so repeated experiment progress tracking is handled by status artifacts, project wrappers, sidecars, or bounded background monitors rather than transcript-visible main-agent polling loops.
- Why: Watching long experiments through the main agent wastes tokens, crowds the context window, and undermines the purpose of a dedicated run-status skill. The main agent should perform at most one bounded probe for an immediate answer, then read a compressed status artifact.
- Alternatives considered: allow the main agent to keep using `sleep` plus repeated scheduler/log/filesystem checks; rely on informal reminders to use the monitor skill; require human manual checks only.
- Affects: `skills/run-status-monitor/`, private compute workflow preferences.
- Revisit when: project wrappers or sidecar monitors fail to provide enough detail for reliable run-state decisions.
- Certainty: user-stated

## DEC-024 - Treat Repeated Agent Mistakes As Skill Hardening Inputs

- Date: 2026-05-13
- Decision: Add a reusable agent-regression hardening reference to `skill-system-auditor`.
- Why: The recent Git, SSH, RunAI, uv, resource-selection, OAuth, and progress-monitoring fixes showed the same pattern: a skill or helper may exist but still fail in practice if routing triggers are too weak, rules are buried too deep, templates do not inherit them, or installed runtime copies are stale.
- Alternatives considered: keep the lessons only in conversation and project memory; add ad hoc notes to each affected skill; create a separate new skill for regression hardening.
- Affects: `skills/skill-system-auditor/`, `memory/`.
- Revisit when: future regressions show the hardening ladder misses a common failure mode.
- Certainty: user-stated

## DEC-025 - Track Resource Inventory And Job Occupancy Separately

- Date: 2026-05-13
- Decision: Extend compute skills from resource-aware launch to utilization-aware feedback. Agents should know both what resources are available or allocated and how active jobs actually occupy those resources.
- Why: A job can be `RUNNING` while only one GPU is active and other allocated GPUs are idle. Without workload-shape awareness, agents may submit sequential target loops to multi-GPU allocations, miss idle cards, or fail to update future launch policy.
- Alternatives considered: rely on scheduler state alone; manually inspect GPU use without writing feedback; treat all running jobs as healthy until they finish.
- Affects: `skills/run-experiment/`, `skills/run-status-monitor/`, `skills/remote-project-control/`, private compute workflow preferences, private Quest memory.
- Revisit when: projects add standardized resource inventory wrappers or automated occupancy dashboards.
- Certainty: user-stated

## DEC-027 - Skill Description Limits Are Platform-Specific And Budget-Driven

- Date: 2026-05-14
- Decision: Treat skill `description` fields as budget-constrained routing signals, not free-form text.
- Why: Official docs (code.claude.com/docs/en/skills and developers.openai.com/codex/skills) confirmed two separate constraints:
  (1) **Per-skill cap**: Claude Code truncates `description` + `when_to_use` at **1,536 chars** combined (configurable via `maxSkillDescriptionChars`); Codex enforces a **500-char hard limit** validated in code (byte-counting bug: multi-byte chars like Chinese/Japanese hit the limit earlier than expected).
  (2) **Global listing budget**: both platforms cap the total skill listing at roughly **8,000 chars** (Claude Code: 1% of context window, configurable via `skillListingBudgetFraction`; Codex: 2% of context window or 8,000 chars). When budget overflows, Claude Code drops descriptions for least-used skills first; Codex shortens all descriptions. This is why many skill descriptions appear truncated (`…`) in the system-reminder.
  At 57 skills with ~12,225 total description chars, this repo exceeds the ~8,000 char global budget on both platforms.
- Key rules derived:
  - Front-load the trigger phrase and key use case; put fine-grained conditions later or in `when_to_use`.
  - Keep descriptions ≤ 500 chars to avoid Codex hard limit and stay safe under Claude Code budget.
  - The `when_to_use` frontmatter field can supplement `description` for routing without redundancy; both count toward the 1,536-char per-skill cap.
  - Use `skillOverrides: { skill-name: "name-only" }` in Claude Code to free listing budget for lower-priority skills.
  - Run `/doctor` in Claude Code to diagnose whether the budget is overflowing and which skills are affected.
- Alternatives considered: assume longer descriptions are always better; ignore the budget and rely on direct `/skill-name` invocation.
- Affects: all `skills/*/SKILL.md` description fields, `skills/safe-git-ops/SKILL.md` (leading `"` bug), README.md, CLAUDE.md.
- Revisit when: Claude Code raises the default budget fraction or Codex fixes the byte-vs-character counting bug.
- Certainty: official-docs-verified

## DEC-026 - Distill Public AI Paper Writing Advice Into Skill Heuristics

- Date: 2026-05-14
- Decision: Incorporate public lessons from hzwer/WritingAIPaper into paper-writing skills as original, workflow-oriented checks rather than copied prose.
- Why: External writing experience is useful when it changes agent behavior: agents should classify the paper's core sell, write for readers rather than research chronology, audit readability, surface evidence-integrity details, and make figure/table interpretation easy to find.
- Alternatives considered: leave the source as a one-off chat summary; add a standalone source note without routing it into skills; copy long excerpts into skills.
- Affects: `skills/paper-writing-assistant/`, `skills/paper-positioning-planner/`, `skills/paper-writing-contract-planner/`, `skills/paper-introduction-argument-writer/`, `skills/paper-draft-consistency-editor/`, `skills/experiment-story-writer/`, `skills/figure-results-review/`, `skills/table-results-review/`, `memory/`.
- Revisit when: writing skills become too broad, or future paper-writing sources suggest a more systematic shared writing-quality reference.
- Certainty: observed

## DEC-028 - Share uv Environments Across Code Worktrees

- Date: 2026-05-18
- Decision: In a project-control-root layout, `<ProjectName>/code/` and sibling `<ProjectName>/code-worktrees/*` should share one project-code uv environment by default via absolute `UV_PROJECT_ENVIRONMENT=<ProjectRoot>/.uv-envs/code`, with Python commands launched through `uv run` from the active worktree.
- Why: Bare `uv sync` in each worktree makes uv create `.venv` relative to that worktree root. This duplicates dependency setup, wastes time, and can leave agents waiting on avoidable environment bootstraps when the dependency stack has not changed.
- Alternatives considered: keep per-worktree `.venv` for maximum isolation; put the shared env under `code/.venv`; use a relative `UV_PROJECT_ENVIRONMENT`; rely on agents to remember the policy without templates.
- Affects: `new-workspace`, `project-init`, `init-python-project`, `research-project-memory` templates/references, README.md, AGENTS.md, CLAUDE.md.
- Revisit when: concurrent sync races become common enough to require automatic lockfile-hash stage env naming or a wrapper script.
- Certainty: user-stated

## DEC-029 - Make Root Skill Discovery Budget-Resilient

- Date: 2026-05-20
- Decision: Treat `ml-research-router` as the explicit entry point when users describe an ML research workflow but do not know which skill to invoke, and give it a local `references/skill-index.md` so it can route even when Claude Code or Codex truncates leaf skill descriptions.
- Why: Full `ml-research-skills` installs contain enough leaf skills that global skill-listing budgets can drop lower-frequency descriptions. Users should not have to memorize skill names; the root router should use local routing data to choose a domain router or high-signal leaf.
- Alternatives considered: require users to point-name leaf skills; keep increasing `skillListingBudgetFraction`; rely only on each leaf skill description being present in every session.
- Affects: `skills/ml-research-router/`, `tests/routing-evals.json`, README.md, AGENTS.md, CLAUDE.md, `memory/project-conventions.md`, `memory/fact-index.yaml`.
- Revisit when: runtime skill listing no longer drops leaf descriptions or the number of installed skills changes the router/index maintenance cost.
- Certainty: user-stated

## DEC-030 - Make Full Skill Bundle Project-Local

- Date: 2026-05-25
- Decision: Stop recommending the full `ml-research-skills` bundle as a default global install. The recommended global install is the thin `ml-research-bootstrap` skill, with optional `project-init`; install the full bundle only inside initialized ML research projects or for maintainer/debug validation of this skill repo.
- Why: The 74-skill ML research lifecycle bundle is too domain-specific for ordinary software projects and can interfere with Codex/Claude Code's non-ML behavior. Inside real ML research projects, local installation ties the bundle to project memory, conventions, worktrees, and evidence state, making the system more useful than a global blanket install.
- Alternatives considered: keep full global install as the default; rely only on `ml-research-router` boundaries; reduce the skill collection size; require users to manually remember which individual skills to install.
- Affects: `skills/ml-research-bootstrap/`, `skills/ml-research-router/`, `skills/project-ops-router/`, README.md, AGENTS.md, CLAUDE.md, `taxonomy/skill-index.yaml`, `tests/routing-evals.json`, `memory/project-conventions.md`, `memory/fact-index.yaml`.
- Revisit when: agent runtimes support first-class project-local skill activation with an explicit profile/manifest, or when `npx skills` supports a documented bootstrap/full profile split.
- Certainty: user-stated

## DEC-031 - Treat Project Profiles As Skill-Matrix Boundaries

- Date: 2026-05-26
- Decision: Add a profile registry under `profiles/` so project type becomes the first-class install and routing boundary. The current active production profile remains `ml-research`; draft profiles capture `core-ops`, `paper-reading`, `research-distillation`, and `automation` extraction targets for a future multi-repo skill matrix.
- Why: The user's goal has expanded from a single ML research skill collection to a portable, extensible Skill OS for work, learning, research, and automation. Profiles let each project load the right pack without relying on one global skill list, and they preserve migration paths across Codex, Claude Code, and future agent runtimes.
- Alternatives considered: keep adding skills only to one repo; create separate repos immediately without a shared profile schema; rely on runtime-specific skill metadata for selection.
- Affects: `profiles/`, `scripts/validate_skill_taxonomy.py`, README.md, AGENTS.md, CLAUDE.md, `memory/project-conventions.md`, `memory/fact-index.yaml`.
- Revisit when: the first non-ML domain pack is split into its own repository or when a shared `skill-kernel` repo is created.
- Certainty: user-stated

## DEC-032 - Keep The Skill Matrix Agent-Neutral And Schema-Validated

- Date: 2026-05-26
- Decision: Record the multi-repo Skill OS direction in `docs/design/skill-matrix.md` and strengthen `validate_skill_taxonomy.py` so profile status, scope, install policy, entrypoints, routers, future repos, gaps, and profile skill references are mechanically checked.
- Why: Profiles should be architecture, not prose. The system needs to remain portable across Codex, Claude Code, and future agents, and future repo splits need a stable profile contract before code or docs move.
- Alternatives considered: rely only on `profiles/README.md`; split repos immediately; defer schema validation until after extraction.
- Affects: `docs/design/skill-matrix.md`, `profiles/`, `scripts/validate_skill_taxonomy.py`, README.md, `memory/`.
- Revisit when: profile-level routing evals or an independent `skill-kernel` repo are added.
- Certainty: user-stated

## DEC-033 - Test Profile Selection Before Leaf-Skill Routing

- Date: 2026-05-26
- Decision: Add `tests/profile-routing-evals.json` and validate it in `scripts/validate_skill_taxonomy.py` so profile selection examples are checked separately from leaf-skill routing examples.
- Why: The skill-matrix architecture needs agents to choose the right project profile before invoking routers or leaf skills. Without profile-level evals, future runtime adapters could regress to the old flat-list behavior even if leaf-skill routing remains valid.
- Alternatives considered: encode profile examples only in prose; overload `tests/routing-evals.json` with mixed profile and skill targets; wait for an executable routing harness before writing fixtures.
- Affects: `tests/profile-routing-evals.json`, `scripts/validate_skill_taxonomy.py`, `profiles/README.md`, README.md, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: a profile-routing harness can execute these prompts against actual Codex/Claude/runtime choices.
- Certainty: user-stated

## DEC-034 - Score Profile Routing Through Explicit Prediction Artifacts

- Date: 2026-05-26
- Decision: Add `scripts/score_profile_routing.py` as a lightweight harness that scores explicit prediction JSON files against `tests/profile-routing-evals.json`, rather than pretending profile selection can be validated without capturing runtime/agent choices.
- Why: The profile-first Skill OS needs an executable regression loop before runtime adapters exist. A prediction-artifact format keeps Codex, Claude Code, and future runtimes comparable while preserving the agent-neutral YAML/JSON source of truth.
- Alternatives considered: leave profile evals as structural fixtures only; build a runtime-specific adapter immediately; fold profile scoring into `validate_skill_taxonomy.py`.
- Affects: `scripts/score_profile_routing.py`, `tests/test_profile_routing_harness.py`, `tests/profile-routing-evals.json`, README.md, AGENTS.md, CLAUDE.md, `profiles/README.md`, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: actual Codex/Claude profile-choice adapters exist and can write prediction files automatically.
- Certainty: observed

## DEC-035 - Incubate Research Distillation As Profile-Local Artifacts First

- Date: 2026-05-26
- Decision: Add `profiles/research-distillation/` with distillation-run, pattern-card, and skill-proposal templates plus examples, and register those paths under `profiles/profile-index.yaml` `artifacts`.
- Why: The user wants skills to distill research, learning, life, strong people, strong projects, and strong papers. That workflow is central to the broader Skill OS, but it should be trialed as portable profile assets before creating a standalone skill or splitting `research-distillation-skills`.
- Alternatives considered: create a full new leaf skill immediately; keep the workflow only in `docs/design/skill-matrix.md`; wait for `skill-kernel` before adding artifacts.
- Affects: `profiles/research-distillation/`, `profiles/profile-index.yaml`, `scripts/validate_skill_taxonomy.py`, `tests/test_research_distillation_assets.py`, README.md, AGENTS.md, CLAUDE.md, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: satisfied by DEC-037; the next question is whether the combined workflow-contract proposal should become a standalone skill, repo-local patch set, or skill-kernel schema rule.
- Certainty: user-stated

## DEC-036 - Use ByteDance UI-TARS As The First Agent-RL Distillation Trial

- Date: 2026-05-26
- Decision: Select ByteDance UI-TARS as the first real public-source `research-distillation` trial and distill it into two pattern cards plus one skill proposal.
- Why: UI-TARS is a domestic big-company public project that combines GUI agents, action interfaces, and RL/trajectory-driven improvement. Its public repo, official ByteDance Seed blog, and paper metadata expose transferable workflow patterns without needing private source material.
- Alternatives considered: Qwen-Agent, other Alibaba/Qwen agent repos, and waiting for a second source before creating any real trial.
- Affects: `profiles/research-distillation/examples/ui-tars-1-5/`, `profiles/profile-index.yaml`, `tests/test_research_distillation_assets.py`, README.md, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: a second agent+RL repo is distilled and the system can compare whether `agent-action-contract-reviewer` deserves a standalone skill.
- Certainty: observed

## DEC-037 - Use Tongyi DeepResearch As The Second Agent-RL Comparison Source

- Date: 2026-05-26
- Decision: Select Alibaba / Tongyi DeepResearch as the second real public-source `research-distillation` trial and compare it with the UI-TARS trial before creating any standalone agent-contract skill.
- Why: Tongyi DeepResearch is a domestic big-company web/search agent project whose public repo and official blog expose a different agent-control problem from UI-TARS: staged data-to-RL training, source/evidence depth, and light/heavy inference modes rather than GUI action execution. The comparison shows that `agent-action-contract-reviewer` is too narrow as a first standalone skill; the next artifact should be a broader `agent-workflow-contract-planner` proposal that covers both action contracts and mode/evidence contracts.
- Alternatives considered: Qwen-Agent, Trinity-RFT, another ByteDance agent repo, or immediately implementing `agent-action-contract-reviewer` from the UI-TARS trial.
- Affects: `profiles/research-distillation/examples/tongyi-deep-research/`, `profiles/profile-index.yaml`, `tests/test_research_distillation_assets.py`, README.md, `profiles/README.md`, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: the combined profile-local proposal clarifies whether the capability should become a new skill, patches to existing routers/skills, or a future `skill-kernel` schema rule.
- Certainty: observed

## DEC-038 - Incubate Agent Workflow Contracts Before Creating A Skill

- Date: 2026-05-26
- Decision: Add `agent-workflow-contract-planner` as a profile-local proposal that merges the UI-TARS action-contract lane and the Tongyi DeepResearch evidence-depth/mode lane, rather than creating a standalone skill immediately.
- Why: The two public trials show one shared control problem: before an agent loop starts, it should declare what it may mutate, how deep it should research, what evidence it must preserve, and when it stops. A proposal plus template/evals gives a lower-risk validation step than adding another cross-domain skill prematurely.
- Alternatives considered: implement `agent-action-contract-reviewer` directly; implement `deep-research-agent-evaluator` directly; patch only existing routers; wait for a future `skill-kernel` repo before recording the schema.
- Affects: `profiles/research-distillation/examples/agent-workflow-contract-planner-proposal.md`, `profiles/profile-index.yaml`, `tests/test_research_distillation_assets.py`, README.md, `profiles/README.md`, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: the workflow-contract template and routing evals show whether this should become a standalone skill, router patches, or a future `skill-kernel` schema.
- Certainty: observed

## DEC-039 - Keep Workflow Contracts Profile-Local After Real-Task Trials

- Date: 2026-05-26
- Decision: Do not scaffold `agent-workflow-contract-planner` as a standalone skill yet; keep it as a profile-local template, lane evals, and filled real-task trials while using the result as input to a future `skill-kernel` schema.
- Why: The automation trial is already owned by `project-ops-router`, `safe-git-ops`, validators, and `project-push`; the research-distillation trial is already owned by `discovery-router`, reference skills, `skill-system-auditor`, and `memory-publication-auditor` for private-derived sources. The workflow contract adds value as a portable preflight schema, but it does not yet own enough execution behavior to justify a new leaf skill.
- Alternatives considered: create the standalone skill now; fold the template directly into `safe-git-ops` and discovery skills; drop the contract after the trials.
- Affects: `profiles/research-distillation/examples/workflow-contract-trials/`, `profiles/profile-index.yaml`, `tests/test_research_distillation_assets.py`, README.md, `profiles/README.md`, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: repeated live sessions miss lane selection or existing routers cannot cleanly own the mutation/evidence boundary.
- Certainty: observed

## DEC-040 - Seed Skill Kernel As A Portable Schema

- Date: 2026-05-26
- Decision: Add `schemas/skill-kernel/` with a minimum JSON schema, a research-distillation workflow-contract example, validator coverage, and focused unit tests before splitting any profile into a separate repo.
- Why: The broader Skill OS needs an agent-neutral contract that can carry profile identity, routing, install policy, lane contracts, validation gates, memory policy, adapter metadata, and promotion gates without making Codex, Claude Code, or any single repo the only source of truth.
- Alternatives considered: keep the kernel as prose in `docs/design/skill-matrix.md`; add runtime-specific manifests first; wait until a new repo exists before defining the schema.
- Affects: `schemas/skill-kernel/`, `scripts/validate_skill_taxonomy.py`, `tests/test_skill_kernel_schema.py`, `profiles/profile-index.yaml`, README.md, AGENTS.md, CLAUDE.md, `profiles/README.md`, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: at least one `core-ops` kernel and one non-ML or research-distillation kernel have been instantiated from the schema.
- Certainty: observed

## DEC-041 - Validate Skill Kernel Across Ops And Reading Profiles

- Date: 2026-05-26
- Decision: Instantiate the skill-kernel schema for `core-ops` and `paper-reading` in addition to the existing research-distillation workflow-contract example, without adding profile-specific schema fields.
- Why: The kernel must support action/combined-heavy operational workflows and evidence-heavy reading workflows before repo splitting. The two new examples show the current schema can represent cross-domain ops and reading-only profiles while preserving install, routing, validation, memory, adapter, and privacy boundaries.
- Alternatives considered: instantiate only `core-ops`; add schema fields before a second example; skip `paper-reading` until a separate repo exists.
- Affects: `schemas/skill-kernel/examples/core-ops.kernel.json`, `schemas/skill-kernel/examples/paper-reading.kernel.json`, `schemas/skill-kernel/README.md`, `tests/test_skill_kernel_schema.py`, `profiles/profile-index.yaml`, README.md, `profiles/README.md`, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: a dry-run adapter/export step is designed from kernel examples into Codex/Claude/runtime metadata.
- Certainty: observed

## DEC-042 - Keep Runtime Adapter Export As A Dry-Run Boundary

- Date: 2026-05-26
- Decision: Add `scripts/export_skill_kernel_adapters.py` as a dry-run exporter that derives Codex, Claude Code, Cursor, and generic-agent metadata from skill-kernel examples while marking outputs `dry_run: true`, `installable: false`, and `source_of_truth: kernel`.
- Why: The project needs to test whether portable kernels can map into runtime-shaped metadata before any repo split, but runtime metadata must not become the only copy of workflow logic.
- Alternatives considered: create installable runtime manifests immediately; fold adapter generation into `validate_skill_taxonomy.py`; keep the adapter step as prose-only design notes.
- Affects: `scripts/export_skill_kernel_adapters.py`, `tests/test_skill_kernel_adapter_export.py`, `schemas/skill-kernel/README.md`, README.md, AGENTS.md, CLAUDE.md, `scripts/README.md`, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: dry-run output is compared against real Codex/Claude install metadata expectations.
- Certainty: observed

## DEC-043 - Anchor Runtime Adapter Contracts In Observed SKILL.md Surfaces

- Date: 2026-05-26
- Decision: Add `schemas/skill-kernel/runtime-adapter-contracts.json` and extend dry-run adapter output with `runtime_contract` plus `runtime_projection`, mapping kernels into preview `SKILL.md` frontmatter while keeping workflow, validation, memory, install policy, and promotion fields docs-only.
- Why: Local Codex and Claude Code skill installs show the real runtime-facing contract is a thin skill directory with `SKILL.md` frontmatter (`name`, `description`) plus optional resources. The portable kernel can inform that surface, but should not copy complex workflow truth into runtime metadata.
- Alternatives considered: generate installable manifests immediately; put all kernel fields into runtime frontmatter; leave Codex/Claude expectations implicit in tests only.
- Affects: `schemas/skill-kernel/runtime-adapter-contracts.json`, `scripts/export_skill_kernel_adapters.py`, `tests/test_skill_kernel_adapter_export.py`, `schemas/skill-kernel/README.md`, README.md, `profiles/README.md`, `scripts/README.md`, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: generated preview `SKILL.md` fixtures are smoke-tested in isolated runtime-like skill roots.
- Certainty: observed

## DEC-044 - Gate Installable Adapters Behind Preview Fixture Smoke Tests

- Date: 2026-05-27
- Decision: Extend `scripts/export_skill_kernel_adapters.py` with `--preview-skill-root` so runtime projections generate preview-only skill directories under `<root>/<runtime>/<skill-name>/`, with `SKILL.md`, optional interface metadata, `preview-manifest.json`, and built-in smoke checks.
- Why: The next risk is not JSON projection shape; it is whether generated skill-directory surfaces remain well formed before real Codex/Claude runtime trigger tests. A temporary preview root exercises the filesystem shape without making the output installable or authoritative.
- Alternatives considered: commit generated fixtures into the repo; create installable manifests immediately; rely only on adapter JSON tests.
- Affects: `scripts/export_skill_kernel_adapters.py`, `tests/test_skill_kernel_adapter_export.py`, `schemas/skill-kernel/README.md`, README.md, `profiles/README.md`, `scripts/README.md`, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: Codex/Claude runtime trigger behavior is captured from generated preview skill roots.
- Certainty: observed

## DEC-045 - Resolve Core-Ops Runtime Semantics Before Installable Adapters

- Date: 2026-05-27
- Decision: Do not create installable adapter manifests yet. First resolve whether `core-ops` should be an isolated profile entrypoint, a stronger routing entrypoint, or an intentional delegator to mature leaf/utility skills when the full shared skill root is visible.
- Why: Runtime capture showed generated preview skills are visible to Codex and Claude Code prompt surfaces, and Codex selects the `paper-reading` and `research-distillation-workflow-contract` preview skills for matching prompts. For general maintenance, Codex saw `core-ops` but selected `project-ops-router`, `safe-git-ops`, and `update-docs`, so the core-ops adapter contract is not yet behaviorally settled.
- Alternatives considered: create installable manifests immediately; treat prompt visibility as enough; make `core-ops` override mature leaf skills without a dedicated profile-first test.
- Affects: `schemas/skill-kernel/runtime-trigger-capture-2026-05-27.json`, `schemas/skill-kernel/runtime-adapter-contracts.json`, `tests/test_skill_kernel_adapter_export.py`, `profiles/README.md`, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: ACT-060 decides and tests the intended `core-ops` behavior.
- Certainty: observed

## DEC-046 - Treat Core-Ops As A Profile-First Entrypoint And Full-Root Delegator

- Date: 2026-05-27
- Decision: Encode `core-ops` runtime selection as `profile-first-entrypoint`: it should be selected when installed as the isolated operational profile or when the runtime/prompt enforces profile-first routing, but it should not be forced to override mature owner skills when the full shared skill root is visible.
- Why: ACT-060 Codex captures showed three distinct behaviors: full shared root without profile-first instruction routed to `project-ops-router`, `safe-git-ops`, and `update-docs`; explicit profile-first routing selected `core-ops` before delegating to leaf skills; isolated `core-ops` install selected `core-ops` directly. This makes delegation semantics more accurate than strengthening the description until it competes with specialized skills.
- Alternatives considered: make `core-ops` a direct leaf that always wins; keep installability blocked; leave the semantics only in prose outside the kernel.
- Affects: `schemas/skill-kernel/skill-kernel.schema.json`, `schemas/skill-kernel/examples/*.kernel.json`, `schemas/skill-kernel/core-ops-runtime-semantics-2026-05-27.json`, `scripts/export_skill_kernel_adapters.py`, `tests/test_skill_kernel_schema.py`, `tests/test_skill_kernel_adapter_export.py`, README.md, `profiles/README.md`, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: installable adapter manifests are prototyped or a runtime supports first-class profile selection without prompt hints.
- Certainty: observed

## DEC-047 - Keep Installable Manifests Review-Gated And Kernel-Authored

- Date: 2026-05-27
- Decision: Prototype installable adapter manifests with `--installable-manifest-root`, but keep them review-gated (`manual_review_required: true`, `safe_to_install_automatically: false`) and generated from the kernel rather than making them a runtime-owned source of workflow truth.
- Why: The manifest is useful as the next artifact between preview `SKILL.md` fixtures and real runtime install exercises, but automatic installation would be premature until the final runtime path proves it preserves `selection_semantics`, especially `core-ops` profile-first activation and full-root delegation.
- Alternatives considered: write real installable skill directories now; commit generated manifest outputs; copy workflow, memory, validation, install policy, and promotion blocks into the manifest as authoritative fields.
- Affects: `scripts/export_skill_kernel_adapters.py`, `tests/test_skill_kernel_adapter_export.py`, `schemas/skill-kernel/README.md`, README.md, AGENTS.md, CLAUDE.md, `profiles/README.md`, `scripts/README.md`, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: ACT-062 exercises the manifest prototypes in a temporary runtime or session-only skill root without modifying global installs.
- Certainty: observed

## DEC-048 - Exercise Manifests Only In Session-Only Roots

- Date: 2026-05-27
- Decision: Add `--exercise-skill-root` only as a paired `--installable-manifest-root` exercise: re-read generated manifests, write session-only runtime-like skill directories, refuse known global skill roots, and record `global_install_modified: false`; do not enable real install automation yet.
- Why: This proves the review-gated manifests carry enough information to reconstruct runtime skill shape while preserving kernel source of truth, manual review, no-auto-install policy, and `selection_semantics`.
- Alternatives considered: copy directly into global runtime skill roots; infer last-mile behavior from manifest JSON only; enable installer automation immediately.
- Affects: `scripts/export_skill_kernel_adapters.py`, `tests/test_skill_kernel_adapter_export.py`, `schemas/skill-kernel/README.md`, README.md, AGENTS.md, CLAUDE.md, `profiles/README.md`, `scripts/README.md`, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: ACT-063 captures real runtime prompt-surface behavior from manifest-exercised session-only roots.
- Certainty: observed

## DEC-049 - Gate Real Install Automation On Reviewed Handoff Contracts

- Date: 2026-05-27
- Decision: Treat the manifest-exercise runtime capture as sufficient to move from session-only validation to designing a reviewed install/repo-split handoff contract, but keep automatic global installation disabled until that contract defines target roots, profile choice, source-of-truth, manual review, and rollback behavior.
- Why: ACT-063 shows manifest-exercised roots are prompt-visible in Codex and Claude Code without global mutation. Codex selects the exercised skills in isolated session-only contexts, while full repo-root maintenance still correctly delegates to mature project-local owner skills. This supports profile-first installability, but not blind global installation.
- Alternatives considered: enable automatic global install now; require more JSON-only adapter checks before runtime planning; block all install planning until Claude model-choice capture succeeds.
- Affects: `schemas/skill-kernel/manifest-exercise-runtime-capture-2026-05-27.json`, `schemas/skill-kernel/runtime-adapter-contracts.json`, `scripts/export_skill_kernel_adapters.py`, `tests/test_skill_kernel_adapter_export.py`, `schemas/skill-kernel/README.md`, README.md, `profiles/README.md`, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: ACT-064 defines the reviewed install or repo-split handoff contract.
- Certainty: observed

## DEC-050 - Keep Install And Repo Split Handoffs Contract-Only Until A Plan Validator Exists

- Date: 2026-05-27
- Decision: Add an active reviewed install/repo-split handoff contract under `schemas/skill-kernel/`, but keep it `contract-only`: no real installer is authorized, runtime writes without review are forbidden, and global roots may not be touched without explicit user request and rollback.
- Why: ACT-063 proved session-only prompt-surface behavior, but real installation and repo splitting introduce new risks: wrong target root, accidental full-bundle global install, adapter output becoming source truth, private path leakage, and no rollback. A contract converts those risks into explicit gates before automation exists.
- Alternatives considered: implement installer automation immediately; keep the boundary as prose in the design doc; block all next steps until another runtime capture.
- Affects: `schemas/skill-kernel/install-handoff-contract.schema.json`, `schemas/skill-kernel/install-handoff-contract-2026-05-27.json`, `profiles/profile-index.yaml`, `scripts/validate_skill_taxonomy.py`, `tests/test_skill_kernel_schema.py`, README.md, AGENTS.md, CLAUDE.md, `profiles/README.md`, `schemas/skill-kernel/README.md`, `scripts/README.md`, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: ACT-065 implements a non-mutating install-plan validator that can consume the contract and generated manifest indexes.
- Certainty: observed

## DEC-051 - Validate Install Plans Before Any Runtime Write Command

- Date: 2026-05-27
- Decision: Add a non-mutating install/repo-split plan validator and schema before adding any command that writes runtime skill files or scaffolds split repositories.
- Why: The handoff contract made the review boundary explicit, but future installer or repo-split code still needs a mechanical preflight that checks target mode, profile/runtime, source-of-truth paths, generated manifest alignment, required review gates, validation commands, global-root policy, privacy audit, forbidden-action acknowledgement, and rollback before any mutation is possible.
- Alternatives considered: implement a real installer with inline checks; rely on the JSON handoff contract and manual review only; keep validator behavior inside `validate_skill_taxonomy.py`.
- Affects: `schemas/skill-kernel/install-plan.schema.json`, `scripts/validate_install_handoff_plan.py`, `tests/test_install_handoff_plan_validator.py`, `scripts/validate_skill_taxonomy.py`, `profiles/profile-index.yaml`, README.md, AGENTS.md, CLAUDE.md, `profiles/README.md`, `schemas/skill-kernel/README.md`, `scripts/README.md`, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: ACT-066 exercises the validator on concrete `core-ops` project-local install and repo-split plan fixtures before implementing any writer.
- Certainty: observed

## DEC-052 - Anchor The Install/Repo-Split Validator With Checked Plan Fixtures

- Date: 2026-05-27
- Decision: Check three concrete `core-ops` install/repo-split plan fixtures into `schemas/skill-kernel/examples/install-plans/` and re-run the validator on them through `tests/test_install_plan_fixtures.py`. Two fixtures (project-local Codex install and `generic-agent` repo split) must pass shape while remaining non-executable under the active contract; a third negative fixture drops the `no-credential-or-private-path-leakage` gate and must be rejected.
- Why: The handoff contract and abstract validator unit tests were not enough to prove the reviewed install/repo-split shape works on real plans. Concrete fixtures pin the review pattern, prevent regressions when contract or manifest shape evolves, and demonstrate that the validator handles both the `project-local-profile-install` and `repo-split-handoff` modes without writing runtime files.
- Alternatives considered: keep generating ephemeral plans only inside unit tests; defer fixture work until the real installer is implemented; bundle fixtures with the (future) split repo instead of the source repo.
- Affects: `schemas/skill-kernel/examples/install-plans/core-ops-project-local-install.plan.json`, `schemas/skill-kernel/examples/install-plans/core-ops-repo-split.plan.json`, `schemas/skill-kernel/examples/install-plans/core-ops-rejected-repo-split-missing-leakage-gate.plan.json`, `tests/test_install_plan_fixtures.py`, `schemas/skill-kernel/README.md`, CLAUDE.md, `memory/`.
- Revisit when: a real installer or repo-split writer is implemented and post-write checks need their own fixture set, or when contract review gates change.
- Certainty: observed

## DEC-053 - Add A Read-Only Install Writer Preview Before Real Installer Code

- Date: 2026-05-27
- Decision: Ship `scripts/preview_install_writer.py` plus `schemas/skill-kernel/write-actions.schema.json` as the next gate after the install-plan validator and plan fixtures. The preview consumes a passing project-local install plan and enumerates the exact list of write actions (create-directory, write-skill-markdown, write-interface-metadata) the future installer would emit, complete with sha256 content hashes, byte counts, and a rollback record template — without ever writing under target_root. Repo-split and other modes are explicitly unsupported by the preview for now.
- Why: Going straight from validator to real installer would skip the chance to verify the exact write shape, content hashes, and rollback surface in a read-only artifact. The preview lets the future installer be a thin wrapper that executes the same action list under explicit authorization, and it lets reviewers diff candidate write actions before any mutation happens.
- Alternatives considered: jump directly from validator to a writer with `--dry-run` flag; reuse `--exercise-skill-root` against the plan's target_root (wrong — exercise-skill-root refuses non-tmp roots and is session-only by design); design the installer interface as docs only without a runnable script.
- Affects: `scripts/preview_install_writer.py`, `schemas/skill-kernel/write-actions.schema.json`, `tests/test_install_writer_preview.py`, `schemas/skill-kernel/README.md`, CLAUDE.md, AGENTS.md, `memory/`.
- Revisit when: ACT-067 ships a real installer that consumes the same write-actions shape, when repo-split preview is added, or when the action kinds need to extend beyond the current three.
- Certainty: observed

## DEC-054 - Anchor Repo Split With A Programmatic Inventory And Privacy Audit

- Date: 2026-05-27
- Decision: Generate `core-ops` repo-split source inventory and privacy audit through `scripts/inventory_profile_for_split.py` (with `schemas/skill-kernel/repo-split-inventory.schema.json` and `schemas/skill-kernel/repo-split-privacy-audit.schema.json`), and check the resulting artifacts into `schemas/skill-kernel/repo-split/` before any repo-split scaffolder is written. The privacy audit must report `status: passed` (zero hits) over every file the inventory marks `include_in_split: true` before any destination repo is scaffolded.
- Why: The repo-split handoff contract requires a source inventory and publication audit as preconditions. Doing this with a script (instead of by hand) keeps the inventory in sync with the kernel, makes drift visible through tests, and produces an auditable artifact that a reviewer can diff before authorizing a real split. Privacy patterns include absolute home paths, concrete sidecar task ids, SSH keys, AWS / GitHub / Anthropic token shapes, and personal institutional emails; documented placeholder paths like `.agent/sidecars/<task-id>/` are intentionally not matched because they describe a public convention, not a private artifact.
- Alternatives considered: hand-write the inventory once; skip the audit and rely on contract acknowledgement only; use `grep` per release.
- Affects: `scripts/inventory_profile_for_split.py`, `schemas/skill-kernel/repo-split-inventory.schema.json`, `schemas/skill-kernel/repo-split-privacy-audit.schema.json`, `schemas/skill-kernel/repo-split/core-ops-source-inventory-2026-05-27.json`, `schemas/skill-kernel/repo-split/core-ops-privacy-audit-2026-05-27.json`, `tests/test_repo_split_inventory.py`, `schemas/skill-kernel/README.md`, CLAUDE.md, AGENTS.md, `memory/`.
- Revisit when: a repo-split preview consumes this inventory (ACT-069), when another profile is prepared for split, or when new privacy patterns must be added.
- Certainty: observed

## DEC-055 - Repo-Split Preview Composes Copy Actions From The Inventory

- Date: 2026-05-27
- Decision: Ship `scripts/preview_repo_split_writer.py` as the repo-split counterpart of the install writer preview. It consumes a passing `repo-split-handoff` plan plus the generated manifest index, auto-locates the profile's source inventory and privacy audit, and emits a write-actions document of copy-file, create-directory, write-profile-index-slice, and post-write-check actions for the future scaffolder. The preview refuses non-`repo-split-handoff` modes, rejected plans, and profiles whose privacy audit is not `status: passed`. It never writes under `target_root`.
- Why: A real repo-split scaffolder must execute many independent copy actions plus a profile-index slice on a destination repo, and reviewers need a diffable artifact before any of those copies run. Sharing the action shape with the project-local preview (same `write-actions.schema.json`, extended with `copy-file`, `write-profile-index-slice`, `post-write-check` kinds) lets the future scaffolder be a thin executor of preview output.
- Alternatives considered: postpone the repo-split preview and design the scaffolder directly; emit a free-form Markdown plan instead of structured JSON; reuse the existing exercise writer (wrong — exercise writer is session-only and writes runtime skill dirs, not destination repo scaffolds).
- Affects: `scripts/preview_repo_split_writer.py`, `schemas/skill-kernel/write-actions.schema.json`, `tests/test_repo_split_writer_preview.py`, `schemas/skill-kernel/README.md`, CLAUDE.md, AGENTS.md, `memory/`.
- Revisit when: a real scaffolder consumes the same write-actions shape and writes to a destination repo, or when the destination action set must extend beyond copies + profile-index slice.
- Certainty: observed

## DEC-056 - Extend Repo-Split Review Chain To All Draft Profiles

- Date: 2026-05-28
- Decision: Generate source inventory, privacy audit, and repo-split plan fixtures for every draft profile slated for future extraction (`paper-reading`, `research-distillation` in addition to `core-ops`), and parametrize the inventory and repo-split-preview tests over all three. The audit must report `status: passed` (zero hits) for each profile before its plan fixture is checked in.
- Why: The review chain is only useful if it covers every profile we plan to split. Anchoring inventories, audits, plan fixtures, and tests across all three profiles makes drift visible early and gives reviewers a concrete diff per profile before any scaffolder runs. The `research-distillation` profile name (`research-distillation`) differs from its kernel id (`research-distillation-workflow-contract`); the plan's `profile` field tracks the profile name (matched against `routing_hints.profile_name`), while `requested_manifests[].kernel_id` tracks the kernel id (matched against the manifest index entry).
- Alternatives considered: cover only `core-ops` until a real scaffolder ships; auto-discover profiles in the preview without checked-in fixtures (loses reviewer diff).
- Affects: `schemas/skill-kernel/repo-split/paper-reading-source-inventory-2026-05-28.json`, `schemas/skill-kernel/repo-split/paper-reading-privacy-audit-2026-05-28.json`, `schemas/skill-kernel/repo-split/research-distillation-source-inventory-2026-05-28.json`, `schemas/skill-kernel/repo-split/research-distillation-privacy-audit-2026-05-28.json`, `schemas/skill-kernel/examples/install-plans/paper-reading-repo-split.plan.json`, `schemas/skill-kernel/examples/install-plans/research-distillation-repo-split.plan.json`, `tests/test_repo_split_inventory.py`, `tests/test_repo_split_writer_preview.py`, `memory/`.
- Revisit when: the `automation` profile gains a kernel and needs the same coverage, when a real scaffolder ships, or when a profile's required-skill set changes.
- Certainty: observed

## DEC-057 - Real Installer And Scaffolder Ship Disabled-By-Contract

- Date: 2026-05-28
- Decision: Ship `scripts/apply_install_plan.py` (project-local installer) and `scripts/apply_repo_split.py` (repo-split scaffolder) as the executable end of the review chain, but keep them disabled by the active handoff contract. Both scripts re-run the validator, re-use the matching preview, and perform real writes only when (1) `automation_policy.real_installer_authorized` is true on the active contract, (2) the plan mode is `allowed_now: true`, and (3) the caller passes `--execute`. Both scripts independently refuse any target under known global skill roots regardless of contract state. The drafted contract revision that would authorize them lives at `schemas/skill-kernel/proposed-revisions/install-handoff-contract-2026-05-28.proposal.md` and is not applied.
- Why: Shipping the executor disabled-by-contract makes the last mile of the Skill OS goal real and testable today: refusal paths are tested under the live contract; happy paths are tested under a synthetic authorized contract in a tmp dir. The remaining authorization decision is then a single, reversible flip the user can review and apply explicitly, instead of a multi-file code change.
- Alternatives considered: ship the executor enabled (violates the contract's review chain); design the executor as docs only (misses regression coverage); flip the active contract automatically (skips human confirmation).
- Affects: `scripts/apply_install_plan.py`, `scripts/apply_repo_split.py`, `tests/test_apply_install_plan.py`, `schemas/skill-kernel/proposed-revisions/install-handoff-contract-2026-05-28.proposal.md`, `schemas/skill-kernel/README.md`, CLAUDE.md, AGENTS.md, `memory/`.
- Revisit when: the user applies the proposal and authorizes real writes, or when post-write checks need a separate gate before the rollback record format is locked.
- Certainty: observed

## DEC-058 - Apply The 2026-05-28 Contract Revision To Authorize Reviewed-Plan Writes

- Date: 2026-05-28
- Decision: Apply the reviewed proposal at `schemas/skill-kernel/proposed-revisions/install-handoff-contract-2026-05-28.proposal.md`. The active install/repo-split handoff contract is now `schemas/skill-kernel/install-handoff-contract-2026-05-28.json` (`status: active`, `implementation_status: reviewed-execute-enabled`, `automation_policy.real_installer_authorized: true`). The two reviewed-plan modes `project-local-profile-install` and `repo-split-handoff` carry `allowed_now: true`; the two global-root modes (`global-bootstrap-install`, `maintainer-debug-global-install`) remain `allowed_now: false` and require explicit per-invocation user request. The 2026-05-27 contract is preserved with `status: superseded` and `superseded_by` annotation, and is consumed by refusal regression tests. Polish: `apply_install_plan.py` now renders `SKILL.md` through `render_installed_skill_markdown` instead of the session-exercise renderer, and `apply_repo_split.py` writes a real YAML profile-index slice instead of a placeholder note.
- Why: All read-only review artifacts and applier code were in place and tested; the user explicitly authorized the flip after a sandbox demo and after acknowledging that global-root writes stay unauthorized by default and that `--rollback-record` will be used for every real run. Splitting the contract into an active 2026-05-28 file and a frozen 2026-05-27 file lets refusal regression tests survive the flip and gives reviewers a side-by-side diff.
- Alternatives considered: edit `install-handoff-contract-2026-05-27.json` in place (loses refusal regression coverage and the side-by-side diff); authorize all five target modes (unnecessarily permits global-root writes); skip the polish items and reuse session-exercise text in real installs (semantically wrong and confusing).
- Affects: `schemas/skill-kernel/install-handoff-contract-2026-05-28.json`, `schemas/skill-kernel/install-handoff-contract-2026-05-27.json` (now superseded), `scripts/validate_install_handoff_plan.py`, `scripts/validate_skill_taxonomy.py`, `scripts/apply_install_plan.py`, `scripts/apply_repo_split.py`, `scripts/export_skill_kernel_adapters.py`, `tests/test_skill_kernel_schema.py`, `tests/test_install_handoff_plan_validator.py`, `tests/test_install_plan_fixtures.py`, `tests/test_install_writer_preview.py`, `tests/test_repo_split_writer_preview.py`, `tests/test_apply_install_plan.py`, `profiles/profile-index.yaml`, `README.md`, `schemas/skill-kernel/README.md`, `scripts/README.md`, `docs/design/skill-matrix.md`, `memory/`.
- Revisit when: post-write check infrastructure becomes more than the advisory `post-write-check` action class, or when an `automation` profile or additional draft profile needs the same flip; when a maintainer-debug-global-install per-invocation request is recorded.
- Certainty: observed

## DEC-059 - Restructure Profile Axes To Match The PhD Student Work Matrix

- Date: 2026-05-28
- Decision: Realign the profile matrix on the user's stated work-shape: writing code / running experiments (heavy ML and quick scratchpad) / reading literature / device-storage-network ops / shared cross-domain substrate. Concretely (a) build `automation` kernel and inventory + privacy audit + repo-split plan fixture so it stands as a real splittable profile alongside `core-ops` / `paper-reading` / `research-distillation`; (b) move `remote-project-control` and `run-status-monitor` out of `core-ops` (optional) and make them required members of `automation`; (c) record `depends_on: core-ops` in `automation`'s profile-index entry to document that `automation` reuses git/memory/docs/sidecar substrate rather than reimplementing it; (d) tighten core-ops intent to "owns git/memory/docs/sidecar/validation/workspaces, does NOT own remote/scheduler probe skills". Tests parametrized over all four split-target profiles; sandbox demo with the active 2026-05-28 contract confirms the new `automation` profile splits cleanly into a destination repo with the right skill set.
- Why: The matrix was previously ML-heavy and didn't reflect the user's actual work axes. Remote/runtime/network/storage ops apply to many non-ML folders (reading PDFs, ops work, quick scratchpad experiments); locking those skills into `core-ops` made `core-ops` itself less reusable and made `automation` a no-op draft. The new cut keeps `core-ops` as the pure cross-domain substrate (git, memory, docs, sidecar) and gives `automation` a real ownership boundary around remote-runtime + scheduler probe work. Profiles can now be combined per folder (e.g., `core-ops + automation` for an ops-only folder; `core-ops + paper-reading` for a literature-only folder; `core-ops + paper-reading + automation` for a remote literature workstation).
- Alternatives considered: leave `remote-project-control` / `run-status-monitor` in `core-ops` (keeps `automation` empty and bloats the substrate); merge `automation` into a generic "ops" bucket that also covers all device/storage/network skills (too broad until those skills actually exist); introduce a new `code-engineering` and/or `quick-experiment` profile in the same revision (deferred — it would couple two structural changes; revisit when concrete code-engineering / quick-experiment skills graduate from `ml-research`).
- Affects: `schemas/skill-kernel/examples/automation.kernel.json`, `schemas/skill-kernel/examples/core-ops.kernel.json`, `profiles/profile-index.yaml`, `schemas/skill-kernel/repo-split/automation-source-inventory-2026-05-28.json`, `schemas/skill-kernel/repo-split/automation-privacy-audit-2026-05-28.json`, `schemas/skill-kernel/repo-split/core-ops-source-inventory-2026-05-27.json`, `schemas/skill-kernel/repo-split/core-ops-privacy-audit-2026-05-27.json`, `schemas/skill-kernel/examples/install-plans/automation-repo-split.plan.json`, `tests/test_skill_kernel_schema.py`, `tests/test_skill_kernel_adapter_export.py`, `tests/test_repo_split_inventory.py`, `tests/test_repo_split_writer_preview.py`, `tests/test_apply_install_plan.py`, `memory/`.
- Revisit when: a kernel is built for `global-bootstrap` or `ml-research`, when a `code-engineering` or `quick-experiment` profile is proposed, or when `automation` gains skills addressing the open gaps (credential boundary, storage retention, scheduled runbook).
- Certainty: observed

## DEC-060 - Add Quick-Experiment Profile And Real-Split All Five Profiles Locally

- Date: 2026-05-28
- Decision: After the work-matrix evaluation (ACT-075), add `quick-experiment` as the fifth split-target profile and skip `code-engineering`. Then real-split all five profiles into sibling local repos under `/Users/jieke/Projects/`: `core-ops-skills`, `paper-reading-skills`, `research-distillation-skills`, `automation-skills`, and `quick-experiment-skills`. Each destination repo is `git init`-ed with an initial commit recording the source repo + scaffolder + plan + rollback record paths. No push to GitHub today; pushes are a separate manual action.
- Why: The matrix as deployed (1 source repo) did not match the matrix as designed (multiple repos with a shared substrate). Splitting locally exercises the full chain (`apply_repo_split.py --execute` against the live active 2026-05-28 contract) without crossing the GitHub-push boundary, and surfaces structural issues (kernel naming vs profile naming for `research-distillation`, depends_on chain documentation, slice acceptance checks) that sandbox /tmp demos hide. `quick-experiment` was added because "quick scratchpad experiment" is a real folder-shape the user identified that `ml-research` (74 skills) is too heavy for; `code-engineering` was skipped because only 2 candidate skills are pure general-engineering and `core-ops` already covers them. The five split repos plus the source repo now form the matrix: `core-ops` (12 skills, substrate), `automation` (6 skills, depends_on core-ops), `paper-reading` (11), `research-distillation` (13), `quick-experiment` (9, depends_on core-ops + automation), `ml-research` (74, include_all_repo_skills bundle, remains in source repo).
- Alternatives considered: split each profile in a separate session (slows down validation of the full matrix shape); skip `quick-experiment` and live with `ml-research` for scratchpad work (defeats the work-matrix goal); push all destination repos to GitHub today (premature — review the local splits first).
- Affects: `schemas/skill-kernel/examples/quick-experiment.kernel.json`, `schemas/skill-kernel/repo-split/quick-experiment-*.json`, `schemas/skill-kernel/examples/install-plans/quick-experiment-repo-split.plan.json`, `profiles/profile-index.yaml`, `tests/test_skill_kernel_schema.py`, `tests/test_skill_kernel_adapter_export.py`, `tests/test_repo_split_inventory.py`, `tests/test_repo_split_writer_preview.py`, `.agent/install-plans/<profile>-real-split-rollback.json` × 5, `memory/`.
- Revisit when: the user wants to push any of the five destination repos to GitHub, when a new profile (e.g., `global-bootstrap` kernel or `automation` gap skills) is added, or when the depends_on relationship needs installer-level enforcement.
- Certainty: observed
