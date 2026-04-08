# Multi-Model AI Orchestration from Claude Code

**Research Date:** 2026-04-06 UTC  
**Use Case:** Startup Engine skill spawns Claude sub-agents; we want to optionally farm out tasks to GPT-4o or Gemini for cost savings, speed, or capability diversity.  
**Confidence Rating:** HIGH — based on current official documentation, GitHub repos, and verified community patterns.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [LiteLLM — Unified API Proxy](#1-litellm--unified-api-proxy)
3. [OpenRouter — Managed Multi-Model Gateway](#2-openrouter--managed-multi-model-gateway)
4. [LiteLLM vs OpenRouter — Head-to-Head](#3-litellm-vs-openrouter--head-to-head)
5. [CrewAI — Multi-Agent Framework](#4-crewai--multi-agent-framework)
6. [AutoGen (Microsoft) — Multi-Agent Conversations](#5-autogen-microsoft--multi-agent-conversations)
7. [LangGraph — Stateful Agent Orchestration](#6-langgraph--stateful-agent-orchestration)
8. [Practical Patterns — Calling GPT/Gemini from Claude Code](#7-practical-patterns--calling-gptgemini-from-claude-code)
9. [Recommendation for Startup Engine](#8-recommendation-for-startup-engine)
10. [Sources](#sources)

---

## Executive Summary

There are three layers of approach for multi-model orchestration from within Claude Code:

| Layer | Approach | Complexity | Best For |
|-------|----------|-----------|----------|
| **Minimal** | Direct API calls via Python scripts in Bash | Low | One-off tasks, quick experiments |
| **Gateway** | LiteLLM (self-hosted) or OpenRouter (managed) | Medium | Unified billing, fallbacks, cost tracking |
| **Framework** | CrewAI, AutoGen, or LangGraph | High | Complex multi-agent workflows with state |

**Bottom line recommendation for the startup engine:** Use **LiteLLM as a Python library** (not the proxy server) for direct multi-model calls within sub-agent scripts. This gives you unified interface, fallbacks, budget caps, and token tracking with zero infrastructure overhead. Reserve OpenRouter as a fallback gateway if you want to avoid self-hosting entirely. Avoid full frameworks (CrewAI/AutoGen/LangGraph) unless you're replacing the entire agent orchestration layer — they conflict with Claude Code's native sub-agent spawning.

---

## 1. LiteLLM — Unified API Proxy

### How It Works

LiteLLM is an open-source Python library (and optional proxy server) that provides a single `completion()` interface for 100+ LLM providers. All calls use the OpenAI chat completions format regardless of the underlying provider.

**Architecture:** Library wraps provider SDKs → translates parameters → normalizes responses → maps errors to OpenAI exception types.

### Code Examples

#### Python (Direct Library — Recommended for Startup Engine)

```python
# pip install litellm
import litellm
import os

os.environ["OPENAI_API_KEY"] = "sk-..."
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."
os.environ["GEMINI_API_KEY"] = "..."

# Call GPT-4o
response = litellm.completion(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Review this code for security issues: ..."}],
    temperature=0.3,
    max_tokens=4000
)
print(response.choices[0].message.content)

# Call Claude — same interface
response = litellm.completion(
    model="claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": "Analyze this architecture: ..."}]
)

# Call Gemini — same interface
response = litellm.completion(
    model="gemini/gemini-2.5-flash",
    messages=[{"role": "user", "content": "Summarize this research: ..."}]
)
```

#### Streaming

```python
response = litellm.completion(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Stream this response"}],
    stream=True
)
for chunk in response:
    print(chunk.choices[0].delta.content or "", end="")
```

#### Fallback Chain

```python
from litellm import Router

model_list = [
    {
        "model_name": "fast-model",
        "litellm_params": {"model": "gpt-4o-mini", "api_key": os.environ["OPENAI_API_KEY"]},
        "model_info": {"id": "gpt-4o-mini-primary"}
    },
    {
        "model_name": "fast-model",
        "litellm_params": {"model": "gemini/gemini-2.5-flash", "api_key": os.environ["GEMINI_API_KEY"]},
        "model_info": {"id": "gemini-flash-fallback"}
    }
]

router = Router(
    model_list=model_list,
    num_retries=3,
    retry_after=5,
    allowed_fails=1,
    cooldown_time=60
)

# Automatically fails over from GPT-4o-mini to Gemini Flash
response = router.completion(
    model="fast-model",
    messages=[{"role": "user", "content": "Quick task here"}]
)
```

#### Budget Caps & Token Tracking

```python
from litellm import BudgetManager, completion

budget_manager = BudgetManager(project_name="startup-engine")

# Set per-phase budget
budget_manager.create_budget(total_budget=5.00, user="phase-7-testing", duration="daily")

if budget_manager.get_current_cost(user="phase-7-testing") <= budget_manager.get_total_budget("phase-7-testing"):
    response = completion(model="gpt-4o", messages=[...])
    budget_manager.update_cost(completion_obj=response, user="phase-7-testing")
else:
    print("Budget exceeded for this phase — falling back to cheaper model")
    response = completion(model="gpt-4o-mini", messages=[...])

# Global hard cap
litellm.max_budget = 50.0  # $50 total across all calls
```

#### TypeScript/JavaScript (via Proxy Server)

LiteLLM's Python proxy exposes an OpenAI-compatible endpoint. From TypeScript, use the standard OpenAI SDK:

```typescript
import OpenAI from 'openai';

// Point OpenAI SDK at LiteLLM proxy
const client = new OpenAI({
  apiKey: "anything",  // LiteLLM proxy handles auth
  baseURL: "http://localhost:4000"
});

const response = await client.chat.completions.create({
  model: "gpt-4o",  // LiteLLM routes to the right provider
  messages: [{ role: "user", content: "Hello" }]
});
```

There is also an npm package (`litellm`) providing a native JS `completion()` function, but the Python library is far more mature.

### Routing Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| simple-shuffle | Default. Distributes by RPM/TPM limits | Production load balancing |
| latency-based | Picks lowest response time | Real-time applications |
| usage-based | Routes to lowest TPM usage | Stay under rate limits |
| cost-based | Routes to cheapest available | Budget optimization |
| least-busy | Fewest concurrent calls | Even distribution |

### Error Handling

- Maps ALL provider errors to OpenAI exception types: `AuthenticationError`, `RateLimitError`, `APIError`
- Cooldown after failures: 429 errors → 5s cooldown; >50% failure rate → configurable cooldown
- Per-error-type retry policies (e.g., retry rate limits 3x, never retry auth errors)

### Pros for Startup Engine
- Zero infrastructure (use as Python library, not proxy)
- Same `completion()` call for Claude, GPT, Gemini — minimal code changes
- Built-in budget caps per user/phase/sprint
- Automatic fallbacks between providers
- Token cost tracking per request
- Open source, free (you pay only provider token costs)

### Cons
- Python-primary (TypeScript is second-class via proxy or thin npm wrapper)
- Proxy server adds operational complexity if you go that route
- Some advanced provider features (thinking tokens, extended context) may lag behind native SDKs

---

## 2. OpenRouter — Managed Multi-Model Gateway

### How It Works

OpenRouter is a managed SaaS API gateway providing access to 300+ AI models through a single OpenAI-compatible endpoint. You get one API key, one credit balance, and intelligent routing across all providers.

**Architecture:** Your app → OpenRouter API (`openrouter.ai/api/v1/chat/completions`) → Provider APIs (OpenAI, Anthropic, Google, etc.)

### Pricing Model

- **No markup** — pricing matches provider websites exactly
- Per-token billing (input and output priced separately)
- Pay-as-you-go with credit balance
- Zero completion insurance: no charge for failed/empty responses
- Model variants: `:free` (free tier), `:nitro` (high-speed), `:thinking` (extended reasoning)

### Code Examples

#### Python (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

# Call any model through one endpoint
response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "Review this code"}]
)

# Switch to Claude — just change the model string
response = client.chat.completions.create(
    model="anthropic/claude-sonnet-4",
    messages=[{"role": "user", "content": "Analyze this architecture"}]
)
```

#### Model Fallbacks

```python
response = client.chat.completions.create(
    model="anthropic/claude-sonnet-4",
    messages=[{"role": "user", "content": "Hello"}],
    extra_body={
        "models": [
            "anthropic/claude-sonnet-4",
            "openai/gpt-4o",
            "google/gemini-2.5-flash"
        ]  # Tries in order; billed only for the model that succeeds
    }
)
```

#### Provider Routing Controls

```python
response = client.chat.completions.create(
    model="meta-llama/llama-3.3-70b-instruct",
    messages=[{"role": "user", "content": "Hello"}],
    extra_body={
        "provider": {
            "sort": "throughput",           # Prioritize speed over cost
            "allow_fallbacks": True,
            "data_collection": "deny",      # Privacy: no data retention
            "max_price": {"prompt": 0.01, "completion": 0.03}  # Per-token caps
        }
    }
)
```

#### TypeScript (Native SDK)

```typescript
import OpenRouter from '@openrouter/sdk';

const openRouter = new OpenRouter({ apiKey: process.env.OPENROUTER_API_KEY });

const completion = await openRouter.chat.send({
  model: 'openai/gpt-4o',
  messages: [{ role: 'user', content: 'Hello' }],
});

// With fallbacks
const completion = await openRouter.chat.send({
  models: ['anthropic/claude-sonnet-4', 'openai/gpt-4o'],
  messages: [{ role: 'user', content: 'Hello' }],
});
```

### Budget Controls

- Credit-based system with spending limits per API key
- Guardrails: set spending limits, restrict model access per team member
- Service tiers for cost/latency tradeoffs
- Per-request `max_price` parameter

### Pros for Startup Engine
- Zero infrastructure — fully managed
- 300+ models through one API key
- Built-in fallbacks with transparent billing (pay only for successful model)
- OpenAI SDK compatible — minimal code changes
- Auto Router selects best model for each prompt automatically
- Free model tier available for non-critical tasks

### Cons
- Third-party dependency (if OpenRouter goes down, all model access stops)
- Less control over routing logic vs self-hosted LiteLLM
- Adds network hop (typically ~25ms latency overhead)
- Budget controls less granular than LiteLLM's per-user/per-phase system
- Credit system requires prepayment

---

## 3. LiteLLM vs OpenRouter — Head-to-Head

| Dimension | LiteLLM | OpenRouter |
|-----------|---------|------------|
| **Deployment** | Self-hosted (library or proxy) | Managed SaaS |
| **Models** | 100+ via provider SDKs | 300+ via gateway |
| **Pricing** | Free (pay provider rates) | No markup (pay provider rates) |
| **Markup** | None | None |
| **Fallbacks** | Router class with configurable strategies | `models` array in request |
| **Budget** | Per-user/per-phase BudgetManager | Per-key spending limits |
| **Token tracking** | Built-in per-request cost tracking | Dashboard analytics |
| **Latency overhead** | None (direct to provider) | ~25ms network hop |
| **Infrastructure** | None (library) or your server (proxy) | None (SaaS) |
| **Customization** | Full control (routing, caching, Redis, webhooks) | Limited to API parameters |
| **Single point of failure** | Your infra (if using proxy) | OpenRouter's infra |
| **Open source** | Yes (MIT) | No |
| **Best for** | Platform teams needing control | Teams wanting zero ops |

**Verdict for Startup Engine:** Use LiteLLM as a Python library. It gives the startup engine budget tracking per phase, fallback chains, and zero infrastructure overhead — just `pip install litellm` and call `completion()`. If you later need a shared gateway for multiple projects, stand up the LiteLLM proxy or switch to OpenRouter.

---

## 4. CrewAI — Multi-Agent Framework

### How It Works

CrewAI is a Python framework for building collaborative multi-agent systems. A "crew" orchestrates multiple "agents," each with their own role, tools, memory, and — critically — their own LLM model.

**Architecture:** Crew (orchestrator) → Agents (each with an LLM) → Tasks (sequential or hierarchical) → Output pipeline

### Multi-Model Configuration

Each agent can use a different LLM provider. This is a first-class feature:

```python
from crewai import Agent, Task, Crew, LLM, Process

# Configure different models for different roles
fast_llm = LLM(model="openai/gpt-4o-mini", temperature=0.3)
powerful_llm = LLM(model="anthropic/claude-sonnet-4", temperature=0.5, max_tokens=4096)
reasoning_llm = LLM(model="openai/o3-mini")
cheap_llm = LLM(model="gemini/gemini-2.5-flash")

# Each agent gets the right model for its job
code_reviewer = Agent(
    role="Senior Code Reviewer",
    goal="Find bugs and security issues in code",
    backstory="20 years of security engineering experience",
    llm=powerful_llm,
    max_iter=20,
    max_retry_limit=2
)

test_writer = Agent(
    role="Test Engineer",
    goal="Write comprehensive test suites",
    backstory="Expert in TDD and property-based testing",
    llm=fast_llm  # Cheaper model for structured, repeatable tasks
)

architect = Agent(
    role="System Architect",
    goal="Design scalable system architectures",
    backstory="Built systems handling 10M+ requests/day",
    llm=reasoning_llm  # Reasoning model for complex design decisions
)

summarizer = Agent(
    role="Documentation Writer",
    goal="Summarize technical decisions clearly",
    llm=cheap_llm  # Cheapest model for writing summaries
)

# Orchestrate
crew = Crew(
    agents=[architect, code_reviewer, test_writer, summarizer],
    tasks=[design_task, review_task, test_task, doc_task],
    process=Process.sequential  # or Process.hierarchical
)

result = crew.kickoff(inputs={"codebase": "..."})
```

### Supported Providers (Native SDK)

- OpenAI (GPT-4o, GPT-4o-mini, o1, o3-mini)
- Anthropic (Claude 3.5 Sonnet, Claude Opus)
- Google Gemini (2.5-flash, 2.0-flash)
- Azure OpenAI & Azure AI Inference
- AWS Bedrock
- 30+ additional providers via LiteLLM integration

### State Management

- **Between agents:** Task outputs flow through the crew's execution pipeline. Each task's output becomes context for the next.
- **Memory:** Agents maintain interaction history when `memory=True`. Auto-summarizes when approaching context window limits.
- **Structured output:** Pydantic models enforce typed data between agents.
- **CrewOutput:** Encapsulates raw string, JSON, Pydantic responses, individual task outputs, and token usage metrics.

### Iteration & Convergence Controls

- `max_iter`: Max iterations per agent (default: 20)
- `max_execution_time`: Timeout in seconds per agent
- `max_rpm`: Rate limiting for API calls per agent
- `max_retry_limit`: Error retries (default: 2)
- `respect_context_window=True`: Auto-summarizes when tokens run low
- Process types: `sequential` (linear) or `hierarchical` (manager delegates)

### Pros for Startup Engine
- Multi-model support is a first-class feature
- Rich agent configuration (memory, tools, delegation, code execution)
- YAML-based configuration for version-controlled agent definitions
- Built-in token usage tracking in CrewOutput
- Hierarchical process mirrors our VP agent delegation pattern

### Cons for Startup Engine
- **Conflicts with Claude Code's native sub-agent model.** Claude Code spawns Task agents; CrewAI wants to be the orchestrator. Running CrewAI inside a Claude Code Task creates a framework-within-a-framework problem.
- Python only (our startup engine skill runs as a Claude Code slash command, not a Python app)
- Heavy dependency footprint
- State management is crew-scoped, not persistent across CLI sessions
- Would require rewriting the startup engine's orchestration layer

---

## 5. AutoGen (Microsoft) — Multi-Agent Conversations

### How It Works

AutoGen is a Python framework for building AI agents that converse with each other. It provides preset team patterns (round-robin, selector, swarm) and handles multi-turn conversations with termination conditions.

**Architecture:** Team → Agents (each with a model client) → Conversation turns → Termination conditions

### Multi-Model Agent Setup

```python
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.anthropic import AnthropicChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination

# Different models for different agents
gpt_client = OpenAIChatCompletionClient(model="gpt-4o-2024-08-06")
claude_client = AnthropicChatCompletionClient(model="claude-sonnet-4-20250514")

# Gemini via OpenAI-compatible endpoint
gemini_client = OpenAIChatCompletionClient(
    model="gemini-2.5-flash",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.environ["GEMINI_API_KEY"]
)

reviewer = AssistantAgent(
    name="code_reviewer",
    model_client=gpt_client,
    system_message="You review code for bugs and security issues."
)

architect = AssistantAgent(
    name="architect",
    model_client=claude_client,
    system_message="You evaluate architecture decisions."
)

summarizer = AssistantAgent(
    name="summarizer",
    model_client=gemini_client,
    system_message="You summarize discussions concisely."
)

# Team with termination
termination = TextMentionTermination("APPROVED")
team = RoundRobinGroupChat(
    [reviewer, architect, summarizer],
    termination_condition=termination
)

result = await team.run(task="Review this pull request: ...")
```

### Team Types

| Type | Pattern | Best For |
|------|---------|----------|
| RoundRobinGroupChat | Sequential turns, broadcast to all | Structured review cycles |
| SelectorGroupChat | LLM picks next speaker dynamically | Open-ended problem solving |
| MagenticOneGroupChat | Generalist multi-agent system | Complex web/file tasks |
| Swarm | HandoffMessage-based transitions | Agent-to-agent delegation |

### Termination & Convergence

- `TextMentionTermination("APPROVED")` — stops when keyword appears
- `TextMessageTermination` — stops when agent produces text (vs tool call)
- `ExternalTermination` — external code triggers stop
- Combine conditions with `|` (OR) operator
- `CancellationToken` for hard abort

### State Management

- Teams maintain conversation history across `run()` calls unless `reset()` is called
- `reset()` clears all agent states
- Teams can be resumed without reset
- No built-in persistence across process restarts (unlike LangGraph)

### Pros for Startup Engine
- Clean multi-model support via separate client classes
- Rich team patterns (round-robin, selector, swarm)
- Explicit termination conditions prevent runaway conversations
- Streaming support for real-time output
- Docker-based code execution for safety

### Cons for Startup Engine
- **Same framework conflict as CrewAI** — AutoGen wants to be the orchestrator, but Claude Code already is
- Experimental Anthropic client support
- Gemini support via OpenAI-compatibility layer (beta)
- No persistent state across process restarts
- Python-only, heavy dependencies
- Async-first API requires `await` everywhere

---

## 6. LangGraph — Stateful Agent Orchestration

### How It Works

LangGraph is a low-level orchestration framework for building stateful agents as directed graphs. Nodes are processing steps, edges are transitions, and state flows through the graph with built-in checkpointing.

**Architecture:** StateGraph → Nodes (functions) → Edges (transitions) → Checkpointer (persistence) → Human-in-the-loop interrupts

### Key Differentiator: Persistent Checkpointing

LangGraph is the ONLY framework that provides durable execution with automatic state persistence:

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver  # Production
from typing_extensions import TypedDict

class ReviewState(TypedDict):
    code: str
    review_comments: str
    fix_applied: bool
    approved: bool

def review_code(state: ReviewState):
    # Call GPT-4o for code review
    response = litellm.completion(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"Review this code:\n{state['code']}"}]
    )
    return {"review_comments": response.choices[0].message.content}

def apply_fix(state: ReviewState):
    # Call Claude for fixing
    response = litellm.completion(
        model="claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": f"Fix these issues:\n{state['review_comments']}\n\nCode:\n{state['code']}"}]
    )
    return {"code": response.choices[0].message.content, "fix_applied": True}

def get_approval(state: ReviewState):
    from langgraph.types import interrupt
    decision = interrupt("Review the fix and approve/reject")
    return {"approved": decision == "approve"}

# Build graph
builder = StateGraph(ReviewState)
builder.add_node("review", review_code)
builder.add_node("fix", apply_fix)
builder.add_node("approve", get_approval)
builder.add_edge(START, "review")
builder.add_edge("review", "fix")
builder.add_edge("fix", "approve")
builder.add_edge("approve", END)

# Compile with checkpointer
memory = InMemorySaver()
graph = builder.compile(checkpointer=memory)

# Execute — pauses at interrupt, resumes later
thread = {"configurable": {"thread_id": "review-pr-42"}}
result = graph.invoke({"code": "def foo(): pass"}, thread)
```

### Supervisor Pattern (Multi-Agent)

```python
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Different models for different agents
gpt_model = ChatOpenAI(model="gpt-4o")
claude_model = ChatAnthropic(model="claude-sonnet-4-20250514")

security_agent = create_react_agent(
    model=gpt_model,
    tools=[security_scan_tool],
    name="security_expert",
    prompt="You are a security expert."
)

architecture_agent = create_react_agent(
    model=claude_model,
    tools=[architecture_review_tool],
    name="architecture_expert",
    prompt="You are an architecture expert."
)

supervisor = create_supervisor(
    [security_agent, architecture_agent],
    model=gpt_model,  # Supervisor uses GPT for routing decisions
    prompt="Route tasks to the appropriate expert."
)

app = supervisor.compile(checkpointer=InMemorySaver())
```

### Human-in-the-Loop

- `interrupt()` pauses graph execution at any node
- State is checkpointed automatically
- Resume with `Command(resume='approve')` 
- Thread IDs enable multiple concurrent workflows

### Pros for Startup Engine
- Durable execution with automatic checkpointing
- Human-in-the-loop is built-in (matches CEO review gates)
- Graph-based workflows map naturally to SDLC phases
- Multi-model via LangChain model wrappers
- Can persist state across process restarts (Postgres checkpointer)
- Nested supervisors for hierarchical delegation

### Cons for Startup Engine
- **Framework conflict again** — LangGraph wants to own the orchestration graph
- Heavier dependency chain (LangChain ecosystem)
- Requires LangChain model wrappers (not raw API calls)
- Debugging graphs is harder than debugging sequential scripts
- Python-only for serious usage
- Overkill for "call GPT instead of Claude for this one task"

---

## 7. Practical Patterns — Calling GPT/Gemini from Claude Code

### Pattern A: Minimal Python Script (Recommended Starting Point)

The simplest approach. Claude Code spawns a Bash command that runs a Python script calling another model directly.

```python
#!/usr/bin/env python3
"""multi_model_call.py — Call any model from Claude Code via Bash"""
import sys
import os
import json

def call_openai(prompt, model="gpt-4o", max_tokens=4000):
    from openai import OpenAI
    client = OpenAI()  # Uses OPENAI_API_KEY env var
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content

def call_gemini(prompt, model="gemini-2.5-flash"):
    from google import genai
    client = genai.Client()  # Uses GEMINI_API_KEY env var
    response = client.models.generate_content(model=model, contents=prompt)
    return response.text

def call_litellm(prompt, model="gpt-4o", max_tokens=4000):
    """Universal caller — works with any model LiteLLM supports"""
    import litellm
    response = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    provider = sys.argv[1]  # "openai", "gemini", or "litellm"
    model = sys.argv[2]     # e.g., "gpt-4o", "gemini-2.5-flash"
    prompt = sys.argv[3]    # The prompt text
    
    if provider == "openai":
        result = call_openai(prompt, model)
    elif provider == "gemini":
        result = call_gemini(prompt, model)
    else:
        result = call_litellm(prompt, model)
    
    print(result)
```

**Usage from Claude Code Bash tool:**
```bash
python3 /path/to/multi_model_call.py litellm gpt-4o "Review this code for security issues: $(cat src/auth.py)"
```

### Pattern B: LiteLLM Library in Sub-Agent Scripts

For the startup engine, each VP agent script can import LiteLLM directly:

```python
#!/usr/bin/env python3
"""vp_testing_agent.py — Uses GPT-4o-mini for test generation (cheaper than Claude)"""
import litellm
import json
import os

# Budget tracking for this phase
litellm.max_budget = 2.00  # $2 cap for test generation

def generate_tests(source_code: str) -> str:
    """Use GPT-4o-mini for test generation — fast and cheap"""
    response = litellm.completion(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Generate comprehensive pytest tests for this code."},
            {"role": "user", "content": source_code}
        ],
        temperature=0.2,
        max_tokens=8000
    )
    print(f"Cost: ${response._hidden_params.get('response_cost', 'N/A')}")
    return response.choices[0].message.content

def review_tests(test_code: str, source_code: str) -> str:
    """Use Claude for reviewing test quality — better reasoning"""
    response = litellm.completion(
        model="claude-sonnet-4-20250514",
        messages=[
            {"role": "system", "content": "Review these tests for completeness and correctness."},
            {"role": "user", "content": f"Source:\n{source_code}\n\nTests:\n{test_code}"}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content

# Pipeline: cheap model generates, expensive model reviews
tests = generate_tests(open("src/auth.py").read())
review = review_tests(tests, open("src/auth.py").read())
print(json.dumps({"tests": tests, "review": review}))
```

### Pattern C: MCP Server Integration

Install model-specific MCP servers that Claude Code can invoke as tools:

```bash
# Install Gemini MCP tool
npm install -g gemini-mcp-tool
claude mcp add -s local gemini-cli -- npx -y gemini-mcp-tool

# Now available as slash commands in Claude Code:
# /gemini-cli:ask-gemini "Analyze this large codebase for patterns"
```

**Reported benefits:** 70% token savings on routine tasks, 50% cost reduction vs single-model.

**Limitation:** Each MCP server is a separate tool, not a unified interface. You can't do fallbacks or budget tracking across them.

### Pattern D: Bash One-Liners (Quick and Dirty)

```bash
# GPT-4o call via Python one-liner
python3 -c "
from openai import OpenAI
c = OpenAI()
r = c.chat.completions.create(model='gpt-4o-mini', messages=[{'role':'user','content':'Summarize: $(cat README.md | head -50)'}])
print(r.choices[0].message.content)
"

# Gemini call
python3 -c "
from google import genai
c = genai.Client()
r = c.models.generate_content(model='gemini-2.5-flash', contents='Summarize: $(cat README.md | head -50)')
print(r.text)
"

# LiteLLM universal call
python3 -c "
import litellm
r = litellm.completion(model='gpt-4o-mini', messages=[{'role':'user','content':'Hello'}])
print(r.choices[0].message.content)
"
```

### Pattern E: OpenRouter as Universal Endpoint

```bash
# Single curl command — works for any model
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello"}]
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

---

## 8. Recommendation for Startup Engine

### Phase 1: Minimal Integration (Do This Now)

**Add LiteLLM as a utility library** that VP agents can call when they want to use a non-Claude model for specific tasks.

1. **Install:** `pip install litellm` in the startup workspace
2. **Add env vars:** `OPENAI_API_KEY` (already optional in startup-engine.md line 93), `GEMINI_API_KEY`
3. **Create utility script:** `scripts/multi_model.py` with the `call_model()` function using LiteLLM
4. **Model routing rules in COO state:**

```yaml
model_routing:
  default: "claude-sonnet-4-20250514"  # Default for all agents
  overrides:
    test_generation: "gpt-4o-mini"      # 10x cheaper for structured output
    code_review_diversity: "gpt-4o"      # Second opinion on reviews
    large_context_analysis: "gemini/gemini-2.5-flash"  # 1M context window
    documentation: "gpt-4o-mini"         # Cheap for prose generation
    summarization: "gemini/gemini-2.5-flash"  # Fast and cheap
  budget:
    per_sprint_total: 25.00             # $25 total for non-Claude models
    per_phase_max: 5.00                 # $5 max per phase
    per_call_max: 0.50                  # $0.50 max per individual call
```

5. **VP agent integration pattern:**

```python
# In any VP agent script
import litellm
import os

# Read routing config from COO state
model = get_model_for_task("test_generation")  # Returns "gpt-4o-mini"

response = litellm.completion(
    model=model,
    messages=[{"role": "user", "content": prompt}],
    max_tokens=4000
)

# Track cost
log_cost(phase="testing", model=model, cost=response._hidden_params.get("response_cost", 0))
```

### Phase 2: Fallback & Budget System

Add the LiteLLM Router for automatic fallbacks and the BudgetManager for per-phase cost tracking:

```python
from litellm import Router, BudgetManager

# Fallback: try Claude first, fall back to GPT if rate-limited
router = Router(model_list=[
    {"model_name": "primary", "litellm_params": {"model": "claude-sonnet-4-20250514"}, "model_info": {"id": "claude-primary"}},
    {"model_name": "primary", "litellm_params": {"model": "gpt-4o"}, "model_info": {"id": "gpt-fallback"}}
], num_retries=2, cooldown_time=30)

budget = BudgetManager(project_name="startup-engine-sprint-42")
budget.create_budget(total_budget=25.0, user="sprint-42", duration="weekly")
```

### Phase 3: Framework Evaluation (Only If Needed)

If the startup engine grows to need persistent state across process restarts, complex agent-to-agent handoffs, or graph-based workflow visualization, THEN evaluate:

- **LangGraph** if you need checkpointing and human-in-the-loop gates
- **CrewAI** if you want to define agents in YAML and need hierarchical delegation
- **AutoGen** if the core workflow is multi-agent conversation/debate

But do NOT adopt these frameworks until the simpler LiteLLM approach proves insufficient. They add significant complexity and conflict with Claude Code's native orchestration model.

### Cost Comparison (Approximate, as of April 2026)

| Task | Claude Sonnet | GPT-4o-mini | Gemini 2.5 Flash | Savings |
|------|--------------|-------------|------------------|---------|
| Test generation (8K out) | ~$0.12 | ~$0.005 | ~$0.003 | 95-97% |
| Code review (4K out) | ~$0.06 | ~$0.04 | ~$0.02 | 33-67% |
| Documentation (4K out) | ~$0.06 | ~$0.005 | ~$0.003 | 92-95% |
| Architecture analysis (4K out) | ~$0.06 | ~$0.04 | ~$0.02 | 33-67% |
| Summarization (2K out) | ~$0.03 | ~$0.002 | ~$0.001 | 93-97% |

**Estimated savings per sprint:** If 60% of tasks can use GPT-4o-mini or Gemini Flash instead of Claude Sonnet, expect 50-70% reduction in non-orchestration LLM costs.

---

## Sources

### Official Documentation
- [LiteLLM Docs — Getting Started](https://docs.litellm.ai/docs/)
- [LiteLLM — Routing & Load Balancing](https://docs.litellm.ai/docs/routing)
- [LiteLLM — Budget Manager](https://docs.litellm.ai/docs/budget_manager)
- [LiteLLM — OpenAI Provider](https://docs.litellm.ai/docs/providers/openai)
- [LiteLLM — Completion Input API](https://docs.litellm.ai/docs/completion/input)
- [LiteLLM — Proxy Quick Start](https://docs.litellm.ai/docs/proxy/quick_start)
- [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter — Model Fallbacks](https://openrouter.ai/docs/guides/routing/model-fallbacks)
- [OpenRouter — Provider Selection](https://openrouter.ai/docs/guides/routing/provider-selection)
- [CrewAI Documentation](https://docs.crewai.com/)
- [CrewAI — LLM Configuration](https://docs.crewai.com/concepts/llms)
- [CrewAI — Agents](https://docs.crewai.com/concepts/agents)
- [CrewAI — Crews](https://docs.crewai.com/concepts/crews)
- [AutoGen Documentation](https://microsoft.github.io/autogen/stable/)
- [AutoGen — AgentChat Quickstart](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/quickstart.html)
- [AutoGen — Teams](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html)
- [AutoGen — Models](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/models.html)
- [LangGraph Overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangGraph GitHub](https://github.com/langchain-ai/langgraph)
- [LangGraph Supervisor Pattern](https://github.com/langchain-ai/langgraph-supervisor-py)
- [Google Gemini API Quickstart](https://ai.google.dev/gemini-api/docs/quickstart)
- [Google Gen AI Python SDK](https://github.com/googleapis/python-genai)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [LiteLLM npm package](https://www.npmjs.com/package/litellm)

### Comparison & Analysis
- [LiteLLM vs OpenRouter — TrueFoundry](https://www.truefoundry.com/blog/litellm-vs-openrouter)
- [OpenRouter vs LiteLLM — Xenoss](https://xenoss.io/blog/openrouter-vs-litellm)
- [OpenRouter vs LiteLLM — Merge.dev](https://www.merge.dev/blog/litellm-vs-openrouter)
- [Top LLM Gateways 2025 — Helicone](https://www.helicone.ai/blog/top-llm-gateways-comparison-2025)
- [OpenRouter Pricing — CostGoat](https://costgoat.com/pricing/openrouter)

### Practical Patterns
- [Claude Code + MCP Multi-Model Integration — lgallardo.com](https://lgallardo.com/2025/09/06/claude-code-supercharged-mcp-integration/)
- [CLI Tool Comparison for Multi-Model Switching — Apiyi](https://help.apiyi.com/en/claude-code-gpt-gemini-model-cli-tool-selection-opencode-cline-aider-guide-en.html)
- [Multi-Model Orchestration Desktop App — DEV Community](https://dev.to/tsunamayo7/i-built-a-desktop-app-that-orchestrates-claude-gpt-gemini-and-local-ollama-in-a-3-phase-pipeline-1ml7)
- [LangGraph Human-in-the-Loop — DEV Community](https://dev.to/jamesbmour/interrupts-and-commands-in-langgraph-building-human-in-the-loop-workflows-4ngl)
- [LangGraph State Management — Medium](https://medium.com/@bharatraj1918/langgraph-state-management-part-1-how-langgraph-manages-state-for-multi-agent-workflows-da64d352c43b)
