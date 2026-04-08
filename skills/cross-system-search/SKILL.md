---
name: cross-system-search
description: >
  Exhaustive cross-system entity search with runtime system discovery,
  fuzzy matching, breadcrumb following, and search exhaustion tracking.
  Searches across ALL connected systems before concluding "not found."
triggers:
  - find
  - search across
  - look up
  - where is
  - do we have
  - cross-system
  - entity search
---

# Cross-System Entity Search

## Core Rule

**NEVER report "not found" after checking only one system or one dataset.** Search every available system, every dataset, every environment, and cross-reference identifiers between systems before concluding something is missing.

## When to Use

- Finding a person, business, or record across connected systems
- Verifying whether data exists before creating duplicates
- Auditing a customer's footprint across all platforms
- Answering "do we have anything on [entity]?"

## Arguments

Parse `$ARGUMENTS` for:
- The entity to find (name, email, phone, ID, URL, or any identifier)
- Optional: `--type person|business|record` (default: infer from identifiers)
- Optional: `--exhaustive` (search ALL systems even low-probability ones)
- Optional: `--dry-run` (show what would be searched without searching)

---

## Phase 1: Discover Available Systems

**Do this FIRST, every time.** The set of available systems changes between sessions.

### 1a. Parse MCP Servers from System Context

Extract server names from deferred tools in the system-reminder:
```
servers = unique prefixes from mcp__<ServerName>__<tool> patterns
```

### 1b. Check Environment Variables

```bash
# Source Doppler secrets if available
set -a; source /tmp/.claude-doppler-env 2>/dev/null; set +a

# Detect configured services by env var presence
for var in ANTHROPIC_API_KEY STRIPE_SECRET_KEY GHL_ACCESS_TOKEN \
  SANITY_API_WRITE_TOKEN SANITY_API_READ_TOKEN SENTRY_AUTH_TOKEN \
  NETLIFY_API_TOKEN GITHUB_PAT GH_TOKEN DIGITAL_OCEAN \
  BRIGHT_DATA_API_TOKEN CLOUDFLARE_API_TOKEN; do
  [ -n "${!var}" ] && echo "CONFIGURED: $var"
done
```

### 1c. Check CLI Tools

```bash
for cmd in gh netlify doctl doppler; do
  command -v "$cmd" >/dev/null 2>&1 && echo "CLI: $cmd"
done
```

### 1d. Build the System Registry

From the discovery above, build a runtime registry of what's available and what each system can search by. Use the capability matrix in [reference/capability_matrix.md](./reference/capability_matrix.md).

---

## Phase 2: Normalize Identifiers

Before searching ANY system, normalize every identifier the user provided.

| Field | Normalization |
|-------|--------------|
| **Name** | Lowercase, strip titles (Dr./Mr./Ms.), split into first/middle/last, expand nicknames (Bob→Robert, Bill→William) |
| **Phone** | Strip all non-digits, prepend country code if missing. `(555) 123-4567` → `+15551234567` |
| **Email** | Lowercase, strip `+aliases`, strip dots from Gmail local part. `J.Doe+work@Gmail.com` → `jdoe@gmail.com` |
| **Business name** | Lowercase, strip legal suffixes (Inc/LLC/Ltd/Corp), remove possessives and punctuation |
| **URL** | Extract the unique identifier (PT ID from Psychology Today URL, slug from site URL, etc.) |

### Nickname Expansion (Common)

```
bob/bobby/rob → robert    bill/billy/will → william
dick/rick/rich → richard  liz/beth/betty → elizabeth
jim/jimmy/jamie → james   mike/mikey → michael
dan/danny → daniel        pat/patty → patricia
sue/suzy → susan          dave/davy → david
tom/tommy → thomas        steve → stephen/steven
chris → christopher/christine  al → albert/alan/alexander
```

---

## Phase 3: Search — Tiered Exhaustion Protocol

Search in order of reliability. **Track every query in the search matrix** (see Phase 5).

### Tier 1: Authoritative Sources (search FIRST)

These are the systems of record. If the entity exists anywhere, it's most likely here.

| Entity Type | Authoritative Source | Search Method |
|-------------|---------------------|---------------|
| Customer/Contact | GoHighLevel CRM | `get-contacts` by name, email, phone |
| Content/Profile | Sanity CMS | GROQ query across ALL datasets |
| Payment/Subscription | Stripe | `search_stripe_resources` by name, email |
| Code/PR/Issue | GitHub | `gh search` by keyword, author |
| Error/Event | Sentry | `search_issues` by user, message |

