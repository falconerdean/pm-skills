# Business Reviewer Question Pool

20+ structurally similar variants per core question. Specific question variants are drawn at random per review to defeat sub-agent pre-optimization. The randomization is enforced by `scripts/select_questions.py`.

**Why this exists:** If the reviewer always asks the same exact question, a capable upstream sub-agent will pre-answer it. The mitigation is rotation: each review draws one variant per category from a pool of 20+, so the sub-agent cannot reliably know which variant it will face.

---

## Q1: The Goal Anchor (20 variants)

The structural test: can the reviewer state the business objective in one sentence, drawn from the source-of-truth artifact, that names the customer, the customer's job-to-be-done, and the measurable change being targeted?

1. State the business objective this work is in service of, in one sentence, citing the source-of-truth artifact.
2. What single sentence in `state/sprint_plan.json` defines what success looks like for this work?
3. If you had to defend this sprint to the CEO in one sentence, drawn from the original goal artifact, what would you say?
4. What is the measurable change in customer behavior that would prove this sprint succeeded?
5. Quote the exact line from the source-of-truth artifact that defines this sprint's goal. Does it name a customer, a job, and a metric?
6. If the original goal artifact and the sub-agent's restatement of it differ, which does this work serve? Cite both.
7. Reading only the source-of-truth artifact (not any sub-agent's restatement), what is the customer's job-to-be-done that this sprint addresses?
8. What would change in the world if this sprint succeeded? Cite the source artifact that defines that change.
9. State the goal in Ulwick outcome-statement format: [direction of improvement] + [metric] + [object of control] + [contextual clarifier]. Cite the source.
10. If you removed this sprint's goal from `sprint_plan.json`, would the work still make sense? Cite both versions.
11. What is the one-sentence summary of this work's purpose, drawn only from the original goal artifact?
12. Does the goal artifact name a specific customer (not "users") with a specific job (not "improvement")? Cite.
13. Read the source-of-truth goal. Now read the work being reviewed. What is the gap between them?
14. What evidence in the goal artifact tells you this is the right sprint to be running right now?
15. If the goal artifact were missing, could you reconstruct the goal from the work alone? If yes, the work is over-specified. If no, the work is goal-divergent.
16. Quote the line in the original PR-FAQ (or founding objective doc) that this sprint maps to.
17. What customer pain does the original goal artifact say this sprint addresses? Quote it.
18. State the business objective in 15 words or fewer, cited from the source artifact.
19. If the COO had to choose between this sprint's stated goal and a single one-sentence summary of the founding business objective, which is the more authoritative goal? Cite both.
20. Can you point to a single line in `sprint_plan.json` that defines this sprint's success? If not, the goal anchor has failed.

---

## Q2: The Outcome Trace (20 variants)

The structural test: is there a measurable customer behavior change with baseline, target, and (if shipped) current measurement?

1. What measurable change in customer behavior is this work intended to produce? Baseline? Target? Current?
2. What is the baseline value for the metric this work is supposed to move? Cite where it came from.
3. What customer behavior will be different after this ships? Quantify it.
4. Pre-ship: what is the predicted change in metric X by date Y? Post-ship: what is the actual change?
5. If this work shipped and the targeted behavior did NOT change, would you still count it as done? Why?
6. What leading indicator will tell you in week 1 whether this is working? Is it predictive of the lag indicator?
7. Show me cohort data: users who experienced this change vs users who did not. What's the delta?
8. Has the metric this work targets actually moved since shipping? Cite the data source and the date.
9. State the outcome in the form: "Currently X% of customers do Y. After this work, we expect (X+N)% of customers will do Y." Cite the X.
10. What is the customer behavior delta this work is meant to produce, and how will you know it occurred?
11. If a senior PM asked you "what changed for the customer because of this work?" what would you say? Cite evidence.
12. Has anyone measured a baseline before this work shipped? If not, you cannot know if it moved.
13. Distinguish output (what shipped) from outcome (what changed for the customer). Which is being claimed here?
14. If the only "result" of this work is that the feature exists, that is output, not outcome. Is anything more being claimed?
15. What is the measurable success criterion, set in advance, in numeric terms?
16. Does the team have analytics to detect whether this worked? If not, the work is unmeasurable.
17. What is the lag measure (the result you actually want) and the lead measure (what tells you in week 1)?
18. After this ships, what specific dashboard or query confirms the targeted behavior change?
19. Did the team write down the success metric BEFORE the work, or are they reverse-engineering it now?
20. If you had to bet whether this work moved the business, what would your evidence be?

---

## Q3: The Falsification Test (20 variants)

The structural test: is there a falsifiable hypothesis with a kill criterion set in advance?

1. State the leap-of-faith assumption being tested. State the observation that would prove it wrong.
2. What kill criterion was set BEFORE the work began? Cite where it was recorded.
3. What result would cause the team to pivot away from this approach? Was that result possible?
4. Is this hypothesis falsifiable? What single observation would refute it?
5. If the team cannot answer "what would prove us wrong?", they have a belief, not a hypothesis.
6. Did the team write down a pass/fail criterion in advance, or are they declaring success after seeing the results?
7. Is the experiment designed so that it COULD have failed? An experiment that cannot fail is not an experiment.
8. State the hypothesis in the form: "If we do X, then Y will increase by N% within Z time." Was that prediction made in advance?
9. What evidence, if it existed, would cause the team to kill this work? Does that evidence exist?
10. The Lean Startup rule: "If you cannot fail, you cannot learn." What was the failure mode for this work?
11. Was the success criterion set BEFORE or AFTER the data came in? Cite the timestamps.
12. Pop test: could a hostile reviewer construct a scenario where this hypothesis is true that the team would not accept as confirming?
13. What is the smallest experiment that could disprove the team's leap-of-faith assumption?
14. If the team has been "iterating" without ever pivoting, are they actually testing or just confirming?
15. Is the hypothesis stated as a prediction with a quantified threshold? Or as a vague directional claim?
16. What number, if observed, would the team have to admit they were wrong about?
17. Was a control group or counterfactual considered? If not, what evidence connects this work to its claimed result?
18. The reviewer's question to the team: "What would you bet $1000 against happening if you're wrong?"
19. State the falsification observation in advance. State the actual observation. Compare.
20. Does the team's success threshold require the lead measure to move BY a specific amount, or just to move?

---

## Q4: The Premortem (20 variants)

The structural test: can the reviewer generate 5 distinct, specific, evidence-cited reasons this work could fail to move the business needle?

1. Assume this work shipped today and the business needle did not move. List 5 distinct reasons why.
2. It's six weeks from now. The sprint failed. Write the post-mortem. What were the causes?
3. A skeptical board member asks "what could go wrong with this?" — give them 5 specific answers grounded in artifacts.
4. List 5 plausible failure modes for this work, each citing a specific decision in the current artifacts.
5. If the team is too optimistic, what are the 5 most likely places the optimism is misplaced?
6. Imagine a competitor wanted this work to fail. What would they exploit?
7. Apply Klein's premortem: imagine the project failed. List 5 reasons. None may blame individuals.
8. What 5 things in the current plan will look obvious in retrospect as causes of failure?
9. Failure analysis (prospective): list 5 concrete failure paths for this work, each grounded in a specific artifact.
10. What 5 risks does the team's plan implicitly accept without acknowledging?
11. If this work shipped and metrics didn't move, what 5 reasons would the post-launch review cite?
12. List 5 things the team did NOT consider that an outside observer would.
13. What would a hostile VC ask about this sprint that has no good answer?
14. Imagine the next sprint retro discusses this sprint as a failure. Write the 5 root causes.
15. List 5 specific assumptions that, if wrong, would cause this work to produce no business impact.
16. What 5 distinct failure modes would each independently cause this work to miss its goal?
17. Generate 5 failure causes from 5 different categories: technical, product, market, organizational, measurement.
18. If you had to predict why this sprint will fail, what 5 things would you bet on?
19. List 5 things in the current plan that would make a senior PM raise their eyebrows.
20. What 5 plausible scenarios would cause the targeted business metric to move in the wrong direction?

---

## Q5: The Most Fragile Assumption (20 variants)

The structural test: identify load-bearing assumptions and classify them; block if any load-bearing assumption is unsupported.

1. List every assumption (explicit and tacit) this work depends on. Classify each as Solid / Correct-with-Caveats / Unsupported.
2. What assumption, if false, would make this entire sprint pointless?
3. What is the team treating as obviously true that hasn't actually been verified?
4. Find the load-bearing assumption. Is there evidence for it? Is it cited?
5. What does this work assume about customer behavior that hasn't been tested?
6. What does this work assume about the market that comes from intuition rather than data?
7. List the 3 most fragile assumptions in this work. For each, explain why it's fragile.
8. What "of course" assumption, if reversed, would force a major redesign?
9. Apply Heuer's Key Assumptions Check: list every assumption, classify as Solid/Caveat/Unsupported. Block on any Unsupported assumption that's load-bearing.
10. What is the unstated warrant in the team's argument? (Toulmin model — the rule that licenses moving from evidence to claim.)
11. What does the team assume the customer wants that the customer has never been asked?
12. Find the assumption that the team would defend as "obviously true" — that's the one to challenge first.
13. What does this work assume about the timeline that hasn't been validated against past sprints?
14. List the assumptions that are LOAD-BEARING (the work fails without them) and classify each.
15. What assumption was true once but might no longer be? (Heuer's "stale assumption" check.)
16. What does the team assume about the technology stack that hasn't been verified?
17. What does the team assume about user adoption that comes from optimism rather than data?
18. List 5 assumptions, in descending order of fragility. Block if the top assumption is load-bearing and Unsupported.
19. Find the silent premise. What is the team taking for granted that should be questioned?
20. What is the cheapest assumption to test, and has the team tested it?

---

## Q6: The Disconfirmation Search (20 variants)

The structural test: did the reviewer actively search for disconfirming evidence and report what was found (including null findings)?

1. List the disconfirming evidence you actively searched for. List what you found.
2. Apply Popper: what observation would disprove this work's central claim? Did that observation occur?
3. Apply Heuer's ACH discipline: focus on which hypotheses each piece of evidence rules OUT, not which it supports.
4. Search for evidence that the team's claim is wrong. What did you find?
5. List 3 disconfirmation attempts you made. Report the result of each (negative findings are valid).
6. What evidence, if it existed in the artifacts, would force you to change your verdict from APPROVE to BLOCK?
7. Apply confirmation bias check: did the team look for evidence that would prove them wrong, or only evidence that proves them right?
8. Did you search for customers who completed the journey but didn't get the expected outcome? What did you find?
9. Did you check whether the lead indicator is actually leading (does it predict the lag), or merely moving in parallel?
10. Did you check whether the metric the team claims is moving is actually attributable to this work, or to confounding variables?
11. Did you check the cohort data before-vs-after? Did the cohort that experienced this work behave differently from the cohort that didn't?
12. List 3 ways the team's claim could be wrong. Did you find evidence for any of them?
13. What evidence is missing that, if present, would change your verdict?
14. Did you search for negative customer feedback related to this work? Did you find any?
15. Did you check whether prior similar sprints had similar metric movements that turned out to be coincidence?
16. Did you check whether the team's "success metric" is the same one they were tracking before the sprint started? Or did they pick a metric that happened to move?
17. Did you challenge the team's interpretation of any positive data point? With what?
18. What's the strongest argument AGAINST the team's claim? Did you steelman it?
19. If you had to write a memo arguing against approving this work, what 3 points would you make?
20. Apply Mom Test: did the team rely on stated customer intent ("would you use this?") rather than past customer behavior? Cite specific instances.

---

## Selection Rules

Per review:
1. Pick exactly ONE variant per category (Q1, Q2, Q3, Q4, Q5, Q6) — six total questions
2. Use a deterministic seed based on the review timestamp + review ID, so the selection is auditable but not predictable to upstream agents
3. Track which variants have been used at `{workspace}/logs/reviewer_question_history.jsonl` so the same variant doesn't appear twice in a row for the same epic
4. After 30 days or 10 reviews, the question pool should be reviewed and updated based on what worked (caught real issues) vs what produced low-signal answers

The selection is enforced by `scripts/select_questions.py`. The validation script `scripts/validate_review.py` confirms that exactly 6 questions were used and that they came from the pool.
