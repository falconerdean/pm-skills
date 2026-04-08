# Phase 7: Testing & Quality Assurance

## CRITICAL: RUN REAL TESTS, REPORT REAL RESULTS

You are running actual test suites, actual security scanners, and actual browser tests.
Your test_results.json must contain results from tests that actually executed — not
hypothetical test outcomes. If a test fails, that failure is real and must be fixed.

**"DONE" MEANS A USER CAN ACCOMPLISH THE GOAL — NOT JUST THAT TESTS PASS.**

275 passing tests shipped a broken product in the insite-v5 sprint. Tests verified
components in isolation. They did not verify the user could accomplish their goal.
Your job is to verify BOTH: tests pass AND the user journey works end-to-end.

## Input
- Read: {workspace}/artifacts/requirements/{epic}/stories.json (acceptance criteria)
- Feature branch code in {workspace}/code/
- Read: {workspace}/artifacts/designs/{epic}/ui_spec.md (for visual/UX validation)
- Read: {workspace}/WORKING_CONTEXT.md (for rules from prior retro to enforce)

## Process

### Step 1: Generate and Run Test Suites
Use /tools:test-harness to generate comprehensive tests, then RUN them:
- Unit tests for all new functions/methods — execute with the real test runner
- Integration tests for API endpoints — make real HTTP requests
- Acceptance tests mapped to story AC (Given/When/Then) — verify real behavior

### Step 2: Cross-Boundary Integration Tests (MANDATORY)

For EVERY external system the feature integrates with, verify there is at least one
test that crosses the boundary with a realistic payload. If such a test doesn't exist,
WRITE IT before proceeding.

**Common boundaries that MUST be tested:**
- Payment webhooks: POST a real/realistic webhook payload → verify the downstream state
  change (document created, record updated, status changed, URL accessible)
- CMS writes: call the write operation → query back through the read path → verify the
  data is accessible at the expected URL or endpoint
- Email triggers: trigger the event → verify the email record exists in the queue or log
- Auth flows: complete the full sign-up/sign-in/protected-route cycle

**The bugs that ship are almost always at system boundaries.** Tests that mock external
systems at the boundary provide false confidence. If Phase 6 mocked boundaries, add
real integration tests here.

### Step 3: Preview & Demo Verification (MANDATORY)

If ANY story includes a preview, demo, trial, or "see your result" step:

1. Load the preview/demo in a browser (Chrome DevTools MCP)
2. Verify it shows ACTUAL data from the ACTUAL connected backend
3. If it shows hardcoded placeholder content, CSS-only fakes, or static mockups:
   **THE STORY IS NOT DONE. Flag as a critical failure.**
4. Take a screenshot as evidence

The preview is the product. A therapist who sees their actual name and bio in a real
rendered template is far more likely to convert than one who sees a generic placeholder.
A fake preview is a product integrity failure, not a bug.

### Step 4: End-to-End User Journey Verification (MANDATORY)

This is the step that would have caught the insite-v5 failures. You MUST:

**Determine browser tool availability (same priority as Phase 7b):**
1. Chrome DevTools MCP available? → Use it (preferred)
2. Playwright installed (`npx playwright --version`)? → Use it
3. Neither? → Install Playwright: `npm install -D @playwright/test && npx playwright install chromium`

**If using Chrome DevTools MCP:**
1. Start the application in a real browser
2. Complete the PRIMARY user journey end-to-end:
   - Sign up / start the flow as a new user
   - Complete every step of the core flow (wizard, form, checkout — whatever the product is)
   - If the flow includes payment: complete a test payment
   - Verify the final outcome: can the user access/see/use what they were promised?
3. Take screenshots at every step
4. If ANY step fails or produces unexpected results: flag as critical, DO NOT advance
5. Write the journey results to `{workspace}/artifacts/tests/{epic}/e2e_journey.md`

**If using Playwright:**
1. Generate a test script at `{workspace}/artifacts/tests/{epic}/e2e_journey.spec.ts`
   based on the actual user stories and acceptance criteria (NOT a generic template)
