# Research Basis

The Silent Observer is derived from two research efforts in this repo:

## Primary Research: Business Objective Evaluation (2026-04-10)

Full report: `research/business_objective_evaluation_research_2026-04-10.md`

The most relevant sections:

- **Section 2.3 — The Coordination Axis (Cemri / MAST):** The MAST taxonomy identifies 14 failure modes in multi-agent LLM systems, including *task verification* as one of three top-level categories. The absence of an independent verifier is a statistically identified root cause of MAS failure, not a missing feature.

- **Section 6 — The Reviewer Bias Problem:** The evidence that LLM-as-judge has 12+ documented biases (CALM benchmark), multi-agent debate collapses to sycophantic consensus (arXiv:2509.05396), and same-model self-review exhibits self-enhancement bias (Zheng MT-Bench 2023). The implication is that a reviewer must be epistemically isolated from the work under review — not just structurally separate, but reading from primary sources rather than any downstream restatement.

- **Section 7 — Agent-as-a-Judge Precedent:** Zhuge et al. 2024 (arXiv:2410.10934) showed that reviewers with agent capabilities (tool use, intermediate artifact inspection, multi-step reasoning) match human experts and dramatically outperform single-prompt LLM judges. The Silent Observer is built as an agent with web search and fetch tools, not as a single critique call, per this precedent.

- **Section 10.5 — Reviewer Capture:** The failure mode where a reviewer adopts the reviewed team's framing because it ingested the team's reasoning chain. Mitigation: the reviewer must read original artifacts and must NOT receive sub-agent self-assessments, handoff summaries, or restatements. The Silent Observer enforces this via an allowlist in the wrapper script.

## Secondary Research: Teams of Rivals (Dean's summary)

Not a full report, but the key findings Dean shared that directly shape the Silent Observer design:

- **Milvus 2026 benchmark:** 53% → 80% bug detection with multi-model rivalry. Claude + Gemini covers 91% of that ceiling specifically because their training lineages are genuinely different. Hence the Silent Observer uses `gemini-3-pro` as a hard requirement, not a fallback.

- **Silent Observer pattern from Milvus:** A model that "barely said a word" caught the one bug that four other models walked past because it was not anchored by the group's prior discussion. The value comes precisely from not participating in the discourse that led to the artifact. The Silent Observer implements this directly — it reads the brief cold, without the primary researcher's search history or reasoning.

- **Sprint 11 retro lesson:** The Stitch failure cascade happened because the primary agent never read `docs/research/`. A rival VP on GPT would have had access to the same hallucinated research doc and made the same mistake. BUT a rival that starts from the deliverable (not the reasoning) and tries to independently verify claims from scratch would likely have caught "this SDK method doesn't exist" — because they would have been searching for it fresh. This points to epistemic isolation from the reasoning chain, not just separation of agents.

- **"Talk Isn't Always Cheap" (arXiv:2509.05396):** Convergence in debate correlates with performance degradation, not improvement. A wrong confident answer from one model can corrupt another model's correct answer. Implication: the Silent Observer does not debate. It reads, verifies, reports. No back-and-forth.

- **"Corruption of correct answers":** In debate settings, a confident-sounding wrong answer can talk a correct model out of its right answer. Implication: the Silent Observer's verdict is not sent back to the primary researcher for rebuttal. The primary either fixes the brief or justifies why the Silent Observer is wrong directly to the CEO.

- **Aspect-specialized rivals (MAV pattern, ReConcile):** Assign each model a specific verification dimension rather than open-ended debate. The Silent Observer's "dimension" is factual verification — it does not evaluate architecture choices, business outcomes, or code quality. Its scope is one clearly defined thing.

## Why This Is Scoped to Phase 2 Only

Phase 2 is the earliest place in the pipeline where factual hallucinations enter the system. Every downstream phase trusts the research brief. If hallucinated facts enter at Phase 2, they compound through architecture, development, and testing — the Sprint 11 Stitch cascade is the canonical example.

