#!/bin/zsh
set -euo pipefail

router=${0:A:h:h}/plugins/agent-worker-router/skills/agent-worker-router/scripts/agent-worker-router
tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT
mkdir "$tmp/work"
mkdir "$tmp/home" "$tmp/bin"

"$router" --help | grep -q 'deepseek|claude|codex'
"$router" --worker unknown -C "$tmp/work" test > /dev/null 2>&1 && exit 1
"$router" --worker codex --access nonsense -C "$tmp/work" test > /dev/null 2>&1 && exit 1
"$router" --worker claude -C "$HOME" test > /dev/null 2>&1 && exit 1
HOME="$tmp/home" "$router" --worker codex --access full -C "$tmp/work" test > /dev/null 2>&1 && exit 1
HOME="$tmp/home" "${router:h}/deepseek" --full -C "$tmp/work" test > /dev/null 2>&1 && exit 1

print '#!/bin/zsh' > "$tmp/bin/codex"
print 'if [[ $1 == exec && $2 == --help ]]; then print -- "--sandbox --ephemeral --ignore-user-config --output-last-message --json --dangerously-bypass-approvals-and-sandbox"; exit 0; fi' >> "$tmp/bin/codex"
print 'print -l -- "$@" > "$HOME/observed"' >> "$tmp/bin/codex"
print 'while (( $# )); do if [[ $1 == --output-last-message ]]; then print OK > "$2"; exit 0; fi; shift; done' >> "$tmp/bin/codex"
chmod +x "$tmp/bin/codex"
HOME="$tmp/home" "${router:h}/setup" --full-access allow > /dev/null
HOME="$tmp/home" PATH="$tmp/bin:$PATH" "$router" --worker codex --access full -C "$tmp/work" test | grep -q OK
grep -q '^--dangerously-bypass-approvals-and-sandbox$' "$tmp/home/observed"
! grep -q '^--sandbox$' "$tmp/home/observed"
HOME="$tmp/home" PATH="$tmp/bin:$PATH" "$router" --worker codex --access edit -C "$tmp/work" test | grep -q OK
grep -A1 '^--sandbox$' "$tmp/home/observed" | grep -q workspace-write

print '#!/bin/zsh' > "$tmp/bin/claude"
print 'if [[ $1 == --help ]]; then print -- "--restricted --strict-mcp-config --safe-mode --no-session-persistence --disable-slash-commands --tools --permission-mode --dangerously-skip-permissions"; exit 0; fi' >> "$tmp/bin/claude"
print 'print -l -- "$@" > "$HOME/observed"' >> "$tmp/bin/claude"
print 'print -- '\''{"result":"OK","modelUsage":{"claude-test":{}},"is_error":false}'\''' >> "$tmp/bin/claude"
chmod +x "$tmp/bin/claude"
HOME="$tmp/home" PATH="$tmp/bin:$PATH" "$router" --worker claude --access full -C "$tmp/work" test | grep -q OK
grep -q '^--dangerously-skip-permissions$' "$tmp/home/observed"
! grep -q '^--restricted$' "$tmp/home/observed"
HOME="$tmp/home" "${router:h}/setup" --full-access ask > /dev/null
[[ $(< "$tmp/home/.config/agent-worker-router/full-access-policy") == ask ]]
HOME="$tmp/home" "${router:h}/setup" --full-access deny > /dev/null
[[ ! -e "$tmp/home/.config/agent-worker-router/full-access-policy" ]]
print 'router smoke OK'
