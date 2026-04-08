---
name: startup-engine
description: >
  Autonomous AI development team that builds and ships real software products.
  COO orchestrator advances through Planning, Research, Requirements, UX/UI Design, Technical Design,
  Development, Testing, Deployment, Growth, and Evolution phases. Spawns VP agents who invoke
  existing skills and MCP tools to produce real, working code and artifacts.
  Runs on /loop cron with 3-day CEO review cadence.
  Triggers on: "startup engine", "start the company", "run the startup", "advance the sprint",
  "coo cycle", "startup loop".
---

# AI Startup Engine

## CRITICAL: THIS IS NOT A SIMULATION

Every agent in this system builds REAL software. Real code committed to real repos. Real tests
that run and pass. Real deployable artifacts. If any agent catches itself writing "In a real
implementation..." or "This would typically..." or describing what code COULD do instead of
writing it — that agent has failed its mission. Stop describing. Start building.

## Core Purpose

Build and ship real software products through an autonomous multi-agent development team.
The COO agent runs on a `/loop` cron, reads company state, detects completed phase artifacts,
and spawns the next phase's VP agent — who in turn invokes existing skills and MCP tools
to do the actual work: writing real code, creating real designs, running real tests, deploying
real infrastructure.

**Autonomy Principle:** Run the full SDLC autonomously between CEO check-ins. Only pause for:
(a) CEO approval gates (deployment, design review), (b) blockers that persist 3+ COO cycles,
(c) the 3-day loop expiry review.

**Build Principle:** Every phase must produce tangible, functional output. Documents exist to
inform the next build step, not as ends in themselves. If a phase produces only prose and
no working artifact that can be tested or executed, it has not completed.

---

## Prerequisites & Environment Setup

Before the engine can build and ship real software, the workspace needs real credentials.
During INITIALIZE, copy [.env.template](./templates/.env.template) to `~/startup-workspace/.env`
and verify each credential is set. **Do NOT skip this step.** Agents that hit auth failures
mid-sprint waste tokens and time.

### CRITICAL: API Access (check first)

| Variable | Purpose | How to Set |
|----------|---------|-----------|
| `ANTHROPIC_API_KEY` | **Use the Anthropic API instead of a consumer subscription (Max/Pro)** | Set as system env var in `~/.zshrc`: `export ANTHROPIC_API_KEY="sk-ant-..."` |

**Why this matters:** The startup engine spawns 15+ agents across hours/days of autonomous
operation. A consumer subscription (Claude Max/Pro) can be:
- **Rate-limited** mid-sprint, stalling all agents
- **Flagged** for automated usage patterns
- **Session-killed** during long-running agent chains
- **Impossible to track costs** per phase/sprint

The Anthropic API gives you: metered billing, predictable rate limits, cost tracking per
request, and reliable multi-agent execution. Get a key at https://console.anthropic.com/settings/keys
and add billing at https://console.anthropic.com/settings/billing.

**Note:** This is a SYSTEM environment variable, not a project .env variable. Claude Code
reads it from your shell environment. Add it to `~/.zshrc` or `~/.bashrc` and restart
your terminal.

### Required (bare minimum to build and deploy)

| Variable | Purpose | Used By Phases |
|----------|---------|----------------|
| `GITHUB_TOKEN` | Push code, create PRs, tag releases | 6, 7, 8 |
| `NETLIFY_AUTH_TOKEN` | Deploy sites, manage builds | 8 |
| `NETLIFY_SITE_ID` | Target site for deployment (set after first `netlify init`) | 8 |
*CEO email notifications use GoHighLevel MCP (no SMTP needed). See "CEO Email Notifications" section below.*

### Required for Full Pipeline

| Variable | Purpose | Used By Phases |
|----------|---------|----------------|
| `BRIGHT_DATA_API_TOKEN` | Web scraping, market research, competitor data | 0, 2 |
| `GHL_API_KEY` | GoHighLevel — blogs, social posts, email campaigns, CRM | 9 |
| `GHL_LOCATION_ID` | GoHighLevel — target location/sub-account | 9 |
| `SANITY_PROJECT_ID` | Sanity CMS — content management | 4, 9 |
| `SANITY_DATASET` | Sanity CMS — target dataset (e.g., `production`) | 4, 9 |
| `SANITY_TOKEN` | Sanity CMS — write access token | 4, 9 |
| `FIGMA_ACCESS_TOKEN` | Figma — create designs, read design systems | 4 |

