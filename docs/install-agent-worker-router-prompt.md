# Copyable installation prompt

Give this prompt to your local Codex or Claude Code agent on a Mac. Replace no secret in the prompt; keep your own DeepSeek key on your own device.

> Install `agent-worker-router` from the public GitHub repository `principalwater/pretty-agent-skills` for my local Codex and Claude Code, using their native plugin marketplaces. Do not change either app's default model or my Claude Desktop settings. First inspect the repository's README and skill, then install the published plugin (not a working-copy symlink). Find its installed `scripts/setup`. Ask me to copy **my own** DeepSeek API key to the macOS clipboard; do not ask me to paste it into chat, a shell argument, a file, or a repo. Once I confirm the clipboard is ready, run `setup --from-clipboard` locally and then `setup --check` without showing the key. Do not enable full access; keep `read` as the default. Run a live, non-sensitive DeepSeek Flash test in a new empty temporary directory and check the output; optionally run equivalent Claude/Codex tests only if those CLIs and accounts are available. Report the plugin version/source, installed paths, test outcome, and any manual steps in a short message without disclosing any credential. If a command fails, stop and explain the failure; do not switch to an unofficial bridge or alter my default provider.

The installer should use these commands (skip a marketplace-add step only if already present):

```sh
codex plugin marketplace add principalwater/pretty-agent-skills
codex plugin add agent-worker-router@pretty-agent-skills
claude plugin marketplace add principalwater/pretty-agent-skills
claude plugin install agent-worker-router@pretty-agent-skills --scope user
```

On a Mac where the older `deepseek-worker` plugin is already configured, the installer may use `setup --from-keychain pretty-agent-deepseek-worker default` instead of the clipboard flow. Do not remove the old plugin until the new one has passed a live call.
