# Secrets Management for Image-Based Environment Provisioning
**DigitalOcean Golden Image → Droplet Pattern | 2026-04-07 UTC**

---

## Executive Summary

Every approach reduces to the "secret zero" problem: something must exist on the droplet at boot to bootstrap trust with a secrets store. The quality of your approach is measured by **how little damage the secret zero can do if it leaks**.

**The core DO constraint:** DigitalOcean has no native secrets management (no AWS IAM instance profiles, no GCP Workload Identity). The metadata endpoint at `http://169.254.169.254/metadata/v1/user-data` exposes user-data **in plaintext to any process on the VM for the droplet's entire lifetime**. Never put actual API keys directly in user-data — only a single bootstrap token.

**Ranked recommendations:**

| Rank | Approach | Complexity | Security | Best For |
|------|----------|------------|----------|----------|
| 1 | **Doppler + cloud-init user-data** | Low | Good | Best overall |
| 2 | **1Password CLI + Service Account** | Low-Med | Good | Teams already on 1Password |
| 3 | **Encrypted .env on DO Spaces + age** | Medium | Moderate-Good | Zero SaaS dependencies |
| 4 | **HashiCorp Vault + Vault Agent** | High | Excellent | Compliance/audit requirements |
| ✗ | **Secrets directly in user-data** | N/A | Very Poor | NEVER — plaintext exposure |
| ✗ | **GitHub Actions/Environments** | N/A | N/A | Wrong tool entirely |

---

## The Metadata Endpoint Risk (Must Understand)

```bash
curl http://169.254.169.254/metadata/v1/user-data
```

Run from inside any process on your droplet — any compromised npm package, container escape, or malicious code — this returns your user-data in **plaintext, no auth required**. This is how all cloud metadata services work (AWS had the same issue until IMDSv2). DigitalOcean doesn't have a hardened equivalent.

**Rule:** Put only ONE bootstrap token in user-data. Never put your actual API keys.

---

## DigitalOcean Has No Native Secrets Management

As of April 2026, DO does not offer:
- IAM instance identities (like AWS EC2 Instance Profiles)
- Native secrets vault (like AWS Secrets Manager)
- Per-service cloud credentials

What exists:
- **App Platform encrypted env vars** — not applicable to snapshot/droplet workflow
- **DO Spaces** — object storage where you can store encrypted files (needs static access key)
- **Metadata endpoint** — useful as delivery mechanism, not a security primitive

**This is the root structural gap.** Until DO builds IAM identity, some static bootstrap credential is unavoidable. Choose the one with the smallest blast radius.

---

## Recommended Approach: Doppler + cloud-init

**Why Doppler:** Purpose-built for this exact pattern. One-click DO Marketplace app. DigitalOcean community explicitly recommends it for this use case.

### One-Time Setup

1. Sign up at doppler.com → Create project → Add all secrets:
   - `ANTHROPIC_API_KEY`
   - `OPENAI_API_KEY` / `GOOGLE_API_KEY`
   - `CLOUDFLARE_API_TOKEN`
   - `SPECSTORY_API_KEY`
   - `GH_TOKEN`
   - `SANITY_API_TOKEN` / `SANITY_PROJECT_ID`
   - `NETLIFY_AUTH_TOKEN`
   - All MCP tokens (GoHighLevel, BrightData, Sentry)

2. Generate a Service Token (read-only, scoped to `prd` config): `dp.st.prd.xxxxxxxxxx`

3. Store token in 1Password or your own password manager

### Golden Image Changes (`provision.sh`)

```bash
# Install Doppler CLI in the golden image
apt-get update && apt-get install -y apt-transport-https
curl -sLf --retry 3 --tlsv1.2 --proto "=https" \
  'https://packages.doppler.com/public/cli/gpg.DE2A7741A397C129.key' | \
  gpg --dearmor -o /usr/share/keyrings/doppler-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/doppler-archive-keyring.gpg] \
  https://packages.doppler.com/public/cli/deb/debian any-version main" | \
  tee /etc/apt/sources.list.d/doppler-cli.list
apt-get update && apt-get install -y doppler

# Add to claude user's .bashrc in the image (above the interactive guard):
cat >> /home/claude/.bashrc << 'EOF'
# Load secrets from Doppler (runs on every login if token is configured)
if command -v doppler &>/dev/null && doppler secrets >/dev/null 2>&1; then
  eval "$(doppler secrets download --no-file --format env 2>/dev/null)"
fi
EOF
```

