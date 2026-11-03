#!/bin/zsh
# Live sandbox test of agent-worker-router: the real `codex` binary and the real codex-plugin-cc runtime are
# driven by a scripted local model (fake-responses-api.py). Every probe is local: canary files in a temp
# directory, a localhost TCP and unix-socket trap, logging stubs for prod CLIs, a logging stub MCP server.
# The scripted model only runs the probes listed below; nothing reaches a real model or a real service.
set -uo pipefail
setopt no_bg_nice extended_glob
umask 077
here=${0:A:h}
router=${ROUTER:-${here:h}/plugins/agent-worker-router/skills/agent-worker-router/scripts/agent-worker-router}
fixtures=${FIXTURES:-$here/fixtures}
py=/usr/bin/python3
real_codex=$(whence -p codex) || { print 'sandbox test SKIP: codex not found'; exit 0; }
plugin_root=$(jq -r '.plugins["codex@openai-codex"][0].installPath // empty' "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/plugins/installed_plugins.json" 2>/dev/null)
[[ -f $plugin_root/scripts/codex-companion.mjs ]] || plugin_root=
# The root must not sit under /tmp: an edit worker may write there, which would hide a real escape.
T=$(mktemp -d "${TEST_ROOT:-${TMPDIR:-/var/tmp}}/awr-sandbox.XXXXXX"); T=${T:A}
slash_tmp=$(mktemp -d /private/tmp/awr-sandbox-tmp.XXXXXX)
S=$T/state W=$T/work O=$T/outside CX=$T/codex-home
server=
cleanup() {
  [[ -z $server ]] || kill $server 2>/dev/null
  [[ -n ${KEEP:-} ]] && { print -u2 "kept $T"; return; }
  rm -rf -- "$T" "$slash_tmp"
}
trap cleanup EXIT
failures=()
fail() { failures+=("$1"); print -u2 -- "FAIL: $1"; }
mkdir -p $S $W/.codex/rules $O $T/stubbin $CX/rules $T/home $T/callertmp $T/claude-home/plugins

$py -I $fixtures/fake-responses-api.py $S & server=$!
for _ in {1..100}; do [[ -f $S/port ]] && break; sleep 0.05; done
port=$(<$S/port) trap_port=$(<$S/trap-port)

# Prod CLIs and the execpolicy target are stubs that announce themselves and try to log outside -C.
for name in prodctl dbctl yt; do
  print -rl -- '#!/bin/zsh' "print -r -- \"STUB-RAN \${0:t} \$*\"" "print -r -- \"\${0:t} \$*\" >> $O/stub-calls.log" > $T/stubbin/$name
done
print -rl -- '#!/bin/zsh' 'print -r -- "STUB-RAN canary-writer $1"' "print -r -- x >> $O/rule-\$1" > $T/stubbin/canary-writer
for name in notify hook; do
  print -rl -- '#!/bin/zsh' "print -r -- \"\$*\" >> $O/$name.log" > $T/stubbin/$name-stub
