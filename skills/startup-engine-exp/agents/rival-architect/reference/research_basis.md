# Research Basis

The Rival Architect is derived from the same research foundation as the Silent Observer (`agents/silent-observer/reference/research_basis.md`), with one critical difference in framing.

## Where the Silent Observer and Rival Architect diverge

| Question | Silent Observer | Rival Architect |
|---|---|---|
| What does it review? | Factual claims in the discovery brief | Architectural decisions in the tech design |
| Pattern | Reader (reads existing artifact, verifies, produces verdict) | Producer (reads same brief as primary, independently generates competing artifact) |
| Number of LLM calls | 1 (extract + verify in one call) | 1 for production + 1 bounded call for comparison judgment |
| When the LLM judges | Once, against external evidence | Once, constrained to "surface differences, not decide" |
| Verdict authority | Deterministic code | Deterministic code |
| Anchoring defense | Reads brief cold; never sees primary's reasoning | Reads same brief as primary; never sees primary's output |

Both agents share the same protocol-as-code philosophy: rules are enforced by Python wrappers, not by prompts. Both use Gemini 3 Pro as the rival model because of training-lineage diversity from Claude (per Milvus 2026). Both are scoped to one specific class of failure they catch better than any other agent in the system.

## The specific evidence supporting Rival Architect

### Milvus 2026 multi-agent benchmark

The strongest case for multi-model rivalry at the architectural layer:

- **53% → 80% bug detection** when adding rivals to single-model code review
- **Claude + Gemini covers 91%** of that bug-detection ceiling — better than any other pair tested
- **Mechanism is complementary blind spots**, not aggregate intelligence:
  - Claude scores 0/2 on concurrency races
  - Gemini scores 1/2 on the same races
  - Neither is "better" — they're differently blind
- **The "silent observer" effect:** the Codex model that "barely said a word" caught the one zero-value primary key bug that four other models walked past. Convergence in the group missed it; the outsider caught it.

This is exactly the dynamic Phase 5 needs. Architectural decisions involve concurrency, compatibility, library-existence — the dimensions where Claude is documented as weakest. Pairing Claude with Gemini at this phase is the highest-leverage rivalry placement in the entire SDLC.

### Why "Independent First Response" is the load-bearing rule

From Dean's Teams of Rivals research synthesis:

> "The rival needs to be epistemically isolated from the primary's reasoning chain, not just the primary's conclusions."

The Rival Architect's wrapper script enforces this by:

1. **Refusing to read the primary's tech output.** The input allowlist explicitly excludes `architecture.md`, `api_spec.json`, and `db_schema.sql` from the primary's tech directory. Even if the COO accidentally tried to pass them as context, the function signature only accepts `(workspace, epic)` — there is nowhere to inject extra context.

2. **Defensive content scanning.** After loading inputs, the wrapper samples the primary's actual content and verifies none of it appears in the rival's loaded inputs. If a substring is found, the wrapper halts with `PROTOCOL VIOLATION`. This catches any future bug where contamination might leak through a shared reference path.

3. **Goal-anchor-first message ordering.** The first message to Gemini is the sprint goal alone. The brief, requirements, and design follow as separate messages. The model anchors on the goal because that's all it sees first. This is the same structural defense Silent Observer uses.

### Why "Talk Isn't Always Cheap" rules out Option 4 (Handoff Dialogue)

The 2025 paper *Talk Isn't Always Cheap: Understanding Failure Modes in Multi-Agent Debate* (arXiv:2509.05396) found that **agent disagreement rate decreases as debate progresses, and this convergence correlates with performance degradation**. A wrong confident answer from a weaker model can talk a correct model out of its right answer.

Implication for the Rival Architect: **the rival never sees Claude's architecture, and Claude never sees the rival's.** If we let either model "review" the other's work, the well-documented sycophantic-consensus failure mode would degrade both. The compare script is the only place where both architectures meet, and it is structured as deterministic comparison (Stages 1-6) plus a single bounded LLM call constrained to "surface, do not decide" (Stage 7). The verdict (Stage 8) is computed by code reading the outputs of all prior stages.

This is the structural rule: **two independent producers, then a comparison.** Never producer-then-critique, never debate, never consensus-seeking. The CEO is the resolver, not the LLMs.

### Why aspect-specialized rivals were considered but not adopted

The research mentioned a fifth option: assign each model a specific verification dimension (Claude: data model, Gemini: concurrency, GPT: security). This is the MAV (Multi-Agent Verification) pattern from ReConcile.

We did not adopt this for Tier 2 because:

1. **The full architecture is the right unit of comparison.** A concurrency model that contradicts the data model is worse than either alone. Splitting the comparison by aspect would miss cross-cutting failures.

2. **The wrapper script's specialization keyword counting (Stage 6) already captures the asymmetry.** If Gemini's concurrency section is substantially more thorough than Claude's, the compare script flags it as "rival caught what primary missed." This achieves the spirit of aspect-specialized rivals without splitting the architectures.

3. **Cost is not the constraint** (per Dean's directive "don't care about budget, only quality"), so we are not optimizing for the cheaper aspect-split pattern when the full-rival pattern produces stronger signal.

If aspect-specialized rivalry proves valuable in a future enhancement, the architecture is set up to support it: each agent (rival-architect, future security-rival, future ux-rival) can run its own wrapper script with its own scoped system prompt.

## What this skill does NOT depend on

To prevent over-coupling to specific research findings, the skill is designed so that:

1. **It would still be useful even if Milvus 2026 were retracted.** The basic pattern of "two independent producers, structured comparison, deterministic verdict" is independently defensible from older inter-rater reliability practice and from the long history of red-team / adversarial review in intelligence analysis.

2. **It does not assume Claude is worse at concurrency.** The specialization keyword counting in Stage 6 is a heuristic that catches asymmetry in either direction. If Claude consistently produces more thorough concurrency sections than Gemini, the compare script would flag the inverse asymmetry.

3. **It works with any rival model.** Replacing `gemini-3-pro` with `gpt-5` or `llama-4` would change one constant in the wrapper. The protocol is model-agnostic.

## Single-source claims (flagged for transparency)

Three claims in this skill rely on single sources:

1. **"Claude + Gemini covers 91% of the Milvus bug-detection ceiling"** — single source (Milvus 2026 benchmark). The general claim that model diversity helps is well-supported across the literature, but the specific 91% number is from one benchmark. Treat as directional, not exact.

2. **"Talk Isn't Always Cheap convergence-degrades-accuracy finding"** — single source (arXiv:2509.05396). The pattern is consistent with broader sycophancy research but the specific quantification is from one preprint. The structural defense (no anchoring) holds regardless because it's also supported by older inter-rater reliability practice.

3. **"Gemini specifically catches concurrency that Claude misses"** — derived from the Milvus 2026 specific data points. The general claim that different training data produces different blind spots is well-supported; the specific Gemini-vs-Claude characterization is from one benchmark.

The skill's design does not collapse if any of these claims is later contradicted. The structural rules (two independent producers, deterministic comparison, bounded judgment surfacing) are defensible from first principles and from older multi-rater practice.

## Pointer to the full research

For the complete research basis, the full bibliography, and the Sonnet adversarial cross-check that informed both this skill and the Silent Observer:

```
research/business_objective_evaluation_research_2026-04-10.md
```

Read it before modifying this skill. The design choices here are direct responses to specific findings, not arbitrary preferences.
