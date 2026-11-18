## What is this?

A community-of-practice collection of **agent skills** for Red Hat technologies. A skill is a folder with a `SKILL.md` — frontmatter (name, description) plus imperative instructions, optionally bundled with `scripts/`, `references/` and `assets/`. Agents load the name and description at startup (~100 tokens), and pull in the full instructions only when a task matches. That is progressive disclosure, per the open [Agent Skills specification](https://agentskills.io/specification).

Every skill here is:

- **Spec-compliant** — installs into any skills-aware harness via the [skills CLI](https://github.com/vercel-labs/skills)
- **Harness-neutral** — no Claude-only constructs; `allowed-tools` is advisory, never the only safety mechanism
- **Review-gated** — spec + house-rule validation, ownership rules, and a cross-harness install smoke test run on every PR
- **Apache-2.0** — inheriting the repository license

## The catalog

Skills below are generated from `SKILL.md` frontmatter at build time. Click through to GitHub for the full source; install with `npx skills add redhat-cop/skills --skill <name>`.
