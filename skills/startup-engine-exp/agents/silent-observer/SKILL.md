---
name: silent-observer
description: >
  Fresh-eyes fact verifier for research deliverables. Reads the discovery brief COLD — no access
  to the primary researcher's search history, tool calls, or reasoning chain — and independently
  verifies specific factual claims (SDK methods, library capabilities, market stats, regulatory
  requirements, company facts). Triggers automatically at Phase 2 after discovery_brief.md is
  written and before phase advancement. Not for business outcome review (use business-reviewer),
  not for code review (use multi-agent-review), not for user journey verification (use E2E
  testing agent). Built as a wrapper script that enforces epistemic isolation structurally —
  the calling COO cannot bypass the protocol by modifying the prompt.
# user-invocable: true
# disable-model-invocation: false
# allowed-tools: [Read, WebFetch, WebSearch, Grep]
# context: fork
# agent: general-purpose
# model: opus
# effort: high
---

# Silent Observer

## Core Rule

**The primary researcher's reasoning is contagious. Read the brief cold and verify the claims from scratch.**

This agent exists to catch the failure mode where a research deliverable contains fabricated facts — most commonly hallucinated SDK methods, library capabilities that don't exist, or market statistics invented by the primary researcher's training data rather than found in the real world. When those facts enter the discovery brief, every downstream agent trusts them, and the entire sprint can be built on a false premise.

The Silent Observer's job is to read the brief as if no prior research existed, identify every specific factual claim, and independently verify each one. It does NOT participate in the research process, debate the primary researcher, or offer alternative framings. It only answers one question per claim: **does this thing actually exist as stated?**

## Why This Exists

Sprint 11 lost three sprints to a single hallucinated SDK method. A research report claimed "Stitch SDK has an `extractUrl()` method." Sprint 9 built around it. Sprint 10 discovered the problem but rationalized a pivot. Sprint 11 ran the retrospective and documented the cascade. The root cause was that no one verified the claim at the time the research doc crystallized it — the downstream agents trusted the prior work. A Silent Observer reading that brief cold, with no access to the primary researcher's reasoning, would have searched for `extractUrl()` in the Stitch docs, failed to find it, and BLOCKED the phase. Three sprints saved.

The research supporting this pattern comes from the Milvus 2026 multi-agent benchmark, which found that a "silent observer" model that "barely said a word" caught the single most important bug because it wasn't anchored by the group's prior discussion. Convergence in debate correlates with performance degradation (arXiv:2509.05396). The observer's value comes precisely from not participating in the discourse that led to the artifact.

See `research/business_objective_evaluation_research_2026-04-10.md` Section 6 for the reviewer bias literature and Section 7 for the Agent-as-a-Judge precedent.

---

## When to Use

- **Phase 2 (Research)** — automatically after `discovery_brief.md` is written by VP Product Research, before COO advances to Phase 3. This is the primary integration point.
- On CEO request: `/btw fact-check research` or "verify the research brief"

## When NOT to Use

- For business outcome review — use `business-reviewer`
- For code review — use `multi-agent-review` or `review_debate.py`
- For rendering verification — use `proof-of-change`
- For user journey verification — use the E2E testing agent
- For architectural review — use the (future) `technical-viability-reviewer` at Phase 5
- On artifacts that contain no factual claims about external reality — infrastructure refactors, internal process docs, retrospectives

---

## The Protocol (Enforced by the Wrapper Script, Not by the Prompt)

This is the critical design decision. Every rule below is enforced by `scripts/invoke_silent_observer.py` — the calling COO cannot violate them by modifying prompts or adding "helpful context." The protocol is code, not instruction.

### Rule 1: Inputs Are Whitelisted, Not Blacklisted

The wrapper script reads exactly three things from disk and passes them to the model:

1. **The product description** — from a fixed path: `{workspace}/state/project_config.json`, specifically the `product_description` field. Nothing else from that file.
2. **The discovery brief** — from a fixed path pattern: `{workspace}/artifacts/research/{epic}/discovery_brief.md`.
3. **The product goal** — from a fixed path: `{workspace}/state/sprint_plan.json`, specifically the `goal` field.

The script does NOT read and does NOT pass:
- The primary researcher's search history
- The primary researcher's tool call logs
- Any `*self_assessment*`, `*handoff*`, `*summary_for_*`, or `*restatement*` files
- Conversation transcripts from prior phases
- Any file the primary researcher created other than the discovery brief itself

This is enforced by the wrapper reading from explicit absolute paths. The calling COO cannot pass additional context as a function argument — the function signature does not accept one.

