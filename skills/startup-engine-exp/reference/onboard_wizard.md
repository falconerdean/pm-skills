# Onboarding Wizard — CEO Setup Interview

Run this wizard during INITIALIZE to configure the project before any agents start work.
Ask questions conversationally — don't dump all questions at once. Group them into stages.
Write answers to `~/startup-workspace/state/project_config.json`.

## How to Run This Wizard

Ask each stage's questions, wait for the CEO's answers, then move to the next stage.
Use AskUserQuestion or direct conversation prompts. Offer sensible defaults in [brackets]
so the CEO can just hit enter to accept.

If the CEO gives a brief answer, infer what you can and confirm. For example:
- CEO says "a task manager" → infer it's a web app, ask to confirm
- CEO says "Next.js" → fill in frontend.framework=Next.js, frontend.language=TypeScript, ask to confirm
- CEO says "just deploy to Netlify" → fill in hosting.provider=netlify, hosting.type=static/SSR

---

## Stage 1: The Product (required)

> "What are we building? Give me the elevator pitch."

From the CEO's answer, extract and confirm:

| Field | Question if not clear | Default |
|-------|----------------------|---------|
| `product.name` | "What should we call it?" | — |
| `product.tagline` | "One-line tagline?" | Generate from description |
| `product.description` | "Tell me more — what does it do?" | — |
| `product.target_audience` | "Who is this for?" | — |
| `product.problem_statement` | "What problem does it solve?" | Infer from description |
| `product.desired_outcomes` | "What does success look like? (e.g., 1000 users, $10K MRR, launch by June)" | — |

**After this stage, summarize back:**
> "Got it — we're building **{name}**: {tagline}. Target audience is {audience}.
> Success = {outcomes}. Sound right?"

---

## Stage 2: The Repository (required)

> "Are we starting a new repo or working in an existing one?"

| Answer | Follow-up | Config |
|--------|-----------|--------|
| "New" | "Where should I create it? [~/startup-workspace/code/{product.name}]" | `repository.type = "new"` |
| "Existing" | "What's the repo URL or local path?" | `repository.type = "existing"`, set url/path |
| Gives a GitHub URL | Parse owner/repo, set url + clone path | `repository.url = "..."` |
| Gives a local path | Verify it exists, check if it has a git remote | `repository.local_path = "..."` |

Then ask:
> "Default branch? [main]"
> "Is this a monorepo (multiple packages/apps in one repo)? [no]"

---

## Stage 3: Tech Stack (required — with smart defaults)

> "What tech stack? If you're not sure, I'll pick a solid default for the type of product."

### If CEO has a preference:
Ask specifically about what they mention, fill in the rest with compatible defaults.

### If CEO says "you pick" or "whatever works":
Choose based on the product type:

| Product Type | Frontend | Backend | DB | Hosting |
|-------------|----------|---------|-----|---------|
| Web app (SaaS) | Next.js / TypeScript / Tailwind | Next.js API routes | PostgreSQL (Supabase or Neon) | Netlify or Vercel |
| Marketing site | Next.js / TypeScript / Tailwind | — (static or SSG) | — | Netlify |
| API / Backend service | — | Express or Fastify / TypeScript | PostgreSQL | DigitalOcean or Railway |
| Mobile app | React Native / TypeScript | Express / TypeScript | PostgreSQL | DigitalOcean |
| CLI tool | — | Node.js / TypeScript | — (file or SQLite) | npm publish |
| AI/ML product | Next.js / TypeScript / Tailwind | Python / FastAPI | PostgreSQL + Redis | DigitalOcean |

**Present the recommendation:**
> "For a {product_type}, I'd go with:
> - **Frontend:** Next.js + TypeScript + Tailwind CSS
> - **Backend:** Next.js API routes (fullstack)
> - **Database:** PostgreSQL via Supabase
> - **Hosting:** Netlify
>
> Want to change anything, or is this good?"

### Specific questions if needed:

