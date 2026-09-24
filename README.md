# pretty-agent-skills

Curated multi-agent skills for design, presentations, and Apple iWork automation.

Current skills:
- `visual-designer` (`skills/visual-designer`) — Create design systems, brand guidelines, and visual identities (product, brand-identity presets)
- `presentation-designer` (`skills/presentation-designer`) — Plan and structure presentations with presets (business-pitch, academic, tech-talk)
- `keynote` (`skills/keynote`) — Read, edit, create, and export Apple Keynote presentations (shapes, fill/border styling, images)
- `numbers` (`skills/numbers`) — Read, edit, create, and export Apple Numbers spreadsheets
- `pages` (`skills/pages`) — Read, edit, create, and export Apple Pages documents

## DeepSeek worker plugin (Codex and Claude Code)

`plugins/deepseek-worker` delegates a bounded task to DeepSeek in a fresh Claude Code process. It does not change the default model in Codex or Claude Code and is not a native subagent. The worker can send everything it reads under the chosen `-C` directory to DeepSeek; use only a narrow, reviewed directory. This plugin needs macOS, Claude Code CLI, `jq`, and your own DeepSeek API key.

Install the plugin from this repository's marketplace:

```sh
codex plugin marketplace add principalwater/pretty-agent-skills
codex plugin add deepseek-worker@pretty-agent-skills
claude plugin marketplace add principalwater/pretty-agent-skills
claude plugin install deepseek-worker@pretty-agent-skills --scope user
```

Find the installed skill's `SKILL.md`, then run its adjacent `scripts/setup --from-clipboard` after copying your key to the macOS clipboard. Never paste the key into a chat or command argument. Setup stores it in the login Keychain under service `pretty-agent-deepseek-worker`, account `default`, and clears the clipboard; `scripts/setup --check` confirms configuration without printing the key. For migration from an existing Keychain entry, use `scripts/setup --from-keychain SERVICE ACCOUNT`. Keychain access is deliberately trusted for `/usr/bin/security` to avoid a prompt on every run: **any process running as your macOS user can read this item**, so this is not malicious-process isolation.

From either host, ask for the `deepseek-worker` skill. Its script defaults to Flash and read-only file tools; `--edit` is opt-in, and `--pro` is only for an explicit Pro request. The master reviews all output and edits. A tool-free `--evidence` mode accepts a reviewed UTF-8 file, but still sends its contents to DeepSeek. Run `scripts/selftest` for live boundary checks after a launcher or Claude Code update.

Marketplace updates use the hosts' commands, followed by a new session/restart to pick up changed skill instructions:

```sh
codex plugin marketplace upgrade pretty-agent-skills
codex plugin add deepseek-worker@pretty-agent-skills
claude plugin marketplace update pretty-agent-skills
claude plugin update deepseek-worker@pretty-agent-skills
```

These are update commands, not a promise that either host silently auto-updates on a schedule.

## Install the design/iWork skills via npx

Use the community installer CLI (`skills`) to install from this repo:

```bash
npx skills add https://github.com/principalwater/pretty-agent-skills --skill visual-designer
npx skills add https://github.com/principalwater/pretty-agent-skills --skill presentation-designer
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
  visual-designer/
    SKILL.md
    LICENSE.txt
    presets/
      product.md
      brand-identity.md
  presentation-designer/
    SKILL.md
    LICENSE.txt
    presets/
      business-pitch.md
      academic.md
      tech-talk.md
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

The Keynote `style-shape` command uses GUI scripting via System Events to set fill/border colors (AppleScript's `background fill type` is read-only). This requires macOS accessibility permissions for the controlling app.
