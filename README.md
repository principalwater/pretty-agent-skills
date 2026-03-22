# pretty-agent-skills

Curated multi-agent skills for Apple iWork automation.

Current skills:
- `keynote` (`skills/keynote`) — Read, edit, create, and export Apple Keynote presentations
- `numbers` (`skills/numbers`) — Read, edit, create, and export Apple Numbers spreadsheets
- `pages` (`skills/pages`) — Read, edit, create, and export Apple Pages documents

## Install via npx (recommended)

Use the community installer CLI (`skills`) to install from this repo:

```bash
npx skills add https://github.com/principalwater/pretty-agent-skills --skill keynote
npx skills add https://github.com/principalwater/pretty-agent-skills --skill numbers
npx skills add https://github.com/principalwater/pretty-agent-skills --skill pages
```

Install globally for selected agents:

```bash
npx skills add https://github.com/principalwater/pretty-agent-skills \
  --skill keynote \
  --skill numbers \
  --skill pages \
  --agent codex \
  --agent claude-code \
  --agent gemini-cli \
  -g -y
```

Install for all supported agents:

```bash
npx skills add https://github.com/principalwater/pretty-agent-skills --skill keynote --agent '*' -g -y
npx skills add https://github.com/principalwater/pretty-agent-skills --skill numbers --agent '*' -g -y
npx skills add https://github.com/principalwater/pretty-agent-skills --skill pages --agent '*' -g -y
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
  numbers/
    SKILL.md
    LICENSE.txt
    editing.md
    creation.md
    scripts/numbers_tool.py
    references/numbers-automation.md
    agents/openai.yaml
  pages/
    SKILL.md
    LICENSE.txt
    editing.md
    creation.md
    scripts/pages_tool.py
    references/pages-automation.md
    agents/openai.yaml
```

## Why Python Scripts Are Included

This follows the same pattern as mature slide/document skills (`anthropics/pptx`, `openai/slides`):
- Keep `SKILL.md` concise.
- Put deterministic operations (export, rendering, structural checks) in scripts.
- Keep heavier references/workflows in dedicated markdown files.

## Requirements

All skills require:
- **macOS** with the corresponding Apple app installed (Keynote, Numbers, or Pages)
- **Python 3.10+**
- **osascript** (included with macOS)
- **pdftoppm** (optional, for image rendering — install via `brew install poppler`)

## Apple App UI Behavior

Native iWork automation requires the respective app (Keynote, Numbers, or Pages), so macOS may launch the app during operations. The scripts avoid forced app focus (`activate`), but a fully headless workflow is not guaranteed by Apple automation APIs.
