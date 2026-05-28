#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
validate_skill_taxonomy.py — Taxonomy consistency checks for ml-research-skills.

Checks:
1. Router child consistency: skills named in route-table.md files all exist.
2. expected_path chains: all skills in routing-evals.json expected_path exist.
3. Contrastive-routing skill mentions: all named skills in contrastive-routing.md exist.
4. Memory contract completeness: applies_to, required_facts, always_read verified.
5. skill-index.yaml consistency: all index entries exist; all real skills are indexed.
6. profile-index.yaml consistency: profile schema, artifacts, and skill references are valid.
7. profile-routing-evals.json consistency: profile eval targets reference real profiles and entrypoint skills.
8. skill-kernel schema consistency: portable kernel schema, examples, install handoff contract, and install-plan validator reference real sources.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "skills"
SKILL_NAME_RE = re.compile(r"^[a-z0-9-]+$")
BACKTICK_SKILL_RE = re.compile(r"`([a-z0-9-]+)`")
# Pseudo-values allowed in applies_to that are not real skill names
CONTRACT_APPLIES_TO_KEYWORDS = {"all-skills", "session-start", "any-skill"}
PROFILE_STATUS_VALUES = {"active", "draft", "deprecated"}
PROFILE_SCOPE_VALUES = {"global", "project-local", "cross-domain", "private"}
INSTALL_RECOMMENDED_VALUES = {"global", "project-local", "maintainer-debug", "private"}
REPO_MATRIX_STATUS_VALUES = {"active", "proposed", "private", "deprecated"}
PROFILE_ARTIFACT_FIELDS = {"docs", "templates", "examples"}
TEXT_ARTIFACT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json", ".toml", ".rst"}
PLACEHOLDER_RE = re.compile(r"\{\{([A-Za-z0-9_]+)\}\}")
VALID_PLACEHOLDER_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
KERNEL_REQUIRED_TOP_LEVEL = {
    "schema_version",
    "kernel_id",
    "owner_repo",
    "source_paths",
    "profile",
    "routing",
    "install_policy",
    "skills",
    "workflow_contract",
    "validation",
    "memory",
    "adapters",
    "promotion",
}
KERNEL_LANES = {"action", "evidence", "combined", "no-contract"}
KERNEL_EVIDENCE_MODES = {"none", "light", "standard", "heavy"}
INSTALL_HANDOFF_REQUIRED_MODES = {
    "session-only-exercise",
    "project-local-profile-install",
    "global-bootstrap-install",
    "maintainer-debug-global-install",
    "repo-split-handoff",
}
INSTALL_HANDOFF_REQUIRED_GATES = {
    "target-root-declared",
    "profile-and-runtime-selected",
    "source-of-truth-preserved",
    "selection-semantics-preserved",
    "global-root-policy-checked",
    "manual-review-recorded",
    "rollback-plan-recorded",
    "validation-plan-recorded",
    "privacy-and-publication-audit",
    "no-credential-or-private-path-leakage",
}


@dataclass(frozen=True)
class Issue:
    path: str
    message: str


def _load_yaml(path: Path) -> dict | list | None:
    try:
        import yaml  # type: ignore
    except ImportError:
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _load_json(path: Path) -> dict | list | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _skill_names_in_text(text: str, known: set[str]) -> set[str]:
    """Return backtick-quoted tokens that look like skill names and exist in known."""
    found = set()
    for m in BACKTICK_SKILL_RE.finditer(text):
        candidate = m.group(1)
        if SKILL_NAME_RE.fullmatch(candidate) and candidate in known:
            found.add(candidate)
    return found


def _all_backtick_names(text: str) -> set[str]:
    """Return all backtick-quoted tokens matching skill-name pattern."""
    return {m.group(1) for m in BACKTICK_SKILL_RE.finditer(text) if SKILL_NAME_RE.fullmatch(m.group(1))}


# ---------------------------------------------------------------------------
# Check 1 — Router child consistency
# ---------------------------------------------------------------------------

def validate_router_children(skill_names: set[str]) -> list[Issue]:
    """Every skill named in a route-table.md must exist in skills/."""
    issues: list[Issue] = []
    for skill_dir in sorted(SKILLS_ROOT.iterdir()):
        if not skill_dir.is_dir():
            continue
        route_table = skill_dir / "references" / "route-table.md"
        if not route_table.exists():
            continue
        text = route_table.read_text(encoding="utf-8")
        named = _all_backtick_names(text)
        rel = str(route_table.relative_to(REPO_ROOT))
        for name in sorted(named):
            if name not in skill_names:
                issues.append(Issue(rel, f"references unknown skill `{name}`"))
    return issues


# ---------------------------------------------------------------------------
# Check 2 — expected_path chain consistency
# ---------------------------------------------------------------------------

