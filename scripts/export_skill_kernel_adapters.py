#!/usr/bin/env python3
"""Export dry-run runtime adapters and preview skill fixtures from kernels."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXAMPLES_DIR = REPO_ROOT / "schemas" / "skill-kernel" / "examples"
DEFAULT_CONTRACTS_PATH = REPO_ROOT / "schemas" / "skill-kernel" / "runtime-adapter-contracts.json"
ADAPTER_SCHEMA_VERSION = "0.1-dry-run"
INSTALLABLE_MANIFEST_SCHEMA_VERSION = "0.1-prototype"
MANIFEST_EXERCISE_SCHEMA_VERSION = "0.1-session-only"
RUNTIME_CHOICES = ("codex", "claude-code", "cursor", "generic-agent", "all")


def repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_kernel(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{repo_relative(path)} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{repo_relative(path)} must contain a JSON object")
    return data


def load_runtime_contracts(path: Path = DEFAULT_CONTRACTS_PATH) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{repo_relative(path)} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("contracts"), dict):
        raise ValueError(f"{repo_relative(path)} must contain a contracts mapping")
    return data


def default_kernel_paths() -> list[Path]:
    return sorted(DEFAULT_EXAMPLES_DIR.glob("*.json"))


def declared_runtimes(kernel: dict[str, Any]) -> list[dict[str, str]]:
    adapters = kernel.get("adapters", {})
    runtimes = adapters.get("runtimes", []) if isinstance(adapters, dict) else []
    if not isinstance(runtimes, list):
        return []

    declared: list[dict[str, str]] = []
    for entry in runtimes:
        if not isinstance(entry, dict):
            continue
        runtime = entry.get("runtime")
        status = entry.get("status", "unknown")
        if isinstance(runtime, str) and runtime:
            declared.append({"runtime": runtime, "status": str(status)})
    return declared


def runtime_status(kernel: dict[str, Any], runtime: str) -> str | None:
    for entry in declared_runtimes(kernel):
        if entry["runtime"] == runtime:
            return entry["status"]
    return None


def validation_commands(kernel: dict[str, Any]) -> list[str]:
    validation = kernel.get("validation", {})
    checks = validation.get("required_checks", []) if isinstance(validation, dict) else []
    commands: list[str] = []
    if not isinstance(checks, list):
        return commands
    for check in checks:
        if not isinstance(check, dict):
            continue
        command = check.get("command")
        if isinstance(command, str) and command:
            commands.append(command)
    return commands


def runtime_contract(contracts: dict[str, Any], runtime: str) -> dict[str, Any]:
    contract = contracts["contracts"].get(runtime)
    if not isinstance(contract, dict):
        raise ValueError(f"runtime `{runtime}` has no adapter contract")
    return contract


def title_from_hyphen_name(name: str) -> str:
    return " ".join(part.capitalize() for part in name.split("-") if part)


def bounded_description(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def build_interface_projection(kernel: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any] | None:
    interface_metadata = contract.get("interface_metadata", {})
    if not isinstance(interface_metadata, dict):
        return None
    support = interface_metadata.get("support")
    if support in {"not-observed", "not-observed-for-claude-code"}:
        return None

    profile = kernel["profile"]
    return {
        "path": interface_metadata.get("path", "agents/openai.yaml"),
        "status": "preview-only",
        "data": {
            "interface": {
                "display_name": title_from_hyphen_name(profile["name"]),
                "short_description": bounded_description(profile["intent"], 96),
                "default_prompt": f"Use the {profile['name']} profile for this project task.",
            }
        },
    }


def build_runtime_projection(
    kernel: dict[str, Any],
    runtime: str,
    contract: dict[str, Any],
    field_classes: dict[str, Any],
) -> dict[str, Any]:
    frontmatter_contract = contract.get("frontmatter", {})
    max_chars = frontmatter_contract.get("description_max_chars", 500)
    if not isinstance(max_chars, int):
        max_chars = 500

    skill_name = kernel["kernel_id"]
    skill_description = bounded_description(kernel["profile"]["intent"], max_chars)
    projection: dict[str, Any] = {
        "contract_id": contract["contract_id"],
        "support_level": contract["support_level"],
        "candidate_directory": skill_name,
        "required_files": contract["required_files"],
        "optional_files": contract.get("optional_files", []),
        "skill_markdown": {
            "path": "SKILL.md",
            "status": "preview-only",
            "frontmatter": {
                "name": skill_name,
                "description": skill_description,
            },
            "body_sources": kernel["source_paths"],
        },
        "routing_hints": {
            "profile_name": kernel["profile"]["name"],
            "entrypoints": kernel["routing"]["entrypoints"],
            "routers": kernel["routing"]["routers"],
            "required_skills": kernel["skills"]["required"],
            "optional_skills": kernel["skills"]["optional"],
            "selection_semantics": kernel["adapters"].get("selection_semantics", {}),
        },
        "field_mapping": {
            "runtime_mappable": field_classes.get("runtime_mappable", []),
            "docs_only": field_classes.get("docs_only", []),
            "never_authoritative_in_adapter": field_classes.get(
                "never_authoritative_in_adapter", []
            ),
        },
        "compatibility": {
            "declared_runtime": runtime_status(kernel, runtime) is not None,
            "frontmatter_name_matches_directory": True,
            "description_within_runtime_limit": len(skill_description) <= max_chars,
            "installable_now": False,
        },
    }

    interface_projection = build_interface_projection(kernel, contract)
    if interface_projection is not None:
        projection["interface_metadata"] = interface_projection
    return projection


def yaml_scalar(value: Any) -> str:
    return json.dumps(str(value))


def render_frontmatter(frontmatter: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.append(f"{key}: {yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def parse_generated_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("missing opening YAML frontmatter marker")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("missing closing YAML frontmatter marker")

    metadata: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line!r}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        try:
            value = json.loads(raw_value.strip())
        except json.JSONDecodeError as exc:
            raise ValueError(f"frontmatter value for `{key}` is not JSON-quoted") from exc
        if not isinstance(value, str):
            raise ValueError(f"frontmatter value for `{key}` must be a string")
        metadata[key] = value
    return metadata


def markdown_bullets(items: list[Any]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- `{item}`" if isinstance(item, str) else f"- {item}" for item in items]


def render_preview_skill_markdown(adapter: dict[str, Any]) -> str:
    projection = adapter["runtime_projection"]
    skill_markdown = projection["skill_markdown"]
    frontmatter = skill_markdown["frontmatter"]
    hints = projection["routing_hints"]
    field_mapping = projection["field_mapping"]
    compatibility = projection["compatibility"]

    lines = [
        render_frontmatter(frontmatter).rstrip(),
        f"# {title_from_hyphen_name(frontmatter['name'])} Preview",
        "",
        "This is a preview-only runtime fixture generated from the portable skill-kernel adapter.",
        "Do not install it as an authoritative skill; regenerate it from the kernel source.",
        "",
        "## Runtime",
        "",
        f"- Runtime: `{adapter['runtime']}`",
        f"- Contract: `{projection['contract_id']}`",
        f"- Support level: `{projection['support_level']}`",
        f"- Generated from: `{adapter['generated_from']}`",
        f"- Source of truth: `{adapter['source_of_truth']}`",
        f"- Installable now: `{str(compatibility['installable_now']).lower()}`",
        "",
        "## Routing Preview",
        "",
        f"- Profile: `{hints['profile_name']}`",
        "- Entrypoints:",
        *markdown_bullets(hints["entrypoints"]),
        "- Routers:",
        *markdown_bullets(hints["routers"]),
        "- Required skills:",
        *markdown_bullets(hints["required_skills"]),
        "- Optional skills:",
        *markdown_bullets(hints["optional_skills"]),
        "- Selection semantics:",
        *markdown_bullets(
            [
                "runtime_expectation: "
                f"{hints.get('selection_semantics', {}).get('runtime_expectation', 'unspecified')}",
                "delegation_policy: "
                f"{hints.get('selection_semantics', {}).get('delegation_policy', 'unspecified')}",
            ]
        ),
        "",
        "## Kernel Sources",
        "",
        *markdown_bullets(skill_markdown.get("body_sources", [])),
        "",
        "## Adapter Boundary",
        "",
        "The following kernel fields remain docs-only and must not become authoritative runtime metadata:",
        *markdown_bullets(field_mapping.get("docs_only", [])),
        "",
        "Never put private paths, credentials, workflow logic, memory writeback policy, or validation gate definitions only in this preview fixture.",
    ]
    return "\n".join(lines) + "\n"


def render_interface_yaml(interface_projection: dict[str, Any]) -> str:
    interface = interface_projection["data"]["interface"]
    return "\n".join(
        [
            "interface:",
            f"  display_name: {yaml_scalar(interface['display_name'])}",
            f"  short_description: {yaml_scalar(interface['short_description'])}",
            f"  default_prompt: {yaml_scalar(interface['default_prompt'])}",
            "",
        ]
    )


def path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def forbidden_global_skill_roots() -> list[Path]:
    home = Path.home()
    return [
        home / ".codex" / "skills",
        home / ".agents" / "skills",
        home / ".claude" / "skills",
    ]


def validate_session_only_root(output_root: Path) -> list[str]:
    issues: list[str] = []
    for root in forbidden_global_skill_roots():
        if path_is_relative_to(output_root, root):
            issues.append(
                f"exercise root {output_root} is inside global skill root {root}"
            )
    return issues


def preview_skill_dir(adapter: dict[str, Any], output_root: Path) -> Path:
    projection = adapter["runtime_projection"]
    return output_root / adapter["runtime"] / projection["candidate_directory"]


def installable_manifest_dir(adapter: dict[str, Any], output_root: Path) -> Path:
    projection = adapter["runtime_projection"]
    return output_root / adapter["runtime"] / projection["candidate_directory"]


def exercise_skill_dir(manifest: dict[str, Any], output_root: Path) -> Path:
    install_target = manifest["install_target"]
    return output_root / manifest["runtime"] / install_target["skill_directory"]


def build_adapter(
    kernel: dict[str, Any],
    kernel_path: Path,
    runtime: str,
    contracts: dict[str, Any],
) -> dict[str, Any]:
    status = runtime_status(kernel, runtime)
    if status is None:
        available = ", ".join(entry["runtime"] for entry in declared_runtimes(kernel)) or "none"
        raise ValueError(
            f"{repo_relative(kernel_path)} does not declare runtime `{runtime}` "
            f"(available: {available})"
        )

    contract = runtime_contract(contracts, runtime)
    workflow = kernel["workflow_contract"]
    return {
        "adapter_schema_version": ADAPTER_SCHEMA_VERSION,
        "runtime": runtime,
        "runtime_status": status,
        "dry_run": True,
        "installable": False,
        "source_of_truth": kernel["adapters"]["source_of_truth"],
        "generated_from": repo_relative(kernel_path),
        "runtime_contract": {
            "contract_id": contract["contract_id"],
            "support_level": contract["support_level"],
            "skill_roots": contract["skill_roots"],
            "required_files": contract["required_files"],
            "frontmatter": contract["frontmatter"],
            "optional_files": contract.get("optional_files", []),
            "interface_metadata": contract.get("interface_metadata", {}),
        },
        "runtime_projection": build_runtime_projection(
            kernel,
            runtime,
            contract,
            contracts.get("field_classes", {}),
        ),
        "kernel": {
            "schema_version": kernel["schema_version"],
            "kernel_id": kernel["kernel_id"],
            "owner_repo": kernel["owner_repo"],
            "source_paths": kernel["source_paths"],
        },
        "profile": kernel["profile"],
        "install_policy": kernel["install_policy"],
        "routing": {
            "entrypoints": kernel["routing"]["entrypoints"],
            "routers": kernel["routing"]["routers"],
            "handoff_policy": kernel["routing"]["handoff_policy"],
        },
        "selection_semantics": kernel["adapters"].get("selection_semantics", {}),
        "skills": {
            "required": kernel["skills"]["required"],
            "optional": kernel["skills"]["optional"],
        },
        "workflow": {
            "supported_lanes": workflow["supported_lanes"],
            "default_lane": workflow["default_lane"],
            "lane_selection_rule": workflow["lane_selection_rule"],
            "action_lane": {
                "mutation_surfaces": workflow["action_lane"]["mutation_surfaces"],
                "risk_classes": workflow["action_lane"]["risk_classes"],
                "required_preflight": workflow["action_lane"]["required_preflight"],
                "forbidden_actions": workflow["action_lane"]["forbidden_actions"],
                "approval_boundary": workflow["action_lane"]["approval_boundary"],
            },
            "evidence_lane": {
                "modes": workflow["evidence_lane"]["modes"],
                "source_ledger_required": workflow["evidence_lane"][
                    "source_ledger_required"
                ],
                "source_types": workflow["evidence_lane"]["source_types"],
                "confidence_policy": workflow["evidence_lane"]["confidence_policy"],
                "citation_policy": workflow["evidence_lane"]["citation_policy"],
            },
            "combined_lane": workflow["combined_lane"],
            "no_contract_lane": workflow["no_contract_lane"],
        },
        "validation": {
            "required_checks": kernel["validation"]["required_checks"],
            "commands": validation_commands(kernel),
            "acceptance_checks": kernel["validation"]["acceptance_checks"],
        },
        "memory": kernel["memory"],
        "promotion": {
            "status": kernel["promotion"]["status"],
            "promotion_gates": kernel["promotion"]["promotion_gates"],
            "rejection_checks": kernel["promotion"]["rejection_checks"],
        },
        "runtime_notes": [
            "dry-run adapter only; do not install directly",
            "regenerate from schemas/skill-kernel examples instead of editing adapter output",
            "runtime metadata must not become the workflow source of truth",
        ],
    }


def validate_adapter(
    kernel: dict[str, Any],
    adapter: dict[str, Any],
    runtime: str,
    contracts: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    contract = runtime_contract(contracts, runtime)

    expected = {
        "adapter_schema_version": ADAPTER_SCHEMA_VERSION,
        "runtime": runtime,
        "dry_run": True,
        "installable": False,
        "source_of_truth": kernel["adapters"]["source_of_truth"],
    }
    for field, value in expected.items():
        if adapter.get(field) != value:
            issues.append(f"{field} must be {value!r}")

    if adapter["kernel"].get("kernel_id") != kernel["kernel_id"]:
        issues.append("kernel.kernel_id drifted from source kernel")
    if adapter["kernel"].get("source_paths") != kernel["source_paths"]:
        issues.append("kernel.source_paths drifted from source kernel")
    if adapter.get("profile") != kernel["profile"]:
        issues.append("profile block drifted from source kernel")
    if adapter.get("install_policy") != kernel["install_policy"]:
        issues.append("install_policy block drifted from source kernel")
    if adapter["routing"].get("entrypoints") != kernel["routing"]["entrypoints"]:
        issues.append("routing.entrypoints drifted from source kernel")
    if adapter["routing"].get("routers") != kernel["routing"]["routers"]:
        issues.append("routing.routers drifted from source kernel")
    if adapter.get("skills") != kernel["skills"]:
        issues.append("skills block drifted from source kernel")
    if adapter.get("selection_semantics") != kernel["adapters"].get(
        "selection_semantics",
        {},
    ):
        issues.append("selection_semantics drifted from source kernel")

    workflow = kernel["workflow_contract"]
    adapter_workflow = adapter.get("workflow", {})
    for field in ("supported_lanes", "default_lane", "lane_selection_rule"):
        if adapter_workflow.get(field) != workflow[field]:
            issues.append(f"workflow.{field} drifted from source kernel")
    if adapter_workflow.get("combined_lane") != workflow["combined_lane"]:
        issues.append("workflow.combined_lane drifted from source kernel")
    if adapter_workflow.get("no_contract_lane") != workflow["no_contract_lane"]:
        issues.append("workflow.no_contract_lane drifted from source kernel")

    if adapter["validation"].get("required_checks") != kernel["validation"]["required_checks"]:
        issues.append("validation.required_checks drifted from source kernel")
    if adapter["validation"].get("commands") != validation_commands(kernel):
        issues.append("validation.commands do not match source required_checks")
    if adapter.get("memory") != kernel["memory"]:
        issues.append("memory block drifted from source kernel")
    if adapter["promotion"].get("status") != kernel["promotion"]["status"]:
        issues.append("promotion.status drifted from source kernel")

    notes = " ".join(adapter.get("runtime_notes", []))
    if "dry-run" not in adapter["adapter_schema_version"] and "dry-run" not in notes:
        issues.append("adapter must be visibly marked as dry-run")
    if runtime_status(kernel, runtime) is None:
        issues.append(f"runtime `{runtime}` is not declared by the source kernel")

    adapter_contract = adapter.get("runtime_contract", {})
    if adapter_contract.get("contract_id") != contract["contract_id"]:
        issues.append("runtime_contract.contract_id does not match contract fixture")
    projection = adapter.get("runtime_projection", {})
    if projection.get("contract_id") != contract["contract_id"]:
        issues.append("runtime_projection.contract_id does not match contract fixture")
    routing_hints = projection.get("routing_hints", {})
    if isinstance(routing_hints, dict) and routing_hints.get(
        "selection_semantics",
    ) != kernel["adapters"].get("selection_semantics", {}):
        issues.append("runtime_projection.routing_hints.selection_semantics drifted from source kernel")
    if projection.get("candidate_directory") != kernel["kernel_id"]:
        issues.append("runtime_projection.candidate_directory must match kernel_id")
    skill_markdown = projection.get("skill_markdown", {})
    frontmatter = skill_markdown.get("frontmatter", {}) if isinstance(skill_markdown, dict) else {}
    if frontmatter.get("name") != kernel["kernel_id"]:
        issues.append("runtime_projection SKILL.md name must map from kernel_id")
    if not isinstance(frontmatter.get("description"), str) or not frontmatter["description"]:
        issues.append("runtime_projection SKILL.md description must be non-empty")
    else:
        max_chars = contract.get("frontmatter", {}).get("description_max_chars", 500)
        if isinstance(max_chars, int) and len(frontmatter["description"]) > max_chars:
            issues.append("runtime_projection SKILL.md description exceeds runtime limit")
    compatibility = projection.get("compatibility", {})
    if compatibility.get("installable_now") is not False:
        issues.append("runtime_projection.compatibility.installable_now must be false")

    return issues


def selected_runtimes(kernel: dict[str, Any], requested: str) -> list[str]:
    runtimes = [entry["runtime"] for entry in declared_runtimes(kernel)]
    if requested == "all":
        return runtimes
    return [requested]


def build_bundle(
    kernel_paths: list[Path],
    requested_runtime: str,
    contracts: dict[str, Any],
) -> dict[str, Any]:
    adapters: list[dict[str, Any]] = []
    for kernel_path in kernel_paths:
        kernel = load_kernel(kernel_path)
        for runtime in selected_runtimes(kernel, requested_runtime):
            adapters.append(build_adapter(kernel, kernel_path, runtime, contracts))

    return {
        "bundle_schema_version": ADAPTER_SCHEMA_VERSION,
        "dry_run": True,
        "source_of_truth": "kernel",
        "runtime_contracts": {
            "schema_version": contracts.get("schema_version"),
            "source_basis": contracts.get("source_basis", []),
        },
        "adapter_count": len(adapters),
        "adapters": adapters,
    }


def check_bundle(
    bundle: dict[str, Any],
    kernel_paths: list[Path],
    contracts: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    kernels_by_source = {
        repo_relative(path): load_kernel(path)
        for path in kernel_paths
    }

    for idx, adapter in enumerate(bundle.get("adapters", []), start=1):
        if not isinstance(adapter, dict):
            issues.append(f"adapter #{idx} is not a JSON object")
            continue
        source = adapter.get("generated_from")
        runtime = adapter.get("runtime")
        if not isinstance(source, str) or source not in kernels_by_source:
            issues.append(f"adapter #{idx} generated_from is unknown: {source!r}")
            continue
        if not isinstance(runtime, str):
            issues.append(f"adapter #{idx} runtime is missing")
            continue
        kernel = kernels_by_source[source]
        for issue in validate_adapter(kernel, adapter, runtime, contracts):
            issues.append(f"{source} [{runtime}]: {issue}")

    if bundle.get("adapter_count") != len(bundle.get("adapters", [])):
        issues.append("adapter_count does not match adapters length")
    if bundle.get("source_of_truth") != "kernel":
        issues.append("bundle source_of_truth must be `kernel`")
    if bundle.get("dry_run") is not True:
        issues.append("bundle must be marked dry_run=true")

    return issues


def write_adapters(bundle: dict[str, Any], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for adapter in bundle["adapters"]:
        kernel_id = adapter["kernel"]["kernel_id"]
        runtime = adapter["runtime"]
        path = output_dir / f"{kernel_id}.{runtime}.adapter.json"
        path.write_text(json.dumps(adapter, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    return written


def write_preview_skill_fixtures(bundle: dict[str, Any], output_root: Path) -> list[Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    fixture_entries: list[dict[str, Any]] = []

    for adapter in bundle["adapters"]:
        skill_dir = preview_skill_dir(adapter, output_root)
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_path = skill_dir / "SKILL.md"
        skill_path.write_text(render_preview_skill_markdown(adapter), encoding="utf-8")
        written.append(skill_path)

        interface_projection = adapter["runtime_projection"].get("interface_metadata")
        interface_path = None
        if isinstance(interface_projection, dict):
            interface_path = skill_dir / interface_projection["path"]
            interface_path.parent.mkdir(parents=True, exist_ok=True)
            interface_path.write_text(render_interface_yaml(interface_projection), encoding="utf-8")
            written.append(interface_path)

        fixture_entries.append(
            {
                "runtime": adapter["runtime"],
                "kernel_id": adapter["kernel"]["kernel_id"],
                "skill_dir": str(skill_dir.relative_to(output_root)),
                "skill_markdown": str(skill_path.relative_to(output_root)),
                "interface_metadata": (
                    str(interface_path.relative_to(output_root))
                    if interface_path is not None
                    else None
                ),
                "generated_from": adapter["generated_from"],
                "contract_id": adapter["runtime_projection"]["contract_id"],
                "preview_only": True,
                "installable": False,
            }
        )

    manifest = {
        "preview_schema_version": ADAPTER_SCHEMA_VERSION,
        "dry_run": True,
        "source_of_truth": "kernel",
        "adapter_count": bundle["adapter_count"],
        "fixture_count": len(fixture_entries),
        "fixtures": fixture_entries,
    }
    manifest_path = output_root / "preview-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    written.append(manifest_path)
    return written


def build_installable_manifest(adapter: dict[str, Any]) -> dict[str, Any]:
    projection = adapter["runtime_projection"]
    skill_markdown = projection["skill_markdown"]
    hints = projection["routing_hints"]
    field_mapping = projection["field_mapping"]
    runtime_contract = adapter["runtime_contract"]
    selection_semantics = adapter["selection_semantics"]

    manifest: dict[str, Any] = {
        "manifest_schema_version": INSTALLABLE_MANIFEST_SCHEMA_VERSION,
        "adapter_schema_version": adapter["adapter_schema_version"],
        "prototype": True,
        "safe_to_install_automatically": False,
        "manual_review_required": True,
        "source_of_truth": adapter["source_of_truth"],
        "generated_from": adapter["generated_from"],
        "runtime": adapter["runtime"],
        "runtime_status": adapter["runtime_status"],
        "runtime_contract": {
            "contract_id": projection["contract_id"],
            "support_level": projection["support_level"],
            "skill_roots": runtime_contract["skill_roots"],
        },
        "kernel": adapter["kernel"],
        "install_target": {
            "skill_directory": projection["candidate_directory"],
            "candidate_roots": runtime_contract["skill_roots"],
            "required_files": projection["required_files"],
            "optional_files": projection.get("optional_files", []),
        },
        "skill_markdown": {
            "path": skill_markdown["path"],
            "status": "candidate-generated-from-kernel",
            "frontmatter": skill_markdown["frontmatter"],
            "body_sources": skill_markdown.get("body_sources", []),
        },
        "routing_hints": {
            "profile_name": hints["profile_name"],
            "entrypoints": hints["entrypoints"],
            "routers": hints["routers"],
            "required_skills": hints["required_skills"],
            "optional_skills": hints["optional_skills"],
        },
        "selection_semantics": selection_semantics,
        "kernel_source_paths": adapter["kernel"]["source_paths"],
        "non_authoritative_kernel_fields": field_mapping.get("docs_only", []),
        "forbidden_authoritative_fields": field_mapping.get(
            "never_authoritative_in_adapter",
            [],
        ),
        "review_gates": [
            {
                "id": "kernel-source-of-truth",
                "status": "passed",
                "summary": "Manifest is generated from the checked kernel and does not replace it.",
            },
            {
                "id": "selection-semantics-preserved",
                "status": "passed",
                "summary": "Runtime selection semantics are copied from adapters.selection_semantics.",
            },
            {
                "id": "docs-only-fields-not-authoritative",
                "status": "passed",
                "summary": "Workflow, validation, memory, install policy, and promotion stay non-authoritative in this manifest.",
            },
            {
                "id": "manual-review-required",
                "status": "passed",
                "summary": "The prototype is not safe for automatic installation.",
            },
        ],
        "runtime_notes": [
            "prototype installable manifest only; do not install automatically",
            "regenerate from schemas/skill-kernel examples instead of editing manifest output",
            "runtime files must stay thin adapters around the kernel source of truth",
        ],
    }

    interface_projection = projection.get("interface_metadata")
    if isinstance(interface_projection, dict):
        manifest["interface_metadata"] = {
            "path": interface_projection["path"],
            "status": interface_projection["status"],
            "data": interface_projection["data"],
        }
    return manifest


def render_exercised_skill_markdown(manifest: dict[str, Any]) -> str:
    skill_markdown = manifest["skill_markdown"]
    frontmatter = skill_markdown["frontmatter"]
    hints = manifest["routing_hints"]
    selection_semantics = manifest["selection_semantics"]

    lines = [
        render_frontmatter(frontmatter).rstrip(),
        f"# {title_from_hyphen_name(frontmatter['name'])} Session Exercise",
        "",
        "This is a session-only runtime exercise generated from a review-gated installable manifest.",
        "Do not copy it into a global skill directory; regenerate it from the kernel and manifest.",
        "",
        "## Runtime",
        "",
        f"- Runtime: `{manifest['runtime']}`",
        f"- Contract: `{manifest['runtime_contract']['contract_id']}`",
        f"- Generated from: `{manifest['generated_from']}`",
        f"- Source of truth: `{manifest['source_of_truth']}`",
        f"- Manual review required: `{str(manifest['manual_review_required']).lower()}`",
        f"- Safe to install automatically: `{str(manifest['safe_to_install_automatically']).lower()}`",
        "",
        "## Routing Exercise",
        "",
        f"- Profile: `{hints['profile_name']}`",
        "- Entrypoints:",
        *markdown_bullets(hints["entrypoints"]),
        "- Routers:",
        *markdown_bullets(hints["routers"]),
        "- Required skills:",
        *markdown_bullets(hints["required_skills"]),
        "- Optional skills:",
        *markdown_bullets(hints["optional_skills"]),
        "- Selection semantics:",
        *markdown_bullets(
            [
                "runtime_expectation: "
                f"{selection_semantics.get('runtime_expectation', 'unspecified')}",
                "delegation_policy: "
                f"{selection_semantics.get('delegation_policy', 'unspecified')}",
            ]
        ),
        "",
        "## Kernel Sources",
        "",
        *markdown_bullets(manifest.get("kernel_source_paths", [])),
        "",
        "## Manifest Review Gates",
        "",
        *markdown_bullets(
            [
                f"{gate['id']}: {gate['status']}"
                for gate in manifest.get("review_gates", [])
                if isinstance(gate, dict) and "id" in gate and "status" in gate
            ]
        ),
        "",
        "## Adapter Boundary",
        "",
        "The following kernel fields remain non-authoritative in this runtime exercise:",
        *markdown_bullets(manifest.get("non_authoritative_kernel_fields", [])),
        "",
        "Never treat this session-only exercise as proof that global installs were modified.",
    ]
    return "\n".join(lines) + "\n"


def render_installed_skill_markdown(manifest: dict[str, Any]) -> str:
    """Render SKILL.md for a real reviewed-plan install (not a session exercise).

    Structurally identical to ``render_exercised_skill_markdown`` so the
    frontmatter and metadata sections stay consistent, but the body wording
    reflects that this file is the result of a reviewed install, not a
    session-only exercise.
    """

    skill_markdown = manifest["skill_markdown"]
    frontmatter = skill_markdown["frontmatter"]
    hints = manifest["routing_hints"]
    selection_semantics = manifest["selection_semantics"]

    lines = [
        render_frontmatter(frontmatter).rstrip(),
        f"# {title_from_hyphen_name(frontmatter['name'])}",
        "",
        "This skill file was generated by a reviewed install plan from the",
        "owner kernel. The kernel remains the source of truth — regenerate from",
        "the kernel rather than editing this file.",
        "",
        "## Runtime",
        "",
        f"- Runtime: `{manifest['runtime']}`",
        f"- Contract: `{manifest['runtime_contract']['contract_id']}`",
        f"- Generated from: `{manifest['generated_from']}`",
        f"- Source of truth: `{manifest['source_of_truth']}`",
        "",
        "## Routing",
        "",
        f"- Profile: `{hints['profile_name']}`",
        "- Entrypoints:",
        *markdown_bullets(hints["entrypoints"]),
        "- Routers:",
        *markdown_bullets(hints["routers"]),
        "- Required skills:",
        *markdown_bullets(hints["required_skills"]),
        "- Optional skills:",
        *markdown_bullets(hints["optional_skills"]),
        "- Selection semantics:",
        *markdown_bullets(
            [
                "runtime_expectation: "
                f"{selection_semantics.get('runtime_expectation', 'unspecified')}",
                "delegation_policy: "
                f"{selection_semantics.get('delegation_policy', 'unspecified')}",
            ]
        ),
        "",
        "## Kernel Sources",
        "",
        *markdown_bullets(manifest.get("kernel_source_paths", [])),
        "",
        "## Adapter Boundary",
        "",
        "The following kernel fields remain non-authoritative for this runtime adapter:",
        *markdown_bullets(manifest.get("non_authoritative_kernel_fields", [])),
        "",
        "Regenerate from the kernel rather than editing this file in place.",
    ]
    return "\n".join(lines) + "\n"


def load_manifest_index(manifest_root: Path) -> dict[str, Any]:
    index_path = manifest_root / "installable-manifest-index.json"
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{index_path} is missing") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{index_path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{index_path} must contain a JSON object")
    return data


def load_manifests_from_root(manifest_root: Path) -> list[dict[str, Any]]:
    index = load_manifest_index(manifest_root)
    entries = index.get("manifests")
    if not isinstance(entries, list):
        raise ValueError("installable-manifest-index.json must contain a manifests list")

    manifests: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("manifest"), str):
            raise ValueError("manifest index entries must contain a manifest path")
        manifest_path = manifest_root / entry["manifest"]
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ValueError(f"{manifest_path} is missing") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"{manifest_path} is not valid JSON: {exc}") from exc
        if not isinstance(manifest, dict):
            raise ValueError(f"{manifest_path} must contain a JSON object")
        manifests.append(manifest)
    return manifests


def write_manifest_exercise_fixtures(
    manifest_root: Path,
    output_root: Path,
) -> list[Path]:
    root_issues = validate_session_only_root(output_root)
    if root_issues:
        raise ValueError("; ".join(root_issues))

    manifests = load_manifests_from_root(manifest_root)
    output_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    fixture_entries: list[dict[str, Any]] = []

    for manifest in manifests:
        skill_dir = exercise_skill_dir(manifest, output_root)
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_path = skill_dir / manifest["skill_markdown"]["path"]
        skill_path.write_text(render_exercised_skill_markdown(manifest), encoding="utf-8")
        written.append(skill_path)

        interface_projection = manifest.get("interface_metadata")
        interface_path = None
        if isinstance(interface_projection, dict):
            interface_path = skill_dir / interface_projection["path"]
            interface_path.parent.mkdir(parents=True, exist_ok=True)
            interface_path.write_text(render_interface_yaml(interface_projection), encoding="utf-8")
            written.append(interface_path)

        fixture_entries.append(
            {
                "runtime": manifest["runtime"],
                "kernel_id": manifest["kernel"]["kernel_id"],
                "skill_dir": str(skill_dir.relative_to(output_root)),
                "skill_markdown": str(skill_path.relative_to(output_root)),
                "interface_metadata": (
                    str(interface_path.relative_to(output_root))
                    if interface_path is not None
                    else None
                ),
                "manifest": str(
                    (
                        manifest_root
                        / manifest["runtime"]
                        / manifest["install_target"]["skill_directory"]
                        / "adapter-manifest.json"
                    ).relative_to(manifest_root)
                ),
                "selection_expectation": manifest["selection_semantics"].get(
                    "runtime_expectation",
                    "unspecified",
                ),
                "session_only": True,
                "global_install_modified": False,
            }
        )

    exercise_summary = {
        "exercise_schema_version": MANIFEST_EXERCISE_SCHEMA_VERSION,
        "manifest_schema_version": INSTALLABLE_MANIFEST_SCHEMA_VERSION,
        "session_only": True,
        "global_install_modified": False,
        "source_of_truth": "kernel",
        "manifest_root": str(manifest_root),
        "exercise_count": len(fixture_entries),
        "fixtures": fixture_entries,
    }
    summary_path = output_root / "manifest-exercise-summary.json"
    summary_path.write_text(
        json.dumps(exercise_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    written.append(summary_path)
    return written


def write_installable_manifests(bundle: dict[str, Any], output_root: Path) -> list[Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    manifest_entries: list[dict[str, Any]] = []

    for adapter in bundle["adapters"]:
        manifest_dir = installable_manifest_dir(adapter, output_root)
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "adapter-manifest.json"
        manifest = build_installable_manifest(adapter)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written.append(manifest_path)

        manifest_entries.append(
            {
                "runtime": adapter["runtime"],
                "kernel_id": adapter["kernel"]["kernel_id"],
                "manifest": str(manifest_path.relative_to(output_root)),
                "generated_from": adapter["generated_from"],
                "contract_id": adapter["runtime_projection"]["contract_id"],
                "selection_expectation": adapter["selection_semantics"].get(
                    "runtime_expectation",
                    "unspecified",
                ),
                "prototype": True,
                "safe_to_install_automatically": False,
            }
        )

    index = {
        "manifest_index_schema_version": INSTALLABLE_MANIFEST_SCHEMA_VERSION,
        "adapter_schema_version": ADAPTER_SCHEMA_VERSION,
        "prototype": True,
        "safe_to_install_automatically": False,
        "manual_review_required": True,
        "source_of_truth": "kernel",
        "adapter_count": bundle["adapter_count"],
        "manifest_count": len(manifest_entries),
        "manifests": manifest_entries,
    }
    index_path = output_root / "installable-manifest-index.json"
    index_path.write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    written.append(index_path)
    return written


def smoke_preview_skill_fixtures(bundle: dict[str, Any], output_root: Path) -> list[str]:
    issues: list[str] = []
    seen_dirs: set[Path] = set()

    for adapter in bundle["adapters"]:
        runtime = adapter["runtime"]
        projection = adapter["runtime_projection"]
        skill_dir = preview_skill_dir(adapter, output_root)
        if skill_dir in seen_dirs:
            issues.append(f"{runtime}/{skill_dir.name}: duplicate preview skill directory")
            continue
        seen_dirs.add(skill_dir)

        skill_path = skill_dir / projection["skill_markdown"]["path"]
        if not skill_path.is_file():
            issues.append(f"{runtime}/{skill_dir.name}: missing SKILL.md")
            continue

        text = skill_path.read_text(encoding="utf-8")
        try:
            metadata = parse_generated_frontmatter(text)
        except ValueError as exc:
            issues.append(f"{runtime}/{skill_dir.name}: invalid SKILL.md frontmatter: {exc}")
            continue

        expected_frontmatter = projection["skill_markdown"]["frontmatter"]
        if metadata.get("name") != expected_frontmatter["name"]:
            issues.append(f"{runtime}/{skill_dir.name}: frontmatter name does not match projection")
        if metadata.get("name") != skill_dir.name:
            issues.append(f"{runtime}/{skill_dir.name}: frontmatter name does not match directory")
        description = metadata.get("description")
        if not description:
            issues.append(f"{runtime}/{skill_dir.name}: frontmatter description is empty")
        else:
            max_chars = adapter["runtime_contract"]["frontmatter"].get(
                "description_max_chars",
                500,
            )
            if isinstance(max_chars, int) and len(description) > max_chars:
                issues.append(f"{runtime}/{skill_dir.name}: description exceeds runtime limit")

        if "preview-only" not in text:
            issues.append(f"{runtime}/{skill_dir.name}: body missing preview-only marker")
        if "Source of truth: `kernel`" not in text:
            issues.append(f"{runtime}/{skill_dir.name}: body missing kernel source-of-truth marker")
        if "Installable now: `false`" not in text:
            issues.append(f"{runtime}/{skill_dir.name}: body missing non-installable marker")

        interface_projection = projection.get("interface_metadata")
        if isinstance(interface_projection, dict):
            interface_path = skill_dir / interface_projection["path"]
            if not interface_path.is_file():
                issues.append(f"{runtime}/{skill_dir.name}: missing interface metadata fixture")

    manifest_path = output_root / "preview-manifest.json"
    if not manifest_path.is_file():
        issues.append("preview-manifest.json is missing")
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(f"preview-manifest.json is not valid JSON: {exc}")
        else:
            if manifest.get("fixture_count") != len(bundle["adapters"]):
                issues.append("preview-manifest.json fixture_count does not match adapter count")
            if manifest.get("source_of_truth") != "kernel":
                issues.append("preview-manifest.json source_of_truth must be `kernel`")
            if manifest.get("dry_run") is not True:
                issues.append("preview-manifest.json must be dry_run=true")

    return issues


def smoke_installable_manifests(bundle: dict[str, Any], output_root: Path) -> list[str]:
    issues: list[str] = []
    seen_dirs: set[Path] = set()
    forbidden_top_level = {"workflow", "memory", "validation", "promotion", "install_policy"}
    required_gate_ids = {
        "kernel-source-of-truth",
        "selection-semantics-preserved",
        "docs-only-fields-not-authoritative",
        "manual-review-required",
    }

    for adapter in bundle["adapters"]:
        runtime = adapter["runtime"]
        projection = adapter["runtime_projection"]
        manifest_dir = installable_manifest_dir(adapter, output_root)
        if manifest_dir in seen_dirs:
            issues.append(f"{runtime}/{manifest_dir.name}: duplicate manifest directory")
            continue
        seen_dirs.add(manifest_dir)

        manifest_path = manifest_dir / "adapter-manifest.json"
        if not manifest_path.is_file():
            issues.append(f"{runtime}/{manifest_dir.name}: missing adapter-manifest.json")
            continue

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(f"{runtime}/{manifest_dir.name}: manifest is not valid JSON: {exc}")
            continue

        if manifest.get("manifest_schema_version") != INSTALLABLE_MANIFEST_SCHEMA_VERSION:
            issues.append(f"{runtime}/{manifest_dir.name}: wrong manifest schema version")
        if manifest.get("prototype") is not True:
            issues.append(f"{runtime}/{manifest_dir.name}: manifest must be prototype=true")
        if manifest.get("safe_to_install_automatically") is not False:
            issues.append(f"{runtime}/{manifest_dir.name}: manifest must block automatic installation")
        if manifest.get("manual_review_required") is not True:
            issues.append(f"{runtime}/{manifest_dir.name}: manifest must require manual review")
        if manifest.get("source_of_truth") != "kernel":
            issues.append(f"{runtime}/{manifest_dir.name}: source_of_truth must be `kernel`")
        if forbidden_top_level.intersection(manifest):
            fields = ", ".join(sorted(forbidden_top_level.intersection(manifest)))
            issues.append(
                f"{runtime}/{manifest_dir.name}: authoritative docs-only field(s) leaked: {fields}"
            )
        if manifest.get("selection_semantics") != adapter["selection_semantics"]:
            issues.append(f"{runtime}/{manifest_dir.name}: selection_semantics drifted")
        if manifest.get("kernel") != adapter["kernel"]:
            issues.append(f"{runtime}/{manifest_dir.name}: kernel summary drifted")
        if manifest.get("kernel_source_paths") != adapter["kernel"]["source_paths"]:
            issues.append(f"{runtime}/{manifest_dir.name}: kernel_source_paths drifted")
        if any(str(path).startswith("/") for path in manifest.get("kernel_source_paths", [])):
            issues.append(f"{runtime}/{manifest_dir.name}: kernel_source_paths must be repo-relative")

        install_target = manifest.get("install_target", {})
        if install_target.get("skill_directory") != projection["candidate_directory"]:
            issues.append(f"{runtime}/{manifest_dir.name}: install target does not match projection")
        if install_target.get("required_files") != projection["required_files"]:
            issues.append(f"{runtime}/{manifest_dir.name}: required files drifted")

        skill_markdown = manifest.get("skill_markdown", {})
        frontmatter = skill_markdown.get("frontmatter", {}) if isinstance(skill_markdown, dict) else {}
        if frontmatter.get("name") != projection["candidate_directory"]:
            issues.append(f"{runtime}/{manifest_dir.name}: frontmatter name does not match directory")
        if skill_markdown.get("body_sources") != projection["skill_markdown"].get("body_sources"):
            issues.append(f"{runtime}/{manifest_dir.name}: SKILL.md body sources drifted")

        runtime_contract = manifest.get("runtime_contract", {})
        if runtime_contract.get("contract_id") != projection["contract_id"]:
            issues.append(f"{runtime}/{manifest_dir.name}: runtime contract id drifted")
        if runtime_contract.get("support_level") != projection["support_level"]:
            issues.append(f"{runtime}/{manifest_dir.name}: runtime support level drifted")

        gate_ids = {
            gate.get("id")
            for gate in manifest.get("review_gates", [])
            if isinstance(gate, dict)
        }
        missing_gates = required_gate_ids.difference(gate_ids)
        if missing_gates:
            issues.append(
                f"{runtime}/{manifest_dir.name}: missing review gate(s): "
                f"{', '.join(sorted(missing_gates))}"
            )

    index_path = output_root / "installable-manifest-index.json"
    if not index_path.is_file():
        issues.append("installable-manifest-index.json is missing")
    else:
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(f"installable-manifest-index.json is not valid JSON: {exc}")
        else:
            if index.get("manifest_count") != len(bundle["adapters"]):
                issues.append("installable-manifest-index.json manifest_count does not match adapter count")
            if index.get("source_of_truth") != "kernel":
                issues.append("installable-manifest-index.json source_of_truth must be `kernel`")
            if index.get("prototype") is not True:
                issues.append("installable-manifest-index.json must be prototype=true")
            if index.get("safe_to_install_automatically") is not False:
                issues.append("installable-manifest-index.json must block automatic installation")

    return issues


def smoke_manifest_exercise(manifest_root: Path, output_root: Path) -> list[str]:
    issues: list[str] = []
    issues.extend(validate_session_only_root(output_root))
    try:
        manifests = load_manifests_from_root(manifest_root)
    except ValueError as exc:
        return [str(exc)]

    seen_dirs: set[Path] = set()
    for manifest in manifests:
        runtime = manifest.get("runtime", "unknown-runtime")
        install_target = manifest.get("install_target", {})
        skill_name = install_target.get("skill_directory", "unknown-skill")
        skill_dir = exercise_skill_dir(manifest, output_root)
        if skill_dir in seen_dirs:
            issues.append(f"{runtime}/{skill_name}: duplicate exercise skill directory")
            continue
        seen_dirs.add(skill_dir)

        skill_path = skill_dir / manifest["skill_markdown"]["path"]
        if not skill_path.is_file():
            issues.append(f"{runtime}/{skill_name}: missing exercised SKILL.md")
            continue

        text = skill_path.read_text(encoding="utf-8")
        try:
            metadata = parse_generated_frontmatter(text)
        except ValueError as exc:
            issues.append(f"{runtime}/{skill_name}: invalid SKILL.md frontmatter: {exc}")
            continue

        expected_frontmatter = manifest["skill_markdown"]["frontmatter"]
        if metadata.get("name") != expected_frontmatter["name"]:
            issues.append(f"{runtime}/{skill_name}: frontmatter name does not match manifest")
        if metadata.get("name") != skill_dir.name:
            issues.append(f"{runtime}/{skill_name}: frontmatter name does not match directory")
        description = metadata.get("description")
        if not description:
            issues.append(f"{runtime}/{skill_name}: frontmatter description is empty")

        if "session-only runtime exercise" not in text:
            issues.append(f"{runtime}/{skill_name}: body missing session-only marker")
        if "Source of truth: `kernel`" not in text:
            issues.append(f"{runtime}/{skill_name}: body missing kernel source-of-truth marker")
        if "Manual review required: `true`" not in text:
            issues.append(f"{runtime}/{skill_name}: body missing manual-review marker")
        if "Safe to install automatically: `false`" not in text:
            issues.append(f"{runtime}/{skill_name}: body missing no-auto-install marker")
        expected_semantics = manifest["selection_semantics"].get(
            "runtime_expectation",
            "unspecified",
        )
        if expected_semantics not in text:
            issues.append(f"{runtime}/{skill_name}: body missing selection semantics")

        interface_projection = manifest.get("interface_metadata")
        if isinstance(interface_projection, dict):
            interface_path = skill_dir / interface_projection["path"]
            if not interface_path.is_file():
                issues.append(f"{runtime}/{skill_name}: missing exercised interface metadata")

    summary_path = output_root / "manifest-exercise-summary.json"
    if not summary_path.is_file():
        issues.append("manifest-exercise-summary.json is missing")
    else:
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(f"manifest-exercise-summary.json is not valid JSON: {exc}")
        else:
            if summary.get("exercise_count") != len(manifests):
                issues.append("manifest-exercise-summary.json exercise_count does not match manifest count")
            if summary.get("source_of_truth") != "kernel":
                issues.append("manifest-exercise-summary.json source_of_truth must be `kernel`")
            if summary.get("session_only") is not True:
                issues.append("manifest-exercise-summary.json must be session_only=true")
            if summary.get("global_install_modified") is not False:
                issues.append("manifest-exercise-summary.json must record global_install_modified=false")

    return issues


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate dry-run runtime adapter metadata from skill-kernel examples."
    )
    parser.add_argument(
        "kernels",
        nargs="*",
        type=Path,
        help="Kernel JSON files. Defaults to schemas/skill-kernel/examples/*.json.",
    )
    parser.add_argument(
        "--runtime",
        choices=RUNTIME_CHOICES,
        default="generic-agent",
        help="Runtime to export. Use `all` for each runtime declared by each kernel.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Write one dry-run adapter JSON file per kernel/runtime instead of printing the bundle.",
    )
    parser.add_argument(
        "--preview-skill-root",
        type=Path,
        help=(
            "Write preview-only runtime-like skill directories under "
            "<root>/<runtime>/<skill-name>/ and smoke-test the generated SKILL.md files."
        ),
    )
    parser.add_argument(
        "--installable-manifest-root",
        type=Path,
        help=(
            "Write review-gated prototype installable adapter manifests under "
            "<root>/<runtime>/<skill-name>/ without writing installable skill files."
        ),
    )
    parser.add_argument(
        "--exercise-skill-root",
        type=Path,
        help=(
            "When combined with --installable-manifest-root, re-read the generated "
            "manifests and write session-only runtime-like skill directories under "
            "<root>/<runtime>/<skill-name>/ without modifying global installs."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate generated adapters and print a short PASS/FAIL summary without writing files.",
    )
    parser.add_argument(
        "--contracts",
        type=Path,
        default=DEFAULT_CONTRACTS_PATH,
        help="Runtime adapter contract fixture. Defaults to schemas/skill-kernel/runtime-adapter-contracts.json.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    output_options = [
        args.output_dir,
        args.preview_skill_root,
        args.installable_manifest_root,
    ]
    if args.exercise_skill_root and not args.installable_manifest_root:
        print("--exercise-skill-root requires --installable-manifest-root", file=sys.stderr)
        return 2
    if args.check and any(output_options):
        print("--check cannot be combined with output-writing options", file=sys.stderr)
        return 2
    if sum(option is not None for option in output_options) > 1:
        print(
            "--output-dir, --preview-skill-root, and --installable-manifest-root "
            "are mutually exclusive",
            file=sys.stderr,
        )
        return 2
    if args.exercise_skill_root:
        root_issues = validate_session_only_root(args.exercise_skill_root)
        if root_issues:
            for issue in root_issues:
                print(f"--exercise-skill-root is unsafe: {issue}", file=sys.stderr)
            return 2

    kernel_paths = [path if path.is_absolute() else REPO_ROOT / path for path in args.kernels]
    if not kernel_paths:
        kernel_paths = default_kernel_paths()
    if not kernel_paths:
        print("No kernel JSON files found.", file=sys.stderr)
        return 1

    try:
        contracts_path = args.contracts if args.contracts.is_absolute() else REPO_ROOT / args.contracts
        contracts = load_runtime_contracts(contracts_path)
        bundle = build_bundle(kernel_paths, args.runtime, contracts)
        issues = check_bundle(bundle, kernel_paths, contracts)
    except (KeyError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if issues:
        print("FAIL: generated adapters did not preserve kernel contracts", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    if args.check:
        print(
            "PASS: generated "
            f"{bundle['adapter_count']} dry-run adapter(s) from {len(kernel_paths)} kernel(s)"
        )
        return 0

    if args.output_dir:
        written = write_adapters(bundle, args.output_dir)
        summary = {
            "bundle_schema_version": ADAPTER_SCHEMA_VERSION,
            "dry_run": True,
            "source_of_truth": "kernel",
            "adapter_count": len(written),
            "output_dir": str(args.output_dir),
            "files": [str(path) for path in written],
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    if args.preview_skill_root:
        written = write_preview_skill_fixtures(bundle, args.preview_skill_root)
        preview_issues = smoke_preview_skill_fixtures(bundle, args.preview_skill_root)
        if preview_issues:
            print("FAIL: generated preview skill fixtures did not pass smoke checks", file=sys.stderr)
            for issue in preview_issues:
                print(f"- {issue}", file=sys.stderr)
            return 1
        summary = {
            "bundle_schema_version": ADAPTER_SCHEMA_VERSION,
            "dry_run": True,
            "source_of_truth": "kernel",
            "adapter_count": bundle["adapter_count"],
            "fixture_count": bundle["adapter_count"],
            "preview_skill_root": str(args.preview_skill_root),
            "smoke_check": "passed",
            "files": [str(path) for path in written],
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    if args.installable_manifest_root:
        written = write_installable_manifests(bundle, args.installable_manifest_root)
        manifest_issues = smoke_installable_manifests(
            bundle,
            args.installable_manifest_root,
        )
        if manifest_issues:
            print("FAIL: generated installable manifests did not pass smoke checks", file=sys.stderr)
            for issue in manifest_issues:
                print(f"- {issue}", file=sys.stderr)
            return 1
        exercise_written: list[Path] = []
        exercise_smoke_check = None
        if args.exercise_skill_root:
            try:
                exercise_written = write_manifest_exercise_fixtures(
                    args.installable_manifest_root,
                    args.exercise_skill_root,
                )
            except ValueError as exc:
                print(f"FAIL: could not write manifest exercise fixtures: {exc}", file=sys.stderr)
                return 1
            exercise_issues = smoke_manifest_exercise(
                args.installable_manifest_root,
                args.exercise_skill_root,
            )
            if exercise_issues:
                print("FAIL: generated manifest exercise fixtures did not pass smoke checks", file=sys.stderr)
                for issue in exercise_issues:
                    print(f"- {issue}", file=sys.stderr)
                return 1
            exercise_smoke_check = "passed"
        summary = {
            "bundle_schema_version": ADAPTER_SCHEMA_VERSION,
            "manifest_schema_version": INSTALLABLE_MANIFEST_SCHEMA_VERSION,
            "prototype": True,
            "safe_to_install_automatically": False,
            "manual_review_required": True,
            "source_of_truth": "kernel",
            "adapter_count": bundle["adapter_count"],
            "manifest_count": bundle["adapter_count"],
            "installable_manifest_root": str(args.installable_manifest_root),
            "smoke_check": "passed",
            "files": [str(path) for path in written],
        }
        if args.exercise_skill_root:
            summary.update(
                {
                    "exercise_schema_version": MANIFEST_EXERCISE_SCHEMA_VERSION,
                    "exercise_skill_root": str(args.exercise_skill_root),
                    "exercise_count": bundle["adapter_count"],
                    "exercise_smoke_check": exercise_smoke_check,
                    "session_only": True,
                    "global_install_modified": False,
                    "exercise_files": [str(path) for path in exercise_written],
                }
            )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    print(json.dumps(bundle, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
