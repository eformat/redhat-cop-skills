# AGENTS.md

Conventions for AI agents (and humans) working **in this repository**.

## What this repo is

`redhat-cop/skills` — Red Hat community-of-practice agent skills. Every skill is a directory under `skills/<skill-name>/` with a `SKILL.md` following the [Agent Skills spec](https://agentskills.io/specification). Skills must be harness-neutral (Claude Code, Codex, Cursor, OpenCode, Pi, Hermes, OpenClaw, OpenHands, DeepSeek).

## Layout

```
skills/<skill-name>/     # the skills (SKILL.md + references/, scripts/, assets/, examples/, evals/)
template/skill-name/     # starter skeleton — copy this, do not edit in place as a skill
scripts/                 # validate_skills.py, generate_index.py, check_evals.py (+ skills_common.py)
tests/                   # pytest suite for the tooling
docs/                    # documentation site source (build_site.py, theme/, pages/)
.github/                 # workflows, PR/issue templates
```

## Commands

```bash
make setup      # dev deps (pyyaml, pytest, ruff)
make lint       # everything CI runs: validate + index check + eval check + pytest
make validate   # skill validator only
make index      # regenerate README skill table + site-data/skills.json
make site       # build the docs site into _site/
make test       # tooling tests
```

## Rules

1. **Frontmatter is the contract.** `name` (kebab-case, == dir name), `description` (what + when, ≤500 chars, no angle brackets), `license: Apache-2.0`, `metadata` with `version` (semver, quoted), `maturity` (`experimental|stable|deprecated`), `owner` (GitHub handle). Unknown frontmatter keys are rejected — extras go in `metadata`.
2. **Body conventions.** Starts with `# <Title>`; has a `## When to use` section; imperative, harness-neutral instructions (no `/slash-command` phrasing, no `context: fork`, no hooks); no hardcoded `/home/<user>/` paths (use `~/`); SKILL.md ≤500 lines, overflow into `references/`.
3. **Generated files.** The README table between `<!-- GENERATED:INDEX:START/END -->` is machine-written. After adding/renaming/removing a skill run `make index` and commit. Never hand-edit inside the markers.
4. **Ownership.** Adding a skill requires adding its CODEOWNERS line (`skills/<name>/ @<owner> @eformat @sabre1041 @hultzj`) — the validator enforces the pair.
5. **Secrets never.** No credentials, tokens, internal hostnames, or customer data in skills — CI runs gitleaks; you should too before proposing.
6. **One skill per PR.** Branches `skill/…`, `fix/…`, `docs/…`.
7. **Version bumps are part of behavior changes.** Patch for fixes, minor for added capability, major for breaking workflow changes — in the same PR as the change.
8. **Evals are checked in, never run in CI.** Add `evals/evals.json` when the skill has verifiable outputs; validate structure with `scripts/check_evals.py`.

Before finishing any change: `make lint` clean, then stop — a human reviews and merges.