def validate_expected_paths(skill_names: set[str]) -> list[Issue]:
    """All skills in expected_path arrays in routing-evals.json must exist."""
    evals_path = REPO_ROOT / "tests" / "routing-evals.json"
    if not evals_path.exists():
        return []
    issues: list[Issue] = []
    rel = str(evals_path.relative_to(REPO_ROOT))
    try:
        data = json.loads(evals_path.read_text())
    except json.JSONDecodeError as exc:
        return [Issue(rel, f"invalid JSON: {exc}")]
    for entry in data.get("evals", []):
        eid = entry.get("id", "?")
        path = entry.get("expected_path", [])
        if not isinstance(path, list):
            issues.append(Issue(rel, f"{eid} expected_path must be a list"))
            continue
        for step in path:
            if step not in skill_names:
                issues.append(Issue(rel, f"{eid} expected_path contains unknown skill `{step}`"))
    return issues


# ---------------------------------------------------------------------------
# Check 3 — Contrastive-routing skill mentions
# ---------------------------------------------------------------------------

def validate_contrastive_routing(skill_names: set[str]) -> list[Issue]:
    """Skill names in contrastive-routing.md files must exist."""
    issues: list[Issue] = []
    for skill_dir in sorted(SKILLS_ROOT.iterdir()):
        if not skill_dir.is_dir():
            continue
        cr_file = skill_dir / "references" / "contrastive-routing.md"
        if not cr_file.exists():
            continue
        text = cr_file.read_text(encoding="utf-8")
        named = _all_backtick_names(text)
        rel = str(cr_file.relative_to(REPO_ROOT))
        for name in sorted(named):
            if name not in skill_names:
                issues.append(Issue(rel, f"references unknown skill `{name}`"))
    return issues


# ---------------------------------------------------------------------------
# Check 4 — Memory contract completeness
# ---------------------------------------------------------------------------

def validate_memory_contracts(skill_names: set[str]) -> list[Issue]:
    """
    For each YAML in taxonomy/memory-contracts/:
    - applies_to skills exist
    - required_facts IDs exist in memory/fact-index.yaml
    - always_read files that are not conditional exist on disk
    """
    contracts_dir = REPO_ROOT / "taxonomy" / "memory-contracts"
    if not contracts_dir.exists():
        return []

    # Load known fact IDs
    fact_ids: set[str] = set()
    fact_index_path = REPO_ROOT / "memory" / "fact-index.yaml"
    if fact_index_path.exists():
        data = _load_yaml(fact_index_path)
        if isinstance(data, dict):
            for fact in data.get("facts", []):
                if isinstance(fact, dict) and "id" in fact:
                    fact_ids.add(fact["id"])

    issues: list[Issue] = []
    for contract_file in sorted(contracts_dir.glob("*.yaml")):
        rel = str(contract_file.relative_to(REPO_ROOT))
        data = _load_yaml(contract_file)
        if not isinstance(data, dict):
            issues.append(Issue(rel, "could not parse as YAML mapping"))
            continue

        # applies_to skills exist (skip known pseudo-keywords)
        for skill in data.get("applies_to", []):
            if skill in CONTRACT_APPLIES_TO_KEYWORDS:
                continue
            if skill not in skill_names:
                issues.append(Issue(rel, f"applies_to references unknown skill `{skill}`"))

        # required_facts IDs exist in fact-index.yaml
        if fact_ids:
            for fid in data.get("required_facts", []):
                if fid not in fact_ids:
                    issues.append(Issue(rel, f"required_facts references unknown fact ID `{fid}`"))

        # always_read files exist (skip conditional patterns with spaces like "if ...")
        for read_path in data.get("always_read", []):
            if " " in read_path:
                continue
            full_path = REPO_ROOT / read_path
            if not full_path.exists():
                issues.append(Issue(rel, f"always_read file missing: `{read_path}`"))

    return issues


# ---------------------------------------------------------------------------
# Check 5 — skill-index.yaml consistency
# ---------------------------------------------------------------------------

def validate_skill_index(skill_names: set[str]) -> list[Issue]:
    """
    If taxonomy/skill-index.yaml exists:
    - Every skill in the index must exist in skills/.
    - Every real skill must appear in the index.
    - Router skills must have role == "router".
    """
    index_path = REPO_ROOT / "taxonomy" / "skill-index.yaml"
    if not index_path.exists():
        return []

    rel = str(index_path.relative_to(REPO_ROOT))
    data = _load_yaml(index_path)
    if not isinstance(data, dict):
        return [Issue(rel, "could not parse as YAML mapping")]

    skills_section = data.get("skills", {})
    if not isinstance(skills_section, dict):
        return [Issue(rel, "`skills` must be a YAML mapping keyed by skill name")]

    issues: list[Issue] = []
    indexed_names = set(skills_section.keys())

    # Every indexed skill must exist
    for name in sorted(indexed_names):
        if name not in skill_names:
            issues.append(Issue(rel, f"index entry `{name}` does not exist in skills/"))

    # Every real skill must be indexed
    for name in sorted(skill_names - indexed_names):
        issues.append(Issue(rel, f"skill `{name}` exists in skills/ but is missing from index"))

    # Routers section consistency
    routers_section = data.get("routers", {})
    if isinstance(routers_section, dict):
        root = routers_section.get("root")
        if root and root not in skill_names:
            issues.append(Issue(rel, f"routers.root `{root}` does not exist in skills/"))
        for name in routers_section.get("domain", []):
            if name not in skill_names:
                issues.append(Issue(rel, f"routers.domain entry `{name}` does not exist in skills/"))

    # Router skills must have role == "router"
    for name, entry in skills_section.items():
        if not isinstance(entry, dict):
            continue
        role = entry.get("role")
        if role == "router" and name not in skill_names:
            issues.append(Issue(rel, f"index marks `{name}` as router but skill does not exist"))

    return issues


