# provision.sh Improvements — Proposed Changes
**Based on audit of insite-v6-sprint7 setup + multi-OS + secrets research | 2026-04-07 UTC**

---

## Summary of Changes Needed

provision.sh has three structural problems:
1. Hooks and settings installed to `/home/claude/.claude/` but Claude Code often runs as root → hooks never fire
2. No secrets injection mechanism — every droplet requires manual SSH to add secrets
3. No cross-platform handling (provision.sh is Ubuntu-only, but the repo needs Mac support too)

---

## Key Changes

### 1. Run ALL Claude Code Setup as the Claude User

```bash
# BEFORE (wrong — root installs to /root's context):
cp "$GOLDEN_ROOT/config/hooks/"*.py /home/claude/.claude/hooks/
cp "$GOLDEN_ROOT/config/settings.json" /home/claude/.claude/settings.json

# AFTER — all Claude Code setup under sudo -Hu claude:
sudo -Hu claude bash << 'CLAUDE_SETUP'
  mkdir -p ~/.claude/hooks ~/.claude/learning/captures ~/.claude/learning/learnings
  cp /opt/claude-golden/hooks/*.py ~/.claude/hooks/
  cp /opt/claude-golden/hooks/*.sh ~/.claude/hooks/
  chmod +x ~/.claude/hooks/*.py ~/.claude/hooks/*.sh
  cp /opt/claude-golden/settings.linux.json ~/.claude/settings.json
CLAUDE_SETUP
```

### 2. Install Doppler CLI + `.bashrc` Loading Snippet

```bash
# Install Doppler CLI
apt-get update -qq
curl -sLf --retry 3 --tlsv1.2 --proto "=https" \
  'https://packages.doppler.com/public/cli/gpg.DE2A7741A397C129.key' | \
  gpg --dearmor -o /usr/share/keyrings/doppler-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/doppler-archive-keyring.gpg] \
  https://packages.doppler.com/public/cli/deb/debian any-version main" | \
  tee /etc/apt/sources.list.d/doppler-cli.list
apt-get update -qq && apt-get install -y -qq doppler

# Add Doppler loading to both users' .bashrc (ABOVE the interactive guard)
DOPPLER_SNIPPET='# doppler-secrets
if command -v doppler >/dev/null 2>&1 && doppler secrets >/dev/null 2>&1; then
  eval "$(doppler secrets download --no-file --format env 2>/dev/null)"
fi'

# Claude user
sed -i "1a $DOPPLER_SNIPPET" /home/claude/.bashrc

# Root user (needed until Claude Code runs exclusively as claude user)
sed -i "1a $DOPPLER_SNIPPET" /root/.bashrc
```

### 3. Add inject_env.sh Hook and `settings.linux.json`

Create `config/hooks/inject_env.sh` in the golden repo:

```bash
#!/usr/bin/env bash
# Inject secrets and PATH into Claude Code's Bash tool environment.
# Called by SessionStart hook. Writes to CLAUDE_ENV_FILE.

[ -z "$CLAUDE_ENV_FILE" ] && exit 0

# Always inject PATH with venv and uv
echo "export PATH=\"$HOME/.local/bin:$HOME/.venvs/litellm/bin:/usr/local/bin:$PATH\"" \
    >> "$CLAUDE_ENV_FILE"

# Load from Doppler if configured
if command -v doppler >/dev/null 2>&1 && doppler secrets >/dev/null 2>&1; then
    doppler secrets download --no-file --format env >> "$CLAUDE_ENV_FILE" 2>/dev/null
# Fallback: load from encrypted secrets file (if using age/Spaces approach)
elif [ -f /etc/app-secrets.env ]; then
    cat /etc/app-secrets.env >> "$CLAUDE_ENV_FILE"
fi

exit 0
```

Create `config/settings.linux.json` (reference for what changes vs Mac):

```json
{
  "permissions": { "allow": ["..."] },
  "hooks": {
    "SessionStart": [
      { "matcher": "", "hooks": [
        { "type": "command", "command": "CLAUDE_HOOK_EVENT=session_start python3 ~/.claude/hooks/capture_session.py" },
        { "type": "command", "command": "bash ~/.claude/hooks/inject_env.sh" }
      ]}
    ],
    "PostToolUse": [
      { "matcher": "", "hooks": [
        { "type": "command", "command": "python3 ~/.claude/hooks/capture_tool_use.py" }
      ]}
    ],
    "SubagentStart": [
      { "matcher": "", "hooks": [
        { "type": "command", "command": "CLAUDE_HOOK_EVENT=subagent_start python3 ~/.claude/hooks/capture_subagent.py" }
      ]}
    ],
    "SubagentStop": [
      { "matcher": "", "hooks": [
        { "type": "command", "command": "CLAUDE_HOOK_EVENT=subagent_stop python3 ~/.claude/hooks/capture_subagent.py" }
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

Note: Mac's `settings.json` keeps existing `osascript` notification hooks. Linux version removes them (headless server has no notification UI).

### 4. PATH Exports Above bashrc Interactive Guard

```bash
# Add PATH above the Ubuntu interactive guard in both users' .bashrc
# This ensures non-interactive shells (Bash tool) can find venvs and uv

