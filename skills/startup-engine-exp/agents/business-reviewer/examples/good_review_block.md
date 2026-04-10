# Business Review Report — BLOCK

**Phase:** phase3_requirements
**Epic:** therapist-profile-customization
**Sprint:** 8
**Timestamp:** 2026-04-08 10:15 UTC
**Reviewer:** business-reviewer (primary)
**Model:** claude-opus-4-6
**Review attempt:** 1 of 3
**Question randomization seed:** therapist-profile_phase3_2026-04-08T10-12-00Z_1

---

## Source-of-Truth Goal Artifact

**Path:** /Users/deanfalconer/startup-workspace/state/sprint_plan.json
**Quote of the founding goal:**

> "Goal: Build therapist profile customization."

---

## Q1: The Goal Anchor

**Question (variant 12 of pool):** Does the goal artifact name a specific customer (not "users") with a specific job (not "improvement")? Cite.

**Finding:** The goal in `sprint_plan.json` is "Build therapist profile customization." This is a description of work to be done, not a goal. It does not name a customer change, a metric, or a target. The goal is not reviewable in its current form.

**Citations:**
- Source: /Users/deanfalconer/startup-workspace/state/sprint_plan.json:12
  Quote: "Goal: Build therapist profile customization."

**Verdict:** FAIL

---

## Q2: The Outcome Trace

**Question (variant 4 of pool):** Pre-ship: what is the predicted change in metric X by date Y? Post-ship: what is the actual change?

**Finding:** Stories specify acceptance criteria like "user can upload headshot" but no story includes a baseline behavior measurement, a target behavior change, or a metric. There is no defined outcome to trace.

**Baseline:** None defined
**Target:** None defined
**Current measurement:** N/A — work has not shipped

**Citations:**
- Source: /Users/deanfalconer/startup-workspace/artifacts/requirements/therapist-profile/stories.json:1-180
  Quote: "[12 stories total, none containing 'baseline', 'target', or numeric metric]"
- Source: /Users/deanfalconer/startup-workspace/artifacts/requirements/therapist-profile/stories.json:34
  Quote: "Story: As a therapist, I want to upload a headshot, so that my profile looks professional. AC: User can select an image file. User can preview the upload. User can save."

**Verdict:** FAIL

---

## Q3: The Falsification Test

**Question (variant 1 of pool):** State the leap-of-faith assumption being tested. State the observation that would prove it wrong.

**Finding:** No hypothesis is stated in any story. No falsification criterion. The work makes empirical claims (implicitly: "customization will increase engagement") but does not test them.

**Leap-of-faith assumption:** Tacit, not stated: "customization will produce some unspecified business benefit"
**Falsification observation:** None defined
**Kill criterion (set in advance):** None

**Citations:**
- Source: /Users/deanfalconer/startup-workspace/artifacts/requirements/therapist-profile/stories.json:1-180
  Quote: "[searched for 'hypothesis', 'falsif', 'kill criterion', 'pivot' — zero matches]"

**Verdict:** FAIL

---

## Q4: The Premortem

**Question (variant 16 of pool):** Generate 5 failure causes from 5 different categories: technical, product, market, organizational, measurement.

**Note:** Q1 already FAILED (no measurable goal), but per the workflow rules, all 6 questions must still be answered before applying the decision tree. The premortem is still informative for the team — it surfaces what could go wrong even if the work proceeded as currently scoped.

**Five distinct failure causes:**

1. **Cause 1 (category: market):** Therapists explicitly asked for templates rather than customization. Building customization will produce a feature that 60% of the user base does not want.
   - Source: /Users/deanfalconer/startup-workspace/artifacts/research/therapist-profile/customer_interviews.md:67
   - Quote: "6 of 10 therapists asked for 'templates that just work' rather than custom controls"

2. **Cause 2 (category: product):** Without a defined success metric, the team will not know if the feature succeeded. Even if customization is built and shipped, there is no way to declare it done.
   - Source: /Users/deanfalconer/startup-workspace/artifacts/requirements/therapist-profile/stories.json:1-180
   - Quote: "[12 stories, zero metrics]"

