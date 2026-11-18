"""Tests for scripts/check_evals.py."""

from __future__ import annotations

import json
from pathlib import Path

import check_evals as ce

VALID = {
    "skill_name": "sample-skill",
    "evals": [
        {
            "id": "basic",
            "prompt": "Create a thing.",
            "assertions": ['The output contains the text "SKILL.md".'],
        },
        {
            "id": "with-fixtures",
            "prompt": "Transform the input file.",
            "assertions": ["The output does not contain the text 'TODO'."],
            "files": ["fixtures/input.txt"],
        },
    ],
}


def make_skill(tmp_path: Path, evals: dict | str, name: str = "sample-skill") -> Path:
    d = tmp_path / "skills" / name
    (d / "evals").mkdir(parents=True, exist_ok=True)
    f = d / "evals" / "evals.json"
    f.write_text(evals if isinstance(evals, str) else json.dumps(evals, indent=2), encoding="utf-8")
    return d


def test_valid_suite(tmp_path: Path):
    d = make_skill(tmp_path, VALID)
    (d / "fixtures").mkdir()
    (d / "fixtures" / "input.txt").write_text("hello", encoding="utf-8")
    errors = ce.check_eval_file(d)
    assert errors == []


def test_skill_name_must_match_dir(tmp_path: Path):
    make_skill(tmp_path, {**VALID, "skill_name": "other-skill"})
    errors = ce.check_eval_file(tmp_path / "skills" / "sample-skill")
    assert any("skill_name" in e for e in errors)


def test_duplicate_ids(tmp_path: Path):
    dup = {"skill_name": "sample-skill", "evals": [VALID["evals"][0], VALID["evals"][0]]}
    make_skill(tmp_path, dup)
    errors = ce.check_eval_file(tmp_path / "skills" / "sample-skill")
    assert any("duplicate id" in e for e in errors)


def test_missing_assertions(tmp_path: Path):
    bad = {"skill_name": "sample-skill", "evals": [{"id": "x", "prompt": "p"}]}
    make_skill(tmp_path, bad)
    errors = ce.check_eval_file(tmp_path / "skills" / "sample-skill")
    assert any("'assertions'" in e for e in errors)


def test_missing_fixture_file(tmp_path: Path):
    make_skill(tmp_path, VALID)  # fixtures/input.txt not created
    errors = ce.check_eval_file(tmp_path / "skills" / "sample-skill")
    assert any("fixture file" in e for e in errors)


def test_invalid_json(tmp_path: Path):
    make_skill(tmp_path, "{not json")
    errors = ce.check_eval_file(tmp_path / "skills" / "sample-skill")
    assert any("invalid JSON" in e for e in errors)


def test_empty_evals_list(tmp_path: Path):
    make_skill(tmp_path, {"skill_name": "sample-skill", "evals": []})
    errors = ce.check_eval_file(tmp_path / "skills" / "sample-skill")
    assert any("non-empty list" in e for e in errors)