### Rule 2: Goal Before Context, Always

The wrapper script structures the outbound API call in this exact order:

1. **System message:** The Silent Observer system prompt (static, loaded from `reference/system_prompt.md`). This defines the role and the six rules below.
2. **First user message:** The product goal, alone. "The goal of this sprint is: {goal text}. Your job is to verify factual claims in the research brief that follows, against this goal as the anchor."
3. **Second user message:** The discovery brief content, labeled. "Here is the discovery brief to verify: {brief contents}"
4. **Third user message:** The task. "Identify every specific factual claim in the brief (SDK methods, library capabilities, market statistics, regulatory requirements, company facts, pricing, technical constraints). For each claim, independently verify using WebSearch or WebFetch. Classify as VERIFIED, UNVERIFIABLE, or CONTRADICTED. Produce a report matching the schema in the system prompt."

This structural ordering is the code-level enforcement of "context comes after unadulterated goals." The model anchors on the goal first because that's all it sees first. Anchoring is unavoidable; by controlling what the model anchors on, we make the anchoring work for us instead of against us.

### Rule 3: Fixed Model, No Fallback

The wrapper script uses a fixed model ID: **`gemini-3-pro`**. Rationale from the Teams of Rivals research: Gemini has the most different training lineage from Claude (Milvus benchmark shows Claude + Gemini covers 91% of the bug-detection ceiling specifically because their blind spots are complementary). A Claude-family model reviewing Claude-generated research would suffer correlated blind spots.

If Gemini 3 Pro is unreachable, the wrapper script FAILS the review with `SILENT_OBSERVER_UNAVAILABLE` and the COO does NOT silently fall back to Claude. The phase does not advance. The CEO is notified.

### Rule 4: Every Claim Must Have a Verification Attempt

The wrapper script validates the response before returning. Each identified claim must have:
- A specific quote from the brief (copyable and findable)
- A verification method attempted (WebSearch query text, WebFetch URL, or grep pattern)
- A verification result (what was found, including null findings)
- A verdict: VERIFIED | UNVERIFIABLE | CONTRADICTED

Claims without all four fields cause the script to reject the response and retry once. A second failure halts the review and reports the schema violation.

### Rule 5: Load-Bearing Contradictions Are Blocking

A claim is "load-bearing" if any downstream phase (architecture, development, testing) would need it to be true for the work to succeed. Example load-bearing claims:

- "Stitch SDK has `extractUrl()` method" — load-bearing if the architecture will call this method
- "Stripe's API rate limit is 100 requests/second" — load-bearing if the system is designed around this limit
- "HIPAA requires encryption at rest for PHI" — load-bearing if the architecture depends on this requirement

The Silent Observer marks each CONTRADICTED or UNVERIFIABLE claim as `load_bearing: true | false`. The wrapper script's decision logic:

- Any `load_bearing: true` AND `verdict: CONTRADICTED` → BLOCK
- Any `load_bearing: true` AND `verdict: UNVERIFIABLE` → BLOCK
- Any `load_bearing: false` AND `verdict: CONTRADICTED` → FLAG
- Any `load_bearing: false` AND `verdict: UNVERIFIABLE` → FLAG
- All claims VERIFIED or flagged-only → APPROVE

### Rule 6: Audit Every Call

The wrapper script appends to `{workspace}/logs/silent_observer_calls.jsonl` on every invocation:
- UTC timestamp
- Model ID used
- Input hash (sha256 of the concatenated input messages)
- Output hash (sha256 of the response)
- Number of claims identified
- Number of each verdict type
- Final decision (APPROVE / FLAG / BLOCK)
- Path to the full report

This log is how we later audit whether the Silent Observer is actually catching real hallucinations or producing false positives. It is also how a future convergence detector (Phase 2 enhancement) will learn which patterns of contradiction predict real problems.

---

## Workflow (What the Wrapper Script Orchestrates)

1. **Setup** (the script, not the model): Read the three whitelisted inputs from disk. Validate they exist and are non-empty. If any required input is missing, halt with a specific error.

2. **First API call** (model: gemini-3-pro): Extract factual claims from the brief. The model returns a JSON array of claims with quotes and initial classifications. No verification yet — just extraction.

3. **Verification loop** (model: gemini-3-pro, with WebSearch + WebFetch tool access): For each extracted claim, the model independently searches and fetches evidence. The model's tool access is scoped — it can search the web and fetch URLs, but cannot read files from the workspace (enforced by the wrapper not passing those tools).

