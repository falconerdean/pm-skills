---
name: sprint-retro
description: >
  Perform a structured sprint retrospective analyzing coding agent sessions. Use this skill
  whenever the user asks for a "retro", "retrospective", "post-mortem", "sprint review",
  "what went wrong", "implementation review", or wants to understand why a feature or set of
  stories didn't go as planned. Also trigger when the user asks to "review agent sessions",
  "analyze coding sessions", "audit the implementation", "trace issues back to requirements",
  or says things like "the feature took too long" or "the agent kept going in circles".
  This skill examines conversation JSON files from coding agent sessions, git commit history,
  the codebase itself, and product requirements to reconstruct what happened, identify root
  causes of problems, and produce actionable improvements.
---

# Sprint Retro: Coding Agent Session Analysis

You are conducting a structured retrospective that forensically examines how a coding agent
implemented a feature or set of stories. The goal is to understand what happened, why things
went wrong (or right), and what concrete changes would improve future outcomes.

This is not a generic team retro — it's an evidence-based audit that traces the path from
product requirements through agent conversations to final code, identifying where the
implementation diverged from intent and why.

## Step 1: Gather Inputs

Before you can analyze anything, you need to locate the evidence. Ask the user to point you
to the following (they may not have all of them, and that's fine — work with what's available):

1. **Product requirements** — PRDs, specs, tickets, user stories, acceptance criteria.
   These are the "ground truth" for what was supposed to be built.
2. **Conversation JSON files** — The raw session logs from the coding agent. These contain
   the full back-and-forth between the user and the agent, including tool calls, errors,
   and decision points.
3. **Git history** — The commits produced during the sprint. Use `git log`, `git diff`,
   and `git show` to reconstruct the timeline of code changes.
4. **The codebase** — The current state of the code, so you can assess the end result
   against the requirements.
5. **Any other context** — Slack threads, design docs, Sentry errors, deployment logs.

If the user has a project directory selected, proactively explore it:
- Look for conversation logs (commonly in `.claude/`, `.cursor/`, or similar directories,
  often as `.jsonl` or `.json` files)
- Run `git log --oneline --since="2 weeks ago"` (adjust timeframe based on user input)
- Search for requirement docs (`*.md`, `*.txt`, tickets, PRDs)
- Look for existing retro artifacts like `CLAUDE.md` files with lessons learned — these
  are extremely valuable because they encode hard-won knowledge from past sessions

### When conversation logs aren't available

Often the raw conversation JSONs have been lost or weren't saved. This is common and the
retro can still be very valuable. Adapt by:

1. **Lean on git history** — commits, diffs, and timestamps tell a rich story even without
   conversation logs. Look for patterns like repeated changes to the same file (rework),
   reverted commits, and long gaps between commits (stuck).
2. **Use existing documentation** — CLAUDE.md files, README lessons-learned sections, and
   architecture docs often encode the problems that were encountered.
3. **Interview the user** — They were there for every session. Ask structured questions:
   "What were the biggest time sinks?", "Where did the agent get stuck?", "What would
   you do differently?"
4. **Analyze the code itself** — Look for code smells that suggest rework: multiple
   similar utilities, commented-out approaches, TODO comments referencing past issues,
   overly defensive code that suggests past bugs.

## Step 2: Reconstruct the Timeline

Build a chronological picture of what actually happened. This is the backbone of the retro.

For each conversation session / coding agent run:
1. **Read the conversation JSON** and extract:
   - The user's initial prompt / goal for that session
   - Key decision points where the agent chose a direction
   - Errors, retries, and course corrections
   - Tool calls and their outcomes (especially failures)
   - How long the session ran and how many tool calls it made
2. **Correlate with git commits** — match conversation sessions to the commits they
   produced. Look at timestamps, commit messages, and changed files.
3. **Note the trajectory** — did the agent make steady progress, or did it spiral?
   Did it get stuck on something and burn tokens? Did it misunderstand the requirement?

Build this into a timeline table:

```
| When | Session/Commit | What Happened | Outcome |
|------|---------------|---------------|---------|
| ...  | ...           | ...           | ...     |
```

## Step 3: Compare Plan vs. Reality

Now that you have the timeline, compare it against the product requirements:

For each requirement / story / acceptance criterion:
- **Was it implemented?** (fully / partially / not at all)
- **Was it implemented correctly?** (does the code actually satisfy the intent?)
- **What was the cost?** (how many sessions, commits, and tokens did it take?)
- **Were there surprises?** (scope changes, technical blockers, misunderstandings)

Create a requirements traceability matrix:

```
| Requirement | Status | Sessions Spent | Key Issues |
|-------------|--------|---------------|------------|
| ...         | ...    | ...           | ...        |
```

## Step 4: Root Cause Analysis (5 Whys)

For each significant problem identified in Steps 2-3, apply the 5 Whys framework.
Focus on the issues that had the biggest impact — don't do a 5 Whys for every minor hiccup.

The 5 Whys works by repeatedly asking "why" until you reach a root cause that's actionable.
The key discipline is to keep going past the surface-level answer.

**Example:**
1. Why did the auth feature take 5 sessions instead of 1?
2. → Because the agent kept rewriting the middleware from scratch each session.
3. Why did it rewrite from scratch?
4. → Because the conversation context didn't carry over between sessions.
5. Why didn't context carry over?
6. → Because there was no summary document or architectural spec for the agent to reference.
7. Why was there no spec?
8. → Because the requirement was a one-liner with no implementation guidance.
9. Why was there no implementation guidance?
10. → Because the team assumed the agent would "figure it out" from the codebase.

**Root cause:** Underspecified requirements that rely on implicit knowledge the agent doesn't have.

