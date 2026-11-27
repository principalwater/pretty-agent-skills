# pretty-agent-skills

Curated multi-agent skills for design, presentations, and Apple iWork automation.

Current skills:
- `visual-designer` (`skills/visual-designer`) — Create design systems, brand guidelines, and visual identities (product, brand-identity presets)
- `presentation-designer` (`skills/presentation-designer`) — Plan and structure presentations with presets (business-pitch, academic, tech-talk)
- `keynote` (`skills/keynote`) — Read, edit, create, and export Apple Keynote presentations (shapes, fill/border styling, images)
- `numbers` (`skills/numbers`) — Read, edit, create, and export Apple Numbers spreadsheets
- `pages` (`skills/pages`) — Read, edit, create, and export Apple Pages documents

## Agent worker router (Codex and Claude Code)

`plugins/agent-worker-router` runs a **fresh external** DeepSeek, Claude Code, Codex, or Grok Build worker without changing the host's default model. It is not a native subagent. Access is explicit per call: `read` (default), `edit`, or `full`; `full` requires a separate local opt-in and exposes same-user files and Keychain. `-C` is a starting directory, **not** a privacy boundary for Codex at any access level or for any full-access worker. Codex read-only restricts writes, not reads. Never route secrets or private data across providers without reviewing what the worker can read.

Requires macOS, `zsh`, `jq`, and the relevant agent CLI. DeepSeek additionally needs the user's own API key in the login Keychain. Install or update through the host marketplace:

```sh
codex plugin marketplace add principalwater/pretty-agent-skills
codex plugin add agent-worker-router@pretty-agent-skills
claude plugin marketplace add principalwater/pretty-agent-skills
claude plugin install agent-worker-router@pretty-agent-skills --scope user
```

Locate the installed `agent-worker-router` skill and run its adjacent `scripts/setup --from-clipboard` after copying your own DeepSeek key locally. Setup clears the clipboard. Existing users can run `scripts/setup --from-keychain pretty-agent-deepseek-worker default`; `scripts/setup --check` verifies without printing the key. The same login Keychain item is shared with the legacy plugin, so no second credential is needed. Never paste a key into chat or command arguments.

```sh
"/absolute/installed/path/skills/agent-worker-router/scripts/agent-worker-router" \
  --worker deepseek --access read -C /reviewed/dir 'A bounded task'
```

