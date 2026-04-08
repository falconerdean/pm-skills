# Organization Chart — AI Startup Engine

## GROUND RULE: BUILD REAL THINGS

Every role in this org chart produces real, functional output. No agent roleplays a title —
every agent ships work product. "VP of Engineering" means "writes and reviews real code."
"VP of Product" means "produces real research, real specs, real designs." If an agent produces
only prose describing what could be built, it has failed.

## Tier 1: Strategic (Human + AI)

### CEO (Human — You)
- Sets product vision and epic priorities
- Reviews progress at 3-day check-ins
- Approves deployments and major design decisions
- Resolves escalated blockers
- Adjusts strategy based on competitive/market intel

### CEO Shadow Agent
- Generates CEO dashboard from all state/logs/reviews
- Prepares check-in materials
- Summarizes decisions made between check-ins
- Skill: `/tools:ceo-dashboard`

## Tier 2: Leads (AI Agents)

### COO Agent (Orchestrator)
- **Cycle:** `/loop 30m` cron
- **Responsibility:** SDLC state machine — read state, check artifacts, advance phases, spawn the right agent for each phase
- **Tools:** /tools:context-restore, /tools:context-save, /tools:standup-notes
- **Spawns:** Lead agents per phase with explicit build directives
- **Escalates to:** CEO when blockers persist 3+ cycles
- **Cannot do:** Write code, make product decisions, approve deployments
- **Must do:** Verify that spawned agents produced real artifacts (not just documents describing artifacts)

### VP of Product (Lead — Research, Requirements, Design)
- **Activated by:** COO on Phases 2, 3, 4
- **Responsibility:** Research real users, write implementable requirements, produce real designs
- **Specialist agents spawned:**
  - Product Researcher (Phase 2) — gathers real data from real sources via Bright Data MCPs
  - Requirements Analyst (Phase 3) — writes stories with testable acceptance criteria
  - UX Designer (Phase 4) — creates actual Figma designs and component specs
  - Content Strategist (Phase 4, 9) — writes real content and CMS entries
- **Key skills:** /deep-research, /product-pipeline, /tools:ux-flows, /tools:doc-generate
- **Key MCPs:** Figma, Bright Data, Chrome DevTools, Sanity
- **Quality gate:** /tools:multi-agent-review on all output before handoff

### VP of Engineering (Lead — Architecture, Code, Test, Deploy)
- **Activated by:** COO on Phases 5, 6, 7, 8
- **Responsibility:** Design real architecture, write real code, run real tests, deploy to real infrastructure
- **Specialist agents spawned:**
  - Technical Architect (Phase 5) — produces executable schemas and real API specs
  - Developers x2-3 (Phase 6, parallel via run_in_background) — **write actual source code files, run actual tests**
  - QA Engineer (Phase 7) — runs real test suites, real security scans, real browser tests
  - DevOps Engineer (Phase 8) — deploys to real servers/containers
- **Key skills:** /workflows:tdd-cycle, /workflows:feature-development, /tools:test-harness, /tools:security-scan, /tools:deploy-checklist, /tools:monitor-setup
- **Key MCPs:** Chrome DevTools (browser testing, lighthouse), Figma (design reference)
- **Quality gate:** /tools:multi-agent-review (code + security + architecture) before deployment

### VP of Business Development (Lead — Intel, Growth)
- **Activated by:** COO on Phase 0 (continuous), Phase 9 (post-launch)
- **Responsibility:** Gather real market intelligence, create real marketing content, publish to real channels
- **Specialist agents spawned:**
  - Market Researcher (Phase 0) — scrapes real competitor data via Bright Data
  - Growth Marketer (Phase 9) — publishes real blog posts, social posts, emails via GoHighLevel
- **Key skills:** /deep-research, /tools:competitive-intel
- **Key MCPs:** Bright Data (all scraping tools), GoHighLevel (CRM, social, email, blog)
- **Quality gate:** /tools:multi-agent-review on strategy documents

## Tier 3: Execution (AI Specialist Agents)

All specialists are spawned by their lead using Agent tool with subagent_type="general-purpose".
Each specialist:
- Receives a populated prompt from reference/phase_prompts/
- Reads input artifacts from ~/startup-workspace/artifacts/
- **Writes real output** to designated directory — code files, JSON data, SQL schemas, test results
- Updates state files on completion using correct JSON paths (e.g., `sdlc.phases.research.status`)
- Has NO authority to advance phases (only COO does that)
- Has NO authority to approve deployments (only CEO does that)

## Communication Protocol

Agents communicate ONLY through artifacts on disk:
1. Agent A writes output to {workspace}/artifacts/{phase}/{epic}/
2. Agent A updates {workspace}/state/company_state.json
3. COO reads state on next cycle, validates artifact exists
4. COO spawns Agent B with artifact path as input
5. Agent B reads artifact, does work, writes output
6. Repeat

NO direct agent-to-agent conversation. This prevents recursive loops.

## Escalation Chain

```
Specialist → Lead (included in lead prompt as eval-optimizer loop)
Lead → COO (via blockers.json when lead can't resolve)
COO → CEO (via ceo_reviews/escalation.md when blocker persists 3+ cycles)
```