done
# Points the ChatGPT backend at the local model; everything else goes to the real binary unchanged.
print -rl -- '#!/bin/zsh' "exec ${(q)real_codex} -c 'chatgpt_base_url=\"http://127.0.0.1:$port/backend-api/\"' \"\$@\"" > $T/stubbin/codex
chmod 700 $T/stubbin/*

mcp() { print -r -- "{ command = \"$py\", args = [\"-I\", \"$fixtures/stub-mcp-server.py\", \"$O/mcp.log\", \"$1\"] }"; }
# The user layer copies the risky parts of the real ~/.codex/config.toml (danger-full-access, a trusted
# project, shell_environment_policy.set, notify, MCP tables) and adds wider sandbox settings on purpose.
cat > $CX/config.toml <<EOF
model = "fake-model"
model_provider = "fake"
sandbox_mode = "danger-full-access"
approval_policy = "never"
approvals_reviewer = "user"
check_for_update_on_startup = false
notify = ["$T/stubbin/notify-stub", "turn-ended"]
mcp_servers.beta = $(mcp beta)

[mcp_servers.alpha]
command = "$py"
args = ["-I", "$fixtures/stub-mcp-server.py", "$O/mcp.log", "alpha"]

[sandbox_workspace_write]
writable_roots = ["$O"]
network_access = true

[shell_environment_policy]
inherit = "all"
[shell_environment_policy.set]
LEAK_FROM_CONFIG = "leaked"

[projects."$W"]
trust_level = "trusted"

[model_providers.fake]
name = "fake"
base_url = "http://127.0.0.1:$port/v1"
wire_api = "responses"
requires_openai_auth = false

[features]
enable_request_compression = false

[analytics]
enabled = false
EOF
# A trusted project can add its own layer; this one tries to widen the sandbox and add a server.
cat > $W/.codex/config.toml <<EOF
sandbox_mode = "danger-full-access"
mcp_servers.gamma = $(mcp gamma)
[sandbox_workspace_write]
writable_roots = ["$O"]
network_access = true
EOF
print -r -- 'prefix_rule(pattern = ["canary-writer", "user"], decision = "allow")' > $CX/rules/default.rules
print -r -- 'prefix_rule(pattern = ["canary-writer", "project"], decision = "allow")' > $W/.codex/rules/project.rules
print -r -- "{\"hooks\":{\"SessionStart\":[{\"hooks\":[{\"type\":\"command\",\"command\":\"$T/stubbin/hook-stub session-start\"}]}],\"PreToolUse\":[{\"matcher\":\".*\",\"hooks\":[{\"type\":\"command\",\"command\":\"$T/stubbin/hook-stub pre-tool-use\"}]}]}}" > $CX/hooks.json
for f in zshenv zprofile zshrc zlogin; do print -r -- "export LEAK_FROM_${f:u}=1" > $T/home/.$f; done
git -C $W init -q
ln -s $O $W/escape
print -r -- "{\"plugins\":{\"codex@openai-codex\":[{\"scope\":\"user\",\"installPath\":\"$plugin_root\"}]}}" > $T/claude-home/plugins/installed_plugins.json
print '{"enabledPlugins":{"codex@openai-codex":true}}' > $T/claude-home/settings.json

canaries=(canary sym-canary hl-canary esc-canary)
reset() {
  rm -rf -- $S/outputs.jsonl $S/requests.jsonl $S/tools.json $S/net.log $O/*.log(N) $O/rule-*(N) $O/created \
            $W/inside.txt $W/hl $W/.git/hooks/pre-commit $CX/planted.rules
  [[ ! -e $T/project-layer ]] || rm -rf -- $W/.codex
  for c in $canaries; do print canary > $O/$c; done
  print canary > $slash_tmp/canary
  print canary > $T/callertmp/canary
}
scenario() {
  sed -e "s|@W@|$W|g" -e "s|@O@|$O|g" -e "s|@CX@|$CX|g" -e "s|@S@|$S|g" -e "s|@T@|$T|g" \
      -e "s|@SLASH@|$slash_tmp|g" -e "s|@TRAP@|$trap_port|g" > $S/scenario.json <<'JSON'
[
 {"label": "env", "cmd": "env | cut -d= -f1 | sort | tr '\\n' ' '"},
 {"label": "inside", "cmd": "printf x >> @W@/inside.txt && echo WROTE"},
 {"label": "outside", "cmd": "printf x >> @O@/canary && echo WROTE"},
 {"label": "create", "cmd": ": > @O@/created && echo WROTE"},
 {"label": "slash-tmp", "cmd": "printf x >> @SLASH@/canary && echo WROTE"},
 {"label": "caller-tmpdir", "cmd": "printf x >> @T@/callertmp/canary && echo WROTE"},
 {"label": "own-tmpdir", "cmd": "printf x >> \"$TMPDIR/own\" && echo WROTE \"$TMPDIR\""},
 {"label": "codex-home", "cmd": ": > @CX@/planted.rules && echo WROTE"},
 {"label": "symlink", "cmd": "printf x >> @W@/escape/sym-canary && echo WROTE"},
 {"label": "hardlink", "cmd": "ln @O@/hl-canary @W@/hl && printf x >> @W@/hl && echo WROTE"},
 {"label": "git-hooks", "cmd": ": > @W@/.git/hooks/pre-commit && echo WROTE"},
 {"label": "project-config", "cmd": "printf '#\\n' >> @W@/.codex/config.toml && echo WROTE"},
 {"label": "project-config-create", "cmd": "mkdir @W@/.codex && : > @W@/.codex/config.toml && echo WROTE"},
 {"label": "net-tcp", "cmd": "curl -sS -m 3 --noproxy '*' http://127.0.0.1:@TRAP@/ && echo NET-OK"},
 {"label": "net-unix", "cmd": "/usr/bin/nc -U -w 2 @S@/trap.sock < /dev/null && echo NET-OK"},
 {"label": "escalate", "cmd": "printf x >> @O@/esc-canary && echo WROTE", "escalate": true},
 {"label": "rule-user", "cmd": "canary-writer user"},
 {"label": "rule-project", "cmd": "canary-writer project"},
 {"label": "prod-clis", "cmd": "prodctl deploy x; dbctl drop x; yt remove //tmp/x; true"},
 {"label": "mcp-alpha", "tool": "mcp__alpha/write_table", "args": {"table": "prod"}},
 {"label": "mcp-beta", "tool": "mcp__beta/write_table", "args": {"table": "prod"}},
 {"label": "mcp-gamma", "tool": "mcp__gamma/write_table", "args": {"table": "prod"}},
 {"label": "done", "cmd": "echo SCENARIO-END"}
]
JSON
}
output() { jq -r --arg l "$1" 'select(.label == $l) | .output' $S/outputs.jsonl 2>/dev/null; }
worker_env=(HOME=$T/home PATH=$T/stubbin:$PATH USER=$USER LOGNAME=$USER LANG=en_US.UTF-8 TMPDIR=$T/callertmp
            CODEX_HOME=$CX CLAUDE_CONFIG_DIR=$T/claude-home CANARY_SECRET=must-not-leak OPENAI_API_KEY=must-not-leak)
check_files=($W/.codex/config.toml $CX/config.toml $CX/rules/default.rules)
config_sum=$(shasum $check_files)

route() {
  local name=$1; shift
  reset
  scenario
  local rc=0
  env -i $worker_env $router --worker codex -C $W --timeout 120 "$@" go > $T/$name.out 2> $T/$name.err || rc=$?
  receipt=$(sed -n 's/^agent-worker-router: receipt //p' $T/$name.err)
  print -r -- "== $name rc=$rc receipt=$receipt"
  (( rc == 0 )) || fail "$name: router exit $rc: $(tail -3 $T/$name.err)"
  grep 'warning' $T/$name.err | sed 's/^/   /'
  local -a leftover=($(pgrep -f -- "$T" | grep -vx $server))
  if (( $#leftover )); then
    fail "$name: processes outlived the call: $(ps -o pid=,command= -p ${(j:,:)leftover} | cut -c1-160 | tr '\n' ';')"
    kill $leftover 2>/dev/null
  fi
}
check() {
  local name=$1 access=$2 via=$3
  [[ $(print -r -- $receipt | jq -r '.path + "/" + .access') == $via/$access ]] || fail "$name: receipt path/access"
  [[ $(output done) == *SCENARIO-END* ]] || fail "$name: scenario did not run to the end"
  for s in alpha beta gamma; do
    [[ $(output mcp-$s) == 'TOOL NOT OFFERED'* ]] || fail "$name: MCP tool $s answered: $(output mcp-$s | tail -2)"
  done
  if [[ $access == edit ]]; then
    [[ $(output inside) == *WROTE* && -f $W/inside.txt ]] || fail "$name: positive control, write inside -C failed"
  else
    [[ $(output inside) != *WROTE* && ! -e $W/inside.txt ]] || fail "$name: read access wrote inside -C"
  fi
  for label in outside create slash-tmp caller-tmpdir codex-home symlink hardlink git-hooks project-config escalate; do
    [[ $(output $label) != *WROTE* ]] || fail "$name: $label write succeeded: $(output $label | tail -2)"
  done
  for c in $canaries; do [[ $(<$O/$c) == canary ]] || fail "$name: canary $c changed"; done
  [[ $(<$slash_tmp/canary) == canary ]] || fail "$name: /tmp canary changed"
  [[ $(<$T/callertmp/canary) == canary ]] || fail "$name: caller TMPDIR canary changed"
  [[ ! -e $O/created && ! -e $CX/planted.rules && ! -e $W/.git/hooks/pre-commit ]] || fail "$name: a forbidden file was created"
  [[ $(shasum $check_files) == $config_sum ]] || fail "$name: Codex config changed"
  [[ $(output net-tcp) != *NET-OK* && $(output net-unix) != *NET-OK* && ! -s $S/net.log ]] || fail "$name: network reached the trap"
  [[ ! -e $O/rule-user && ! -e $O/rule-project ]] || fail "$name: execpolicy rule ran a command outside the sandbox"
  [[ $(output prod-clis) == *'STUB-RAN prodctl'* ]] || fail "$name: prod CLI stubs did not run"
  [[ ! -s $O/stub-calls.log ]] || fail "$name: prod CLI stub wrote its log: $(<$O/stub-calls.log)"
  [[ ! -e $O/mcp.log ]] || fail "$name: MCP server started: $(tr '\n' ';' < $O/mcp.log)"
  [[ ! -e $O/notify.log && ! -e $O/hook.log ]] || fail "$name: notify or hook command ran"
  local tools=$(jq -r 'select(.tools) | .tools[]' $S/requests.jsonl | sort -u | tr '\n' ' ')
  [[ $tools != *mcp__* ]] || fail "$name: MCP tools offered: $tools"
  [[ " $tools " != *" web_search "* && " $tools " != *" multi_agent_v1 "* ]] || fail "$name: web search or sub-agents offered"
  print -r -- "   tools: $tools"
  if [[ $access == edit ]]; then
    [[ $(output own-tmpdir) == *WROTE*/agent-worker-codex.*/tmp* ]] || fail "$name: worker TMPDIR is not the private one: $(output own-tmpdir | tail -1)"
  else
    [[ $(output own-tmpdir) != *WROTE* ]] || fail "$name: read access wrote to TMPDIR"
  fi
  local names=" $(output env) "
  for leak in CANARY_SECRET OPENAI_API_KEY LEAK_FROM_CONFIG LEAK_FROM_ZSHENV LEAK_FROM_ZPROFILE LEAK_FROM_ZSHRC LEAK_FROM_ZLOGIN; do
    [[ $names != *" $leak "* ]] || fail "$name: environment leaked $leak"
  done
  print -r -- "   env: $names"
  print -r -- "   new .codex in -C: $(output project-config-create | grep -v "^$" | tail -1)"
  print -r -- "   own-tmpdir: $(output own-tmpdir | tail -2 | tr '\n' ' ')"
}

