---
name: skill-name
description: >
  [What it does — one sentence, third person, starts with a verb].
  Triggers on "[keyword1]", "[keyword2]", "[keyword3]", "[keyword4]".
  Not for [anti-scenario1], [anti-scenario2], or [anti-scenario3].
# user-invocable: true
# disable-model-invocation: false
# allowed-tools: []
# context: fork
# agent: general-purpose
# model: sonnet
# effort: high
---

# [Skill Name]

## Purpose

[One paragraph. What problem does this solve? Why does it exist? Who is the customer?]

## When to Use

- [Specific scenario 1]
- [Specific scenario 2]
- [Specific scenario 3]

## When NOT to Use

- [Anti-scenario 1 — what this skill should NOT be used for]
- [Anti-scenario 2]
- [Anti-scenario 3]

## Workflow

### Phase 1: [Name]
[Brief description of what happens in this phase.]

Load [phase_1_detail.md](./reference/phase_1_detail.md) for detailed instructions.

### Phase 2: [Name]
[Brief description.]

Load [phase_2_detail.md](./reference/phase_2_detail.md) for detailed instructions.

### Phase 3: [Name]
[Brief description.]

## Output Contract

This skill produces:

| Deliverable | Format | Location | Requirements |
|-------------|--------|----------|-------------|
| [Primary output] | [Markdown/JSON/HTML] | [File path] | [Min sections, word counts, etc.] |
| [Secondary output] | [Format] | [File path] | [Requirements] |

### Required Sections
1. **[Section 1]** — [description] ([word count range])
2. **[Section 2]** — [description] ([word count range])
3. **[Section 3]** — [description] ([word count range])

## Quality Gates

### Self-Evaluation Rubric
Score each dimension 1-5 before delivering:
- **Completeness:** All required sections present with minimum word counts?
- **Accuracy:** Every claim grounded in cited source or verifiable code?
- **Actionability:** Could someone act on this without asking follow-up questions?
- **Format:** Matches output contract exactly?

Decision rules:
- Average 4.0+: Deliver
- Average 3.0-3.9: Rewrite weakest dimension (max 2 rewrites)
- Average <3.0: Escalate to user

### Validation Script
Run [validate_output.py](./scripts/validate_output.py) before declaring done.

## Error Recovery

### Recoverable (retry or skip)
- [Error type]: [recovery action]
- [Error type]: [recovery action]

### Unrecoverable (halt with diagnostics)
- [Error type]: halt, [what to report]
- [Error type]: halt, [what to report]

### Halt Protocol
Write diagnostics file with: timestamp (UTC), exact error, last successful action, task goal, suggested next step.

## Anti-Simulation Rules

If any output contains these phrases, the skill has FAILED:
- "In a real implementation..."
- "You would typically..."
- "This could be extended to..."
- Pseudocode instead of working code
- Descriptions of what code WOULD do instead of the code itself

When detected: delete the output, start over with explicit instruction to produce working artifacts.
