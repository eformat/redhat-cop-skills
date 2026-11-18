"""Shared helpers for the redhat-cop/skills tooling.

Used by scripts/validate_skills.py, scripts/generate_index.py and
scripts/check_evals.py. Stdlib + PyYAML only.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


class SkillError(Exception):
    """Raised for structural problems a caller should surface as a finding."""


def repo_root() -> Path:
    """Repository root (the directory containing this scripts/ dir)."""
    return Path(__file__).resolve().parent.parent


def skills_root() -> Path:
    return repo_root() / "skills"


def parse_frontmatter(text: str, path: Path) -> tuple[dict, str]:
    """Split a SKILL.md into (frontmatter dict, markdown body)."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise SkillError(
            f"{path}: SKILL.md must start with YAML frontmatter delimited by '---' lines"
        )
    try:
        meta = yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        raise SkillError(f"{path}: frontmatter is not valid YAML: {exc}") from exc
    if not isinstance(meta, dict):
        raise SkillError(f"{path}: frontmatter must be a YAML mapping")
    return meta, text[m.end():]


def iter_skill_dirs(skills_dir: Path | None = None) -> list[Path]:
    """Sorted skill directories directly under skills/ (one level, no nesting)."""
    root = skills_dir if skills_dir is not None else skills_root()
    if not root.is_dir():
        return []
    return sorted(p for p in root.iterdir() if p.is_dir())


def load_skill(skill_dir: Path) -> dict:
    """Load one skill directory. Raises SkillError on structural problems."""
    md = skill_dir / "SKILL.md"
    if not md.is_file():
        raise SkillError(f"{skill_dir}: missing SKILL.md")
    text = md.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text, md)
    return {
        "dir": skill_dir,
        "dir_name": skill_dir.name,
        "path": md,
        "meta": meta,
        "body": body,
        "text": text,
    }


def load_all_skills(skills_dir: Path | None = None) -> list[dict]:
    """Load every skill; structural failures come back as pseudo-skills with an 'error' key."""
    out = []
    for d in iter_skill_dirs(skills_dir):
        try:
            out.append(load_skill(d))
        except SkillError as exc:
            out.append({"dir": d, "dir_name": d.name, "error": str(exc)})
    return out


def one_line(text: str) -> str:
    """Collapse any whitespace (incl. YAML folded scalars) to single spaces."""
    return " ".join(str(text).split())
