## Secrets & Environment: Doppler is the Source of Truth

This environment uses **Doppler** for all secrets management. Secrets are **auto-downloaded at session start** to `/tmp/.claude-doppler-env` via a SessionStart hook. When you need secrets in a Bash command, source the file:

```bash
set -a; source /tmp/.claude-doppler-env 2>/dev/null; set +a
```

On **droplets**, secrets auto-load via `.profile` — no sourcing needed.

Key variable mappings:
- `GITHUB_PAT` → use as `GH_TOKEN` (map it: `export GH_TOKEN="$GITHUB_PAT"`)
- `ANTHROPIC_API_KEY` → Claude API key (sk-ant-...)
- `NETLIFY_API_TOKEN` → Netlify auth
- `SANITY_API_WRITE_TOKEN` / `SANITY_API_READ_TOKEN` → Sanity CMS
- `STRIPE_SECRET_KEY` → Stripe
- `SENTRY_AUTH_TOKEN` → Sentry

**Never hardcode secrets.** Never store them in files. If you need a secret, pull it from Doppler. If a secret is missing from Doppler, ask — do not guess or use placeholders.

---

## RULE: Quality First — Meet the Goal

The priority is **quality and meeting the goal**. Not speed. Not cost. Not "good enough."

If the output does not meet the stated goal, it does not matter how fast or cheap it was — it is worthless. Every agent, every skill, every pipeline should optimize for:

1. **Does it meet the goal?** The acceptance criteria, the user story, the stated objective. If not, it is not done.
2. **Is it correct?** No hallucinations, no broken code, no compliance violations, no untested assumptions.
3. **Is it complete?** No placeholder sections, no "in a real implementation" hand-waving, no deferred critical paths.

Speed and cost optimization come AFTER quality is proven. When choosing between models, tools, or approaches, choose the one most likely to produce a correct, complete result that meets the goal. If that means using the most expensive model, running multiple reviewers, or taking three rounds of iteration — do it.

**When in doubt:** spend more to get it right rather than less to get it fast.

---

## RULE: Who Is the Customer?

Before making ANY product decision, design choice, or recommendation — ask: **who is the customer and what do they want?**

The customer is the person paying for and using the tool. They are NOT the end-user of whatever the tool produces. If you are building a website builder, the customer is the person building the website — not the visitors to that website. If you are building a CRM, the customer is the sales team — not the leads in the pipeline. Always identify the customer for the specific project before proceeding.

- **Research informs recommendations — it does not make decisions.** Data about what works for end-users is valuable as information the customer can use, not as invisible rules the system imposes.
- **Present choices, do not make them.** Every research-backed default must be visible, explained, and overridable with zero friction.
- **Know the customer before recommending.** Generic recommendations are paternalistic. Personalized recommendations based on THIS customer are helpful.
- **Smart defaults, not mandates.** The research-optimized version is the default. The customer can change anything.
- **Creative decisions belong to the customer. Technical decisions belong to the system.**

---


## CRITICAL: Data-First Answers

Before answering any question about projects, customers, code, errors, deployments, or business status — ALWAYS check connected systems first. Never answer from memory or assumptions when real data exists.

- If a connected tool or MCP could contain the answer, query it BEFORE responding.
- **Never assume one query is enough.** Always check both production AND development environments (e.g., production vs preview datasets, production vs staging deployments, main vs feature branches). If they differ, present both results and flag the discrepancy. Do not assume which environment contains the correct answer.
- If you are unsure which system holds the answer, say so and ask — do not guess.

## CRITICAL: All Timestamps in UTC

Every timestamp produced by agents, scripts, or conversation logs MUST be in UTC. This applies to:
- History/conversation log filenames (use `Z` suffix: `{phase}_{YYYYMMDD_HHMMSSZ}.md`)
- All ISO timestamps in JSON state files
- WORKING_CONTEXT.md and session handoff documents
- Email notifications, deploy logs, retro reports
- Any date displayed to the user should show `YYYY-MM-DD HH:MM UTC`

**Why:** Agents run on local machines (various timezones) and remote droplets (UTC). Local timestamps create confusion when correlating events across sessions. UTC is the single source of truth.

**How:** In Python: `datetime.now(timezone.utc).isoformat()`. In agent-generated content: always append `Z` or `+00:00`.

## CRITICAL: Rebuild Golden Image After Any Change

When you modify ANY file that is baked into the droplet golden image — `CLAUDE.md`, skills, `settings.json`, commands, memory, or the `droplet-clone` skill itself — you MUST rebuild the golden image immediately using `/tools:droplet-clone --build`. Do not wait for the next deploy to discover the image is stale. Do not ask — just rebuild.

---

## Self-Learning Loop (Active)

A capture and analysis pipeline runs automatically on every Claude Code session via hooks in `~/.claude/settings.json`. It logs tool calls, subagent activity, and session metadata to `~/.claude/learning/captures/`. At session end, `analyze_session.py` extracts error patterns, hot files, and subagent anomalies into `~/.claude/learning/learnings/`. If you notice recurring failures or want to understand cross-session patterns, check those files. SpecStory syncs full conversation transcripts to `~/.specstory/history/` after every session.

---

## CRITICAL: Look Up Instructions Before Giving Them

When the user asks "how do I set up X", "how do I configure X", or any request for step-by-step instructions — NEVER answer from training data or assumptions. Always fetch current documentation first.

- WebSearch or WebFetch the official docs BEFORE giving any steps
- If instructions reference a UI path (e.g., "go to Settings > Limits"), verify that path exists in current docs
- If you can't verify, say so — don't guess. Link to the official docs page instead
- This applies to all platforms, tools, dashboards, APIs, and configuration screens
- UIs change constantly. Training data is always stale. The user has wasted hours following wrong instructions.