PATH_SNIPPET='# claude-code-path (must be above interactive guard)
export PATH="$HOME/.local/bin:$HOME/.venvs/litellm/bin:/usr/local/bin:$PATH"'

# Insert at top of both .bashrc files
sed -i "1a $PATH_SNIPPET" /home/claude/.bashrc
sed -i "1a $PATH_SNIPPET" /root/.bashrc
```

### 5. GitHub Auth (needs user-data or post-boot automation)

```bash
# In user-data (alongside Doppler token):
# gh auth token comes from Doppler — reference it after Doppler is configured
doppler run -- bash -c 'echo "$GH_TOKEN" | gh auth login --with-token'
doppler run -- gh auth setup-git
```

Or configure git credential.helper in the golden image to use `gh` directly:
```bash
# In provision.sh:
su - claude -c 'git config --global credential.helper "$(which gh) auth git-credential"'
```

### 6. Install startup-engine-exp Skill

```bash
# provision.sh — after cloning wshobson/commands for startup-engine:
# The startup-engine-exp skill lives in the pm-skills repo (not public)
# Either:
#   a) Move it to its own public repo and clone it
#   b) Include it in the golden repo's config directory
#   c) Fetch it as part of user-data after gh auth is set up

# Option b — include in golden repo:
if [ -d "$GOLDEN_ROOT/config/skills/startup-engine-exp" ]; then
  cp -r "$GOLDEN_ROOT/config/skills/startup-engine-exp" /home/claude/.claude/skills/
  chown -R claude:claude /home/claude/.claude/skills/startup-engine-exp/
fi
```

---

## New Droplet Creation Workflow (After These Changes)

```bash
# 1. Create user-data file
cat > /tmp/droplet-userdata.sh << 'EOF'
#!/bin/bash
set -e

# Configure Doppler for both users
DOPPLER_TOKEN="dp.st.prd.xxxxxxxxxxxxxxxx"
doppler configure set token "$DOPPLER_TOKEN" --scope /root
sudo -u claude doppler configure set token "$DOPPLER_TOKEN" --scope /home/claude

# Authenticate GitHub CLI (token comes from Doppler)
source <(doppler secrets download --no-file --format env)
echo "$GH_TOKEN" | gh auth login --with-token
sudo -u claude bash -c "echo $GH_TOKEN | gh auth login --with-token && gh auth setup-git"

# Clone project repos as claude user
sudo -u claude bash -c '
  cd ~/projects
  gh repo clone try-insite/insite-v6 2>/dev/null || (cd insite-v6 && git pull)
  gh repo clone try-insite/cf-pipeline-v2 2>/dev/null || (cd cf-pipeline-v2 && git pull)
'

history -c
EOF

# 2. Create droplet from golden snapshot
doctl compute droplet create "insite-v6-sprint8" \
  --image YOUR_GOLDEN_SNAPSHOT_ID \
  --size s-2vcpu-4gb \
  --region nyc1 \
  --ssh-keys YOUR_SSH_KEY_ID \
  --user-data-file /tmp/droplet-userdata.sh \
  --wait

# 3. Done. SSH in as claude user and start working.
doctl compute ssh insite-v6-sprint8 --ssh-user claude
```

**Total manual steps after this:** 0. The droplet boots with:
- All secrets loaded via Doppler
- GitHub CLI authenticated
- Project repos cloned
- Hooks active (via inject_env.sh + settings.linux.json)

---

## Immediate Fix for Current Droplet (134.122.24.60)

```bash
ssh root@134.122.24.60 << 'FIX'

# Fix 1: Root hooks in wrong directory
mkdir -p /root/.claude/hooks
cp /home/claude/.claude/hooks/* /root/.claude/hooks/
chmod +x /root/.claude/hooks/*.py /root/.claude/hooks/*.sh

# Fix 2: Settings.json for root
cp /home/claude/.claude/settings.json /root/.claude/settings.json

# Fix 3: PATH above bashrc guard for both users
for rcfile in /root/.bashrc /home/claude/.bashrc; do
  if ! grep -q "# claude-code-path" "$rcfile"; then
    sed -i '1i# claude-code-path\nexport PATH="$HOME/.local/bin:$HOME/.venvs/litellm/bin:/usr/local/bin:$PATH"\n' "$rcfile"
  fi
done

# Fix 4: Create inject_env.sh
cat > /home/claude/.claude/hooks/inject_env.sh << 'HOOK'
#!/usr/bin/env bash
[ -z "$CLAUDE_ENV_FILE" ] && exit 0
echo "export PATH=\"$HOME/.local/bin:$HOME/.venvs/litellm/bin:/usr/local/bin:$PATH\"" >> "$CLAUDE_ENV_FILE"
# Load secrets from .bashrc exports
grep '^export ' /home/claude/.bashrc >> "$CLAUDE_ENV_FILE" 2>/dev/null || true
exit 0
HOOK
chmod +x /home/claude/.claude/hooks/inject_env.sh
cp /home/claude/.claude/hooks/inject_env.sh /root/.claude/hooks/

FIX
```