# ---------------------------------------------------------------------------
# Check 6 — profile-index.yaml consistency
# ---------------------------------------------------------------------------

def validate_profile_index(skill_names: set[str]) -> list[Issue]:
    """If profiles/profile-index.yaml exists, validate profile schema and skill refs."""
    profile_path = REPO_ROOT / "profiles" / "profile-index.yaml"
    if not profile_path.exists():
        return []

    rel = str(profile_path.relative_to(REPO_ROOT))
    data = _load_yaml(profile_path)
    if not isinstance(data, dict):
        return [Issue(rel, "could not parse as YAML mapping")]

    issues: list[Issue] = []
    schema_version = data.get("schema_version")
    if not isinstance(schema_version, str) or not schema_version.strip():
        issues.append(Issue(rel, "`schema_version` must be a non-empty string"))

    repo_matrix = data.get("repo_matrix", {})
    if not isinstance(repo_matrix, dict):
        issues.append(Issue(rel, "`repo_matrix` must be a YAML mapping"))
    else:
        for repo_name, repo in repo_matrix.items():
            if not isinstance(repo_name, str) or not SKILL_NAME_RE.fullmatch(repo_name):
                issues.append(Issue(rel, f"repo_matrix key `{repo_name}` must be lowercase hyphenated"))
                continue
            if not isinstance(repo, dict):
                issues.append(Issue(rel, f"repo_matrix `{repo_name}` must be a mapping"))
                continue
            status = repo.get("status")
            if status not in REPO_MATRIX_STATUS_VALUES:
                issues.append(
                    Issue(
                        rel,
                        f"repo_matrix `{repo_name}` status must be one of {sorted(REPO_MATRIX_STATUS_VALUES)}",
                    )
                )
            role = repo.get("role")
            if not isinstance(role, str) or not role.strip():
                issues.append(Issue(rel, f"repo_matrix `{repo_name}` role must be a non-empty string"))

    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        issues.append(Issue(rel, "`profiles` must be a non-empty YAML mapping"))
        return issues

    for profile_name, profile in profiles.items():
        if not isinstance(profile_name, str) or not SKILL_NAME_RE.fullmatch(profile_name):
            issues.append(Issue(rel, f"profile name `{profile_name}` must be lowercase hyphenated"))
            continue
        if not isinstance(profile, dict):
            issues.append(Issue(rel, f"profile `{profile_name}` must be a mapping"))
            continue

        status = profile.get("status")
        if status not in PROFILE_STATUS_VALUES:
            issues.append(
                Issue(rel, f"profile `{profile_name}` status must be one of {sorted(PROFILE_STATUS_VALUES)}")
            )

        scope = profile.get("scope")
        if scope not in PROFILE_SCOPE_VALUES:
            issues.append(
                Issue(rel, f"profile `{profile_name}` scope must be one of {sorted(PROFILE_SCOPE_VALUES)}")
            )

        intent = profile.get("intent")
        if not isinstance(intent, str) or not intent.strip():
            issues.append(Issue(rel, f"profile `{profile_name}` intent must be a non-empty string"))

        future_repo = profile.get("future_repo")
        if status == "draft" and (not isinstance(future_repo, str) or not SKILL_NAME_RE.fullmatch(future_repo)):
            issues.append(Issue(rel, f"profile `{profile_name}` draft profiles must set lowercase-hyphen future_repo"))

        include_all = profile.get("include_all_repo_skills", False)
        if not isinstance(include_all, bool):
            issues.append(Issue(rel, f"profile `{profile_name}` include_all_repo_skills must be boolean"))

        entrypoints = profile.get("entrypoints", [])
        if not isinstance(entrypoints, list) or not entrypoints or not all(isinstance(item, str) for item in entrypoints):
            issues.append(Issue(rel, f"profile `{profile_name}` entrypoints must be a non-empty list of skill names"))
            entrypoints = []

        for field in ("entrypoints", "routers"):
            value = profile.get(field, [])
            if value is None:
                continue
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                issues.append(Issue(rel, f"profile `{profile_name}` `{field}` must be a list of skill names"))
                continue
            for skill in value:
                if skill not in skill_names:
                    issues.append(Issue(rel, f"profile `{profile_name}` `{field}` references unknown skill `{skill}`"))
                if field == "routers" and not (SKILLS_ROOT / skill / "references" / "route-table.md").exists():
                    issues.append(Issue(rel, f"profile `{profile_name}` routers entry `{skill}` is not a router skill"))

        skills = profile.get("skills", {})
        if not isinstance(skills, dict):
            issues.append(Issue(rel, f"profile `{profile_name}` `skills` must be a mapping"))
            continue
        profile_skill_names: set[str] = set()
        for field in ("required", "optional"):
            value = skills.get(field, [])
            if value is None:
                continue
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                issues.append(Issue(rel, f"profile `{profile_name}` skills.{field} must be a list of skill names"))
                continue
            for skill in value:
                profile_skill_names.add(skill)
                if skill not in skill_names:
                    issues.append(Issue(rel, f"profile `{profile_name}` skills.{field} references unknown skill `{skill}`"))

        for entrypoint in entrypoints:
            if entrypoint not in profile_skill_names:
                issues.append(
                    Issue(rel, f"profile `{profile_name}` entrypoint `{entrypoint}` must appear in skills.required or skills.optional")
                )

        install_policy = profile.get("install_policy")
        if not isinstance(install_policy, dict):
            issues.append(Issue(rel, f"profile `{profile_name}` install_policy must be a mapping"))
            continue
        recommended = install_policy.get("recommended")
        if recommended not in INSTALL_RECOMMENDED_VALUES:
            issues.append(
                Issue(
                    rel,
                    f"profile `{profile_name}` install_policy.recommended must be one of {sorted(INSTALL_RECOMMENDED_VALUES)}",
                )
            )
        full_bundle_allowed = install_policy.get("full_bundle_allowed")
        if not isinstance(full_bundle_allowed, bool):
            issues.append(Issue(rel, f"profile `{profile_name}` install_policy.full_bundle_allowed must be boolean"))
        if scope == "global" and full_bundle_allowed:
            issues.append(Issue(rel, f"profile `{profile_name}` global profiles may not allow full bundles"))
        if full_bundle_allowed and not include_all:
            issues.append(Issue(rel, f"profile `{profile_name}` full_bundle_allowed requires include_all_repo_skills: true"))

        gaps = profile.get("gaps", [])
        if gaps is not None and (not isinstance(gaps, list) or not all(isinstance(item, str) for item in gaps)):
            issues.append(Issue(rel, f"profile `{profile_name}` gaps must be a list of strings"))

        artifacts = profile.get("artifacts", {})
        if artifacts is None:
            continue
        if not isinstance(artifacts, dict):
            issues.append(Issue(rel, f"profile `{profile_name}` artifacts must be a mapping"))
            continue

        for field, value in artifacts.items():
            if field not in PROFILE_ARTIFACT_FIELDS:
                issues.append(
                    Issue(
                        rel,
                        f"profile `{profile_name}` artifacts.{field} is unsupported; use {sorted(PROFILE_ARTIFACT_FIELDS)}",
                    )
                )
                continue
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                issues.append(Issue(rel, f"profile `{profile_name}` artifacts.{field} must be a list of repo-relative paths"))
                continue

            for artifact in value:
                artifact_path = Path(artifact)
                if artifact_path.is_absolute() or ".." in artifact_path.parts:
                    issues.append(Issue(rel, f"profile `{profile_name}` artifacts.{field} path `{artifact}` must be repo-relative"))
                    continue
                if not artifact.startswith(f"profiles/{profile_name}/"):
                    issues.append(
                        Issue(
                            rel,
                            f"profile `{profile_name}` artifacts.{field} path `{artifact}` must live under profiles/{profile_name}/",
                        )
                    )
                full_path = REPO_ROOT / artifact
                if not full_path.exists():
                    issues.append(Issue(rel, f"profile `{profile_name}` artifacts.{field} missing path `{artifact}`"))
                    continue
                if not full_path.is_file():
                    issues.append(Issue(rel, f"profile `{profile_name}` artifacts.{field} path `{artifact}` must be a file"))
                    continue
                if full_path.suffix in TEXT_ARTIFACT_SUFFIXES:
                    try:
                        text = full_path.read_text(encoding="utf-8")
                    except UnicodeDecodeError:
                        issues.append(Issue(rel, f"profile `{profile_name}` artifact `{artifact}` must be UTF-8 text"))
                        continue
                    for placeholder in sorted(set(PLACEHOLDER_RE.findall(text))):
                        if not VALID_PLACEHOLDER_RE.fullmatch(placeholder):
                            issues.append(
                                Issue(
                                    artifact,
                                    f"invalid template placeholder `{{{{{placeholder}}}}}`; use upper-case snake case",
                                )
                            )

    return issues


