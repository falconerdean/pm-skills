# Phase 2: Product Research & User Discovery

## CRITICAL: REAL RESEARCH WITH REAL DATA

You are conducting real market and user research. Use the MCP tools to gather actual data
from actual sources. Do NOT fabricate personas, invent user quotes, or write hypothetical
research findings. Every claim in your output must trace to a real source you actually queried.

## Input
- Read sprint plan: {workspace}/state/sprint_plan.json
- Read latest intel: {workspace}/intel/ (most recent competitive and market reports)

## Process

### Step 1: User Research
Use /deep-research to investigate: "{epic_description} user needs pain points behaviors current solutions"

This must produce real findings from real web sources — not hypothetical scenarios.

### Step 2: Competitive Deep Dive
Use the following Bright Data MCP tools IN PARALLEL:
- mcp__Bright_Data__web_data_reddit_posts: Search for real user discussions about the problem space
- mcp__Bright_Data__web_data_youtube_comments: Find real user feedback on competing products
- mcp__Bright_Data__scrape_as_markdown: Scrape top 3 competitor product/feature pages
- mcp__Bright_Data__web_data_crunchbase_company: Get real competitor funding/team data (if applicable)

### Step 3: Visual Competitive Audit
Use Chrome DevTools MCP:
- mcp__chrome-devtools__navigate_page: Visit top 3 competitor sites
- mcp__chrome-devtools__take_screenshot: Capture actual screenshots for reference

### Step 4: Synthesize Discovery Brief
Combine all research into a discovery brief:
- Problem statement grounded in real research data (cite source URLs)
- 2-3 user personas derived from actual user feedback (not invented)
- Competitive landscape based on real competitor data
- Recommended approach with evidence-based rationale

## Output
Write to {workspace}/artifacts/research/{epic}/:
- user_research.json (real findings with source URLs)
- competitive_analysis.json (real competitor data)
- screenshots/ (actual competitor screen captures)
- discovery_brief.md (synthesized brief citing real sources)

## State Update
Update {workspace}/state/company_state.json:
- Set `sdlc.phases.research.status` to `"complete"`
- Set `sdlc.phases.research.completed_at` to current UTC ISO timestamp (with Z suffix)
