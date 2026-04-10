# Canonical Architecture Schema

This document defines what a complete technical architecture must contain. Both the primary architect (Claude VP Engineering) and the rival architect (Gemini 3 Pro) are evaluated against this schema. The compare script checks that both architectures cover all eleven required sections; missing sections become a structural diff finding.

The schema is intentionally framework-agnostic — it does not prescribe REST vs GraphQL, Postgres vs MongoDB, or k8s vs Lambda. Architects choose these per the requirements and defend their choices in the relevant section.

---

## Required Sections (in order)

### 1. Overview

One paragraph. What system is being built, what does it do at a high level, and what is the architectural pattern (monolith, microservices, serverless, JAMstack, etc.). The reader should be able to understand the scope from this section alone.

**Example phrasing:**
> Insite Profile Customization is a feature within a Next.js 15 monolith that allows therapists to upload a custom headshot, edit their bio, and select up to 5 specialty tags. State is persisted to Sanity CMS via authenticated server actions. The feature integrates with the existing therapist authentication and consumes the existing user session. No new microservices are introduced.

### 2. Data Model

Describe the entities, their relationships, and how data flows through the system. Reference db_schema.sql for the actual SQL. This section is prose; the SQL is the contract.

**Required sub-content:**
- Entity list with one-line description of each
- Relationship diagram (text-based, e.g., "User 1:N Profile, Profile 1:N Specialty")
- Ownership: which service or component owns each entity
- Data flow: how data moves through the system on a typical request

### 3. API Surface

Describe the user-facing and integration-facing APIs. Reference api_spec.json for the actual contract. This section is prose; the JSON spec is the contract.

**Required sub-content:**
- Total endpoint count
- Public vs authenticated breakdown
- High-level grouping (auth, profile, content, admin, etc.)
- Versioning strategy
- Pagination strategy (if applicable)
- Rate limiting strategy

### 4. Authentication

How users prove who they are. Specific decisions:

- Auth provider (built-in, Clerk, Auth0, Supabase, NextAuth, custom)
- Token format (JWT, session cookie, opaque token)
- Token storage (HTTP-only cookie, localStorage, memory)
- Session lifetime
- Refresh strategy
- MFA support (yes/no, which methods)
- Password requirements (if applicable)
- Social login providers (if any)

### 5. Authorization

How the system decides what authenticated users can do. Specific decisions:

- Authorization model (RBAC, ABAC, ACL, custom)
- Role definitions and permissions
- Where authorization checks happen (middleware, function decorators, database policies)
- How permissions are tested
- Admin/owner/user/guest distinctions

### 6. Deployment

Where the system runs in production. Specific decisions:

- Cloud provider (AWS, GCP, Azure, Vercel, Netlify, DigitalOcean, Cloudflare, fly.io, self-hosted)
- Runtime (Node.js version, Python version, container, edge function, serverless)
- Region(s)
- Scaling model (vertical, horizontal, auto-scaling rules)
- CDN strategy
- Database hosting
- Static asset hosting
- Environment separation (dev/staging/prod)

### 7. Observability

How problems are detected and diagnosed in production. Specific decisions:

- Logging stack (CloudWatch, Datadog, Sentry, Logtail, custom)
- Metrics platform
- Tracing (OpenTelemetry, Datadog APM, custom)
- Alerting rules
- Dashboards
- On-call rotation (if applicable to scope)
- Error budgets and SLOs

### 8. Concurrency

How the system handles concurrent requests, race conditions, locking, queueing, retries. **This section is required to be substantive — not a one-liner.** It is the section where the rival architect's specialization (Gemini's documented strength on concurrency per Milvus 2026) is most likely to surface differences from the primary.

**Required sub-content:**
- Race conditions identified and how they're prevented
- Locking strategy (optimistic, pessimistic, advisory locks, Redis distributed locks)
- Queueing strategy (if applicable): which queue, ordering guarantees, dead letter handling
- Retry semantics: which operations retry, max attempts, backoff strategy
- Idempotency: which endpoints are idempotent, how clients prove idempotency
- Ordering guarantees: where order matters, how it's preserved
- Eventual consistency: where it's acceptable, where it isn't
- Specific race condition examples for THIS feature, with mitigation

### 9. Error Handling

Failure modes and how the system responds. Specific decisions:

- Error response format (HTTP status + JSON error body shape)
- Client-facing error messages vs internal error details
- Retry logic for upstream failures
- Circuit breakers (if applicable)
- Fallback behavior when external services are down
- User-facing error pages and messaging

### 10. Dependencies

Third-party libraries, SDKs, external services. **Specific versions where it matters.**

**Required sub-content:**
- Direct dependencies with version pins
- External services consumed (Stripe, Sanity, GHL, etc.) with API version
- Dev dependencies that affect the build
- License audit (any GPL/AGPL/SSPL?)
- Critical security dependencies that need monitoring (auth libs, crypto, etc.)
- For each external service, the verification method (e.g., "Stripe API verified at https://docs.stripe.com/api on 2026-04-10")

### 11. Compatibility

Runtime versions, browser support, OS support, language version constraints. **This section is required to be substantive.** It is the second section where the rival architect's specialization (Gemini's strength on compatibility per Milvus 2026) is most likely to surface differences.

**Required sub-content:**
- Node.js / Python / Ruby / etc. version range
- Database server version requirements
- Browser support matrix (if applicable)
- Mobile OS support (if applicable)
- Known incompatibilities between dependencies
- Migration path from older versions (if relevant)

---

## How the Compare Script Uses This Schema

For each architecture under review, the compare script:

1. **Parses the markdown for level-2 headings** (`## Section Name`)
2. **Maps each heading to a canonical section** using fuzzy matching (e.g., "Auth", "Authentication", "User Auth" all match section 4)
3. **Records which canonical sections are present and which are missing**
4. **Flags any architecture missing required sections** as a BLOCK condition
5. **For sections 8 (Concurrency) and 11 (Compatibility) specifically**, counts the section length in words. If either section is shorter than ~100 words, the architect is flagged for "shallow specialization treatment"

The compare script does NOT evaluate the QUALITY of any section's content. It only checks structural presence and substance. Quality differences between the two architectures are surfaced via the constrained LLM call in the comparison protocol, not via this schema.

## Anti-Patterns

The schema exists to catch architectures that look complete but are actually thin. Common anti-patterns the schema defends against:

1. **Authentication section that says "we use auth" with no specifics** — the schema requires auth provider, token format, storage, lifetime. If any are missing, the section is incomplete.

2. **Concurrency section that says "we use a queue"** — the schema requires queue choice, ordering guarantees, dead letter handling, race conditions identified, retry semantics. A one-liner fails.

3. **Dependencies section without versions** — "We use React" is not a dependency. "React 19.0.0" is.

4. **Deployment section without regions, scaling, or CDN** — "We deploy to AWS" is not deployment. The full stack of decisions is.

5. **Observability section that says "we use Datadog" with no rules or dashboards** — half a tool is half an answer.

If the primary architect (Claude) writes a thin section and the rival architect (Gemini) writes a substantive one for the same section, the compare script flags it as an asymmetry — the CEO sees that one architect dug deeper than the other on a specific dimension.
