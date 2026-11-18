## Which agents do these skills work with?

All skills-following-harnesses: Claude Code, Codex, Cursor, OpenCode, Pi, Oh My Pi, Hermes Agent, OpenClaw, OpenHands, DeepSeek (Deep Code), and the rest of the [skills CLI's 20+ supported agents](https://github.com/vercel-labs/skills/blob/main/docs/agents.md). Skills stick to the open Agent Skills spec and avoid harness-only constructs, so one skill behaves the same everywhere. CI proves it by installing every skill into every harness on each PR.

## How do I install?

```bash
npx skills add redhat-cop/skills --skill <skill-name>
```

See the [Install](install.html) page for the per-harness table and the shared `.agents/skills/` directory explanation.

## Are evals run in CI?

No — by policy. CI validates that eval suites are *structurally* sound (unique ids, fixture files exist) but never calls a model. You run evals locally; the recommended method is the paired with-skill/without-skill benchmark that the bundled `skill-creator` skill automates.

## How does versioning work?

Per skill, in `metadata.version` (semver), bumped in the same PR as the change: patch for fixes, minor for added capability, major for breaking workflow changes. There is no repo-wide release train — git history is the record, and `npx skills add owner/repo@vX.Y.Z` pins via git tags if you want reproducibility.

## Why no marketplace?

There is no real standard for marketplaces yet, so we optimized for the thing that *is* standard: the Agent Skills spec plus the skills CLI. A `.claude-plugin/marketplace.json` (generated from the same frontmatter) is the planned seam if plugin-style install becomes worth it — the repo layout already anticipates it.

## Can I contribute my team's internal skills?

If they contain no secrets, internal hostnames, or customer data — yes, that is the point of a community of practice. Sanitize, generalize the hard-coded bits into parameters, and submit via the [proposal issue](https://github.com/redhat-cop/skills/issues/new?template=skill-proposal.yml). Gitleaks runs on every PR as the backstop.

## What does "maturity" mean?

`experimental` — new, still proving itself in the field. `stable` — field-proven, owned, review-gated. `deprecated` — heading out; kept at least a quarter with a pointer to its replacement. Promotions and deprecations are ordinary PRs.
