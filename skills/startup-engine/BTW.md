---
name: btw
description: >
  Quick side-channel for the CEO to interact with the running Startup Engine without
  disrupting the SDLC loop. Ask questions, update credentials, check status, add notes,
  manage blockers, or do maintenance — all without pausing the COO cycle.
  Triggers on: "btw", "quick question", "while that's running", "side note".
---

# /btw — CEO Side Channel

Lightweight command for quick interactions with the Startup Engine while it's running.
Does NOT advance phases, spawn VP agents, or modify the SDLC state machine.

## Decision Tree

```
$ARGUMENTS Analysis
├── env / credentials / token / key
│   ├── "check" or "status" → Run env_setup.py --check
│   ├── "set KEY=VALUE"     → Run env_setup.py --set KEY=VALUE
│   └── "add KEY"           → Prompt CEO for value, then --set
│
├── status / "where are we" / "what phase"
│   → Read company_state.json, print current phase + sprint + blockers
│
├── blocker / blocked / stuck
│   ├── "add DESCRIPTION"   → Append to blockers array in company_state.json
│   ├── "list"              → Show current blockers
│   └── "resolve N"         → Remove blocker by index
│
├── note / reminder / "don't forget"
│   → Append to logs/ceo_notes.jsonl with UTC timestamp
│
├── backlog / priority / epic
│   ├── "show"              → Print current backlog.json
│   ├── "add ITEM"          → Append item to backlog
│   └── "reprioritize"      → Show backlog, ask CEO for new order
│
├── cost / spend / budget
│   → Read costs from company_state.json, print summary
│
├── approve / "looks good" / lgtm
│   → Check if any phase is awaiting_ceo_approval, if so mark approved
│
├── stop / kill / "shut it down" / emergency
│   → Create ~/startup-workspace/STOP file with reason + UTC timestamp (hard kill switch)
│   → COO will NOT spawn any agents on next cycle
│
├── pause / hold
│   → Set company_state.json flag: paused = true (soft pause — COO checks this)
│
├── resume / continue / go
│   → Remove STOP file if exists, set paused = false in company_state.json
│
├── retry / "try again" / "reset attempts"
│   → Reset phase_attempts.json counter for current phase to 0
│
├── dashboard
│   → Run generate_dashboard.py, print summary (lighter than full CEO review)
│
└── anything else
    → Treat as a question — read relevant state/artifacts and answer
```

## Execution

### Workspace Detection
1. Check if `~/startup-workspace/state/company_state.json` exists
2. If not: "No active startup workspace found. Run `/startup-engine` to initialize."
3. If yes: load state and proceed with the request

### Environment Commands

```
/btw check env
/btw set GITHUB_TOKEN=ghp_xxxx
/btw add SANITY_TOKEN
```

For env operations, use [env_setup.py](./scripts/env_setup.py):
- `--check`: audit and report
- `--set KEY=VALUE`: write single var
- For "add KEY" without value: ask the CEO to paste it, then write

### Status Commands

```
/btw status
/btw what phase are we in?
/btw how's it going?
```

Read `~/startup-workspace/state/company_state.json` and print:
- Current phase + status
- Sprint number + epic name
- Time in current phase
- Active blockers (if any)
- Last COO cycle timestamp (UTC)
- Budget remaining

Keep it concise — 5-10 lines max.

### Blocker Commands

```
/btw blocker add "Figma MCP not connecting"
/btw blocker list
/btw blocker resolve 0
```

Read/write the `blockers` array in company_state.json:
- Each blocker: `{"description": "...", "added_at": "ISO 8601 UTC timestamp", "added_by": "ceo"}`
- On resolve: remove from array, log to `logs/decisions.jsonl`

### Note Commands

```
/btw note: remember to add rate limiting before launch
/btw don't forget to check the Stripe webhook URL
```

Append to `~/startup-workspace/logs/ceo_notes.jsonl`:
```json
{"timestamp": "ISO 8601 UTC", "note": "...", "context_phase": "current phase"}
```

These notes are picked up by the COO during Planning and Evolution phases.

### Approval Commands

```
/btw approve
/btw lgtm
/btw approve deployment
```

Check company_state.json for any `awaiting_ceo_approval: true`:
- If found: set to false, log approval to `logs/decisions.jsonl`
- If not found: "Nothing awaiting your approval right now."

### Quick Dashboard

```
/btw dashboard
```

Run `python3 scripts/generate_dashboard.py --workspace ~/startup-workspace/`
Print the summary (not the full CEO review flow — no feedback collection).

## Rules

- **Never advance phases** — that's the COO's job
- **Never spawn VP agents** — that's the COO's job
- **Never modify artifacts** — that's the VP agents' job
- **Always read before writing** — don't overwrite state blindly
- **Keep responses short** — the CEO is checking in quickly, not doing a deep review
- **Log everything** — all CEO interactions go to `logs/ceo_notes.jsonl` or `logs/decisions.jsonl`
