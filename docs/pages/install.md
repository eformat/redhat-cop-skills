## Quickstart

```bash
npx skills add redhat-cop/skills --skill <skill-name>
```

The CLI detects which agents you have installed and links the skill where each one reads it. Add `-g` for global scope, `--skill '*'` for everything, `--list` to browse, and `redhat-cop/skills@vX.Y.Z` to pin a tag.

## Every harness

Most harnesses read the same shared directory, so **one install lights up several at once** — Codex, Cursor, OpenCode, Pi, Oh My Pi and DeepSeek all read `.agents/skills/` (project) or `~/.agents/skills/` (global).

| Harness | Install flag | Skills land in (project) |
|---|---|---|
| Claude Code | `-a claude-code` | `.claude/skills/` |
| Codex | `-a codex` | `.agents/skills/` |
| Cursor | `-a cursor` | `.agents/skills/` |
| OpenCode | `-a opencode` | `.agents/skills/` |
| Pi | `-a pi` | `.agents/skills/` |
| Oh My Pi | *(pi / codex providers)* | `.agents/skills/` |
| Hermes Agent | `-a hermes-agent` | `.hermes/skills/` |
| OpenClaw | `-a openclaw` | `skills/` |
| OpenHands | `-a openhands` | `.openhands/skills/` |
| DeepSeek (Deep Code) | *(no flag — native reader)* | `.agents/skills/` or `.dsh/skills/` |

Example — everything, everywhere, non-interactive:

```bash
npx skills add redhat-cop/skills --skill '*' -g \
  -a claude-code -a codex -a cursor -a opencode -a pi \
  -a hermes-agent -a openclaw -a openhands
```

## Notes

- **DeepSeek (Deep Code / `dsh`)** reads the Agent Skills format natively and follows symlinks; install by linking skills into `~/.agents/skills/` or a project's `.agents/skills/` — the same place the CLI puts them for Codex/OpenCode/Pi.
- **Oh My Pi** discovers skills through its Claude/Codex/Pi providers plus its native `.agents/skills` location, so the installs above cover it.
- **OpenClaw** uses the project's own `skills/` directory at project scope (shown above) and `~/.openclaw/skills/` globally.
- CI installs every skill into every harness on each PR and asserts the files actually landed — compatibility is verified, not assumed.