| Field | Question | Common answers |
|-------|----------|---------------|
| `tech_stack.frontend.framework` | "Frontend framework?" | Next.js, React, Vue, Svelte, Astro, none |
| `tech_stack.frontend.language` | "TypeScript or JavaScript?" | TypeScript [default], JavaScript |
| `tech_stack.frontend.styling` | "CSS approach?" | Tailwind [default], CSS Modules, styled-components, Sass |
| `tech_stack.frontend.component_library` | "Component library?" | shadcn/ui, MUI, Chakra, Radix, none |
| `tech_stack.backend.framework` | "Backend framework?" | Next.js API, Express, Fastify, Django, FastAPI, none |
| `tech_stack.backend.language` | "Backend language?" | TypeScript [default], Python, Go |
| `tech_stack.backend.api_style` | "API style?" | REST [default], GraphQL, tRPC |
| `tech_stack.database.type` | "Database?" | PostgreSQL [default], MySQL, MongoDB, SQLite, none |
| `tech_stack.database.provider` | "Database hosting?" | Supabase, Neon, PlanetScale, self-hosted, local |
| `tech_stack.hosting.provider` | "Deploy to?" | Netlify [default], Vercel, DigitalOcean, AWS, Railway |
| `tech_stack.hosting.type` | (infer from framework) | static, SSR, serverless, container |

---

## Stage 4: Integrations (optional — ask briefly)

> "A few quick questions about integrations. Say 'skip' for any you don't need."

| Integration | Question | If yes |
|-------------|----------|--------|
| CMS | "Need a CMS for content? [skip / Sanity / other]" | Set provider, ask for project ID if Sanity |
| Design | "Got an existing Figma file, or start fresh? [fresh / paste Figma URL]" | Set provider + file URL |
| Marketing | "Want automated marketing? (blog, social, email via GoHighLevel) [yes/skip]" | Set channels |
| Payments | "Need payments? [skip / Stripe / other]" | Set provider |
| Analytics | "Analytics? [skip / PostHog / other]" | Set provider |
| Error tracking | "Error tracking? [skip / Sentry / other]" | Set provider |

**Keep this fast.** Most of these can be added later via `/btw`.

---

## Stage 5: Preferences (optional — offer defaults)

> "Last few preferences, then we're ready to build."

| Field | Question | Default |
|-------|----------|---------|
| `preferences.tdd` | "Use TDD (test-driven development)? [yes]" | true |
| `preferences.ci_cd` | "Set up CI/CD pipeline? [yes]" | true |
| `preferences.code_review_strictness` | "Code review strictness? [standard / strict / relaxed]" | "standard" |
| `preferences.ceo_gate_on_design` | "Want to review designs before we build? [yes]" | true |
| `preferences.auto_deploy_staging` | "Auto-deploy to staging after tests pass? [yes]" | true |
| `preferences.budget_per_sprint` | "Budget cap per sprint? [$150]" | 150 |

---

## Stage 6: Confirmation

Summarize everything in a compact table:

```
STARTUP ENGINE — PROJECT CONFIGURATION
=======================================
Product:    {name} — {tagline}
Audience:   {target_audience}
Outcomes:   {desired_outcomes}

Repository: {type} at {path/url}
Stack:      {frontend.framework} + {backend.framework} + {database.type}
Hosting:    {hosting.provider}

Integrations: {list enabled ones}
TDD: {yes/no}  |  CI/CD: {yes/no}  |  Budget: ${budget}/sprint

Ready to build? [yes / change something]
```

If the CEO confirms: write `project_config.json`, proceed to env setup, then start Phase 1.
If the CEO wants changes: go back to the relevant stage.

---

## How VP Agents Use This Config

Every VP agent prompt should include:
- `project_config.json` path so agents know the tech stack, repo location, and preferences
- Agents MUST use the configured stack — don't pick a different framework
- Agents MUST write code to the configured repository path
- Agents MUST deploy to the configured hosting provider

Add this to every VP agent spawn prompt:
> "Read {workspace}/state/project_config.json for the tech stack, repository, and hosting
> configuration. Use the configured technologies — do not substitute your own preferences."