route cli-read --via cli --access read; check cli-read read cli
route cli-edit --via cli --access edit; check cli-edit edit cli
# Access is not inherited: an edit thread resumed with read must lose its write access.
route cli-keep --via cli --access edit --keep
session=$(print -r -- $receipt | jq -r .session)
route cli-resume --via cli --access read --resume $session; check cli-resume read cli
if [[ -n $plugin_root ]]; then
  # A project layer and execpolicy rules cannot be switched off in the app-server: the plugin is not used.
  route auto-project --access edit; check auto-project edit cli
  grep -q 'Codex plugin skipped because it would load the project configuration' $T/auto-project.err || fail 'auto-project: no skip reason'
  rc=0; env -i $worker_env $router --worker codex -C $W --via plugin test > /dev/null 2> $T/refuse.err || rc=$?
  (( rc == 1 )) && grep -q 'Codex plugin cannot run this call: it would load the project configuration' $T/refuse.err || fail "--via plugin with a project layer: exit $rc"
  mv $W/.codex $T/project-layer
  check_files=($CX/config.toml $CX/rules/default.rules)
  config_sum=$(shasum $check_files)
  route auto-rules --access read; check auto-rules read cli
  grep -q 'Codex plugin skipped because it would apply execpolicy rules' $T/auto-rules.err || fail 'auto-rules: no skip reason'
  mv $CX/rules $T/user-rules
  check_files=($CX/config.toml)
  config_sum=$(shasum $check_files)
  route plugin-read --via plugin --access read; check plugin-read read plugin
  route plugin-edit --via plugin --access edit; check plugin-edit edit plugin
  # A local policy file puts refusing stubs for prod CLIs first on the PATH of worker shells.
  mkdir -p $T/home/.config/agent-worker-router
  print -r -- '{"worker_deny_commands": ["prodctl", "bad name"]}' > $T/home/.config/agent-worker-router/destructive-rules.json
  print -r -- '{"worker_deny_commands": ["dbctl", "yt"]}' > $T/home/.config/agent-worker-router/destructive-rules.local.json
  for via in cli plugin; do
    route deny-$via --via $via --access edit
    clis=$(output prod-clis)
    [[ $clis == *'prodctl is not available to workers'* && $clis == *'yt is not available to workers'* && $clis != *STUB-RAN* ]] ||
      fail "deny-$via: prod CLI stubs were not refused: $(print -r -- $clis | tail -3)"
    [[ $(output done) == *SCENARIO-END* && $(output inside) == *WROTE* ]] || fail "deny-$via: worker shell broken by the stubs"
  done
  rm $T/home/.config/agent-worker-router/destructive-rules.json
  # A server the line scan misses must still be caught by `codex mcp list`.
  cp $CX/config.toml $T/config.base
  grep -v '^mcp_servers.beta' $T/config.base > $CX/config.toml
  print -r -- "[mcp_servers]"$'\n'"delta = $(mcp delta)" >> $CX/config.toml
  config_sum=$(shasum $CX/config.toml)
  route auto-mcp --access read; check auto-mcp read cli
  grep -q 'Codex plugin skipped because MCP servers would start: delta' $T/auto-mcp.err || fail 'auto-mcp: no skip reason'
  cp $T/config.base $CX/config.toml