Catching a hallucination at Phase 2 costs one review cycle. Catching it at Phase 7 costs the entire sprint. Catching it at Phase 8 (deployment) costs the sprint plus customer impact. Earlier intervention has asymmetric returns.

The Business Reviewer (business outcome review at Phase 3, 7c, 10a) is a complementary agent — it asks "should we have built this at all?" The Silent Observer asks "do the facts in the research brief actually exist?" These are different questions requiring different approaches. A brief can pass Silent Observer (all facts verified) and still fail Business Reviewer (the facts are real but the sprint doesn't serve the business goal). Conversely, a brief can pass Business Reviewer (the goal is clear and measurable) but fail Silent Observer (the goal depends on an API method that doesn't exist).

Both matter. The Silent Observer is the lower-cost, higher-signal catch for the specific failure mode of factual hallucination.

## Why This Is Not Cross-Checked

The Business Reviewer has a dual-reviewer cross-check at Phase 7c. The Silent Observer does not, for three reasons:

1. **Fact verification is binary.** Either the SDK method exists or it doesn't. A second reviewer verifying the same claim against the same documentation would reach the same conclusion (if it does the work honestly). The value of a second reviewer comes from judgment diversity, not fact-check diversity.

2. **The Silent Observer's tool access already defeats training-data hallucination.** The model is forced to use web search and document fetch for every verdict. Validation rejects any claim marked VERIFIED without a specific quoted source. This is already the structural defense against the failure mode.

3. **Cost scales with claim count, not phase importance.** A brief with 30 factual claims would require 60 verification calls in a dual-reviewer setup. The marginal value of the second review is low while the cost is high.

If the Silent Observer proves unreliable in practice — false positives or false negatives — the next iteration should introduce a dual-model verification at the CLAIM level, not the review level. That is, each claim is verified by both Gemini 3 Pro AND a second model (GPT-5 or Claude Sonnet with different system prompt), and only claims that both agree are VERIFIED pass. This is Phase 2 enhancement, not Tier 1.

## The Protocol as Code

The single most important architectural choice in the Silent Observer is that the protocol is enforced by Python code (`invoke_silent_observer.py`), not by the reviewer's system prompt. This comes from Dean's insight in the pm-skills conversation on 2026-04-10:

> "I also wonder if we built logic into the outbound calls themselves (e.g. like a startup script that is always run and the calling AI model has no way to change it?"

Dean's instinct was correct. Prompted rules drift; coded rules don't. A prompted rule like "don't read the self-assessment" depends on the reviewer agent reading and following it. A coded rule like "the wrapper's allowlist only includes three specific paths" cannot be bypassed by the reviewer or the COO — the files are simply not in the input payload.

Every rule in the Silent Observer's SKILL.md that could be enforced in code has been enforced in code:

| Rule | Where it's enforced |
|---|---|
| Only read three whitelisted files | `load_inputs()` function — reads only from hardcoded paths |
| Self-assessment files are never read | `load_inputs()` ignores them; `scan_for_contamination()` detects them for logging only |
| Goal before context before task | `build_messages()` returns a fixed-order list |
| System prompt is static | `load_system_prompt()` reads from `reference/system_prompt.md` on disk |
| Fixed model, no fallback | `FIXED_MODEL = "gemini-3-pro"` constant; `call_gemini()` halts if unreachable |
| Simulation language is rejected | `validate_response()` regex-matches against `SIMULATION_PHRASES` |
| VERIFIED claims must have quoted evidence | `validate_claim()` rejects VERIFIED claims with empty `verdict_evidence_quote` |
| CONTRADICTED claims need ≥3 attempts | `validate_claim()` rejects CONTRADICTED claims with fewer than 3 attempts |
| Load-bearing CONTRADICTED = BLOCK | `compute_verdict()` is deterministic code, not LLM judgment |
| Every call is audit-logged | `append_audit_log()` runs on every review |

The SKILL.md documents these rules for human readers. The Python is the enforcement layer. The tests (`tests/test_wrapper_protocol.py`) prove the enforcement works.
