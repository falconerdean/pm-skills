# Block vs Flag Decision Tree

The reviewer's verdict must be one of: **APPROVE**, **APPROVE WITH CONDITIONS**, **BLOCK**.

There are no other verdicts. "PARTIAL" is not allowed (the Sprint 7 retro made this rule). "Conditional approval" is allowed but means specific conditions must be met before next phase advance, with each condition cited and specific.

---

## The Tree

```
START: All 6 questions answered with citations?
├── NO  → BLOCK: "Review incomplete. Re-run with all 6 questions."
└── YES → continue

Q1 (Goal Anchor): Can the goal be stated in one sentence from the source-of-truth artifact?
├── NO  → BLOCK
│   Reason: "The work cannot be reviewed without a goal that names a customer, a job, and a measurable change."
│   Required action: Rewrite the goal in the source-of-truth artifact (state/sprint_plan.json) in
│   Ulwick outcome-statement format, then re-submit for review.
└── YES → continue

Q2 (Outcome Trace): Is there a baseline + target + measurement plan?
├── NO and the work is customer-facing → BLOCK
│   Reason: "Customer-facing work must define what behavior change it's targeting and how that change will be measured."
│   Required action: For each story, specify: baseline value, target value, measurement source, leading indicator.
├── NO and the work is purely infrastructural (e.g., refactoring, infra setup) → CONTINUE with FLAG
│   Flag: "Outcome trace not required for infrastructural work but should be documented in next sprint planning."
└── YES → continue

Q3 (Falsification Test): Falsifiable hypothesis with kill criterion set in advance?
├── NO and the work makes empirical claims about customers/markets → BLOCK
│   Reason: "Empirical claims require falsification tests. Without one, the team cannot distinguish 
│   success from luck."
│   Required action: State the leap-of-faith assumption, the falsification observation, and the kill 
│   criterion BEFORE the next sprint advances.
├── NO and the work is execution-only (no empirical claims) → CONTINUE with FLAG
│   Flag: "No falsification test, but no empirical claims being made. Verify this is correct."
├── YES, kill criterion was set in advance → CONTINUE
└── YES, but kill criterion was reverse-engineered after results came in → BLOCK
    Reason: "A kill criterion set after the data is post-hoc rationalization, not falsification. 
    The Lean Startup rule is: set the criterion BEFORE running the experiment."
    Required action: Acknowledge the post-hoc framing and either accept the work was not a 
    falsifiable test, or design a real test for the next sprint.

Q4 (Premortem): 5 distinct causes from at least 3 different categories generated?
├── Fewer than 5 distinct causes → FLAG
│   Flag: "Premortem produced fewer than 5 distinct causes — review may be shallow."
├── 5+ causes but all from same category (e.g., all technical) → FLAG
│   Flag: "All 5 premortem causes are technical/product/etc. — diverse failure modes not 
│   adequately considered."
├── Causes blame individuals → BLOCK
│   Reason: "Toyota's rule: root causes are systems, not people. Premortem with individual blame 
│   indicates the analysis is not deep enough."
│   Required action: Re-run the premortem looking for system causes, not personal causes.
├── 5+ distinct causes from 3+ categories with no showstoppers → CONTINUE
└── 5+ causes including one or more "showstopper" causes (causes that, if true, would cause 
    catastrophic business harm) → BLOCK
    Reason: "Premortem identified [N] showstopper failure modes. These must be mitigated before 
    advancement, not flagged as risks."
    Required action: For each showstopper cause, specify the mitigation and the evidence that 
    the mitigation works.

Q5 (Most Fragile Assumption): Any load-bearing assumption classified as Unsupported?
├── YES, load-bearing AND Unsupported → BLOCK
│   Reason: "Load-bearing assumption [X] is unsupported. The work depends on it being true, but 
│   no evidence justifies it. Heuer's Key Assumptions Check rule: do not approve work whose 
│   load-bearing assumptions are unsupported."
│   Required action: Either find evidence supporting the assumption, or remove the assumption 
│   from the load-bearing path (redesign so the work doesn't depend on it).
├── YES, Unsupported but NOT load-bearing → CONTINUE with FLAG
│   Flag: "Unsupported assumption [X] is not load-bearing but should be tracked."
└── NO load-bearing Unsupported assumptions → CONTINUE

Q6 (Disconfirmation Search): Was the search performed and reported?
├── NO (empty disconfirmation) → BLOCK
│   Reason: "An approval without a disconfirmation search is just confirmation. The reviewer is 
│   structurally required to search for evidence the team is wrong before approving."
│   Required action: Perform the search. Report what was found, including null findings 
│   ("I searched for X and did not find it" is valid).
├── YES, with no disconfirming evidence found → CONTINUE
│   (This is acceptable — the search was performed, the result is the work survives scrutiny.)
└── YES, with disconfirming evidence found → consider the evidence:
    ├── Evidence is decisive (e.g., the metric the team claims is moving is actually flat) → BLOCK
    │   Reason: "Disconfirming evidence found that contradicts the team's central claim."
    │   Required action: Address the disconfirming evidence specifically.
    ├── Evidence is concerning but not decisive → APPROVE WITH CONDITIONS
    │   Conditions: Specific actions the team must take in the next sprint to address the concern.
    └── Evidence is minor → CONTINUE with FLAG

FINAL VERDICT
├── Any BLOCK condition triggered → BLOCK
├── No BLOCKs but at least one CONDITIONS-level concern → APPROVE WITH CONDITIONS
└── No BLOCKs and no conditions → APPROVE
```