4. **Classification**: For each claim, the model produces a verdict (VERIFIED / UNVERIFIABLE / CONTRADICTED) with evidence quoted from the search/fetch result. The model also classifies `load_bearing: true | false`.

5. **Validation** (the script, not the model): The wrapper validates the response structure. If any claim is missing required fields, retry once. Second failure halts.

6. **Decision** (the script, not the model): Apply Rule 5 to compute the overall verdict. This is deterministic code, not an LLM judgment.

7. **Report writing** (the script): Write the full report to `{workspace}/artifacts/reviews/silent_observer/{epic}_{timestamp_utc}.md` using the template at `templates/verification_report.md`.

8. **Audit log** (the script): Append to `logs/silent_observer_calls.jsonl`.

9. **Return** (to the COO): A structured verdict object. The COO does not see the raw API response — only the validated structured output.

10. **COO action** (per the decision): On BLOCK, return Phase 2 to VP Product Research with the contradicted claims as required fixes. On FLAG, advance Phase 2 with flags attached. On APPROVE, advance Phase 2 cleanly.

---

## Output Contract

| Deliverable | Format | Location | Requirements |
|---|---|---|---|
| Verification report | Markdown | `{workspace}/artifacts/reviews/silent_observer/{epic}_{YYYYMMDD_HHMMSSZ}.md` | One entry per factual claim with quote, verification method, result, verdict, load-bearing flag |
| Audit log entry | JSONL append | `{workspace}/logs/silent_observer_calls.jsonl` | Timestamps, hashes, counts, decision |
| State update | JSON write | `{workspace}/state/company_state.json` | `silent_observer.phase2.verdict`, `silent_observer.phase2.report_path` |
| CEO email (if BLOCK) | HTML via GHL MCP | `dean@try-insite.com` | Subject: `[Block] {product} — Silent Observer caught fact issues in research`; body lists contradicted/unverifiable load-bearing claims with evidence |

### Required Sections in the Verification Report

1. **Header** — epic, sprint, timestamp UTC, model used, input hashes
2. **Summary** — total claims extracted, count by verdict type, count by load-bearing
3. **Verdict** — APPROVE | FLAG | BLOCK
4. **Claim-by-claim log** — for each claim: quote, source line, type (SDK/library/market/regulatory/company/pricing/technical), verification method, verification result, verdict, load-bearing flag, impact if wrong
5. **Blocking claims** (if any) — the subset that drove a BLOCK verdict, with specific required actions
6. **Flag claims** — the subset that are UNVERIFIABLE or CONTRADICTED but not load-bearing
7. **Verified claims** — the claims that passed (brief summary, not full repetition)

---

## Anti-Simulation Rules

If any part of the verification report contains these phrases, the report has FAILED and must be regenerated:

- "This claim seems reasonable..."
- "In a real implementation..."
- "You would typically..."
- "The team should verify..."
- "Based on my training data..." (the Silent Observer must verify externally, not from training)
- Any verdict of VERIFIED without a quoted search result or fetched document
- Any verdict of CONTRADICTED without quoting the contradicting evidence
- Paraphrased quotes rather than verbatim extracts

The wrapper script's validation layer detects these patterns and rejects the response.

---

## Error Recovery

### Recoverable (retry or degrade gracefully)
- Gemini API transient error (timeout, 5xx): retry once with exponential backoff
- Single claim verification fails (search returned nothing): mark UNVERIFIABLE with explanation, do not fail the whole review
- Response schema validation fails on first try: return to the model with the schema error and ask for re-format

### Unrecoverable (halt with diagnostics)
- Gemini API key missing or invalid: halt, `SILENT_OBSERVER_UNAVAILABLE`, email CEO
- Gemini API persistent 4xx errors (auth, quota): halt, `SILENT_OBSERVER_UNAVAILABLE`, email CEO
- Discovery brief is missing or empty: halt, phase cannot be reviewed without a brief
- Response schema validation fails on second try: halt, report model output for manual review
- No factual claims identified in a brief that's >500 words: halt with warning — likely a model failure

### Halt Protocol
Write diagnostics to `{workspace}/logs/silent_observer_halts/{timestamp_utc}.md` with:
- Timestamp UTC
- Phase (always 2)
- Epic
- Exact error
- Last successful step
- Partial output if any
- Suggested next action

---

## Integration Point: Phase 2 Research

### Current Phase 2 Flow (before Silent Observer)
```
VP Product Research completes discovery_brief.md
  ↓
COO detects discovery_brief.md exists
  ↓
COO advances to Phase 3 (Requirements)
```

