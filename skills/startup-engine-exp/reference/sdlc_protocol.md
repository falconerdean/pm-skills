# SDLC Protocol — Phase Transitions and Handoffs

## GROUND RULES

Every phase produces real, functional artifacts. Agents write real code, query real APIs,
create real designs, run real tests. Phase completion requires real artifacts on disk —
not documents describing what artifacts could exist.

### Rule: "Done" Means a User Can Accomplish the Goal
Tests passing and builds passing are NECESSARY but NOT SUFFICIENT. A story is done when
a real user, using the actual deployed product, can accomplish the goal the story was
written to enable. If 275 tests pass but the core user journey is broken, IT IS NOT DONE.

### Rule: The Preview Is the Product
Any preview, demo, trial, or "see your result" step MUST show actual output from the
actual system with actual user data. Hardcoded placeholders, static mockups, or CSS-only
fakes are NEVER acceptable as "preview." If the preview shows fake data, the story is not
done regardless of test status.

### Rule: Sandbox First, Production Never During Development
Phase 6 (Development) MUST use sandbox/test credentials for ALL external services:
- Stripe: `sk_test_` ONLY. Never `sk_live_` during development.
- Email: sandbox provider (Mailtrap, Resend test mode). Never real emails during dev.
- Databases: separate dev project/schema. Never the production instance.
- Webhooks: test endpoints only.
Production credentials are set ONLY in Phase 8 (Deployment), ONLY after CEO approval.

### Rule: .gitignore Before Everything
The FIRST commit of any repository must contain ONLY `.gitignore` and optionally README.
No code. No environment files. No configuration. The `.gitignore` must cover `.env`,
`env.txt`, `*.local`, `secrets.*`, and any project-specific secret files BEFORE any
other file is created.

### Rule: Never Skip a Phase Because of Missing Credentials
If a credential is missing, DO NOT skip the phase or substitute a mock. Instead:
1. Pause the phase
2. Email the CEO via GHL explaining what credential is needed, what it's for, and
   step-by-step instructions for how to get it (looked up from real documentation)
3. Poll `~/startup-workspace/.env` every 60 seconds for the missing variable
4. If not provided within 60 minutes: write WORKING_CONTEXT.md, commit to git, STOP
5. The credential instructions must come from REAL documentation — WebSearch the
   provider's docs. Never assume you know the URL or steps.

### Rule: Separate Builder from Reviewer
The agent that builds a feature MUST NOT be the only agent that reviews it. A separate
agent session with a different mandate (security, UX, integration) must review. This
is why Phase 7 (Testing) exists as a separate phase from Phase 6 (Development).

### Rule: Test Across System Boundaries
For every external system a feature integrates with, there must be at least one test
that crosses the boundary with a realistic payload. Mocking at the boundary provides
false confidence. The bugs that ship are almost always at system boundaries.

## Phase State Machine

```
INITIALIZE → PLANNING → RESEARCH → REQUIREMENTS → UX_DESIGN → TECH_DESIGN
    → CREDENTIAL_VERIFY → DEVELOPMENT → TESTING → E2E_TESTING
    → CEO_BROWSER_REVIEW → DEPLOYMENT → GROWTH → EVOLUTION → PLANNING (loop)
```

## Phase Definitions

### Phase 0: CONTINUOUS_INTEL
- **Owner:** VP BizDev
- **Trigger:** Independent /loop 1d cycle (not part of main SDLC loop)
- **Input:** Competitor list from backlog.json, market keywords
- **Skills:**
  - /deep-research (weekly market pulse)
  - /tools:competitive-intel (daily competitor scrape)
- **MCPs:**
  - mcp__Bright_Data__web_data_crunchbase_company
  - mcp__Bright_Data__web_data_linkedin_job_listings
  - mcp__Bright_Data__web_data_reddit_posts
  - mcp__Bright_Data__web_data_x_posts
  - mcp__Bright_Data__web_data_google_play_store
  - mcp__Bright_Data__web_data_apple_app_store
