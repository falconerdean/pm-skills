# Phase 5: Technical Design

## CRITICAL: EXECUTABLE ARCHITECTURE

You are producing a technical design that will be directly implemented in the next phase.
Your API spec must be complete enough to generate route handlers from. Your database schema
must be valid SQL that can be executed. Your architecture document must contain real technology
choices with real configuration, not "we could use X or Y."

Make decisions. Be specific. Write things that can be executed.

## Input
- Read: {workspace}/artifacts/requirements/{epic}/stories.json
- Read: {workspace}/artifacts/requirements/{epic}/epics.json
- Read: {workspace}/artifacts/designs/{epic}/ui_spec.md
- Read: {workspace}/artifacts/designs/{epic}/ux_flows.md

## Process

### Step 1: API Design
Use /tools:api-scaffold patterns:
- Define all API endpoints mapped to stories (method, path, request/response types)
- Specify request/response shapes as actual TypeScript interfaces or JSON Schema
- Define authentication approach with specific implementation (JWT, session, OAuth provider)
- Set rate limiting values and versioning strategy

### Step 2: Data Architecture
Use /tools:data-pipeline and /tools:data-validation patterns:
- Design database schema (entities, relationships, indexes) as real SQL or ORM models
- Define data flow (write path, read path) with specific technologies
- Specify caching strategy with TTLs and invalidation rules
- Define validation rules as actual schemas (Zod, JSON Schema, etc.)

### Step 3: Database Schema
Use /tools:db-migrate patterns:
- Generate actual migration files that can be run
- Define seed data as real SQL INSERT statements or seed scripts
- Plan zero-downtime migration strategy

### Step 4: Infrastructure Design
Using /tools:config-validate and /tools:deploy-checklist patterns:
- Select specific cloud services and justify (not "AWS or GCP" — pick one)
- Design CI/CD pipeline with specific steps
- Define environment strategy (dev/staging/prod) with real config values
- Specify monitoring approach with specific tools and alert thresholds

### Step 5: System Architecture
Produce an architecture document with:
- Architecture style decision (monolith/microservices/serverless) with rationale
- ASCII or Mermaid architecture diagram
- Service boundaries and communication patterns
- Security architecture (auth flow, data encryption, API security)

### Step 6: Architecture Review
Use /workflows:full-review to get multi-perspective review:
- Architecture: scalability, maintainability
- Security: threat model, data protection
- Performance: bottleneck identification
If critical issues, revise (max 2 iterations).

## Output
Write to {workspace}/artifacts/designs/{epic}/tech/:
- architecture.md (system design, diagrams, concrete decisions)
- api_spec.json (complete endpoint inventory with request/response types)
- db_schema.sql (executable migration-ready schema)
- infra_spec.md (specific cloud services, CI/CD config, monitoring setup)

## State Update
Update {workspace}/state/company_state.json:
- Set `sdlc.phases.tech_design.status` to `"complete"`
- Set `sdlc.phases.tech_design.completed_at` to current UTC ISO timestamp (with Z suffix)
