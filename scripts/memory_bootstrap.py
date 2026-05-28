#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""
memory_bootstrap.py — Generate a task-specific memory context report.

Detects project scope, loads active P0/P1 facts from memory/fact-index.yaml,
loads a skill-specific memory contract if --skill is provided, and prints
a structured MUST READ / ACTIVE FACTS / DO NOT / WRITEBACK report.

Usage:
    uv run scripts/memory_bootstrap.py
    uv run scripts/memory_bootstrap.py --skill run-experiment
    uv run scripts/memory_bootstrap.py --task "submit ablation to SLURM" --skill run-experiment
    uv run scripts/memory_bootstrap.py --check-stale --seen-revision 5
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Git / scope helpers
# ---------------------------------------------------------------------------

def _git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def detect_scope(cwd: Path) -> dict:
    toplevel = _git(["rev-parse", "--show-toplevel"], cwd)
    common_dir = _git(["rev-parse", "--git-common-dir"], cwd)

    if not toplevel:
        return {"type": "unknown", "project_root": None, "in_worktree": False}

    project_root = Path(toplevel)
    # common_dir is relative when inside a worktree
    abs_common = (cwd / common_dir).resolve() if not Path(common_dir).is_absolute() else Path(common_dir)
    in_worktree = abs_common != project_root / ".git"

    return {
        "type": "worktree" if in_worktree else "root",
        "project_root": project_root,
        "working_dir": cwd,
        "in_worktree": in_worktree,
    }


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------

def find_project_root(cwd: Path) -> Path | None:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd, capture_output=True, text=True,
    )
    if result.returncode == 0:
        return Path(result.stdout.strip())
    return None


def load_fact_index(project_root: Path) -> dict:
    path = project_root / "memory" / "fact-index.yaml"
    if not path.exists():
        return {"facts": []}
    with open(path) as f:
        return yaml.safe_load(f) or {"facts": []}


def load_memory_revision(project_root: Path) -> dict | None:
    path = project_root / "memory" / "memory-revision.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def load_memory_contract(project_root: Path, skill: str) -> dict | None:
    contracts_dir = project_root / "taxonomy" / "memory-contracts"
    if not contracts_dir.exists():
        return None

    # Map skill name to contract file
    skill_to_contract = {
        "run-experiment": "experiment-run.yaml",
        "experiment-execution-router": "experiment-run.yaml",
        "run-status-monitor": "experiment-monitor.yaml",
        "result-diagnosis": "result-interpretation.yaml",
        "research-results-auditor": "result-interpretation.yaml",
        "experiment-evidence-router": "experiment-run.yaml",
    }

    contract_file = skill_to_contract.get(skill)
    if not contract_file:
        # Try matching by skill name prefix
        for f in contracts_dir.glob("*.yaml"):
            if f.stem in skill or skill in f.stem:
                contract_file = f.name
                break

    if not contract_file:
        return None

    path = contracts_dir / contract_file
    if not path.exists():
        return None
    with open(path) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _section(title: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))


def _items(items: list[str]) -> None:
    for item in items:
        print(f"  {item}")


def _check_file_exists(project_root: Path, rel_path: str) -> str:
    path = project_root / rel_path
    exists = "✓" if path.exists() else "✗ (missing)"
    return f"{rel_path} [{exists}]"


