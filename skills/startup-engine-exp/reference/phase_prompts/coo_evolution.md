# Phase 10: Evolution & Sprint Retrospective

## CRITICAL: REAL METRICS, REAL DECISIONS

You are conducting a real retrospective based on real data. Read actual logs, actual test
results, actual production metrics. Do NOT fabricate sprint velocity or invent lessons learned.
Every finding must be backed by real data from the workspace.

## Input
- Read: {workspace}/state/company_state.json (full sprint state)
- Read: {workspace}/logs/agent_activity.jsonl (what agents actually did)
- Read: {workspace}/logs/decisions.jsonl (decisions actually made)
- Read: {workspace}/logs/costs.jsonl (actual spending)
- Read: {workspace}/artifacts/tests/{epic}/ (actual quality results)
- Read: {workspace}/intel/ (latest market intel)
- Read: {workspace}/history/ (ALL agent session logs from this sprint)
- Read: {workspace}/WORKING_CONTEXT.md (current state)

## Process

### Step 1: Sprint Retro (Phase 10a — RUN FIRST)

Invoke /sprint-retro with the workspace as context. The retro skill will:
1. Reconstruct timeline from `{workspace}/history/` session logs and git commits
2. Build requirements traceability matrix (sprint plan vs. what was built)
3. Run 5 Whys root cause analysis on major issues
4. Calculate token & cost efficiency from `{workspace}/logs/costs.jsonl`
5. Identify systemic process patterns
6. Generate action items

Write output to: `{workspace}/reviews/retrospectives/sprint-retro-{sprint_N}.md`

**The retro MUST complete before Steps 2-6.** Its findings inform everything else.

### Step 2: Email Sprint Summary to CEO

After the retro document is written, send the summary via SMTP:

```bash
# Write the retro summary as an HTML snippet to a temp file
cat > /tmp/retro_summary.html <<'RETRO_HTML'
<h3>Sprint Metrics</h3>
<table style="border-collapse: collapse; width: 100%;">
<tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;"><strong>Phases completed</strong></td><td>{N}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;"><strong>Agents spawned</strong></td><td>{N}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;"><strong>Total tokens</strong></td><td>{N}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;"><strong>Estimated cost</strong></td><td>${N}</td></tr>
</table>

<h3>Top 3 Wins</h3>
<ol><li>{win 1}</li><li>{win 2}</li><li>{win 3}</li></ol>

<h3>Top 3 Issues</h3>
<ol><li>{issue 1 + root cause}</li><li>{issue 2 + root cause}</li><li>{issue 3 + root cause}</li></ol>

<h3>Action Items</h3>
<table style="border-collapse: collapse; width: 100%;">
<tr style="background: #003d5c; color: white;"><th style="padding: 8px;">Action</th><th style="padding: 8px;">Owner</th><th style="padding: 8px;">Due</th></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{action}</td><td>{owner}</td><td>{due}</td></tr>
</table>

<p><strong>Next sprint:</strong> {next epic description}</p>
<p>Full retro: <code>.claude-engine/reviews/retrospectives/</code></p>
RETRO_HTML

# Send via SMTP
python3 scripts/send_email.py --type retro --product "{name}" --sprint {N} --details "$(cat /tmp/retro_summary.html)"
```

Replace all `{placeholders}` with real data from the retro document before sending.

### Step 3: Production Health Check
Use /tools:error-trace to check for real production errors since deployment.
If real issues found: Use /workflows:incident-response to triage.

### Step 4: Technical Debt Assessment (informed by retro)
Use /tools:tech-debt to scan the actual codebase.
Prioritize debt items that the retro identified as causing problems.
Also check:
- Real debt introduced this sprint (from actual code review)
- Existing debt that should be addressed
- Prioritized remediation recommendations

### Step 5: Dependency & Performance Health
Use /tools:deps-upgrade to check real dependencies.
If performance concerns exist:
- Use /workflows:performance-optimization to profile real bottlenecks
- Use /tools:cost-optimize to review actual cloud spend

### Step 6: Agent Performance Review (informed by retro)
Use /workflows:improve-agent to evaluate based on retro findings:
- Which agents produced quality output vs. document-only output
- Token efficiency data from the retro
- Which agents hit retry limits and why
- Prompt adjustments needed to improve next sprint
- Update VP prompts in `reference/phase_prompts/` if needed

### Step 7: Backlog Update
Read current backlog.json and update:
- Mark completed epic as done
- Add retro action items as backlog tickets
- Add new items from: real tech debt findings, real market intel, real production issues
- Reprioritize based on evolution findings
- Select next epic for upcoming sprint

### Step 8: Update WORKING_CONTEXT.md (Full Rewrite)
Rewrite WORKING_CONTEXT.md as a clean context for the next sprint:
- Update "Where We Are Right Now" to reflect the new sprint
- Move completed decisions to a "Previous Sprint Decisions" section
- Update "What's Been Built" with everything from this sprint
- Clear resolved blockers
- Set the new sprint goal from the selected epic

### Step 9: Save & Commit Everything
Use /tools:context-save to persist architectural decisions and lessons.

Commit all `.claude-engine/` files to git:
```bash
cd {repo}
git add .claude-engine/
git commit -m "chore(engine): sprint {N} evolution complete — retro, context, backlog updated"
git push origin {branch} 2>/dev/null || true
```

## Output
Write to {workspace}/reviews/retrospectives/:
- sprint-retro-{sprint_N}.md (from /sprint-retro skill)
- sprint_{N}_summary.md (overall evolution summary)

Update:
- {workspace}/state/backlog.json (new items, reprioritized, retro action items added)
- {workspace}/WORKING_CONTEXT.md (full rewrite for next sprint)
- Gmail draft sent to dean@try-insite.com

## State Update
Update {workspace}/state/company_state.json:
- Set `sdlc.phases.evolution.status` to `"complete"`
- Set `sdlc.phases.evolution.completed_at` to current UTC ISO timestamp (with Z suffix)

The COO will detect "evolution complete" on next cycle and loop back to Phase 1: Planning.
