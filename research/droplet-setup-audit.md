# Droplet Setup Audit — insite-v6-sprint7 (134.122.24.60)
**Date:** 2026-04-07 UTC  
**Droplet:** Built from golden-v5 snapshot  
**Purpose:** Document what went wrong and what needed manual intervention

---

## Summary

The golden image approach **mostly worked** — all software was installed correctly. What failed was the **human-loop problem**: secrets, GitHub auth, and cross-user file placement all require decisions that can't be baked into an image. The process took 30–60 minutes of debugging that should take under 5 minutes.

---

## What Worked (Golden Image Delivered)

| Component | Status | Notes |
|-----------|--------|-------|
| Node.js 20 | ✅ | Installed via NodeSource |
| Claude Code | ✅ | Globally installed via npm |
| SpecStory 1.12.0 | ✅ | Binary from GitHub releases |
| Wrangler 4.80.0 | ✅ | npm global install |
| GitHub CLI | ✅ | Installed via apt |
| Netlify CLI | ✅ | npm global install |
| doctl | ✅ | Binary from GitHub releases |
| UFW firewall | ✅ | Port 22 open, deny incoming |
| fail2ban | ✅ | Active and running |
| litellm venv | ✅ | `~/.venvs/litellm/` with litellm 1.83.4 |
| Hook scripts | ✅ | In `/home/claude/.claude/hooks/` |
| settings.json | ✅ | In `/home/claude/.claude/settings.json` |
| startup-engine skill | ✅ | Cloned from wshobson/commands |
| mount-engine-volume.service | ✅ | Installed, waits for /mnt/engine_state |
| claude user | ✅ | Created with sudo, correct home dir |
| Project repos | ✅ | cf-pipeline-v2, claude-worker-golden, insite-v6 cloned |

---

## What Failed / Required Manual Intervention

### 1. SSH Authentication — Terminus App
**Problem:** SSH client (Terminus) failed to authenticate with the droplet.  
**Root cause:** SSH key path mismatch — user's private key at a non-standard path, Terminus config pointed elsewhere.  
**Impact:** ~15 minutes of debugging auth failures before switching approach.  
**Fix applied:** Used `doctl compute ssh` fallback / adjusted Terminus to use correct key path.

### 2. `--dangerously-skip-permissions` Blocked as Root
**Problem:** Claude Code refuses to run with `--dangerously-skip-permissions` when running as root.  
**Root cause:** Claude Code security policy explicitly blocks root usage with permission bypass.  
**Impact:** Discovered only after SSH access was established, required switching to `su - claude`.  
**Fix applied:** `su - claude` then run Claude as the claude user.

### 3. `su -claude` vs `su - claude` (Space Required)
**Problem:** Typing `su -claude` (no space) causes "authentication failure" rather than user switching.  
**Root cause:** `su -username` is interpreted as a flag, not as `-l username`. The correct syntax is `su - claude`.  
**Impact:** ~5 minutes of confusion.

### 4. GitHub Authentication — Fine-Grained PAT Failed
**Problem:** Fine-grained personal access token (fine-grained PATs) failed to resolve private org repos via GitHub CLI's GraphQL endpoint.  
**Root cause:** Fine-grained PATs for organization repos require org admin approval and have limited API scope. They can't do GraphQL queries for org membership.  
**Fix applied:** Used classic PAT (stored in Doppler as `GITHUB_PAT`) which has full `repo` scope.

### 5. GitHub CLI + Git Credential Helper Not Configured
**Problem:** After `gh auth login`, `git pull` still prompted for credentials.  
**Root cause:** `gh auth login` sets up the gh token, but `git` uses a separate credential helper. `gh auth setup-git` must be run to wire them together.  
**Fix applied:** `gh auth setup-git`

### 6. Root User Missing Hooks and Settings
**Problem:** Claude Code sometimes runs as root (especially early in setup), but hooks and settings.json were only installed to `/home/claude/.claude/`.  
**Root cause:** `provision.sh` only copies to `/home/claude/.claude/hooks/`. The `settings.json` hook commands use `~/.claude/hooks/` path, which resolves to `/root/.claude/hooks/` when running as root — that directory was empty.  
**Fix applied:** Manually copied hooks and settings.json to `/root/.claude/`.  
**Note:** The copy was imperfect — hook scripts landed in `/root/.claude/` directly, not `/root/.claude/hooks/`. This means root user hooks still don't work correctly.

