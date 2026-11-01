#!/bin/zsh
set -euo pipefail
setopt no_bg_nice
umask 077
router=${0:A:h:h}/plugins/agent-worker-router/skills/agent-worker-router/scripts/agent-worker-router
tmp=$(mktemp -d)
tmp=${tmp:A}
trap 'rm -rf -- "$tmp"' EXIT
mkdir -p "$tmp/work" "$tmp/home" "$tmp/bin"
export HOME=$tmp/home PATH=$tmp/bin:$PATH TMPDIR=$tmp
unset CODEX_HOME CLAUDE_CONFIG_DIR AGENT_WORKER_ROUTER_LEASE AGENT_WORKER_ROUTER_LEASE_WAIT AGENT_WORKER_ROUTER_LEASE_VAR AGENT_WORKER_ROUTER_LEASE_HELD
unset HTTPS_PROXY HTTP_PROXY ALL_PROXY NO_PROXY https_proxy http_proxy all_proxy no_proxy
fail() { print -u2 -- "router smoke FAIL: $1"; exit 1; }
run() {
  rc=0
  "$router" "$@" > "$tmp/stdout" 2> "$tmp/stderr" || rc=$?
  (( rc == 0 )) || { cat "$tmp/stderr" >&2; fail "unexpected exit $rc: $*"; }
  [[ $(< "$tmp/stdout") == OK ]] || fail 'stdout is not just the answer'
}
receipt() {
  sed -n 's/^agent-worker-router: receipt //p' "$tmp/stderr" > "$tmp/receipt"
  jq -se 'length == 1' "$tmp/receipt" >/dev/null || fail 'expected exactly one receipt'
  jq -e "$1" "$tmp/receipt" >/dev/null || fail "receipt: $1"
}
reject() {
  local expected=$1
  shift
  rc=0
  "$router" "$@" > "$tmp/stdout" 2> "$tmp/stderr" || rc=$?
  (( rc == expected )) || fail "expected $expected, got $rc: $*"
  ! grep -q '^agent-worker-router: receipt ' "$tmp/stderr" || fail 'receipt without worker'
}
argv() {
  local -a observed=("${(@f)$(< "$HOME/argv")}") expected=("$@") normalized=()
  local value previous=
  for value in "${observed[@]}"; do
    if [[ $previous == --output-last-message ]]; then normalized+=(ANSWER)
    elif [[ $value == "$tmp/work" ]]; then normalized+=(DIR)
    else normalized+=("$value")
    fi
    previous=$value
  done
  if [[ "${(pj:\n:)normalized}" != "${(pj:\n:)expected}" ]]; then
    print -u2 -l -- 'expected:' "${expected[@]}" 'observed:' "${normalized[@]}"
    fail argv
  fi
}
wait_file() { perl -e 'for (1..500) { exit 0 if -e $ARGV[0]; select undef,undef,undef,0.02 } exit 1' "$1" || fail 'waiting for worker'; }

cat > "$tmp/bin/codex" <<'FAKE'
#!/bin/zsh
set -euo pipefail
if [[ $* == 'exec --help' || $* == 'exec resume --help' ]]; then
  print -- '--sandbox --ephemeral --ignore-user-config --skip-git-repo-check --output-last-message --dangerously-bypass-approvals-and-sandbox -c'
  exit 0
fi
print -l -- "$@" > "$HOME/argv"
env > "$HOME/environment"
print -r -- "$PWD" > "$HOME/cwd"
cat > "$HOME/brief"
if [[ -f $HOME/check-lease ]]; then
  perl -e 'my @want=stat shift; for (glob "/dev/fd/*") { my @s=stat $_; die "lease fd leaked\n" if @s && $s[0]==$want[0] && $s[1]==$want[1] }' "$(< "$HOME/check-lease")"
fi
data=$(< "$HOME/fake.json")
print -u2 -l -- 'Reading additional input from stdin...' 'OpenAI Codex v0.163.0' '--------' "workdir: $PWD"
print -u2 -l -- "model: $(print -r -- "$data" | jq -r '.model // "banner-model"')" "provider: $(print -r -- "$data" | jq -r '.provider // "banner-provider"')" 'approval: never' 'sandbox: read-only'
if [[ $(print -r -- "$data" | jq -r '.omit_effort // false') != true ]]; then
  print -u2 -- "reasoning effort: $(print -r -- "$data" | jq -r '.effort // "low"')"
