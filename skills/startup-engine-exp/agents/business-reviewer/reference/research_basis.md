# Research Basis

The full research report informing this agent design is at:

```
research/business_objective_evaluation_research_2026-04-10.md
```

That report contains:
- The empirical evidence for agent goal drift (Langosco/Shah ICML 2022, Apollo 2025, MAST taxonomy 2025)
- The critical-thinking canon synthesis (Socratic, Toulmin, Heuer, Klein, Hoffman, Cosier/Schwenk, Popper, Kahneman)
- The business operator framework synthesis (Amazon PR-FAQ, JTBD/ODI, OKRs, Lean Startup, Theory of Change, 4DX, Outcomes Over Output, Mom Test, MECE)
- The LLM-as-judge bias literature (Zheng MT-Bench, CALM 12 biases, Talk-Isn't-Cheap multi-agent debate)
- The Agent-as-a-Judge architectural precedent (Zhuge 2024)
- The Sleeper Agents warning (Hubinger 2024)
- The Sonnet adversarial cross-check that identified 6 blocking issues in an earlier draft of this design
- Full bibliography with 30+ sources
- Methodology appendix documenting the 8-phase deep research pipeline

**Read it before modifying this agent.** The design choices here are not arbitrary — they are direct responses to specific findings in the literature and to the adversarial critique. Changing the design without re-reading the rationale will likely re-introduce defects the design was built to prevent.

Key sections to read first:

- **Section 2** — Why agents drift (the empirical case for the reviewer's existence)
- **Section 5** — The Disconfirmation Discipline (the central epistemic move the reviewer enforces)
- **Section 6** — The Reviewer Bias Problem (why the cross-check protocol is structured the way it is)
- **Section 9** — The Two-Tier Cross-Check Protocol Refined (why blind independent scoring beats verdict-on-verdict auditing)
- **Section 11** — The Business Reviewer Agent Design (the specific design choices)
- **Section 12** — The Strongest Argument Against Doing This (the steelmanned counter-argument and its rebuttal)
- **Section 14** — Limitations and Caveats

## Single-Source Claims (Flagged)

Three claims in the research basis rest on single sources. They should be treated with appropriate caution and ideally validated by future research:

1. **Multi-agent debate sycophancy** — *Talk Isn't Always Cheap*, arXiv:2509.05396 (single source). Used to justify blind independent scoring in the cross-check protocol. The architectural choice is also supported by older inter-rater reliability practice and intelligence community SAT tradition, so the design is not solely dependent on this paper. But the specific claim about disagreement-rate decay should not be over-cited.

2. **Agent-as-a-Judge outperforms LLM-as-a-Judge for agentic tasks** — Zhuge et al. 2024, arXiv:2410.10934 (single source). Used to justify building the reviewer as an agent rather than a single critique call. Architecturally well-supported by the multi-step reasoning literature broadly, but the specific empirical comparison is from one paper.

3. **Apollo Research goal drift quantification** — Arike et al. 2025, arXiv:2505.02709 (single source, Apollo Research). Used to justify the reviewer's "fresh context advantage" claim — that placing the reviewer at the end of the pipeline doesn't suffer from accumulated context drift because the reviewer has its own fresh session. The Apollo finding aligns with the broader context-drift literature but is the most direct empirical evidence.

If any of these single-source claims is later contradicted, the design choices that depend on them should be re-evaluated.
