# Phase 4: UX/UI Design

## CRITICAL: REAL DESIGNS, NOT DESCRIPTIONS OF DESIGNS

You are producing real design artifacts. Use the Figma MCP to create actual diagrams and
wireframes. Write actual component specifications with real token values. Create actual
content entries in the CMS. Do NOT write prose describing what a design "would look like."
Create the design.

## Input
- Read: {workspace}/artifacts/requirements/{epic}/stories.json
- Read: {workspace}/artifacts/research/{epic}/discovery_brief.md (personas)
- Read: {workspace}/artifacts/research/{epic}/screenshots/ (competitor reference)

## Process

### Step 1: UX Flows
Use /tools:ux-flows with the stories and personas:
- Map user journeys for each persona through the feature
- Identify key screens and transitions
- Document interaction patterns (forms, navigation, feedback)
- Flag edge cases (errors, empty states, loading)

### Step 2: Wireframes & Mockups (Figma)
Use Figma MCP tools to create real designs:
- mcp__claude_ai_Figma__generate_diagram: Create user flow diagrams in FigJam
- mcp__claude_ai_Figma__create_new_file: Create wireframe mockups
- mcp__claude_ai_Figma__search_design_system: Find existing reusable components
- mcp__claude_ai_Figma__get_variable_defs: Get current design tokens

### Step 3: UI Specification
Generate a concrete design system spec for this epic:
- Design tokens with real values (hex colors, px sizes, font stacks)
- Component inventory with props, variants, and states
- Responsive breakpoints with specific behavior per breakpoint
- Accessibility requirements (WCAG 2.1 AA) with specific implementation notes
Use /tools:accessibility-audit to validate.

### Step 4: Content Strategy
- Write all actual UI microcopy (button labels, error messages, onboarding text)
- Define content structure for CMS-driven content
- Use mcp__Sanity__get_schema to check existing content model
- Use mcp__Sanity__create_documents_from_markdown for real content entries

### Step 5: Design Review
Run /tools:multi-agent-review on all design artifacts:
- Is the design technically feasible to build?
- Are components well-defined enough for a developer to implement?
- Do designs address every story's design_needs field?
If critical issues found, revise (max 2 iterations).

## Output
Write to {workspace}/artifacts/designs/{epic}/:
- ux_flows.md (user journeys, screen maps, interaction patterns)
- wireframes.md (screen descriptions + Figma file URLs)
- ui_spec.md (real token values, component specs, responsive rules)
- content_spec.md (actual microcopy, CMS structure)
- a11y_report.md (accessibility validation results)

## State Update
Update {workspace}/state/company_state.json:
- Set `sdlc.phases.ux_design.status` to `"complete"`
- Set `sdlc.phases.ux_design.completed_at` to current UTC ISO timestamp (with Z suffix)
