# Architecture Comparison Report — Example: ESCALATE on Divergent Architectures

**Epic:** therapist-website-import
**Timestamp:** 2026-04-11T14:32:08.123456+00:00
**Primary architect:** Claude Opus (path: `/Users/deanfalconer/startup-workspace/artifacts/designs/therapist-website-import/tech/architecture.md`)
**Rival architect:** Gemini 3 Pro (path: `/Users/deanfalconer/startup-workspace/artifacts/designs/therapist-website-import/tech/rival/architecture.md`)

## Verdict: **ESCALATE**

Both architectures pass structural validation but disagree on substantive decisions. Phase 5 PAUSES. CEO must review both architectures and decide via /btw approve before Phase 5 can advance.

## Stage 1: Structural Validation

- Primary: ✅ PASS
- Rival: ✅ PASS

## Stage 2: Required Section Coverage

### Primary architecture sections
- Present: overview, data model, api surface, authentication, authorization, deployment, observability, concurrency, error handling, dependencies, compatibility

### Rival architecture sections
- Present: overview, data model, api surface, authentication, authorization, deployment, observability, concurrency, error handling, dependencies, compatibility

## Stage 3: Database Schema Diff

- Tables in primary: 4
- Tables in rival: 6
- Tables in both: 3
- Overlap: 42.9%
- Only in primary: ['imports']
- Only in rival: ['import_jobs', 'import_results', 'scrape_attempts']

### Column-level differences (shared tables)
- **users**:
  - Only in primary: ['credentials_json']
  - Only in rival: ['credentials_jsonb']
- **profiles**:
  - Only in primary: []
  - Only in rival: ['imported_from_url', 'imported_at']

## Stage 4: API Surface Diff

- Endpoints in primary: 4
- Endpoints in rival: 7
- Endpoints in both: 2
- Overlap: 22.2%
- **Only in primary:**
  - `POST /api/imports`
  - `GET /api/imports/:id`
- **Only in rival:**
  - `POST /api/import-jobs`
  - `GET /api/import-jobs/:id`
  - `GET /api/import-jobs/:id/results`
  - `POST /api/import-jobs/:id/retry`
  - `DELETE /api/import-jobs/:id`

## Stage 5: Dependencies Diff

- Dependencies in both: ['next', '@sanity/client', 'redis']
- Only in primary: ['scrapingbee', 'cheerio']
- Only in rival: ['bullmq', 'apify-client', 'puppeteer-core', '@aws-sdk/client-sqs']

## Stage 6: Specialization Keyword Counts (Concurrency / Compatibility)

- Concurrency keywords — primary: 4, rival: 19
- Compatibility keywords — primary: 6, rival: 14
- ⚠️  Asymmetric concurrency treatment — rival's section is substantially more thorough.

## Stage 7: Substantive Disagreements (LLM judgment surface)

**Agreement signal strength:** low

**Rationale:** The two architectures take fundamentally different approaches to the import problem. Primary treats imports as synchronous one-shot operations against ScrapingBee. Rival treats imports as long-running jobs queued through BullMQ with explicit retry semantics, dead-letter handling, and a more granular API surface separating job creation from job results. The data models reflect this — primary has a single `imports` table while rival decomposes into `import_jobs`, `import_results`, and `scrape_attempts`. The disagreement is not about which tools to use but about whether imports should be modeled as transactions or as jobs.

### Disagreement 1: Import processing model
- **Primary's position:** Synchronous import via ScrapingBee. Single `POST /api/imports` blocks until scrape completes (or times out at 30s). Result returned in the response body.
- **Rival's position:** Asynchronous import via BullMQ-orchestrated workers. `POST /api/import-jobs` returns immediately with a job ID. Client polls `GET /api/import-jobs/:id/results` or subscribes via webhook. Workers can retry, results persist independently.
- **Decision type:** pattern_choice
- **Requires CEO decision:** true
- Primary section: `## API Surface`
- Rival section: `## API Surface, ## Concurrency`

### Disagreement 2: Scraping provider
- **Primary's position:** ScrapingBee — single vendor, simple API, claimed 99% success rate per their docs.
- **Rival's position:** Apify with Puppeteer — open-source actor model, more configurable, supports custom scrape logic. Notes that ScrapingBee has documented rate limits (5 req/s on Business tier per stripe.com/docs/api-keys/limits) that conflict with the sprint's "20+ concurrent therapists" requirement.
- **Decision type:** technology_choice
- **Requires CEO decision:** true
- Primary section: `## Dependencies`
- Rival section: `## Dependencies, ## Concurrency`

