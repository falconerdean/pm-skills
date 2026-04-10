# Business Review Report

**Phase:** {phase} ({phase3_requirements | phase7c_outcome_review | phase10a_retro})
**Epic:** {epic_name}
**Sprint:** {sprint_number}
**Timestamp:** {YYYY-MM-DD HH:MM UTC}
**Reviewer:** business-reviewer ({primary | secondary})
**Model:** {model_name_and_version}
**Review attempt:** {N} of 3
**Question randomization seed:** {seed}

---

## Source-of-Truth Goal Artifact

**Path:** {absolute path}
**Quote of the founding goal:**

> "{exact text from the source}"

---

## Q1: The Goal Anchor

**Question (variant {N} of pool):** {selected question text}

**Finding:** {1-3 sentences}

**Citations:**
- Source: {absolute path}:{line/section}
  Quote: "{exact text}"
- Source: ...
  Quote: ...

**Verdict:** PASS | FAIL | INSUFFICIENT_EVIDENCE

---

## Q2: The Outcome Trace

**Question (variant {N} of pool):** {selected question text}

**Finding:** {1-3 sentences}

**Baseline:** {value with citation}
**Target:** {value with citation}
**Current measurement (if shipped):** {value with citation}

**Citations:**
- Source: {absolute path}:{line/section}
  Quote: "{exact text}"

**Verdict:** PASS | FAIL | INSUFFICIENT_EVIDENCE

---

## Q3: The Falsification Test

**Question (variant {N} of pool):** {selected question text}

**Finding:** {1-3 sentences}

**Leap-of-faith assumption:** {statement}
**Falsification observation:** {what would prove it wrong}
**Kill criterion (set in advance):** {numeric threshold + when set}
**Test result (if available):** {pass/fail/pending}

**Citations:**
- Source: {absolute path}:{line/section}
  Quote: "{exact text}"

**Verdict:** PASS | FAIL | INSUFFICIENT_EVIDENCE

---

## Q4: The Premortem

**Question (variant {N} of pool):** {selected question text}

**Five distinct failure causes:**

1. **Cause 1 (category: {technical | product | market | organizational | measurement}):** {specific cause}
   - Source: {absolute path}:{line/section}
   - Quote: "{exact text}"

2. **Cause 2 (category: ...):** {specific cause}
   - Source: ...
   - Quote: ...

3. **Cause 3 (category: ...):** {specific cause}
   - Source: ...
   - Quote: ...

4. **Cause 4 (category: ...):** {specific cause}
   - Source: ...
   - Quote: ...

5. **Cause 5 (category: ...):** {specific cause}
   - Source: ...
   - Quote: ...

**Showstopper causes (if any):** {list}

**Verdict:** PASS | FAIL | INSUFFICIENT_EVIDENCE

---

## Q5: The Most Fragile Assumption

**Question (variant {N} of pool):** {selected question text}

**Assumption inventory:**

| Assumption | Classification | Load-bearing? | Citation |
|---|---|---|---|
| {assumption text} | Solid / Correct-with-Caveats / Unsupported | Yes / No | {source:line + quote} |
| ... | ... | ... | ... |

**Most fragile assumption:** {the one most at risk}

**Verdict:** PASS | FAIL | INSUFFICIENT_EVIDENCE

---

## Q6: The Disconfirmation Search

**Question (variant {N} of pool):** {selected question text}

**Disconfirmation attempts (minimum 3):**

1. **Searched:** {what you looked for}
   **Found:** {result, including null findings}
   **Source:** {absolute path}:{line/section}
   **Quote:** "{exact text or 'no matching content found'}"

2. **Searched:** ...
   **Found:** ...
   **Source:** ...
   **Quote:** ...

3. **Searched:** ...
   **Found:** ...
   **Source:** ...
   **Quote:** ...

**Decisive disconfirming evidence (if any):** {description with citation}

**Verdict:** PASS | FAIL | INSUFFICIENT_EVIDENCE

---

## Verdict

**APPROVE** | **APPROVE WITH CONDITIONS** | **BLOCK**

### Rationale

{1-3 sentence summary of why this verdict, citing the questions that drove it}

### Conditions (if APPROVE WITH CONDITIONS)

1. {Specific actionable condition with deadline}
2. {Specific actionable condition with deadline}

### Block Reasons (if BLOCK)

**BLOCK REASON 1:** {one-sentence summary}

- Source artifact: {absolute path}:{line/section}
- Quote: "{exact text from source}"
- Why this is a block (not a flag): {explanation}
- Required action: {specific actionable step}
- Re-review prerequisite: {what must be produced/changed before re-running}

**BLOCK REASON 2:** ...

---

## Cross-Check Result (Phase 7c only)

**Other reviewer:** {primary | secondary}
**Other reviewer's verdict:** {APPROVE | APPROVE WITH CONDITIONS | BLOCK}
**Agreement:** {Yes | No}
**Comparison document:** {path}

(This section is filled in only when the cross-check protocol runs at Phase 7c. For single-reviewer phases, this section is omitted.)

---

## Self-Evaluation

| Dimension | Score (1-5) | Notes |
|---|---|---|
| Citation completeness | {N}/5 | Every finding cited? |
| Disconfirmation effort | {N}/5 | At least 3 searches with results? |
| Independence | {N}/5 | No sub-agent self-assessments used? |
| Scope discipline | {N}/5 | All findings trace to Q1-Q6? |

If any dimension is below 5/5, the review is invalid. Re-run.

---

## Validation

```bash
python3 ../scripts/validate_review.py --report {this report path}
```

Expected output: `VALIDATION PASSED`. If validation fails, address the errors and re-run.

---

## Audit Trail

**Logged to:**
- `{workspace}/state/company_state.json` → `business_review.{phase}.verdict`
- `{workspace}/logs/decisions.jsonl` → entry for this review
- `{workspace}/state/business_review_attempts.json` → attempt counter for the three-strikes rule

**Email sent (if BLOCK):** Yes / No
**CEO escalation (if attempt 3 of 3):** Yes / No
