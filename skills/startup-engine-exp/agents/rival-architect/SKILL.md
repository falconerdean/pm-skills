---
name: rival-architect
description: >
  Independent rival technical architect for Phase 5 (Tech Design). Produces a competing
  architecture from the same project brief that the primary VP Engineering used —
  structurally isolated from the primary's architecture document, requirements interpretation,
  or reasoning chain. After both architectures exist, a deterministic comparison script
  surfaces structural disagreements (data model differences, API surface differences,
  dependency divergence) and escalates judgment-level differences to the CEO. Triggers
  automatically after Phase 5 produces architecture.md. Not for code review (use
  multi-agent-review), not for fact verification (use silent-observer), not for business
  outcome review (use business-reviewer). Built as a wrapper-script protocol — the calling
  COO cannot bypass independent-first-response by modifying prompts or merging context.
# user-invocable: true
# disable-model-invocation: false
# allowed-tools: [Read, Grep, Glob, WebFetch, WebSearch]
# context: fork
# agent: general-purpose
# model: opus
# effort: high
---

# Rival Architect

## Core Rule

**Two architectures, produced independently from the same brief, by models with different training lineages. Then compared, never debated.**

The Rival Architect does NOT review the primary VP Engineering's architecture document. It does NOT critique it, suggest improvements to it, or even read it. It produces its OWN architecture from scratch, starting from exactly the same inputs the primary architect had: the sprint goal, the product description, the discovery brief (already verified by Silent Observer at Phase 2), the requirements (`stories.json`, `prd.md`), and the UX design (`ui_spec.md`, `ux_flows.md`, `content_spec.md`).

After both architectures exist on disk, a separate comparison script identifies structural agreements and disagreements. Substantive disagreements are escalated to the CEO. The system never asks one model to evaluate the other's work — that pattern (Option 4 handoff dialogue from the Teams of Rivals research) consistently degrades accuracy because confident wrong answers can talk correct answers into being wrong.

## Why This Exists

The Sprint 11 Stitch failure cascade happened because a primary researcher hallucinated an SDK method and no one verified it. The Silent Observer at Phase 2 catches that class of failure. But the next class of failure — and the one Sprint 7 hit hardest — is **architectural decisions built on training-data assumptions about how libraries work, what concurrency models a runtime supports, or what compatibility constraints exist between dependencies.**

The Milvus 2026 multi-agent benchmark (53% → 80% bug detection with multi-model rivalry) found that Claude scores 0/2 on concurrency races where Gemini scores 1/2. Claude is excellent at deep system-level reasoning but blind to specific compatibility and concurrency issues that Gemini catches because of different training data. Pairing Claude + Gemini covers 91% of the bug-detection ceiling — not because either is "better" but because their blind spots are complementary.

The research is also clear about what NOT to do: **do not feed Claude's architecture to Gemini and ask "what's wrong with this?"** That is Option 4 handoff dialogue, and the data shows convergence in debate degrades accuracy. The correct pattern is **independent first response** — both architects produce their work from the same brief, without seeing each other's output, and then a separate comparison surfaces the differences.

See `research/business_objective_evaluation_research_2026-04-10.md` Section 6 (the reviewer bias problem) and Dean's Teams of Rivals synthesis (referenced in `reference/research_basis.md`).

---

## When to Use

- **Phase 5 (Tech Design)** — automatically after VP Engineering completes `architecture.md`, `api_spec.json`, and `db_schema.sql`. Before Phase 5.5 (Credential Verification).

## When NOT to Use

- For code review of implementation — use `multi-agent-review` or the existing `review_debate.py`
- For fact verification of research claims — use `silent-observer` (Phase 2)
- For business outcome review — use `business-reviewer`
- For UX review — use the (future) UX rival or accessibility-audit
- When the architecture is trivial (single-page form, static site, no integrations) — the rival cost outweighs the value

---

## The Two-Phase Protocol

### Phase A: Parallel Production (Independent First Response)

