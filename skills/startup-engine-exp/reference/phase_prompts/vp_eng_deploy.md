# Phase 8: Deployment

## CRITICAL: DEPLOY TO REAL INFRASTRUCTURE

You are preparing and executing a real deployment. The deploy checklist must pass against
real infrastructure. The smoke tests must run against a real server. The monitoring must
be configured in a real monitoring service.

## Input
- Read: {workspace}/artifacts/tests/{epic}/test_results.json (must be passing)
- Read: {workspace}/artifacts/designs/{epic}/tech/infra_spec.md
- Feature branch with all story PRs merged in {workspace}/code/

## Process

### Step 1: Pre-Deployment Checklist
Use /tools:deploy-checklist to verify:
- All tests actually passing (re-run to confirm)
- Security scan clean
- Dependencies audited
- Environment configs validated (/tools:config-validate)
- Monitoring configured (/tools:monitor-setup)
- SLOs defined (/tools:slo-implement)

### Step 2: Container & Infrastructure
- Use /tools:docker-optimize to build optimized containers
- Use /tools:k8s-manifest if Kubernetes deployment
- Validate real infrastructure matches infra_spec.md

### Step 3: Release Preparation
- Use /workflows:git-workflow to merge feature branch to main, tag release
- Use /tools:pr-enhance to generate release notes
- Write deployment summary for CEO review

### Step 4: Switch to Production Credentials
This is the ONLY phase where production credentials are set. Before deploying:
1. Read `~/startup-workspace/.env` and identify all sandbox/test credentials
2. For each one that needs a production equivalent, check if the production version exists
3. If ANY production credential is missing:
   - WebSearch the provider's official documentation for how to get it
   - Write step-by-step instructions with REAL URLs
   - Email CEO via GHL with the instructions
   - Poll `.env` every 60 seconds for up to 60 minutes
   - If still missing: update WORKING_CONTEXT.md, commit, STOP
4. Verify each production credential is valid (e.g., Stripe `sk_live_` starts correctly)
5. Update `.env` with production values

### Step 5: CEO Approval Gate
Write deployment summary to {workspace}/reviews/ceo_reviews/deploy_{epic}.md:
- What's being deployed (features, stories completed)
- Real test results summary
- Real security scan results
- Rollback plan with specific steps
- Estimated user impact
- Preview/staging URL for CEO to review
- **Confirmation that CEO completed browser review in Phase 7.5**

**PAUSE HERE. Set `sdlc.phases.deployment.awaiting_ceo_approval` to `true` in company_state.json.**
Email CEO via GHL with the deployment summary and staging URL.
Do NOT deploy until CEO approves via `/btw approve`.

### Step 5b: Verify CI/CD Pipeline (Sprint 7 Retro, 2026-04-08)

Before deploying, verify the automated deploy pipeline actually works. Do NOT rely on manual deploys.

1. **Check the platform has a repo linked:**
   - Netlify: `netlify api getSite --data '{"site_id":"$SITE_ID"}' | jq '.build_settings.repo_url'` — must not be null/empty
   - If null: the GitHub App is not installed or the repo is not linked. **Fix this before deploying.**
2. **Verify a push triggers a build:**
   - Push a trivial change (whitespace in README, comment in config)
   - Check if the platform starts a build: `netlify api listSiteDeploys --data '{"site_id":"$SITE_ID"}' | jq '.[0].created_at'`
   - If no build starts: the webhook is broken. Fix it.
3. **If the automated path is broken, FIX IT** — do not work around it with `netlify deploy --prod` or manual uploads. Manual deploys hide broken CI/CD and guarantee that future pushes silently fail to deploy.

**Why this exists:** Sprint 7 ran 7 sprints with manual `netlify deploy --prod`. When auto-deploy was needed, the Netlify site had no GitHub App installation, no webhook, and no repo link. Pushes to `main` did nothing.

### Step 6: Deploy (after CEO approval)
- Deploy to staging, run real smoke tests
- If smoke tests pass: deploy to production

### Step 6b: Post-Deploy E2E Verification (MANDATORY)

After deployment, re-run E2E tests against the deployed URL. This catches environment-only bugs
(missing env vars, CORS, CDN issues, serverless cold starts) that localhost testing cannot find.

**Browser tool priority:**
1. Chrome DevTools MCP (if available): navigate, screenshot, verify
2. Playwright (if installed or installable): re-run e2e.spec.ts with `E2E_BASE_URL=$DEPLOYED_URL`
3. curl-based HTTP verification (last resort): verify routes return 200, forms accept POST

**Steps:**
1. Detect the deployed URL (Netlify, Vercel, or custom domain)
2. Run the SAME E2E tests from Phase 7b against the deployed URL
3. Complete the primary user journey on the deployed URL with production credentials
4. Verify system boundaries work with production services (Stripe live mode, real CMS, real email)
5. Compare results: if any test passes on localhost but fails on deployed URL, flag as deployment environment issue
6. Write results to `{workspace}/artifacts/tests/{epic}/e2e_deploy_report.md`

**If using Playwright:**
```bash
# Re-run the exact same tests against the deployed URL
DEPLOYED_URL=$(cat .netlify/state.json 2>/dev/null | grep -o '"url":"[^"]*"' | cut -d'"' -f4)
E2E_BASE_URL=$DEPLOYED_URL npx playwright test e2e.spec.ts --reporter=list
```

**If using Chrome DevTools MCP:**
- `mcp__chrome-devtools__navigate_page` to the deployed URL
- `mcp__chrome-devtools__take_screenshot` at each step
- `mcp__chrome-devtools__lighthouse_audit` for production baseline scores
- `mcp__chrome-devtools__list_console_messages` for JS errors

**If a test fails on deployed URL that passed on localhost: DO NOT declare deployment complete.**
Fix the environment issue first. Common causes: missing env var in Netlify/Vercel dashboard,
SPA redirect rule not configured, API endpoint not whitelisted for production domain.

### Step 7: Post-Deploy Monitoring
- Confirm monitoring dashboards are active and receiving data
- Watch for errors in first 30 minutes
- Document deployment in {workspace}/artifacts/deployments/{epic}/deploy_log.md

## Output
Write to {workspace}/artifacts/deployments/{epic}/:
- deploy_checklist.md (completed checklist with real pass/fail)
- release_notes.md
- deploy_log.md (real UTC timestamps, real status, any issues encountered)

## State Update
Update {workspace}/state/company_state.json:
- Set `sdlc.phases.deployment.status` to `"complete"`
- Set `sdlc.phases.deployment.completed_at` to current UTC ISO timestamp (with Z suffix)
