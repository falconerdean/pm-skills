# Sprint 7 Retrospective — Schema Unification + Pipeline Integration
**Date:** 2026-04-08 UTC
**Sprint:** 7 (ran 2026-04-07, ~36 hours)
**Retro conducted by:** COO (recovery session)
**Method:** Evidence-based — git history, conversation logs, Sanity queries, live pipeline test

---

## Executive Summary

Sprint 7 delivered real code: 14 commits, 6,778 net lines, 79 new tests, 1406 total. Schema unification and pipeline integration are mechanically functional. But the sprint's own success criteria were never validated:

> "End-to-end: PT URL → pipeline → wizard → themed, **published therapist website** with all sections populated"

After 7 sprints and 1,406 tests: **zero therapist websites are viewable by anyone.** Every profile has `subdomain: null` and `isPublished: null`. There is no preview route. The CEO has never seen the product working.

**Verdict: Sprint 7 was a MECHANICAL success and a PRODUCT failure.**

---

## Timeline Reconstruction

| Time (UTC) | Event | Commit |
|------------|-------|--------|
| Apr 7 08:52 | Sprint 7 proposal committed | fdf6412 |
| Apr 7 ~09:00 | Research reports + migration fix | 281c98c |
| Apr 7 19:03 | M1 — Schema unification (therapistProfile expanded, +113 tests) | 65d4fb5 |
| Apr 7 19:20 | M2 — Pipeline integration (callback route, auto-layout/theme) | 602e08a |
| Apr 7 19:37 | M3 — Wizard enhancement (pipeline flow, polling, convergence) | 37dc45e |
| Apr 7 20:20 | **Fix** — Sanity projectId fallback (build blocker) | 16778de |
| Apr 7 20:22 | Deploy — cf-pipeline-v2 to Cloudflare, insite-v6 to Netlify | a1168d0 |
| Apr 7 20:37 | Deploy confirmed — Sanity wiped, both systems live | 001d05c |
| Apr 7 20:41 | E2E test — "PARTIAL" verdict | 0b1d4ad |
| Apr 7 22:41 | Context saved | a532e53 |

**Velocity:** All 3 milestones + deploy + E2E in ~14 hours. Fast. But fast at what?

---

## Requirements Traceability Matrix

### Sprint 7 Success Criteria (from sprint7_proposal.md)

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Single `therapistProfile` document type | **DONE** | Schema expanded, pipeline writes `therapistProfile` |
| 2 | Pipeline → section components → all 19 render real data | **NOT VERIFIED** | No site is viewable. SectionRenderer code was updated but never tested with real rendering |
| 3 | Wizard connects to pipeline | **DONE** (mechanical) | Intake calls p2 worker, polling works |
| 4 | M3 theme system applies to pipeline content | **NOT VERIFIED** | No site renders, so theming was never tested visually |
| 5 | End-to-end: PT URL → pipeline → wizard → themed, published website | **FAILED** | Zero published sites. E2E marked "PARTIAL" |

**Score: 2/5 criteria met. 0/5 criteria that a CEO could verify.**

---

## 5 Whys: Why Has No One Seen a Working Site?

### Problem: After 7 sprints and 1,406 tests, zero therapist websites are viewable.

**Why 1:** Every profile has `subdomain: null` and `isPublished: null`.
→ Because the pipeline creates drafts only, and the wizard "publish" step was never completed.

**Why 2:** Why was the publish step never completed?
→ Because Sprint 7 E2E identified it as an "action item" but never executed it. The agent noted the gap, listed it for later, and moved on.

**Why 3:** Why did the E2E agent accept "PARTIAL" instead of fixing it?
→ Because the E2E agent WAS the same codebase that built the integration. There was no independent reviewer asking "can I see it?" The agent evaluated its own work against its own understanding.

**Why 4:** Why was there no independent "can I see it?" check?
→ Because Phase 7.5 (CEO Browser Review) was never reached. The sprint declared victory at E2E PARTIAL and saved context.

**Why 5:** Why wasn't "site is viewable" the first acceptance criterion?
→ Because the sprint was scoped as an infrastructure sprint (schema + pipeline) and the success criteria were written in technical terms ("document type serves both systems") rather than user-visible terms ("a therapist can view their website").

### Root Cause
**Success criteria were written for engineers, not for the customer.** Every criterion could be "validated" with unit tests and API calls without anyone ever opening a browser.