### Optional (enhance specific phases)

| Variable | Purpose | Used By Phases |
|----------|---------|----------------|
| `OPENAI_API_KEY` | Alternative LLM for code review diversity | 7 |
| `SENTRY_DSN` | Error tracking in deployed application | 8, 10 |
| `SENTRY_AUTH_TOKEN` | Sentry API access for error monitoring | 8, 10 |
| `DATABASE_URL` | Production database connection string | 6, 8 |
| `DATABASE_URL_DEV` | Development database connection string | 6, 7 |
| `REDIS_URL` | Cache/session store connection | 6, 8 |
| `AWS_ACCESS_KEY_ID` | AWS services (S3, CloudFront, etc.) | 8 |
| `AWS_SECRET_ACCESS_KEY` | AWS services | 8 |
| `DO_API_TOKEN` | DigitalOcean — droplets, databases, spaces | 8 |
| `CLOUDFLARE_API_TOKEN` | DNS, CDN, Workers | 8 |
| `STRIPE_SECRET_KEY` | Payment processing | 6, 9 |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASS` | Transactional email | 6, 9 |
| `NPM_TOKEN` | Publish packages to npm | 8 |

### MCP Server Access

These are configured in Claude Code settings (not .env), but agents depend on them:

| MCP Server | Needed For | Configure Via |
|------------|-----------|---------------|
| Bright Data | Research, competitive intel, market scraping | Claude Code MCP settings |
| GoHighLevel | Blog posts, social media, email campaigns, CRM | Claude Code MCP settings |
| Figma | Design creation, design system access | Claude Code MCP settings |
| Sanity | CMS content management, schema access | Claude Code MCP settings |
| Chrome DevTools | Browser testing, Lighthouse audits, screenshots | Claude Code MCP settings |
| GitHub (gh CLI) | PR creation, issue tracking | `gh auth login` |
| Netlify (netlify CLI) | Deploy, build management | `netlify login` or env token |

### Environment Setup Script

All env management goes through [env_setup.py](./scripts/env_setup.py):

```bash
# Initialize .env from template
python3 scripts/env_setup.py --workspace ~/startup-workspace --init

# Audit what's configured vs missing
python3 scripts/env_setup.py --workspace ~/startup-workspace --check

# Set a single credential
python3 scripts/env_setup.py --workspace ~/startup-workspace --set GITHUB_TOKEN=ghp_xxx