### Droplet Creation (user-data)

Only this one credential goes in user-data:

```bash
#!/bin/bash
# User-data script — runs once at first boot via cloud-init
# Configure Doppler for the root user
doppler configure set token dp.st.prd.xxxxxxxxxxxxxxxx --scope /root

# Also configure for the claude user
sudo -u claude doppler configure set token dp.st.prd.xxxxxxxxxxxxxxxx --scope /home/claude

# Clear from shell history
history -c
```

Pass it at droplet creation:
```bash
doctl compute droplet create insite-v6-sprint8 \
  --image YOUR_GOLDEN_SNAPSHOT_ID \
  --size s-2vcpu-4gb \
  --region nyc1 \
  --user-data-file ./doppler-bootstrap.sh
```

### Result

Boot → cloud-init runs (5 seconds) → every subsequent shell login as root or claude auto-fetches all secrets from Doppler → Claude Code, hooks, and all CLI tools have full credentials from first login. **Zero manual SSH required.**

### Security Properties

- Only bootstrap token in user-data (not the actual secrets)
- Bootstrap token compromised? Revoke in Doppler dashboard, generate new one — existing running droplets still work, new droplets get new token
- Doppler encrypts at rest (AES-256) and in transit (TLS 1.2+)
- Full audit log: every secret access logged (when, which secret, which token)
- Rotation: update a secret in Doppler UI → running droplets pick it up on next login

---

## Alternative 1: 1Password Service Account

Best if the team already uses 1Password Teams or Business.

```bash
# Golden image: install op CLI
curl -sS https://downloads.1password.com/linux/debian/amd64/stable/1password-cli-amd64-latest.deb -o /tmp/op.deb
dpkg -i /tmp/op.deb

# Create /etc/op-references.env in the image (no secrets — just paths):
cat > /etc/op-references.env << 'EOF'
ANTHROPIC_API_KEY=op://Server Secrets/Anthropic/api-key
OPENAI_API_KEY=op://Server Secrets/OpenAI/api-key
CLOUDFLARE_API_TOKEN=op://Server Secrets/Cloudflare/api-token
SPECSTORY_API_KEY=op://Server Secrets/SpecStory/api-key
EOF

# Add to .bashrc in image:
echo 'eval "$(op inject --in-file /etc/op-references.env)"' >> /home/claude/.bashrc
```

User-data (only the service account token):
```bash
#!/bin/bash
echo 'export OP_SERVICE_ACCOUNT_TOKEN=ops_xxxxxxxxxxxxxxxxxxxxxxxxx' >> /etc/environment
history -c
```

---

## Alternative 2: Encrypted .env on DO Spaces + age (Zero SaaS)

Best if you want no SaaS dependency beyond what you already pay for.

**One-time setup:**
```bash
# On your Mac:
brew install age awscli

# Generate key pair
age-keygen -o ~/age-secrets-key.txt
# Keep ~/age-secrets-key.txt SECRET — bake the private key into golden image
# The public key line looks like: age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Create secrets file
cat > secrets.env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
# ... all secrets
EOF

# Encrypt with the public key
age -e -r age1xxxxxxxxxxxxxxxxxxxxxxxxxx secrets.env > secrets.env.age
rm secrets.env

# Upload to DO Spaces
aws --endpoint=https://nyc3.digitaloceanspaces.com s3 cp secrets.env.age \
  s3://your-secrets-bucket/secrets.env.age
```

**Golden image:** Bake the age private key into `/etc/age-key.txt` (mode 600, owned root).