The primary VP Engineering (Claude Opus) writes architecture artifacts following the existing Phase 5 flow:
- `{workspace}/artifacts/designs/{epic}/tech/architecture.md`
- `{workspace}/artifacts/designs/{epic}/tech/api_spec.json`
- `{workspace}/artifacts/designs/{epic}/tech/db_schema.sql`

The COO then invokes `scripts/invoke_rival_architect.py`. The wrapper script:

1. Loads inputs from a fixed allowlist of paths — sprint goal, product description, discovery brief, requirements, design spec. **Does NOT load** any of the primary's tech output (architecture.md, api_spec.json, db_schema.sql) or any reasoning trace.
2. Loads the static system prompt from `reference/system_prompt.md`.
3. Constructs API messages in protocol order: anchor (goal) → context (brief + requirements + design) → task (produce architecture).
4. Calls `gemini-3-pro` (fixed model, no fallback to Claude family).
5. Validates the response: must include all three artifacts, each must parse, architecture.md must contain required sections.
6. Writes the rival's artifacts to a separate directory: `{workspace}/artifacts/designs/{epic}/tech/rival/`.
7. Logs to `logs/rival_architect_calls.jsonl`.

The rival artifacts are produced WITHOUT the rival ever seeing the primary's work. This is the structural defense against anchoring (Talk Isn't Always Cheap, arXiv:2509.05396).

### Phase B: Deterministic Comparison + Constrained Judgment Escalation

After both architectures exist on disk, the COO invokes `scripts/compare_architectures.py`. The compare script:

1. Reads both `architecture.md` files.
2. Reads both `api_spec.json` files.
3. Reads both `db_schema.sql` files.
4. **Deterministic structural diff** (Python code, no LLM):
   - **Database schema:** parse both SQL files, extract table and column sets, compute symmetric difference. Tables in both, tables only in Claude's, tables only in Gemini's. For tables in both, diff the column sets.
   - **API surface:** parse both JSON specs, extract endpoint paths and HTTP methods, compute symmetric difference. Endpoints in both, only in Claude's, only in Gemini's. Mismatched methods on the same path are flagged.
   - **Required sections:** check that both architecture.md files include the canonical sections (Data Model, API Surface, Authentication, Authorization, Deployment, Observability, Concurrency, Error Handling). Missing sections are flagged.
   - **Dependencies:** regex-extract package mentions (`npm install X`, `pip install X`, `from X import`) and compute the union and differences.
   - **Concurrency/compatibility keywords:** count mentions of `concurrent`, `race condition`, `rate limit`, `async`, `compatibility`, `version` in both. If Gemini's mentions these substantially more than Claude's, flag — this is the Milvus pattern where Gemini catches what Claude misses.
5. **Constrained LLM call** (Claude Opus, but bounded):
   - Sends a condensed comparison summary to Claude with the explicit instruction: *"These are two independently-produced architectures for the same problem. List substantive disagreements — not style, naming, or phrasing differences. For each disagreement, state the specific difference and which aspects warrant CEO review. You MUST NOT decide which architecture is better. You MUST NOT add your own opinion. Only surface what the two architects disagreed on so the CEO can decide."*
   - Returns a structured JSON list of substantive disagreements.
6. **Verdict computation** (deterministic, not LLM):
   - **APPROVE** — both architectures parse, share structural decisions, no substantive disagreements
   - **FLAG** — minor structural differences (different naming, slightly different schemas with no functional impact); advance Phase 5 with flags attached
   - **ESCALATE** — substantive disagreements exist on database choice, API pattern, auth model, concurrency model, deployment target, or any decision where one architect made a load-bearing choice the other didn't make; pause Phase 5, email CEO with both architectures and the comparison report
   - **BLOCK** — one or both architectures fail structural validation (invalid SQL, invalid JSON spec, missing required sections); return to the failing architect's owner