# ---------------------------------------------------------------------------
# Check 7 — profile-routing-evals.json consistency
# ---------------------------------------------------------------------------

def validate_profile_routing_evals(skill_names: set[str]) -> list[Issue]:
    """Validate profile-level routing evals against profile-index.yaml."""
    evals_path = REPO_ROOT / "tests" / "profile-routing-evals.json"
    if not evals_path.exists():
        return []

    rel = str(evals_path.relative_to(REPO_ROOT))
    profile_path = REPO_ROOT / "profiles" / "profile-index.yaml"
    profile_data = _load_yaml(profile_path)
    if not isinstance(profile_data, dict) or not isinstance(profile_data.get("profiles"), dict):
        return [Issue(rel, "profiles/profile-index.yaml must exist and define profiles before profile evals can be validated")]
    profiles: dict = profile_data["profiles"]
    profile_names = set(profiles.keys())

    data = _load_json(evals_path)
    if not isinstance(data, dict):
        return [Issue(rel, "could not parse as JSON object")]

    evals = data.get("evals")
    if not isinstance(evals, list) or not evals:
        return [Issue(rel, "`evals` must be a non-empty list")]

    issues: list[Issue] = []
    seen_ids: set[str] = set()
    for idx, entry in enumerate(evals, start=1):
        if not isinstance(entry, dict):
            issues.append(Issue(rel, f"eval #{idx} must be an object"))
            continue

        eid = entry.get("id")
        if not isinstance(eid, str) or not eid.strip():
            issues.append(Issue(rel, f"eval #{idx} missing non-empty id"))
            eid = f"#{idx}"
        elif eid in seen_ids:
            issues.append(Issue(rel, f"duplicate eval id `{eid}`"))
        else:
            seen_ids.add(eid)

        for field in ("prompt", "rationale"):
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                issues.append(Issue(rel, f"{eid} `{field}` must be a non-empty string"))

        expected_profile = entry.get("expected_profile")
        if expected_profile not in profile_names:
            issues.append(Issue(rel, f"{eid} expected_profile references unknown profile `{expected_profile}`"))
            expected_entrypoints: set[str] = set()
        else:
            entrypoints = profiles[expected_profile].get("entrypoints", [])
            expected_entrypoints = set(entrypoints) if isinstance(entrypoints, list) else set()

        expected_entrypoint = entry.get("expected_entrypoint")
        if expected_entrypoint not in skill_names:
            issues.append(Issue(rel, f"{eid} expected_entrypoint references unknown skill `{expected_entrypoint}`"))
        elif expected_profile in profile_names and expected_entrypoint not in expected_entrypoints:
            issues.append(
                Issue(
                    rel,
                    f"{eid} expected_entrypoint `{expected_entrypoint}` is not an entrypoint for profile `{expected_profile}`",
                )
            )

        should_not_profiles = entry.get("should_not_profiles", [])
        if not isinstance(should_not_profiles, list) or not all(isinstance(item, str) for item in should_not_profiles):
            issues.append(Issue(rel, f"{eid} should_not_profiles must be a list of profile names"))
        else:
            for profile in should_not_profiles:
                if profile not in profile_names:
                    issues.append(Issue(rel, f"{eid} should_not_profiles references unknown profile `{profile}`"))
            if expected_profile in should_not_profiles:
                issues.append(Issue(rel, f"{eid} should_not_profiles must not include expected_profile `{expected_profile}`"))

    return issues