---

## What Counts as a "Showstopper" Premortem Cause

A premortem cause is a showstopper if ALL THREE are true:

1. **Plausibility:** A senior PM would estimate the cause's probability above 25%
2. **Severity:** If the cause occurred, the business impact would be material (customer harm, revenue loss, brand damage, or regulatory exposure)
3. **Reversibility:** The damage from the cause could not be undone within the next sprint

Examples of showstoppers:
- "We acquire customers who churn within 7 days because the onboarding doesn't match the marketing promise"
- "The feature works for 1% of users but breaks the page for the other 99% on mobile"
- "Compliance/legal review was skipped and the feature violates regulation X"
- "The new pricing model loses money on every sale below tier Y"

Examples of NOT showstoppers (track as flags, not blocks):
- "Some users may find the new flow confusing at first"
- "The feature might not have the impact we hope for"
- "Performance might degrade slightly under high load"

---

## Citation Format for Block Reasons

Every BLOCK must include:

```
BLOCK REASON [N]: [one-sentence summary]

Source artifact: [absolute path]:[line/section]
Quote: "[exact text from source]"

Why this is a block (not a flag): [explanation tying to one of the rules above]

Required action: [specific, actionable step the team must take]

Re-review prerequisite: [what the team must produce/change before re-running this review]
```

A block reason without a source citation is invalid. The validation script flags it.

---

## What Cannot Be a Block Reason

The reviewer is forbidden from blocking on:

- Code style or formatting
- Variable naming
- File organization
- Choice of framework or library
- Aesthetic design preferences
- "I think this could be better" without specific evidence
- "The team should consider..." without a specific action
- Concerns that don't trace to one of the six core questions
- Concerns that come from the reviewer's training data rather than the project artifacts

If a finding doesn't fit one of the six question categories, it cannot be in the verdict. The validation script enforces this.

---

## The Three-Strikes Rule

If the same review iterates 3 times without resolution:

1. The reviewer cannot block a 4th time
2. Instead, the case is escalated to the CEO with a full history of all 3 attempts
3. The CEO decides: override the block, kill the work, or pause the engine for investigation

The three-strikes count is tracked at `{workspace}/state/business_review_attempts.json` in this format:

```json
{
  "phase7c_therapist-profile": {
    "attempts": 2,
    "last_verdict": "BLOCK",
    "last_attempt_at": "2026-04-09T15:22:03Z",
    "block_reasons_history": [
      {"attempt": 1, "reasons": [...]},
      {"attempt": 2, "reasons": [...]}
    ]
  }
}
```

The validation script reads this file and refuses to record a 4th BLOCK without an explicit CEO escalation flag.
