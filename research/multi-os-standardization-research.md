# Multi-OS Standardization Research
**macOS ↔ Ubuntu Linux (DigitalOcean) | 2026-04-07 UTC**

---

## Executive Summary

Four high-priority fixes solve the majority of cross-platform problems:

1. **Fix provision.sh to run Claude Code setup as the `claude` user** (via `sudo -Hu claude`) — this is why hooks silently don't fire on the droplet.
2. **Use `CLAUDE_ENV_FILE` via a `SessionStart` hook** to inject PATH into all Bash tool calls — the canonical cross-platform env-var injection mechanism.
3. **Migrate Python skills to `uv` inline script format (PEP 723)** — eliminates venv provisioning, the `pip install` failure, and `python3-venv` apt dependency entirely.
4. **Separate `settings.macos.json` and `settings.linux.json`** — the current `osascript` notification hooks fail silently on Ubuntu.

---

## Problem 1: Python Shebang and Venv Portability

### Current Hooks (Already Correct)

`capture_tool_use.py`, `capture_subagent.py`, `analyze_session.py` already use `#!/usr/bin/env python3` and only use stdlib modules. No changes needed for hooks.

### Current Skills (Need Fix)

`model_client.py` and `review_debate.py` need `litellm`. On macOS, bare `pip install` fails with PEP 668 "externally-managed-environment". On Ubuntu, you need the `python3-venv` apt package before creating a venv.

### Recommended Fix: `uv` with PEP 723 Inline Dependencies

`uv` is the modern cross-platform Python package manager (Rust binary, installs identically everywhere):

```bash
# Same install command on macOS and Ubuntu:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Installs to ~/.local/bin/uv
```

Migrate skills to this format — they become self-installing:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["litellm>=1.0", "openai>=1.0", "anthropic>=0.30"]
# ///
"""model_client.py — now self-installing, cross-platform"""
import litellm
# ... rest unchanged
```

When invoked, `uv` auto-creates a cached isolated env, installs deps, executes. No manual `pip install`, no venv activation, no `python3-venv` apt dependency needed. Works identically on Mac and Ubuntu.

---

## Problem 2: Shell Profile Loading for Non-Interactive Shells

### Why Env Vars Don't Reach Hooks

Claude Code's Bash tool runs in a **non-interactive, non-login shell**. Ubuntu's default `~/.bashrc` has an early-exit guard:

```bash
case $- in *i*) ;; *) return ;; esac
```

This causes the shell to return before reaching any PATH or env var additions you've put below it. Your `ANTHROPIC_API_KEY` export in `~/.bashrc` never runs.

### Canonical Fix: `CLAUDE_ENV_FILE` via `SessionStart` Hook

Claude Code provides `CLAUDE_ENV_FILE` — write `export KEY=value` lines to this file and they're applied to all subsequent Bash tool calls in the session. Add to `settings.json` SessionStart hooks:

```json
{
  "type": "command",
  "command": "~/.claude/hooks/inject_env.sh"
}
```

Create `~/.claude/hooks/inject_env.sh`:

```bash
#!/usr/bin/env bash
# Inject platform-appropriate env vars into Claude's Bash tool environment

# Guard: CLAUDE_ENV_FILE may be empty in some versions
[ -z "$CLAUDE_ENV_FILE" ] && exit 0

PLATFORM="$(uname -s)"

# Always inject
echo "export PATH=\"$HOME/.local/bin:$HOME/.venvs/litellm/bin:/usr/local/bin:$PATH\"" \
    >> "$CLAUDE_ENV_FILE"

# Env vars — load from a secret file if it exists (see secrets strategy)
if [ -f "$HOME/.claude/env" ]; then
    cat "$HOME/.claude/env" >> "$CLAUDE_ENV_FILE"
fi

# macOS-specific PATH additions
if [ "$PLATFORM" = "Darwin" ]; then
    BREW_PREFIX="$(brew --prefix 2>/dev/null || echo /opt/homebrew)"
    echo "export PATH=\"$BREW_PREFIX/bin:$PATH\"" >> "$CLAUDE_ENV_FILE"
fi

exit 0
```

### Quick Fix: Move PATH Additions Above the Interactive Guard

On Ubuntu, put critical PATH/env exports **before** the guard in `~/.bashrc`:

```bash
# ~/.bashrc — BEFORE the interactive guard:
export PATH="$HOME/.local/bin:$HOME/.venvs/litellm/bin:$PATH"
# (Add env var exports here for non-interactive shell access)

# Then the Ubuntu default guard (don't move this):
case $- in
    *i*) ;;
      *) return;;
