"""Tests for scripts/generate_index.py."""

from __future__ import annotations

import json
from pathlib import Path

import generate_index as gi
import skills_common

SKILL_MD = """\
---
name: {name}
description: {desc}
license: Apache-2.0
metadata:
  version: "1.2.3"
  maturity: stable
  owner: someuser
  domain: openshift
---

# {name}

## When to use

Always.
"""


def make_repo(tmp_path: Path, skills: list[tuple[str, str]]) -> None:
    (tmp_path / "skills").mkdir(exist_ok=True)
    for name, desc in skills:
        d = tmp_path / "skills" / name
        d.mkdir(exist_ok=True)
        (d / "SKILL.md").write_text(SKILL_MD.format(name=name, desc=desc), encoding="utf-8")
    (tmp_path / "README.md").write_text(
        "# skills\n\n## Skills\n\n" + gi.START + "\nold content\n" + gi.END + "\n\n## More\n",
        encoding="utf-8",
    )


def patch_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(gi, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(skills_common, "repo_root", lambda: tmp_path)


def test_replaces_only_between_markers(tmp_path: Path, monkeypatch):
    patch_root(tmp_path, monkeypatch)
    make_repo(tmp_path, [("my-skill", "Does things. Use when doing things.")])
    skills = gi.collect_skills()
    status, _ = gi.update_readme(skills)
    assert status == "updated"
    text = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "[my-skill](skills/my-skill/)" in text
    assert "Does things. Use when doing things." in text
    assert "old content" not in text
    assert "# skills" in text and "## More" in text  # outside the markers: untouched


def test_check_passes_when_fresh(tmp_path: Path, monkeypatch):
    patch_root(tmp_path, monkeypatch)
    make_repo(tmp_path, [("my-skill", "Desc.")])
    gi.update_readme(gi.collect_skills())
    monkeypatch.setattr("sys.argv", ["generate_index.py", "--check"])
    assert gi.main() == 0


def test_check_fails_when_stale(tmp_path: Path, monkeypatch):
    patch_root(tmp_path, monkeypatch)
    make_repo(tmp_path, [("my-skill", "Desc.")])  # README still holds 'old content'
    monkeypatch.setattr("sys.argv", ["generate_index.py", "--check"])
    assert gi.main() == 1


def test_empty_repo_renders_placeholder(tmp_path: Path, monkeypatch):
    patch_root(tmp_path, monkeypatch)
    make_repo(tmp_path, [])
    table = gi.render_table([])
    assert "No skills yet" in table
    assert gi.START in table and gi.END in table


def test_description_truncated_at_240(tmp_path: Path, monkeypatch):
    patch_root(tmp_path, monkeypatch)
    make_repo(tmp_path, [("my-skill", "x" * 400)])
    table = gi.render_table(gi.collect_skills())
    assert "…" in table
    assert "x" * 241 not in table


def test_pipes_escaped_in_description(tmp_path: Path, monkeypatch):
    patch_root(tmp_path, monkeypatch)
    make_repo(tmp_path, [("my-skill", "a | b")])
    table = gi.render_table(gi.collect_skills())
    assert "a \\| b" in table


def test_skills_json_written(tmp_path: Path, monkeypatch):
    patch_root(tmp_path, monkeypatch)
    make_repo(tmp_path, [("my-skill", "Desc.")])
    monkeypatch.setattr("sys.argv", ["generate_index.py"])
    assert gi.main() == 0
    data = json.loads((tmp_path / "site-data" / "skills.json").read_text(encoding="utf-8"))
    assert data == [
        {
            "name": "my-skill",
            "description": "Desc.",
            "version": "1.2.3",
            "maturity": "stable",
            "owner": "someuser",
            "domain": "openshift",
            "path": "skills/my-skill",
        }
    ]