3. **Cause 3 (category: organizational):** With no falsification test, the team cannot pivot away from this approach if it doesn't work — they will keep iterating without ever questioning the premise.
   - Source: /Users/deanfalconer/startup-workspace/artifacts/research/therapist-profile/discovery_brief.md
   - Quote: "[no hypothesis, no kill criterion in the discovery brief]"

4. **Cause 4 (category: technical):** Customization features create maintenance debt. Without a clear scope, the team will keep adding customization options indefinitely, increasing the test surface and the failure surface.
   - Source: /Users/deanfalconer/startup-workspace/artifacts/requirements/therapist-profile/stories.json:34-180
   - Quote: "[12 stories, no acceptance criterion limiting scope expansion in future sprints]"

5. **Cause 5 (category: measurement):** Profile completion rate (the implicit metric) does not measure whether customization helps therapists acquire clients — which is the actual business goal. The team would optimize completion without moving the business needle.
   - Source: /Users/deanfalconer/startup-workspace/state/sprint_plan.json:12
   - Quote: "Goal: Build therapist profile customization."

**Showstopper causes:** Yes — Cause #1 is a showstopper. The team is building something the majority of customers explicitly said they do not want, which meets all three showstopper criteria (plausibility >25%: confirmed by data; severity: feature investment with no customer benefit; reversibility: a sprint of work is hard to recover).

**Verdict:** FAIL — premortem identified a showstopper cause

---

## Q5: The Most Fragile Assumption

**Question (variant 11 of pool):** What does the team assume the customer wants that the customer has never been asked?

**Finding:** Tacit assumption throughout the stories: "if we let therapists customize, they will, and the result will be better." This is load-bearing (the entire sprint depends on it) and Unsupported. Worse, it is contradicted by the customer interview data already in the repo.

**Assumption inventory:**

| Assumption | Classification | Load-bearing? | Citation |
|---|---|---|---|
| "Therapists want customization" | **Unsupported** | **Yes** | customer_interviews.md:67 contradicts |
| "Customization improves outcomes" | Unsupported | Yes | No data either way |
| "Custom controls are better than templates" | **Unsupported and contradicted** | Yes | customer_interviews.md:67 — 6 of 10 therapists asked for templates |

**Most fragile assumption:** "Therapists want customization" — load-bearing, Unsupported, AND contradicted by 60% of available customer interviews.

**Citations:**
- Source: /Users/deanfalconer/startup-workspace/artifacts/research/therapist-profile/customer_interviews.md:67
  Quote: "Q: How do you want to set up your profile? A: 'Honestly, I just want a template that looks good. I'm a therapist not a designer.' [6 of 10 therapists gave variants of this answer]"
- Source: /Users/deanfalconer/startup-workspace/artifacts/research/therapist-profile/customer_interviews.md:89
  Quote: "Themes: 'just want defaults that work' (6/10), 'don't have time to customize' (4/10), 'want to control what's shown' (3/10)"

**Verdict:** FAIL — load-bearing Unsupported AND contradicted assumption

---

## Q6: The Disconfirmation Search

**Question (variant 18 of pool):** What's the strongest argument AGAINST the team's claim? Did you steelman it?

**Disconfirmation attempts:**

1. **Searched:** Have prior profile-customization features in this product or comparable products moved any business metric?
   **Found:** No internal data — no prior customization sprint to compare to. One comparable product (Psychology Today) saw a 4% lift in profile completion but no measurable impact on therapist acquisition or therapist retention.
   **Source:** /Users/deanfalconer/GitHub/pm-skills/research/therapy-client-selection-research.md:201
   **Quote:** "Psychology Today's 2024 profile customization launch: +4% completion, no measurable acquisition or retention lift"

2. **Searched:** Do therapists actually want customization, or is the team projecting?
   **Found:** Customer interview data is mixed. 6 of 10 therapists explicitly asked for "templates that just work" rather than custom controls. 3 of 10 wanted to control what's shown. 1 of 10 was indifferent. The majority preference is the OPPOSITE of customization.
   **Source:** /Users/deanfalconer/startup-workspace/artifacts/research/therapist-profile/customer_interviews.md:67
   **Quote:** "6 of 10 therapists asked for 'templates that just work' rather than custom controls"

3. **Searched:** Does the team have any data showing that customization specifically (vs better defaults) drives the desired outcome?
   **Found:** None. The team's case rests on intuition.
   **Source:** /Users/deanfalconer/startup-workspace/artifacts/research/therapist-profile/discovery_brief.md
   **Quote:** "[searched the entire discovery brief — no quantitative data on customization vs templates]"

