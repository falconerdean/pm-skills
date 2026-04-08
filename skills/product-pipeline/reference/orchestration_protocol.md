# Orchestration Protocol

## Execution Order and Dependencies

```
Phase 1 (Research) ─────────────────────────┐
                                             │
Phase 2 (Problem Frame) ──┐  [parallel]      ├── Gate 1 ──┐
Phase 3 (Concepts) ───────┘                  │             │
                          depends on Phase 1 ─┘             │
                                                            │
Phase 4 (Features) ────────────────────────────────────────┤
    depends on Gate 1 output                                │
                                                            │
Phase 5 (Epics) ───────────────────────────────────────────┤
    depends on Phase 4                                      │
                                                            │
Phase 6 (Stories) ─── N parallel agents ───── Gate 2 ──────┤
    depends on Phase 5                                      │
    spawns 1 agent per epic                                 │
                                                            │
Phase 7 (Design System) ──┐  [parallel]                     │
Phase 8 (Tech Arch) ──────┘                 ── Final Gate ──┘
    both depend on Gate 2 output
```

## Agent Spawning Rules

### Parallel Execution
When spawning parallel agents, ALL agents MUST be launched in a SINGLE message
with multiple Agent tool calls. This is how Claude Code executes them concurrently.

**Parallel groups:**
1. Phases 2+3: Two agents in one message after Phase 1 completes
2. Phase 6 stories: N agents (one per epic) in one message after Phase 5
3. Phases 7+8: Two agents in one message after Gate 2 completes

### Agent Configuration
- All agents use `subagent_type: "general-purpose"`
- All agents run in foreground EXCEPT Phase 6 story agents which use `run_in_background: true`
- Each agent's prompt includes the full phase prompt from reference/ with variables substituted
- Each agent writes its output to a specific file in the output directory

### Variable Substitution
Before passing a phase prompt to an agent, substitute these variables:
- `{idea_statement}` — The user's original idea
- `{outcomes_list}` — Bullet list of desired outcomes
- `{output_dir}` — Full path to output directory
- `{phase_N_output}` — Content or path of a prior phase's output file
- `{epic_json}` — JSON of a single epic (Phase 6 only)
- `{epic_id}` — Sanitized epic identifier (Phase 6 only)

## Synthesis Gate Protocol

Each gate follows this exact sequence:

### 1. Merge
Read all input artifacts. Produce a single coherent document that:
- Preserves all critical information from each input
- Resolves any contradictions (preferring higher-evidence claims)
- Adds cross-references between related elements
- Structures output according to the gate's template

### 2. Critique
Score the merged output against the quality rubric (see quality_rubric.md).
For each dimension, assign a score 0-100. Compute weighted total.

Identify specific gaps:
- Missing information that should be present
- Vague language that should be specific
- Contradictions between sections
- Claims without supporting evidence

### 3. Refine (if score < 70)
For each identified gap:
- If it's a RESEARCH gap: spawn a targeted WebSearch (time-box 2 min)
- If it's a LOGIC gap: reason through the contradiction and resolve it
- If it's a SPECIFICITY gap: add concrete details from existing artifacts

### 4. Re-score
After refinement, re-score. If still below 70 and iterations < 3, repeat.
If at max iterations, proceed with limitations noted.

### 5. Write Output
Write the final merged document to the designated output file.
Update pipeline_state.json with the gate's quality score and iteration count.

## State Management

### pipeline_state.json Updates
After EVERY phase completion or gate evaluation:
1. Read current pipeline_state.json
2. Update the relevant phase/gate entry
3. Write back to disk

### Error Recovery
If an agent fails or produces empty output:
1. Log the failure in pipeline_state.json
2. Retry the agent once with the same prompt
3. If retry fails, mark phase as "failed" and ask user for guidance

### Checkpoint Protocol
After each synthesis gate completes successfully:
- Print a brief status update to the user
- Include: phases completed, current quality score, next steps
- Do NOT wait for user input unless quality gate failed after max iterations

## Mode-Specific Phase Selection

| Phase | Quick | Standard | Deep |
|-------|-------|----------|------|
| 1. Research | YES | YES | YES |
| 2. Problem Frame | skip | YES | YES |
| 3. Concepts | skip | YES | YES |
| Gate 1 | skip (use Phase 1 directly) | YES | YES |
| 4. Features | YES | YES | YES |
| 5. Epics | YES | YES | YES |
| 6. Stories | skip | YES | YES |
| Gate 2 | skip | YES | YES |
| 7. Design System | skip | skip | YES |
| 8. Tech Arch | YES | YES | YES |
| Final Gate | YES | YES | YES |

In Quick mode:
- Phase 1 output feeds directly into Phase 4 (no problem framing or concepts)
- Phase 5 output feeds directly into Phase 8 (no story breakdown)
- Final output is: research + epics + tech architecture