### 7. Secrets Not Available at Boot
**Problem:** No API keys were available after first boot. Claude Code, SpecStory sync, and all AI model calls fail silently until secrets are manually added.  
**Secrets added manually (via SSH + nano/echo):**
- `ANTHROPIC_API_KEY`
- `CLOUDFLARE_API_TOKEN`  
- `SPECSTORY_API_KEY`

**Secrets still missing (not added to this droplet):**
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY` / `GEMINI_API_KEY`
- `GH_TOKEN` (separate from gh config)
- `SANITY_API_TOKEN` / `SANITY_PROJECT_ID`
- `NETLIFY_AUTH_TOKEN`
- GoHighLevel, BrightData, Sentry MCP tokens

**Impact:** Major — this is the core problem. Every new droplet requires the same manual secret injection.

### 8. startup-engine-exp Skill Missing
**Problem:** The newer `startup-engine-exp` skill (with multi-model LiteLLM support) was not on the droplet. Only `startup-engine` was there.  
**Root cause:** `provision.sh` clones `wshobson/commands` which contains `startup-engine` but NOT `startup-engine-exp`. The exp skill lives in `~/.claude/skills/` on the Mac and was never pushed to any repo.  
**Fix applied:** Not applied — still missing on this droplet.

### 9. Nested Projects Directory
**Problem:** Running `cp -r /root/projects /home/claude/projects/` copied INTO the existing directory, creating `/home/claude/projects/projects/insite-v6/` etc.  
**Root cause:** If the destination directory already exists, `cp -r src/ dest/` copies `src/` as a subdirectory rather than merging. Should have used `cp -r /root/projects/. /home/claude/projects/` or `rsync`.  
**Fix applied:** `mv /home/claude/projects/projects/* /home/claude/projects/ && rmdir /home/claude/projects/projects`

---

## Current Droplet State (After Manual Fixes)

| Item | Status |
|------|--------|
| Claude Code accessible as claude user | ✅ |
| gh authenticated (classic PAT) | ✅ |
| insite-v6 cloned and authenticated | ✅ |
| ANTHROPIC_API_KEY in .bashrc | ✅ |
| CLOUDFLARE_API_TOKEN in .bashrc | ✅ |
| SPECSTORY_API_KEY in .bashrc | ✅ |
| Root hooks correctly installed | ❌ (in wrong directory) |
| startup-engine-exp skill | ❌ (not installed) |
| OPENAI_API_KEY | ❌ (missing) |
| GOOGLE_API_KEY | ❌ (missing) |
| SANITY / NETLIFY tokens | ❌ (missing) |
| GH_TOKEN env var | ❌ (gh config works, but env var missing) |

---

## Required Manual Steps (Every New Droplet — Current Process)

1. SSH in as root
2. `su - claude`
3. `gh auth login --with-token <<< "ghp_..."` to authenticate GitHub CLI
4. `gh auth setup-git` to wire credential helper
5. Add secrets to `~/.bashrc`:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   export CLOUDFLARE_API_TOKEN="cfat_..."
   export SPECSTORY_API_KEY="eyJ..."
   export OPENAI_API_KEY="sk-..."
   # ... etc for each service
   ```
6. Copy root hooks: `cp -r /home/claude/.claude/hooks /root/.claude/` and `cp /home/claude/.claude/settings.json /root/.claude/`
7. Fix root hooks path: ensure they're in `/root/.claude/hooks/` not `/root/.claude/`

That's 7 manual steps, some requiring secret values to be typed or pasted — no automation possible without a secrets management solution.

---

## Root Cause: Two Unsolved Problems

### Problem 1: Secrets Can't Be Baked Into Images
Golden images must be shareable/snapshotable. Secrets in the image = secrets in the snapshot = security risk. There's no way around this — secrets MUST be injected at runtime. The question is HOW to automate that injection.

### Problem 2: Claude Code Runs as Both Root and Claude User
When you SSH in as root and run Claude Code, it uses `/root/.claude/`. When you `su - claude`, it uses `/home/claude/.claude/`. The golden image only sets up one. If secrets are in `/home/claude/.bashrc`, running as root won't see them. If hooks are in `/home/claude/.claude/hooks/`, running as root won't use them.

---

## See Also

- `secrets-management-research.md` — Research on automated secrets injection approaches
- `multi-os-standardization-research.md` — Research on Mac/Ubuntu tooling parity
- `provision-improvements.md` — Proposed provision.sh changes based on this audit
