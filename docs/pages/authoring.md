## Anatomy

```
skills/<skill-name>/
├── SKILL.md          # required — frontmatter + instructions
├── references/       # optional — docs the agent reads on demand
├── scripts/          # optional — deterministic helpers
├── assets/           # optional — templates, images, data
├── examples/         # optional — input/output examples
└── evals/evals.json  # optional — checked-in test prompts
```

One level only — deeper nesting is invisible to some harnesses and rejected by CI. Copy `template/skill-name/` to start, or ask your agent to follow the repo's `AGENTS.md`.

## Frontmatter contract

```yaml
---
name: my-skill                    # kebab-case, <=64, == directory name
description: >-                   # what + when; <=500 hard cap, <=200 target
  Provisions a kind cluster with OpenShift AI. Use when the user asks to
  "set up a local cluster", "demo environment", or "sandbox RHOAI".
license: Apache-2.0
allowed-tools: Read Grep Bash     # optional; advisory (some harnesses ignore it)
metadata:
  version: "0.1.0"                # semver, quoted
  maturity: experimental          # experimental | stable | deprecated
  owner: github-handle            # who reviews changes
  domain: openshift               # optional free tag
---
```

## House rules (CI-enforced)

- Description: no angle brackets; ≤500 chars hard cap (DeepSeek renders only name+description into its catalog and truncates at 500); say **when** to trigger, with concrete phrases
- Body starts with `# <Title>`, has a `## When to use` section, stays under 500 lines (overflow into `references/`)
- No `/home/<user>/` paths (use `~/`), no hidden unicode, no secrets (gitleaks runs in CI)
- No harness-only constructs (`context: fork`, hooks) — skills behave identically everywhere
- `metadata.version` semver, `maturity` valid enum, `owner` a real GitHub handle with a matching `CODEOWNERS` rule
- Skill names unique across the repo

## Quality bar

PRs need **validation evidence**: you ran the workflow on realistic inputs, a peer confirms it, a checked-in eval, or explicit test steps. Scope `allowed-tools` to exactly what the skill calls, and state human-approval gates in the body for anything that writes to external systems.

## Evals

Checked in at `skills/<name>/evals/evals.json`, structurally validated in CI, run locally — the recommended loop is the bundled [skill-creator](https://github.com/redhat-cop/skills/tree/main/skills/skill-creator) paired-with/without-skill benchmark.

## Lifecycle

`experimental` → `stable` (promote via PR once field-proven) → `deprecated` (keep ≥1 quarter, then remove). Version bumps ship with the change: patch for fixes, minor for capability, major for breaking workflow changes.

The full contract — including the review flow and PR checklist — is [CONTRIBUTING.md](https://github.com/redhat-cop/skills/blob/main/CONTRIBUTING.md) in the repo.