7. Writes the comparison report to `{workspace}/artifacts/reviews/architecture_comparison/{epic}_{timestamp_utc}.md`.
8. Updates `state/company_state.json` with `rival_architect.phase5.verdict`.
9. Returns the verdict to the COO via stdout JSON.

---

## Hard Rules (Enforced by the Wrapper Script, Not by the Prompt)

1. **The rival NEVER sees the primary's tech output.** The wrapper's input allowlist excludes `architecture.md`, `api_spec.json`, and `db_schema.sql` from `artifacts/designs/{epic}/tech/`. The rival reads only from the parent design directory and earlier-phase artifacts.

2. **The rival is not given the primary's reasoning.** No handoff notes, no self-assessments, no "VP Engineering's notes." The script's input list is hardcoded.

3. **The rival uses a fixed model: `gemini-3-pro`.** No fallback to Claude-family models. If Gemini is unreachable, the script halts with `RIVAL_ARCHITECT_UNAVAILABLE` and the COO escalates to CEO. We deliberately do not fall back because the whole point is different training lineage.

4. **Goal-before-context-before-task ordering.** The first message to Gemini is the sprint goal alone. The second message is the brief + requirements + design. The third message is the production task. The model anchors on the goal because that's all it sees first.

5. **The compare script is deterministic where possible.** Structural diffs (tables, endpoints, dependencies) are Python code. Only judgment-level differences require an LLM call, and that call is constrained to "surface differences, do not decide which is right."

6. **Comparison output never says one architecture is "better" than the other.** The compare script's job is to surface disagreements. The CEO decides. If the system ever auto-resolves a substantive disagreement, the protocol has failed.

7. **Both architectures must parse for an APPROVE verdict.** If Claude's SQL doesn't parse, BLOCK. If Gemini's JSON spec is malformed, BLOCK. Both must clear structural validation independently.

8. **The CEO must see both architectures on ESCALATE.** The compare report includes paths to both, and the CEO email includes a side-by-side summary. The CEO never decides based on the compare script's summary alone — they always have access to the full source documents.

---

## Output Contract

| Deliverable | Format | Location | Requirements |
|---|---|---|---|
| Rival architecture | Markdown | `{workspace}/artifacts/designs/{epic}/tech/rival/architecture.md` | Same canonical sections as primary architecture |
| Rival API spec | JSON | `{workspace}/artifacts/designs/{epic}/tech/rival/api_spec.json` | Valid JSON, endpoints with methods + request/response shapes |
| Rival DB schema | SQL | `{workspace}/artifacts/designs/{epic}/tech/rival/db_schema.sql` | Valid SQL, parseable CREATE TABLE statements |
| Comparison report | Markdown | `{workspace}/artifacts/reviews/architecture_comparison/{epic}_{YYYYMMDD_HHMMSSZ}.md` | Structural diff + judgment surface + verdict |
| State update | JSON write | `{workspace}/state/company_state.json` | `rival_architect.phase5.verdict`, `rival_architect.phase5.report_path`, `rival_architect.phase5.escalation_required` |
| Audit log | JSONL append | `{workspace}/logs/rival_architect_calls.jsonl` | Timestamps, model, hashes, verdict |
| CEO email (if ESCALATE) | HTML via GHL | `dean@try-insite.com` | Subject: `[Escalate] {product} — Phase 5 architectures diverge`; body lists substantive disagreements with paths to both source documents |

### Required Sections in the Comparison Report

1. **Header** — epic, timestamp, both architecture paths, both model IDs
2. **Structural Diff Summary** — table counts, endpoint counts, dependency counts (intersection and difference)
3. **Database Schema Comparison** — tables in both, only in Claude's, only in Gemini's; column-level diffs for shared tables
4. **API Surface Comparison** — endpoints in both, only in Claude's, only in Gemini's; mismatched methods on shared paths
5. **Required Section Coverage** — checklist of canonical architecture sections, present in each
6. **Dependency Comparison** — packages in both, only in Claude's, only in Gemini's
7. **Concurrency/Compatibility Coverage** — keyword counts; flag if asymmetric
8. **Substantive Disagreements** — judgment-level differences identified by the constrained LLM call
9. **Verdict** — APPROVE | FLAG | ESCALATE | BLOCK
10. **CEO Decision Required (if ESCALATE)** — specific questions for the CEO with both architects' positions

