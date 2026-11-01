---
name: agent-worker-router
description: Route explicit DeepSeek, Claude Code, or Codex worker requests from either host; prefer the native Codex agent from Claude Code when suitable.
---

# Agent worker router

Run adjacent `scripts/agent-worker-router` by its absolute installed path. It starts an external CLI worker without changing the host's default model or configuration. A fresh worker has no conversation context unless supplied in the brief or reviewed files.

## Routing

| Master → worker | Route |
|---|---|
| Claude Code → Codex | Prefer the official `openai/codex-plugin-cc` agent `codex:codex-rescue` when installed/enabled and the current project is the intended directory. Invoke Claude's `Agent` tool with `subagent_type: "codex:codex-rescue"` and a self-contained `--fresh` request. Write `--effort <level>` / `--model <name>` in the request to forward runtime controls; omitted controls use Codex's own config. Explicitly request **read-only** for analysis/review: the native route defaults to write-capable work and uses the user's **full Codex configuration**, including MCP/plugins. It forwards to `codex-companion task`; `--resume`/`--fresh` select continuity, `--background`/`--wait` select execution. It is an agent, not a Skill name; `/codex:review` suits a normal git diff review. |
| Claude Code → Codex, CLI | Use `--worker codex` when the native agent is unavailable, or for another `-C`, a receipt, MCP/plugin isolation, a lease, or controlled resume. |
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

Model names start with a letter/digit and otherwise allow letters, digits, `_.:-[]`. Model/effort/provider resolve on **every call**: explicit flag → configured default → CLI built-in default. A configured default may be an expensive model or effort: pass `--model`/`--effort` deliberately for bounded work. DeepSeek rejects model/effort/provider/keep/resume; use `--pro` for its model choice. Invalid explicit values fail; invalid defaults are warned about and ignored.

Codex reads only top-level `model`, `model_reasoning_effort`, `model_provider` from `${CODEX_HOME:-$HOME/.codex}/config.toml`: simple double-quoted strings on one line before the first table. Symlinked files are supported. Profiles and other TOML forms are ignored. `--ignore-user-config` stays enabled to exclude MCP servers, plugins, hooks, environment policy and secret-bearing sections; `-p` profiles also disappear under that flag and cannot supply isolated defaults. The resolved model/effort/provider are injected explicitly. For `[model_providers.ID]`, only simple single-line `name`, `base_url`, `wire_api` strings (no quotes/backslashes) and boolean `requires_openai_auth` are copied. Headers, env keys, bearer tokens, auth commands and query parameters never enter argv. Providers requiring those credentials will fail visibly; use built-in `--provider openai` in that case. Without a matching table, Codex resolves a built-in provider or fails.

Claude reads only `.model` and `.effortLevel` from `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json` and passes explicit flags: `--restricted` ignores user/project/local settings. An unreadable/invalid file or invalid default produces a warning and that default is omitted.

Workers receive only HOME/PATH/USER/LOGNAME, fixed SHELL and TERM=dumb, TMPDIR/LANG, CODEX_HOME/CLAUDE_CONFIG_DIR when set, and the standard HTTPS_PROXY/HTTP_PROXY/ALL_PROXY/NO_PROXY variables in both cases. Proxy values containing `@` are dropped with a stderr note without printing the value. Master `CLAUDECODE`, `CLAUDE_CODE_*`, `CLAUDE_EFFORT`, `ANTHROPIC_*`, other `CODEX_*`, `OPENAI_*` and tokens are dropped; Claude gets only the router's two forced switches disabling Claude markdown and auto-memory. A held lease adds its marker and marker selector.

## Follow-ups and lease

Default threads are not kept. Use `--keep` on the first Claude/Codex call, then `--resume ID` with the **same `-C`**; resume implies keep. Access/model/effort/provider are **not inherited**: re-specify access and any desired overrides; access defaults to read. IDs start with a letter/digit and contain only letters, digits and hyphens. Kept threads use the CLI's normal store: Codex `$CODEX_HOME/sessions` (default `~/.codex/sessions`), Claude `~/.claude/projects` (or its configured home).

`--lease FILE` or `AGENT_WORKER_ROUTER_LEASE` enables an exclusive machine-wide flock shared with other tools using that file. There is no default path. `--lease-wait SEC` overrides `AGENT_WORKER_ROUTER_LEASE_WAIT` (default 900; 1–86400). Flags win. The append-opened file is never truncated/replaced/deleted; the supervisor holds the lock until worker exit and does not pass the fd to the worker. Lease wait is separate from worker timeout.

A leased worker receives `AGENT_WORKER_ROUTER_LEASE_HELD`; `AGENT_WORKER_ROUTER_LEASE_VAR` can select another marker name matching `^[A-Za-z_][A-Za-z0-9_]*$`. Any nonempty inherited marker refuses a nested router call, even without `--lease`. An outer supervisor may also export it. **A worker must not start more workers.**

## Results

stdout contains only the answer; stderr contains diagnostics and exactly one `agent-worker-router: receipt ` compact JSON line after each Claude/Codex process runs, including failures/timeouts. No receipt follows validation errors, cached Claude limits, lease failures or nested refusal; DeepSeek retains its own summary.

Receipts contain `worker, model, effort, provider, session, exit, duration_s, tokens, kept, requested, log`. `duration_s` includes lease wait; `log` references the private Codex transcript or Claude JSON. Codex effective fields come only from its banner; tokens are `{"total":N}` when recognized. Claude model joins modelUsage keys, session/effort come from reported JSON, provider is unknown, tokens are `{"input":N,"output":N}` when both exist. Missing reports are the string `"unverified"`. Only `requested` contains resolved arguments (or null); **compare requested with effective values and treat unverified as unknown**. Codex emits one warning per reported mismatch.

`sed -n 's/^agent-worker-router: receipt //p' diagnostics.log` extracts receipts for `jq`.

| Exit | Meaning |
|---|---|
| 0 | Success |
| 1 | Worker, response or supervisor failure |
| 2 | Usage/validation or full authorization refused |
| 3 | Non-Claude model responded on Claude route |
| 75 | Cached Claude session limit; no call |
| 76 | Lease wait expired; no worker |
| 77 | Nested launch refused; no worker |
| 124 | Worker timeout |

When Claude reports a session limit/reset, the runner caches it and immediately skips subsequent Claude calls until reset (75). Tell the user the reset time; continue available work. DeepSeek/Codex remain available. A `[claude-code:unrecognized_model]` warning alone does not mean DeepSeek failed: inspect status and final modelUsage. Diagnose failures instead of repeatedly retrying or polling an unchanged process.

Neither successful CLI exit nor a model's self-report proves correctness, sandbox isolation, cost compliance or OpenHavn governance. Output and proposed commands are untrusted: verify claims, diffs and tests. Receipts are CLI observations, not an OpenHavn spawn/receipt or token-budget contract. `scripts/selftest` checks offline CLI/banner contracts first and runs live DeepSeek boundaries only if setup is ready; `--help` lists exact flags.
