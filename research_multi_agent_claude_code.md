# Multi-Agent Claude Code Systems: Community Patterns, Tools, and Real-World Findings

**Research Date:** March 29, 2026
**Sources:** 40+ across GitHub, blog posts, official docs, Substack, Medium, dev.to, and engineering blogs

---

## Table of Contents

1. [Official Architecture: How Claude Code Multi-Agent Works](#1-official-architecture)
2. [GitHub Repositories with Multi-Agent Setups](#2-github-repositories)
3. [Blog Posts and Deep Dives](#3-blog-posts-and-deep-dives)
4. [Patterns for Specialized Agents](#4-patterns-for-specialized-agents)
5. [Structuring ~/.claude/commands/ for Agent Orchestration](#5-structuring-claude-commands)
6. [Comparisons with Other Frameworks](#6-comparisons-with-other-frameworks)
7. [Limitations and Gotchas](#7-limitations-and-gotchas)
8. [Key Takeaways](#8-key-takeaways)

---

## 1. Official Architecture

Claude Code provides three tiers of multi-agent capability, each with different coordination primitives:

### Tier 1: Subagents (Task Tool)

Subagents are the simplest pattern. A parent agent spawns focused child agents via the `Task` tool (renamed to `Agent` tool in v2.1.63). Each runs in its own context window with a custom system prompt, specific tool access, and independent permissions.

- **Communication:** Report results back to parent only. No peer-to-peer messaging.
- **Context:** Own window. Only the summary returns to the parent.
- **Best for:** Focused tasks where only the result matters -- code review, test execution, codebase exploration.
- **Token cost:** Lower, since results are summarized back.
- **Limitation:** Cannot spawn other subagents (no nesting).

Subagents are defined as Markdown files with YAML frontmatter in `.claude/agents/` (project) or `~/.claude/agents/` (user). Key frontmatter fields include `name`, `description`, `tools`, `disallowedTools`, `model`, `permissionMode`, `memory`, `hooks`, `skills`, `isolation`, `maxTurns`, and `mcpServers`.

**Source:** [Claude Code Subagents Docs](https://code.claude.com/docs/en/sub-agents)

### Tier 2: Agent Teams

Agent Teams add true coordination primitives on top of subagents. One session acts as team lead; teammates work in parallel with:

- **Shared task list** with dependency tracking and automatic unblocking
- **Peer-to-peer messaging** between teammates (not just back to lead)
- **File locking** to prevent race conditions on task claims
- **Display modes:** In-process (single terminal, Shift+Down to cycle) or split-pane (tmux/iTerm2)

Enable with: `"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"` in settings.json. Requires Claude Code v2.1.32+.

**Source:** [Claude Code Agent Teams Docs](https://code.claude.com/docs/en/agent-teams)

### Tier 3: Cloud Orchestrators

External tools running agents in cloud VMs for 5-20+ parallel agents across repos. Examples include Gas Town ("Kubernetes for AI agents"), Multiclaude (Brownian ratchet philosophy with auto-PR-merging), and hosted platforms.

**Source:** [Shipyard: Multi-agent orchestration for Claude Code in 2026](https://shipyard.build/blog/claude-code-multi-agent/)

---

## 2. GitHub Repositories

### Major Multi-Agent Repos

| Repository | Stars/Scale | What It Provides |
|---|---|---|
| [wshobson/agents](https://github.com/wshobson/agents) | 112 agents, 16 workflows, 146 skills, 79 tools | Production-ready multi-agent system organized as 72 focused plugins. Three-tier model strategy: Opus for architecture/security, Inherit for complex tasks, Sonnet for support, Haiku for fast ops. Install via `/plugin marketplace add wshobson/agents`. |
| [wshobson/commands](https://github.com/wshobson/commands) | 57 commands (15 workflows, 42 tools) | Clone directly into `~/.claude/commands/`. Invoked via directory prefix (`/workflows:feature-development`, `/tools:security-scan`). |
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | Curated list | Comprehensive index of skills, hooks, slash commands, agent orchestrators, applications, and plugins. Covers Subagent Orchestration, Progressive Skills, Parallel Tool Calling, Master-Clone Architecture patterns. |
| [Yeachan-Heo/oh-my-claudecode](https://github.com/yeachan-heo/oh-my-claudecode) | Teams-first orchestration | Zero-config orchestration layer with 19 specialized agents and 28 skills. Claims 3-5x speedup and 30-50% token cost reduction. Team is the canonical orchestration surface since v4.1.7. |
| [ruvnet/ruflo](https://github.com/ruvnet/ruflo) | Orchestration platform | Multi-agent swarm deployment with self-learning, vector-based multi-layered memory, systematic planning, and security guardrails. Native Claude Code / Codex integration. |
| [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | 100+ subagents | Collection of specialized subagents covering wide range of development use cases. |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | 1000+ skills | Compatible with Codex, Antigravity, Gemini CLI, Cursor, and others. |
| [rohitg00/awesome-claude-code-toolkit](https://github.com/rohitg00/awesome-claude-code-toolkit) | Comprehensive toolkit | 135 agents, 35 curated skills (+400K via SkillKit), 42 commands, 150+ plugins, 19 hooks, 15 rules, 7 templates, 8 MCP configs. |
| [shinpr/claude-code-workflows](https://github.com/shinpr/claude-code-workflows) | Workflow library | Production-ready development workflows powered by specialized AI agents. |
| [qdhenry/Claude-Command-Suite](https://github.com/qdhenry/Claude-Command-Suite) | Professional commands | Structured workflows for code review, feature creation, security auditing, and architectural analysis. |
| [feiskyer/claude-code-settings](https://github.com/feiskyer/claude-code-settings) | Settings collection | Claude Code settings, commands, and agents for vibe coding. |
| [FlorianBruniaux/claude-code-ultimate-guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide) | Guide repo | Comprehensive guide including agent teams workflows. |
| [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) | Reference repo | Includes AGENTS.md example for multi-agent coordination. |

### Swarm Orchestration Gist

[kieranklaassen/swarm-orchestration-skill](https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea) -- Complete guide to multi-agent coordination with TeammateTool, Task system, and all five patterns (Parallel Specialists, Pipeline, Swarm, Research+Implementation, Plan Approval).

---

## 3. Blog Posts and Deep Dives

### Anthropic Engineering: Building a C Compiler with 16 Parallel Claudes

The definitive case study. 16 Claude Opus 4.6 instances across ~2,000 sessions over two weeks. 2 billion input tokens, 140 million output tokens, ~$20,000. Produced 100,000 lines of Rust capable of building Linux 6.9 on x86, ARM, and RISC-V.

**Key architecture decisions:**
- Each agent in its own Docker container with shared Git repo
- Task locking via files in `current_tasks/` directory -- Git merge conflicts prevented duplicate claims
- Agent loop: pull upstream, merge, push, remove locks, spawn next session
- GCC used as "known-good compiler oracle" to parallelize debugging of monolithic tasks
- No inter-agent communication beyond Git -- "very early research prototype"

**Key lessons:**
- Test quality is the foundation: "Claude will solve whatever problem I give it, so the verifier must be nearly perfect"
- New features frequently broke existing functionality -- approaching capability ceiling for autonomous development
- Human-in-the-loop catches errors that tests miss; autonomous "tests pass" != "job is done"

**Source:** [Anthropic Engineering Blog](https://www.anthropic.com/engineering/building-c-compiler)

### Addy Osmani: The Code Agent Orchestra

Google Chrome engineering lead's analysis of why multi-agent coding works:

- **Three focused agents consistently outperform one generalist working 3x as long**
- Four compounding benefits: parallelism (3x throughput), specialization (focused context), isolation (git worktrees), compound learning (AGENTS.md accumulates patterns)
- Quality gates are critical: plan approval before implementation, hooks on lifecycle events, human-curated AGENTS.md (machine-written versions reduce success ~3%)
- Ralph Loop pattern: Pick task, Implement, Validate, Commit, Reset context -- stateless iterations avoid confusion accumulation
- "The bottleneck has shifted from code generation to verification"
- Multi-model routing cuts costs: planning on cheaper models, implementation on Opus/Sonnet

**Source:** [AddyOsmani.com](https://addyosmani.com/blog/code-agent-orchestra/)

### HAMY: 9 Parallel AI Agents That Review My Code

Practical subagent-based code review setup with 9 specialized reviewers:

1. Test Runner
2. Linter & Static Analysis
3. Code Reviewer (5 ranked improvements by impact/effort)
4. Security Reviewer
5. Quality & Style Reviewer
6. Test Quality Reviewer
7. Performance Reviewer
8. Dependency & Deployment Safety Reviewer
9. Simplification & Maintainability Reviewer

All 9 launch simultaneously via Task tool. Results synthesize into a prioritized verdict: Ready to Merge, Needs Attention, or Needs Work. Reports ~75% useful suggestion rate vs <50% with single-agent review.

**Source:** [hamy.xyz](https://hamy.xyz/blog/2026-02_code-reviews-claude-subagents)

### John Kim: 30 Tips for Claude Code Agent Teams

Practical operational tips from the "Push to Prod" newsletter:

- Start with 3 teammates (more feels like overkill for most tasks)
- 5-6 tasks per teammate is the sweet spot
- Assign different models per teammate: debugger on Opus, UI perf on Sonnet, UX quality on Haiku
- Teammates don't inherit conversation history -- embed context in task descriptions
- Require planning before implementation to avoid token waste
- Parallel code review with "bias isolation" is the killer use case -- separate agents for security, performance, and test coverage investigate independently with fresh eyes
- Always clean up through the lead agent, never kill agents manually

**Source:** [Push to Prod Substack](https://getpushtoprod.substack.com/p/30-tips-for-claude-code-agent-teams)

### Ilyas Ibrahim: Solving Context Amnesia

Deep practical account of iterating through three architectures:

- **Attempt 1 (26 separate agents):** Massive context overhead from redundant protocol loading
- **Attempt 2 (8 coordinators with sub-agents):** Confusion about auto-invoke triggers, doubling workload with 850+ lines per invocation
- **Final (flat 22-agent design):** Single main agent handles coordination, 22 specialized agents receive complete context in task prompts, Agent-Memory-Protocol (370 lines) invoked only by main agent

**Results:** Context window went from 15-20 minutes to 2+ hours. 67% reduction in protocol length. 73% average reduction across all agent definitions. Key insight: "Context availability -- not automation -- was the constraint."

**Source:** [Medium](https://medium.com/@ilyas.ibrahim/how-i-made-claude-code-agents-coordinate-100-and-solved-context-amnesia-5938890ea825)

### Anthropic: Claude Code Review (Official)

Anthropic's own production review system running on nearly every internal PR:

- Fleet of specialized agents examine changes in full codebase context
- Five independent reviewers: CLAUDE.md compliance, bug detection, git history analysis, previous PR comment review, code comment verification
- On large PRs (1000+ lines): 84% get findings averaging 7.5 issues
- On small PRs (<50 lines): 31% get findings averaging 0.5 issues
- Less than 1% of findings marked incorrect by engineers

**Source:** [Claude Blog: Code Review](https://claude.com/blog/code-review)

### Additional Notable Posts

| Post | Source | Key Insight |
|---|---|---|
| [Heeki Park: Collaborating with Agent Teams](https://heeki.medium.com/collaborating-with-agents-teams-in-claude-code-f64a465f3c11) | Medium | Real-world walkthrough of setting up and running agent teams |
| [Addy Osmani: Conductors to Orchestrators](https://addyosmani.com/blog/future-agentic-coding/) | AddyOsmani.com | The evolution from single-agent to multi-agent coding paradigms |
| [Addy Osmani: Claude Code Swarms](https://addyosmani.com/blog/claude-code-agent-teams/) | AddyOsmani.com | Deep dive on swarm patterns |
| [PubNub: Best Practices for Subagents](https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/) | PubNub Blog | Practical subagent design patterns |
| [CLI Agents Part 2: Claude Code Best Practices](https://vld-bc.com/blog/cli-agents-part2-claude-code-best-practices) | VLD Blog | Context management, permission modes, CLAUDE.md tips |
| [Task Tool vs Subagents](https://www.ibuildwith.ai/blog/task-tool-vs-subagents-how-agents-work-in-claude-code/) | iBuildWith.ai | Comparison of Task tool and subagent patterns |
| [Sub-agent vs Agent Team in 60 Seconds](https://medium.com/data-science-collective/sub-agent-vs-agent-team-in-claude-code-pick-the-right-pattern-in-60-seconds-e856e5b4e5cc) | Medium | Quick decision framework |
| [From Tasks to Swarms](https://alexop.dev/posts/from-tasks-to-swarms-agent-teams-in-claude-code/) | alexop.dev | Evolution of agent patterns |

---

## 4. Patterns for Specialized Agents

### Architecture Review Agent

```yaml
---
name: architecture-reviewer
description: Reviews architectural decisions and system design
tools: Read, Grep, Glob
model: sonnet
memory: project
---

You are a senior software architect. Analyze system design for:
- Component coupling and cohesion
- Dependency direction violations
- Scalability bottlenecks
- API contract consistency
- Data flow patterns

Consult your memory for project-specific patterns before starting.
```

### Code Review Agent (from Anthropic's production system)

Five parallel reviewers with distinct lenses:
1. **CLAUDE.md compliance checker** -- verifies code follows project-specific rules
2. **Bug detector** -- logic errors, security vulnerabilities, edge cases, regressions
3. **Git history analyzer** -- checks changes against recent commit patterns
4. **PR comment reviewer** -- ensures previous review feedback was addressed
5. **Code comment verifier** -- validates documentation accuracy

### PRD Q&A / Requirements Agent

```yaml
---
name: requirements-analyst
description: Analyzes PRDs and requirements for completeness and ambiguity
tools: Read, Grep, Glob, WebFetch
model: inherit
---

You are a requirements analyst. When given a PRD or spec:
1. Identify ambiguous requirements
2. Flag missing acceptance criteria
3. Check for conflicting requirements
4. Verify testability of each requirement
5. Suggest edge cases not covered
```

### Testing Agent Pattern

```yaml
---
name: test-architect
description: Designs and reviews test strategies
tools: Read, Edit, Bash, Grep, Glob
model: sonnet
hooks:
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/run-tests.sh"
---

You are a test architect. Focus on:
- Coverage gaps in critical paths
- Missing edge case tests
- Test isolation and independence
- Performance test opportunities
- Integration test completeness
```

### Multi-Review Orchestration Pattern (from HAMY's 9-agent setup)

The parent agent spawns 9 specialized reviewers simultaneously:
- Each reviewer has a single focus area (security, performance, test quality, etc.)
- All run in parallel via background Task tool calls
- Results synthesize into a prioritized verdict with severity rankings
- Placed in `.claude/commands/code-review.md` for `/code-review` slash command access

### Competing Hypotheses Pattern (from Agent Teams docs)

```
Spawn 5 agent teammates to investigate different hypotheses about [bug].
Have them talk to each other to try to disprove each other's theories,
like a scientific debate. Update the findings doc with whatever consensus emerges.
```

This prevents anchoring bias where sequential investigation gets biased by the first plausible explanation found.

---

## 5. Structuring ~/.claude/commands/ for Agent Orchestration

### Directory Structure (from community patterns)

```
~/.claude/
├── agents/                          # User-scope subagent definitions
│   ├── code-reviewer.md
│   ├── debugger.md
│   ├── architecture-reviewer.md
│   ├── security-scanner.md
│   ├── test-architect.md
│   └── data-scientist.md
├── agent-memory/                    # Persistent memory per agent
│   ├── code-reviewer/
│   │   └── MEMORY.md
│   └── architecture-reviewer/
│       └── MEMORY.md
├── commands/                        # Slash commands (now merged with skills)
│   ├── tools/                       # Single-purpose utilities
│   │   ├── code-review.md           # /tools:code-review
│   │   ├── security-scan.md
│   │   ├── test-harness.md
│   │   └── refactor-clean.md
│   └── workflows/                   # Multi-agent orchestration
│       ├── feature-development.md   # /workflows:feature-development
│       ├── full-review.md           # /workflows:full-review
│       ├── tdd-cycle.md
│       └── smart-fix.md
├── skills/                          # Progressive disclosure skills
│   ├── api-conventions/
│   │   └── SKILL.md
│   └── agent-memory-protocol/
│       └── SKILL.md
└── settings.json                    # Global settings
```

### Key Conventions

1. **Directory prefixes as namespaces:** Commands in `tools/` are invoked as `/tools:command-name`, workflows as `/workflows:workflow-name`
2. **Skills and commands are now equivalent:** A file at `.claude/commands/review.md` and `.claude/skills/review/SKILL.md` both create `/review`
3. **Agents are separate from commands:** Agent definitions go in `.claude/agents/`, not commands
4. **Progressive disclosure for skills:** Three tiers -- metadata always loaded, instructions on activation, resources on demand. Minimizes token overhead.
5. **Plugin architecture:** Install curated collections via `/plugin marketplace add wshobson/agents` rather than maintaining everything manually

### The wshobson/agents Model (72 plugins, 112 agents)

This is the most comprehensive community setup:
- Single-responsibility plugins averaging 3.4 components each
- Install only what you need: `/plugin install python-development`
- Four-tier model strategy across agents (Opus for critical, Inherit for complex, Sonnet for support, Haiku for fast)
- Conductor workflow for structured project execution

**Source:** [wshobson/agents](https://github.com/wshobson/agents)

---

## 6. Comparisons with Other Frameworks

### Claude Code Agent Teams vs. Other Multi-Agent Frameworks

| Dimension | Claude Code (Agent Teams/Subagents) | LangGraph | CrewAI | OpenAI Agents SDK (Codex) |
|---|---|---|---|---|
| **Architecture** | Tool-use-first; agents are Claude models with tools, including sub-agent tools | Graph-based state machines with persistence and checkpointing | Role-based crews with task assignment | Tool-use agents with handoffs; cloud sandbox isolation |
| **Multi-agent coordination** | Shared task list, peer messaging, dependency tracking | Explicit graph edges, conditional routing | Hierarchical process with crew manager | No inter-agent messaging; isolated sandbox per task |
| **Model lock-in** | Claude only (Opus, Sonnet, Haiku) | Model-agnostic | Model-agnostic | OpenAI only |
| **Context handling** | 1M tokens; each agent gets own window | Checkpointing; configurable memory | Shared crew memory | 400K tokens; diff-based forgetting |
| **Persistence** | Team config in `~/.claude/teams/`, tasks in `~/.claude/tasks/` | LangSmith observability, full state checkpoints | Mission memory across runs | Cloud sandbox state per task |
| **Production maturity** | Experimental (requires env var) | Highest production readiness | Largest community, broadest protocol support | Open-source CLI, 365 contributors |
| **Best for** | Complex refactoring, large codebase analysis, coordinated multi-file changes | Complex stateful orchestration | Rapid multi-agent prototyping | Background autonomous tasks, test generation |
| **Typical cost** | ~$200/mo (Max plan); high token consumption | Depends on model provider | Depends on model provider | $20/mo + ACU costs |

### Claude Code vs. Cursor vs. Codex vs. Devin

| Tool | Approach | Multi-Agent | Context Window | Strength |
|---|---|---|---|---|
| **Claude Code** | Terminal-native assistant | Agent Teams (coordinated parallel) | 1M tokens | Complex refactoring, architectural decisions |
| **Cursor** | AI-native IDE | Composer multi-file editing | IDE-scoped | Daily coding productivity, visual diffs |
| **Codex** | Cloud autonomous agent | Isolated sandbox per task | 400K tokens | Background work, async PR generation |
| **Devin** | Fully autonomous | Parallel sessions | Full environment | Complete task delegation, hands-off |

Key tradeoff: "Isolated speed with generous limits (Codex) versus orchestrated depth with tighter constraints (Claude Code)."

In February 2026, every major tool shipped multi-agent in the same two-week window: Grok Build (8 agents), Windsurf (5 parallel agents), Claude Code Agent Teams, Codex CLI (Agents SDK), Devin (parallel sessions).

**Sources:**
- [Codex vs Claude Code 2026](https://www.morphllm.com/comparisons/codex-vs-claude-code)
- [Bridge ACE vs Claude Code vs Cursor vs Windsurf vs Devin](https://dev.to/bridgeace/bridge-ace-vs-claude-code-vs-cursor-vs-windsurf-vs-devin-an-honest-comparison-march-2026-1de0)
- [Best Multi-Agent Frameworks 2026](https://gurusup.com/blog/best-multi-agent-frameworks-2026)

---

## 7. Limitations and Gotchas

### Context Window Constraints

- **Effective context is smaller than advertised.** With 200K tokens, system prompt + tools + autocompact buffer consume ~67K, leaving ~133K for actual work. On a 50K+ line codebase, a single agent fills 80-90% of context just loading files.
- **Auto-compaction loses nuance.** When approaching limits, Claude auto-runs `/compact` which summarizes but loses important details. Multiple practitioners recommend starting fresh conversations rather than letting context rot.
- **Machine-written AGENTS.md/CLAUDE.md reduces success ~3%.** Human-curated context files consistently outperform LLM-generated ones.

### Agent Teams Specific Issues

- **No session resumption for in-process teammates.** `/resume` and `/rewind` don't restore teammates. After resuming, the lead may message non-existent agents.
- **Task status can lag.** Teammates sometimes fail to mark tasks complete, blocking dependents. May need manual intervention.
- **Shutdown is slow.** Teammates finish current request before shutting down.
- **One team per session.** Must clean up before starting a new team.
- **No nested teams.** Teammates cannot spawn their own teams.
- **Lead is fixed.** Cannot promote a teammate or transfer leadership.
- **All teammates share lead's permission mode at spawn.** Can change individually after, but not at spawn time.
- **Split panes require tmux or iTerm2.** Not supported in VS Code integrated terminal, Windows Terminal, or Ghostty.
- **All agents run the same model (as of March 2026).** Community has requested role-based model selection (Opus for lead, cheaper models for workers) but this is not yet natively supported in Agent Teams. Subagents do support per-agent model selection.

### Token and Cost Gotchas

- **Token costs scale linearly with team size.** Each teammate has its own context window.
- **Claude Code consumes 3.2-4.2x more tokens than Codex on identical tasks.** Higher thoroughness comes at a cost.
- **Set per-agent token limits.** Pause at 85% threshold to prevent runaway spending.
- **Multi-agent is expensive and experimental.** Applicable to only ~5% of agent-assisted development tasks per Shipyard's analysis.

### Coordination Challenges

- **File conflicts are the #1 failure mode.** Two teammates editing the same file leads to overwrites. Must strictly separate file ownership.
- **Coordination overhead increases non-linearly.** Beyond 5 teammates, diminishing returns. Three focused teammates often outperform five scattered ones.
- **Lead may start implementing instead of delegating.** Must explicitly tell it to wait for teammates.
- **Teammates don't inherit conversation history.** Must embed all needed context in spawn prompts.
- **Flaky environments compound across parallel agents.** Problems that occur 5% of the time in a single agent occur frequently when running 10+ agents.

### Quality and Reliability

- **"Tests pass" does not mean "job is done."** Anthropic's C compiler experiment confirmed: new features frequently broke existing functionality.
- **Loop exhaustion.** Agents need reflection prompts and kill criteria (3+ stuck iterations should trigger reassignment).
- **Vague requirements multiply errors across parallel teams.** Precise specs multiply precise implementations.
- **Third-party orchestration tools are "vibe-coded."** Carry inherent bugs and potential security vulnerabilities.

---

## 8. Key Takeaways

### When to Use Multi-Agent

1. **Research and review** (parallel investigation from different angles)
2. **New modules/features** (each agent owns a separate piece)
3. **Debugging with competing hypotheses** (test theories in parallel)
4. **Cross-layer coordination** (frontend/backend/tests each owned by different agent)
5. **Large codebase analysis** (split context across agents to keep each at ~40% utilization)

### When NOT to Use Multi-Agent

1. Sequential tasks with heavy dependencies
2. Same-file edits
3. Quick, targeted changes
4. When latency matters (agents need time to gather context)
5. Routine tasks where a single session suffices

### Decision Framework

```
Need quick results?              --> Single subagent
Need collaboration/coordination? --> Agent Team
Need 5+ parallel agents?         --> External orchestrator (Gas Town, Multiclaude)
Need isolated background work?   --> Codex/sandbox approach
```

### The Two-Step Pattern (Most Recommended)

1. **Plan first** using plan mode in a single session
2. **Hand the plan to a team** for parallel execution

This prevents the most common failure mode: agents going off in random directions and wasting tokens.

### Cost-Optimization Strategy

- Route planning to cheaper models (Haiku/Sonnet)
- Route implementation to Opus/Sonnet
- Route review to specialized security/performance models
- Set per-agent limits, pause at 85% threshold
- Use subagents for isolated tasks, teams only for tasks requiring coordination

---

## Source Index

### Official Documentation
- [Claude Code Agent Teams](https://code.claude.com/docs/en/agent-teams)
- [Claude Code Subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code Review](https://claude.com/blog/code-review)

### Engineering Case Studies
- [Anthropic: Building a C Compiler with Parallel Claudes](https://www.anthropic.com/engineering/building-c-compiler)

### Blog Posts & Analysis
- [Addy Osmani: The Code Agent Orchestra](https://addyosmani.com/blog/code-agent-orchestra/)
- [Addy Osmani: Conductors to Orchestrators](https://addyosmani.com/blog/future-agentic-coding/)
- [Addy Osmani: Claude Code Swarms](https://addyosmani.com/blog/claude-code-agent-teams/)
- [HAMY: 9 Parallel AI Agents That Review My Code](https://hamy.xyz/blog/2026-02_code-reviews-claude-subagents)
- [John Kim: 30 Tips for Agent Teams](https://getpushtoprod.substack.com/p/30-tips-for-claude-code-agent-teams)
- [Ilyas Ibrahim: Solving Context Amnesia](https://medium.com/@ilyas.ibrahim/how-i-made-claude-code-agents-coordinate-100-and-solved-context-amnesia-5938890ea825)
- [Shipyard: Multi-agent Orchestration 2026](https://shipyard.build/blog/claude-code-multi-agent/)
- [HumanLayer: Writing a Good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [Complete Guide to Agent Memory Files](https://medium.com/data-science-collective/the-complete-guide-to-ai-agent-memory-files-claude-md-agents-md-and-beyond-49ea0df5c5a9)
- [CLI Agents Part 2: Claude Code Best Practices](https://vld-bc.com/blog/cli-agents-part2-claude-code-best-practices)
- [Heeki Park: Collaborating with Agent Teams](https://heeki.medium.com/collaborating-with-agents-teams-in-claude-code-f64a465f3c11)
- [Task Tool vs Subagents](https://www.ibuildwith.ai/blog/task-tool-vs-subagents-how-agents-work-in-claude-code/)
- [Codex vs Claude Code Comparison](https://www.morphllm.com/comparisons/codex-vs-claude-code)
- [The Task Tool: Agent Orchestration System](https://dev.to/bhaidar/the-task-tool-claude-codes-agent-orchestration-system-4bf2)
- [PubNub: Best Practices for Subagents](https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/)

### GitHub Repositories
- [wshobson/agents](https://github.com/wshobson/agents) -- 112 agents, 72 plugins
- [wshobson/commands](https://github.com/wshobson/commands) -- 57 slash commands
- [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) -- Curated resource list
- [Yeachan-Heo/oh-my-claudecode](https://github.com/yeachan-heo/oh-my-claudecode) -- Teams-first orchestration
- [ruvnet/ruflo](https://github.com/ruvnet/ruflo) -- Swarm orchestration platform
- [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) -- 100+ subagents
- [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) -- 1000+ agent skills
- [rohitg00/awesome-claude-code-toolkit](https://github.com/rohitg00/awesome-claude-code-toolkit) -- Comprehensive toolkit
- [shinpr/claude-code-workflows](https://github.com/shinpr/claude-code-workflows) -- Production workflows
- [qdhenry/Claude-Command-Suite](https://github.com/qdhenry/Claude-Command-Suite) -- Professional slash commands
- [feiskyer/claude-code-settings](https://github.com/feiskyer/claude-code-settings) -- Settings and agents
- [FlorianBruniaux/claude-code-ultimate-guide](https://github.com/FlorianBruniaux/claude-code-ultimate-guide) -- Ultimate guide
- [kieranklaassen/swarm-orchestration-skill (Gist)](https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea) -- Swarm patterns reference

### Comparisons & Market Analysis
- [Bridge ACE vs Claude Code vs Cursor vs Windsurf vs Devin](https://dev.to/bridgeace/bridge-ace-vs-claude-code-vs-cursor-vs-windsurf-vs-devin-an-honest-comparison-march-2026-1de0)
- [Best Multi-Agent Frameworks 2026](https://gurusup.com/blog/best-multi-agent-frameworks-2026)
- [Codex vs Cursor vs Claude Code 2026](https://www.nxcode.io/resources/news/codex-vs-cursor-vs-claude-code-2026)
- [We Tested 15 AI Coding Agents 2026](https://www.morphllm.com/ai-coding-agent)