**User-data (only the Spaces access key):**
```bash
#!/bin/bash
# Configure DO Spaces access
aws configure set aws_access_key_id "SPACES_KEY" --profile secrets
aws configure set aws_secret_access_key "SPACES_SECRET" --profile secrets
aws configure set region nyc3 --profile secrets

# Download and decrypt secrets
aws --endpoint=https://nyc3.digitaloceanspaces.com --profile secrets \
  s3 cp s3://your-secrets-bucket/secrets.env.age /tmp/secrets.enc

age -d -i /etc/age-key.txt /tmp/secrets.enc > /etc/app-secrets.env
chmod 600 /etc/app-secrets.env
rm /tmp/secrets.enc

# Source on login (add to /etc/environment or .bashrc)
echo 'set -a; source /etc/app-secrets.env; set +a' >> /home/claude/.bashrc
history -c
```

**Rotation:** Edit secrets locally → re-encrypt → upload. Running droplets need to re-run the decrypt script. Best combined with a cron job or systemd timer that re-fetches on startup.

---

## Fixing Claude Code Non-Interactive Shell Gaps

Even with secrets in `.bashrc`, Claude Code hooks run in non-interactive shells — `.bashrc` is often not sourced. Two approaches:

### Option A: `inject_env.sh` + `CLAUDE_ENV_FILE` (Recommended)

Add an `inject_env.sh` hook to `SessionStart` in `settings.json`:

```bash
#!/usr/bin/env bash
# ~/.claude/hooks/inject_env.sh
[ -z "$CLAUDE_ENV_FILE" ] && exit 0

# Load Doppler secrets directly
if command -v doppler &>/dev/null && doppler secrets >/dev/null 2>&1; then
    doppler secrets download --no-file --format env >> "$CLAUDE_ENV_FILE"
elif [ -f /etc/app-secrets.env ]; then
    cat /etc/app-secrets.env >> "$CLAUDE_ENV_FILE"
fi

exit 0
```

### Option B: `doppler run -- hook-script`

Wrap hook commands in `settings.json`:
```json
{
  "type": "command",
  "command": "doppler run -- python3 ~/.claude/hooks/capture_tool_use.py"
}
```

---

## What GitHub Actions Is Good For (Adjacent Use Case)

GitHub Actions secrets/environments are not a runtime secrets delivery mechanism, but they are the right tool for:

1. **Deploying new droplets with the bootstrap token**: A GitHub Actions workflow that calls `doctl compute droplet create --user-data "doppler configure set token ${{ secrets.DOPPLER_TOKEN }}"` — the Doppler token lives in GitHub Secrets, never in your repo
2. **Rotating the bootstrap token**: A workflow that revokes old token, generates new one via Doppler API, stores it back to GitHub Secrets, updates all droplet `user-data` configs
3. **CI/CD pipelines that need secrets**: Standard use case — secrets injected into workflow runs

---

## HashiCorp Vault (When You Need It)

Only pursue Vault if you have compliance requirements, audit mandates, or a team large enough to justify dedicated infrastructure. For a 1-3 person dev team, the operational overhead is not worth it.

If you go this route: use **HCP Vault Dedicated** (HashiCorp's managed service) rather than self-hosted. Eliminates the unseal ceremony, availability concerns, and upgrade maintenance. Use AppRole with response wrapping for the tightest "secret zero" security — the bootstrap token is one-time-use and consumed on first boot.

---

## Action Plan

### This Sprint
1. Sign up for Doppler free tier
2. Add all current secrets to Doppler project
3. Generate a service token
4. Test: create a test droplet with Doppler user-data, verify all secrets load on first login

### Next Sprint (Golden Image Rebuild)
5. Add Doppler CLI install to `provision.sh`
6. Add Doppler env-loading snippet to both `/root/.bashrc` and `/home/claude/.bashrc` in the image
7. Add `inject_env.sh` hook to `settings.linux.json` that loads from Doppler
8. Rebuild golden image (v6)
9. Create new droplet from v6 snapshot with Doppler user-data
10. Target: zero manual SSH steps after droplet creation

### Future
- Evaluate Doppler's paid tier for audit logs if/when needed
- Consider age/Spaces approach as a backup for air-gapped or compliance scenarios