2. Run on localhost: `E2E_BASE_URL=http://localhost:3000 npx playwright test e2e_journey.spec.ts`
3. Review output — any failure is a critical issue
4. Screenshots saved to `e2e-screenshots/` directory
5. Write results to `{workspace}/artifacts/tests/{epic}/e2e_journey.md`

**If you cannot complete the user journey end-to-end, Phase 7 has NOT passed.**

### Step 5: Run Multi-Agent Code Review
Use /tools:multi-agent-review on the complete feature branch:
- Code quality review (SOLID, readability, patterns)
- Security review (OWASP, injection, auth — especially authorization on mutation endpoints)
- Architecture review (scalability, coupling)

**Security-specific checks:**
- Every API route that modifies data verifies the authenticated user is authorized
  to modify that SPECIFIC resource — not just that they are authenticated
- No caller-supplied resource IDs are trusted without ownership verification
- Secrets are not in git history (check: `git log --diff-filter=A -- '*.env' 'env.txt'`)

### Step 6: Security Scan
Use /tools:security-scan for real vulnerability assessment:
- OWASP Top 10 checks against actual code
- Dependency vulnerability scan (/tools:deps-audit)
- If compliance required: /tools:compliance-check

### Step 7: Accessibility Audit
Use /tools:accessibility-audit on all user-facing changes:
- WCAG 2.1 AA compliance
- Keyboard navigation
- Screen reader compatibility

### Step 8: Browser Testing (Lighthouse + Visual)

**If Chrome DevTools MCP is available:**
- mcp__chrome-devtools__navigate_page: Walk through key user flows
- mcp__chrome-devtools__take_screenshot: Capture each screen state (verify >10KB — blank screenshots produce no errors but are useless)
- mcp__chrome-devtools__lighthouse_audit: Get real performance, accessibility, SEO scores
- mcp__chrome-devtools__list_console_messages: Check for JS errors

**If Chrome DevTools MCP is NOT available, use Playwright:**
```bash
# Lighthouse via Playwright (install if needed)
npm install -D lighthouse
# Run Lighthouse programmatically or via CLI
npx lighthouse http://localhost:3000 --output=json --output-path=lighthouse_report.json --chrome-flags="--headless --no-sandbox"

# Visual screenshots via Playwright
npx playwright test e2e_journey.spec.ts --update-snapshots
```

**If neither Chrome DevTools nor Playwright is available:**
```bash
# Minimal HTTP verification as last resort
echo "=== Route verification ===" 
for route in "/" "/about" "/services" "/contact"; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000$route")
  echo "$route -> $STATUS"
done
echo "=== Console errors (check build output) ==="
npm run build 2>&1 | grep -i "error\|warning" | head -20
```

### Step 9: Fix Failures (Inner Loop)
If tests or reviews fail:
1. Classify failures: critical / major / minor
2. For critical: Use /workflows:smart-fix to auto-fix
3. For major: Spawn developer agent with specific failure context and the actual error output
4. Re-run affected tests and verify the fix
5. Max 3 fix-test cycles, then escalate to COO with the actual error details

## Pre-Advance Checklist

```
[ ] All unit tests pass
[ ] All integration tests pass
[ ] Cross-boundary tests exist for EVERY external system
[ ] Preview/demo shows REAL data (not hardcoded)
[ ] Primary user journey completed end-to-end in browser
[ ] User can accomplish the stated goal (not just "no errors")
[ ] Security review passed (authorization on mutations, no secrets in git)
[ ] Lighthouse scores > 80
[ ] No critical console errors
[ ] Screenshots captured and > 10KB each
```

**If ANY of these fail, DO NOT advance. Fix first.**

## Output
Write to {workspace}/artifacts/tests/{epic}/:
- test_results.json (real pass/fail per story, real coverage %)
- security_report.json (real vulnerabilities found/fixed)
- a11y_report.json (real WCAG compliance results)
- lighthouse_report.json (real performance scores)
- e2e_journey.md (screenshots and results of end-to-end user journey)
- review_summary.md (consolidated review findings)

## State Update
Update {workspace}/state/company_state.json:
- Set `sdlc.phases.testing.status` to `"complete"`
- Set `sdlc.phases.testing.completed_at` to current UTC ISO timestamp (with Z suffix)
