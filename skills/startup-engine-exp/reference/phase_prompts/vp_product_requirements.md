# Phase 3: Requirements Analysis

## CRITICAL: IMPLEMENTABLE REQUIREMENTS

You are writing requirements that developers will directly implement. Every user story must
be specific enough to code against. Every acceptance criterion must be testable. If a developer
reads your stories.json and cannot start writing code immediately, you have failed.

Do NOT produce vague, aspirational requirements. Produce concrete, buildable specifications.

## Input
- Read: {workspace}/artifacts/research/{epic}/discovery_brief.md
- Read: {workspace}/state/sprint_plan.json

## Process

### Step 1: Feature Definition
Following /product-pipeline Phase 4 patterns, decompose the concept into features:
- Extract features from real user needs identified in research (not hypothetical needs)
- Score each with RICE (Reach, Impact, Confidence, Effort)
- Define MVP boundary (must/should/could/won't)

### Step 2: Epic Definition
Following /product-pipeline Phase 5 patterns:
- Group MVP features into 3-7 epics
- Write acceptance criteria in Gherkin (Given/When/Then) — these must be directly automatable as tests
- Define dependencies and sequencing

### Step 3: Story Breakdown
Following /product-pipeline Phase 6 patterns:
- Decompose each epic into 5-12 user stories
- Each story must include: user story statement, acceptance criteria (Given/When/Then), implementation tasks with hour estimates, story points, design needs, technical notes
- Spawn one agent per epic for parallel story writing if needed

### Step 4: Documentation
- Use /tools:doc-generate to create API documentation from requirements
- Use /tools:accessibility-audit to bake a11y requirements into stories
- Use /tools:compliance-check if regulatory requirements apply

### Step 5: Self-Review
Review all output against quality criteria:
- Every story has 3+ acceptance criteria in Given/When/Then format
- No placeholder text (TBD, TODO, "to be determined")
- Design needs flagged for every user-facing story
- Technical notes for every backend story
- A developer could start coding from any story without asking clarifying questions
If quality < 70/100, revise (max 2 iterations).

## Output
Write to {workspace}/artifacts/requirements/{epic}/:
- features.json
- epics.json
- stories.json (consolidated — this is the primary handoff artifact to engineering)
- prd.md (human-readable product requirements document)

## State Update
Update {workspace}/state/company_state.json:
- Set `sdlc.phases.requirements.status` to `"complete"`
- Set `sdlc.phases.requirements.completed_at` to current UTC ISO timestamp (with Z suffix)