# ---------------------------------------------------------------------------
# Main report
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> int:
    cwd = Path.cwd()
    project_root = find_project_root(cwd)

    if project_root is None:
        print("ERROR: not inside a git repository.", file=sys.stderr)
        return 1

    scope = detect_scope(cwd)
    fact_data = load_fact_index(project_root)
    revision_data = load_memory_revision(project_root)
    contract = load_memory_contract(project_root, args.skill) if args.skill else None

    # --check-stale mode
    if args.check_stale:
        if revision_data is None:
            print("WARNING: memory-revision.json not found. Cannot check staleness.")
            return 0
        current = revision_data["revision"]
        if args.seen_revision < current:
            print(
                f"ERROR: memory revision changed from {args.seen_revision} to {current}.\n"
                f"Reread BRIEFING.md and project-conventions.md before acting."
            )
            return 1
        print(f"OK: memory revision {current} matches seen revision {args.seen_revision}.")
        return 0

    # --- SCOPE ---
    _section("SCOPE")
    print(f"  Project root:  {project_root}")
    print(f"  Working dir:   {scope['working_dir']}")
    print(f"  Worktree:      {'yes — write in-progress results to .agent/ not memory/' if scope['in_worktree'] else 'no (root checkout)'}")
    if args.skill:
        print(f"  Skill:         {args.skill}")
    if args.task:
        print(f"  Task:          {args.task}")

    # --- MEMORY REVISION ---
    if revision_data:
        _section("MEMORY REVISION")
        rev = revision_data["revision"]
        updated = revision_data.get("updated_at", "unknown")
        changelog = revision_data.get("changelog", "")
        print(f"  Revision:      {rev}  (updated {updated})")
        if changelog:
            print(f"  Last change:   {changelog}")
        print(f"  If your last seen revision is lower, reread BRIEFING.md and project-conventions.md before acting.")

    # --- MUST READ ---
    _section("MUST READ")
    must_read: list[str] = []

    # Always from kernel contract
    base_reads = ["memory/BRIEFING.md", "memory/project-conventions.md"]
    if (project_root / "memory" / "hot-results.md").exists():
        base_reads.append("memory/hot-results.md")
    if scope["in_worktree"] and (cwd / ".agent" / "worktree-status.md").exists():
        base_reads.append(".agent/worktree-status.md")
    must_read.extend(base_reads)

    # From skill contract
    if contract:
        for path in contract.get("always_read", []):
            if path not in must_read:
                must_read.append(path)
        for cond in contract.get("conditional_read", []):
            when = cond.get("when", "")
            files = cond.get("files", [])
            for f in files:
                note = f"{f} (if {when})"
                must_read.append(note)

    _items([_check_file_exists(project_root, p.split(" ")[0]) if not p.startswith(".agent") else p
            for p in must_read])

    # --- ACTIVE FACTS ---
    facts = fact_data.get("facts", [])
    required_ids: set[str] = set()
    if contract:
        required_ids.update(contract.get("required_facts", []))

    p0_facts = [f for f in facts if f.get("priority") == "P0" and f.get("status") == "active"]
    p1_facts = [f for f in facts if f.get("priority") == "P1" and f.get("status") == "active"
                and f["id"] in required_ids]

    if p0_facts or p1_facts:
        _section("ACTIVE FACTS")
        for fact in p0_facts:
            text = fact["text"].replace("\n", " ").strip()
            print(f"  [{fact['id']} P0] {text}")
        for fact in p1_facts:
            text = fact["text"].replace("\n", " ").strip()
            print(f"  [{fact['id']} P1] {text}")

    # --- NEEDS VERIFY ---
    _section("NEEDS VERIFY")
    verify_items = [
        "git state (git status --short --branch)",
        "installed skill copy freshness (npx skills list or check ~/.claude/skills/)",
    ]
    if contract:
        for v in contract.get("verify_before_acting", {}).items() if isinstance(contract.get("verify_before_acting"), dict) else []:
            verify_items.append(f"{v[0]}: {v[1]}")
    _items(verify_items)

    # --- DO NOT ---
    _section("DO NOT")
    do_not = [
        "Write provisional worktree-only results into root memory/.",
        "Skip validate_skills.py before commits that touch skills or inventories.",
        "Use raw 'git push'; use project-push instead.",
    ]
    if contract:
        do_not.extend(contract.get("forbidden", []))
    _items(do_not)

    # --- WRITEBACK ---
    _section("WRITEBACK")
    writeback_items = [
        "In-progress state: .agent/worktree-status.md (if in worktree)",
        "New convention: memory/project-conventions.md + memory/fact-index.yaml + bump memory-revision.json",
        "Skill change: validate → update README/AGENTS/CLAUDE → reinstall",
    ]
    if contract:
        wb = contract.get("writeback", {})
        for category, paths in wb.items():
            if isinstance(paths, list):
                for p in paths:
                    writeback_items.append(f"{category}: {p}")
    _items(writeback_items)

    print()
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a task-specific memory context report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--task", default="", help="Short description of the current task")
    parser.add_argument("--skill", default="", help="Skill being used (loads matching memory contract)")
    parser.add_argument("--scope", default="auto", choices=["auto", "root", "worktree"],
                        help="Override scope detection")
    parser.add_argument("--check-stale", action="store_true",
                        help="Check if memory revision has changed since --seen-revision")
    parser.add_argument("--seen-revision", type=int, default=0,
                        help="Last memory revision the agent has seen (for --check-stale)")
    args = parser.parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
