# Citation Format

Every finding in a Business Reviewer report must include a specific citation. Findings without citations are invalid and the validation script will reject the report.

## Format

```
Source: <absolute file path>:<line number or section anchor>
Quote: "<exact text from the source, copied verbatim>"
```

## Examples

### Good citations

```
Source: /Users/deanfalconer/startup-workspace/state/sprint_plan.json:12
Quote: "Goal: Increase therapist profile completion rate from 38% baseline to 60% within 14 days of feature launch"
```

```
Source: /Users/deanfalconer/startup-workspace/intel/analytics_2026-04-09.md:47
Quote: "Therapist profile completion rate (last 7 days): 52% (up from 38% baseline)"
```

```
Source: /Users/deanfalconer/startup-workspace/artifacts/research/therapist-profile/customer_interviews.md:67-89
Quote: "6 of 10 therapists asked for 'templates that just work' rather than custom controls"
```

### Invalid citations (will be rejected)

```
# No source
Finding: The team's plan is solid

# Vague source
Source: the requirements doc

# No quote
Source: /Users/deanfalconer/startup-workspace/state/sprint_plan.json
Finding: The goal is clear

# Quoting from a sub-agent's restatement instead of original artifact
Source: /Users/deanfalconer/startup-workspace/artifacts/research/therapist-profile/sub_agent_summary.md:5
Quote: "The customer wants profile customization"
# (This is invalid because it cites a sub-agent's summary, not the original customer research)

# Paraphrased quote (not verbatim)
Source: /Users/deanfalconer/startup-workspace/intel/analytics_2026-04-09.md:47
Quote: "Completion rates went up by about half"
# (Invalid — the actual text is "52% (up from 38% baseline)"; paraphrasing is not allowed)
```

## Rules

1. **Absolute paths only.** Relative paths are ambiguous and may resolve differently in different sessions.
2. **Specific line numbers or section anchors.** "Somewhere in the file" is not a citation.
3. **Verbatim quotes.** Copy the exact text from the source. Paraphrasing is not allowed.
4. **Original artifacts only.** Citations to sub-agent restatements, summaries, or hand-off notes are invalid. Read and cite the original.
5. **Quotes must be findable.** A reviewer or CEO must be able to open the source file at the cited line and find the quoted text. The validation script may sample-check this.
6. **Multi-source findings.** A finding can cite multiple sources, but each must be specific.

## Why This Matters

The reviewer's authority comes from grounded evidence. A reviewer that says "the team's plan seems weak" without citation is producing opinion, not analysis. The cited evidence is the audit trail — anyone (CEO, future reviewer, sprint retro) can verify the reviewer's reasoning by opening the cited file at the cited line.

This is also a structural defense against hallucination. An LLM reviewer that fabricates evidence will struggle to produce specific line numbers and verbatim quotes that can be checked. The citation requirement is the equivalent of "show your work."
