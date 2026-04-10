# Multi-Model Cross-Check Protocol

The cross-check protocol runs at high-stakes phases (Phase 7c) where two independent reviewer instances evaluate the same work and the COO compares verdicts.

**Purpose:** Defeat single-model bias (Zheng et al. MT-Bench 2023 — self-enhancement, position, verbosity bias) and sycophantic consensus collapse (arXiv:2509.05396 — multi-agent debate failure modes) by enforcing **blind independent scoring before any cross-talk**.

---

## Protocol

### Step 1: Spawn Both Reviewers

The COO spawns two reviewer instances simultaneously:

| Role | Model | System prompt | Question randomization seed |
|---|---|---|---|
| Primary | Opus 4.6 (or whatever the COO's primary is) | The standard `business-reviewer/SKILL.md` system prompt | Seed A |
| Secondary | Sonnet (different family if available, e.g., Gemini, GPT) | The standard `business-reviewer/SKILL.md` system prompt | Seed B (different from A) |

Both reviewers are given:
- The path to the same source-of-truth goal artifact
- The path to the same work being reviewed
- The randomization seed for their question selection

Both reviewers are NOT given:
- Each other's identity
- Each other's verdict
- Each other's reasoning
- Any sub-agent's self-assessment

The reviewers run in **parallel**, not sequentially. Sequential review would let the second reviewer see timing or resource patterns from the first.

### Step 2: Both Reviewers Score Independently

Each reviewer follows the standard workflow in `SKILL.md`:
1. Read the source-of-truth goal artifact
2. Read the work being reviewed
3. Select 6 questions from the pool using their randomization seed
4. Answer each with citations
5. Apply the decision tree
6. Produce a verdict with full report

Each reviewer writes its report to a separate file:
- Primary: `{workspace}/artifacts/reviews/business/phase7c_{epic}_{timestamp_utc}_primary.md`
- Secondary: `{workspace}/artifacts/reviews/business/phase7c_{epic}_{timestamp_utc}_secondary.md`

### Step 3: COO Compares Verdicts

After BOTH reports are written, the COO reads them and compares:

```
Primary verdict: [APPROVE | APPROVE_WITH_CONDITIONS | BLOCK]
Secondary verdict: [APPROVE | APPROVE_WITH_CONDITIONS | BLOCK]
```

### Step 4: Resolution Matrix

| Primary | Secondary | COO action |
|---|---|---|
| APPROVE | APPROVE | **APPROVE — high confidence.** Phase advances. Both reports archived. |
| APPROVE WITH CONDITIONS | APPROVE | **APPROVE WITH CONDITIONS** from primary. Conditions enforced. |
| APPROVE | APPROVE WITH CONDITIONS | **APPROVE WITH CONDITIONS** from secondary. Conditions enforced. |
| APPROVE WITH CONDITIONS | APPROVE WITH CONDITIONS | **APPROVE WITH UNION OF CONDITIONS.** Both sets of conditions must be met. |
| BLOCK | BLOCK | **BLOCK — high confidence.** Return to upstream agent with both block reports as input. |
| APPROVE | BLOCK | **ESCALATE TO CEO.** Disagreement on direction. Both reports + COO summary sent to CEO via GHL email. |
| BLOCK | APPROVE | **ESCALATE TO CEO.** Same as above. |
| APPROVE WITH CONDITIONS | BLOCK | **ESCALATE TO CEO.** Same as above. |
| BLOCK | APPROVE WITH CONDITIONS | **ESCALATE TO CEO.** Same as above. |

**No disagreement is auto-resolved.** Direction disagreements always escalate. This is intentional — if the two models disagree, the disagreement itself is signal that something is wrong, and the CEO should see both perspectives.

### Step 5: Comparison Document

The COO writes a comparison document at:

```
{workspace}/artifacts/reviews/business/phase7c_{epic}_{timestamp_utc}_comparison.md
```

Format:

```markdown
# Cross-Check Comparison: Phase 7c Business Review
**Epic:** {epic}
**Timestamp:** {YYYY-MM-DD HH:MM UTC}
**Primary model:** {model name + version}
**Secondary model:** {model name + version}

## Verdicts
- Primary: {APPROVE | APPROVE_WITH_CONDITIONS | BLOCK}
- Secondary: {APPROVE | APPROVE_WITH_CONDITIONS | BLOCK}
- Resolution: {agreement | disagreement → escalated}

## Question-by-Question Comparison

| Question | Primary Verdict | Secondary Verdict | Agreement? |
|---|---|---|---|
| Q1 Goal Anchor | PASS/FAIL | PASS/FAIL | Y/N |
| Q2 Outcome Trace | PASS/FAIL | PASS/FAIL | Y/N |
| Q3 Falsification | PASS/FAIL | PASS/FAIL | Y/N |
| Q4 Premortem | PASS/FAIL | PASS/FAIL | Y/N |
| Q5 Fragile Assumption | PASS/FAIL | PASS/FAIL | Y/N |
| Q6 Disconfirmation | PASS/FAIL | PASS/FAIL | Y/N |

## Citation Overlap

How many of the cited evidence quotes appear in BOTH reports?
- Total citations primary: N
- Total citations secondary: M
- Overlap: K
- Overlap percentage: K / max(N, M) * 100

(High overlap with same verdict = high confidence. Low overlap with same verdict = the two models found different evidence supporting the same conclusion, which is also high confidence. Same evidence with different verdicts = the models interpret the evidence differently, which is the most interesting case.)

## Disagreement Summary (if applicable)

- Primary's strongest reason: ...
- Secondary's strongest reason: ...
- Where they diverge: ...
- COO recommendation: escalate to CEO with full reports
```

---

## Why Blind Independent Scoring Matters

The 2025 paper *Talk Isn't Always Cheap: Understanding Failure Modes in Multi-Agent Debate* (arXiv:2509.05396) found that in multi-agent debate settings, **agent disagreement rate decreases as debate progresses, and this convergence correlates with performance degradation**. Stacking multiple reviewers who can see each other's opinions does not produce better judgment — it produces sycophantic consensus that is less accurate than a single reviewer.

The structural defense is: each reviewer scores blind, then verdicts are aggregated. No reviewer sees another's reasoning before producing its own.

This is the same discipline used in:

- **Intelligence community structured analytic techniques** — analysts produce independent assessments before group review (Heuer 1999)
- **Medical second opinions** — the second physician should not see the first's diagnosis before forming their own
- **Inter-rater reliability studies in research** — coders score independently, then agreement is measured

The protocol implements this discipline structurally. The randomization seed ensures the two reviewers ask different specific questions even though they're drawing from the same pool, so each reviewer is exercising independent judgment on slightly different evidence rather than running identical procedures.

---

## When NOT to Run Cross-Check

The cross-check protocol doubles review cost. Reserve it for:

- **Phase 7c (Business Outcome Review)** — always cross-checked. This is the highest-stakes review.

Single-reviewer config is acceptable for:

- **Phase 3 (Requirements)** — early review, cheap to re-run, lower stakes
- **Phase 10a (Sprint Retro action items)** — retrospective review, no immediate ship pressure
- **Ad-hoc CEO requests** — flexible, single reviewer is sufficient

If a single-reviewer review BLOCKS three times in Phase 3, escalate to a cross-check on attempt 4 before triggering the CEO escalation. This catches cases where the single reviewer is itself the problem (consistent false positive).

---

## Configuration

The cross-check is configured via `state/project_config.json`:

```json
{
  "business_reviewer": {
    "phase3_requirements": {
      "enabled": true,
      "cross_check": false,
      "primary_model": "opus"
    },
    "phase7c_outcome_review": {
      "enabled": true,
      "cross_check": true,
      "primary_model": "opus",
      "secondary_model": "sonnet"
    },
    "phase10a_retro": {
      "enabled": true,
      "cross_check": false,
      "primary_model": "opus"
    },
    "max_attempts_before_escalation": 3,
    "time_box_minutes": 15
  }
}
```

The COO reads this on every cycle and runs the appropriate config for the current phase.

---

## Audit Trail

Every cross-check produces an entry in `{workspace}/logs/cross_check_audit.jsonl`:

```json
{
  "timestamp_utc": "2026-04-10T15:22:03Z",
  "phase": "phase7c",
  "epic": "therapist-profile-customization",
  "primary_model": "claude-opus-4-6",
  "secondary_model": "claude-sonnet-4-5",
  "primary_verdict": "APPROVE",
  "secondary_verdict": "BLOCK",
  "agreement": false,
  "primary_report_path": "...",
  "secondary_report_path": "...",
  "comparison_path": "...",
  "ceo_escalated": true,
  "ceo_resolution": null
}
```

The CEO can query this to track over time:
- How often do the two reviewers agree vs disagree?
- When they disagree, who is right? (Verified by sprint outcomes.)
- Is one reviewer systematically more strict or more lenient?
- Is the cross-check catching real failure modes the single reviewer would have missed?

After ~30 cross-checks, this audit trail can answer whether the cross-check is justified or whether single-reviewer is sufficient.
