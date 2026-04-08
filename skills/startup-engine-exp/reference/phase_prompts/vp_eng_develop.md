# Phase 6: Development

## CRITICAL: WRITE REAL, WORKING CODE

This is the most important phase. You are a software engineer. Your job is to write actual
source code files that compile, run, and pass tests. You will use real tools — git, npm/pip,
test runners — and produce real commits on a real branch.

DO NOT:
- Write pseudocode or placeholder stubs ("// TODO: implement this")
- Describe what code would do instead of writing it
- Create "example" or "sample" implementations
- Produce documentation about code that doesn't exist
- Skip writing tests because "they would be similar to..."
- Output code blocks in markdown instead of writing to actual files
- Use production/live API keys (Stripe `sk_live_`, real email, production DB)
- Skip a feature because a credential is missing — pause and escalate instead

DO:
- Write actual source code files (.ts, .py, .js, .go, etc.) using the Write tool
- Initialize real projects (npm init, pip install, etc.) if needed
- Run actual tests with real test runners and verify they pass
- Create actual git commits on real branches
- Build actual working features that serve real HTTP responses, render real UI, process real data
- Use SANDBOX/TEST mode for ALL external services (Stripe `sk_test_`, email sandbox, dev DB)
- Make previews render REAL data from REAL backends — never hardcoded placeholders

## Input
- Read: {workspace}/artifacts/requirements/{epic}/stories.json
- Read: {workspace}/artifacts/designs/{epic}/tech/api_spec.json
- Read: {workspace}/artifacts/designs/{epic}/tech/db_schema.sql
- Read: {workspace}/artifacts/designs/{epic}/ui_spec.md
- Read: {workspace}/WORKING_CONTEXT.md (for prior sprint decisions and rules)

## CRITICAL: Credential Verification Before Writing Code

Before writing ANY code that touches an external service:

1. Check `~/startup-workspace/.env` for the required credential
2. Verify it's a SANDBOX/TEST credential (not production)
3. If the credential is MISSING:
   - DO NOT mock it, skip it, or use a placeholder
   - DO NOT continue with the story
   - PAUSE and write to `{workspace}/state/pending_credentials.json`:
     ```json
     {"var": "STRIPE_SECRET_KEY", "needed_for": "ST-8 payment integration", "phase": "development"}
     ```
   - WebSearch the provider's official documentation for how to get the credential
   - Write step-by-step instructions with REAL URLs (not assumed)
   - Email the CEO via GHL MCP explaining what's needed and how to get it
   - Check `.env` every 60 seconds for up to 60 minutes
   - If still missing after 60 minutes: update WORKING_CONTEXT.md, commit to git, STOP

**The instructions for getting credentials must come from REAL documentation.** WebSearch
the provider's setup guide. Do not assume you know the URL. UIs change, setup flows change.
If you give the CEO instructions that don't match the actual screen, they waste hours.

## Process

### Step 0: .gitignore First
If this is a new repository:
1. First commit: `.gitignore` + `README.md` ONLY
2. Verify `.gitignore` covers: `.env`, `env.txt`, `*.local`, `secrets.*`, `node_modules/`
3. Create `.env` file
4. Verify `.env` appears in `git status` as ignored (NOT tracked)
5. THEN proceed to code

### Step 1: Project Setup
- Create or navigate to the project directory under {workspace}/code/
- Initialize the project if first sprint (npm init, create package.json, install dependencies)
- Create feature branch: `git checkout -b feature/{epic}`
- Run the db_schema.sql migration if applicable
- Use /tools:context-restore to load any coding conventions from prior sprints

### Step 2: Implement Stories via TDD
For EACH story in stories.json, use /workflows:tdd-cycle:
- **RED:** Write real failing test files from the story's acceptance criteria
- **GREEN:** Write real source code to make the tests pass
- **REFACTOR:** Improve code quality while keeping tests green

For stories that span frontend + backend:
- Use /workflows:full-stack-feature
- Use /tools:api-mock for parallel frontend/backend development

Reference designs during build:
- mcp__claude_ai_Figma__get_design_context (for UI implementation)
- mcp__claude_ai_Figma__get_code_connect_map (component mapping)

### Step 3: Cross-Boundary Integration Tests
For EVERY external system boundary (webhook, CMS, email, auth, payment):
- Write at least ONE integration test that crosses the boundary with a realistic payload
- Verify the downstream state change (document created, URL accessible, record updated)
- Do NOT mock the external system at the boundary — test the real integration path
- Example: POST a realistic Stripe webhook → verify Sanity document created with correct slug → verify the URL returns 200

### Step 4: Preview Verification
If any story includes a preview, demo, or "see your result" step:
- The preview MUST render actual data from the actual connected backend
- Hardcoded CSS-only previews or static mockups are NOT acceptable
- Verify by: loading the preview URL → confirming it shows the user's real data
- If the preview shows placeholder content, the story is NOT DONE

### Step 5: Code Review Loop
After each story is implemented:
1. Run /tools:multi-agent-review (code quality + security + architecture)
2. If critical/major issues: use /workflows:smart-fix to fix them
3. Re-run review (max 3 total iterations)
4. On pass: commit and create PR via /workflows:git-workflow
5. Use /tools:pr-enhance to generate PR description

### Step 6: Integration
- Merge story PRs into feature branch
- Run full test suite: `npm test` or equivalent — verify ALL tests pass
- Run the full build: `npm run build` — zero warnings, lint clean, type check
- Fix any integration failures using /tools:smart-debug

## Parallel Execution
If multiple stories are independent, spawn developer agents in parallel:
- Use Agent tool with run_in_background: true
- One agent per story (or group of related stories)
- Max 3 parallel developer agents
- Each agent works on different files to avoid conflicts

## Pre-Ship Checklist (Run Before Marking Phase Complete)

```
STORY LEVEL (for each story):
[ ] Tests pass (unit + integration)
[ ] Build passes (zero warnings, lint clean, type check)
[ ] Cross-boundary integration tests exist for every external system
[ ] Preview/demo steps show REAL data, not placeholders
[ ] ALL credentials are sandbox/test mode (no production keys)
[ ] The reviewer is not the builder (Phase 7 will do separate review)

PROJECT LEVEL:
[ ] .gitignore covers all secret files
[ ] No secrets in git history (check with: git log --diff-filter=A -- '*.env' 'env.txt')
[ ] Full build passes: npm run build (zero warnings)
[ ] Full test suite passes: npm test (all green)
[ ] Application starts without errors
```

## Output
- Working code committed to feature/{epic} branch in {workspace}/code/
- PRs created for each story with real code diffs and review results
- Test results from actual test runs
- Cross-boundary integration test results

## State Update
Update {workspace}/state/company_state.json:
- Set `sdlc.phases.development.status` to `"complete"`
- Set `sdlc.phases.development.completed_at` to current UTC ISO timestamp (with Z suffix)
