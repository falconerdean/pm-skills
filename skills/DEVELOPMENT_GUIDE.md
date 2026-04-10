# Skill Development Guide

How to build high-quality, reusable skills for Claude Code. Based on deep research across Anthropic's official guidance, production multi-agent patterns, and lessons from 8 existing skills.

**Last updated:** 2026-04-09 UTC

---

## Core Principles

### 1. Skills Are Engineering Artifacts, Not Prose
A skill is not a paragraph of instructions. It's a structured directory with a routing hub (SKILL.md), supporting reference files, validation scripts, output templates, and test scenarios. Treat it like a module, not a memo.

### 2. The Description Is the Most Important Line
Research shows skill activation rates jump from ~20% to ~90% with optimized descriptions. A vague description means the skill never fires. Every description must include:
- **What it does** (capability in third person)
- **When to use it** (trigger keywords: "Triggers on 'X', 'Y', 'Z'")
- **What it's NOT for** (negative boundaries)

### 3. Progressive Disclosure Over Monolithic Prompts
SKILL.md is the routing hub (<500 lines). Detailed methodology, phase prompts, reference data, and examples live in subdirectories. Claude loads them on demand. Providing all instructions at once causes agents to collapse phases and skip steps.

### 4. Context Engineering > Prompt Engineering
You're managing the entire state available to the LLM, not just writing instructions. Find the smallest set of high-signal tokens that maximize the likelihood of desired outcomes. Every line should earn its place by solving a real problem you've encountered.

### 5. Creative Decisions Belong to the Customer
Skills encode technical best practices (how to structure, validate, format). Domain-specific creative decisions (what to build, how it looks, what to prioritize) belong to the human invoking the skill. Research informs recommendations; it does not make decisions.

---

## Skill Directory Structure

```
my-skill/
├── SKILL.md              # Required. Routing hub. <500 lines.
├── reference/            # Detailed methodology, phase prompts, domain knowledge
│   ├── methodology.md
│   └── phase_prompts/
├── templates/            # Output templates Claude fills in
│   └── report_template.md
├── scripts/              # Validation, quality gates, automation
│   ├── validate_output.py
│   └── quality_check.sh
├── examples/             # Example inputs and outputs
│   ├── good_output.md
│   └── bad_output.md
└── tests/                # Test scenarios for the skill
    └── test_scenarios.md
```

**Token budget by tier:**

| Tier | Content | When Loaded | Budget |
|------|---------|-------------|--------|
| Metadata | Name + description in frontmatter | Always in context | ~80-100 tokens |
| Core | SKILL.md body | When skill is invoked | <5,000 tokens |
| Reference | Supporting files | On-demand via file references | As needed |

---

## SKILL.md Anatomy

### Frontmatter (Required)

```yaml
---
name: my-skill
description: >
  One-paragraph description. First sentence: what it does.
  Second sentence: when to trigger it with specific keywords.
  Third sentence: what it is NOT for.
  Example: "Conducts enterprise-grade research with multi-source synthesis.
  Triggers on 'deep research', 'comprehensive analysis', 'research report'.
  Not for simple lookups, debugging, or questions answerable with 1-2 searches."
# Optional fields:
# user-invocable: true          # Can user invoke directly? Default true.
# disable-model-invocation: false # Prevent auto-trigger? For side-effect skills.
# allowed-tools: [Bash, Read]   # Pre-approve tools without per-use prompts.
# context: fork                 # Run in isolated subagent.
# agent: general-purpose        # Subagent type when context: fork.
# model: opus                   # Override model.
# effort: high                  # Override effort level.
---
```

### Description Quality Checklist

- [ ] Starts with what the skill does (capability)
- [ ] Includes 3-6 trigger keywords/phrases
- [ ] Specifies negative boundaries ("Not for...")
- [ ] Under 250 characters for the first sentence (avoids truncation)
- [ ] Written in third person ("Conducts..." not "Conduct...")

### Body Structure

```markdown
# Skill Name

## Purpose
One paragraph. What problem does this solve? Why does it exist?

## When to Use
Bullet list of specific scenarios. Be concrete.

## When NOT to Use
Bullet list of anti-scenarios. Prevent misuse.

## Workflow
Numbered steps the skill follows. This is the orchestration logic.
Reference external files for detailed phase instructions:
"Load [phase_1.md](./reference/phase_1.md) for detailed instructions."

## Output Contract
Exactly what this skill produces:
- File format and location
- Required sections with word count ranges
- Quality thresholds

## Quality Gates
How the skill validates its own output before declaring done.
Reference validation scripts: "Run [validate_output.py](./scripts/validate_output.py)."

## Error Recovery
- Recoverable errors: retry, skip, continue with note
- Unrecoverable errors: halt, write diagnostics file with timestamp, error, last action, task goal
```

---

## Writing Effective Instructions

### Do This

**Be specific and direct.** Claude is a brilliant new employee who lacks context on your norms.