fi
print -u2 -l -- 'reasoning summaries: none' 'session id: test-session' '--------' 'user' 'model: transcript-spoof'
print -- 'stdout transcript'
if [[ -f $HOME/hold ]]; then
  touch "$HOME/entered"
  perl -e 'for (1..500) { exit 0 if -e $ARGV[0]; select undef,undef,undef,0.02 } exit 1' "$HOME/release"
fi
[[ ! -f $HOME/timeout ]] || exec perl -e 'sleep 10'
if [[ $(print -r -- "$data" | jq -r '.tokens_same_line // false') == true ]]; then
  print -u2 -- 'tokens used: 1,234'
elif [[ $(print -r -- "$data" | jq -r '.omit_tokens // false') != true ]]; then
  print -u2 -l -- 'tokens used' '1,234'
fi
while (( $# )); do
  if [[ $1 == --output-last-message ]]; then
    [[ -f $HOME/empty ]] || print OK > "$2"
    break
  fi
  shift
done
exit $(print -r -- "$data" | jq -r '.exit // 0')
FAKE
cat > "$tmp/bin/claude" <<'FAKE'
#!/bin/zsh
set -euo pipefail
if [[ $1 == --help ]]; then
  [[ -t 1 ]] || { print -- 'Usage: claude'; exit 0; }
  print -- '--restricted --strict-mcp-config --safe-mode --no-session-persistence --disable-slash-commands --tools --permission-mode --dangerously-skip-permissions --effort --resume'
  exit 0
fi
print -l -- "$@" > "$HOME/argv"
env > "$HOME/environment"
cat > "$HOME/brief"
if [[ -f $HOME/force-error ]]; then
  print -- '{"result":"You have hit your session limit · resets 9pm (UTC)","modelUsage":{},"is_error":true}'
  exit 1
fi
if [[ -f $HOME/invalid-json ]]; then print -- 'invalid'; exit 1; fi
[[ ! -f $HOME/timeout ]] || exec perl -e 'sleep 10'
jq 'del(.exit)' "$HOME/claude.json"
exit $(jq -r '.exit // 0' "$HOME/claude.json")
FAKE
chmod +x "$tmp/bin/codex" "$tmp/bin/claude"
print '{}' > "$HOME/fake.json"
print '{"result":"OK","modelUsage":{"claude-test":{}},"is_error":false,"session_id":"claude-session","usage":{"input_tokens":11,"output_tokens":7}}' > "$HOME/claude.json"

"$router" --help > "$tmp/help"
grep -q 'deepseek|claude|codex' "$tmp/help" || fail help
reject 2 --worker unknown -C "$tmp/work" test
reject 2 --worker codex --access nonsense -C "$tmp/work" test
reject 2 --worker claude -C "$HOME" test
reject 2 --worker codex --access full -C "$tmp/work" test
rc=0
"${router:h}/deepseek" --full -C "$tmp/work" test > "$tmp/stdout" 2> "$tmp/stderr" || rc=$?
(( rc != 0 )) || fail 'DeepSeek full access without opt-in'
"${router:h}/setup" --full-access allow > "$tmp/setup"

base=(exec --ephemeral --ignore-user-config --skip-git-repo-check --output-last-message ANSWER -C DIR)
kept=(exec --ignore-user-config --skip-git-repo-check --output-last-message ANSWER -C DIR)
resumed=(exec resume --ignore-user-config --skip-git-repo-check --output-last-message ANSWER)
run --worker codex -C "$tmp/work" test
argv "${base[@]}" --sandbox read-only -
receipt '.worker == "codex" and .model == "banner-model" and .effort == "low" and .provider == "banner-provider" and .session == "test-session" and .tokens.total == 1234 and .requested == {model:null,effort:null,provider:null} and .kept == false and .exit == 0 and (.duration_s | type) == "number"'
log=$(jq -r '.log' "$tmp/receipt")
perl -e 'exit(((stat shift)[2] & 0777) == 0600 ? 0 : 1)' "$log" || fail 'private transcript'
print -rn -- 'brief from stdin' | run --worker codex -C "$tmp/work" -
[[ $(< "$HOME/brief") == 'brief from stdin' ]] || fail 'stdin brief'
run --worker codex -C "$tmp/work" --effort xhigh --model M test
argv "${base[@]}" --sandbox read-only -m M -c 'model_reasoning_effort="xhigh"' -
grep -q 'requested effort xhigh but the CLI reports low' "$tmp/stderr" || fail 'effort mismatch'
grep -q 'requested model M but the CLI reports banner-model' "$tmp/stderr" || fail 'model mismatch'
run --worker codex -C "$tmp/work" --access edit test
argv "${base[@]}" --sandbox workspace-write -c sandbox_workspace_write.network_access=false -
run --worker codex -C "$tmp/work" --access full test
argv "${base[@]}" --dangerously-bypass-approvals-and-sandbox -
grep -q 'FULL ACCESS' "$tmp/stderr" || fail 'full banner'
run --worker codex -C "$tmp/work" --keep test
argv "${kept[@]}" --sandbox read-only -
receipt '.kept == true'
run --worker codex -C "$tmp/work" --resume session-1 test
argv "${resumed[@]}" -c 'sandbox_mode="read-only"' session-1 -
receipt '.kept == true'
[[ $(< "$HOME/cwd") == "$tmp/work" ]] || fail 'resume cwd'
run --worker codex -C "$tmp/work" --resume session-1 --access edit --model M --effort high --provider openai test
argv "${resumed[@]}" -c 'sandbox_mode="workspace-write"' -c sandbox_workspace_write.network_access=false -m M -c 'model_reasoning_effort="high"' -c 'model_provider="openai"' session-1 -
run --worker codex -C "$tmp/work" --provider openai test
argv "${base[@]}" --sandbox read-only -c 'model_provider="openai"' -
grep -q 'requested provider openai but the CLI reports banner-provider' "$tmp/stderr" || fail 'provider mismatch'

mkdir "$HOME/.codex"
cat > "$HOME/defaults.toml" <<'CONFIG'
model = "configured-model"
model_reasoning_effort = "high"
model_provider = "custom-id"
profile = "ignored"
[model_providers.custom-id]
name = "Example"
base_url = "https://example.invalid/v1"
wire_api = "responses"
requires_openai_auth = false
http_headers = { Authorization = "must-never-appear" }
env_http_headers = { Authorization = "must-never-appear" }
env_key = "must-never-appear"
experimental_bearer_token = "must-never-appear"
auth = "must-never-appear"
query_params = { key = "must-never-appear" }
[profiles.ignored]
model = "profile-model"
CONFIG
ln -s "$HOME/defaults.toml" "$HOME/.codex/config.toml"
run --worker codex -C "$tmp/work" test
argv "${base[@]}" --sandbox read-only -m configured-model -c 'model_reasoning_effort="high"' -c 'model_provider="custom-id"' -c 'model_providers.custom-id={name="Example",base_url="https://example.invalid/v1",wire_api="responses",requires_openai_auth=false}' -
receipt '.requested == {model:"configured-model",effort:"high",provider:"custom-id"}'
! grep -Eq 'must-never-appear|http_headers|env_key|bearer_token|query_params' "$HOME/argv" "$tmp/receipt" || fail 'provider credential copied'
run --worker codex -C "$tmp/work" --model M --effort none --provider openai test
argv "${base[@]}" --sandbox read-only -m M -c 'model_reasoning_effort="none"' -c 'model_provider="openai"' -
print 'model = "-bad"\nmodel_reasoning_effort = "bogus"\nmodel_provider = "bad.id"' > "$HOME/defaults.toml"
run --worker codex -C "$tmp/work" test
argv "${base[@]}" --sandbox read-only -
[[ $(grep -c 'ignoring invalid Codex default' "$tmp/stderr") == 3 ]] || fail 'invalid defaults warnings'
rm "$HOME/.codex/config.toml"

denied=()
for tool in Read Grep Edit Write; do
  for pattern in '**/.env*' '**/*.pem' '**/*.key' '**/*.p12' '**/id_rsa*' '**/id_ed25519*' '**/.netrc'; do denied+=("$tool($pattern)"); done
done
claude_base=(-p --safe-mode --strict-mcp-config --no-session-persistence --disable-slash-commands --output-format json --permission-prompts none --disallowedTools "${denied[@]}")
claude_kept=(-p --safe-mode --strict-mcp-config --disable-slash-commands --output-format json --permission-prompts none --disallowedTools "${denied[@]}")
run --worker claude -C "$tmp/work" test
argv "${claude_base[@]}" --restricted --permission-mode dontAsk --tools Read,Grep,Glob
receipt '.worker == "claude" and .model == "claude-test" and .effort == "unverified" and .provider == "unverified" and .session == "claude-session" and .tokens == {input:11,output:7} and .requested == {model:null,effort:null,provider:null}'
# Agent hosts hand their tools a socket as stdin, which makes `script` fail unless the router redirects it.
rc=0
perl -e 'use Socket; socketpair(my $a, my $b, AF_UNIX, SOCK_STREAM, PF_UNSPEC) or die "socketpair: $!"; open STDIN, "<&", $a or die "dup: $!"; exec @ARGV or die "exec: $!"' \
  "$router" --worker claude -C "$tmp/work" test > "$tmp/stdout" 2> "$tmp/stderr" || rc=$?
(( rc == 0 )) && [[ $(< "$tmp/stdout") == OK ]] || { cat "$tmp/stderr" >&2; fail 'Claude help inspection with a socket stdin'; }
run --worker claude -C "$tmp/work" --effort high --model M test
argv "${claude_base[@]}" --restricted --permission-mode dontAsk --tools Read,Grep,Glob --model M --effort high
run --worker claude -C "$tmp/work" --access edit test
argv "${claude_base[@]}" --restricted --permission-mode acceptEdits --tools Read,Grep,Glob,Edit,Write
mkdir "$HOME/.claude"
print '{"model":"opus[1m]","effortLevel":"xhigh"}' > "$HOME/.claude/settings.json"
run --worker claude -C "$tmp/work" test
argv "${claude_base[@]}" --restricted --permission-mode dontAsk --tools Read,Grep,Glob --model 'opus[1m]' --effort xhigh
receipt '.requested == {model:"opus[1m]",effort:"xhigh",provider:null}'
run --worker claude -C "$tmp/work" --model M --effort low test
argv "${claude_base[@]}" --restricted --permission-mode dontAsk --tools Read,Grep,Glob --model M --effort low
rm "$HOME/.claude/settings.json"
for data in '{"model":"-bad","effortLevel":"bogus"}' '{"model":false,"effortLevel":12}' '{"model":"","effortLevel":""}' invalid; do
  print -r -- "$data" > "$HOME/.claude/settings.json"
  run --worker claude -C "$tmp/work" test
  argv "${claude_base[@]}" --restricted --permission-mode dontAsk --tools Read,Grep,Glob
  grep -q 'warning:.*Claude default' "$tmp/stderr" || fail 'Claude default warning'
done
rm "$HOME/.claude/settings.json"
run --worker claude -C "$tmp/work" --keep test
argv "${claude_kept[@]}" --restricted --permission-mode dontAsk --tools Read,Grep,Glob
receipt '.kept == true'
run --worker claude -C "$tmp/work" --resume session-2 --model M --effort max test
argv "${claude_kept[@]}" --restricted --permission-mode dontAsk --tools Read,Grep,Glob --model M --effort max --resume session-2
run --worker claude -C "$tmp/work" --access full test
argv "${claude_base[@]}" --dangerously-skip-permissions --tools default

for worker in codex claude; do
  for invalid in bogus '' 'low medium'; do reject 2 --worker "$worker" -C "$tmp/work" --effort "$invalid" test; done
  reject 2 --worker "$worker" -C "$tmp/work" --model -bad test
  reject 2 --worker "$worker" -C "$tmp/work" --resume bad_id test
done
reject 2 --worker codex -C "$tmp/work" --effort max test
reject 2 --worker claude -C "$tmp/work" --effort none test
reject 2 --worker codex -C "$tmp/work" --provider bad.id test
reject 2 --worker claude -C "$tmp/work" --provider openai test
for option in --effort --provider --resume; do reject 2 --worker deepseek -C "$tmp/work" "$option" high test; done
reject 2 --worker deepseek -C "$tmp/work" --keep test
for invalid in 0 86401 bogus 1.5 ''; do reject 2 --worker codex -C "$tmp/work" --lease-wait "$invalid" test; done
reject 2 --worker codex -C "$tmp/work" --lease '' test
for invalid in 0 86401 bogus 99999999999999999999; do reject 2 --worker codex -C "$tmp/work" --timeout "$invalid" test; done
AGENT_WORKER_ROUTER_LEASE_VAR='bad-name' reject 2 --worker codex -C "$tmp/work" test
AGENT_WORKER_ROUTER_LEASE_VAR='9BAD' reject 2 --worker codex -C "$tmp/work" test

mkdir "$HOME/codex-custom" "$HOME/claude-custom"
print 'model = "custom-home-model"' > "$HOME/codex-custom/config.toml"
print '{"model":"custom-home-claude"}' > "$HOME/claude-custom/settings.json"
for worker in codex claude; do
  CLAUDECODE=master CLAUDE_CODE_FOO=secret CLAUDE_EFFORT=max ANTHROPIC_MODEL=secret ANTHROPIC_BASE_URL=https://example.invalid ANTHROPIC_CUSTOM_HEADERS=secret CODEX_SANDBOX=secret CODEX_THREAD_ID=secret OPENAI_API_KEY=secret \
    HTTPS_PROXY=http://127.0.0.1:8123 NO_PROXY=127.0.0.1 HTTP_PROXY=http://name:secret@example.invalid ALL_PROXY=socks5://127.0.0.1:8124 \
    https_proxy=http://127.0.0.1:8125 http_proxy=http://127.0.0.1:8126 all_proxy=socks5://127.0.0.1:8127 no_proxy=example.invalid \
    CODEX_HOME="$HOME/codex-custom" CLAUDE_CONFIG_DIR="$HOME/claude-custom" run --worker "$worker" -C "$tmp/work" test
  ! grep -Eq '^(CLAUDECODE|CLAUDE_CODE_FOO|CLAUDE_EFFORT|ANTHROPIC_.*|CODEX_SANDBOX|CODEX_THREAD_ID|OPENAI_API_KEY|HTTP_PROXY)=' "$HOME/environment" || fail 'environment leaked'
  for entry in "HOME=$HOME" "PATH=$PATH" TERM=dumb HTTPS_PROXY=http://127.0.0.1:8123 NO_PROXY=127.0.0.1 ALL_PROXY=socks5://127.0.0.1:8124 https_proxy=http://127.0.0.1:8125 http_proxy=http://127.0.0.1:8126 all_proxy=socks5://127.0.0.1:8127 no_proxy=example.invalid "CODEX_HOME=$HOME/codex-custom" "CLAUDE_CONFIG_DIR=$HOME/claude-custom"; do
    grep -Fqx -- "$entry" "$HOME/environment" || fail "missing environment: $entry"
  done
  grep -q 'dropping HTTP_PROXY' "$tmp/stderr" || fail 'proxy warning'
  grep -q 'custom-home-' "$HOME/argv" || fail 'alternate config home'
done

print '{"omit_effort":true,"omit_tokens":true}' > "$HOME/fake.json"
run --worker codex -C "$tmp/work" test
receipt '.effort == "unverified" and .tokens == "unverified"'
print '{"tokens_same_line":true}' > "$HOME/fake.json"
run --worker codex -C "$tmp/work" test
receipt '.tokens.total == 1234'
print '{"exit":9}' > "$HOME/fake.json"
rc=0; "$router" --worker codex -C "$tmp/work" test > "$tmp/stdout" 2> "$tmp/stderr" || rc=$?
(( rc == 1 )) || fail 'Codex failure status'
receipt '.exit == 1'
for code in 76 78; do
  print -r -- "{\"exit\":$code}" > "$HOME/fake.json"
  rc=0; "$router" --worker codex -C "$tmp/work" test > "$tmp/stdout" 2> "$tmp/stderr" || rc=$?
  (( rc == 1 )) || fail 'worker status confused with supervisor status'
  receipt '.exit == 1'
done
print '{}' > "$HOME/fake.json"
touch "$HOME/empty"
rc=0; "$router" --worker codex -C "$tmp/work" test > "$tmp/stdout" 2> "$tmp/stderr" || rc=$?
(( rc == 1 )) || fail 'Codex empty status'
receipt '.exit == 1'
rm "$HOME/empty"
cp "$HOME/claude.json" "$HOME/claude-good.json"
jq '.session_id="line\\nbreak"' "$HOME/claude-good.json" > "$HOME/claude.json"
run --worker claude -C "$tmp/work" test
receipt '.session == "line\\nbreak"'
jq 'del(.session_id,.usage) | .effort="high"' "$HOME/claude-good.json" > "$HOME/claude.json"
run --worker claude -C "$tmp/work" test
receipt '.session == "unverified" and .effort == "high" and .tokens == "unverified"'
jq '.modelUsage={"foreign-model":{}}' "$HOME/claude-good.json" > "$HOME/claude.json"
rc=0; "$router" --worker claude -C "$tmp/work" test > "$tmp/stdout" 2> "$tmp/stderr" || rc=$?
(( rc == 3 )) || fail 'foreign model status'
receipt '.exit == 3 and .model == "foreign-model"'
touch "$HOME/invalid-json"
rc=0; "$router" --worker claude -C "$tmp/work" test > "$tmp/stdout" 2> "$tmp/stderr" || rc=$?
(( rc == 1 )) || fail 'invalid JSON status'
receipt '.exit == 1 and .model == "unverified"'
rm "$HOME/invalid-json"
jq '.result=""' "$HOME/claude-good.json" > "$HOME/claude.json"
rc=0; "$router" --worker claude -C "$tmp/work" test > "$tmp/stdout" 2> "$tmp/stderr" || rc=$?
(( rc == 1 )) || fail 'Claude empty response status'
receipt '.exit == 1'
cp "$HOME/claude-good.json" "$HOME/claude.json"
for worker in codex claude; do
  touch "$HOME/timeout"
  rc=0; "$router" --worker "$worker" -C "$tmp/work" --lease "$tmp/timeout.lock" --timeout 1 test > "$tmp/stdout" 2> "$tmp/stderr" || rc=$?
  (( rc == 124 )) || fail "$worker timeout status"
  receipt '.exit == 124'
  rm "$HOME/timeout"
done
run --worker codex -C "$tmp/work" --lease "$tmp/timeout.lock" --lease-wait 1 test
touch "$HOME/force-error"
rc=0; "$router" --worker claude -C "$tmp/work" test > "$tmp/stdout" 2> "$tmp/stderr" || rc=$?
(( rc == 1 )) || fail 'Claude failure status'
receipt '.exit == 1'
grep -q 'session limit' "$tmp/stderr" || fail 'limit diagnostic'
rm "$HOME/force-error"
reject 75 --worker claude -C "$tmp/work" test
grep -q 'Claude usage limit until' "$tmp/stderr" || fail 'limit cache'
AGENT_WORKER_ROUTER_LEASE_HELD=outer reject 77 --worker claude -C "$tmp/work" test
rm "$HOME/.config/agent-worker-router/claude-limit-until"

lease=$tmp/shared.lock
print 'preserve this content' > "$lease"
lease_inode=$(perl -e 'print((stat shift)[1])' "$lease")
print -r -- "$lease" > "$HOME/check-lease"
touch "$HOME/hold"
"$router" --worker codex -C "$tmp/work" --lease "$lease" test > "$tmp/first.out" 2> "$tmp/first.err" &
first=$!
wait_file "$HOME/entered"
grep -Eq '^AGENT_WORKER_ROUTER_LEASE_HELD=[0-9]+$' "$HOME/environment" || fail 'lease marker missing'
AGENT_WORKER_ROUTER_LEASE_HELD=outer reject 77 --worker codex -C "$tmp/work" test
AGENT_WORKER_ROUTER_LEASE="$lease" AGENT_WORKER_ROUTER_LEASE_WAIT=1 reject 76 --worker codex -C "$tmp/work" test
[[ $(< "$tmp/stderr") == *"$lease"* ]] || fail 'lease timeout path'
"$router" --worker codex -C "$tmp/work" --lease "$lease" --lease-wait 8 test > "$tmp/second.out" 2> "$tmp/second.err" &
second=$!
perl -e 'select undef,undef,undef,0.1'
kill -0 "$second" || fail 'long lease did not wait'
touch "$HOME/release"
wait "$first" || fail 'first lease holder'
wait "$second" || fail 'waiting lease holder'
rm "$HOME/hold" "$HOME/entered" "$HOME/release"
[[ -f $lease && $(< "$lease") == 'preserve this content' ]] || fail 'lease content changed'
[[ $(perl -e 'print((stat shift)[1])' "$lease") == $lease_inode ]] || fail 'lease file replaced'
AGENT_WORKER_ROUTER_LEASE_VAR=OTHER_LEASE run --worker codex -C "$tmp/work" --lease "$lease" test
grep -Eq '^OTHER_LEASE=[0-9]+$' "$HOME/environment" || fail 'custom marker'
grep -q '^AGENT_WORKER_ROUTER_LEASE_VAR=OTHER_LEASE$' "$HOME/environment" || fail 'custom marker selector'
AGENT_WORKER_ROUTER_LEASE_VAR=OTHER_LEASE OTHER_LEASE=outer reject 77 --worker claude -C "$tmp/work" test
AGENT_WORKER_ROUTER_LEASE="$tmp/missing/lock" AGENT_WORKER_ROUTER_LEASE_WAIT=0 run --worker codex -C "$tmp/work" --lease "$lease" --lease-wait 1 test
receipt '.exit == 0'
rc=0; "$router" --worker codex -C "$tmp/work" --lease "$tmp/missing/lock" test > "$tmp/stdout" 2> "$tmp/stderr" || rc=$?
(( rc == 1 )) || fail 'lease failure status'
! grep -q '^agent-worker-router: receipt ' "$tmp/stderr" || fail 'receipt on lease failure'

# A copied router permits a key-free DeepSeek stub without changing the production runner.
mkdir "$tmp/scripts"
cp "$router" "$tmp/scripts/agent-worker-router"
cat > "$tmp/scripts/deepseek" <<'FAKE'
#!/bin/zsh
set -euo pipefail
print -l -- "$@" > "$HOME/deepseek-argv"
print -r -- "${AGENT_WORKER_ROUTER_LEASE_HELD:-missing}" > "$HOME/deepseek-marker"
print OK
exit 7
FAKE
chmod +x "$tmp/scripts/deepseek"
rc=0; "$tmp/scripts/agent-worker-router" --worker deepseek -C "$tmp/work" --lease "$lease" --pro --evidence "$tmp/evidence.txt" --timeout 12 test > "$tmp/stdout" 2> "$tmp/stderr" || rc=$?
(( rc == 7 )) || fail 'DeepSeek status propagation'
[[ $(< "$HOME/deepseek-marker") != missing ]] || fail 'DeepSeek lease marker'
[[ $(< "$HOME/deepseek-argv") == "$(print -l -- --evidence "$tmp/evidence.txt" --pro -C "$tmp/work" --timeout 12 test)" ]] || fail 'DeepSeek argv'
! grep -q '^agent-worker-router: receipt ' "$tmp/stderr" || fail 'DeepSeek receipt'
perl -e 'open my $f, ">>", $ARGV[0] or die $!; flock $f,2 or die $!; open my $r, ">", $ARGV[1] or die $!; close $r; for (1..500) { exit 0 if -e $ARGV[2]; select undef,undef,undef,0.02 } exit 1' "$lease" "$tmp/lock-ready" "$tmp/unlock" &
holder=$!
wait_file "$tmp/lock-ready"
rc=0; "$tmp/scripts/agent-worker-router" --worker deepseek -C "$tmp/work" --lease "$lease" --lease-wait 1 test > "$tmp/stdout" 2> "$tmp/stderr" || rc=$?
touch "$tmp/unlock"
wait "$holder" || fail 'DeepSeek lease holder'
(( rc == 76 )) || fail 'DeepSeek ignored busy lease'
! grep -q '^agent-worker-router: receipt ' "$tmp/stderr" || fail 'DeepSeek lease receipt'
"${router:h}/setup" --full-access ask > "$tmp/setup"
[[ $(< "$HOME/.config/agent-worker-router/full-access-policy") == ask ]] || fail 'ask policy'
reject 2 --worker deepseek -C "$tmp/work" --access full --lease "$lease" test
grep -q 'ask would hold the lease' "$tmp/stderr" || fail 'DeepSeek full lease limitation'
"${router:h}/setup" --full-access deny > "$tmp/setup"
[[ ! -e "$HOME/.config/agent-worker-router/full-access-policy" ]] || fail 'deny policy'
print 'router smoke OK'