Categorize each root cause into one of these buckets:
- **Requirements** — Ambiguous, incomplete, or missing specs
- **Context** — Agent lacked necessary context (architecture, conventions, prior decisions)
- **Technical** — Genuine technical difficulty, tooling limitations, or environment issues
- **Process** — Workflow problems (e.g., no review checkpoints, sessions too long)
- **Scope** — Feature was bigger than estimated, or scope crept during implementation

## Step 4b: Token & Cost Efficiency Analysis

For each conversation session, extract token usage data to quantify efficiency:

1. **Parse token counts** from conversation JSON files. Different agent platforms store this
   differently — look for fields like `usage`, `tokens`, `input_tokens`, `output_tokens`,
   `total_tokens`, or `cost` in the JSON structure. If exact token counts aren't available,
   estimate from message lengths.

2. **Identify waste patterns:**
   - **Retry loops** — The agent tried the same approach multiple times with minor variations.
     Count the tokens spent on each attempt after the first.
   - **Dead-end explorations** — The agent went down a path that was later abandoned entirely.
     Sum up all tokens from the abandoned approach.
   - **Redundant context** — The agent re-read the same files or re-explained the same things
     across sessions because there was no persistent memory.
   - **Overly verbose output** — The agent generated long explanations when the user just
     needed code changes.

3. **Calculate efficiency metrics:**
   - **Total tokens used** across all sessions for this feature
   - **Productive tokens** — tokens that contributed to the final working code
   - **Wasted tokens** — tokens spent on retries, dead ends, and abandoned approaches
   - **Efficiency ratio** — productive / total (higher is better)
   - **Cost estimate** — if token pricing is known, estimate the dollar cost and waste

4. **Add a "Token Efficiency" section** to the retro document:

```markdown
## Token & Cost Efficiency
| Metric | Value |
|--------|-------|
| Total tokens | X |
| Productive tokens (est.) | Y |
| Wasted tokens (est.) | Z |
| Efficiency ratio | Y/X% |
| Estimated cost | $N.NN |

**Biggest token sinks:**
1. [description of biggest waste area and token count]
2. [description of second biggest waste area and token count]
```

This analysis is inherently approximate — the line between "productive exploration" and
"waste" isn't always clear. Use your best judgment and flag estimates as estimates. The
goal is to give the team a sense of magnitude, not a precise accounting.

## Step 5: Process Breakdown Analysis

Look across all the issues for systemic patterns. This is where individual root causes
become organizational insights:

- **Communication gaps** — Were requirements clearly communicated to the agent? Did the
  user provide enough context in prompts? Were there handoff problems between sessions?
- **Agent limitations** — Did the agent hit known limitations (context window, tool
  availability, inability to run certain tests)? Could these have been anticipated?
- **Feedback loops** — How quickly were problems caught? Did issues compound because
  they weren't caught early? Were there review checkpoints?
- **Scope management** — Did the scope grow? Were there requirements that should have
  been split into smaller pieces?

## Step 6: Generate Action Items

Every retro needs to end with concrete, assignable actions. For each major finding,
produce an action item with:

- **What** — A specific, actionable change (not vague like "improve communication")
- **Why** — Which root cause(s) this addresses
- **Who** — The person or role responsible
- **When** — A target date or sprint for completion
- **How to verify** — How you'll know it worked

Focus on the highest-leverage changes. A retro that produces 3 strong action items is
better than one that produces 15 vague ones.

Good action items for coding agent retros often look like:
- "Create an ARCHITECTURE.md that documents the auth flow so future agent sessions have context"
- "Break stories over 5 points into sub-tasks with explicit acceptance criteria"
- "Add a pre-session checklist: paste the relevant spec section into the agent's first prompt"
- "Set up a CLAUDE.md with project conventions so the agent follows existing patterns"

## Step 7: Write the Retro Document

Produce a markdown document with these sections:

```markdown
# Sprint Retro: [Feature/Sprint Name]
**Date:** [date]
**Sprint/Period:** [timeframe]
**Participants:** [who was involved]

## Executive Summary
[2-3 sentences: what was built, what went well, what didn't, and the single biggest takeaway]

## Timeline
[The timeline table from Step 2]

## Requirements Traceability
[The matrix from Step 3]

## Root Cause Analysis
[5 Whys for each major issue, grouped by category]

## Token & Cost Efficiency
[Efficiency metrics table and biggest token sinks from Step 4b]

## Systemic Patterns
[Process breakdown findings from Step 5]

## Action Items
| # | Action | Addresses | Owner | Due | Verification |
|---|--------|-----------|-------|-----|-------------|
| 1 | ...    | ...       | ...   | ... | ...         |

## What Went Well
[Don't forget to call out what worked — this provides signal for what to keep doing]

## Raw Data
[Links to or summaries of the conversation logs, commits, and other evidence reviewed]
```

Save the document to the outputs directory as `sprint-retro-[feature-name].md`.

## Important Guidance

- **Be specific and evidence-based.** Every claim should reference a specific conversation,
  commit, or requirement. "The agent struggled" is useless. "In session 3, the agent made
  12 attempts to fix the JWT validation (commits abc123..def456) because the error message
  from the test runner was misleading" is useful.

- **Distinguish agent problems from people problems.** Sometimes the agent did something
  wrong. Sometimes the agent was set up to fail by bad requirements or missing context.
  The retro should clearly distinguish these because the fixes are different.

- **Quantify where possible.** How many sessions? How many commits? How many tokens burned
  on dead-end approaches? Numbers make the case for change more compelling than narratives.

- **Be constructive.** The goal is to improve future sprints, not to assign blame. Frame
  findings as opportunities for improvement.

- **Ask the user to fill gaps.** You'll inevitably hit points where the data doesn't tell
  the full story. Ask the user what happened — they were there and can provide context
  the logs don't capture.