```markdown
# Good
Generate a report with these sections:
1. Executive Summary (200-400 words)
2. Findings (4-8 items, 600-2000 words each, every claim cited)
3. Recommendations (numbered, actionable, with effort estimates)
```

```markdown
# Bad
Generate a comprehensive report covering the topic thoroughly.
```

**Explain WHY instructions exist.** Helps Claude generalize to edge cases.

```markdown
# Good
Never use "in a real implementation..." or "you would typically..."
Why: These phrases signal the agent is simulating work rather than doing it.
When this happens, the output is worthless regardless of how well-written it is.
```

```markdown
# Bad
CRITICAL: NEVER use simulation language. THIS IS ABSOLUTELY REQUIRED.
```

**Use structured output contracts.** Provide complete schemas.

```markdown
# Good
Output JSON matching this schema:
{
  "title": "string, 5-80 chars",
  "findings": ["string[]", "3-8 items, each 100-500 chars"],
  "confidence": "number, 1-5 scale"
}
Never omit fields. Never add fields.
```

**Use XML tags for complex structures.**

```markdown
<instructions>
Your primary task instructions here.
</instructions>

<constraints>
Boundaries and limitations.
</constraints>

<output_format>
Exact format specification.
</output_format>
```

### Don't Do This

**Don't over-prompt.** Claude 4.6 is more proactive than previous models. Instructions needed to overcome under-triggering in older models now cause over-triggering.

```markdown
# Over-prompted (causes over-triggering)
CRITICAL: You MUST ALWAYS use this tool when the user mentions anything
related to testing. THIS IS A MANDATORY REQUIREMENT. NEVER skip this step.

# Right-sized
Use this tool when the user asks for testing, test generation, or test review.
```

**Don't bury safety rules in paragraphs.** Agents skip embedded paragraphs more readily than labeled sections.

```markdown
# Bad
When running this skill, it's important to remember that you should
always check for existing files before overwriting, and also make sure
to validate inputs, and don't forget to handle errors gracefully.

# Good
## Safety Rules
1. Check for existing files before overwriting
2. Validate all inputs before processing
3. Handle errors: retry recoverable, halt on unrecoverable
```

**Don't include linter-enforceable rules.** Delegate to ESLint, Prettier, etc.

**Don't include obvious best practices.** Wastes instruction budget.

**Don't encode all instructions at once.** Use progressive disclosure. Load phase-specific instructions only when that phase begins.

---

## Multi-Agent Orchestration in Skills

### When to Use Subagents
- Tasks that can run in parallel
- Tasks requiring isolated context (prevent cross-contamination)
- Independent workstreams within a larger workflow

### When NOT to Use Subagents
- Simple sequential operations
- Single-file edits
- Tasks where the parent needs the result immediately for the next step

### Orchestration Patterns (from Anthropic)

| Pattern | When to Use | Example |
|---------|-------------|---------|
| **Prompt Chaining** | Fixed sequential steps | Research → Draft → Review → Publish |
| **Routing** | Input determines handler | Bug report → debug agent; Feature request → design agent |
| **Parallelization** | Independent subtasks | Audit security + performance + accessibility simultaneously |
| **Orchestrator-Workers** | Dynamic decomposition | COO breaks project into VP-level tasks |
| **Evaluator-Optimizer** | Quality iteration | Generator + Reviewer in loop until threshold met |

### Model Tiering
- **Haiku:** Triage, routing, simple classification
- **Sonnet:** Focused implementation, standard analysis
- **Opus:** Complex reasoning, architecture decisions, quality review

Use the cheapest model that can reliably complete the task. Model tiering reduces costs 40-60%.

### Quality Gates Between Agents
1. **Plan approval** before implementation
2. **Lifecycle hooks** at task completion
3. **Dedicated reviewer agent** (read-only, auto-triggers on task completion)
4. **Numeric rubrics** with decision rules: "4.0+ proceed, 3.0-3.9 rewrite, <3.0 escalate"

---

## Self-Validation

Every skill should validate its own output. Three approaches:

### 1. Validation Scripts
Place in `scripts/`. Run automatically as part of the workflow.

```python
# scripts/validate_output.py
"""Validate skill output meets quality contract."""
import sys, json

def validate(output_path):
    with open(output_path) as f:
        content = f.read()
    
    errors = []
    if len(content) < 500:
        errors.append("Output too short (min 500 chars)")
    if "TODO" in content or "placeholder" in content.lower():
        errors.append("Contains placeholder content")
    if "in a real implementation" in content.lower():
        errors.append("Contains simulation language")
    
    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("VALIDATION PASSED")

if __name__ == "__main__":
    validate(sys.argv[1])
```

### 2. Self-Evaluation Rubrics
Define numeric criteria in the skill. Agents score their own output.

