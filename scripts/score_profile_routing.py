#!/usr/bin/env python3
"""
Score profile-level routing predictions against tests/profile-routing-evals.json.

Prediction JSON accepts either:

{
  "predictions": [
    {"id": "PRE-001", "profile": "global-bootstrap", "entrypoint": "ml-research-bootstrap"}
  ]
}

or a mapping keyed by eval id:

{
  "PRE-001": {"profile": "global-bootstrap", "entrypoint": "ml-research-bootstrap"}
}
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVALS = REPO_ROOT / "tests" / "profile-routing-evals.json"


class InputError(ValueError):
    """Raised when an eval or prediction file has an invalid shape."""


@dataclass(frozen=True)
class EvalCase:
    id: str
    prompt: str
    expected_profile: str
    expected_entrypoint: str
    should_not_profiles: tuple[str, ...]


@dataclass(frozen=True)
class Prediction:
    id: str
    profile: str
    entrypoint: str
    notes: str = ""


@dataclass(frozen=True)
class Failure:
    id: str
    messages: tuple[str, ...]
    prompt: str


@dataclass(frozen=True)
class Score:
    total: int
    scored: int
    missing: int
    profile_ok: int
    entrypoint_ok: int
    exact_ok: int
    failures: tuple[Failure, ...]

    @property
    def passed(self) -> bool:
        return not self.failures and self.missing == 0


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise InputError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON in {path}: {exc}") from exc


def load_evals(path: Path) -> list[EvalCase]:
    data = _read_json(path)
    if not isinstance(data, dict):
        raise InputError(f"{path} must contain a JSON object")
    evals = data.get("evals")
    if not isinstance(evals, list) or not evals:
        raise InputError(f"{path} must contain a non-empty `evals` list")

    cases: list[EvalCase] = []
    seen_ids: set[str] = set()
    for idx, raw in enumerate(evals, start=1):
        if not isinstance(raw, dict):
            raise InputError(f"eval #{idx} must be an object")

        eid = raw.get("id")
        prompt = raw.get("prompt")
        expected_profile = raw.get("expected_profile")
        expected_entrypoint = raw.get("expected_entrypoint")
        should_not = raw.get("should_not_profiles", [])

        for field_name, value in (
            ("id", eid),
            ("prompt", prompt),
            ("expected_profile", expected_profile),
            ("expected_entrypoint", expected_entrypoint),
        ):
            if not isinstance(value, str) or not value.strip():
                raise InputError(f"eval #{idx} has missing or empty `{field_name}`")

        if eid in seen_ids:
            raise InputError(f"duplicate eval id `{eid}`")
        seen_ids.add(eid)

        if not isinstance(should_not, list) or not all(isinstance(item, str) for item in should_not):
            raise InputError(f"eval `{eid}` has invalid `should_not_profiles`; expected list of strings")

        cases.append(
            EvalCase(
                id=eid,
                prompt=prompt,
                expected_profile=expected_profile,
                expected_entrypoint=expected_entrypoint,
                should_not_profiles=tuple(should_not),
            )
        )
    return cases


def _prediction_field(raw: dict[str, Any], *names: str) -> str:
    for name in names:
        value = raw.get(name)
        if isinstance(value, str):
            return value.strip()
    return ""


def _prediction_from_object(eid: str, raw: Any) -> Prediction:
    if not isinstance(raw, dict):
        raise InputError(f"prediction `{eid}` must be an object")
    profile = _prediction_field(raw, "profile", "predicted_profile", "selected_profile")
    entrypoint = _prediction_field(raw, "entrypoint", "predicted_entrypoint", "selected_entrypoint")
    notes = _prediction_field(raw, "notes", "rationale", "comment")
    return Prediction(id=eid, profile=profile, entrypoint=entrypoint, notes=notes)


def load_predictions(path: Path) -> dict[str, Prediction]:
    data = _read_json(path)
    predictions: dict[str, Prediction] = {}

    if isinstance(data, dict) and isinstance(data.get("predictions"), list):
        raw_predictions = data["predictions"]
        for idx, raw in enumerate(raw_predictions, start=1):
            if not isinstance(raw, dict):
                raise InputError(f"prediction #{idx} must be an object")
            eid = _prediction_field(raw, "id", "eval_id", "case_id")
            if not eid:
                raise InputError(f"prediction #{idx} is missing `id`")
            if eid in predictions:
                raise InputError(f"duplicate prediction id `{eid}`")
            predictions[eid] = _prediction_from_object(eid, raw)
        return predictions

    if isinstance(data, list):
        for idx, raw in enumerate(data, start=1):
            if not isinstance(raw, dict):
                raise InputError(f"prediction #{idx} must be an object")
            eid = _prediction_field(raw, "id", "eval_id", "case_id")
            if not eid:
                raise InputError(f"prediction #{idx} is missing `id`")
            if eid in predictions:
                raise InputError(f"duplicate prediction id `{eid}`")
            predictions[eid] = _prediction_from_object(eid, raw)
        return predictions

    if isinstance(data, dict):
        for eid, raw in data.items():
            if eid.startswith("_"):
                continue
            if eid in predictions:
                raise InputError(f"duplicate prediction id `{eid}`")
            predictions[eid] = _prediction_from_object(eid, raw)
        return predictions

    raise InputError(f"{path} must contain a predictions object, list, or id-keyed mapping")


def score_predictions(
    cases: list[EvalCase],
    predictions: dict[str, Prediction],
    *,
    allow_missing: bool = False,
) -> Score:
    known_ids = {case.id for case in cases}
    unknown_ids = sorted(set(predictions) - known_ids)
    if unknown_ids:
        raise InputError(f"predictions contain unknown eval id(s): {', '.join(unknown_ids)}")

    profile_ok = 0
    entrypoint_ok = 0
    exact_ok = 0
    scored = 0
    missing = 0
    failures: list[Failure] = []

    for case in cases:
        pred = predictions.get(case.id)
        if pred is None:
            missing += 1
            if not allow_missing:
                failures.append(Failure(case.id, ("missing prediction",), case.prompt))
            continue

        scored += 1
        messages: list[str] = []

        if pred.profile == case.expected_profile:
            profile_ok += 1
        else:
            messages.append(f"profile expected `{case.expected_profile}`, got `{pred.profile or '<empty>'}`")

        if pred.entrypoint == case.expected_entrypoint:
            entrypoint_ok += 1
        else:
            messages.append(f"entrypoint expected `{case.expected_entrypoint}`, got `{pred.entrypoint or '<empty>'}`")

        if pred.profile in case.should_not_profiles:
            messages.append(f"profile `{pred.profile}` is listed in should_not_profiles")

        if not messages:
            exact_ok += 1
        else:
            failures.append(Failure(case.id, tuple(messages), case.prompt))

    if allow_missing and scored == 0:
        failures.append(Failure("<all>", ("no predictions were scored",), ""))

    return Score(
        total=len(cases),
        scored=scored,
        missing=missing,
        profile_ok=profile_ok,
        entrypoint_ok=entrypoint_ok,
        exact_ok=exact_ok,
        failures=tuple(failures),
    )


def write_predictions_file(path: Path, cases: list[EvalCase], *, gold: bool) -> None:
    predictions: list[dict[str, str]] = []
    for case in cases:
        predictions.append(
            {
                "id": case.id,
                "profile": case.expected_profile if gold else "",
                "entrypoint": case.expected_entrypoint if gold else "",
                "notes": "gold fixture output" if gold else "",
            }
        )

    payload = {
        "_comment": (
            "Gold profile-routing predictions generated from the eval fixture."
            if gold
            else "Fill profile and entrypoint with actual runtime/agent choices, then score this file."
        ),
        "predictions": predictions,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _fmt_count(numerator: int, denominator: int) -> str:
    pct = (100.0 * numerator / denominator) if denominator else 0.0
    return f"{numerator}/{denominator} ({pct:.1f}%)"


def print_score(score: Score, *, allow_missing: bool = False, show_prompts: bool = False) -> None:
    denominator = score.scored if allow_missing else score.total
    print("Profile routing score")
    print(f"Evals: {score.total}")
    print(f"Scored predictions: {score.scored}")
    print(f"Missing predictions: {score.missing}")
    print(f"Profile accuracy: {_fmt_count(score.profile_ok, denominator)}")
    print(f"Entrypoint accuracy: {_fmt_count(score.entrypoint_ok, denominator)}")
    print(f"Exact accuracy: {_fmt_count(score.exact_ok, denominator)}")

    if not score.failures:
        if allow_missing and score.missing:
            print("PASS (partial; missing predictions allowed)")
        else:
            print("PASS")
        return

    print("FAIL")
    for failure in score.failures:
        print(f"- {failure.id}: {'; '.join(failure.messages)}")
        if show_prompts and failure.prompt:
            print(f"  prompt: {failure.prompt}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evals", type=Path, default=DEFAULT_EVALS, help="Path to profile-routing eval JSON.")
    parser.add_argument("--predictions", type=Path, help="Path to runtime/agent profile-routing predictions.")
    parser.add_argument("--write-template", type=Path, help="Write a blank prediction template and exit unless scoring is also requested.")
    parser.add_argument("--write-gold", type=Path, help="Write gold predictions from eval answers; useful for smoke tests.")
    parser.add_argument("--allow-missing", action="store_true", help="Do not fail for eval ids missing from the prediction file.")
    parser.add_argument("--show-prompts", action="store_true", help="Print prompt text for failed cases.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    try:
        cases = load_evals(args.evals)
        wrote_file = False

        if args.write_template:
            write_predictions_file(args.write_template, cases, gold=False)
            print(f"Wrote blank prediction template: {args.write_template}")
            wrote_file = True

        if args.write_gold:
            write_predictions_file(args.write_gold, cases, gold=True)
            print(f"Wrote gold prediction file: {args.write_gold}")
            wrote_file = True

        if not args.predictions:
            if wrote_file:
                return 0
            print("ERROR: provide --predictions, --write-template, or --write-gold", file=sys.stderr)
            return 2

        predictions = load_predictions(args.predictions)
        score = score_predictions(cases, predictions, allow_missing=args.allow_missing)
        print_score(score, allow_missing=args.allow_missing, show_prompts=args.show_prompts)
        return 0 if score.passed or (args.allow_missing and not score.failures) else 1
    except InputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