---

## Anti-Simulation Rules

The rival's architecture must contain real, testable artifacts. The wrapper script's response validator rejects:

- Architecture sections labeled "TBD", "to be determined", "in a real implementation"
- API spec endpoints with empty `parameters` or `responses` arrays
- SQL schema files with `-- TODO: define schema` placeholders
- Architecture.md prose like "the system would typically use" or "you could use"
- Missing required sections from the canonical list

If any of these patterns appear, the wrapper rejects the response and retries once with explicit instructions. Second failure halts the review.

---

## Error Recovery

### Recoverable
- Gemini API transient error: retry once with exponential backoff
- One artifact (e.g., db_schema.sql) is missing from the response: re-prompt with the specific missing artifact requested
- LLM judgment call returns malformed JSON: retry with stricter format instructions

### Unrecoverable (halt with diagnostics)
- `GEMINI_API_KEY` missing: halt, `RIVAL_ARCHITECT_UNAVAILABLE`, email CEO. Do NOT silently fall back to Claude.
- Both retries of the rival production fail validation: halt, write diagnostics, email CEO
- Compare script cannot parse one of the architectures: halt, return BLOCK with the parse error
- The primary's tech output directory doesn't exist (Phase 5 didn't complete): halt with `PHASE5_PRIMARY_INCOMPLETE`

### Halt Protocol
Write diagnostics to `{workspace}/logs/rival_architect_halts/{timestamp_utc}.md` with full context.

---

## Integration Point: Phase 5 Tech Design

### Current Phase 5 Flow (before Rival Architect)

```
VP Engineering completes architecture.md + api_spec.json + db_schema.sql
  ↓
COO detects all three exist
  ↓
COO advances to Phase 5.5 (Credential Verification)
```

### New Phase 5 Flow (with Rival Architect)

```
VP Engineering completes architecture.md + api_spec.json + db_schema.sql
  ↓
COO detects all three exist
  ↓
COO invokes scripts/invoke_rival_architect.py --workspace {} --epic {}
  ↓
Wrapper produces rival/{architecture.md, api_spec.json, db_schema.sql} via Gemini 3 Pro
  ↓
COO invokes scripts/compare_architectures.py --workspace {} --epic {}
  ↓
Compare script reads both, runs structural diff + constrained judgment surface, writes verdict
  ├── APPROVE → Phase 5 advances to Phase 5.5
  ├── FLAG    → Phase 5 advances with comparison report attached
  ├── ESCALATE → Phase 5 PAUSES; CEO email sent with both architectures + disagreements; wait for /btw approve
  └── BLOCK   → Phase 5 returns to VP Engineering with the failing architecture's specific issues
```

### SDLC Protocol Update Required

Add to `skills/startup-engine-exp/reference/sdlc_protocol.md` in the Phase 5 TECH_DESIGN section:

> **Rival Architect Gate (NEW — Sprint 12 Rule):** After VP Engineering produces architecture.md + api_spec.json + db_schema.sql, the COO MUST invoke `scripts/invoke_rival_architect.py` followed by `scripts/compare_architectures.py` before advancing to Phase 5.5. Both scripts use the wrapper-script protocol pattern (fixed model, fixed input paths, structural validation, deterministic verdict). On ESCALATE, Phase 5 pauses and CEO must approve a direction via /btw before advancing. On BLOCK, the failing architect's work is returned with specific structural issues. Three-strikes rule applies.

---

## Reference Files (loaded on demand)

- `reference/system_prompt.md` — the static Rival Architect system prompt (loaded by the wrapper, not the COO)
- `reference/architecture_schema.md` — what a complete architecture must contain (the canonical sections checklist)
- `reference/comparison_protocol.md` — the structural diff rules and the constrained LLM judgment prompt
- `reference/research_basis.md` — pointer to research/business_objective_evaluation_research_2026-04-10.md and Dean's Teams of Rivals synthesis

## Scripts

- `scripts/invoke_rival_architect.py` — the wrapper script that produces the rival architecture (the load-bearing artifact)
- `scripts/compare_architectures.py` — the comparison script that produces the verdict

## Tests

- `tests/test_rival_wrapper_protocol.py` — proves the rival wrapper enforces the structural protocol
- `tests/test_compare_architectures.py` — proves the compare script's structural diffs are correct and the verdict logic is deterministic

## Examples

- `examples/divergent_architectures.md` — example where Claude and Gemini reached substantively different conclusions; shows ESCALATE verdict
- `examples/convergent_architectures.md` — example where they reached structurally equivalent architectures; shows APPROVE verdict

---

## What This Catches That Other Reviewers Do Not

| Failure mode | Caught by |
|---|---|
| Code that doesn't compile | `multi-agent-review` (existing) |
| Hallucinated SDK method in research | `silent-observer` Phase 2 (existing) |
| User cannot complete journey | Strict E2E gate (existing) |
| User completes journey but no business impact | `business-reviewer` Phase 7c |
| **Architectural decision built on Claude's training-data assumption about a library** | **Rival Architect Phase 5** |
| **Concurrency model that works in theory but fails in production for the chosen runtime** | **Rival Architect Phase 5** (Gemini's documented strong suit per Milvus) |
| **Database schema that mirrors Claude's typical patterns but doesn't fit the use case** | **Rival Architect Phase 5** (Gemini may model the data differently) |
| **API surface that assumes a pattern Claude is biased toward (REST vs GraphQL preference, naming conventions, error code conventions)** | **Rival Architect Phase 5** |
| **Single-vendor lock-in not surfaced because Claude's training data favored that vendor** | **Rival Architect Phase 5** (Gemini may default to a different vendor and surface the choice) |

The Rival Architect is the only place in the SDLC where two genuinely different model lineages independently produce the same artifact and a structural comparison is run. Code review (multi-agent-review) compares opinions about the same code; the Rival Architect compares two independently-conceived implementations.

---

## Limitations

1. **The compare script's structural diff is heuristic.** Regex-based SQL parsing handles standard CREATE TABLE syntax but may miss exotic patterns. JSON parsing for api_spec assumes a roughly OpenAPI-like structure. If the architecture uses unusual formats, the diff degrades to checking presence rather than structure.

2. **The constrained LLM call uses Claude.** This re-introduces a self-enhancement risk if the comparison ever asks "which is better." The prompt is explicitly engineered to forbid that — it only asks for surfacing disagreements. But the risk is non-zero. Long-term, this call should move to a third-party model (GPT-5 or local) to fully eliminate the bias path.

3. **The rival's quality depends on the brief quality.** If the discovery brief is vague, both architectures will be vague. The Rival Architect cannot manufacture clarity that the upstream phases didn't produce. (The Silent Observer at Phase 2 is the structural defense for brief quality.)

4. **The rival uses 1 API call per Phase 5 invocation, plus 1-2 calls for the compare script.** Per Dean's instruction, cost is not a concern — but for awareness, a typical Phase 5 review will cost ~$5-15 in API spend, depending on architecture complexity.

5. **`GEMINI_API_KEY` must be in the environment.** Without it, the script halts. We deliberately do not fall back. If Gemini is unavailable for an extended period, Phase 5 cannot advance — the CEO will need to either wait, manually approve a single-architect verdict, or temporarily disable the gate via project_config.json.

6. **The comparison script does not run end-to-end build verification.** It compares the architecture documents, not the actual buildability. If both architects produce structurally similar but mutually unbuildable architectures, the comparison passes and Phase 6 (Development) catches the failure. The future enhancement would be to actually run a "smoke build" on each architecture's stack — out of scope for Tier 2.