**Decisive disconfirming evidence:** Yes — customer interview data directly contradicts the team's central premise. 60% of therapists want templates, not customization.

**Verdict:** FAIL — decisive disconfirming evidence found

---

## Verdict

**BLOCK**

### Rationale

This work fails on Q1 (no measurable goal), Q2 (no outcome trace), Q3 (no falsification test), Q5 (load-bearing assumption is unsupported AND contradicted by available customer data), and Q6 (decisive disconfirming evidence found in the customer interviews already in the repo). The work as currently scoped is not buildable as a business sprint because it does not specify what business change it would produce.

More damningly: the team's central premise — that therapists want customization — is contradicted by 60% of the customer interview data the team's own discovery brief already contains. The team appears to have decided to build customization first and then discovered (but ignored) the customer evidence pointing the other direction.

### Block Reasons

**BLOCK REASON 1: Goal is not measurable.**

- Source artifact: /Users/deanfalconer/startup-workspace/state/sprint_plan.json:12
- Quote: "Goal: Build therapist profile customization."
- Why this is a block (not a flag): Q1 BLOCK condition. The goal must name a customer behavior change with a metric and a target. As written, it is a description of work, not a goal.
- Required action: Rewrite the goal in `sprint_plan.json` in Ulwick outcome-statement format: "[direction of improvement] + [metric] + [object of control] + [contextual clarifier]". Example: "Increase therapist profile completion rate from X% baseline to Y% within Z days, because [evidence-cited reason]."
- Re-review prerequisite: Updated `sprint_plan.json` with measurable goal.

**BLOCK REASON 2: No outcome trace in any story.**

- Source artifact: /Users/deanfalconer/startup-workspace/artifacts/requirements/therapist-profile/stories.json:1-180
- Quote: "[12 stories, zero baseline values, zero target values, zero metric definitions]"
- Why this is a block: Q2 BLOCK condition. Customer-facing stories must define what behavior change they target and how it will be measured.
- Required action: For each story, add: baseline value, target value, measurement source (which dashboard/query), leading indicator (what tells you in week 1 whether it's working).
- Re-review prerequisite: Updated `stories.json` with outcome trace per story.

**BLOCK REASON 3: Load-bearing assumption is contradicted by available customer data.**

- Source artifact: /Users/deanfalconer/startup-workspace/artifacts/research/therapist-profile/customer_interviews.md:67
- Quote: "6 of 10 therapists asked for 'templates that just work' rather than custom controls"
- Why this is a block: Q5 + Q6 BLOCK conditions. The team's central premise (therapists want customization) is the OPPOSITE of what 60% of interviewed therapists said. Building customization despite this evidence is a goal misgeneralization risk: the team's interpretation has drifted from the customer's actual job-to-be-done.
- Required action: Address the customer interview contradiction explicitly in the discovery brief. Either (a) explain why the 60% are wrong and the team is right (requires evidence), or (b) re-scope the sprint as "build templates that work for therapists" rather than "build customization." Option (b) is the recommended path based on the available evidence.
- Re-review prerequisite: Updated discovery brief addressing the contradiction, OR updated sprint scope.

### Required actions before re-review

1. Rewrite sprint goal as outcome statement with metric and target (BLOCK REASON 1)
2. Add baseline + target + measurement to each story (BLOCK REASON 2)
3. Address the customer interview contradiction in the discovery brief — likely by re-scoping to templates rather than customization (BLOCK REASON 3)

This is attempt **1 of 3**. Two more block-then-fix cycles are allowed before automatic CEO escalation.

---

## Self-Evaluation

| Dimension | Score (1-5) | Notes |
|---|---|---|
| Citation completeness | 5/5 | Every finding has source + line + verbatim quote |
| Disconfirmation effort | 5/5 | 3 distinct searches with results, found decisive contrary evidence |
| Independence | 5/5 | All citations from original artifacts; no sub-agent summaries used |
| Scope discipline | 5/5 | All findings trace to Q1-Q6 |

---

## Validation

```bash
python3 ../scripts/validate_review.py --report ../examples/good_review_block.md
```

Expected: `VALIDATION PASSED`
