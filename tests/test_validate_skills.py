"""Tests for scripts/validate_skills.py."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import validate_skills as vs


VALID_FRONTMATTER = """\
---
name: sample-skill
description: Does a useful thing. Use when the user asks for that thing.
license: Apache-2.0
metadata:
  version: "0.1.0"
  maturity: experimental
  owner: someuser
---

# Sample Skill

Body text.
"""

VALID_BODY_EXTRA = """
## When to use

Whenever the thing is needed.
"""


def write_skill(root: Path, name: str, frontmatter: str = VALID_FRONTMATTER, body_extra: str = "") -> Path:
    d = root / "skills" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(frontmatter + body_extra, encoding="utf-8")
    return d


def run(root: Path, strict: bool = False) -> tuple[int, list[tuple[str, str, str]]]:
    findings: list = []
    seen: dict[str, str] = {}
    for skill in vs.load_all_skills(root / "skills"):
        vs.check_skill(skill, findings, seen)
    errors = sum(1 for s, _, _ in findings if s == vs.ERROR)
    warns = sum(1 for s, _, _ in findings if s == vs.WARN)
    rc = 1 if errors or (strict and warns) else 0
    return rc, findings


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    return tmp_path


def test_valid_skill_passes(tree: Path):
    write_skill(tree, "sample-skill", VALID_FRONTMATTER + VALID_BODY_EXTRA)
    rc, findings = run(tree)
    assert rc == 0, findings
    assert not [f for f in findings if f[0] == vs.ERROR]


def test_name_must_match_directory(tree: Path):
    write_skill(tree, "other-dir")
    rc, findings = run(tree)
    assert rc == 1
    assert any("must match the directory name" in m for _, _, m in findings)


def test_name_rejects_uppercase_and_double_hyphen(tree: Path):
    for bad in ("Bad-Name", "double--hyphen", "-leading", "trailing-"):
        d = tree / "skills" / bad
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            VALID_FRONTMATTER.replace("name: sample-skill", f"name: {bad}") + VALID_BODY_EXTRA,
            encoding="utf-8",
        )
    rc, findings = run(tree)
    assert rc == 1
    assert sum(1 for _, _, m in findings if "kebab-case" in m) == len(
        [b for b in ("Bad-Name", "double--hyphen", "-leading", "trailing-")]
    )


def test_unknown_frontmatter_key_rejected(tree: Path):
    write_skill(
        tree, "sample-skill",
        VALID_FRONTMATTER.replace("license: Apache-2.0", "license: Apache-2.0\ncolor: blue\n")
        + VALID_BODY_EXTRA,
    )
    rc, findings = run(tree)
    assert rc == 1
    assert any("unknown frontmatter key" in m for _, _, m in findings)


def test_description_caps(tree: Path):
    long_desc = "x" * 600
    write_skill(
        tree, "sample-skill",
        VALID_FRONTMATTER.replace(
            "description: Does a useful thing. Use when the user asks for that thing.",
            f"description: {long_desc}",
        )
        + VALID_BODY_EXTRA,
    )
    rc, findings = run(tree)
    assert rc == 1
    assert any(f"hard cap is {vs.DESC_DSH_MAX}" in m for _, _, m in findings)


def test_description_warns_over_house_target(tree: Path):
    desc = "word " * 45  # 225 chars -> > 200, < 500
    write_skill(
        tree, "sample-skill",
        VALID_FRONTMATTER.replace(
            "description: Does a useful thing. Use when the user asks for that thing.",
            f"description: {desc.strip()}",
        )
        + VALID_BODY_EXTRA,
    )
    rc, findings = run(tree)
    assert rc == 0
    assert any("house target" in m for s, _, m in findings if s == vs.WARN)


def test_angle_brackets_in_description_rejected(tree: Path):
    write_skill(
        tree, "sample-skill",
        VALID_FRONTMATTER.replace(
            "Use when the user asks for that thing.",
            "Use when the user asks for <that> thing.",
        )
        + VALID_BODY_EXTRA,
    )
    rc, findings = run(tree)
    assert rc == 1
    assert any("angle brackets" in m for _, _, m in findings)


def test_metadata_missing_fields(tree: Path):
    write_skill(
        tree, "sample-skill",
        VALID_FRONTMATTER.replace('  version: "0.1.0"\n', "").replace("  owner: someuser\n", "")
        + VALID_BODY_EXTRA,
    )
    rc, findings = run(tree)
    assert rc == 1
    assert any("metadata.version is required" in m for _, _, m in findings)
    assert any("metadata.owner is required" in m for _, _, m in findings)


def test_metadata_value_must_be_string(tree: Path):
    # YAML parses unquoted 1.0 as a float — metadata values must be strings (spec)
    write_skill(
        tree, "sample-skill",
        VALID_FRONTMATTER.replace('  version: "0.1.0"', "  version: 1.0") + VALID_BODY_EXTRA,
    )
    rc, findings = run(tree)
    assert rc == 1
    assert any("must be a string" in m and "version" in m for _, _, m in findings)


def test_bad_maturity(tree: Path):
    write_skill(
        tree, "sample-skill",
        VALID_FRONTMATTER.replace("maturity: experimental", "maturity: awesome") + VALID_BODY_EXTRA,
    )
    rc, findings = run(tree)
    assert rc == 1
    assert any("metadata.maturity must be one of" in m for _, _, m in findings)


def test_deprecated_without_replacement_warns(tree: Path):
    write_skill(
        tree, "sample-skill",
        VALID_FRONTMATTER.replace("maturity: experimental", "maturity: deprecated") + VALID_BODY_EXTRA,
    )
    rc, findings = run(tree)
    assert rc == 0
    assert any("metadata.replaced-by is unset" in m for _, _, m in findings)


def test_allowed_tools_must_be_string(tree: Path):
    write_skill(
        tree, "sample-skill",
        VALID_FRONTMATTER.replace(
            "license: Apache-2.0", "license: Apache-2.0\nallowed-tools:\n  - Read\n  - Bash"
        )
        + VALID_BODY_EXTRA,
    )
    rc, findings = run(tree)
    assert rc == 1
    assert any("allowed-tools must be a space-separated string" in m for _, _, m in findings)


def test_body_requires_h1_and_when_to_use(tree: Path):
    d = write_skill(tree, "sample-skill", VALID_FRONTMATTER)
    md = d / "SKILL.md"
    md.write_text(md.read_text(encoding="utf-8").replace("# Sample Skill", "Sample Skill"), encoding="utf-8")
    rc, findings = run(tree)
    assert rc == 1
    assert any("'# <Title>' H1" in m for _, _, m in findings)
    assert any("'## When to use'" in m for _, _, m in findings)


def test_hardcoded_home_path_rejected(tree: Path):
    d = write_skill(tree, "sample-skill", VALID_FRONTMATTER + VALID_BODY_EXTRA)
    md = d / "SKILL.md"
    md.write_text(
        md.read_text(encoding="utf-8") + "\nRun: cd /home/alice/git/thing\n",
        encoding="utf-8",
    )
    rc, findings = run(tree)
    assert rc == 1
    assert any("hardcoded user path" in m for _, _, m in findings)


def test_hidden_unicode_rejected(tree: Path):
    d = write_skill(tree, "sample-skill", VALID_FRONTMATTER + VALID_BODY_EXTRA)
    md = d / "SKILL.md"
    md.write_text(
        md.read_text(encoding="utf-8").replace("Body text.", "Body\u200btext."),
        encoding="utf-8",
    )
    rc, findings = run(tree)
    assert rc == 1
    assert any("hidden unicode" in m for _, _, m in findings)


def test_duplicate_names_across_skills(tree: Path):
    write_skill(tree, "first-skill", VALID_FRONTMATTER + VALID_BODY_EXTRA)
    second = tree / "skills" / "second-skill"
    second.mkdir(parents=True)
    (second / "SKILL.md").write_text(VALID_FRONTMATTER + VALID_BODY_EXTRA, encoding="utf-8")
    rc, findings = run(tree)
    assert rc == 1
    assert any("duplicate skill name" in m for _, _, m in findings)


def test_over_500_lines_warns_not_fails(tree: Path):
    d = write_skill(tree, "sample-skill", VALID_FRONTMATTER + VALID_BODY_EXTRA)
    md = d / "SKILL.md"
    md.write_text(md.read_text(encoding="utf-8") + ("\nfiller line\n" * 520), encoding="utf-8")
    rc, findings = run(tree)
    assert rc == 0
    assert any("lines (recommended max" in m for _, _, m in findings)


def test_missing_skill_md_reported(tree: Path):
    (tree / "skills" / "empty-skill").mkdir(parents=True)
    rc, findings = run(tree)
    assert rc == 1
    assert any("missing SKILL.md" in m for _, _, m in findings)


def test_codeowners_sync_checked(tree: Path):
    write_skill(tree, "sample-skill", VALID_FRONTMATTER + VALID_BODY_EXTRA)
    findings: list = []
    vs.check_codeowners_sync(tree, findings)
    assert any("CODEOWNERS is missing or empty" in m for _, _, m in findings)
    (tree / "CODEOWNERS").write_text("* @eformat @sabre1041 @hultzj\n", encoding="utf-8")
    findings = []
    vs.check_codeowners_sync(tree, findings)
    assert any("no CODEOWNERS rule" in m for _, _, m in findings)
    (tree / "CODEOWNERS").write_text(
        "* @eformat @sabre1041 @hultzj\nskills/sample-skill/ @someuser @eformat @sabre1041 @hultzj\n",
        encoding="utf-8",
    )
    findings = []
    vs.check_codeowners_sync(tree, findings)
    assert findings == []


def test_no_skills_dir_is_clean(tree: Path):
    rc, findings = run(tree)
    assert rc == 0 and findings == []
