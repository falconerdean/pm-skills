---
name: product-pipeline
description: >
  End-to-end product development pipeline. Takes a simple idea with desired outcomes
  and produces fully-defined epics, stories, design system spec, and technical architecture
  through multi-agent orchestration with iterative quality gates.
  Triggers on: "product pipeline", "idea to epic", "product development cycle",
  "full product spec", "product dev pipeline", "idea to stories".
---

# Product Development Pipeline

## Core Purpose

Transform a product idea into a complete, implementation-ready specification through
an 8-phase multi-agent pipeline with iterative quality gates. Produces: discovery brief,
prioritized features, epics with acceptance criteria, user stories, design system spec,
and technical architecture.

**Autonomy Principle:** Run the full pipeline autonomously. Only pause for user input
when: (a) the idea statement is missing desired outcomes, (b) a quality gate fails after
3 iterations, or (c) the user explicitly requested a checkpoint.

---

## Decision Tree

```
Input Analysis
├── Has idea + outcomes? → CONTINUE
├── Has only idea? → Ask for 2-5 desired outcomes, then CONTINUE
├── Has existing pipeline_state.json? → RESUME mode
├── Has --re-run flag? → RE-RUN specific phases
└── No idea provided? → Ask for idea + outcomes

Mode Selection
├── --quick → quick (Phases 1,4,5,8 — rapid epic definition)
├── (default) → standard (Phases 1-6,8 — full cycle, skip design system)
└── --deep → deep (Phases 1-8 — complete with design system)
```

---

## Execution

**On invocation, follow these steps exactly:**

### Step 0: Initialize

1. Load [orchestration_protocol.md](./reference/orchestration_protocol.md) — this is the master execution guide
2. Parse the input: extract `idea_statement` and `outcomes_list` from $ARGUMENTS
3. If outcomes are missing, ask the user for 2-5 desired outcomes before proceeding
4. Determine execution mode (quick/standard/deep) from flags or default to standard
5. Generate a slug from the idea (lowercase, hyphens, max 30 chars)
6. Create output directory: `~/Documents/product_pipeline_{slug}_{YYYYMMDD}/`
7. Initialize `pipeline_state.json` from [pipeline_state_template.json](./templates/pipeline_state_template.json)
8. Load [quality_rubric.md](./reference/quality_rubric.md) — needed for all synthesis gates

### Step 1: Stage 1 — Discovery (Phases 1-3)

**Phase 1: Research & User Discovery**
- Load [phase1_research_prompt.md](./reference/phase1_research_prompt.md)
- Substitute variables: `{idea_statement}`, `{outcomes_list}`, `{output_dir}`
- Spawn Agent (foreground, general-purpose) with the populated prompt
- On completion, update pipeline_state.json: phase1.status = "completed"

**Phases 2+3: Problem Framing & Concepts (PARALLEL)**
- Load [phase2_problem_frame_prompt.md](./reference/phase2_problem_frame_prompt.md)
- Load [phase3_concepts_prompt.md](./reference/phase3_concepts_prompt.md)
- Substitute variables in both (include Phase 1 output path)
- Spawn BOTH agents in a single message (parallel execution)
- On completion, update pipeline_state.json for both phases

**Synthesis Gate 1: Discovery Convergence**
- Load [synthesis_gate_prompt.md](./reference/synthesis_gate_prompt.md) with gate_id=1
- Agent reads all Phase 1-3 outputs, merges into discovery_brief.md
- Apply quality rubric (target: 70/100)
- If below threshold and iterations < 3: identify gaps, re-run targeted research
- If threshold met or max iterations reached: proceed
- Write `{output_dir}/discovery_brief.md`

### Step 2: Stage 2 — Definition (Phases 4-6)

**Phase 4: Feature Definition & Prioritization**
- Load [phase4_features_prompt.md](./reference/phase4_features_prompt.md)
- Input: discovery_brief.md
- Spawn Agent (foreground)
- Output: phase4_features.json

**Phase 5: Epic Definition**
- Load [phase5_epics_prompt.md](./reference/phase5_epics_prompt.md)
- Input: phase4_features.json + discovery_brief.md
- Spawn Agent (foreground)
- Output: phase5_epics.json

**Phase 6: Story Breakdown (PARALLEL — one agent per epic)**
- Load [phase6_stories_prompt.md](./reference/phase6_stories_prompt.md)
- Read phase5_epics.json, extract each epic
- Spawn ONE agent per epic in a SINGLE message (parallel execution)
- Each agent writes: phase6_stories_{epic_id}.json
- Collect all story files on completion

**Synthesis Gate 2: Definition Convergence**
- Load synthesis_gate_prompt.md with gate_id=2
- Merge all story files into story_map.json
- Validate: every MVP feature covered, no circular deps, ACs are testable
- Apply quality rubric
- Write `{output_dir}/story_map.json`

### Step 3: Stage 3 — Specification (Phases 7-8, PARALLEL)

**Skip Phase 7 in quick and standard modes.**

**Phases 7+8: Design System & Tech Architecture (PARALLEL)**
- Load [phase7_design_system_prompt.md](./reference/phase7_design_system_prompt.md)
- Load [phase8_tech_arch_prompt.md](./reference/phase8_tech_arch_prompt.md)
- Spawn BOTH agents in a single message (parallel execution)
- Phase 7 output: phase7_design_system.md
- Phase 8 output: phase8_tech_architecture.md

**Final Gate: Package**
- Load [final_spec_template.md](./templates/final_spec_template.md)
- Merge all artifacts into FINAL_PRODUCT_SPEC.md
- Cross-validate design system against tech architecture
- Present summary to user with file location

### Step 4: Completion

1. Update pipeline_state.json: all phases completed
2. Print summary: phases run, quality scores, artifact locations
3. Open FINAL_PRODUCT_SPEC.md for user review

---

## Resume & Re-Run

**Resume:** If `pipeline_state.json` exists in the output directory:
- Read current state
- Identify last completed phase
- Ask user: "Resume from Phase {N}?" 
- Continue from that phase, using existing artifacts as inputs

**Re-Run:** If user specifies `--re-run phase2,phase7`:
- Load existing pipeline state
- Re-execute only specified phases with any new feedback
- Re-run all downstream synthesis gates
- Produce updated FINAL_PRODUCT_SPEC.md

---

## Output Contract

All output to `~/Documents/product_pipeline_{slug}_{YYYYMMDD}/`:

| File | Description |
|------|-------------|
| `pipeline_state.json` | Progress tracker, quality scores |
| `phase1_research.json` | Market research, user insights |
| `phase2_problem_frame.json` | Problem statement, personas, metrics |
| `phase3_concepts.json` | Solution concepts, feasibility |
| `discovery_brief.md` | Stage 1 synthesis |
| `phase4_features.json` | Feature inventory, RICE scores |
| `phase5_epics.json` | Epic definitions with AC |
| `phase6_stories_*.json` | Stories per epic |
| `story_map.json` | Stage 2 synthesis |
| `phase7_design_system.md` | Design tokens, components, patterns |
| `phase8_tech_architecture.md` | System architecture, API, infra |
| `FINAL_PRODUCT_SPEC.md` | Consolidated deliverable |