For a Grok Build review, install the official CLI, run `grok login`, then select `--worker grok -C DIR --access read`. It supports `--model` and `--effort`, uses the CLI’s minimal sandbox and starts a fresh session for each call. [Grok Build CLI](https://docs.x.ai/build/overview)

`--worker claude` uses your Claude Code account; `--worker codex` uses your Codex account. When the official Claude Code plugin `openai/codex-plugin-cc` is installed and enabled, `--worker codex` runs through that plugin's runtime with your MCP servers, plugins, hooks and apps switched off, and otherwise through `codex exec`; `--resume ID`, `--access full`, a `-C` below its Git root, a `.codex` project layer in `-C`, execpolicy rules in `$CODEX_HOME/rules` and an MCP server that `codex mcp list` still reports enabled always use `codex exec`, and `--via plugin|cli` pins the route. On both routes read and edit workers run without execpolicy rules, plugins, hooks, apps, notify, web search and sub-agents, without login shells or your zsh dotfiles, and with only the router's environment; edit writes only to `-C` and a private `TMPDIR` (no `/tmp`, no configured `writable_roots`). Commands listed as `worker_deny_commands` in `~/.config/agent-worker-router/destructive-rules.json` are refused inside worker shells. The receipt's `path` names the route that ran. Keep the native `codex:codex-rescue` agent for in-session work that needs your full Codex configuration: request read-only explicitly (it can write), and note that its shared broker keeps app-server and MCP processes alive after the call. From Codex, Claude and DeepSeek use the router CLI; DeepSeek never uses a native `deepseek-worker` subagent. The Claude worker needs network and macOS Keychain access from the calling Codex session.

Claude/Codex accept `--model`, `--effort`, `--keep` and `--resume ID`; Codex also accepts `--provider ID`. Omitted controls use narrow defaults from Codex `config.toml` or Claude `settings.json`, then CLI defaults; Codex user configuration stays isolated and credential-bearing provider fields are excluded. A compact JSON receipt on stderr reports the route and the settings, access, session, tokens and status that the CLI or the thread rollout observed; missing values are `unverified`, and stdout contains only the answer. Keep the first thread with `--keep`, then resume with the same `-C`; access and controls are resolved again each time. Optional `--lease FILE` / `AGENT_WORKER_ROUTER_LEASE` serializes workers, `--lease-wait SEC` / `AGENT_WORKER_ROUTER_LEASE_WAIT` bounds the wait (default 900), and inherited lease markers refuse nesting. Workers must not start more workers.

When Claude reports a session limit and reset time, the router remembers it locally and skips further Claude-account calls until reset; DeepSeek and Codex remain available. `--access edit` is opt-in. Full access is disabled by default and requires `--access full` plus one setup choice: `scripts/setup --full-access allow` runs without further confirmation, `scripts/setup --full-access ask` opens a macOS confirmation dialog each time, and `scripts/setup --full-access deny` disables it. With `allow`, a prompt-injected master agent could initiate a full call without asking you; use only in trusted workflows. Neither mode isolates same-user malicious code or protects the Keychain. The worker's claims and edits still need master review. No token/cost budget or OpenHavn receipt is enforced. A portable installation prompt for another Mac is in [docs/install-agent-worker-router-prompt.md](docs/install-agent-worker-router-prompt.md).

For updates, use `codex plugin marketplace upgrade pretty-agent-skills` then `codex plugin add agent-worker-router@pretty-agent-skills`; for Claude Code use `claude plugin marketplace update pretty-agent-skills` then `claude plugin update agent-worker-router@pretty-agent-skills`. Restart the host or start a new session to load changed skill instructions. These commands do not imply automatic scheduled updates.

### Optional guard hook

`scripts/agent-worker-guard` is a Claude Code `PreToolUse` hook. It denies Codex launches that bypass the router and asks before destructive actions: recursive deletes outside the session scratchpad, history-rewriting git commands, pushes to `main`/`master`, force pushes, branch deletion and tags, SQL writes, and similar commands or MCP calls. Pushes of other branches go through. Copy the script to `~/.local/bin/agent-worker-guard`, copy `scripts/destructive-rules.default.json` to `~/.config/agent-worker-router/destructive-rules.json`, and add `~/.local/bin/agent-worker-guard --all` as a `PreToolUse` hook for `Bash|Agent|Task|Write|Edit|MultiEdit|NotebookEdit|mcp__.*`. Keep your own tools, accounts, MCP servers and messages in `~/.config/agent-worker-router/destructive-rules.local.json`, outside any repository. It uses the same format, a rule with a known id replaces the default, and its `selftest` section holds its own cases. For example, a local rule with `push_url_regex` can ask before every push to a public host. `agent-worker-guard --selftest` checks both files. If the guard cannot parse a line that runs a command one of its rules watches, it asks instead of allowing it. The guard refuses agent edits to these files, to its off switches and to its hook entry; only the user changes them.

An owner who uses the personal `git-push-public` rule can add `"approved_push": {"url": "https://github.com/example/repo.git", "branch_prefix": "work/"}` to that rule. Use the exact push URL reported by Git. A plain `git push origin <full-commit-id>:refs/heads/work/topic` then uses the standing approval. Several explicit refspecs can be sent together with `--atomic`. Every destination must be in the configured namespace and the remote must have exactly one push URL. Other commands continue through the regular approval rules.

SQL is judged by what it does, not by where it comes from: a query in the arguments, a heredoc or a file is read, comments and strings are set aside, and only a statement that is not a read asks. A file that the same command writes through a redirection, `tee`, `cp`, `mv`, `sed -i` or an interpreter is unknown rather than read from disk, so the copy an earlier run left there is not taken for the query; a script that writes to a path of its own choosing is beyond what the guard can see. Optional settings in the rules narrow the questions: `"sql_ask": "destructive"` lets an `INSERT INTO` and a `CREATE` of a table, view, database, dictionary or function go through unless they overwrite, while every other statement that is not a read still asks; `"unknown_sql_decision": "deny"` refuses a query the guard cannot read and tells the agent to save it to a file in a separate call instead of asking the user about text nobody can see; `tool_scripts` names scripts that are themselves watched commands so that sourcing one is not read as running everything inside it; and `help_commands` names CLIs whose `--help` only prints help. The `about` section of the rules file describes these keys.

Page JavaScript run through a browser tool (`javascript_tool`, `browser_batch`) acts with the user's signed-in session, so rule `browser-js-write` asks when the text holds a write request: a quoted `POST`, `PUT`, `PATCH` or `DELETE` unless it is compared with something (`m === 'DELETE'`), a client call such as `.post(` or `axios.delete(`, a form submit, or an obvious write statement of SQL anywhere in the text. A read sent with `POST` goes through when it is a `fetch` of a plain literal root-relative path (no host, query string or `${}` substitution) that ends in Grafana's `/api/ds/query` or in the Prometheus `/api/v1/query` or `query_range`, with `method: 'POST'` as its first option; the rest of the text is still searched. The exception goes by the path alone: the guard does not know which site the page is on or where a `<base>` element points. For `browser_batch` every string of the input is read, typed text and action summaries included. A method assembled at run time and a mouse click are not seen: the rule catches a mistake, not an attempt to get around it. It rests on two conditions that any MCP rule can use: `when.matches`, a regex searched in each string of a field or of the whole input, and `when.ignore`, a regex whose matches are cut out first. A condition the guard cannot evaluate does not switch its rule off: the rule matches.

The hook speaks the hook protocol that Claude Code and Codex share, and `--harness claude|codex` names the caller. Under Codex a hook cannot ask: `ask` is taken for a failed hook and the call runs (read from the source of Codex 0.163 and 0.172; try it in your own client before you rely on it). So there a match is a denial with a reason, and two optional routes turn that denial into the user's decision. Register one command line, `~/.local/bin/agent-worker-guard --destructive --harness codex --native-prompt --reply`, in `~/.codex/hooks.json` three times: for `PreToolUse` with the matcher `^(Bash|apply_patch|mcp__.*)$`, for `PermissionRequest` with `^Bash$` and for `UserPromptSubmit` without a matcher. Give each entry a `statusMessage`: Codex lists a hook under that text, and as "Hook N" without it. Then trust the entries in Codex (`/hooks`). Without the two flags and the two extra entries the guard only denies, as before.

- `--native-prompt`. When the approval policy lets Codex ask (anything but `never`), a destructive shell call is rewritten to `agent-worker-guard --confirm RULE TOKEN && eval 'command'` and Codex shows its own approval prompt for that line. This needs a rule file in `~/.codex/rules/`, for example `agent-worker-guard.rules` with `prefix_rule(pattern = ["/absolute/path/to/agent-worker-guard", "--confirm"], decision = "prompt")`, the guard installed at a path without spaces or shell metacharacters, and a restart of Codex. The `PermissionRequest` entry notes that Codex asked, and `--confirm` succeeds only with that note: with a rule that is not loaded it fails, and the shell never reaches the command instead of running it unasked. The command itself runs in the shell Codex started, as it would without the guard, but Codex's own rules no longer see it. With an automatic approval reviewer the decision is the reviewer's, not a person's. To get this prompt by default, run Codex with `approval_policy = "on-request"`; the sandbox mode can stay as it is, and with `danger-full-access` other commands still run unasked.
- `--reply`. Any other call (approval policy `never`, `apply_patch`, MCP tools) is refused with a four-digit code and a request to ask the user in plain text. The user's own message that is just that code (`4821`, or `ok 4821`) allows the call, and the same call repeated unchanged passes once within ten minutes. The `UserPromptSubmit` entry reads the message, and only what is typed into the session that asked counts: the prompt of a spawned agent is written by a model and is ignored. The question is plain text because Codex tells its model not to use `request_user_input` for permission requests. A long call is quoted by its start and its end, with the number of characters left out. Codex 0.163 does not tell a hook the working directory of a call, so there an approval also fits the same line in another directory of that session; from 0.172 the directory counts. Whatever types into the same session in the user's place, such as an agent that resumes its own session through `codex exec resume`, passes for the user: this route catches a mistake, not an attempt to get around it.

Approvals and notes live in `~/.config/agent-worker-router/guard-approvals` for a day at most: a note that Codex asked counts for an hour, an approval for ten minutes. The guard refuses agent writes there and to the rule file, and agent runs of the guard itself with `--confirm`, `--native-prompt` or `--reply`: only Codex calls those, for its own events. Codex has no hook event for input sent to a running process, lets a call through when a hook fails or its entry is not trusted, and can switch hooks off in its `config.toml`, which the guard does not protect yet: under Codex the guard is a net, not a boundary.

Upgrading from 0.4: copy both the script and `destructive-rules.default.json` again, since `help_commands` and the option list of `yt` live in the rules. Some decisions change without any setting. No longer asked about: a read whose SQL comment holds an apostrophe, a query given in the arguments while stdin is redirected, `yt start-query` with options before the engine, a ClickHouse temporary table on the Memory engine, `--help` of a CLI in `help_commands`, and a path next to `2>` that used to be read together with the descriptor number. Now asked about, where the old version let them through: a statement behind a SQL comment with an apostrophe, a query passed through a helper function that uses `shift`, `set --`, `"$*"` or `${@:2}`, a command after a quoted `<<WORD` or a quoted operator such as `';'`, a query file that the same command rewrites, and `--queries-file=FILE`. An interpreter that only reads the guard's settings or hook files is refused like one that writes them: read those with `cat` or `jq`.

Upgrading from 0.5: copy the script first and `destructive-rules.default.json` second, because the older script fails on a rule whose `when` names no field, and a hook that fails lets the call through. Now asked about: page JavaScript that sends a write request, as described above.

Upgrading from 0.6: destructive calls are decided as before until the Codex hook entry gets the new flags. With them, and with the two extra entries and the rule file described above, a destructive call under Codex waits for the user's decision instead of being refused outright. Two things change without any setting: `codex execpolicy` counts as inspection and is no longer refused as a direct launch, and the guard refuses an agent's writes to `guard-approvals` and to `agent-worker-guard.rules` and its runs of the guard with `--confirm`, `--native-prompt` or `--reply`.

## Legacy DeepSeek worker plugin (Codex and Claude Code)

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
