#!/usr/bin/env python3
"""Repository validator for ml-research-skills.

Checks:
1. Every skill has a parseable YAML frontmatter block.
2. The frontmatter `name` matches the skill directory name.
3. Common helper-file references in `SKILL.md` exist.
4. Skill instructions do not hardcode Claude-only install paths.
5. Template placeholders are well-formed.
6. Top-level docs list the current skill inventory correctly.
7. Python and shell helper scripts pass a basic syntax check.
8. tests/routing-evals.json references only real skill names.
"""

from __future__ import annotations

import json
import os
import py_compile
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "skills"
SKILL_NAME_RE = re.compile(r"^[a-z0-9-]+$")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
RELATIVE_SUPPORT_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_])((?:scripts|templates|references|assets)/[A-Za-z0-9_./-]+)"
)
SKILL_DIR_PLACEHOLDER_RE = re.compile(r"<([a-z0-9-]+)-skill-dir>/(.+)")
CLAUDE_ONLY_PATH_RE = re.compile(r"~/.claude/skills/")
COMMON_SUPPORT_FILES = ("sources.yaml", "environments.yaml", "checklist.md")
PLACEHOLDER_RE = re.compile(r"\{\{([A-Za-z0-9_]+)\}\}")
VALID_PLACEHOLDER_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
SKILL_TABLE_ENTRY_RE = re.compile(r"^\|\s*`([a-z0-9-]+)`\s*\|")
DOC_SKILL_TABLES = (
    REPO_ROOT / "README.md",
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "CLAUDE.md",
)
MANIFEST_FILE_NAME = "template_manifest.json"
TEXT_TEMPLATE_SUFFIXES = {
    ".md",
    ".txt",
    ".py",
    ".sh",
    ".tex",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".cfg",
    ".ini",
    ".rst",
    ".bib",
    ".cff",
}


@dataclass(frozen=True)
class Issue:
    path: Path
    message: str


def extract_frontmatter(text: str) -> str | None:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    return match.group(1)


def parse_yaml(frontmatter: str) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return parse_yaml_with_ruby(frontmatter)

    parsed = yaml.safe_load(frontmatter)
    if not isinstance(parsed, dict):
        raise ValueError("frontmatter must parse to a mapping")
    return parsed


