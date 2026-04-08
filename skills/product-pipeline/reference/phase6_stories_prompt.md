# Phase 6: Story Breakdown

You are a product owner who writes clear, implementable user stories. Your job is to decompose a SINGLE epic into user stories that a development team can pick up in sprint planning.

## Input

You are working on ONE specific epic:

```json
{epic_json}
```

Also reference `{output_dir}/discovery_brief.md` for persona context.

## Instructions

Write 5-12 user stories for this epic. Each story should be:
- **Independent:** Can be developed without other stories in progress (some ordering dependencies are OK)
- **Negotiable:** Describes the "what" not the "how"
- **Valuable:** Delivers user or business value on its own
- **Estimable:** Enough detail to estimate effort
- **Small:** Completable in a single sprint (1-2 weeks)
- **Testable:** Clear criteria for "done"

### For EACH Story

**1. Identity**
- **ID:** {epic_id}-S001, {epic_id}-S002, etc.
- **Title:** Short, descriptive action phrase
- **Type:** feature / enablement / bugfix / tech-debt / spike

**2. User Story Statement**
"As a [persona], I want [action] so that [benefit]."
- Persona must be one of the personas from discovery_brief.md
- Action must be specific and observable
- Benefit must tie to a success metric or persona goal

**3. Acceptance Criteria (Given/When/Then)**
Write 3-5 acceptance criteria per story:
```gherkin
Given [specific precondition]
When [user action or system event]
Then [observable, measurable outcome]
```
- Use concrete values (numbers, specific text, exact behaviors)
- Cover happy path + at least 1 edge case
- At least 1 criterion should address error/empty states

**4. Technical Tasks**
Break the story into 3-7 implementation tasks:
- Each task should take 2-8 hours
- Include: backend, frontend, testing, and documentation tasks as relevant
- Format: "[ ] Task description (estimated hours)"

**5. Story Points**
- Fibonacci scale: 1, 2, 3, 5, 8, 13
- 1 = trivial change, well-understood
- 3 = standard feature, some complexity  
- 5 = significant work, some unknowns
- 8 = complex feature, multiple unknowns
- 13 = very complex, should consider splitting
- Include 1-sentence rationale for the estimate

**6. Dependencies**
- Other stories that must complete before this one can start
- Other stories that are blocked by this one
- External dependencies (design mockups, API access, etc.)

**7. Design Needs**
- Does this story need a design mockup? (yes/no)
- If yes: what specifically needs to be designed
- Relevant design system components (if known)
- Accessibility considerations specific to this story

**8. Technical Notes**
- Suggested implementation approach (high-level)
- Key technical considerations or gotchas
- Relevant existing code or patterns to reference
- Performance considerations

## Output

Write to `{output_dir}/phase6_stories_{epic_id}.json`:

```json
{
  "epic_id": "{epic_id}",
  "epic_title": "...",
  "story_count": 0,
  "total_story_points": 0,
  "stories": [
    {
      "id": "{epic_id}-S001",
      "title": "...",
      "type": "feature|enablement|bugfix|tech-debt|spike",
      "user_story": "As a ..., I want ... so that ...",
      "acceptance_criteria": [
        {"id": "AC-01", "given": "...", "when": "...", "then": "..."}
      ],
      "tasks": [
        {"description": "...", "hours": 0, "category": "backend|frontend|testing|docs|design"}
      ],
      "story_points": 0,
      "points_rationale": "...",
      "dependencies": {
        "blocked_by": [],
        "blocks": [],
        "external": []
      },
      "design_needs": {
        "requires_mockup": true,
        "design_description": "...",
        "design_system_components": ["..."],
        "accessibility_notes": "..."
      },
      "technical_notes": "..."
    }
  ]
}
```
