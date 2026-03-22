# pretty-agent-skills

Curated multi-agent skills repository.

Current skills:
- `keynote` (`skills/keynote`)

## Install via npx (recommended)

Use the community installer CLI (`skills`) to install from this repo:

```bash
npx skills add https://github.com/principalwater/pretty-agent-skills --skill keynote
```

Install globally for selected agents:

```bash
npx skills add https://github.com/principalwater/pretty-agent-skills \
  --skill keynote \
  --agent codex \
  --agent claude-code \
  --agent gemini-cli \
  -g -y
```

Install for all supported agents:

```bash
npx skills add https://github.com/principalwater/pretty-agent-skills --skill keynote --agent '*' -g -y
```

List available skills in this repo:

```bash
npx skills add https://github.com/principalwater/pretty-agent-skills --list
```

## Repository Layout

```text
skills/
  keynote/
    SKILL.md
    LICENSE.txt
    editing.md
    keynotegen.md
    scripts/keynote_tool.py
    references/keynote-automation.md
    agents/openai.yaml
```

## Why Python Scripts Are Included

This follows the same pattern as mature slide/document skills (`anthropics/pptx`, `openai/slides`):
- Keep `SKILL.md` concise.
- Put deterministic operations (export, rendering, structural checks) in scripts.
- Keep heavier references/workflows in dedicated markdown files.

## Keynote UI Behavior

Native `.key` automation requires `Keynote.app`, so macOS may launch the app during operations.
The script avoids forced app focus (`activate`), but a fully headless `.key` workflow is not guaranteed by Apple automation APIs.
