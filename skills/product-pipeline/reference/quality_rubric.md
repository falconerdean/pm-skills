# Quality Rubric for Synthesis Gates

## Scoring Dimensions

| Dimension | Weight | 0-25 (Fail) | 26-50 (Weak) | 51-75 (Acceptable) | 76-100 (Strong) |
|-----------|--------|-------------|--------------|---------------------|-----------------|
| Evidence Grounding | 25% | Claims unsupported | Some claims supported | Most claims have evidence | All claims cite specific data |
| Internal Consistency | 25% | Major contradictions | Some contradictions | Minor tensions only | Fully coherent across artifacts |
| Completeness | 20% | Missing required sections | Key gaps exist | Minor gaps only | All required fields populated |
| Specificity | 15% | Vague, generic language | Mix of vague/specific | Mostly concrete | Measurable, testable, concrete |
| Actionability | 15% | Cannot act on output | Needs significant clarification | Mostly actionable | Developer/designer can act immediately |

## Threshold

- **Pass:** Weighted score >= 70/100
- **Fail:** Below 70 — trigger refinement iteration
- **Max iterations:** 3 per gate

## Scoring Formula

```
total = (evidence * 0.25) + (consistency * 0.25) + (completeness * 0.20) + (specificity * 0.15) + (actionability * 0.15)
```

## Gate-Specific Criteria

### Gate 1: Discovery Convergence

**Evidence Grounding:**
- Problem statement references specific research findings
- Personas based on identified user pain points (not invented)
- Market data cited for opportunity sizing

**Internal Consistency:**
- Recommended concept addresses the stated problem
- Personas' needs align with identified pain points
- Success metrics relate to the opportunity hypothesis

**Completeness:**
- Problem statement present and well-formed
- At least 2 user personas defined
- Success metrics (primary + 2 secondary) defined
- At least 1 concept fully described
- Constraints and assumptions listed

**Specificity:**
- Personas have concrete goals, not vague aspirations
- Metrics are quantifiable (not "improve engagement")
- Concept features are described, not just named

**Actionability:**
- A product team could start feature definition from this brief
- No critical open questions without a path to resolution

### Gate 2: Definition Convergence

**Evidence Grounding:**
- Every feature traces to a persona need or research finding
- RICE scores use defensible estimates
- Epic groupings have logical rationale

**Internal Consistency:**
- Every MVP feature appears in at least one epic
- Every epic appears in at least one story set
- Story dependencies don't create circular references
- Story points are consistent within similar-complexity stories

**Completeness:**
- All MVP features covered by stories
- Every story has acceptance criteria (Given/When/Then)
- Every story has task breakdown
- Story points assigned to every story
- Design needs flagged for user-facing stories

**Specificity:**
- Acceptance criteria use concrete values, not "appropriate" or "reasonable"
- Tasks are implementation-level, not vague "build the thing"
- Dependencies reference specific story IDs

**Actionability:**
- A sprint planning session could use these stories
- Design needs are specific enough to brief a designer
- Technical notes give enough context for estimation

### Final Gate: Specification Convergence

**Cross-Validation Checks:**
- Every design system component maps to at least one story's design needs
- API endpoints cover all stories with backend requirements
- Infrastructure design supports the implied scale
- Security architecture covers all personas' access patterns
- Accessibility requirements reflected in both design and tech specs
- No technology choices that contradict each other

## Gap Classification

When scoring reveals gaps, classify each:

| Type | Description | Refinement Action |
|------|-------------|-------------------|
| RESEARCH | Missing market/user data | Targeted WebSearch (2 min time-box) |
| LOGIC | Contradiction between artifacts | Reason through and resolve inline |
| SPECIFICITY | Vague language needs concrete detail | Add details from existing artifacts |
| STRUCTURE | Missing required section/field | Generate from available information |
| SCOPE | Requirement outside current scope | Document as limitation, don't address |