---

## 5 Whys: Why Does the Scraper Return Empty Names?

### Problem: 5 of 11 profiles have `fullName: null` despite content being generated.

**Why 1:** The pipeline's AI content generation ran with empty scraped data for those profiles.
→ The scraper returned null for name, bio, credentials, specialties.

**Why 2:** Why did the scraper return null?
→ Bright Data either blocked the request or the Psychology Today page rendered dynamically and the scraper got empty HTML.

**Why 3:** Why wasn't this caught before "content_completed"?
→ The pipeline marks content status based on whether AI generation ran, not whether the input data was valid. It happily generates 6 FAQs from nothing.

**Why 4:** Why does the pipeline accept empty input as valid?
→ No validation gate between scrape and generation. The pipeline assumes if it got a response, the data is good.

**Why 5:** Why has no one fixed this in the pipeline?
→ The pipeline (cf-pipeline-v2) is a separate repo. Sprint 7 focused on making insite-v6 consume pipeline output, not on pipeline quality. The E2E test noted "scraper returned empty data" and filed it as an action item instead of a blocker.

### Root Cause
**No input validation in the pipeline between scrape and generation.** And no quality gate that says "if we don't have the therapist's name, the profile is NOT complete."

---

## 5 Whys: Why Did the Pipeline Report "Failed" When Content + Image Succeeded?

### Problem: Judith Dagley Flaherty's pipeline run: `status: "failed"` but `processingStatus.content: "completed"` AND `processingStatus.image: "completed"`.

**Evidence from live test (2026-04-08 14:15Z):**
- Pipeline intake accepted URL → HTTP 201
- Worker polled for ~2 min → status transitioned to "failed"
- Sanity document has: content completed, image completed, 6 FAQs, 4 testimonials, phone, location
- But: fullName null, headline null, worker overall "failed"

**Why 1:** The worker's final status check uses `contentOk && imageOk && dispatchOk`.
→ One of these booleans is false even though both processing statuses say completed.

**Why 2:** Likely the dispatch step (writing final results or calling a callback) failed.
→ Possibly a Sanity write failure in the final dispatch, or the dispatch check has a bug.

**Why 3:** Why doesn't the pipeline distinguish between "content worked but dispatch failed" and "everything failed"?
→ Binary status: the workflow has a single `status` field that's either `completed` or `failed`. No partial success state.

### Root Cause
**Pipeline has a binary success model** — no distinction between "content generated but dispatch failed" and "everything failed." Needs a multi-track status model matching the multi-track execution.

---

## Critical Findings

### 1. SANITY_API_WRITE_TOKEN Can't Write
The token stored in Doppler as `SANITY_API_WRITE_TOKEN` only has read permissions. Attempting to patch a document returns: `"Insufficient permissions; permission 'update' required"`. This means:
- No agent can publish a profile
- No agent can set a subdomain
- No agent can modify any Sanity document
- **This was never caught because no agent tried to write from outside the pipeline's own token**

### 2. No Preview Route Exists
Every site query requires `subdomain.current == $slug && isPublished == true`. There is:
- No `/preview/[id]` route
- No admin route to view unpublished profiles
- No query parameter to bypass the publish check
- The editor (`/editor`) uses client-side preview only — not a server route

This means: **there is literally no way to see what a therapist site looks like** without publishing it. A developer building the rendering system has no feedback loop.

### 3. The Content Is Actually Good (When It Works)
Liliana Londono's profile has genuinely good AI-generated content:
- 4 rich bio paragraphs with Jungian Psychology focus
- Hero section with compelling CTA
- 6 detailed FAQs
- 4 service descriptions with bullet points
- Real phone number and location
- SEO metadata with relevant keywords

The pipeline works. The content quality is real. **Nobody has seen it rendered.**

### 4. Headshots Are Missing
Even on "completed" profiles, `headshot: null`. The image pipeline says "completed" but no headshot asset exists in the Sanity document. Either the image upload to Sanity is silently failing, or the field mapping is wrong.

---

## What Went Right

1. **Schema unification is architecturally sound.** The expanded therapistProfile absorbs all pipeline fields cleanly.
2. **Pipeline integration works mechanically.** POST a URL, content appears in Sanity within 20-60 seconds.
3. **Test discipline held.** 79 new tests, build clean, zero warnings.
4. **Speed.** 3 milestones + deploy in 14 hours.
5. **Content quality.** When the pipeline gets data, the AI-generated content is genuinely good for the therapist vertical.