### New Phase 2 Flow (with Silent Observer)
```
VP Product Research completes discovery_brief.md
  ↓
COO detects discovery_brief.md exists
  ↓
COO invokes scripts/invoke_silent_observer.py --workspace {path} --epic {epic}
  ↓
Wrapper script runs protocol (goal → brief → task, fixed model, validated output)
  ↓
Wrapper returns verdict
  ├── APPROVE → COO advances to Phase 3
  ├── FLAG    → COO advances to Phase 3, attaches flags to phase output
  └── BLOCK   → COO does NOT advance. Returns Phase 2 to VP Product Research with contradicted claims as required fixes. Three-strikes rule applies.
```

### SDLC Protocol Update Required

Add to `skills/startup-engine-exp/reference/sdlc_protocol.md` in the Phase 2 RESEARCH section:

> **Quality Gate (Silent Observer):** After `discovery_brief.md` is written, the COO MUST invoke `scripts/invoke_silent_observer.py` before advancing to Phase 3. If the Silent Observer returns BLOCK, Phase 2 does NOT advance until the contradicted claims are fixed and re-verified. Three-strikes rule: after 3 BLOCKs on the same brief, escalate to CEO.

---

## Reference Files (loaded on demand)

- `reference/system_prompt.md` — the static Silent Observer system prompt (the wrapper script reads this and sends it as-is to the model)
- `reference/verification_protocol.md` — detailed mechanics of claim extraction and verification
- `reference/load_bearing_classification.md` — how to determine if a claim is load-bearing
- `reference/research_basis.md` — pointer to research/business_objective_evaluation_research_2026-04-10.md

## Templates

- `templates/verification_report.md` — output report structure

## Scripts

- `scripts/invoke_silent_observer.py` — the wrapper that enforces the full protocol. **This is the load-bearing artifact.** The SKILL.md is secondary documentation; the Python is the enforcement layer.
- `scripts/validate_verification_report.py` — validates an output report against the schema

## Tests

- `tests/test_wrapper_protocol.py` — unit tests verifying the wrapper enforces the structural protocol:
  - Cannot include self-assessment files
  - Reads from fixed source-of-truth paths
  - Sends goal before context before task
  - Uses fixed model ID
  - Validates response structure
  - Writes audit log

## Examples

- `examples/hallucinated_sdk_blocked.md` — what a BLOCK verdict looks like (based on the Sprint 11 Stitch case)
- `examples/clean_brief_approved.md` — what an APPROVE verdict looks like

---

## What This Catches That Other Reviewers Do Not

| Failure mode | Caught by |
|---|---|
| Code that doesn't compile | `multi-agent-review` / `review_debate.py` (existing) |
| User cannot complete journey | Strict E2E gate (existing) |
| User completes journey but no business impact | `business-reviewer` (Phase 7c) |
| **Research brief cites an SDK method that doesn't exist** | **Silent Observer (Phase 2)** |
| **Research brief contains fabricated market statistics** | **Silent Observer (Phase 2)** |
| **Research brief assumes a regulatory requirement that isn't real** | **Silent Observer (Phase 2)** |
| **Downstream phases build on a primary researcher's hallucination** | **Silent Observer (Phase 2)** |

The Silent Observer is the only agent in the pipeline whose job is "did the primary researcher tell us things that are actually true?" Every other reviewer assumes the research inputs are correct. The Silent Observer questions that assumption.

## Limitations

1. **Cannot verify proprietary or private information.** If the research brief cites internal company data, closed API documentation, or undocumented behavior, the Silent Observer cannot web-verify it. These should be marked UNVERIFIABLE with a note.

2. **Cannot verify judgment claims, only factual claims.** "X is the right approach for this use case" is judgment; "X exists and supports method Y" is fact. The Silent Observer only handles facts.

3. **Depends on Gemini 3 Pro availability.** When Gemini is unreachable, the review cannot run. We deliberately do NOT fall back to Claude — that would defeat the different-training-lineage purpose.

4. **Can be defeated by sufficiently obscure false claims.** If a hallucinated SDK method can't be easily refuted by a 30-second web search (e.g., the claim is about a rare edge case buried deep in documentation), the Silent Observer may return UNVERIFIABLE when it should return CONTRADICTED. The FLAG vs BLOCK distinction is a partial mitigation — UNVERIFIABLE load-bearing claims still block the phase.

5. **Does not catch logical errors in the research.** "If A, then B" where the reasoning is flawed — that's a different failure mode, not factual verification. The business-reviewer and future technical-viability-reviewer handle those.
