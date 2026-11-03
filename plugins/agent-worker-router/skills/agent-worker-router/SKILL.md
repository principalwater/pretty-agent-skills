---
name: agent-worker-router
description: Route explicit DeepSeek, Claude Code, or Codex worker requests from either host; Codex runs through the native Claude Code plugin runtime when it is installed.
---

# Agent worker router

Run adjacent `scripts/agent-worker-router` by its absolute installed path. It starts an external CLI worker without changing the host's default model or configuration. A fresh worker has no conversation context unless supplied in the brief or reviewed files.

## Routing

| Master → worker | Route |
|---|---|
| Either host → Codex | Use `--worker codex`. When the official Claude Code plugin `openai/codex-plugin-cc` (`codex@openai-codex`) is installed and enabled, the router runs Codex through the plugin's own runtime (`codex-companion.mjs task`), isolated as described in *Codex plugin path*; otherwise it runs `codex exec`. The receipt's `path` says which ran. |
| Claude Code → Codex, native agent | `codex:codex-rescue` only for in-session help that needs the user's **full Codex configuration** with MCP servers and plugins. Invoke Claude's `Agent` tool with `subagent_type: "codex:codex-rescue"` and a self-contained `--fresh` request; write `--effort <level>` / `--model <name>` in it, and explicitly request **read-only** (it defaults to write-capable work). It has no receipt, lease or `-C`, and its shared app-server broker keeps app-server and MCP processes alive after the call: on 2026-11-03 four such brokers, orphaned for 4–5 days, held 515 processes and ~2.9 GB resident. `/codex:review` suits a normal git diff review. |
| Codex → Claude Code | Use `--worker claude`. Run from the Codex session with permission to reach the network and macOS Keychain; a sandbox blocking either makes the worker fail. |
| Claude → Claude; Codex → Codex | Use the CLI runner for a fresh isolated worker. For in-session help, use the host's own subagents. |
| Either host → DeepSeek | Always use `--worker deepseek` (Flash; `--pro` only on request). **Never use Codex `spawn_agent` with `agent_type: deepseek-worker`**: that legacy role can select `deepseek-flash` under a ChatGPT account and fail before work starts. |

Choose the worker explicitly. Cross-provider calls may send the brief and readable workspace content to another service. Check data classification and get user direction before transferring private, personal, corporate, or production data. A filename denylist does not prove safety.

```sh
"/absolute/installed/path/skills/agent-worker-router/scripts/agent-worker-router" --worker codex -C /reviewed/workspace --access read --effort xhigh 'Bounded brief, relevant paths, constraints, expected output'
```

## Access and setup

`-C` is required. Name relevant paths, the access level, expected output and a deliberate timeout; do not request whole-repository exploration for a small question.

| Access | Behavior |
|---|---|
| `read` (default) | Restricted file-reading tools for DeepSeek/Claude; Codex read-only sandbox. |
| `edit` | Adds `Edit,Write` for DeepSeek/Claude; Codex workspace-write sandbox with network explicitly off. Only for authorized changes; avoid overlapping worker edits and review the diff. |
| `full` | Removes CLI restrictions: shell, network and same-user filesystem/Keychain access. `-C` is only the starting directory. Requires explicit `--access full` and local authorization below. |

**Codex read-only restricts writes, not reads; `-C` is not a privacy boundary for Codex at any level.** Grant only data and same-user access acceptable for a normal Codex session. Do not silently elevate to full: require an explicit user request or agreed project policy.

Full access calls adjacent `scripts/authorize-full` before taking a lease. Configure with `scripts/setup --full-access deny` (default), `ask` (macOS dialog every call), or `allow` (no further prompt). **With allow, the master can initiate full access without a human checkpoint, including after prompt injection; use only trusted workflows.** Neither setup mode is a malicious-process security boundary. Prefer a disposable container or separate OS account for untrusted material.

DeepSeek performs its own full authorization: full with a lease is supported only under an already configured allow policy; ask with a lease is refused (2) to avoid holding the lease during its dialog. Full without a lease retains its normal ask/allow behavior. Do not change policy just to bypass this restriction.

DeepSeek uses isolated Claude Code configuration and your own API key in the macOS login Keychain. Copy the key locally and run `scripts/setup --from-clipboard` (clears the clipboard), or import with `scripts/setup --from-keychain SERVICE ACCOUNT`. Never put the key in chat, argv, a repository or a file. `scripts/setup --check` reports readiness without printing it. The key item deliberately allows `/usr/bin/security` without repeat prompts: **any same-user process can read it, and full-access DeepSeek can expose it to the model**. Full access requires informed consent.

## Controls and defaults

