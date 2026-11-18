#!/usr/bin/env python3
"""Structurally validate every skills/<name>/evals/evals.json.

Evals are checked in but never run in CI (repo policy: no LLM keys in CI) —
this gate only proves the suites are well-formed so they can be run locally
or by skill-creator. Schema follows the skill-creator / tailwind convention.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from skills_common import iter_skill_dirs, repo_root

ERROR, INFO = "ERROR", "INFO"


def check_eval_file(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    eval_file = skill_dir / "evals" / "evals.json"
    try:
        data = json.loads(eval_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{eval_file}: invalid JSON: {exc}"]
    except OSError as exc:
        return [f"{eval_file}: cannot read: {exc}"]

    if not isinstance(data, dict):
        return [f"{eval_file}: top level must be a JSON object"]
    if data.get("skill_name") != skill_dir.name:
        errors.append(
            f"{eval_file}: skill_name {data.get('skill_name')!r} must match directory {skill_dir.name!r}"
        )
    evals = data.get("evals")
    if not isinstance(evals, list) or not evals:
        errors.append(f"{eval_file}: 'evals' must be a non-empty list")
        return errors

    seen_ids: set[str] = set()
    for i, case in enumerate(evals):
        ref = f"{eval_file}: evals[{i}]"
        if not isinstance(case, dict):
            errors.append(f"{ref}: must be an object")
            continue
        case_id = case.get("id")
        if isinstance(case_id, bool) or not isinstance(case_id, (str, int)) or (
            isinstance(case_id, str) and not case_id.strip()
        ):
            errors.append(
                f"{ref}: 'id' is required and must be a non-empty string or number "
                "(skillsaw agentskill-evals expects numbers)"
            )
        elif str(case_id) in seen_ids:
            errors.append(f"{ref}: duplicate id {case_id!r}")
        else:
            seen_ids.add(str(case_id))
        prompt = case.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(f"{ref} ({case_id!r}): 'prompt' is required and must be non-empty")
        assertions = case.get("assertions")
        if not isinstance(assertions, list) or not assertions:
            errors.append(f"{ref} ({case_id!r}): 'assertions' must be a non-empty list of strings")
        else:
            for j, a in enumerate(assertions):
                if not isinstance(a, str) or not a.strip():
                    errors.append(f"{ref} ({case_id!r}): assertions[{j}] must be a non-empty string")
        if "expected_output" in case and not isinstance(case["expected_output"], str):
            errors.append(f"{ref} ({case_id!r}): 'expected_output' must be a string")
        files = case.get("files")
        if files is not None:
            if not isinstance(files, list):
                errors.append(f"{ref} ({case_id!r}): 'files' must be a list of paths relative to the skill dir")
            else:
                for f in files:
                    if not isinstance(f, str) or not f.strip():
                        errors.append(f"{ref} ({case_id!r}): file entries must be non-empty strings")
                    elif not (skill_dir / f).exists():
                        errors.append(f"{ref} ({case_id!r}): fixture file {f!r} does not exist")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true", help="(reserved) fail on any finding")
    args = ap.parse_args()

    root = repo_root()
    all_errors: list[str] = []
    found = 0
    for skill_dir in iter_skill_dirs():
        if (skill_dir / "evals" / "evals.json").is_file():
            found += 1
            all_errors.extend(check_eval_file(skill_dir))

    if not found:
        print(f"INFO: no eval suites under {root / 'skills'} (optional per skill) — nothing to check")
        return 0
    for e in all_errors:
        print(f"{ERROR}: {e}")
    print(f"\n{found} eval suite(s) checked: {len(all_errors)} error(s)")
    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())
