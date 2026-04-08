# Phase 8: Technical Architecture Specification

You are a senior technical architect designing systems for production deployment. Your job is to define the complete technical architecture needed to implement the product's stories.

## Input

Read:
- `{output_dir}/story_map.json` (all stories with technical notes)
- `{output_dir}/discovery_brief.md` (constraints, personas, scale expectations)

## Instructions

### 1. System Architecture

**Architecture Style Decision:**
- Evaluate: monolith, modular monolith, microservices, serverless, hybrid
- Choose one with a 3-sentence rationale based on team size, complexity, and scale needs
- Draw an ASCII architecture diagram showing major components and data flows

**Service Boundaries (if applicable):**
For each service/module:
- Name and responsibility
- API surface (REST/GraphQL/gRPC)
- Data store
- Scaling characteristics

**Communication Patterns:**
- Synchronous: HTTP/REST, GraphQL, gRPC — when to use each
- Asynchronous: message queues, event bus — what events flow through
- Real-time: WebSockets, SSE — if stories require real-time updates

### 2. Data Architecture

**Database Selection:**
- Primary database: type (SQL/NoSQL/NewSQL) + specific technology + rationale
- Secondary stores if needed: cache, search, time-series, etc.

**Schema Design:**
- Entity list with key fields and relationships
- Relationship types (1:1, 1:N, M:N)
- Indexes needed for common query patterns (derived from stories)

**Data Flow:**
- Write path: how data enters the system
- Read path: how data is queried
- Caching strategy: what to cache, TTLs, invalidation approach

### 3. API Design

**Endpoint Inventory:**
For each endpoint needed by the stories:
- Method + Path (e.g., GET /api/v1/users)
- Request body / query params
- Response shape
- Auth requirement
- Rate limit
- Which stories use this endpoint

**Authentication:**
- Mechanism: JWT, session, OAuth2, API key
- Token lifecycle: issuance, refresh, revocation
- Multi-factor if required by security constraints

**Authorization:**
- Model: RBAC, ABAC, or resource-based
- Role definitions
- Permission matrix

**API Standards:**
- Versioning strategy (URL path vs header)
- Error response format
- Pagination approach
- Rate limiting tiers

### 4. Infrastructure

**Cloud Architecture:**
- Provider recommendation with rationale
- Core services: compute, storage, CDN, DNS
- Managed services: database, cache, queue, search

**Container Strategy:**
- Container runtime
- Orchestration (Kubernetes, ECS, Cloud Run, etc.)
- Service mesh if needed

**CI/CD Pipeline:**
- Source → Build → Test → Deploy stages
- Environment strategy: dev, staging, production
- Deployment strategy: blue-green, canary, rolling
- Rollback procedure

**Observability:**
- Logging: structured logging format, aggregation tool
- Metrics: key application metrics, infrastructure metrics, business metrics
- Tracing: distributed tracing approach
- Alerting: critical alerts, warning alerts, on-call setup

### 5. Security Architecture

**Defense in Depth:**
- Network layer: VPC, security groups, WAF
- Application layer: input validation, CSRF, XSS protection
- Data layer: encryption at rest (AES-256) and in transit (TLS 1.3)

**Secret Management:**
- Tool: Vault, AWS Secrets Manager, etc.
- Rotation policy
- Access control for secrets

**Compliance:**
- Data residency requirements
- PII handling and minimization
- Audit logging
- GDPR/CCPA considerations (if applicable based on research)

### 6. Technical Decisions

**Language & Framework:**
- Backend: language + framework + rationale
- Frontend: framework + build tool + rationale
- Mobile (if applicable): approach (native, cross-platform) + rationale

**Key Libraries:**
- ORM/database client
- HTTP client
- Validation library
- Testing framework
- State management (frontend)

**Build Tooling:**
- Package manager
- Bundler
- Linter/formatter
- Pre-commit hooks

### 7. Implementation Roadmap

**Sprint Plan (2-week sprints):**
- Sprint 0: Project setup, CI/CD, dev environment
- Sprint 1-N: Map epics to sprints based on epic sequencing
- For each sprint: primary deliverables, technical milestones

**Technical Spikes:**
- Unknowns that need investigation before implementation
- Time-boxed experiments to de-risk technical choices

**Performance Targets:**
- API response times: p50, p95, p99 targets
- Page load times: FCP, LCP, TTI targets
- Database query times: p95 target
- Throughput: requests/second target based on expected scale

## Output

Write to `{output_dir}/phase8_tech_architecture.md` as a well-structured markdown document with all sections above. Use ASCII diagrams for architecture, tables for API endpoints and decision matrices, and code blocks for configuration examples.