### Disagreement 3: Retry semantics for failed scrapes
- **Primary's position:** No retry. If ScrapingBee fails, return error to user, user retries manually.
- **Rival's position:** Automatic retry with exponential backoff (3 attempts: 5s, 30s, 5min). Dead-letter queue for permanently failed jobs, polled hourly for manual review. Idempotency key required on every POST so client retries are safe.
- **Decision type:** pattern_choice
- **Requires CEO decision:** true
- Primary section: `## Error Handling`
- Rival section: `## Error Handling, ## Concurrency`

### Disagreement 4: Concurrency capacity
- **Primary's position:** Not explicitly addressed. Architecture assumes one-import-at-a-time per user with no global concurrency limits.
- **Rival's position:** Explicit concurrency limits: 5 jobs per user, 50 jobs globally, distributed via Redis-backed BullMQ rate limiter. Race condition on duplicate imports of the same URL handled via SHA-256 hash deduplication.
- **Decision type:** scope_decision
- **Requires CEO decision:** true
- Primary section: `## Concurrency`
- Rival section: `## Concurrency`

## Stage 8: Verdict Detail

### Escalations (CEO decision required)
- Import processing model: primary=Synchronous import via ScrapingBee. Single POST blocks until scrape completes.; rival=Asynchronous import via BullMQ-orchestrated workers. POST returns immediately, client polls for results.
- Scraping provider: primary=ScrapingBee — single vendor, simple API.; rival=Apify with Puppeteer — open-source, more configurable, notes ScrapingBee rate limit conflict.
- Retry semantics for failed scrapes: primary=No retry; user retries manually.; rival=Automatic retry with exponential backoff and dead-letter queue.
- Concurrency capacity: primary=Not explicitly addressed.; rival=Explicit limits: 5/user, 50 global, deduplication via SHA-256.
- Data models substantially different: only 43% of tables overlap

## Source Documents

- Primary architecture: `/Users/deanfalconer/startup-workspace/artifacts/designs/therapist-website-import/tech/architecture.md`
- Primary API spec: `/Users/deanfalconer/startup-workspace/artifacts/designs/therapist-website-import/tech/api_spec.json`
- Primary DB schema: `/Users/deanfalconer/startup-workspace/artifacts/designs/therapist-website-import/tech/db_schema.sql`
- Rival architecture: `/Users/deanfalconer/startup-workspace/artifacts/designs/therapist-website-import/tech/rival/architecture.md`
- Rival API spec: `/Users/deanfalconer/startup-workspace/artifacts/designs/therapist-website-import/tech/rival/api_spec.json`
- Rival DB schema: `/Users/deanfalconer/startup-workspace/artifacts/designs/therapist-website-import/tech/rival/db_schema.sql`

## Protocol Attestation

- ✅ Both architectures produced independently — neither saw the other's output before producing its own
- ✅ Structural diffs (Stages 1-6) computed by deterministic Python code
- ✅ Stage 7 LLM call constrained to surface disagreements only — does not decide which is better
- ✅ Verdict computation (Stage 8) is deterministic — code, not LLM
- ✅ Audit log entry written to `logs/architecture_comparisons.jsonl`

---

## What This Example Shows

This is the high-value case for the Rival Architect. Both architects are competent. Both produced complete, defensible architectures. Neither is "wrong." But they reached **fundamentally different solutions to the same problem** — Claude defaulted to a synchronous transactional model, Gemini defaulted to an asynchronous job-queue model.

Critically:

1. **The rival caught a load-bearing constraint Claude missed.** ScrapingBee has documented rate limits (5 req/s on Business tier) that conflict with the sprint's "20+ concurrent therapists" requirement. Claude's training data likely associates ScrapingBee with "easy scraping" and didn't surface the rate limit. Gemini, with different training data, did. This is exactly the Milvus 2026 finding: Gemini catches concurrency and compatibility issues Claude misses.

2. **The decision is genuinely the CEO's.** Synchronous-vs-async is a trade-off, not a bug. Synchronous is simpler to build and debug. Async is more resilient and supports higher throughput. Without knowing the expected import volume, the deployment timeline, and the team's operational maturity, neither architecture is "better."

3. **The compare script does not decide.** Stage 7's constrained LLM prompt explicitly forbids "which is better" judgments. The script surfaces the four substantive disagreements and ESCALATES. The CEO sees both architectures, both reasonings, and both implications, and decides.

4. **What happens next:** the CEO opens both `architecture.md` files in a side-by-side review (paths in the report), reads each architect's reasoning in the disagreement sections, and responds via `/btw approve sync` or `/btw approve async` (or some custom direction). The COO records the decision in `decisions.jsonl`, then advances Phase 5 with the chosen architecture.

This is what "two heads are better than one" looks like as a structural protocol: not arguing, not voting, just two independent perspectives surfaced to the human who has to decide.