# Set multiple at once
python3 scripts/env_setup.py --workspace ~/startup-workspace --set-batch GITHUB_TOKEN=ghp_xxx NETLIFY_AUTH_TOKEN=nfp_xxx
```

### Interactive Setup During INITIALIZE

When INITIALIZE detects missing required credentials, it should prompt the CEO interactively:

1. Run `python3 scripts/env_setup.py --workspace ~/startup-workspace --check`
2. Parse the output and the saved `logs/env_check.json`
3. For each missing **required** credential:
   - Tell the CEO what it is and exactly where to get it (URL + steps)
   - Ask: "Paste your GITHUB_TOKEN here, or type 'skip' to set it later:"
   - If the CEO provides a value, write it via `--set KEY=VALUE`
   - If the CEO skips, warn which phases will be blocked
4. For missing **pipeline** credentials, show the summary but don't prompt one-by-one
   - Say: "These are needed for the full pipeline. Set them anytime with:"
   - Print the `--set` command for each missing var
5. For missing **CLI tools**, suggest the install command and offer:
   - "Type `! gh auth login` to configure GitHub CLI now, or skip."

The CEO can also set credentials at any time outside the engine by running `--set` directly
or editing `~/startup-workspace/.env` in their editor.

This list will evolve as the product evolves. After each sprint, the Evolution phase should
check whether new services were added that need credentials, and update .env.template accordingly.

---

## Decision Tree

```
Input Analysis
├── First run (no company_state.json)? → INITIALIZE mode (includes env setup)
├── Has company_state.json? → COO CYCLE mode (advance to next phase)
├── "start the company" + product description? → INITIALIZE with product
├── "setup" or "configure"? → Run env_setup.py --check, prompt for missing credentials
├── "advance the sprint"? → Force COO cycle immediately
├── "ceo review"? → Generate CEO dashboard
└── "shutdown"? → Save state, stop loop
```

---

## Execution

### On First Invocation (INITIALIZE)

1. Load [org_chart.md](./reference/org_chart.md) — role definitions
2. Load [sdlc_protocol.md](./reference/sdlc_protocol.md) — phase rules and handoffs
3. **Recovery check:** If a repo is configured, `git pull` first to get latest `.claude-engine/` state.
   Then check for `WORKING_CONTEXT.md` in the workspace OR in `{repo}/.claude-engine/`:
   - **If WORKING_CONTEXT.md exists:** Read it FIRST. This is a recovery from a killed session.
     Skip onboarding. Resume from the phase documented in the file. Print:
     "Recovered working context from {timestamp}. Resuming from Phase {N}: {phase_name}."
   - **If no WORKING_CONTEXT.md:** This is a fresh start. Proceed with full INITIALIZE.
4. Create workspace: `~/startup-workspace/` (or restore existing)
4. Create directory structure:
   ```
   ~/startup-workspace/
   ├── state/          (company_state.json, project_config.json, backlog.json, sprint_state.json)
   ├── artifacts/      (research/, requirements/, designs/, code/, tests/, deployments/)
   ├── reviews/        (ceo_reviews/, peer_reviews/, retrospectives/)
   ├── intel/          (competitive reports, market pulse, growth metrics)
   ├── logs/           (agent_activity.jsonl, decisions.jsonl, costs.jsonl, env_check.json)
   ├── history/        (conversation logs — one file per agent session for retro analysis)
   └── WORKING_CONTEXT.md  (living document — the "brain" that survives session kills)
   ```
5. **Onboarding Wizard** (via [onboard_wizard.md](./reference/onboard_wizard.md)):
   Run the wizard as a conversational interview with the CEO. Ask in stages — don't dump
   all questions at once. Offer smart defaults in [brackets].
   a. **Stage 1 — The Product:** "What are we building?" → name, description, audience, success criteria
   b. **Stage 2 — The Repository:** New or existing? Where? Branch? Monorepo?
   c. **Stage 3 — Tech Stack:** Framework, language, DB, hosting — or "you pick" for smart defaults
   d. **Stage 4 — Integrations:** CMS, Figma, marketing, payments — "skip" for any not needed
   e. **Stage 5 — Preferences:** TDD, CI/CD, review strictness, budget cap
   f. **Stage 6 — Confirm:** Show summary table, let CEO approve or change anything
   g. Write answers to `~/startup-workspace/state/project_config.json`

   If $ARGUMENTS already contains a product description, pre-fill Stage 1 and confirm it,
   then continue with Stage 2.

6. **Environment Setup** (via [env_setup.py](./scripts/env_setup.py)):
   a. Run `python3 scripts/env_setup.py --workspace ~/startup-workspace --init` (copies template if no .env)
   b. Run `python3 scripts/env_setup.py --workspace ~/startup-workspace --check` (audit + save report)
   c. For each missing **required** credential: tell the CEO what it is, where to get it, ask to paste or skip
   d. Write any provided values via `--set KEY=VALUE`
   e. For missing **pipeline** credentials: show summary, print `--set` commands for later
   f. For missing **CLI tools**: suggest install commands, offer `! command` to run in-session
   g. **Block if required vars are still missing** — prompt again or warn which phases are blocked
   h. **Warn but continue** for optional/pipeline vars

7. Initialize [company_state_template.json](./templates/company_state_template.json) → `~/startup-workspace/state/company_state.json`
8. **Repository Setup (gitignore-first rule):**
   a. Create the git repo if new
   b. FIRST COMMIT: `.gitignore` + `README.md` ONLY — no code, no env files
   c. `.gitignore` must cover: `.env`, `env.txt`, `*.local`, `secrets.*`, `node_modules/`, `.claude-engine/logs/`, `*.key`
   d. Create `.env` file AFTER .gitignore is committed
   e. Verify `.env` does NOT appear in `git status` (must be ignored)
   f. Only THEN proceed to any code
9. Write first product epic to `state/backlog.json` (from wizard Stage 1 answers)
10. Set company_state.json: current_phase = "planning"
11. Print: "Company initialized. Run `/loop 30m /startup-engine` to start the COO cycle."

### On COO Cycle (every 30 min via /loop)

**Safety checks FIRST (before any agent work):**

1. **Kill switch:** Check if `~/startup-workspace/STOP` file exists → if yes, print reason, do NOT spawn any agents, exit
2. **Pause check:** Check if `company_state.json` has `paused: true` → if yes, print status, exit
3. **Budget check:** Read `logs/costs.jsonl`, sum this sprint → if over `preferences.budget_per_sprint`, pause and escalate to CEO. **Email CEO:**
   **Email CEO** via GHL (see CEO Email Notifications section)
4. **Stale phase check:** Read `company_state.json` → if same phase for 6+ consecutive COO cycles (3 hours) with no new artifacts, mark as blocker and escalate to CEO — do NOT re-spawn the same agent. **Email CEO:**
   **Email CEO** via GHL (see CEO Email Notifications section)
5. **Max retries check:** Read `state/phase_attempts.json` → if current phase has been attempted 3+ times, escalate instead of retrying. **Email CEO:**
   **Email CEO** via GHL (see CEO Email Notifications section)

**Then proceed with normal cycle:**

6. Read `~/startup-workspace/state/company_state.json`
7. Read [sdlc_protocol.md](./reference/sdlc_protocol.md)
8. Determine current phase
9. Check: does the current phase's expected output artifact exist?
   - YES → Run quality gate check → If pass: advance to next phase, reset attempt counter
   - NO → Increment attempt counter in `state/phase_attempts.json`
10. If advancing: load the next phase's VP prompt from [phase_prompts/](./reference/phase_prompts/)
11. Substitute variables ({workspace}, {epic}, {sprint}, prior phase outputs)
12. Spawn VP Agent via Agent tool (**always foreground** — see Safety Controls below)
13. Update company_state.json with new phase, UTC timestamp
14. Append to logs/agent_activity.jsonl (include cost estimate for this cycle, UTC timestamps)
15. Update WORKING_CONTEXT.md with current status (even if nothing changed — update UTC timestamp)
16. Git commit and push all `.claude-engine/` files:
    ```bash
    cd {repo} && git add .claude-engine/ && git commit -m "chore(engine): COO cycle — phase {phase}" && git push origin {branch} 2>/dev/null || true
    ```
17. If phase is a CEO gate: write summary to reviews/ceo_reviews/ and PAUSE. **Email CEO:**
    **Email CEO** via GHL (see CEO Email Notifications section)

**IMPORTANT:** When spawning VP agents, prepend this directive to every prompt:
> "You are building a real software product. Write real code, create real files, produce real
> working artifacts. This is NOT a simulation, roleplay, or thought exercise. Every file you
> create must be functional and testable. Do not describe what you would build — build it.
>
> Read {workspace}/state/project_config.json for the tech stack, repository, hosting, and
> integration configuration. Use the configured technologies — do not substitute your own
> preferences. Write code to the configured repository path.
>
> **SANDBOX-FIRST RULE:** Use sandbox/test credentials for ALL external services during
> development. Stripe: `sk_test_` ONLY. Email: sandbox mode. Database: dev instance.
> Production credentials are set ONLY in Phase 8 after CEO approval.
>
> **CREDENTIAL PAUSE RULE:** If ANY required credential is missing from .env, DO NOT skip
> the feature, mock it, or use a placeholder. PAUSE immediately:
> 1. WebSearch the provider's REAL documentation for how to get the credential
> 2. Write step-by-step instructions with verified URLs
> 3. Email CEO via GHL MCP with what's needed and how to get it
> 4. Poll .env every 60 seconds for the credential
> 5. If not provided within 60 minutes: write WORKING_CONTEXT.md, commit to git, STOP
> NEVER assume you know where to get a credential. Look it up. UIs change.
>
> **PREVIEW = REAL DATA RULE:** Any preview, demo, or "see your result" step MUST render
> actual data from the actual backend. Hardcoded placeholders are NEVER acceptable.
>
> **PRE-SHIP CHECKLIST (verify before marking any story done):**
> [ ] Tests pass (unit + integration + cross-boundary)
> [ ] Build passes (zero warnings, lint clean, type check)
> [ ] Feature works in browser with real data (not just tests)
> [ ] User can accomplish the stated goal end-to-end
> [ ] External system boundaries tested with realistic payloads
> [ ] Preview/demo shows real backend data
> [ ] All credentials are sandbox/test mode
> [ ] No secrets in git history
>
> **Conversation Logging:** At the END of your work, write a session summary to
> {workspace}/history/{phase}_{timestamp_utc}.md (where timestamp_utc is YYYYMMDD_HHMMSSZ in UTC) containing:
> 1. Your role and phase
> 2. What you were asked to do (the prompt you received)
> 3. Key decisions you made and why
> 4. What you produced (file paths, commits, artifacts)
> 5. Errors encountered and how you resolved them
> 6. What you would do differently
> 7. Token/cost estimate if available
> 8. Time spent (start/end timestamps)
> This history file is critical — the sprint retro skill reads these to reconstruct
> what happened during the sprint."

### Timestamp Convention — ALL Timestamps in UTC

**Every timestamp in the startup engine MUST be in UTC.** This applies to:
- History file names: `{phase}_{YYYYMMDD_HHMMSSZ}.md` (the Z suffix indicates UTC)
- All ISO timestamps in JSON state files (company_state.json, agent_activity.jsonl, decisions.jsonl, costs.jsonl, ceo_notes.jsonl)
- WORKING_CONTEXT.md "Last updated" field
- Sprint retro reports
- Deploy logs
- Email notification timestamps

**Why:** The engine may run on local machines (various timezones), remote droplets (UTC), or switch between them mid-sprint. Using local time creates confusion when correlating events across sessions. UTC is the single source of truth.

**How:** In Python scripts, use `datetime.now(timezone.utc).isoformat()`. In agent prompts that generate timestamps, always append `Z` or `+00:00` to indicate UTC. When displaying timestamps to the CEO, format as `YYYY-MM-DD HH:MM UTC`.

### Conversation History Protocol

Every COO cycle and VP agent session MUST produce a history file at
`{workspace}/history/{phase}_{YYYYMMDD_HHMMSSZ}.md` (UTC timestamp). This is non-negotiable because:

1. **The sprint retro skill depends on it.** Without history files, the retro can only
   reconstruct from git commits — losing all the context about decisions, errors, and
   reasoning that makes retros actually useful.
2. **Context doesn't survive between sessions.** Each `/loop` tick is a fresh Claude session.
   History files are the only way to pass qualitative context between sessions.
3. **Cost tracking needs narrative.** `costs.jsonl` tracks numbers; history files explain
   why those costs were incurred.

**COO history entries** should log: which phase was detected, what decision was made
(advance/spawn/wait/halt), which agent was spawned, and the outcome.

**VP history entries** should log: the full directive they received, their approach,
what they built, problems they hit, and their recommendations for next steps.

### WORKING_CONTEXT.md — The Living Brain

`{workspace}/WORKING_CONTEXT.md` is the single most important file in the workspace. It is
the running context that allows any new session to pick up exactly where the last one left off.
If the session gets killed, the loop expires, or the droplet reboots — this file is how we
recover without losing progress.

**Structure:**

```markdown
# Working Context — {Product Name}
**Last updated:** {YYYY-MM-DD HH:MM UTC}
**Current sprint:** {N}
**Current phase:** {phase_name}
**Updated by:** {COO/VP role}