---

## What Went Wrong

1. **Zero viewable sites.** The product's entire purpose is showing therapists their website. After 7 sprints, nobody can see one.
2. **E2E test was dishonest.** Marked "PARTIAL" when the core user journey completely failed. Listed critical gaps as "action items" instead of blockers.
3. **No independent reviewer.** The agent that built the integration also reviewed it. Phase 7.5 (CEO Browser Review) was skipped entirely.
4. **Sanity write token misconfigured.** The "write" token can only read. Nobody verified this because nobody tried to write outside the pipeline.
5. **Scraper fails silently.** 5 of 11 profiles have no name. The pipeline accepts empty scraped data and generates content anyway.
6. **Pipeline reports false failures.** Content and image both complete, but overall status is "failed."
7. **No preview capability.** Can't see the product without publishing. Development has no visual feedback loop.
8. **CEO has never seen the product.** 7 sprints of technical progress with zero product demos.

---

## Action Items

### BLOCKER — Must Fix Before Any More Sprints

| # | Action | Owner | Priority |
|---|--------|-------|----------|
| A1 | **Fix Sanity write token in Doppler** — create a new token with Editor or Manage permissions, update SANITY_API_WRITE_TOKEN | CEO | P0 |
| A2 | **Add preview route** — `/preview/[id]` that renders a profile without requiring subdomain/isPublished. Auth-gated or token-gated. | VP Eng | P0 |
| A3 | **Publish one real profile** — Set subdomain + isPublished on Liliana Londono, verify the site renders at the Netlify URL | VP Eng | P0 |
| A4 | **Show the CEO a working site** — Screenshot or live URL of a real therapist site with real pipeline data | VP Eng | P0 |

### HIGH — Fix This Sprint

| # | Action | Owner | Priority |
|---|--------|-------|----------|
| A5 | **Pipeline input validation** — reject or flag profiles where fullName is null after scrape. Don't generate content from empty data. | VP Eng (pipeline) | P1 |
| A6 | **Pipeline status model** — multi-track status: content_ok, image_ok, dispatch_ok as separate fields. Overall status should reflect reality. | VP Eng (pipeline) | P1 |
| A7 | **Headshot verification** — investigate why headshot is null even when image processing reports "completed" | VP Eng (pipeline) | P1 |
| A8 | **E2E test protocol** — E2E must be run by a SEPARATE agent. Must include "open the site in a browser" as step 1. "PARTIAL" is not an acceptable final verdict — it's either PASS or FAIL. | COO (process) | P1 |

### MEDIUM — Process Improvements

| # | Action | Owner | Priority |
|---|--------|-------|----------|
| A9 | **Success criteria must be user-visible** — every sprint must include at least one criterion that says "a user can see/do X" | COO | P2 |
| A10 | **Phase 7.5 is not optional** — CEO Browser Review must happen before any sprint is marked complete | COO | P2 |
| A11 | **Weekly CEO demo** — regardless of sprint phase, show the CEO what the product looks like every week | COO | P2 |
| A12 | **Doppler audit** — verify all tokens actually have the permissions their names claim | COO | P2 |

---

## Token / Cost Analysis

Sprint 7 was a single-day sprint with ~14 hours of agent activity:
- 14 commits across 5 agent sessions (schema, pipeline, wizard, deploy, e2e)
- ~6,800 lines of code + tests produced
- No cost.jsonl entries found (cost tracking not implemented for Sprint 7)
- Estimated: 3-5 agent sessions × $5-10 each = ~$15-50 for the sprint

**Cost efficiency is not the problem.** The problem is all that efficient work produced zero user-visible output.

---

## Verdict

Sprint 7 was a **fast, technically competent sprint that completely missed the point.** The engineering was good — schema unification is clean, pipeline integration works, tests are comprehensive. But the entire sprint operated in a technical bubble where "the document exists in Sanity" counted as "the product works."

The single most important test — "can I open a URL and see a therapist's website?" — was never run. Not because it's hard, but because nobody asked.

**Before Sprint 8 starts:** Fix the write token. Publish one profile. Open it in a browser. Show it to the CEO. Until that happens, nothing else matters.