- **Output:** {workspace}/intel/competitive_report_{date}.md, market_pulse_{date}.md
- **Quality Gate:** Reports contain real scraped data with source URLs
- **Advance Condition:** N/A (runs independently)

### Phase 1: PLANNING
- **Owner:** COO
- **Trigger:** Start of sprint or return from EVOLUTION
- **Input:** backlog.json, latest intel/*.md, previous retrospective
- **Skills:**
  - /tools:context-restore
  - /tools:standup-notes
  - /tools:tech-debt
- **Output:** {workspace}/state/sprint_plan.json
- **Quality Gate:** Sprint plan has >=1 epic, effort estimates, assignments
- **Advance Condition:** sprint_plan.json exists and is valid JSON
- **CEO Gate:** No (unless CEO requested checkpoint)

### Phase 2: RESEARCH
- **Owner:** VP Product
- **Trigger:** COO detects sprint_plan.json complete
- **Input:** sprint_plan.json (current epic)
- **Skills:**
  - /deep-research "{epic} user needs pain points competitors"
  - /tools:competitive-intel (targeted competitor deep-dive)
- **MCPs:**
  - mcp__Bright_Data__web_data_reddit_posts
  - mcp__Bright_Data__web_data_youtube_comments
  - mcp__Bright_Data__scrape_as_markdown
  - mcp__Bright_Data__extract
  - mcp__chrome-devtools__navigate_page + take_screenshot
- **Output:**
  - {workspace}/artifacts/research/{epic}/user_research.json
  - {workspace}/artifacts/research/{epic}/competitive_analysis.json
  - {workspace}/artifacts/research/{epic}/discovery_brief.md
- **Quality Gate:** >=10 real sources with URLs, 2+ personas grounded in data, evidence-backed problem statement
- **Advance Condition:** discovery_brief.md exists and passes gate
- **CEO Gate:** No

### Phase 3: REQUIREMENTS
- **Owner:** VP Product
- **Trigger:** COO detects discovery_brief.md complete
- **Input:** discovery_brief.md
- **Skills:**
  - /product-pipeline (Phases 4-6: features, epics, stories)
  - /tools:doc-generate (API documentation)
  - /tools:accessibility-audit (bake a11y into requirements)
  - /tools:compliance-check (bake compliance in)
- **Output:**
  - {workspace}/artifacts/requirements/{epic}/features.json
  - {workspace}/artifacts/requirements/{epic}/epics.json
  - {workspace}/artifacts/requirements/{epic}/stories.json
  - {workspace}/artifacts/requirements/{epic}/prd.md
- **Quality Gate:** All stories have testable AC (Given/When/Then), no TBD placeholders, developer can code from any story immediately
- **Advance Condition:** stories.json exists, self-review passes
- **CEO Gate:** No

### Phase 4: UX_DESIGN
- **Owner:** VP Product
- **Trigger:** COO detects stories.json complete
- **Input:** stories.json, discovery_brief.md, personas
- **Skills:**
  - /tools:ux-flows (user flow diagrams, wireframe specs)
  - /tools:accessibility-audit (WCAG on design intent)
- **MCPs:**
  - mcp__claude_ai_Figma__generate_diagram (FigJam flows)
  - mcp__claude_ai_Figma__create_new_file (wireframes)
  - mcp__claude_ai_Figma__search_design_system (reusable components)
  - mcp__claude_ai_Figma__get_variable_defs (design tokens)
  - mcp__chrome-devtools__navigate_page (competitor UX audit)
  - mcp__chrome-devtools__take_screenshot (reference captures)
  - mcp__Sanity__get_schema (CMS content model)
  - mcp__Sanity__create_documents_from_markdown (content entries)
- **Output:**
  - {workspace}/artifacts/designs/{epic}/ux_flows.md
  - {workspace}/artifacts/designs/{epic}/wireframes.md
  - {workspace}/artifacts/designs/{epic}/ui_spec.md (real token values, component specs)
  - {workspace}/artifacts/designs/{epic}/content_spec.md
- **Quality Gate:** /tools:multi-agent-review + /tools:accessibility-audit, components defined well enough to code against
- **Advance Condition:** All design artifacts exist and pass review
- **CEO Gate:** OPTIONAL — design review before committing to build

### Phase 5: TECH_DESIGN
- **Owner:** VP Engineering
- **Trigger:** COO detects design artifacts complete
- **Input:** stories.json, ui_spec.md, ux_flows.md
- **Skills:**
  - /tools:api-scaffold (API endpoints)
  - /tools:data-pipeline (data architecture)
  - /tools:data-validation (validation schemas)
  - /tools:db-migrate (database schema)
  - /tools:config-validate (environment configs)
  - /product-pipeline Phase 8 pattern (full tech architecture)
- **Output:**
  - {workspace}/artifacts/designs/{epic}/tech/architecture.md
  - {workspace}/artifacts/designs/{epic}/tech/api_spec.json (complete endpoint definitions)
  - {workspace}/artifacts/designs/{epic}/tech/db_schema.sql (executable SQL)
- **Quality Gate:** /workflows:full-review, db_schema.sql is valid SQL, api_spec.json has real request/response types
- **Advance Condition:** architecture.md + api_spec.json exist and pass review
- **CEO Gate:** No

### Phase 5.5: CREDENTIAL VERIFICATION
- **Owner:** COO
- **Trigger:** COO detects tech design complete, BEFORE development starts
- **Purpose:** Ensure all credentials needed for Phase 6-8 are available. Do NOT start
  development with missing credentials — it leads to mocked integrations that ship broken.
- **Process:**
  1. Read `architecture.md` and `api_spec.json` to determine which external services are needed
  2. Map each service to required env vars (Stripe → `STRIPE_SECRET_KEY`, Sanity → `SANITY_TOKEN`, etc.)
  3. Check `~/startup-workspace/.env` for each required var
  4. For any MISSING credential:
     a. **WebSearch the provider's official documentation** to find exactly how to get the credential
     b. Write step-by-step instructions with real URLs (NOT assumed URLs)
     c. Email CEO via GHL with the instructions for each missing credential
     d. Write the missing vars to `{workspace}/state/pending_credentials.json`
     e. Poll `.env` every 60 seconds checking for the missing vars
     f. If all vars provided: advance to Phase 6
     g. If 60 minutes pass without all vars: write WORKING_CONTEXT.md, commit to git, PAUSE
  5. Verify sandbox/test variants exist: if Stripe is needed, confirm `sk_test_` not `sk_live_`
- **Quality Gate:** All required credentials set in .env, all using sandbox/test mode
- **Advance Condition:** pending_credentials.json is empty (all resolved)
- **CEO Gate:** No (but CEO is emailed for each missing credential)

### Phase 6: DEVELOPMENT
- **Owner:** VP Engineering
- **Trigger:** COO detects tech design complete AND all credentials verified
- **Input:** api_spec.json, db_schema.sql, stories.json, ui_spec.md
- **Skills:**
  - /workflows:tdd-cycle (DEFAULT for all stories — write real tests, then real code)
  - /workflows:feature-development (non-TDD fallback)
  - /workflows:full-stack-feature (multi-platform stories)
  - /tools:api-mock (parallel frontend/backend development)
  - /workflows:git-workflow (branch, commit, PR)
- **MCPs:**
  - mcp__claude_ai_Figma__get_design_context (reference designs during build)
  - mcp__claude_ai_Figma__get_code_connect_map (component-to-code mapping)
- **Eval-Optimizer Loop:**
  1. Developer writes real code → /tools:multi-agent-review (evaluator)
  2. If critical issues → /workflows:smart-fix (optimizer) fixes real code
  3. Re-review → max 3 iterations → advance
- **Output:** Real code committed to feature branch, real PRs with real diffs
- **Credential Rule:** ALL external service credentials MUST be sandbox/test mode. Verify:
  - Stripe keys start with `sk_test_` (NEVER `sk_live_`)
  - Email provider is in sandbox/test mode
  - Database is dev instance, not production
  - If ANY production credential is detected, STOP and flag as a blocker
- **Quality Gate:** All tests actually pass when run, code review passes, no critical security issues, ALL credentials are sandbox/test mode
- **Advance Condition:** All story PRs created, reviewed, and contain real code
- **CEO Gate:** No

### Phase 7: TESTING
- **Owner:** VP Engineering
- **Trigger:** COO detects all story PRs reviewed
- **Input:** Feature branch code, stories.json (acceptance criteria)
- **Skills:**
  - /tools:test-harness (generate and RUN comprehensive tests)
  - /tools:security-scan (real OWASP scan)
  - /tools:deps-audit (real dependency vulnerabilities)
  - /tools:compliance-check (regulatory compliance)
  - /tools:accessibility-audit (WCAG on built product)
  - /tools:error-analysis (analyze real failures)
  - /tools:smart-debug (debug real failures)
  - /workflows:smart-fix (auto-fix routing)
- **MCPs:**
  - mcp__chrome-devtools__lighthouse_audit (real performance, a11y, SEO scores)
  - mcp__chrome-devtools__navigate_page (real E2E smoke testing)
  - mcp__chrome-devtools__take_screenshot (real visual regression)
- **Output:**
  - {workspace}/artifacts/tests/{epic}/test_results.json (from real test runs)
  - {workspace}/artifacts/tests/{epic}/security_report.json (from real scans)
  - {workspace}/artifacts/tests/{epic}/lighthouse_report.json (from real audits)
- **Cross-Boundary Test Mandate:** For EVERY external system boundary (payment webhook,
  CMS write, email trigger, auth flow), there MUST be at least one integration test that:
  - Sends a realistic payload across the boundary
  - Verifies the downstream state change (document created, record updated, URL accessible)
  - Does NOT mock the external system — exercises the real integration path
  - Quality gate FAILS if any system boundary lacks a cross-boundary test
- **Preview Verification:** If any story includes a preview, demo, or "see your result"
  step, the testing agent MUST verify: "Does the preview render actual data from the
  connected backend, or is it hardcoded/faked?" Faked previews = story NOT done.
- **Quality Gate:** >80% real test pass rate, zero critical security findings, lighthouse >80,
  ALL system boundaries have cross-boundary tests, ALL previews show real data
- **Advance Condition:** All reports exist with real data meeting thresholds
- **Inner Loop:** Failed tests → developer fixes real code → re-run real tests (max 3 cycles)
- **CEO Gate:** No

### Phase 7b: E2E TESTING (Separate Agent)
- **Owner:** E2E Testing Agent (MUST be a different agent from the developer)
- **Trigger:** COO detects Phase 7 (Testing) complete
- **Purpose:** A separate agent — with NO knowledge of the code — tries to use the product
  as a real user would. This is the checkpoint that catches "tests pass but product is broken."
- **Process:**
  1. Read the PRD and stories to understand what the user should be able to do
  2. Open the application in a real browser (Chrome DevTools MCP)
  3. Complete the primary user journey end-to-end with real data
  4. Verify all system boundary outcomes (payment → record, content → URL, etc.)
  5. Test sad paths (empty forms, invalid data, mobile, direct URLs)
  6. Verify previews/demos show real backend data, not hardcoded fakes
  7. Write detailed e2e_report.md with screenshots at every step
- **Prompt:** Load [vp_eng_e2e.md](./phase_prompts/vp_eng_e2e.md)
- **Output:** {workspace}/artifacts/tests/{epic}/e2e_report.md + e2e_plan.md
- **Quality Gate:** E2E agent reports PASS verdict — user can accomplish their goal
- **On FAIL:** Return to Phase 6 with the e2e_report.md as input. Developer fixes. Re-run E2E. Max 3 cycles.
- **Advance Condition:** e2e_report.md exists with PASS verdict
- **CEO Gate:** No (Phase 7.5 follows immediately)

### Phase 7.5: CEO BROWSER REVIEW
- **Owner:** CEO (human)
- **Trigger:** COO detects Phase 7 (Testing) complete
- **Purpose:** A human looks at the product in a browser before it reaches real users.
  This is the checkpoint that would have caught the insite-v5 fake preview and slug bug.
- **Process:**
  1. COO generates a preview/staging URL or starts the dev server
  2. COO emails CEO via GHL with:
     - The preview URL
     - The primary user journey to complete (step-by-step)
     - What to verify ("complete signup → see preview → make payment → verify site is live")
     - Screenshots of the current state
  3. Engine PAUSES and waits for CEO response via `/btw approve`
  4. Poll for approval every 60 seconds
  5. If no response within 24 hours: write WORKING_CONTEXT.md, commit, send reminder email
- **Quality Gate:** CEO has explicitly approved via `/btw approve`
- **Advance Condition:** `company_state.json` has `ceo_browser_review: "approved"`
- **CEO Gate:** REQUIRED — this gate cannot be bypassed or auto-approved

### Phase 8: DEPLOYMENT
- **Owner:** VP Engineering
- **Trigger:** COO detects all tests passing
- **Input:** Passing test results, feature branch
- **Skills:**
  - /tools:deploy-checklist (pre-deployment verification)
  - /tools:docker-optimize (container optimization)
  - /tools:k8s-manifest (Kubernetes configs if applicable)
  - /tools:monitor-setup (logging, metrics, alerting)
  - /tools:slo-implement (SLOs and error budgets)
  - /tools:config-validate (env config validation)
  - /workflows:git-workflow (merge PR, tag release)
  - /tools:pr-enhance (release notes)
- **MCPs:**
  - mcp__chrome-devtools__navigate_page + take_screenshot (real prod smoke test)
  - mcp__chrome-devtools__lighthouse_audit (real prod performance)
- **Output:**
  - {workspace}/artifacts/deployments/{epic}/deploy_log.md
  - {workspace}/artifacts/deployments/{epic}/release_notes.md
- **Quality Gate:** Real smoke test passes on real deployed application
- **CEO Gate:** REQUIRED — CEO must approve production deployment
- **Advance Condition:** CEO approval + successful real deployment

### Phase 9: GROWTH
- **Owner:** VP BizDev
- **Trigger:** COO detects successful deployment
- **Input:** Deployed feature description, release notes
- **Skills:**
  - /tools:competitive-intel (position against competitors)
- **MCPs:**
  - mcp__GoHighLevel__blogs_create-blog-post (publish real blog post)
  - mcp__GoHighLevel__social-media-posting_create-post (publish real social posts)
  - mcp__GoHighLevel__emails_create-template (create real email campaign)
  - mcp__Sanity__create_documents_from_markdown (create real CMS content)
  - mcp__Sanity__publish_documents (publish real content)
  - mcp__GoHighLevel__contacts_get-contacts (track real leads)
  - mcp__GoHighLevel__social-media-posting_get-social-media-statistics (real engagement)
- **Output:** {workspace}/intel/growth/launch_{epic}.md with real published URLs
- **Quality Gate:** Content actually published and accessible, no broken links
- **Advance Condition:** Launch content published to real channels
- **CEO Gate:** No

### Phase 10: EVOLUTION
- **Owner:** COO + All Leads
- **Trigger:** COO detects growth phase complete (or 1 week post-deploy)
- **Input:** All phase artifacts, real production metrics, real intel reports
- **Sub-phases:** Run in this order:
  1. **Sprint Retro** (FIRST — before any other evolution work)
  2. **Technical Health** (informed by retro findings)
  3. **Agent Improvement** (informed by retro findings)
  4. **Context Save & Backlog Update** (wrap up)

#### Sub-phase 10a: Sprint Retro
- **Skill:** /sprint-retro
- **Input:** Conversation logs from agent sessions, git commit history, sprint plan, requirements
- **Process:**
  1. Reconstruct timeline of what happened across all agent sessions this sprint
  2. Build requirements traceability matrix (what was planned vs. what was built)
  3. Run 5 Whys root cause analysis on major issues
  4. Calculate token & cost efficiency (productive vs. wasted tokens)
  5. Identify systemic process patterns
  6. Generate concrete action items with owners and due dates
- **Output:** {workspace}/reviews/retrospectives/sprint-retro-{sprint_N}.md
- **Quality Gate:** Retro document has timeline, traceability matrix, root causes, token analysis, and action items. Action items are specific and assignable, not vague.
- **Email Summary:** After retro is complete, send via SMTP to dean@try-insite.com:
  ```bash
  python3 scripts/send_email.py --type retro --product "{name}" --sprint {N} --details "{HTML summary}"
  ```
- **Why this matters:** The retro MUST run before technical health checks because its findings inform what to fix. Without the retro, evolution is just guessing at improvements.

#### Sub-phase 10b: Technical Health
- **Skills:**
  - /tools:error-trace (real production errors)
  - /tools:tech-debt (real debt in real codebase)
  - /tools:cost-optimize (real cloud spend)
  - /tools:deps-upgrade (real dependency upgrades)
  - /workflows:performance-optimization (if real perf issues)
  - /tools:refactor-clean (refactor real code)
  - /workflows:incident-response (if real production issues)
- **Input:** Retro action items tagged as "Technical", production metrics
- **Output:** Updated code, resolved tech debt items, dependency upgrades applied

#### Sub-phase 10c: Agent Improvement
- **Skills:**
  - /workflows:improve-agent (tune agent prompts based on retro findings)
- **Input:** Retro action items tagged as "Process" or "Context", token efficiency data
- **Output:** Updated VP prompts, improved CLAUDE.md/conventions docs, better requirement templates

#### Sub-phase 10d: Context Save & Backlog Update
- **Skills:**
  - /tools:context-save (save real state for next sprint)
- **Output:**
  - {workspace}/reviews/retrospectives/sprint_{N}.md (summary from retro + health + improvements)
  - Updated backlog.json with real items (including retro action items as tickets)
  - Updated agent prompts (if improved)
- **Quality Gate:** Retrospective backed by real metrics, backlog updated with retro action items
- **Advance Condition:** backlog.json has next epic → LOOP TO PHASE 1
- **CEO Gate:** Sprint retrospective review (part of 3-day check-in)

## Handoff Protocol

Every phase transition:
1. Producing agent writes real artifact to designated path
2. Producing agent updates company_state.json: `sdlc.phases.{phase_name}.status = "complete"`
3. COO reads state on next 30-min cycle
4. COO validates artifact exists on disk AND passes quality gate
5. COO updates company_state.json: `sdlc.current_phase = {next_phase}`
6. COO spawns next agent with artifact paths and build-real-things directive
7. COO logs transition to agent_activity.jsonl

## State Update Convention

All phase prompts must use these exact JSON paths when updating company_state.json:
```
sdlc.phases.planning.status = "complete"
sdlc.phases.research.status = "complete"
sdlc.phases.requirements.status = "complete"
sdlc.phases.ux_design.status = "complete"
sdlc.phases.tech_design.status = "complete"
sdlc.phases.development.status = "complete"
sdlc.phases.testing.status = "complete"
sdlc.phases.deployment.status = "complete"
sdlc.phases.growth.status = "complete"
sdlc.phases.evolution.status = "complete"
```
Do NOT use `phase{N}_status` — that path does not exist in the state schema.

## Cost Controls

```json
{
  "per_agent_invocation": "$5",
  "per_phase": "$25",
  "per_sprint": "$150",
  "per_3_day_cycle": "$300",
  "hard_monthly_cap": "$750",
  "alert_at": "80%",
  "action_on_breach": "pause_and_escalate_to_ceo"
}
```