**For EVERY Tier 1 system, search with ALL normalized identifiers:**
- Full name (exact)
- Full name (partial/wildcard: `*LastName*`)
- Email (exact)
- Phone (exact, digits only)
- Any IDs from the user's input

### Tier 2: Secondary Sources (search NEXT)

| System | When to Search | Search Method |
|--------|---------------|---------------|
| Gmail | Always for people | `gmail_search_messages` with name, email, phone |
| Otter.ai | If looking for meeting context | `search` by name or topic |
| Netlify | If looking for deployments/sites | `netlify-project-services-reader` |
| NPI Registry | If entity is a healthcare provider | `npi_search` by name + state |
| ClickUp | If project/task context | `search` by keyword |

### Tier 3: Web & External (search LAST)

| System | When to Search | Search Method |
|--------|---------------|---------------|
| Bright Data | When entity has a public web presence | `search_engine` or structured extractors |
| Chrome DevTools | When checking if a live URL renders | `navigate_page` + `take_screenshot` |
| Web Search | When checking public presence | `WebSearch` for name + business + location |

---

## Phase 4: Cross-Reference Amplification

**This is the critical step that prevents the failures from Mary Jo Harmon and Twana Curry.**

When you find data in ANY system, extract ALL identifiers and use them to search systems you've already checked:

```
Found in GHL:
  email: jane@therapy.com
  phone: (555) 123-4567
  tags: [purchased]
  custom_fields: {slug: "abc123", pt_link: "psychologytoday.com/us/therapists/123456"}

→ NEW SEARCH VECTORS:
  - Search Sanity for slug "abc123"
  - Search Sanity for sourceUrl matching "123456"
  - Search Stripe for email "jane@therapy.com"
  - Search Gmail for "jane@therapy.com"
  - WebFetch the PT link for additional data (office address, credentials)
```

**Rules:**
1. Every newly discovered identifier gets searched in ALL previously-searched systems
2. Cap amplification at 2 hops (entity A → entity B → entity C, stop)
3. Track which identifiers have been searched where (the search matrix handles this)

---

## Phase 5: Search State Matrix

Maintain this structure throughout the search. Print it in the final report.

```
SEARCH MATRIX — {Entity Name/Description}
══════════════════════════════════════════

Identifiers:
  [1] name: "Jane Smith" (user input)
  [2] email: "jane@therapy.com" (user input)
  [3] phone: "+15551234567" (discovered: GHL)
  [4] slug: "abc123" (discovered: GHL custom field)

Systems Searched:
  ✓ GoHighLevel   — [1]name:1 result, [2]email:1 result → Contact ID: xyz
  ✓ Sanity (prod)  — [1]name:0, [2]email:0, [4]slug:1 result → Profile abc123
  ✓ Sanity (dev)   — [1]name:0, [2]email:0, [4]slug:1 result → Profile abc123 (draft)
  ✓ Stripe         — [2]email:1 result → Customer cus_xxx
  ✓ Gmail          — [2]email:3 threads found
  ○ Sentry         — not relevant (no user-facing product)
  ○ NPI Registry   — [1]name+state: 1 result → NPI 1234567890
  — Otter.ai       — not available this session

Legend: ✓ searched  ○ searched (no results)  — not available/relevant
        ✗ ERROR (permission denied / API failure)

Exhaustion Status:
  [✓] All Tier 1 sources searched
  [✓] All Tier 2 sources searched
  [✓] All discovered identifiers cross-referenced
  [✓] All environments checked (production + develop)
  [ ] No permission errors unresolved
```

---

## Phase 6: Multi-Environment Awareness

**ALWAYS check multiple environments. This is the #1 cause of false "not found."**

| System | Environments to Check |
|--------|----------------------|
| **Sanity** | List ALL datasets first: `list_datasets`. Query each. Check both `perspective: "drafts"` and `"published"`. |
| **Stripe** | Check if key is test (`sk_test_`) or live (`sk_live_`). Note which mode data is in. |
| **GoHighLevel** | Check all sub-accounts if accessible. Note which location the API key is scoped to. |
| **Netlify** | Check both production deploys and preview/branch deploys. |
| **GitHub** | Check all branches, not just main. Check open AND closed PRs/issues. |

