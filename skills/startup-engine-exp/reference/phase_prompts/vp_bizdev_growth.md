# Phase 9: Growth & Content + Phase 0: Continuous Intelligence

## CRITICAL: REAL DATA, REAL CONTENT, REAL PUBLISHING

You are gathering real market data and publishing real content to real channels.
Use the Bright Data MCPs to scrape real competitor data. Use GoHighLevel MCPs to publish
real blog posts, real social media posts, real email campaigns. Do NOT write draft content
that sits in a markdown file — publish it through the actual platform APIs.

You have two modes of operation:

## Mode A: Continuous Intelligence (Phase 0 — runs on /loop 1d)

### Process
Run these Bright Data MCP tools IN PARALLEL to monitor the real market:

**Competitor Tracking:**
- mcp__Bright_Data__web_data_crunchbase_company: Check real competitor funding/growth
- mcp__Bright_Data__web_data_linkedin_job_listings: Monitor real competitor hiring
- mcp__Bright_Data__web_data_google_play_store: Track real app ratings and reviews
- mcp__Bright_Data__web_data_apple_app_store: Same for iOS

**Market Sentiment:**
- mcp__Bright_Data__web_data_reddit_posts: Real user discussions in relevant subreddits
- mcp__Bright_Data__web_data_x_posts: Real industry conversation and trends
- mcp__Bright_Data__search_engine: Track real search volume for key terms

**Weekly Deep Dive (every 7 days):**
- Use /deep-research for comprehensive market pulse report
- Use /tools:competitive-intel for structured competitor analysis

### Output
Write to {workspace}/intel/:
- competitive_report_{date}.md (real competitor data, not hypothetical)
- market_pulse_{date}.md (real market analysis from real sources)

---

## Mode B: Growth & Content (Phase 9 — post-deployment)

### Input
- Read: {workspace}/artifacts/deployments/{epic}/release_notes.md
- Read: {workspace}/artifacts/research/{epic}/discovery_brief.md (positioning context)
- Read: {workspace}/intel/ (latest market context)

### Process

#### Step 1: Launch Content — PUBLISH FOR REAL
Create and publish real announcement content using GoHighLevel MCP:
- mcp__GoHighLevel__blogs_create-blog-post: Write and **publish** a real blog post
- mcp__GoHighLevel__social-media-posting_create-post: Create and **post** real social media content
- mcp__GoHighLevel__emails_create-template: Create a real email campaign template

#### Step 2: CMS Updates
If product has a content-managed site:
- mcp__Sanity__get_schema: Check current content model
- mcp__Sanity__create_documents_from_markdown: Create real content documents
- mcp__Sanity__publish_documents: **Publish** the content (don't leave as drafts)

#### Step 3: Track Real Performance
- mcp__GoHighLevel__social-media-posting_get-social-media-statistics: Real engagement metrics
- mcp__GoHighLevel__contacts_get-contacts: Real new leads from launch
- mcp__GoHighLevel__opportunities_search-opportunity: Real pipeline impact
- mcp__GoHighLevel__payments_list-transactions: Real revenue impact (if applicable)

#### Step 4: Competitive Positioning
Use /tools:competitive-intel to update positioning based on real data:
- How does the new feature compare to real competitors?
- What messaging resonates based on real social engagement data?
- What's the next competitive gap to address?

### Output
Write to {workspace}/intel/growth/:
- launch_{epic}.md (launch content summary + real published URLs)
- engagement_{epic}.md (real performance metrics)
- positioning_{epic}.md (competitive positioning based on real data)

## State Update
Update {workspace}/state/company_state.json:
- Set `sdlc.phases.growth.status` to `"complete"`
- Set `sdlc.phases.growth.completed_at` to current UTC ISO timestamp (with Z suffix)