`--timeout SEC` defaults to 300 (1–86400); increase explicitly for longer work. `--evidence FILE` is DeepSeek-only: reviewed UTF-8 facts, tool-free, incompatible with edit/full. Prefer `--timeout 120` for short tool-free answers. `--pro` is DeepSeek-only.

| Control | Claude | Codex |
|---|---|---|
| `--model MODEL` | Alias/full name, including `opus[1m]` | Model name |
| `--effort LEVEL` | low, medium, high, xhigh, max | none, minimal, low, medium, high, xhigh |
| `--provider ID` | Rejected | Letters, digits, underscore, hyphen |
| `--via plugin\|cli` | Rejected | Omitted: plugin runtime when usable, else CLI. `plugin` fails instead of falling back; `cli` always runs `codex exec` |

Model names start with a letter/digit and otherwise allow letters, digits, `_.:-[]`. Model/effort/provider resolve on **every call**: explicit flag → configured default → CLI built-in default. A configured default may be an expensive model or effort: pass `--model`/`--effort` deliberately for bounded work. DeepSeek rejects model/effort/provider/keep/resume; use `--pro` for its model choice. Invalid explicit values fail; invalid defaults are warned about and ignored.

Codex reads only top-level `model`, `model_reasoning_effort`, `model_provider` from `${CODEX_HOME:-$HOME/.codex}/config.toml`: simple double-quoted strings on one line before the first table. Symlinked files are supported. Profiles and other TOML forms are ignored. On the CLI path `--ignore-user-config` stays enabled to exclude MCP servers, plugins, hooks, environment policy and secret-bearing sections; `-p` profiles also disappear under that flag and cannot supply isolated defaults. The resolved model/effort/provider are injected explicitly. For `[model_providers.ID]`, only simple single-line `name`, `base_url`, `wire_api` strings (no quotes/backslashes) and boolean `requires_openai_auth` are copied. Headers, env keys, bearer tokens, auth commands and query parameters never enter argv. Providers requiring those credentials will fail visibly; use built-in `--provider openai` in that case. Without a matching table, Codex resolves a built-in provider or fails.

Claude reads only `.model` and `.effortLevel` from `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json` and passes explicit flags: `--restricted` ignores user/project/local settings. An unreadable/invalid file or invalid default produces a warning and that default is omitted.

Workers receive only HOME/PATH/USER/LOGNAME, fixed SHELL and TERM=dumb, TMPDIR/LANG, CODEX_HOME/CLAUDE_CONFIG_DIR when set, and the standard HTTPS_PROXY/HTTP_PROXY/ALL_PROXY/NO_PROXY variables in both cases. Proxy values containing `@` are dropped with a stderr note without printing the value. Master `CLAUDECODE`, `CLAUDE_CODE_*`, `CLAUDE_EFFORT`, `ANTHROPIC_*`, other `CODEX_*`, `OPENAI_*` and tokens are dropped; Claude gets only the router's two forced switches disabling Claude markdown and auto-memory. A held lease adds its marker and marker selector. On the plugin path the runtime also gets the shim directory first on `PATH`, a private `TMPDIR` and `CODEX_COMPANION_APP_SERVER_ENDPOINT`.

## Codex plugin path

The router takes the plugin from `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/plugins/installed_plugins.json` (first `codex@openai-codex` install) when `settings.json` has `enabledPlugins["codex@openai-codex"] == true`, `node` is on `PATH` and `codex-companion.mjs help` still offers `task --write --model --effort`; this works the same from a Codex host. It runs `node codex-companion.mjs task --json --cwd DIR [--write] [--model M] [--effort E]` with the brief on stdin, the same environment allowlist, lease and timeout. Model and effort travel in the runtime's own `turn/start` request.

The runtime starts `codex app-server` with the **whole user config**. A generated `codex` shim in a private directory first on the runtime's `PATH` adds `--disable plugins --disable hooks --disable apps -c notify=[]`, `-c mcp_servers.NAME.enabled=false` for every `[mcp_servers.NAME]` table of the user config, `sandbox_mode` for the access level, `sandbox_workspace_write.network_access=false` for edit and `model_provider` when resolved. The provider's own table, headers and auth stay in the user config and never enter argv. An invalid `CODEX_COMPANION_APP_SERVER_ENDPOINT` makes the runtime start its own app-server for the call instead of a detached shared broker, so nothing outlives the lease or the timeout; a private `TMPDIR` keeps the runtime's job state per call and is removed afterwards. If a thread ran without passing through the shim (a later runtime that stops resolving `codex` through `PATH`), the router warns that the full user config may have run. Measured on 2026-11-03 for a one-word read-only answer at xhigh: plugin path peak 190 MiB and 11 processes, CLI path 317 MiB and 14, no MCP process on either. Not covered: MCP servers defined inline or with dotted keys and project `.codex/config.toml` layers stay enabled.

