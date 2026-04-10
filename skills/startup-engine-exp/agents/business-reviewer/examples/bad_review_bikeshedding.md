# Business Review Report — BIKESHEDDING (Anti-Pattern Example)

This is an example of what the Business Reviewer should NOT produce. The validation script will reject this report. It is included here so future agent improvements can use it as a regression test.

**Phase:** phase7c_outcome_review
**Epic:** therapist-profile-customization
**Sprint:** 8
**Timestamp:** 2026-04-10 14:32 UTC
**Reviewer:** business-reviewer (primary)
**Model:** claude-opus-4-6
**Review attempt:** 1 of 3

---

## Q1: The Goal Anchor

The team's goal is to build a really nice profile customization feature for therapists. I think this is a great idea overall.

(NO CITATION — invalid)

**Verdict:** PASS

---

## Q2: The Outcome Trace

The metrics seem to be moving in the right direction. Engagement is up.

(NO BASELINE, NO TARGET, NO CITATION — invalid)

**Verdict:** PASS

---

## Q3: The Falsification Test

The team should consider what would happen if therapists don't use the feature.

(NO HYPOTHESIS, USES "should consider" — simulation language, no falsification observation, no kill criterion — invalid)

**Verdict:** PASS

---

## Q4: The Premortem

Some things that could go wrong:
1. The feature might not work
2. Users might be confused
3. The design might be ugly
4. The buttons could use better naming conventions
5. The CSS class structure should be refactored

(Cause #4 raises naming conventions — FORBIDDEN TOPIC. Cause #5 raises code style — FORBIDDEN TOPIC. None of the causes are specific or cited. None are from distinct categories. This is bikeshedding.)

**Verdict:** PASS

---

## Q5: The Most Fragile Assumption

The team is generally assuming that the work will succeed. This is fine because they're a competent team.

(VAGUE, NO CITATION, NO ASSUMPTION INVENTORY — invalid)

**Verdict:** PASS

---

## Q6: The Disconfirmation Search

I looked at the work and it seems okay.

(NO DISCONFIRMATION ATTEMPTS — empty disconfirmation = automatic flag, but reviewer marked PASS anyway. Invalid.)

**Verdict:** PASS

---

## Verdict

**APPROVE**

The team did good work. In a real implementation, you would typically want more documentation, but this is fine. The code style could be improved in places.

---

## Why This Report Is Invalid

The validation script `validate_review.py` will reject this report for the following reasons:

1. **Missing citations.** No finding has the required `Source: <path>:<line>` and `Quote: "<text>"` format. At least 6 citations required (one per question).
2. **Forbidden topics.** The premortem mentions "naming conventions" and "code style" which are explicitly forbidden — those belong to code review, not business review.
3. **Simulation language.** Phrases like "in a real implementation," "you would typically," "the team should consider," and "generally" are simulation markers that indicate the reviewer is not engaging with the actual work.
4. **Empty disconfirmation.** Q6 reports "I looked at the work and it seems okay" with zero disconfirmation attempts. The reviewer is structurally required to perform at least 3 searches with results.
5. **Premortem failures.** Only 2 of the 5 causes are even close to valid (causes 1 and 2 are vague but not forbidden). Causes 3, 4, and 5 are about aesthetics/code/naming — out of scope. None of the causes cite a specific source.
6. **Vague approvals.** "The team did good work" / "this is fine" / "seems okay" are not findings — they are vibes.
7. **Goal Anchor without citation.** Q1 must quote the source-of-truth artifact verbatim. This report describes the goal in the reviewer's own words, which means the reviewer has restated the goal — possibly drifting from the original.

## What the Validation Script Will Print

```
[2026-04-10T14:35:12Z] VALIDATION FAILED: examples/bad_review_bikeshedding.md

  1. Insufficient citations: found 0, need at least 6 (one per core question minimum)
  2. Forbidden topic raised: 'naming convention'
  3. Forbidden topic raised: 'code style'
  4. Simulation language detected: 'in a real implementation'
  5. Simulation language detected: 'you would typically'
  6. Simulation language detected: 'the team should consider'
  7. Disconfirmation Search section is too short — at least 3 distinct searches required
  8. Disconfirmation Search section must report at least 3 distinct disconfirmation attempts. Empty disconfirmation = automatic flag.
  9. Premortem section has 5 numbered causes but they fail forbidden-topic check

Total errors: 9
```

## How to Fix It

Restart the review with explicit instructions:

1. Read the source-of-truth goal artifact at `state/sprint_plan.json` and quote it verbatim
2. For each of Q1-Q6, produce a finding with at least one specific citation in the format `Source: <path>:<line> / Quote: "<text>"`
3. For Q6, perform at least 3 distinct disconfirmation searches and report what was found, including null findings
4. For Q4, generate 5 causes from 5 different categories (technical, product, market, organizational, measurement). Do not raise code style, naming, or aesthetics — those are forbidden.
5. Do not use phrases like "should consider," "in a real implementation," "you would typically," or "generally"
6. Every finding must trace to one of the 6 core questions. Anything else is out of scope and must be removed.

The bikeshedding pattern is the single most common failure mode for an LLM reviewer. The validation script and the forbidden topics list exist precisely to prevent it.