def parse_yaml_with_ruby(frontmatter: str) -> dict[str, Any]:
    cmd = [
        "ruby",
        "-r",
        "yaml",
        "-r",
        "json",
        "-e",
        (
            "data = YAML.safe_load(ARGF.read, permitted_classes: [], aliases: false); "
            "abort('frontmatter must parse to a mapping') unless data.is_a?(Hash); "
            "puts JSON.generate(data)"
        ),
    ]
    proc = subprocess.run(
        cmd,
        input=frontmatter,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "unknown YAML parse error"
        raise ValueError(detail)
    parsed = json.loads(proc.stdout)
    if not isinstance(parsed, dict):
        raise ValueError("frontmatter must parse to a mapping")
    return parsed


def is_allowed_claude_path_line(line: str) -> bool:
    allowed_markers = (
        "Do not assume",
        "for example",
        "such as",
        "target agent's skill home",
    )
    return any(marker in line for marker in allowed_markers)


def iter_helper_refs(skill_dir: Path, text: str) -> list[tuple[int, str]]:
    refs: list[tuple[int, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        explicit_placeholder = None
        placeholder_match = SKILL_DIR_PLACEHOLDER_RE.search(line)
        if placeholder_match:
            explicit_placeholder = placeholder_match.group(1)
            if explicit_placeholder != skill_dir.name:
                continue

        helper_context = any(
            marker in line
            for marker in (
                "<installed-skill-dir>/",
                f"<{skill_dir.name}-skill-dir>/",
                "├──",
                "└──",
                "│",
            )
        )
        if not helper_context and explicit_placeholder is None:
            continue

        for match in RELATIVE_SUPPORT_PATH_RE.finditer(line):
            refs.append((line_no, match.group(1).rstrip(".,)")))

        for basename in COMMON_SUPPORT_FILES:
            if basename in line:
                refs.append((line_no, basename))

    return refs


def validate_skill(skill_dir: Path) -> list[Issue]:
    issues: list[Issue] = []
    skill_file = skill_dir / "SKILL.md"
    rel_skill_file = skill_file.relative_to(REPO_ROOT)

    if not skill_file.exists():
        return [Issue(rel_skill_file, "missing SKILL.md")]

    text = skill_file.read_text(encoding="utf-8")
    frontmatter = extract_frontmatter(text)
    if frontmatter is None:
        issues.append(Issue(rel_skill_file, "missing YAML frontmatter block"))
        return issues

    try:
        metadata = parse_yaml(frontmatter)
    except Exception as exc:  # noqa: BLE001
        issues.append(Issue(rel_skill_file, f"invalid YAML frontmatter: {exc}"))
        return issues

    name = metadata.get("name")
    if not isinstance(name, str) or not name.strip():
        issues.append(Issue(rel_skill_file, "frontmatter missing non-empty `name`"))
    else:
        if name != skill_dir.name:
            issues.append(
                Issue(
                    rel_skill_file,
                    f"frontmatter name `{name}` does not match directory `{skill_dir.name}`",
                )
            )
        if not SKILL_NAME_RE.fullmatch(name):
            issues.append(Issue(rel_skill_file, f"invalid skill name `{name}`"))

    description = metadata.get("description")
    if not isinstance(description, str) or not description.strip():
        issues.append(Issue(rel_skill_file, "frontmatter missing non-empty `description`"))

    for line_no, line in enumerate(text.splitlines(), start=1):
        if CLAUDE_ONLY_PATH_RE.search(line) and not is_allowed_claude_path_line(line):
            issues.append(
                Issue(
                    rel_skill_file,
                    f"line {line_no} contains hardcoded Claude-only path `~/.claude/skills/`",
                )
            )

    seen_refs: set[str] = set()
    for line_no, ref in iter_helper_refs(skill_dir, text):
        if ref in seen_refs:
            continue
        seen_refs.add(ref)
        if not (skill_dir / ref).exists():
            issues.append(
                Issue(
                    rel_skill_file,
                    f"line {line_no} references missing helper path: `{ref}`",
                )
            )

    return issues


def validate_templates(skill_dir: Path) -> list[Issue]:
    issues: list[Issue] = []
    templates_root = skill_dir / "templates"
    if not templates_root.exists():
        return issues

    for template_file in sorted(path for path in templates_root.rglob("*") if path.is_file()):
        rel = template_file.relative_to(REPO_ROOT)
        if template_file.suffix not in TEXT_TEMPLATE_SUFFIXES and template_file.name not in {
            ".gitignore",
            ".env.example",
            "Dockerfile",
            "Makefile",
        }:
            continue
        try:
            text = template_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            issues.append(Issue(rel, "template looks like a text file but is not valid UTF-8"))
            continue
        placeholders = sorted(set(PLACEHOLDER_RE.findall(text)))
        for placeholder in placeholders:
            if not VALID_PLACEHOLDER_RE.fullmatch(placeholder):
                issues.append(
                    Issue(
                        rel,
                        f"invalid template placeholder `{{{{{placeholder}}}}}`; use upper-case snake case",
                    )
                )
    return issues


def validate_template_manifest(skill_dir: Path) -> list[Issue]:
    issues: list[Issue] = []
    manifest_path = skill_dir / MANIFEST_FILE_NAME
    if not manifest_path.exists():
        return issues

    rel = manifest_path.relative_to(REPO_ROOT)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [Issue(rel, f"invalid manifest JSON: {exc}")]

    if not isinstance(manifest, dict):
        return [Issue(rel, "manifest must be a JSON object")]

    placeholders = manifest.get("placeholders", [])
    if not isinstance(placeholders, list) or not all(isinstance(item, str) for item in placeholders):
        issues.append(Issue(rel, "`placeholders` must be a list of strings"))
    else:
        for placeholder in placeholders:
            if not VALID_PLACEHOLDER_RE.fullmatch(placeholder):
                issues.append(Issue(rel, f"invalid manifest placeholder `{placeholder}`"))

    groups = manifest.get("template_groups", {})
    if not isinstance(groups, dict):
        issues.append(Issue(rel, "`template_groups` must be an object"))
        groups = {}

    for group_name, entries in groups.items():
        if not isinstance(entries, list) or not all(isinstance(item, str) for item in entries):
            issues.append(Issue(rel, f"`template_groups.{group_name}` must be a list of strings"))
            continue
        for entry in entries:
            entry_path = skill_dir / entry
            if not entry_path.exists():
                issues.append(Issue(rel, f"manifest references missing template file `{entry}`"))

    project_types = manifest.get("project_types", {})
    if not isinstance(project_types, dict):
        issues.append(Issue(rel, "`project_types` must be an object"))
        project_types = {}

    for project_type, cfg in project_types.items():
        if not isinstance(cfg, dict):
            issues.append(Issue(rel, f"`project_types.{project_type}` must be an object"))
            continue
        group_names = cfg.get("template_groups", [])
        if not isinstance(group_names, list) or not all(isinstance(item, str) for item in group_names):
            issues.append(Issue(rel, f"`project_types.{project_type}.template_groups` must be a list of strings"))
        else:
            for group_name in group_names:
                if group_name not in groups:
                    issues.append(
                        Issue(
                            rel,
                            f"`project_types.{project_type}.template_groups` references unknown group `{group_name}`",
                        )
                    )

    return issues


def validate_doc_skill_tables(skill_names: set[str]) -> list[Issue]:
    issues: list[Issue] = []
    for doc_path in DOC_SKILL_TABLES:
        found: list[str] = []
        for line in doc_path.read_text(encoding="utf-8").splitlines():
            match = SKILL_TABLE_ENTRY_RE.match(line.strip())
            if match:
                found.append(match.group(1))

        found_set = set(found)
        missing = sorted(skill_names - found_set)
        extra = sorted(found_set - skill_names)
        duplicates = sorted({name for name in found if found.count(name) > 1})
        rel = doc_path.relative_to(REPO_ROOT)

        if missing:
            issues.append(Issue(rel, f"skill table missing entries: {', '.join(missing)}"))
        if extra:
            issues.append(Issue(rel, f"skill table contains unknown entries: {', '.join(extra)}"))
        if duplicates:
            issues.append(Issue(rel, f"skill table contains duplicate entries: {', '.join(duplicates)}"))

    return issues


def validate_script_syntax() -> list[Issue]:
    issues: list[Issue] = []

    for py_file in sorted(REPO_ROOT.rglob("*.py")):
        if any(part in {".git", "__pycache__"} for part in py_file.parts):
            continue
        rel = py_file.relative_to(REPO_ROOT)
        text = py_file.read_text(encoding="utf-8")
        if PLACEHOLDER_RE.search(text):
            continue
        try:
            compile(text, str(py_file), "exec")
        except SyntaxError as exc:
            issues.append(Issue(rel, f"python syntax check failed: {exc.msg}"))

    for sh_file in sorted(REPO_ROOT.rglob("*.sh")):
        if any(part == ".git" for part in sh_file.parts):
            continue
        rel = sh_file.relative_to(REPO_ROOT)
        proc = subprocess.run(
            ["bash", "-n", str(sh_file)],
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "BASH_ENV": ""},
        )
        if proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip() or "unknown shell syntax error"
            issues.append(Issue(rel, f"shell syntax check failed: {detail}"))

    return issues


def validate_routing_evals(skill_names: set[str]) -> list[Issue]:
    """Check that tests/routing-evals.json only references real skill names."""
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
        for field in ("should_trigger", "should_not_trigger"):
            val = entry.get(field, [])
            names = [val] if isinstance(val, str) else val
            for name in names:
                if name and name not in skill_names:
                    issues.append(Issue(rel, f"{eid} {field} references unknown skill `{name}`"))
    return issues


def main() -> int:
    if not SKILLS_ROOT.exists():
        print(f"skills directory not found: {SKILLS_ROOT}", file=sys.stderr)
        return 2

    skill_dirs = sorted(path for path in SKILLS_ROOT.iterdir() if path.is_dir())
    all_issues: list[Issue] = []
    skill_names = {path.name for path in skill_dirs}
    for skill_dir in skill_dirs:
        all_issues.extend(validate_skill(skill_dir))
        all_issues.extend(validate_templates(skill_dir))
        all_issues.extend(validate_template_manifest(skill_dir))
    all_issues.extend(validate_doc_skill_tables(skill_names))
    all_issues.extend(validate_script_syntax())
    all_issues.extend(validate_routing_evals(skill_names))

    if all_issues:
        for issue in all_issues:
            print(f"ERROR {issue.path}: {issue.message}")
        print(f"\nValidation failed: {len(all_issues)} issue(s) across {len(skill_dirs)} skill(s).")
        return 1

    print(f"Validated {len(skill_dirs)} skill(s); no issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
