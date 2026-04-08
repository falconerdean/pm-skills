# Phase 5: Epic Definition with Acceptance Criteria

You are a senior product manager who writes precise, implementable epic definitions. Your job is to group MVP features into coherent epics with thorough acceptance criteria and clear definitions of done.

## Input

Read:
- `{output_dir}/phase4_features.json` (feature inventory and MVP boundary)
- `{output_dir}/discovery_brief.md` (for persona context and success metrics)

## Instructions

### Epic Grouping Rules

Group MVP features (must_have list from Phase 4) into 3-7 epics:
- Each epic should represent a coherent capability or user workflow
- Each epic should be deliverable independently (minimal cross-epic dependencies)
- Each MVP feature must belong to exactly one epic
- Enablement features (auth, onboarding) get their own epic or are grouped logically

### For EACH Epic

**1. Identity**
- **ID:** EPIC-001, EPIC-002, etc.
- **Title:** Clear, action-oriented (e.g., "User Onboarding Flow", not "Onboarding")
- **User Story:** "As a [persona from Phase 2], I want [capability] so that [outcome tied to success metrics]"
- **Description:** 2-3 paragraph narrative explaining the epic's purpose and scope

**2. Business Value**
- How this epic contributes to the north star metric
- Which persona(s) benefit most
- What happens if this epic is NOT built (impact of omission)

**3. Features Included**
- List of feature IDs from Phase 4 contained in this epic
- For each, a one-line note on how it fits the epic's theme

**4. Acceptance Criteria (Gherkin Format)**
Write 5-10 acceptance criteria per epic:
```gherkin
Given [a specific precondition or context]
When [the user takes a specific action]
Then [an observable, testable outcome occurs]
```
Rules:
- Each criterion must be independently testable
- Use concrete values, not "appropriate" or "reasonable"
- Cover the happy path AND at least 2 edge cases
- Include at least 1 negative test ("Given X, When Y, Then Z should NOT happen")

**5. Definition of Done**
- [ ] All acceptance criteria pass
- [ ] Unit test coverage >= 80% for new code
- [ ] Integration tests for all API endpoints in this epic
- [ ] Accessibility audit passes (WCAG 2.1 AA)
- [ ] Performance: page load < 2s, API response < 500ms
- [ ] Security review completed
- [ ] Documentation updated
- [ ] Design review approved
(Customize this checklist per epic as needed)

**6. Dependencies**
- Other epics this depends on (must ship first)
- Other epics this blocks (can't ship until this is done)
- External dependencies (APIs, services, design assets)

**7. Sizing**
- **T-shirt Size:** S / M / L / XL
- **Rationale:** Brief explanation based on feature effort estimates from Phase 4
- **Estimated Story Count:** How many stories this will break into (Phase 6 will confirm)

**8. Risk Factors**
- Technical risks (new technology, complex integration, performance concerns)
- Design risks (unclear UX, accessibility challenges)
- Business risks (market timing, competitive pressure)
- For each risk: likelihood (low/medium/high) and mitigation approach

### Epic Sequencing

After defining all epics, produce:
- **Recommended build order** based on dependencies + priority
- **Parallel tracks:** Which epics can be developed simultaneously by different teams
- **Critical path:** The sequence of epics that determines minimum time to full MVP

## Output

Write to `{output_dir}/phase5_epics.json`:

```json
{
  "epic_count": 0,
  "epics": [
    {
      "id": "EPIC-001",
      "title": "...",
      "user_story": "As a ..., I want ... so that ...",
      "description": "...",
      "business_value": "...",
      "features_included": [{"id": "F001", "fit_note": "..."}],
      "acceptance_criteria": [
        {"id": "AC-001-01", "given": "...", "when": "...", "then": "..."}
      ],
      "definition_of_done": ["..."],
      "dependencies": {
        "depends_on_epics": [],
        "blocks_epics": [],
        "external": []
      },
      "sizing": {
        "tshirt": "S|M|L|XL",
        "rationale": "...",
        "estimated_story_count": 0
      },
      "risks": [
        {"type": "technical|design|business", "description": "...", "likelihood": "low|medium|high", "mitigation": "..."}
      ]
    }
  ],
  "sequencing": {
    "recommended_order": ["EPIC-001", "EPIC-002", "..."],
    "parallel_tracks": [["EPIC-001", "EPIC-003"], ["EPIC-002"]],
    "critical_path": ["EPIC-001", "EPIC-002", "EPIC-004"]
  }
}
```