## What We're Building
{1-2 sentence product description from onboarding}

## Current Sprint Goal
{The epic/goal for this sprint}

## Where We Are Right Now
{Exactly what phase we're in, what's been completed, what's in progress}
- Last completed phase: {phase} at {YYYY-MM-DD HH:MM UTC}
- Current phase: {phase} — {status}
- Next phase: {phase}
- Blockers: {any blockers or "none"}

## Key Decisions Made This Sprint
{Numbered list of significant decisions with rationale — these are the things
a new session needs to know to avoid re-debating settled questions}

## What's Been Built So Far
{List of real artifacts produced — file paths, commits, deployments}

## Open Questions / Risks
{Things that haven't been decided yet or risks being tracked}

## Tech Stack & Config Summary
{Quick reference pulled from project_config.json — framework, repo, hosting}

## Credentials Status
{Which env vars are set vs missing — so a new session knows what's available}
```

**Update Rules:**

1. **COO updates WORKING_CONTEXT.md on EVERY cycle** — even if nothing changed, update
   the timestamp so we know the last heartbeat.

2. **VP agents update it after completing their work** — add what they built, decisions
   they made, and any issues they encountered.

3. **Sprint retro (Phase 10a) does a full rewrite** — after the retro, WORKING_CONTEXT.md
   gets a fresh version incorporating everything learned. This is the "clean slate" that
   the next sprint starts from.

4. **On INITIALIZE,** if WORKING_CONTEXT.md already exists, read it FIRST before doing
   anything else. This is how a killed session recovers.

### Git Persistence Protocol — Everything Gets Committed

All audit trail and context files MUST be committed to the project git repo so they survive
droplet destruction, session kills, and machine switches. This is how local and remote stay
in sync.

**What gets committed to the repo (in a `.claude-engine/` directory at repo root):**

```
{repo}/.claude-engine/
├── WORKING_CONTEXT.md          (the living brain — always current)
├── state/                       (company_state.json, project_config.json, backlog.json)
├── history/                     (all conversation logs from every agent session)
├── reviews/retrospectives/      (all sprint retro reports)
├── logs/                        (agent_activity.jsonl, decisions.jsonl, costs.jsonl)
└── context/                     (context-save snapshots)
```

**What does NOT get committed (stays in workspace only):**
- `.env` files (secrets)
- `artifacts/code/` (this IS the repo — don't nest it)
- Temporary build artifacts

**When to commit:**

| Event | What to commit | Commit message |
|-------|---------------|----------------|
| Every COO cycle | WORKING_CONTEXT.md, state/*.json | `chore(engine): COO cycle {N} — phase {phase}` |
| VP agent completes | WORKING_CONTEXT.md, history/{session}.md | `chore(engine): {phase} complete — {summary}` |
| Sprint retro (10a) | WORKING_CONTEXT.md, reviews/retrospectives/ | `chore(engine): sprint {N} retro complete` |
| Context save (10d) | context/{snapshot}.md, WORKING_CONTEXT.md | `chore(engine): sprint {N} context saved` |
| CEO review | state/*.json, WORKING_CONTEXT.md | `chore(engine): CEO review — {date}` |

**How to commit (add this to every VP agent's directive):**

```bash
cd {repo}
git add .claude-engine/
git commit -m "chore(engine): {phase} — {one-line summary}"
git push origin {branch} 2>/dev/null || true
```

The `|| true` on push ensures a failed push (network issue, auth problem) doesn't crash the
agent. The commit is still local and will be pushed on the next successful cycle.

**On session recovery (INITIALIZE with existing state):**

1. `git pull` to get latest `.claude-engine/` state from remote
2. Read `WORKING_CONTEXT.md` — this tells you exactly where to pick up
3. Read `state/company_state.json` — this tells you the current phase
4. Read the latest `history/` entry — this tells you what the last agent did
5. Resume from the current phase

This means: if a droplet dies, you spin up a new one, clone the repo, and the engine picks
up exactly where it left off. No lost context. No re-doing completed work.

### On CEO Review

1. Run `python3 scripts/generate_dashboard.py --workspace ~/startup-workspace/`
2. Present dashboard with: progress, quality scores, decisions made, blockers, costs
3. Accept CEO feedback and priority adjustments
4. Update backlog.json and company_state.json with CEO direction
5. Print: "Re-run `/loop 30m /startup-engine` to resume."

---

## Phase Sequence

| # | Phase | VP Owner | Key Skills Invoked | Real Output |
|---|-------|----------|-------------------|-------------|
| 0 | Continuous Intel | VP BizDev | /deep-research, Bright Data MCPs | Market reports with real scraped data |
| 1 | Planning | COO | /tools:context-restore, /tools:tech-debt, /tools:standup-notes | Sprint plan with concrete tasks |
| 2 | Product Research | VP Product | /deep-research, Bright Data MCPs, /product-pipeline P1-3 | User research backed by real data sources |
| 3 | Requirements | VP Product | /product-pipeline P4-6, /tools:doc-generate, /tools:accessibility-audit | Implementable stories with testable acceptance criteria |
| 4 | UX/UI Design | VP Product | /tools:ux-flows, Figma MCPs, Chrome MCPs, Sanity MCPs | Figma designs, component specs, content models |
| 5 | Technical Design | VP Eng | /tools:api-scaffold, /tools:db-migrate, /tools:data-pipeline | Architecture doc, executable DB schema, API spec |
| 5.5 | Credential Verify | COO | WebSearch provider docs, env_setup.py | All required credentials verified, sandbox mode confirmed |
| 6 | Development | VP Eng | /workflows:tdd-cycle, /workflows:feature-development, /workflows:git-workflow | **Working code with cross-boundary tests, sandbox creds** |
| 7 | Testing & Review | VP Eng | /tools:test-harness, /tools:multi-agent-review, /tools:security-scan, Chrome MCPs | Test results, cross-boundary tests, security scan |
| 7b | E2E Testing | E2E Agent (separate) | Chrome DevTools MCP, real browser | User journey verified end-to-end by a NON-builder agent |
| 7.5 | CEO Browser Review | CEO | Chrome DevTools, staging URL | CEO completes user journey in browser, approves |
| 8 | Deployment | VP Eng | /tools:deploy-checklist, /tools:monitor-setup, /tools:slo-implement | **Real deployment with production creds after CEO approval** |
| 9 | Growth & Content | VP BizDev | GoHighLevel MCPs, Sanity MCPs | Published blog posts, social posts, email campaigns |
| 10a | Sprint Retro | COO | /sprint-retro | Evidence-based retro: timeline, root causes, token analysis, action items |
| 10b | Technical Health | VP Eng | /tools:tech-debt, /tools:deps-upgrade, /tools:error-trace, /tools:refactor-clean | Resolved debt, upgraded deps, fixed production issues |
| 10c | Agent Improvement | COO | /workflows:improve-agent | Updated VP prompts, better conventions docs |
| 10d | Context Save | COO | /tools:context-save | Saved state, updated backlog with retro action items |

## CEO Gates (Pause Points)

- **After Phase 4 (Design):** Optional — review UX/UI before committing to build
- **Phase 5.5 (Credential Verify):** Email CEO for any missing credentials with step-by-step instructions from real docs
- **Phase 7.5 (CEO Browser Review):** REQUIRED — CEO must complete user journey in browser before deploy
- **Before Phase 8 (Deployment):** REQUIRED — approve production deployment + production credentials
- **Phase 10 (Evolution):** Sprint retrospective and next epic selection
- **3-Day Auto-Expiry:** Forced review of all progress
- **Any missing credential at any phase:** Email CEO with instructions, pause and poll

## Safety Controls — Preventing Runaway Agents

### How the Loop Architecture Works

The `/loop 30m /startup-engine` command is the heartbeat. Each tick:
- Starts a **fresh Claude Code session** (no leftover state from previous tick)
- Reads all state from disk (company_state.json, artifacts, logs)
- Makes ONE decision: advance, spawn, wait, or halt
- Spawns at most ONE VP agent per tick (foreground, so it completes before the COO exits)
- The loop has a **built-in expiry** (default 3 days) — after which it stops and forces a CEO review

This means: **no orphaned background agents.** The COO spawns a VP in foreground, waits for
it to complete, logs the result, and exits. The next loop tick starts fresh.

### Kill Switch

Create `~/startup-workspace/STOP` to immediately halt all engine activity:
```bash
echo "Reason: investigating cost spike" > ~/startup-workspace/STOP
```
Or via `/btw stop` which creates this file.

The COO checks for this file **before doing anything else** on every cycle. If it exists,
the COO prints the reason, logs the stop, and exits without spawning any agents.

To resume: delete the file (`rm ~/startup-workspace/STOP`) and re-run `/loop 30m /startup-engine`.

### Budget Enforcement

The COO reads `logs/costs.jsonl` on every cycle and sums costs for the current sprint.
If the total exceeds `preferences.budget_per_sprint` from `project_config.json`:
1. Creates a STOP file: "Budget exceeded: ${spent}/${budget}"
2. Writes escalation to `reviews/ceo_reviews/budget_alert.md`
3. Does NOT spawn any agents
4. The CEO must review, adjust budget via `/btw`, and remove the STOP file

### Stale Phase Detection

If the same phase has been `in_progress` for 6+ consecutive COO cycles (3 hours) with
no new artifacts appearing in the expected output directory:
1. COO marks the phase as "stalled" in company_state.json
2. Writes escalation to `reviews/ceo_reviews/stall_alert.md` with:
   - Which phase, how long, what's missing
   - Last agent activity from logs
3. Does NOT re-spawn the same agent (that's the definition of insanity)
4. Waits for CEO intervention via `/btw`

### Max Retry Policy

Each phase gets a maximum of **3 attempts** (tracked in `state/phase_attempts.json`):
```json
{"research": 1, "development": 2, "testing": 3}
```
On the 3rd failure: escalate to CEO instead of retrying. The CEO can:
- Reset the counter via `/btw` after fixing the underlying issue
- Skip the phase and move forward
- Modify the phase prompt and retry

### Agent Spawn Rules

| Rule | Limit | Why |
|------|-------|-----|
| Agents per COO cycle | **1** (foreground) | Prevents orphans — agent must complete before COO exits |
| Parallel sub-agents per VP | **3 max** | VP Development can spawn parallel developers, but capped |
| VP agent runtime | **30 min** (matches loop interval) | If the VP hasn't finished by next tick, COO detects stale |
| Background agents | **Avoid** — only for independent sub-tasks within a VP | Background agents outlive the session; use sparingly |
| Total agents per sprint | Tracked in `logs/agent_activity.jsonl` | CEO dashboard shows agent count for cost awareness |

### Why /loop, Not External Cron

`/loop` is the right control mechanism because:
1. **Built-in expiry** — forces CEO review after 3 days (configurable)
2. **Same process model** — runs inside Claude Code with access to all tools and MCPs
3. **Natural circuit breaker** — if Claude Code crashes, the loop stops (fail-safe)
4. **Session isolation** — each tick is a fresh session, no accumulated state corruption
5. **Visible** — the loop status is shown in the Claude Code UI

An external cron (`crontab`, launchd) would:
- Need to invoke `claude-code` CLI, which adds complexity
- Not have access to MCP servers configured in the desktop app
- Not benefit from the built-in expiry safety net
- Be harder for the CEO to monitor and control

**Exception:** If running on a remote server (e.g., DigitalOcean droplet via `/tools:droplet-clone`),
use the `/schedule` skill to set up a cron-based trigger instead of `/loop`. The schedule
skill creates remote triggers with built-in monitoring.

### CEO Email Notifications (via GoHighLevel)

All CEO emails are sent through the GoHighLevel MCP — no SMTP, no extra accounts, works everywhere including DO droplets where outbound SMTP is blocked.

**How to send:** Use the `mcp__GoHighLevel__conversations_send-a-new-message` tool:

```
mcp__GoHighLevel__conversations_send-a-new-message(
    body_type="Email",
    body_contactId="M6SGycSNsrBUq2Elzn6o",
    body_emailTo="dean@try-insite.com",
    body_subject="[Subject prefix] Product Name — Details",
    body_html="<html>...</html>"
)
```

**IMPORTANT:** Always include `body_emailTo="dean@try-insite.com"` — the contact has the email but the API requires it explicitly.

**When to email the CEO:**

| Event | Subject Prefix | Trigger |
|-------|---------------|---------|
| CEO gate reached | `[Action Required]` | Phase 4 (design) or Phase 8 (deploy) complete |
| Engine waiting | `[Waiting]` | Paused for any CEO input |
| Phase stalled | `[Stall]` | Same phase 6+ COO cycles with no progress |
| Blocker hit | `[Blocker]` | Phase failed after 3 attempts |
| Budget exceeded | `[Budget]` | Sprint spend > budget limit |
| Sprint retro | `[Retro]` | Phase 10a complete |
| 3-day expiry | `[Review]` | Loop auto-expired, CEO review needed |

Use `python3 scripts/send_email.py --type {type} --product {name} --json` to generate the HTML body, then pass it to the GHL MCP call. Or build the HTML inline — the script is a convenience helper, not a requirement.

### Emergency Procedures

| Situation | Action |
|-----------|--------|
| Agent seems stuck | `/btw status` → check phase + last activity time |
| Costs climbing fast | `echo "cost pause" > ~/startup-workspace/STOP` |
| Want to stop everything | `/btw stop` or create STOP file |
| Agent produced garbage | Delete the bad artifact, `/btw blocker add "Phase X produced invalid output"` |
| Need to skip a phase | `/btw` → manually set phase to next in company_state.json |
| Loop expired naturally | Review dashboard, then `/loop 30m /startup-engine` to resume |

## Output Contract

All state in `~/startup-workspace/`. Key files:
- `state/company_state.json` — current phase, sprint, blockers, pause state
- `state/project_config.json` — tech stack, repo, hosting, preferences (from wizard)
- `state/phase_attempts.json` — retry counter per phase
- `state/backlog.json` — prioritized product backlog
- `reviews/ceo_reviews/dashboard_{date}.md` — CEO check-in summaries
- `logs/agent_activity.jsonl` — full audit trail with cost estimates
- `logs/costs.jsonl` — per-cycle cost tracking
- `STOP` — kill switch file (presence halts all activity)
