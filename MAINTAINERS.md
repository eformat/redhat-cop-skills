# Maintainers

This document defines who reviews what and how changes merge.

## Maintainers

| Handle | Role |
|---|---|
| [@eformat](https://github.com/eformat) | Maintainer |
| [@hultzj](https://github.com/hultzj) | Maintainer |

## Principles

1. **No direct commits to `main`.** Everything through PRs, even for maintainers.
2. **Tag reviewers explicitly** in the PR description; CODEOWNERS auto-requests as backstop.
3. **Docs ship with code.** A skill change that alters behavior updates the skill's own docs in the same PR.
4. **Structural changes need joint review** — two maintainers, not one.

## Approval tiers

| Change | Approval required |
|---|---|
| Repo files (`scripts/`, `tests/`, `.github/`, `docs/`, `README`, `template/`) | ≥1 maintainer |
| New skill | Skill `metadata.owner` + ≥1 maintainer |
| Behavioral change to an existing skill | Skill owner + ≥1 maintainer (owner unavailable → 2 maintainers) |
| Structural (new top-level dirs, governance files, validator rules, taxonomy) | 2 maintainers, at least one different from the author |

## Path ownership matrix

| Path | Reviewers |
|---|---|

Keep CODEOWNERS in sync with this matrix when skills are added — CI enforces per-skill rules; the root rules are hand-maintained here.

## Responsibilities

- Review PRs for the paths above; aim to triage unassigned PRs within **2 business days**
- Keep the quality bar honest: validation evidence is required for skill changes, not optional
- Own lifecycle: promote `experimental` → `stable` when field-proven, drive deprecations
- Grow the maintainer group deliberately: nominate contributors with a track record of merged, field-proven skills
