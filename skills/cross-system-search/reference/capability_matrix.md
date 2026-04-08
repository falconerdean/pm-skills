# System Capability Matrix

Use this to determine which systems can answer which query types. Updated as new systems are connected.

## Search Capabilities

| System | By Name | By Email | By Phone | By ID | By Date | Full-Text | Fuzzy | Multi-Env |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| GoHighLevel | Y | Y | Y | Y | Y | Y | N | Sub-accounts |
| Sanity | Y (match) | Y | Y (match) | Y | Y | Y (match) | Y (match) | Datasets |
| Stripe | Y (~) | Y (~) | Y | Y | Y | N | Y (~) | Test/Live |
| Gmail | Y | Y | N | Y | Y | Y | N | N |
| GitHub | Y | Y (author) | N | Y (#) | Y | Y | N | Branches |
| Sentry | N | Y | N | Y | Y | Y | N | Projects |
| Netlify | Y | N | N | Y | N | N | N | Deploys |
| NPI Registry | Y | N | N | Y (NPI) | N | N | N | N |
| Otter.ai | Y | N | N | Y | Y | Y | N | N |
| DigitalOcean | Y | N | N | Y | N | N | N | Tags |
| Bright Data | scrape | N | N | N | N | scrape | N | N |
| Chrome DevTools | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| Cloudflare | Y | N | N | Y | N | Y (docs) | N | N |
| ClickUp | Y | N | N | Y | Y | Y | N | Spaces |
| Figma | Y | N | N | Y (file) | N | N | N | N |

## Detection Methods

| System | MCP Prefix | Env Var | CLI |
|--------|-----------|---------|-----|
| GoHighLevel | `mcp__GoHighLevel__` | `GHL_ACCESS_TOKEN` | — |
| Sanity | `mcp__Sanity__` | `SANITY_API_*_TOKEN` | — |
| Stripe | `mcp__claude_ai_Stripe__` | `STRIPE_SECRET_KEY` | — |
| Gmail | `mcp__claude_ai_Gmail__` | — | — |
| GitHub | — | `GITHUB_PAT` / `GH_TOKEN` | `gh` |
| Sentry | `mcp__Sentry__` | `SENTRY_AUTH_TOKEN` | — |
| Netlify | `mcp__claude_ai_Netlify__` | `NETLIFY_API_TOKEN` | `netlify` |
| NPI Registry | `mcp__claude_ai_NPI_Registry__` | — | — |
| Otter.ai | `mcp__claude_ai_Otter_ai__` | — | — |
| DigitalOcean | `mcp__digitalocean__` | `DIGITAL_OCEAN` | `doctl` |
| Bright Data | `mcp__Bright_Data__` | `BRIGHT_DATA_API_TOKEN` | — |
| Chrome DevTools | `mcp__chrome-devtools__` | — | — |
| Cloudflare | `mcp__claude_ai_Cloudflare*` | `CLOUDFLARE_API_TOKEN` | — |
| ClickUp | `mcp__clickup__` | — | — |
| Figma | `mcp__claude_ai_Figma__` | — | — |

## Multi-Environment Details

| System | How to Enumerate | How to Search Each |
|--------|-----------------|-------------------|
| Sanity | `list_datasets` | `query_documents` with dataset param |
| Stripe | Check key prefix: `sk_test_` vs `sk_live_` | `get_stripe_account_info` |
| GoHighLevel | Check `GHL_LOCATION_ID` in env | Each location needs separate API key |
| GitHub | `git branch -a` | Search per-branch or use `--all` |
| Sentry | `find_projects` lists all | Specify project in search |
| Netlify | `netlify-deploy-services-reader` | Filter by `published` status |
