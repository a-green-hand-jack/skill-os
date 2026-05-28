# ml-research-skills Source Visibility Board

Track which source surfaces are public, collaborator-visible, or local/private.

| ID | Surface | Path | Tier | Audience | Sync target | Allowed paths | Forbidden paths | Cleanup gate | Audit status | Certainty | Updated |
|---|---|---|---|---|---|---|---|---|---|---|---|
| VIS-001 | public repo | `.` | public-preprint | GitHub users, Codex/Claude Code skill installers | GitHub | `skills/`, `README.md`, `AGENTS.md`, `CLAUDE.md`, `scripts/`, `tests/`, `asset/`, `memory/` | raw session logs, private local paths, credentials, `.agent/sidecars/`, local workstation facts | before push | partial | observed | 2026-05-05 |

## Open Visibility Actions

- Keep `.agent/sidecars/` out of public commits unless the user explicitly decides to publish sanitized sidecar artifacts.
- Store local workstation facts in private memory, not in shared repo memory.
