#!/usr/bin/env python3
"""Validate every skill in skills/ against the Agent Skills spec + house rules.

Spec rules: https://agentskills.io/specification (name, description, allowed
frontmatter keys). House rules add Red Hat metadata, body conventions,
harness portability, and ownership sync. Exit 1 on any ERROR; warnings pass
unless --strict.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from skills_common import SkillError, iter_skill_dirs, load_all_skills, repo_root

ERROR, WARN, INFO = "ERROR", "WARN", "INFO"

SPEC_KEYS = {"name", "description", "license", "compatibility", "allowed-tools", "metadata"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
GH_HANDLE_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
HOME_PATH_RE = re.compile(r"/home/[A-Za-z0-9._-]+/")
H1_RE = re.compile(r"^#\s+\S")
WHEN_RE = re.compile(r"^##\s+when to use\b", re.IGNORECASE | re.MULTILINE)
INVISIBLE_RE = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2066-\u2069\u00a0\u00ad\ufeff]")
NESTED_SKILL_RE = re.compile(r"skills/[^/]+/[^/]+/SKILL\.md$")

MATURITIES = {"experimental", "stable", "deprecated"}
MAX_NAME_LEN = 64  # Agent Skills spec
DESC_SPEC_MAX = 1024  # Agent Skills spec
DESC_DSH_MAX = 500  # DeepSeek dsh renders the catalog from description, bounded at 500
DESC_HOUSE_TARGET = 200  # beyond this: warn (trigger quality review)
BODY_LINES_WARN = 500  # Agent Skills spec recommendation

REQUIRED_METADATA = ("version", "maturity", "owner")
OPTIONAL_METADATA = ("domain", "replaced-by", "archived-since")


def add(findings: list, severity: str, location: str, message: str) -> None:
    findings.append((severity, location, message))


def check_metadata(meta: dict, loc: str, findings: list) -> None:
    md = meta.get("metadata")
    if md is None:
        add(findings, ERROR, loc, "missing 'metadata' block (requires version, maturity, owner)")
        return
    if not isinstance(md, dict):
        add(findings, ERROR, loc, "'metadata' must be a YAML mapping")
        return
    for key, value in md.items():
        if not isinstance(value, str):
            add(
                findings, ERROR, loc,
                f"metadata.{key} must be a string (Agent Skills spec: metadata is a map of "
                f"strings) — got {type(value).__name__}; quote it, e.g. version: \"{value}\"",
            )
    for key in REQUIRED_METADATA:
        if key not in md or not str(md.get(key, "")).strip():
            add(findings, ERROR, loc, f"metadata.{key} is required")
    version = md.get("version")
    if isinstance(version, str) and version.strip() and not SEMVER_RE.match(version.strip()):
        add(findings, ERROR, loc, f"metadata.version must be semver (X.Y.Z), got {version!r}")
    maturity = md.get("maturity")
    if isinstance(maturity, str) and maturity.strip() and maturity not in MATURITIES:
        add(
            findings, ERROR, loc,
            f"metadata.maturity must be one of {sorted(MATURITIES)}, got {maturity!r}",
        )
    owner = md.get("owner")
    if isinstance(owner, str) and owner.strip():
        for handle in owner.split(","):
            handle = handle.strip().lstrip("@")
            if handle and not GH_HANDLE_RE.match(handle):
                add(findings, ERROR, loc, f"metadata.owner has invalid GitHub handle {handle!r}")
    if maturity == "deprecated" and not str(md.get("replaced-by", "")).strip():
        add(
            findings, WARN, loc,
            "maturity is 'deprecated' but metadata.replaced-by is unset — point at the "
            "successor skill or explain the removal plan",
        )


def check_skill(skill: dict, findings: list, seen: dict[str, str]) -> None:
    if "error" in skill:
        add(findings, ERROR, str(skill["dir"]), skill["error"])
        return
    d: Path = skill["dir"]
    loc = str(skill["path"])
    meta = skill["meta"]

    # --- frontmatter keys (spec-pure) ---
    unknown = set(meta) - SPEC_KEYS
    if unknown:
        add(
            findings, ERROR, loc,
            f"unknown frontmatter key(s): {', '.join(sorted(unknown))} — allowed: "
            f"{', '.join(sorted(SPEC_KEYS))}; put extras in the metadata block",
        )

    # --- name ---
    name = meta.get("name")
    if name is None or not str(name).strip():
        add(findings, ERROR, loc, "frontmatter 'name' is required")
        name = None
    elif not isinstance(name, str) or not NAME_RE.match(name):
        add(
            findings, ERROR, loc,
            f"name {name!r} must be kebab-case (lowercase letters, digits, single hyphens), "
            "max 64 chars, no leading/trailing hyphens",
        )
    elif len(name) > MAX_NAME_LEN:
        add(findings, ERROR, loc, f"name is {len(name)} chars; max is {MAX_NAME_LEN}")
    elif name != d.name:
        add(findings, ERROR, loc, f"name {name!r} must match the directory name {d.name!r}")
    if isinstance(name, str) and name in seen:
        add(findings, ERROR, loc, f"duplicate skill name {name!r} (already used by {seen[name]})")
    elif isinstance(name, str):
        seen[name] = loc

    # --- description ---
    desc = meta.get("description")
    if desc is None or not isinstance(desc, str) or not desc.strip():
        add(findings, ERROR, loc, "frontmatter 'description' is required and must be non-empty")
    else:
        if "<" in desc or ">" in desc:
            add(findings, ERROR, loc, "description must not contain angle brackets")
        n = len(desc)
        if n > DESC_SPEC_MAX:
            add(findings, ERROR, loc, f"description is {n} chars; Agent Skills spec max is {DESC_SPEC_MAX}")
        elif n > DESC_DSH_MAX:
            add(
                findings, ERROR, loc,
                f"description is {n} chars; hard cap is {DESC_DSH_MAX} (DeepSeek dsh renders only "
                "name+description into the model catalog, bounded at 500, and silently truncates)",
            )
        elif n > DESC_HOUSE_TARGET:
            add(
                findings, WARN, loc,
                f"description is {n} chars; house target is <= {DESC_HOUSE_TARGET} — keep it "
                "trigger-rich but tight",
            )
        if "when" not in desc.lower():
            add(
                findings, WARN, loc,
                "description should say when to use the skill (trigger phrases) — it is the "
                "primary triggering mechanism in every harness",
            )

    # --- allowed-tools (optional, advisory across harnesses) ---
    tools = meta.get("allowed-tools")
    if tools is not None:
        if not isinstance(tools, str) or not tools.strip():
            add(
                findings, ERROR, loc,
                "allowed-tools must be a space-separated string (e.g. 'Read Grep Bash'), not a list",
            )

    # --- compatibility / license ---
    compat = meta.get("compatibility")
    if compat is not None:
        if not isinstance(compat, str):
            add(findings, ERROR, loc, "compatibility must be a string")
        elif len(compat) > 500:
            add(findings, ERROR, loc, "compatibility max is 500 chars (spec)")
    lic = meta.get("license")
    if lic is None:
        add(findings, WARN, loc, "no 'license' declared — add 'license: Apache-2.0' (repo default)")
    elif not isinstance(lic, str):
        add(findings, ERROR, loc, "license must be a string")
    elif lic.strip() != "Apache-2.0":
        add(
            findings, WARN, loc,
            f"license is {lic.strip()!r}; repo convention is 'license: Apache-2.0' (root LICENSE "
            "covers every skill)",
        )

    # --- metadata block ---
    check_metadata(meta, loc, findings)

    # --- body conventions ---
    body = skill["body"]
    stripped = body.strip()
    if not stripped:
        add(findings, ERROR, loc, "SKILL.md body is empty")
    else:
        if not H1_RE.match(stripped.splitlines()[0]):
            add(findings, ERROR, loc, "body must start with a '# <Title>' H1 heading")
        if not WHEN_RE.search(body):
            add(findings, ERROR, loc, "body must contain a '## When to use' section")
        for m in HOME_PATH_RE.finditer(body):
            add(
                findings, ERROR, loc,
                f"hardcoded user path {m.group()!r} — use '~/…' instead (docs must be portable)",
            )
    lines = skill["text"].count("\n") + 1
    if lines > BODY_LINES_WARN:
        add(
            findings, WARN, loc,
            f"SKILL.md is {lines} lines (recommended max {BODY_LINES_WARN}); move detail "
            "into references/",
        )

    # --- hidden unicode (prompt-safety, mirrors autofix-skills' unicode-safety CI) ---
    for i, line in enumerate(skill["text"].splitlines(), start=1):
        m = INVISIBLE_RE.search(line)
        if m:
            add(
                findings, ERROR, loc,
                f"line {i}: hidden unicode character U+{ord(m.group()):04X} "
                "(zero-width/bidi/nbsp class) — remove it; these are invisible to review and "
                "unsafe in prompts",
            )


def check_codeowners_sync(root: Path, findings: list) -> None:
    """Every skill needs its per-skill CODEOWNERS rule (owner + maintainers)."""
    codeowners = root / "CODEOWNERS"
    co_text = codeowners.read_text(encoding="utf-8") if codeowners.is_file() else ""
    if not co_text.strip():
        add(findings, ERROR, str(codeowners), "CODEOWNERS is missing or empty")
        return
    for skill in load_all_skills(root / "skills"):
        if "error" in skill:
            continue
        name = skill["meta"].get("name")
        if isinstance(name, str) and f"skills/{name}/" not in co_text:
            add(
                findings, ERROR, str(codeowners),
                f"no CODEOWNERS rule for skills/{name}/ — add a line "
                f"'skills/{name}/ @<owner> @eformat @sabre1041 @hultzj'",
            )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--strict", action="store_true", help="fail on warnings too")
    args = ap.parse_args()

    root = repo_root()
    findings: list[tuple[str, str, str]] = []
    skill_dirs = iter_skill_dirs()

    if not skill_dirs:
        print(f"INFO: no skills under {root / 'skills'} yet — nothing to validate")
        return 0

    # one-level layout rule: skills/<name>/SKILL.md, nothing deeper
    for nested in sorted(root.glob("skills/*/*/SKILL.md")):
        add(
            findings, ERROR, str(nested),
            "nested skill detected — skills must live exactly one level under skills/ "
            "(Pi, Oh My Pi and DeepSeek dsh discovery only scan one level; deeper skills are "
            "silently invisible to them)",
        )

    seen: dict[str, str] = {}
    for skill in load_all_skills():
        check_skill(skill, findings, seen)

    # ownership sync: every skill needs its CODEOWNERS rule (owner + maintainers)
    check_codeowners_sync(root, findings)

    order = {ERROR: 0, WARN: 1, INFO: 2}
    findings.sort(key=lambda f: (order[f[0]], f[1], f[2]))
    for severity, location, message in findings:
        print(f"{severity}: {location}: {message}")

    errors = sum(1 for s, _, _ in findings if s == ERROR)
    warns = sum(1 for s, _, _ in findings if s == WARN)
    print(f"\n{len(skill_dirs)} skill(s) checked: {errors} error(s), {warns} warning(s)")
    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