esac
```

---

## Problem 3: Claude Code Running as Wrong User on Servers

### Root Cause

provision.sh runs as root and installs hooks/settings to `/home/claude/.claude/`. But if `claude` CLI is launched as root (which happens during initial setup), it reads `/root/.claude/` — which doesn't exist. **Hooks silently never fire.** No error.

### Primary Fix: Run Claude Code Setup as the `claude` User

All Claude Code setup in provision.sh must use `sudo -Hu claude` or `su - claude`:

```bash
# In provision.sh — all Claude Code setup:
sudo -Hu claude bash << 'CLAUDE_SETUP'
set -euo pipefail

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Set up litellm venv (legacy approach — or use uv per-script instead)
python3 -m venv ~/.venvs/litellm
~/.venvs/litellm/bin/pip install --upgrade pip litellm

# Set up directory structure
mkdir -p ~/.claude/hooks ~/.claude/learning/captures ~/.claude/learning/learnings
mkdir -p ~/.claude/skills ~/projects

# Install hooks (from golden repo baked into the image)
cp /opt/claude-golden/hooks/*.py ~/.claude/hooks/
cp /opt/claude-golden/hooks/*.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/*.sh

# Install settings (linux variant)
cp /opt/claude-golden/settings.linux.json ~/.claude/settings.json

# PATH additions BEFORE the bashrc interactive guard
if ! grep -q "# claude-code-path" ~/.bashrc; then
    sed -i '1i# claude-code-path\nexport PATH="$HOME/.local/bin:$HOME/.venvs/litellm/bin:$PATH"\n' ~/.bashrc
fi
CLAUDE_SETUP
```

### Secondary Fix (Stopgap): Symlink Root's .claude to Claude User's

```bash
# Temporary until provision.sh is updated:
ln -sfn /home/claude/.claude /root/.claude
ln -sfn /home/claude/.bashrc /root/.bash_aliases
```

Note: files written by root will be root-owned and may not be readable by the `claude` user. Not a permanent solution.

---

## Problem 4: Platform-Specific settings.json

Create two settings files — install the right one during provisioning:

`settings.linux.json` — removes macOS-only `osascript` calls, adjusts any Mac-specific paths:

```json
{
  "permissions": { "allow": [ "..." ] },
  "hooks": {
    "SessionStart": [
      { "matcher": "", "hooks": [
        { "type": "command", "command": "CLAUDE_HOOK_EVENT=session_start python3 ~/.claude/hooks/capture_session.py" },
        { "type": "command", "command": "~/.claude/hooks/inject_env.sh" }
      ]}
    ],
    "PostToolUse": [
      { "matcher": "", "hooks": [
        { "type": "command", "command": "python3 ~/.claude/hooks/capture_tool_use.py" }
      ]}
    ],
    "Stop": [
      { "matcher": "", "hooks": [
        { "type": "command", "command": "CLAUDE_HOOK_EVENT=session_stop python3 ~/.claude/hooks/capture_session.py" },
        { "type": "command", "command": "python3 ~/.claude/hooks/analyze_session.py" },
        { "type": "command", "command": "bash ~/.claude/hooks/specstory_sync.sh" }
      ]}
    ]
  }
}
```

Install logic in provision.sh:

```bash
if [ "$(uname -s)" = "Darwin" ]; then
    cp settings.macos.json ~/.claude/settings.json
else
    cp settings.linux.json ~/.claude/settings.json
fi
```

---

## Problem 5: Cross-Platform Package Management

### Decision: Conditional Scripting (Not Homebrew on Linux)

Homebrew on Linux is valid but adds 500MB+ overhead and is slower than apt for server provisioning. Use conditional scripting:

```bash
#!/usr/bin/env bash
OS="$(uname -s)"

install_package() {
    local apt_name="$1"
    local brew_name="${2:-$1}"
    
    if [ "$OS" = "Darwin" ]; then
        brew install "$brew_name" 2>/dev/null || true
    elif [ "$OS" = "Linux" ]; then
        apt-get install -y -qq "$apt_name"
    fi
}

install_package jq jq
install_package python3 python3
install_package nodejs node
# python3-venv only needed on Linux (macOS has venv built-in or use uv)
[ "$OS" = "Linux" ] && apt-get install -y python3-venv
```

### `uv` as the Cross-Platform Python Solution

| Approach | macOS | Ubuntu | Complexity |
|----------|-------|--------|------------|
| system pip | Fails (PEP 668) | Works | Low |
| venv + pip | Works | Needs python3-venv | Medium |
| conda | Works | Works | High (heavy) |
| **uv** | **Works** | **Works** | **Low** |

One install command, works everywhere, handles venv internally.

---

## Problem 6: Dotfiles Management for Servers

### Recommended: `chezmoi`

Designed explicitly for "manage dotfiles across multiple machines with platform differences":

```bash
# In provision.sh, run as claude user:
curl -fsSL https://get.chezmoi.io | bash
~/.local/bin/chezmoi init --apply https://github.com/your-org/dotfiles.git
```

Single command: clones dotfiles repo, applies all configs, runs `run_once_` install scripts.

Example platform-conditional settings.json template (`~/.local/share/chezmoi/dot_claude/settings.json.tmpl`):

```
{{- if eq .chezmoi.os "darwin" }}
{
  "hooks": {
    "Stop": [{ "type": "command", "command": "osascript -e 'display notification \"Session ended\"'" }]
  }
}
{{- else }}
{
  "hooks": {
    "Stop": [{ "type": "command", "command": "python3 ~/.claude/hooks/analyze_session.py" }]
  }
}
{{- end }}
```

Example `run_once_install-packages.sh.tmpl`:
```bash
#!/bin/bash
{{ if eq .chezmoi.os "darwin" -}}
brew install jq uv gh
{{ else if eq .chezmoi.os "linux" -}}
apt-get install -y jq python3 gh
curl -LsSf https://astral.sh/uv/install.sh | sh
{{ end -}}
```

---

## Problem 7: Testing That Hooks Work

### Pipe Test (Official Approach)

```bash
# Test capture_tool_use.py
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"session_id":"test-123","agent_id":null}' \
    | python3 ~/.claude/hooks/capture_tool_use.py
echo "Exit: $?"
tail -1 ~/.claude/learning/captures/tool_events.jsonl | python3 -m json.tool

# Simulate Claude Code's exact invocation context (non-interactive, no-profile):
bash --norc --noprofile -c '
    echo "{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"ls\"},\"session_id\":\"test\"}" \
        | python3 ~/.claude/hooks/capture_tool_use.py
    echo "Exit: $?"
'
```

### Critical Gotcha: Echo in Shell Profile

If `~/.zshrc` or `~/.bashrc` has an unconditional `echo`, Claude Code's JSON parsing breaks:

```bash
echo "Welcome to zsh"  # BAD — this gets prepended to hook JSON output
```

Fix:
```bash
if [[ $- == *i* ]]; then
    echo "Welcome to zsh"  # Only in interactive shells
fi
```

### GitHub Actions CI (Cross-Platform Validation)

```yaml
name: Test Hooks Cross-Platform
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - name: Test hooks
        run: |
          mkdir -p /tmp/test-home/.claude/learning/captures
          HOME=/tmp/test-home python3 hooks/capture_tool_use.py \
              <<< '{"tool_name":"Bash","tool_input":{"command":"ls"},"session_id":"ci"}'
          echo "Hook exit: $?"
```

---

## Recommended Repository Structure

```
claude-golden/                     ← git repo (baked into golden image)
├── Makefile                       ← setup-macos / setup-linux / test-hooks
├── provision.sh                   ← Ubuntu droplet provisioning (root)
├── hooks/
│   ├── capture_tool_use.py        ← stdlib only, no changes needed
│   ├── capture_subagent.py        ← stdlib only, no changes needed
│   ├── capture_session.py         ← stdlib only, no changes needed
│   ├── analyze_session.py         ← stdlib only, no changes needed
│   ├── inject_env.sh              ← NEW: CLAUDE_ENV_FILE injection
│   └── specstory_sync.sh          ← already has PATH guard ✓
├── settings.macos.json            ← with osascript notifications
└── settings.linux.json            ← without osascript (headless server)
```

---

## Prioritized Action Plan

### This Week
1. **Update provision.sh** — use `sudo -Hu claude` for all Claude Code setup steps
2. **Create `settings.linux.json`** — remove `osascript`, add `inject_env.sh` to SessionStart
3. **Create `inject_env.sh`** — CLAUDE_ENV_FILE injection + load from `~/.claude/env` secret file
4. **Move PATH exports above bashrc guard** — on both Mac and Ubuntu

### Next Week  
5. **Install `uv`** in provision.sh (as claude user, to `~/.local/bin/`)
6. **Migrate `model_client.py`** and `review_debate.py` to `uv` inline script format
7. **Create `Makefile`** with `setup-macos`, `setup-linux`, `test-hooks` targets

### Month 2
8. **Evaluate chezmoi** for dotfiles management
9. **Add GitHub Actions** workflow for cross-platform hook testing
10. **Add `run_once_` provisioning scripts** to dotfiles repo

---

## Current Droplet Fix (Immediate)

SSH into 134.122.24.60 and run as root:

```bash
# Fix hooks being in wrong directory for root
mkdir -p /root/.claude/hooks
cp /home/claude/.claude/hooks/* /root/.claude/hooks/
chmod +x /root/.claude/hooks/*.py /root/.claude/hooks/*.sh

# Fix root's settings.json to point to correct hooks path
cp /home/claude/.claude/settings.json /root/.claude/settings.json

# Fix env var injection — add PATH above bashrc guard
sed -i '1i# claude-code-env\nexport PATH="$HOME/.local/bin:$HOME/.venvs/litellm/bin:/usr/local/bin:$PATH"\n' \
    /root/.bashrc /home/claude/.bashrc

# Add env file for non-interactive shell secret loading
cat > /home/claude/.claude/env << 'EOF'
export ANTHROPIC_API_KEY="$(grep ANTHROPIC_API_KEY /home/claude/.bashrc | cut -d'"' -f2)"
EOF
```