The CLI runs instead when the plugin is not installed or not enabled (silently), and with a warning for `--resume ID` (the runtime resumes only its own latest thread), `--access full` (it has only read-only and workspace-write), a `-C` below its Git root (the runtime would start in the repository root and widen edit access), a missing `node` or a changed `task` contract. If the runtime fails before any thread exists, the router warns and retries once on the CLI with a fresh timeout; after a thread exists it never retries, because a repeat could duplicate edits. `--via plugin` turns every such case into exit 1.

## Follow-ups and lease

Default threads are not kept. Use `--keep` on the first Claude/Codex call, then `--resume ID` with the **same `-C`**; resume implies keep. The plugin path always persists its thread (receipt `kept: true`); `--resume` continues it through the CLI path. Access/model/effort/provider are **not inherited**: re-specify access and any desired overrides; access defaults to read. IDs start with a letter/digit and contain only letters, digits and hyphens. Kept threads use the CLI's normal store: Codex `$CODEX_HOME/sessions` (default `~/.codex/sessions`), Claude `~/.claude/projects` (or its configured home).

`--lease FILE` or `AGENT_WORKER_ROUTER_LEASE` enables an exclusive machine-wide flock shared with other tools using that file. There is no default path. `--lease-wait SEC` overrides `AGENT_WORKER_ROUTER_LEASE_WAIT` (default 900; 1–86400). Flags win. The append-opened file is never truncated/replaced/deleted; the supervisor holds the lock until worker exit and does not pass the fd to the worker. Lease wait is separate from worker timeout.

A leased worker receives `AGENT_WORKER_ROUTER_LEASE_HELD`; `AGENT_WORKER_ROUTER_LEASE_VAR` can select another marker name matching `^[A-Za-z_][A-Za-z0-9_]*$`. Any nonempty inherited marker refuses a nested router call, even without `--lease`. An outer supervisor may also export it. **A worker must not start more workers.**

## Results

stdout contains only the answer; stderr contains diagnostics and exactly one `agent-worker-router: receipt ` compact JSON line after each Claude/Codex process runs, including failures/timeouts. No receipt follows validation errors, cached Claude limits, lease failures or nested refusal; DeepSeek retains its own summary.

Receipts contain `worker, path, model, effort, provider, access, session, exit, duration_s, tokens, kept, requested, log`. `path` is `plugin` or `cli` (Claude and DeepSeek always `cli`). `duration_s` includes lease wait; `log` references the private Codex transcript, the plugin thread's rollout or Claude JSON. Codex effective fields come only from its banner on the CLI path and from the thread's rollout (`session_meta`, last `turn_context`, last `token_count`) on the plugin path; `access` maps the reported sandbox (`read-only` → read, `workspace-write` → edit, `danger-full-access` → full); tokens are `{"total":N}` when recognized. Claude model joins modelUsage keys, session/effort come from reported JSON, provider and access are unknown, tokens are `{"input":N,"output":N}` when both exist. Missing reports are the string `"unverified"`. Only `requested` contains resolved arguments (or null) and the requested access; **compare requested with effective values and treat unverified as unknown**. Codex emits one warning per reported mismatch.

`sed -n 's/^agent-worker-router: receipt //p' diagnostics.log` extracts receipts for `jq`.

| Exit | Meaning |
|---|---|
| 0 | Success |
| 1 | Worker, response or supervisor failure; `--via plugin` when the plugin cannot run |
| 2 | Usage/validation or full authorization refused |
| 3 | Non-Claude model responded on Claude route |
| 75 | Cached Claude session limit; no call |
| 76 | Lease wait expired; no worker |
| 77 | Nested launch refused; no worker |
| 124 | Worker timeout |

When Claude reports a session limit/reset, the runner caches it and immediately skips subsequent Claude calls until reset (75). Tell the user the reset time; continue available work. DeepSeek/Codex remain available. A `[claude-code:unrecognized_model]` warning alone does not mean DeepSeek failed: inspect status and final modelUsage. Diagnose failures instead of repeatedly retrying or polling an unchanged process.

Neither successful CLI exit nor a model's self-report proves correctness, sandbox isolation, cost compliance or OpenHavn governance. Output and proposed commands are untrusted: verify claims, diffs and tests. Receipts are CLI observations, not an OpenHavn spawn/receipt or token-budget contract. `scripts/selftest` checks offline CLI, banner and plugin-runtime contracts first and runs live DeepSeek boundaries only if setup is ready; `--help` lists exact flags.