# ---------------------------------------------------------------------------
# Check 8 — skill-kernel schema consistency
# ---------------------------------------------------------------------------

def validate_skill_kernel_schema(skill_names: set[str]) -> list[Issue]:
    """Validate the portable skill-kernel schema and checked examples."""
    schema_path = REPO_ROOT / "schemas" / "skill-kernel" / "skill-kernel.schema.json"
    handoff_schema_path = (
        REPO_ROOT / "schemas" / "skill-kernel" / "install-handoff-contract.schema.json"
    )
    handoff_contract_path = (
        REPO_ROOT
        / "schemas"
        / "skill-kernel"
        / "install-handoff-contract-2026-05-28.json"
    )
    install_plan_schema_path = (
        REPO_ROOT / "schemas" / "skill-kernel" / "install-plan.schema.json"
    )
    install_plan_validator_path = REPO_ROOT / "scripts" / "validate_install_handoff_plan.py"
    examples_dir = REPO_ROOT / "schemas" / "skill-kernel" / "examples"
    if not schema_path.exists() and not examples_dir.exists():
        return []

    issues: list[Issue] = []
    schema_rel = str(schema_path.relative_to(REPO_ROOT))
    schema = _load_json(schema_path)
    if not isinstance(schema, dict):
        return [Issue(schema_rel, "could not parse as JSON object")]

    required = schema.get("required")
    if not isinstance(required, list):
        issues.append(Issue(schema_rel, "`required` must list top-level kernel fields"))
    else:
        missing = KERNEL_REQUIRED_TOP_LEVEL - set(required)
        for field in sorted(missing):
            issues.append(Issue(schema_rel, f"schema top-level required fields missing `{field}`"))

    properties = schema.get("properties")
    if not isinstance(properties, dict):
        issues.append(Issue(schema_rel, "`properties` must be a mapping"))
    else:
        for field in sorted(KERNEL_REQUIRED_TOP_LEVEL):
            if field not in properties:
                issues.append(Issue(schema_rel, f"schema properties missing `{field}`"))

    profile_path = REPO_ROOT / "profiles" / "profile-index.yaml"
    profile_data = _load_yaml(profile_path)
    profiles = profile_data.get("profiles", {}) if isinstance(profile_data, dict) else {}
    profile_names = set(profiles.keys()) if isinstance(profiles, dict) else set()

    profile_index_rel = str(profile_path.relative_to(REPO_ROOT))
    repo_matrix = profile_data.get("repo_matrix", {}) if isinstance(profile_data, dict) else {}
    kernel_repo = repo_matrix.get("skill-kernel", {}) if isinstance(repo_matrix, dict) else {}
    if isinstance(kernel_repo, dict):
        declared_schema = kernel_repo.get("schema_path")
        if declared_schema and declared_schema != schema_rel:
            issues.append(
                Issue(
                    profile_index_rel,
                    f"repo_matrix.skill-kernel schema_path `{declared_schema}` does not match `{schema_rel}`",
                )
            )
        declared_handoff_schema = kernel_repo.get("handoff_contract_schema_path")
        handoff_schema_rel = str(handoff_schema_path.relative_to(REPO_ROOT))
        if declared_handoff_schema != handoff_schema_rel:
            issues.append(
                Issue(
                    profile_index_rel,
                    "repo_matrix.skill-kernel handoff_contract_schema_path "
                    f"`{declared_handoff_schema}` does not match `{handoff_schema_rel}`",
                )
            )
        declared_handoff_contract = kernel_repo.get("handoff_contract_path")
        handoff_contract_rel = str(handoff_contract_path.relative_to(REPO_ROOT))
        if declared_handoff_contract != handoff_contract_rel:
            issues.append(
                Issue(
                    profile_index_rel,
                    "repo_matrix.skill-kernel handoff_contract_path "
                    f"`{declared_handoff_contract}` does not match `{handoff_contract_rel}`",
                )
            )
        declared_install_plan_schema = kernel_repo.get("install_plan_schema_path")
        install_plan_schema_rel = str(install_plan_schema_path.relative_to(REPO_ROOT))
        if declared_install_plan_schema != install_plan_schema_rel:
            issues.append(
                Issue(
                    profile_index_rel,
                    "repo_matrix.skill-kernel install_plan_schema_path "
                    f"`{declared_install_plan_schema}` does not match `{install_plan_schema_rel}`",
                )
            )

    if not install_plan_schema_path.is_file():
        issues.append(
            Issue(
                str(install_plan_schema_path.relative_to(REPO_ROOT)),
                "install plan schema missing",
            )
        )
    else:
        install_plan_schema = _load_json(install_plan_schema_path)
        if not isinstance(install_plan_schema, dict):
            issues.append(
                Issue(
                    str(install_plan_schema_path.relative_to(REPO_ROOT)),
                    "could not parse as JSON object",
                )
            )
        else:
            required_plan_fields = set(install_plan_schema.get("required", []))
            for field in (
                "requested_manifests",
                "review_gates",
                "source_of_truth_paths",
                "validation_commands",
                "privacy_audit",
                "rollback",
                "automation",
            ):
                if field not in required_plan_fields:
                    issues.append(
                        Issue(
                            str(install_plan_schema_path.relative_to(REPO_ROOT)),
                            f"install plan schema required fields missing `{field}`",
                        )
                    )

    if not install_plan_validator_path.is_file():
        issues.append(
            Issue(
                str(install_plan_validator_path.relative_to(REPO_ROOT)),
                "install plan validator missing",
            )
        )

    if not handoff_schema_path.is_file():
        issues.append(
            Issue(
                str(handoff_schema_path.relative_to(REPO_ROOT)),
                "install handoff schema missing",
            )
        )
    else:
        handoff_schema = _load_json(handoff_schema_path)
        if not isinstance(handoff_schema, dict):
            issues.append(
                Issue(
                    str(handoff_schema_path.relative_to(REPO_ROOT)),
                    "could not parse as JSON object",
                )
            )

    if not handoff_contract_path.is_file():
        issues.append(
            Issue(
                str(handoff_contract_path.relative_to(REPO_ROOT)),
                "install handoff contract missing",
            )
        )
    else:
        handoff_rel = str(handoff_contract_path.relative_to(REPO_ROOT))
        handoff_contract = _load_json(handoff_contract_path)
        if not isinstance(handoff_contract, dict):
            issues.append(Issue(handoff_rel, "could not parse as JSON object"))
        else:
            allowed_implementation_states = {
                "contract-only",
                "reviewed-execute-enabled",
            }
            if (
                handoff_contract.get("implementation_status")
                not in allowed_implementation_states
            ):
                issues.append(
                    Issue(
                        handoff_rel,
                        "implementation_status must be one of "
                        + ", ".join(sorted(allowed_implementation_states)),
                    )
                )
            automation = handoff_contract.get("automation_policy", {})
            if not isinstance(automation, dict):
                issues.append(Issue(handoff_rel, "`automation_policy` must be a mapping"))
            else:
                # Dangerous switches must always stay false; real_installer_authorized
                # may be true once the reviewed-execute-enabled state is in force.
                for field in (
                    "may_write_runtime_files_without_review",
                    "may_write_global_roots_without_explicit_user_request",
                ):
                    if automation.get(field) is not False:
                        issues.append(
                            Issue(
                                handoff_rel,
                                f"automation_policy.{field} must be false",
                            )
                        )
                if automation.get("real_installer_authorized") not in (True, False):
                    issues.append(
                        Issue(
                            handoff_rel,
                            "automation_policy.real_installer_authorized must be a boolean",
                        )
                    )

            derived_from = handoff_contract.get("derived_from", {})
            runtime_capture = (
                derived_from.get("runtime_capture")
                if isinstance(derived_from, dict)
                else None
            )
            if not isinstance(runtime_capture, str) or not (REPO_ROOT / runtime_capture).is_file():
                issues.append(
                    Issue(
                        handoff_rel,
                        "derived_from.runtime_capture must reference an existing repo file",
                    )
                )

            target_modes = handoff_contract.get("target_modes", [])
            if isinstance(target_modes, list):
                mode_ids = {
                    mode.get("id")
                    for mode in target_modes
                    if isinstance(mode, dict) and isinstance(mode.get("id"), str)
                }
            else:
                mode_ids = set()
            missing_modes = INSTALL_HANDOFF_REQUIRED_MODES - mode_ids
            for mode in sorted(missing_modes):
                issues.append(Issue(handoff_rel, f"target_modes missing `{mode}`"))

            review_gates = handoff_contract.get("review_gates", [])
            if isinstance(review_gates, list):
                gate_ids = {
                    gate.get("id")
                    for gate in review_gates
                    if isinstance(gate, dict) and isinstance(gate.get("id"), str)
                }
            else:
                gate_ids = set()
            missing_gates = INSTALL_HANDOFF_REQUIRED_GATES - gate_ids
            for gate in sorted(missing_gates):
                issues.append(Issue(handoff_rel, f"review_gates missing `{gate}`"))

            for source in handoff_contract.get("authoritative_sources", []):
                if not isinstance(source, dict):
                    continue
                for source_path in source.get("paths", []):
                    if not isinstance(source_path, str):
                        issues.append(Issue(handoff_rel, "authoritative source paths must be strings"))
                    elif source_path.startswith("/"):
                        issues.append(
                            Issue(
                                handoff_rel,
                                f"authoritative source path must be repo-relative: `{source_path}`",
                            )
                        )
                    elif not (REPO_ROOT / source_path).exists():
                        issues.append(
                            Issue(
                                handoff_rel,
                                f"authoritative source path missing: `{source_path}`",
                            )
                        )

    if not examples_dir.exists():
        issues.append(Issue(str(examples_dir.relative_to(REPO_ROOT)), "examples directory missing"))
        return issues

    example_paths = sorted(examples_dir.glob("*.json"))
    if not example_paths:
        issues.append(Issue(str(examples_dir.relative_to(REPO_ROOT)), "no kernel example JSON files found"))
        return issues

    declared_examples = set()
    if isinstance(kernel_repo, dict):
        raw_examples = kernel_repo.get("example_paths", [])
        if isinstance(raw_examples, list):
            declared_examples = {item for item in raw_examples if isinstance(item, str)}

    for example_path in example_paths:
        rel = str(example_path.relative_to(REPO_ROOT))
        data = _load_json(example_path)
        if not isinstance(data, dict):
            issues.append(Issue(rel, "could not parse as JSON object"))
            continue

        if declared_examples and rel not in declared_examples:
            issues.append(Issue(profile_index_rel, f"repo_matrix.skill-kernel example_paths missing `{rel}`"))

        missing = KERNEL_REQUIRED_TOP_LEVEL - set(data.keys())
        for field in sorted(missing):
            issues.append(Issue(rel, f"kernel example missing top-level field `{field}`"))

        source_paths = data.get("source_paths", [])
        if not isinstance(source_paths, list) or not source_paths:
            issues.append(Issue(rel, "`source_paths` must be a non-empty list"))
        else:
            for source_path in source_paths:
                if not isinstance(source_path, str):
                    issues.append(Issue(rel, "`source_paths` entries must be strings"))
                    continue
                full_path = REPO_ROOT / source_path
                if not full_path.exists():
                    issues.append(Issue(rel, f"source path does not exist: `{source_path}`"))

        profile = data.get("profile", {})
        profile_name = profile.get("name") if isinstance(profile, dict) else None
        if profile_name not in profile_names:
            issues.append(Issue(rel, f"profile.name references unknown profile `{profile_name}`"))
            expected_entrypoints: set[str] = set()
        else:
            raw_entrypoints = profiles[profile_name].get("entrypoints", [])
            expected_entrypoints = set(raw_entrypoints) if isinstance(raw_entrypoints, list) else set()

        routing = data.get("routing", {})
        if not isinstance(routing, dict):
            issues.append(Issue(rel, "`routing` must be a mapping"))
        else:
            entrypoints = routing.get("entrypoints", [])
            if not isinstance(entrypoints, list) or not entrypoints:
                issues.append(Issue(rel, "routing.entrypoints must be a non-empty list"))
                entrypoints = []
            for entrypoint in entrypoints:
                if entrypoint not in skill_names:
                    issues.append(Issue(rel, f"routing.entrypoints references unknown skill `{entrypoint}`"))
                elif expected_entrypoints and entrypoint not in expected_entrypoints:
                    issues.append(
                        Issue(
                            rel,
                            f"routing.entrypoint `{entrypoint}` is not an entrypoint for profile `{profile_name}`",
                        )
                    )
            routers = routing.get("routers", [])
            if not isinstance(routers, list):
                issues.append(Issue(rel, "routing.routers must be a list"))
                routers = []
            for router in routers:
                if router not in skill_names:
                    issues.append(Issue(rel, f"routing.routers references unknown skill `{router}`"))
                elif not (SKILLS_ROOT / router / "references" / "route-table.md").exists():
                    issues.append(Issue(rel, f"routing.routers entry `{router}` is not a router skill"))

        skills = data.get("skills", {})
        if not isinstance(skills, dict):
            issues.append(Issue(rel, "`skills` must be a mapping"))
        else:
            for field in ("required", "optional"):
                value = skills.get(field, [])
                if not isinstance(value, list):
                    issues.append(Issue(rel, f"skills.{field} must be a list"))
                    continue
                for skill in value:
                    if skill not in skill_names:
                        issues.append(Issue(rel, f"skills.{field} references unknown skill `{skill}`"))

        workflow = data.get("workflow_contract", {})
        if not isinstance(workflow, dict):
            issues.append(Issue(rel, "`workflow_contract` must be a mapping"))
        else:
            lanes = workflow.get("supported_lanes", [])
            if not isinstance(lanes, list) or set(lanes) != KERNEL_LANES:
                issues.append(
                    Issue(rel, f"workflow_contract.supported_lanes must equal {sorted(KERNEL_LANES)}")
                )
            evidence_lane = workflow.get("evidence_lane", {})
            modes = evidence_lane.get("modes", []) if isinstance(evidence_lane, dict) else []
            if not isinstance(modes, list) or set(modes) != KERNEL_EVIDENCE_MODES:
                issues.append(
                    Issue(rel, f"workflow_contract.evidence_lane.modes must equal {sorted(KERNEL_EVIDENCE_MODES)}")
                )

        validation = data.get("validation", {})
        checks = validation.get("required_checks", []) if isinstance(validation, dict) else []
        if not isinstance(checks, list) or not checks:
            issues.append(Issue(rel, "validation.required_checks must be a non-empty list"))
        else:
            for idx, check in enumerate(checks, start=1):
                if not isinstance(check, dict):
                    issues.append(Issue(rel, f"validation.required_checks #{idx} must be a mapping"))
                    continue
                for field in ("name", "scope", "mutates_files", "required"):
                    if field not in check:
                        issues.append(Issue(rel, f"validation.required_checks #{idx} missing `{field}`"))

        adapters = data.get("adapters", {})
        runtimes = adapters.get("runtimes", []) if isinstance(adapters, dict) else []
        if not isinstance(runtimes, list) or not runtimes:
            issues.append(Issue(rel, "adapters.runtimes must be a non-empty list"))

    if declared_examples:
        actual_examples = {str(path.relative_to(REPO_ROOT)) for path in example_paths}
        for declared in sorted(declared_examples - actual_examples):
            issues.append(Issue(profile_index_rel, f"repo_matrix.skill-kernel example path missing file `{declared}`"))

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    if not SKILLS_ROOT.exists():
        print(f"skills directory not found: {SKILLS_ROOT}", file=sys.stderr)
        return 2

    skill_names = {p.name for p in SKILLS_ROOT.iterdir() if p.is_dir()}
    all_issues: list[Issue] = []

    checks = [
        ("router-children", validate_router_children(skill_names)),
        ("expected-paths", validate_expected_paths(skill_names)),
        ("contrastive-routing", validate_contrastive_routing(skill_names)),
        ("memory-contracts", validate_memory_contracts(skill_names)),
        ("skill-index", validate_skill_index(skill_names)),
        ("profile-index", validate_profile_index(skill_names)),
        ("profile-routing-evals", validate_profile_routing_evals(skill_names)),
        ("skill-kernel-schema", validate_skill_kernel_schema(skill_names)),
    ]

    for check_name, issues in checks:
        if issues:
            for issue in issues:
                print(f"ERROR [{check_name}] {issue.path}: {issue.message}")
        all_issues.extend(issues)

    if all_issues:
        print(f"\nTaxonomy validation failed: {len(all_issues)} issue(s).")
        return 1

    router_count = sum(
        1 for p in SKILLS_ROOT.iterdir()
        if p.is_dir() and (p / "references" / "route-table.md").exists()
    )
    print(
        f"Taxonomy OK: {len(skill_names)} skills, {router_count} routers with route tables, "
        f"no issues found."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