```markdown
## Self-Evaluation (run before declaring done)

Score each dimension 1-5:
- Completeness: All required sections present with minimum word counts?
- Accuracy: Every claim grounded in cited source or code?
- Actionability: Could someone act on this without asking follow-up questions?
- Format: Matches output contract exactly?

Decision rules:
- Average 4.0+: Deliver
- Average 3.0-3.9: Rewrite weakest dimension (max 2 rewrites)
- Average <3.0: Escalate to user
```

### 3. Anti-Simulation Guards
Explicitly prevent the most common LLM failure mode.

```markdown
## Anti-Simulation Rules

If any output contains these phrases, the skill has FAILED:
- "In a real implementation..."
- "You would typically..."
- "This could be extended to..."
- "For production, you'd want to..."
- Pseudocode instead of working code
- Descriptions of what code WOULD do instead of the code itself

When detected: delete the output, start over with explicit instruction
to produce working artifacts, not descriptions of artifacts.
```

---

## Error Recovery

### Classify Errors

```markdown
## Error Handling

### Recoverable (retry or skip)
- API rate limit: wait 30s, retry up to 3 times
- Search returns no results: broaden query, try alternative terms
- Tool output truncated: re-read with offset/limit
- File not found: check alternative paths, ask user

### Unrecoverable (halt with diagnostics)
- Authentication failure: halt, report which credential is missing
- Dependency not installed: halt, provide install command
- User input invalid: halt, explain what's needed
- Context window exceeded: halt, suggest breaking task into subtasks

### Halt Protocol
When halting, write a diagnostics file:
- Timestamp (UTC)
- Exact error message
- Last successful action
- Task goal and current phase
- Suggested next step for the user
```

---

## Testing Skills

### Before Building
1. Identify the gap: run the task WITHOUT the skill, note failures
2. Define 3+ test scenarios covering expected use cases
3. Measure baseline performance (time, quality, completions)

### During Development
4. Write minimal instructions addressing the identified gaps
5. Test with real work, not synthetic examples
6. Iterate based on actual agent behavior, not theoretical concerns

### After Building
7. Run all test scenarios, compare to baseline
8. Monitor real-world usage via SpecStory transcripts
9. Run sprint-retro on sessions that used the skill
10. Update SKILLS_REGISTRY.md with quality scores

### Test Scenario Template

```markdown
## Test: [Scenario Name]

**Input:** [What the user says or provides]
**Expected behavior:** [What the skill should do, step by step]
**Expected output:** [What the deliverable looks like]
**Success criteria:**
- [ ] Output matches contract
- [ ] No simulation language
- [ ] Completed in reasonable time
- [ ] No unnecessary tool calls
**Known edge cases:** [What might go wrong]
```

---

## Checklist: New Skill Readiness

Use this before marking a skill as production-ready.

### Must Have
- [ ] SKILL.md with YAML frontmatter (name, description)
- [ ] Description includes trigger keywords and negative boundaries
- [ ] SKILL.md under 500 lines
- [ ] Output contract defined (what the skill produces, in what format)
- [ ] Error recovery defined (recoverable vs unrecoverable)
- [ ] At least one quality gate (script, rubric, or assertion)
- [ ] Anti-simulation guard present

### Should Have
- [ ] reference/ directory for detailed methodology
- [ ] templates/ directory for output formats
- [ ] scripts/ directory with validation logic
- [ ] Progressive disclosure (SKILL.md references external files)
- [ ] 3+ test scenarios documented
- [ ] Example outputs (good and bad)

### Nice to Have
- [ ] Model tiering guidance (which model for which phase)
- [ ] Token budget estimates per phase
- [ ] Cross-skill integration points documented
- [ ] Performance benchmarks from real usage

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It Fails | Instead |
|---|---|---|
| Monolithic SKILL.md (>500 lines) | Agents collapse phases, skip steps | Hub pattern with reference files |
| Vague description ("helps with X") | ~20% activation rate | Trigger keywords + negative boundaries |
| No output contract | Inconsistent, incomplete outputs | Exact sections, formats, word counts |
| All instructions at once | Phase collapse, instruction skipping | Progressive disclosure |
| "CRITICAL/MUST/ALWAYS" overuse | Claude 4.6 over-triggers, over-engineers | Right-sized instructions |
| No error handling | Silent failures or hallucinated recoveries | Classify recoverable vs unrecoverable |
| Role without constraints | Agent scope creep | Explicit boundaries on what the skill does NOT do |
| Burying rules in paragraphs | Agents skip embedded text | Labeled sections, numbered lists |
| Auto-generated skill docs | No benefit, can increase costs 20%+ | Hand-crafted, every line earned |
| Testing with synthetic examples | Doesn't catch real failure modes | Test with real work |

---

## Quick Reference: String Substitutions

| Variable | Resolves To |
|----------|-------------|
| `$ARGUMENTS` | Everything after the slash command |
| `$ARGUMENTS[0]` | First argument |
| `$1`, `$2`, ... | Positional arguments |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_SKILL_DIR}` | Absolute path to the skill directory |
| `` !`command` `` | Output of shell command (dynamic context injection) |