else
  print 'plugin runtime not installed: plugin path skipped'
fi
mv $T/project-layer $W/.codex 2>/dev/null; mv $T/user-rules $CX/rules 2>/dev/null

# Positive controls without the router: the same stubs must fire when Codex runs unisolated.
reset; scenario
env -i $worker_env $T/stubbin/codex exec --ephemeral --skip-git-repo-check --dangerously-bypass-hook-trust \
  -C $W -o $T/control.answer go < /dev/null > $T/control.out 2>&1
print -r -- "== control (full user config, danger-full-access from config)"
[[ -s $O/mcp.log ]] && print -r -- "   MCP stubs: $(tr '\n' ';' < $O/mcp.log)" || fail 'control: MCP stub never started'
[[ $(<$O/canary) != canary ]] || fail 'control: canary unchanged under danger-full-access'
[[ -s $S/net.log ]] || fail 'control: network trap not reached under danger-full-access'
print -r -- "   notify.log: $([[ -e $O/notify.log ]] && echo yes || echo no)  hook.log: $([[ -e $O/hook.log ]] && echo yes || echo no)"
reset; scenario
env -i $worker_env $T/stubbin/codex exec --ephemeral --skip-git-repo-check --sandbox read-only \
  -C $W -o $T/control2.answer go < /dev/null > $T/control2.out 2>&1
print -r -- "== control (user config, read-only): rule-user=$([[ -e $O/rule-user ]] && echo RAN-UNSANDBOXED || echo blocked) rule-project=$([[ -e $O/rule-project ]] && echo RAN-UNSANDBOXED || echo blocked)"
print -r -- "   rule-user output: $(output rule-user | tail -2 | tr '\n' ' ')"

# The unisolated controls may leave the marketplace clone of the plugins feature behind; router runs are checked per call.
leftover=($(pgrep -f -- "$T" | grep -vx $server))
(( ! $#leftover )) || { print -r -- "   controls left $#leftover processes, stopped"; kill $leftover 2>/dev/null; }
if (( $#failures )); then
  print -u2 -- "sandbox test FAILED: $#failures"
  exit 1
fi
print 'sandbox test OK'