### Sanity Multi-Dataset Search Pattern

```groq
// ALWAYS list datasets first
list_datasets → ["production", "develop", "staging"]

// Then search EACH dataset
// By name (partial)
*[_type == "profile" && founder.name match "*Smith*"]{ _id, founder, slug, _createdAt }

// By email
*[_type == "profile" && contactDetails.email == "jane@therapy.com"]

// By phone (flexible matching — different formats exist)
*[_type == "profile" && contactDetails.phone match "*5551234567*"]

// By slug
*[_type == "profile" && slug.current == "abc123"]

// By source URL (extract ID from URL)
*[_type == "profile" && therapistProfile.sourceUrl match "*123456*"]

// By location (when name search fails, narrow by geography)
*[_type == "profile" && contactDetails.city == "Memphis" && contactDetails.state == "TN"]
```

---

## Phase 7: Verdict

### Entity Found

Present a consolidated view across all systems:

```
ENTITY FOUND: Jane Smith
═══════════════════════════

| System | Record | Key Data |
|--------|--------|----------|
| GoHighLevel | Contact xyz | email, phone, tags: [purchased] |
| Sanity (develop) | Profile abc123 | Full website content, 11 services |
| Sanity (production) | NOT PRESENT | Needs promotion from develop |
| Stripe | Customer cus_xxx | No active subscription |
| Gmail | 3 threads | Last contact: 2026-03-15 |
| NPI | 1234567890 | Licensed Clinical Social Worker, IL |

Discrepancies:
- Profile exists in develop but NOT production (site will 404)
- GHL slug field is empty (should be "abc123")
- Email in Sanity is empty (GHL has it)

Recommended Actions:
1. Promote Sanity profile from develop → production
2. Update GHL slug custom field to "abc123"
3. Add email to Sanity contact details
```

### Entity Not Found

Only after the search matrix shows ALL systems searched with ALL identifiers:

```
ENTITY NOT FOUND: Jane Smith
═════════════════════════════

Search exhaustion confirmed:
  ✓ 6 systems searched
  ✓ 4 identifiers used across all systems
  ✓ 2 environments checked per system
  ✓ 0 permission errors
  ✓ 0 new identifiers discovered (no amplification needed)

This entity does not exist in any connected system.
[Search matrix attached above]
```

---

## Query Templates Quick Reference

### GoHighLevel
```
get-contacts with query: "Jane Smith"
get-contacts with email: "jane@therapy.com"
get-contacts with phone: "+15551234567"
```

### Stripe
```
search_stripe_resources: customers where email~"jane" AND name~"smith"
list_customers (paginate if needed)
```

### Gmail
```
gmail_search_messages: "jane smith" OR "jane@therapy.com"
gmail_search_messages: from:jane@therapy.com
gmail_search_messages: to:jane@therapy.com
```

### GitHub
```
gh search issues "jane smith" --repo=owner/repo
gh search prs --author=username
gh search code "identifier" --filename="*.ts"
```

### Sentry
```
search_issues: user.email:jane@therapy.com
search_events: user.email:jane@therapy.com
```

### NPI Registry
```
npi_search: first_name=Jane, last_name=Smith, state=IL
npi_search: organization_name="Smith Counseling"
```

### Otter.ai
```
search: "Jane Smith" OR "Smith Counseling"
```

---

## Anti-Patterns (What NOT to Do)

1. **Search one dataset, report "not found"** — The Mary Jo Harmon failure. Always `list_datasets` first.
2. **Use exact match only** — Names have variations. Use wildcards: `match "*Smith*"` not `== "Smith"`.
3. **Search systems in isolation** — The Twana Curry failure. Cross-reference identifiers between systems.
4. **Assume production is canonical** — Data may exist in develop/staging but not production.
5. **Report "not found" without a search matrix** — If you can't show what you searched, you didn't search enough.
6. **Skip WebFetch/browser verification** — WebFetch can't render SPAs. Use Chrome DevTools to verify live URLs.
7. **Treat permission errors as "not found"** — API errors, wrong scopes, and missing access are NOT the same as non-existence. Log them separately.
8. **Hardcode the system list** — Systems change between sessions. Discover at runtime.
