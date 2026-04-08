# Resilience Patterns & Multi-Turn Iteration Controls for Multi-Model AI Agent Systems

**Research Date:** 2026-04-06 UTC
**Sources:** 50+ across academic papers, framework docs, GitHub repos, engineering blogs, and production case studies
**Use Case:** Startup-engine orchestrator (Claude) spawning agents that call GPT-4o, Gemini, or Claude for specific tasks

---

## Table of Contents

1. [Resilience When External Models Are Unavailable](#1-resilience-when-external-models-are-unavailable)
2. [Detecting and Stopping Runaway Agents](#2-detecting-and-stopping-runaway-agents)
3. [Multi-Turn Conversation Iteration Controls](#3-multi-turn-conversation-iteration-controls)
4. [State Persistence Across Turns](#4-state-persistence-across-turns)
5. [Recommended Architecture for Startup-Engine](#5-recommended-architecture-for-startup-engine)
6. [Sources](#6-sources)

---

## 1. Resilience When External Models Are Unavailable

### 1.1 Circuit Breaker Pattern for AI API Calls

The circuit breaker pattern prevents cascading failures when an external model API is degraded. It operates as a three-state machine:

- **Closed** (normal): Requests pass through. Failures increment a counter.
- **Open** (tripped): All requests fail immediately without calling the API. A timer starts.
- **Half-Open** (testing): After the timer expires, one request is allowed through. Success closes the circuit; failure reopens it.

**Production-tested configuration values:**

| Parameter | Recommended Value | Rationale |
|-----------|------------------|-----------|
| `fail_max` | 5 | Balances sensitivity vs. false positives. Cloud APIs experience brief transient errors; threshold of 3 causes unnecessary flapping. |
| `reset_timeout` | 30-60 seconds | Start at 30s for OpenAI/Claude, measure p50 recovery time, set to 1.5x that value. For local models (Ollama), 10s suffices. |
| `success_threshold` | 2-3 | Consecutive successes required before closing the circuit in half-open state. |

**Python implementation using pybreaker (production-grade):**

```python
import pybreaker
import asyncio
from datetime import datetime, timezone

class LLMCircuitBreakerListener(pybreaker.CircuitBreakerListener):
    """Logs state changes and failures for observability."""
    
    def state_change(self, cb, old_state, new_state):
        timestamp = datetime.now(timezone.utc).isoformat()
        print(f"[{timestamp}] Circuit '{cb.name}': {old_state.name} -> {new_state.name}")
    
    def failure(self, cb, exc):
        timestamp = datetime.now(timezone.utc).isoformat()
        print(f"[{timestamp}] Circuit '{cb.name}' failure #{cb.fail_counter}: {exc}")
    
    def success(self, cb):
        if cb.current_state == pybreaker.STATE_HALF_OPEN:
            print(f"Circuit '{cb.name}' recovery probe succeeded")

# One breaker per provider per operation type
gpt4o_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    success_threshold=2,
    exclude=[
        lambda e: hasattr(e, 'status_code') and e.status_code in (400, 401, 403, 404)
    ],
    listeners=[LLMCircuitBreakerListener()],
    name="gpt-4o-chat"
)

gemini_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    success_threshold=2,
    exclude=[
        lambda e: hasattr(e, 'status_code') and e.status_code in (400, 401, 403, 404)
    ],
    listeners=[LLMCircuitBreakerListener()],
    name="gemini-2.5-pro-chat"
)

claude_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    success_threshold=2,
    exclude=[
        lambda e: hasattr(e, 'status_code') and e.status_code in (400, 401, 403, 404)
    ],
    listeners=[LLMCircuitBreakerListener()],
    name="claude-sonnet-chat"
)
```

**Critical design rule:** Never share a single circuit breaker across unrelated API operations. If the Claude messages endpoint is down but the embeddings endpoint is healthy, a shared breaker blocks embedding requests unnecessarily. Each logical operation gets its own breaker instance.

### 1.2 Timeout Strategies

LLM API calls have fundamentally different timeout characteristics than traditional APIs because response time scales with output token count.

**Recommended timeout configuration:**

| Model | Simple task (<1K output) | Complex task (1-4K output) | Long generation (4K+) |
|-------|-------------------------|---------------------------|----------------------|
| GPT-4o | 30s | 60s | 120s |
| Gemini 2.5 Pro | 30s | 60s | 120s |
| Claude Sonnet 4 | 30s | 60s | 120s |
| Claude Opus 4 | 45s | 90s | 180s |

**Implementation pattern with adaptive timeouts:**

```python
import asyncio
import time
from dataclasses import dataclass, field

@dataclass
class AdaptiveTimeout:
    """Adjusts timeout based on observed latency history."""
    base_timeout: float = 30.0
    max_timeout: float = 180.0
    multiplier: float = 1.5  # timeout = multiplier * p95_latency
    latency_history: list = field(default_factory=list)
    window_size: int = 20
    
    def record_latency(self, latency_seconds: float):
        self.latency_history.append(latency_seconds)
        if len(self.latency_history) > self.window_size:
            self.latency_history = self.latency_history[-self.window_size:]
    
    def get_timeout(self, estimated_output_tokens: int = 1000) -> float:
        if len(self.latency_history) < 3:
            # Not enough data; use base scaled by expected output
            token_factor = max(1.0, estimated_output_tokens / 1000)
            return min(self.base_timeout * token_factor, self.max_timeout)
        
        sorted_latencies = sorted(self.latency_history)
        p95_index = int(len(sorted_latencies) * 0.95)
        p95_latency = sorted_latencies[min(p95_index, len(sorted_latencies) - 1)]
        
        token_factor = max(1.0, estimated_output_tokens / 1000)
        timeout = p95_latency * self.multiplier * token_factor
        return min(max(timeout, self.base_timeout), self.max_timeout)

# Per-provider timeout trackers
timeouts = {
    "gpt-4o": AdaptiveTimeout(base_timeout=30),
    "gemini-2.5-pro": AdaptiveTimeout(base_timeout=30),
    "claude-sonnet-4": AdaptiveTimeout(base_timeout=30),
    "claude-opus-4": AdaptiveTimeout(base_timeout=45),
}
```

### 1.3 Retry with Exponential Backoff (Token-Cost-Aware)

Standard exponential backoff doubles wait time after each failure. For LLM APIs, this must be token-cost-aware: retrying a 50K-token generation costs real money.

**Retryable vs. non-retryable errors:**

| Status Code | Retryable? | Reason |
|-------------|-----------|--------|
| 429 | Yes | Rate limit; backoff and retry |
| 500 | Yes (cautiously) | Server error; may be transient |
| 502, 503, 504 | Yes | Gateway/availability; typically transient |
| 400 | No | Bad request; retrying wastes tokens |
| 401, 403 | No | Auth failure; permanent until credentials change |
| 404 | No | Model not found; permanent |

**Token-cost-aware retry implementation:**

```python
import random
import asyncio
from enum import Enum
from dataclasses import dataclass

class RetryDecision(Enum):
    RETRY = "retry"
    FALLBACK = "fallback"
    FAIL = "fail"

@dataclass
class TokenCostTracker:
    """Tracks cumulative token spend to make retry decisions."""
    max_cost_per_task: float = 1.00  # USD
    cumulative_cost: float = 0.0
    
    # Approximate costs per 1K tokens (input/output)
    COST_TABLE = {
        "gpt-4o":           {"input": 0.0025, "output": 0.01},
        "gemini-2.5-pro":   {"input": 0.00125, "output": 0.01},
        "claude-sonnet-4":  {"input": 0.003, "output": 0.015},
        "claude-opus-4":    {"input": 0.015, "output": 0.075},
        "claude-haiku-3.5": {"input": 0.0008, "output": 0.004},
    }
    
    def estimate_retry_cost(self, model: str, est_input_tokens: int, est_output_tokens: int) -> float:
        costs = self.COST_TABLE.get(model, {"input": 0.01, "output": 0.03})
        return (est_input_tokens / 1000 * costs["input"] + 
                est_output_tokens / 1000 * costs["output"])
    
    def should_retry(self, model: str, est_input_tokens: int, est_output_tokens: int) -> RetryDecision:
        retry_cost = self.estimate_retry_cost(model, est_input_tokens, est_output_tokens)
        if self.cumulative_cost + retry_cost > self.max_cost_per_task:
            return RetryDecision.FALLBACK  # Try cheaper model instead
        return RetryDecision.RETRY
    
    def record_cost(self, model: str, input_tokens: int, output_tokens: int):
        costs = self.COST_TABLE.get(model, {"input": 0.01, "output": 0.03})
        self.cumulative_cost += (input_tokens / 1000 * costs["input"] + 
                                  output_tokens / 1000 * costs["output"])

async def retry_with_backoff(
    func,
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: bool = True,
    cost_tracker: TokenCostTracker = None,
    model: str = "gpt-4o",
    est_input_tokens: int = 2000,
    est_output_tokens: int = 1000,
    **kwargs
):
    """Exponential backoff with jitter and token-cost awareness."""
    for attempt in range(max_retries + 1):
        try:
            result = await func(*args, **kwargs)
            if cost_tracker and hasattr(result, 'usage'):
                cost_tracker.record_cost(
                    model, 
                    result.usage.input_tokens, 
                    result.usage.output_tokens
                )
            return result
        except Exception as e:
            status = getattr(e, 'status_code', getattr(e, 'code', None))
            
            # Non-retryable errors
            if status in (400, 401, 403, 404):
                raise
            
            if attempt == max_retries:
                raise
            
            # Check cost budget before retrying
            if cost_tracker:
                decision = cost_tracker.should_retry(model, est_input_tokens, est_output_tokens)
                if decision == RetryDecision.FALLBACK:
                    raise CostBudgetExceeded(
                        f"Retry would exceed task budget "
                        f"(${cost_tracker.cumulative_cost:.4f} / "
                        f"${cost_tracker.max_cost_per_task:.2f})"
                    )
            
            # Exponential backoff with jitter
            delay = min(base_delay * (2 ** attempt), max_delay)
            if jitter:
                delay = delay * (0.5 + random.random())  # Full jitter
            
            # Respect Retry-After header if present
            retry_after = getattr(e, 'headers', {}).get('Retry-After')
            if retry_after:
                delay = max(delay, float(retry_after))
            
            await asyncio.sleep(delay)

class CostBudgetExceeded(Exception):
    pass
```

### 1.4 Fallback Chains: Multi-Provider Failover

When the primary model is unavailable, the system should cascade through alternatives. The order matters: prioritize by capability match, then cost.

**Fallback chain architecture:**

```
Task requires strong reasoning:
  Primary:    Claude Opus 4        (best reasoning)
  Fallback 1: GPT-4o              (strong alternative)
  Fallback 2: Gemini 2.5 Pro      (comparable)
  Fallback 3: Claude Sonnet 4     (graceful degradation)

Task requires fast generation:
  Primary:    Claude Haiku 3.5     (fastest, cheapest)
  Fallback 1: GPT-4o-mini         (fast alternative)
  Fallback 2: Gemini 2.0 Flash    (comparable)
  Fallback 3: Claude Sonnet 4     (over-provisioned but available)
```

**Complete fallback chain implementation:**

```python
import pybreaker
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from datetime import datetime, timezone

@dataclass
class ModelConfig:
    name: str
    provider: str  # "openai", "anthropic", "google"
    breaker: pybreaker.CircuitBreaker
    timeout: AdaptiveTimeout
    call_fn: Callable  # async function that calls the model
    cost_per_1k_input: float
    cost_per_1k_output: float

@dataclass
class FallbackChain:
    """Ordered list of models to try. Each gets its own circuit breaker."""
    models: list[ModelConfig]
    cost_tracker: TokenCostTracker = field(default_factory=TokenCostTracker)
    
    async def call(self, messages: list, max_tokens: int = 2000, **kwargs) -> dict:
        errors = []
        
        for i, model in enumerate(self.models):
            # Check circuit breaker state
            if not model.breaker.current_state == pybreaker.STATE_OPEN:
                try:
                    timeout = model.timeout.get_timeout(max_tokens)
                    
                    result = await asyncio.wait_for(
                        retry_with_backoff(
                            model.call_fn,
                            messages=messages,
                            max_tokens=max_tokens,
                            max_retries=2,  # Fewer retries per model in a chain
                            cost_tracker=self.cost_tracker,
                            model=model.name,
                            **kwargs
                        ),
                        timeout=timeout
                    )
                    
                    # Record success latency
                    if hasattr(result, '_latency'):
                        model.timeout.record_latency(result._latency)
                    
                    return {
                        "result": result,
                        "model_used": model.name,
                        "fallback_depth": i,
                        "errors_before_success": errors,
                        "total_cost": self.cost_tracker.cumulative_cost,
                    }
                    
                except pybreaker.CircuitBreakerError:
                    errors.append({
                        "model": model.name,
                        "error": "circuit_open",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                except asyncio.TimeoutError:
                    errors.append({
                        "model": model.name,
                        "error": "timeout",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                except CostBudgetExceeded as e:
                    errors.append({
                        "model": model.name,
                        "error": "budget_exceeded",
                        "detail": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                except Exception as e:
                    errors.append({
                        "model": model.name,
                        "error": type(e).__name__,
                        "detail": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
            else:
                errors.append({
                    "model": model.name,
                    "error": "circuit_open",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
        
        # All models failed
        raise AllModelsUnavailable(
            f"All {len(self.models)} models in fallback chain failed",
            errors=errors
        )

class AllModelsUnavailable(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors or []
```

**LiteLLM as a production shortcut:**

For teams that want this without building from scratch, [LiteLLM](https://github.com/BerriAI/litellm) provides a unified interface with built-in fallback, cost tracking, and budget routing:

```python
from litellm import Router

model_list = [
    {
        "model_name": "strong-reasoning",
        "litellm_params": {
            "model": "anthropic/claude-opus-4",
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
            "timeout": 90,
            "order": 1,  # Primary
            "max_budget": 5.00,
            "budget_duration": "1d",
        }
    },
    {
        "model_name": "strong-reasoning",
        "litellm_params": {
            "model": "openai/gpt-4o",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "timeout": 60,
            "order": 2,  # First fallback
            "max_budget": 5.00,
            "budget_duration": "1d",
        }
    },
    {
        "model_name": "strong-reasoning",
        "litellm_params": {
            "model": "google/gemini-2.5-pro",
            "api_key": os.getenv("GOOGLE_API_KEY"),
            "timeout": 60,
            "order": 3,  # Second fallback
        }
    },
]

router = Router(
    model_list=model_list,
    retry_policy=RetryPolicy(
        TimeoutErrorRetries=2,
        RateLimitErrorRetries=3,
        AuthenticationErrorRetries=0,
    ),
    allowed_fails=3,
    cooldown_time=30,
    routing_strategy="cost-based-routing",
    enable_pre_call_checks=True,
)

# Usage -- automatically handles fallback and cost tracking
response = await router.acompletion(
    model="strong-reasoning",
    messages=[{"role": "user", "content": "Analyze this architecture..."}],
)
```

### 1.5 Graceful Degradation Strategies

When all models for a task are down, agents must degrade gracefully rather than crash.

**Degradation hierarchy:**

| Level | Condition | Agent Behavior |
|-------|-----------|---------------|
| 0 | Primary model available | Normal operation |
| 1 | Primary down, fallback succeeds | Log warning, continue with fallback model name in metadata |
| 2 | All models down, cached result exists | Return cached result with `stale: true` flag |
| 3 | All models down, no cache | Return partial result with `degraded: true` flag |
| 4 | All models down, no partial possible | Queue task for retry, notify orchestrator |
| 5 | Orchestrator itself cannot reach any model | Write state to disk, exit with recoverable status code |

**Implementation pattern:**

```python
@dataclass
class DegradedResult:
    """Returned when full model capability is unavailable."""
    content: Optional[str] = None
    degradation_level: int = 0
    model_used: Optional[str] = None
    fallback_depth: int = 0
    is_stale: bool = False
    is_partial: bool = False
    errors: list = field(default_factory=list)
    retry_after_seconds: Optional[int] = None
    
    @property
    def is_degraded(self) -> bool:
        return self.degradation_level > 0

async def resilient_agent_call(
    chain: FallbackChain,
    messages: list,
    task_id: str,
    cache: dict = None,
    **kwargs
) -> DegradedResult:
    try:
        response = await chain.call(messages, **kwargs)
        result = DegradedResult(
            content=response["result"].content,
            model_used=response["model_used"],
            fallback_depth=response["fallback_depth"],
            degradation_level=response["fallback_depth"],  # 0 = primary
        )
        # Update cache on success
        if cache is not None:
            cache[task_id] = {
                "content": result.content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model": result.model_used,
            }
        return result
        
    except AllModelsUnavailable as e:
        # Level 2: Try cache
        if cache and task_id in cache:
            cached = cache[task_id]
            return DegradedResult(
                content=cached["content"],
                degradation_level=2,
                model_used=f"cache({cached['model']})",
                is_stale=True,
                errors=[{"error": "all_models_down", "cached_from": cached["timestamp"]}],
            )
        
        # Level 4: Queue for retry
        return DegradedResult(
            degradation_level=4,
            errors=e.errors,
            retry_after_seconds=60,
        )
```

---

## 2. Detecting and Stopping Runaway Agents

### 2.1 Token Budget Caps Per Agent Call

Every agent invocation must have a hard token budget. The Claude Agent SDK supports this natively:

```python
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

# Using Claude Agent SDK built-in controls
options = ClaudeAgentOptions(
    max_budget_usd=0.50,    # Hard cost cap
    max_turns=10,           # Hard iteration cap
)

async for message in query(prompt="Analyze this codebase", options=options):
    if isinstance(message, ResultMessage):
        if message.subtype == "error_max_budget_usd":
            print(f"Budget exceeded at ${message.total_cost_usd:.4f}")
            # Trigger graceful degradation
        else:
            print(f"Complete. Cost: ${message.total_cost_usd:.4f}, "
                  f"Turns: {message.num_turns}, "
                  f"Duration: {message.duration_ms}ms")
```

**For external model calls without built-in budget controls:**

```python
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class AgentBudget:
    """Enforces per-agent resource limits."""
    max_tokens_input: int = 50_000       # Max input tokens across all calls
    max_tokens_output: int = 20_000      # Max output tokens across all calls
    max_cost_usd: float = 1.00           # Max USD spend
    max_wall_clock_seconds: float = 300  # 5 minutes
    max_api_calls: int = 10              # Max LLM API calls
    
    # Tracking
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    api_calls: int = 0
    start_time: float = field(default_factory=lambda: time.time())
    
    def check_budget(self, est_input: int = 0, est_output: int = 0) -> tuple[bool, str]:
        """Returns (ok, reason). Call BEFORE each API request."""
        elapsed = time.time() - self.start_time
        
        if elapsed > self.max_wall_clock_seconds:
            return False, f"wall_clock_exceeded ({elapsed:.0f}s > {self.max_wall_clock_seconds}s)"
        
        if self.api_calls >= self.max_api_calls:
            return False, f"api_calls_exceeded ({self.api_calls} >= {self.max_api_calls})"
        
        if self.total_input_tokens + est_input > self.max_tokens_input:
            return False, f"input_tokens_exceeded ({self.total_input_tokens + est_input} > {self.max_tokens_input})"
        
        if self.total_output_tokens + est_output > self.max_tokens_output:
            return False, f"output_tokens_exceeded ({self.total_output_tokens + est_output} > {self.max_tokens_output})"
        
        if self.total_cost_usd > self.max_cost_usd:
            return False, f"cost_exceeded (${self.total_cost_usd:.4f} > ${self.max_cost_usd:.2f})"
        
        return True, "ok"
    
    def record_usage(self, input_tokens: int, output_tokens: int, cost_usd: float):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost_usd += cost_usd
        self.api_calls += 1
    
    def summary(self) -> dict:
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "cost_usd": round(self.total_cost_usd, 6),
            "api_calls": self.api_calls,
            "wall_clock_seconds": round(time.time() - self.start_time, 1),
            "budget_remaining_usd": round(self.max_cost_usd - self.total_cost_usd, 6),
        }
```

**Recommended budget presets per task type:**

| Task Type | Max Input Tokens | Max Output Tokens | Max Cost | Max Time | Max Calls |
|-----------|-----------------|-------------------|----------|----------|-----------|
| Quick classification | 5,000 | 500 | $0.05 | 30s | 1 |
| Code review | 50,000 | 5,000 | $0.50 | 120s | 3 |
| Architecture analysis | 100,000 | 10,000 | $2.00 | 300s | 5 |
| Full code generation | 100,000 | 50,000 | $5.00 | 600s | 10 |
| Multi-turn review loop | 200,000 | 30,000 | $3.00 | 600s | 15 |

### 2.2 Wall-Clock Timeouts

**Two-layer timeout strategy:**

```python
import signal
import asyncio

class AgentTimeoutManager:
    """Enforces both per-call and per-agent wall-clock limits."""
    
    def __init__(self, max_agent_seconds: float = 300, max_call_seconds: float = 60):
        self.max_agent_seconds = max_agent_seconds
        self.max_call_seconds = max_call_seconds
        self.agent_start = None
    
    async def run_with_agent_timeout(self, agent_coroutine):
        """Wraps entire agent execution with a hard timeout."""
        self.agent_start = time.time()
        try:
            return await asyncio.wait_for(
                agent_coroutine,
                timeout=self.max_agent_seconds
            )
        except asyncio.TimeoutError:
            elapsed = time.time() - self.agent_start
            raise AgentTimeoutError(
                f"Agent exceeded wall-clock limit: {elapsed:.0f}s > {self.max_agent_seconds}s"
            )
    
    def remaining_time(self) -> float:
        """How much time the agent has left. Use for adaptive sub-timeouts."""
        if self.agent_start is None:
            return self.max_agent_seconds
        elapsed = time.time() - self.agent_start
        return max(0, self.max_agent_seconds - elapsed)
    
    def call_timeout(self) -> float:
        """Timeout for the next individual API call."""
        return min(self.max_call_seconds, self.remaining_time())
```

### 2.3 Output Validation: Detecting Loops and Garbage

Runaway agents manifest in three patterns:

1. **Repetition loops**: Agent produces the same or near-identical output across iterations.
2. **Garbage output**: Model returns malformed, incoherent, or off-topic content.
3. **Tool-call loops**: Agent repeatedly calls the same tool with the same arguments.

**Detection implementation:**

```python
import hashlib
import json
from difflib import SequenceMatcher

@dataclass
class OutputValidator:
    """Detects runaway agent patterns."""
    similarity_threshold: float = 0.85   # 85% similarity = likely loop
    min_output_length: int = 10          # Outputs shorter than this are suspicious
    max_consecutive_similar: int = 2      # Stop after 2 near-identical outputs
    output_history: list = field(default_factory=list)
    tool_call_history: list = field(default_factory=list)
    
    def check_output(self, output: str) -> tuple[bool, str]:
        """Returns (valid, reason). Call after each agent output."""
        
        # Check 1: Minimum length
        if len(output.strip()) < self.min_output_length:
            return False, f"output_too_short (len={len(output.strip())})"
        
        # Check 2: Similarity to recent outputs (loop detection)
        consecutive_similar = 0
        for prev_output in reversed(self.output_history[-5:]):
            similarity = SequenceMatcher(None, output, prev_output).ratio()
            if similarity > self.similarity_threshold:
                consecutive_similar += 1
            else:
                break
        
        if consecutive_similar >= self.max_consecutive_similar:
            return False, f"repetition_loop (similarity>{self.similarity_threshold} " \
                          f"for {consecutive_similar} consecutive outputs)"
        
        # Check 3: Detect common garbage patterns
        garbage_indicators = [
            output.count("```") > 10,                    # Excessive code blocks
            len(set(output.split())) < len(output.split()) * 0.1,  # Extreme word repetition
            output.count("\n\n\n") > 5,                  # Excessive blank lines
        ]
        if any(garbage_indicators):
            return False, "garbage_detected"
        
        self.output_history.append(output)
        return True, "ok"
    
    def check_tool_call(self, tool_name: str, arguments: dict) -> tuple[bool, str]:
        """Detect tool-call loops."""
        call_hash = hashlib.md5(
            json.dumps({"tool": tool_name, "args": arguments}, sort_keys=True).encode()
        ).hexdigest()
        
        # Count identical calls in recent history
        recent = self.tool_call_history[-10:]
        identical_count = sum(1 for h in recent if h == call_hash)
        
        self.tool_call_history.append(call_hash)
        
        if identical_count >= 3:
            return False, f"tool_call_loop ({tool_name} called {identical_count+1} " \
                          f"times with identical arguments)"
        
        return True, "ok"
```

**Trustworthiness scoring** (from Cleanlab research): Production systems using Trustworthy Language Model (TLM) trust scores can detect LLM output errors with 25% greater precision/recall than LLM-as-a-judge evaluations. When using trust scoring, teams can focus human review on just 1-5% of cases where the LLM is untrustworthy.

### 2.4 Kill Switches

**Process-level kill switch:**

```python
import subprocess
import os
import signal

class AgentKillSwitch:
    """Hard termination for stuck external model calls."""
    
    def __init__(self):
        self.active_processes: dict[str, subprocess.Popen] = {}
        self.active_tasks: dict[str, asyncio.Task] = {}
    
    def register_process(self, agent_id: str, process: subprocess.Popen):
        self.active_processes[agent_id] = process
    
    def register_task(self, agent_id: str, task: asyncio.Task):
        self.active_tasks[agent_id] = task
    
    def kill(self, agent_id: str, reason: str = "manual") -> dict:
        """Terminate a specific agent immediately."""
        result = {"agent_id": agent_id, "reason": reason, "killed": False}
        
        if agent_id in self.active_tasks:
            self.active_tasks[agent_id].cancel()
            del self.active_tasks[agent_id]
            result["killed"] = True
            result["method"] = "task_cancel"
        
        if agent_id in self.active_processes:
            proc = self.active_processes[agent_id]
            try:
                proc.terminate()  # SIGTERM first
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()  # SIGKILL if SIGTERM fails
            except ProcessLookupError:
                pass  # Already dead
            del self.active_processes[agent_id]
            result["killed"] = True
            result["method"] = "process_kill"
        
        result["timestamp"] = datetime.now(timezone.utc).isoformat()
        return result
    
    def kill_all(self, reason: str = "emergency") -> list[dict]:
        """Kill all active agents. Emergency stop."""
        results = []
        for agent_id in list(self.active_processes.keys()) + list(self.active_tasks.keys()):
            results.append(self.kill(agent_id, reason))
        return results
```

### 2.5 Cost Monitoring

**Real-time spend tracking per agent, per model, per session:**

```python
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

@dataclass
class CostMonitor:
    """Tracks spend across agents, models, and sessions with alert thresholds."""
    daily_budget: float = 50.00
    alert_thresholds: list = field(default_factory=lambda: [0.50, 0.75, 0.90])
    
    # Tracking
    spend_by_agent: dict = field(default_factory=lambda: defaultdict(float))
    spend_by_model: dict = field(default_factory=lambda: defaultdict(float))
    spend_by_session: dict = field(default_factory=lambda: defaultdict(float))
    total_spend: float = 0.0
    alerts_fired: set = field(default_factory=set)
    
    # Persistence
    log_path: Path = Path("/tmp/agent-cost-log.jsonl")
    
    def record(self, agent_id: str, model: str, session_id: str,
               input_tokens: int, output_tokens: int, cost_usd: float):
        self.spend_by_agent[agent_id] += cost_usd
        self.spend_by_model[model] += cost_usd
        self.spend_by_session[session_id] += cost_usd
        self.total_spend += cost_usd
        
        # Log to file
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_id": agent_id,
            "model": model,
            "session_id": session_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost_usd, 6),
            "cumulative_total": round(self.total_spend, 6),
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        # Check alert thresholds
        self._check_alerts()
    
    def _check_alerts(self):
        utilization = self.total_spend / self.daily_budget
        for threshold in self.alert_thresholds:
            if utilization >= threshold and threshold not in self.alerts_fired:
                self.alerts_fired.add(threshold)
                print(f"COST ALERT: {threshold*100:.0f}% of daily budget "
                      f"(${self.total_spend:.2f} / ${self.daily_budget:.2f})")
    
    def report(self) -> dict:
        return {
            "total_spend_usd": round(self.total_spend, 4),
            "daily_budget_usd": self.daily_budget,
            "utilization_pct": round(self.total_spend / self.daily_budget * 100, 1),
            "by_agent": dict(self.spend_by_agent),
            "by_model": dict(self.spend_by_model),
            "by_session": dict(self.spend_by_session),
        }
```

---

## 3. Multi-Turn Conversation Iteration Controls

### 3.1 Code Review Loop: Reviewer-Developer-Reviewer

The evaluator-optimizer pattern from Anthropic's "[Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)" guide provides the canonical framework. One LLM generates a response while another evaluates it in a loop.

**Mathematical convergence model** (from Yannick Schroeder's research):

The accuracy after round `t` follows:

```
Acc_t = Upp - α^t × (Upp - Acc_0)
```

Where:
- `Upp = CS / (1 - CL + CS)` = theoretical accuracy ceiling
- `α = CL - CS` = convergence rate (smaller = faster convergence)
- `CL` = probability model preserves correct content (Confidence Level, typically 0.9)
- `CS` = probability model successfully fixes an error (Critique Score, typically 0.4)

**Improvement distribution per round:**

| Round | Share of Total Improvement |
|-------|--------------------------|
| 1 | 50% |
| 2 | 25% (cumulative: 75%) |
| 3 | 12.5% (cumulative: 87.5%) |
| 4+ | Diminishing rapidly |

**Key finding:** Rounds 1-2 capture 75% of total reachable improvement. Beyond round 3, diminishing returns are severe.

**Recommended maximum rounds by task type:**

| Task Type | Max Rounds | Rationale |
|-----------|-----------|-----------|
| Code review (style/lint) | 2 | Style issues are binary; 2 rounds catches 75% |
| Code review (logic/bugs) | 3 | Logic errors need more iteration |
| Architecture review | 2 | High-level feedback converges fast |
| Documentation review | 3 | Nuance in language benefits from iteration |
| Security review | 3-4 | Critical enough to warrant extra passes |
| Full TDD cycle | 5 | Tests provide objective convergence signal |

**Complete review loop implementation:**

```python
import json
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum

class ReviewVerdict(Enum):
    PASS = "pass"
    NEEDS_WORK = "needs_work"
    REJECT = "reject"

@dataclass
class ReviewFinding:
    severity: str       # "critical", "major", "minor", "suggestion"
    category: str       # "bug", "security", "performance", "style", "logic"
    description: str
    file_path: Optional[str] = None
    line_range: Optional[tuple] = None

@dataclass
class ReviewResult:
    verdict: ReviewVerdict
    findings: list[ReviewFinding]
    summary: str
    confidence: float   # 0.0 - 1.0

@dataclass
class ReviewLoopController:
    """Controls the Reviewer <-> Developer iteration loop."""
    max_rounds: int = 3
    min_rounds: int = 2
    convergence_threshold: float = 0.85  # Similarity threshold for convergence
    improvement_floor: float = 0.10      # Stop if improvement < 10%
    
    # Tracking
    round_results: list[ReviewResult] = field(default_factory=list)
    findings_per_round: list[int] = field(default_factory=list)
    
    def should_continue(self, current_round: int, review: ReviewResult) -> tuple[bool, str]:
        """Decides whether to run another review round."""
        self.round_results.append(review)
        self.findings_per_round.append(len(review.findings))
        
        # Always run minimum rounds
        if current_round < self.min_rounds:
            return True, f"min_rounds_not_met ({current_round} < {self.min_rounds})"
        
        # Hard cap
        if current_round >= self.max_rounds:
            return False, f"max_rounds_reached ({current_round} >= {self.max_rounds})"
        
        # Convergence: reviewer says PASS
        if review.verdict == ReviewVerdict.PASS:
            return False, "reviewer_passed"
        
        # Convergence: zero findings
        if len(review.findings) == 0 and current_round >= self.min_rounds:
            return False, "zero_findings"
        
        # Diminishing returns: findings not decreasing
        if len(self.findings_per_round) >= 2:
            prev = self.findings_per_round[-2]
            curr = self.findings_per_round[-1]
            if prev > 0:
                improvement_rate = (prev - curr) / prev
                if improvement_rate < self.improvement_floor:
                    return False, f"diminishing_returns (improvement={improvement_rate:.1%})"
            
            # Findings increasing = regression
            if curr > prev:
                return False, f"regression_detected (findings: {prev} -> {curr})"
        
        # Stochastic drift: findings oscillating (same count for 2+ rounds)
        if len(self.findings_per_round) >= 3:
            last_three = self.findings_per_round[-3:]
            if last_three[0] == last_three[2] and last_three[0] != last_three[1]:
                return False, "oscillation_detected"
        
        return True, "continue"
    
    def summary(self) -> dict:
        return {
            "total_rounds": len(self.round_results),
            "findings_per_round": self.findings_per_round,
            "final_verdict": self.round_results[-1].verdict.value if self.round_results else None,
            "total_findings_found": sum(self.findings_per_round),
            "convergence_trajectory": [
                f"Round {i+1}: {n} findings" 
                for i, n in enumerate(self.findings_per_round)
            ],
        }

async def run_review_loop(
    code: str,
    reviewer_fn,   # async fn(code) -> ReviewResult
    developer_fn,  # async fn(code, findings) -> str (revised code)
    controller: ReviewLoopController = None,
    budget: AgentBudget = None,
) -> dict:
    """Execute the full review loop with convergence detection."""
    controller = controller or ReviewLoopController()
    current_code = code
    round_num = 0
    
    while True:
        round_num += 1
        
        # Budget check
        if budget:
            ok, reason = budget.check_budget()
            if not ok:
                return {
                    "code": current_code,
                    "stopped_reason": f"budget_{reason}",
                    "rounds_completed": round_num - 1,
                    **controller.summary(),
                }
        
        # Review phase
        review = await reviewer_fn(current_code)
        
        # Check convergence
        should_continue, reason = controller.should_continue(round_num, review)
        
        if not should_continue:
            return {
                "code": current_code,
                "stopped_reason": reason,
                "rounds_completed": round_num,
                **controller.summary(),
            }
        
        # Development phase: apply fixes
        current_code = await developer_fn(current_code, review.findings)
    
    # Unreachable, but for safety:
    return {"code": current_code, "rounds_completed": round_num, **controller.summary()}
```

### 3.2 Convergence Detection Patterns

Beyond the simple findings-count approach, several convergence signals can be combined:

```python
from difflib import SequenceMatcher

@dataclass  
class ConvergenceDetector:
    """Multi-signal convergence detection for agent loops."""
    
    # Semantic similarity between consecutive outputs
    similarity_history: list[float] = field(default_factory=list)
    similarity_ceiling: float = 0.90  # Above this = converged
    
    # Quality score tracking (from evaluator)
    quality_scores: list[float] = field(default_factory=list)
    quality_plateau_window: int = 3
    quality_plateau_epsilon: float = 0.02  # 2% improvement is noise
    
    # Findings tracking
    findings_counts: list[int] = field(default_factory=list)
    
    def update(self, output: str, prev_output: str = None, 
               quality_score: float = None, findings_count: int = None):
        """Feed new round data. Call after each iteration."""
        
        if prev_output:
            sim = SequenceMatcher(None, output, prev_output).ratio()
            self.similarity_history.append(sim)
        
        if quality_score is not None:
            self.quality_scores.append(quality_score)
        
        if findings_count is not None:
            self.findings_counts.append(findings_count)
    
    def is_converged(self) -> tuple[bool, dict]:
        """Returns (converged, evidence_dict)."""
        evidence = {}
        signals = []
        
        # Signal 1: Output similarity plateau
        if len(self.similarity_history) >= 2:
            recent_sim = self.similarity_history[-1]
            evidence["latest_similarity"] = round(recent_sim, 3)
            if recent_sim >= self.similarity_ceiling:
                signals.append("output_similarity_ceiling")
        
        # Signal 2: Quality score plateau
        if len(self.quality_scores) >= self.quality_plateau_window:
            window = self.quality_scores[-self.quality_plateau_window:]
            max_delta = max(window) - min(window)
            evidence["quality_window_delta"] = round(max_delta, 3)
            if max_delta < self.quality_plateau_epsilon:
                signals.append("quality_plateau")
        
        # Signal 3: Zero findings
        if self.findings_counts and self.findings_counts[-1] == 0:
            signals.append("zero_findings")
            evidence["last_findings_count"] = 0
        
        # Signal 4: Findings increasing (regression)
        if len(self.findings_counts) >= 2:
            if self.findings_counts[-1] > self.findings_counts[-2]:
                signals.append("regression")
                evidence["findings_trend"] = "increasing"
        
        evidence["signals"] = signals
        
        # Converged if any strong signal fires
        strong_signals = {"zero_findings", "output_similarity_ceiling", "regression"}
        converged = bool(signals and (set(signals) & strong_signals))
        
        return converged, evidence
```

### 3.3 Structured Handoff Format Between Turns

When agents hand off work to each other, the handoff payload must be machine-parseable, self-describing, and include enough context to continue without the full conversation history.

**Recommended JSON handoff schema:**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AgentHandoff",
  "type": "object",
  "required": ["handoff_id", "from_agent", "to_agent", "task", "context", "constraints"],
  "properties": {
    "handoff_id": {
      "type": "string",
      "description": "Unique ID for this handoff (UUID v4)"
    },
    "from_agent": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "role": {"type": "string"},
        "model_used": {"type": "string"}
      }
    },
    "to_agent": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "role": {"type": "string"},
        "preferred_model": {"type": "string"}
      }
    },
    "task": {
      "type": "object",
      "required": ["action", "description"],
      "properties": {
        "action": {
          "type": "string",
          "enum": ["review", "fix", "generate", "answer_question", "approve", "reject"]
        },
        "description": {"type": "string"},
        "acceptance_criteria": {
          "type": "array",
          "items": {"type": "string"}
        },
        "priority": {
          "type": "string",
          "enum": ["critical", "high", "medium", "low"]
        }
      }
    },
    "context": {
      "type": "object",
      "properties": {
        "summary": {
          "type": "string",
          "description": "Compressed summary of conversation history (max 500 tokens)"
        },
        "artifacts": {
          "type": "array",
          "description": "File paths or inline content produced so far",
          "items": {
            "type": "object",
            "properties": {
              "type": {"type": "string", "enum": ["file", "inline", "reference"]},
              "path": {"type": "string"},
              "content": {"type": "string"},
              "description": {"type": "string"}
            }
          }
        },
        "decisions_made": {
          "type": "array",
          "description": "Key decisions from prior turns to preserve",
          "items": {"type": "string"}
        },
        "failed_approaches": {
          "type": "array",
          "description": "Approaches tried and failed (avoid repeating)",
          "items": {"type": "string"}
        }
      }
    },
    "constraints": {
      "type": "object",
      "properties": {
        "max_tokens_output": {"type": "integer"},
        "max_cost_usd": {"type": "number"},
        "max_wall_clock_seconds": {"type": "number"},
        "remaining_rounds": {"type": "integer"},
        "required_output_format": {"type": "string"}
      }
    },
    "iteration_state": {
      "type": "object",
      "properties": {
        "round_number": {"type": "integer"},
        "total_rounds_allowed": {"type": "integer"},
        "findings_history": {
          "type": "array",
          "items": {"type": "integer"}
        },
        "convergence_signals": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },
    "questions": {
      "type": "array",
      "description": "Questions from one agent to another that need answers",
      "items": {
        "type": "object",
        "required": ["question", "blocking"],
        "properties": {
          "id": {"type": "string"},
          "question": {"type": "string"},
          "blocking": {
            "type": "boolean",
            "description": "If true, receiving agent must answer before proceeding"
          },
          "context": {"type": "string"},
          "suggested_answer": {"type": "string"}
        }
      }
    }
  }
}
```

**Practical Python implementation:**

```python
from dataclasses import dataclass, field, asdict
from typing import Optional
import uuid
import json

@dataclass
class AgentHandoff:
    """Structured handoff between agents in a multi-turn loop."""
    from_agent_id: str
    from_agent_role: str
    to_agent_id: str
    to_agent_role: str
    action: str  # "review", "fix", "generate", "answer_question"
    description: str
    
    # Context (compressed)
    summary: str = ""
    artifacts: list[dict] = field(default_factory=list)
    decisions_made: list[str] = field(default_factory=list)
    failed_approaches: list[str] = field(default_factory=list)
    
    # Constraints
    max_tokens: int = 4000
    max_cost_usd: float = 0.50
    remaining_rounds: int = 3
    
    # Iteration state
    round_number: int = 1
    findings_history: list[int] = field(default_factory=list)
    
    # Questions
    questions: list[dict] = field(default_factory=list)
    
    # Metadata
    handoff_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_prompt_context(self) -> str:
        """Convert handoff to a context block for the receiving agent's prompt."""
        parts = [
            f"## Task Handoff (Round {self.round_number})",
            f"**From:** {self.from_agent_role} ({self.from_agent_id})",
            f"**Action:** {self.action}",
            f"**Description:** {self.description}",
        ]
        
        if self.summary:
            parts.append(f"\n### Prior Context\n{self.summary}")
        
        if self.decisions_made:
            parts.append("\n### Decisions Already Made")
            for d in self.decisions_made:
                parts.append(f"- {d}")
        
        if self.failed_approaches:
            parts.append("\n### Failed Approaches (Do Not Repeat)")
            for f in self.failed_approaches:
                parts.append(f"- {f}")
        
        if self.questions:
            parts.append("\n### Questions Requiring Answers")
            for q in self.questions:
                blocking = " [BLOCKING]" if q.get("blocking") else ""
                parts.append(f"- {q['question']}{blocking}")
        
        parts.append(f"\n### Constraints")
        parts.append(f"- Max output: {self.max_tokens} tokens")
        parts.append(f"- Budget remaining: ${self.max_cost_usd:.2f}")
        parts.append(f"- Rounds remaining: {self.remaining_rounds}")
        
        if self.findings_history:
            parts.append(f"- Findings trend: {' -> '.join(str(f) for f in self.findings_history)}")
        
        return "\n".join(parts)
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)
    
    def to_file(self, path: str):
        with open(path, 'w') as f:
            f.write(self.to_json())
    
    @classmethod
    def from_file(cls, path: str) -> 'AgentHandoff':
        with open(path, 'r') as f:
            data = json.loads(f.read())
        return cls(**data)
```

### 3.4 Question-Answer Protocol Between Agents

When one agent has questions for another, routing depends on whether the question is blocking (must be answered before proceeding) or non-blocking (can be answered asynchronously).

```python
from enum import Enum

class QuestionPriority(Enum):
    BLOCKING = "blocking"       # Must answer before agent can proceed
    HIGH = "high"               # Should answer this turn if possible
    LOW = "low"                 # Can answer whenever convenient
    INFORMATIONAL = "info"      # No answer needed, just FYI

@dataclass
class AgentQuestion:
    question: str
    priority: QuestionPriority
    from_agent: str
    to_agent: str
    context: str = ""
    suggested_answer: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

class QuestionRouter:
    """Routes questions between agents in a multi-agent system."""
    
    def __init__(self):
        self.pending: dict[str, list[AgentQuestion]] = defaultdict(list)
        self.answered: dict[str, str] = {}  # question_id -> answer
    
    def ask(self, question: AgentQuestion):
        """Submit a question to another agent."""
        self.pending[question.to_agent].append(question)
    
    def get_questions_for(self, agent_id: str) -> list[AgentQuestion]:
        """Get all pending questions for an agent, blocking first."""
        questions = self.pending.get(agent_id, [])
        return sorted(questions, key=lambda q: 
            0 if q.priority == QuestionPriority.BLOCKING else
            1 if q.priority == QuestionPriority.HIGH else 2
        )
    
    def answer(self, question_id: str, answer: str):
        self.answered[question_id] = answer
        # Remove from pending
        for agent_questions in self.pending.values():
            self.pending[agent_questions] = [
                q for q in agent_questions if q.id != question_id
            ]
    
    def has_blocking_questions(self, agent_id: str) -> bool:
        return any(
            q.priority == QuestionPriority.BLOCKING 
            for q in self.pending.get(agent_id, [])
        )
```

---

## 4. State Persistence Across Turns

### 4.1 Maintaining Context When Calling External Models

Each external model has its own context window limit and no inherent memory of previous calls. The orchestrator must manage context explicitly.

**Context window sizes (as of 2026-04):**

| Model | Context Window | Effective Window* |
|-------|---------------|-------------------|
| Claude Opus 4 | 200K tokens | ~180K reliable |
| Claude Sonnet 4 | 200K tokens | ~180K reliable |
| GPT-4o | 128K tokens | ~100K reliable |
| Gemini 2.5 Pro | 1M tokens | ~500K reliable |
| Claude Haiku 3.5 | 200K tokens | ~180K reliable |

*"Effective window" reflects research showing models lose accuracy when key information sits in the middle of context (the "Lost in the Middle" problem). Accuracy falls over 30% for mid-context information.

### 4.2 Token Window Management: Summarization Strategies

JetBrains Research (December 2025) tested two approaches on software engineering agents and found surprising results:

**Approach 1: Observation Masking** (recommended as primary)
- Replace older environment observations with placeholders while preserving the agent's reasoning and action history
- 52% average cost savings with Qwen3-Coder 480B
- Performance matched or exceeded LLM summarization in 4/5 test scenarios

**Approach 2: LLM Summarization**
- Deploy a separate model to compress interaction histories into summaries
- Caused agents to run 15% longer (52 vs. 45 turns on average)
- Summary generation consumed over 7% of total costs
- Summaries may "smooth over" stopping signals, encouraging unnecessary continuation

**Recommended hybrid approach:**

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ContextWindowManager:
    """Manages context for multi-turn external model calls."""
    max_context_tokens: int = 100_000  # Conservative limit for the target model
    reserved_for_output: int = 4_000
    reserved_for_system: int = 2_000
    
    # History
    system_prompt: str = ""
    turns: list[dict] = field(default_factory=list)  # [{role, content, tokens, important}]
    
    # Summarization
    summary: str = ""
    summary_covers_through_turn: int = 0
    
    def available_tokens(self) -> int:
        """Tokens available for conversation history."""
        return (self.max_context_tokens - 
                self.reserved_for_output - 
                self.reserved_for_system - 
                self._estimate_tokens(self.summary))
    
    def add_turn(self, role: str, content: str, important: bool = False):
        """Add a conversation turn. Important turns resist eviction."""
        self.turns.append({
            "role": role,
            "content": content,
            "tokens": self._estimate_tokens(content),
            "important": important,
            "turn_number": len(self.turns),
        })
    
    def build_messages(self) -> list[dict]:
        """Build the message array for the API call, fitting within context window."""
        messages = []
        
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        # Add summary of older turns if it exists
        if self.summary:
            messages.append({
                "role": "system",
                "content": f"Summary of prior conversation:\n{self.summary}"
            })
        
        # Add recent turns, newest first, until we run out of budget
        budget = self.available_tokens()
        included_turns = []
        
        for turn in reversed(self.turns[self.summary_covers_through_turn:]):
            if turn["tokens"] <= budget:
                included_turns.insert(0, {"role": turn["role"], "content": turn["content"]})
                budget -= turn["tokens"]
            elif turn["important"]:
                # Important turns get observation-masked (keep role + first 200 chars)
                masked = turn["content"][:200] + "\n[... content truncated for context limit ...]"
                masked_tokens = self._estimate_tokens(masked)
                if masked_tokens <= budget:
                    included_turns.insert(0, {"role": turn["role"], "content": masked})
                    budget -= masked_tokens
        
        messages.extend(included_turns)
        return messages
    
    async def compress_if_needed(self, summarizer_fn=None):
        """
        Compress old turns when context is >70% full.
        Uses observation masking by default; LLM summarization as supplement.
        """
        total_turn_tokens = sum(t["tokens"] for t in self.turns[self.summary_covers_through_turn:])
        
        if total_turn_tokens < self.available_tokens() * 0.7:
            return  # No compression needed
        
        # Phase 1: Observation masking (replace old non-important tool outputs with placeholders)
        mask_boundary = len(self.turns) - 5  # Keep last 5 turns verbatim
        for i, turn in enumerate(self.turns[self.summary_covers_through_turn:mask_boundary]):
            idx = i + self.summary_covers_through_turn
            if not turn["important"] and turn["tokens"] > 200:
                # Mask the content
                self.turns[idx]["content"] = (
                    f"[Turn {turn['turn_number']}: {turn['role']} - "
                    f"{turn['content'][:100]}... (masked, {turn['tokens']} tokens original)]"
                )
                self.turns[idx]["tokens"] = self._estimate_tokens(self.turns[idx]["content"])
        
        # Phase 2: If still over budget, summarize oldest masked turns
        total_turn_tokens = sum(t["tokens"] for t in self.turns[self.summary_covers_through_turn:])
        
        if total_turn_tokens > self.available_tokens() * 0.7 and summarizer_fn:
            # Summarize the oldest 50% of turns
            midpoint = self.summary_covers_through_turn + (len(self.turns) - self.summary_covers_through_turn) // 2
            turns_to_summarize = self.turns[self.summary_covers_through_turn:midpoint]
            
            history_text = "\n".join(
                f"{t['role']}: {t['content']}" for t in turns_to_summarize
            )
            
            new_summary = await summarizer_fn(
                f"Summarize the key points, decisions, and outcomes from this conversation "
                f"segment. Preserve any technical details, file paths, and action items. "
                f"Be concise (max 300 words):\n\n"
                f"Previous summary: {self.summary}\n\n"
                f"New segment:\n{history_text}"
            )
            
            self.summary = new_summary
            self.summary_covers_through_turn = midpoint
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation: ~4 chars per token for English."""
        return len(text) // 4 if text else 0
```

### 4.3 File-Based State vs. In-Memory State

Your existing file-based pattern is well-suited for the startup-engine use case. Here is a comparison with trade-offs:

| Aspect | File-Based State | In-Memory State |
|--------|-----------------|----------------|
| **Survives process crash** | Yes (durability) | No |
| **Survives machine reboot** | Yes (if on disk) | No |
| **Cross-agent sharing** | Via filesystem (simple) | Requires IPC or shared memory |
| **Speed** | ~1-10ms per read/write (SSD) | Sub-microsecond |
| **Debugging** | Easy -- just read the files | Requires debugger attachment |
| **Size limits** | Disk space (effectively unlimited) | RAM (can be constrained) |
| **Concurrency** | Needs file locking or atomic writes | Needs mutex/locks |
| **Git integration** | Natural -- commit checkpoints | Requires serialization step |

**Recommended: File-based state with structured directory layout.**

This matches the patterns proven in Anthropic's C compiler project (16 parallel agents using Git as coordination mechanism) and the Ralph Loop pattern.

```
.startup-engine/
├── state/
│   ├── session.json              # Current session metadata
│   ├── agents/
│   │   ├── {agent-id}/
│   │   │   ├── status.json       # running | complete | failed | timeout
│   │   │   ├── budget.json       # Token/cost tracking
│   │   │   ├── handoff-in.json   # Last handoff received
│   │   │   ├── handoff-out.json  # Last handoff sent
│   │   │   ├── output.md         # Latest output artifact
│   │   │   └── history.jsonl     # Append-only log of all turns
│   │   └── ...
│   ├── loops/
│   │   ├── {loop-id}/
│   │   │   ├── config.json       # Max rounds, convergence params
│   │   │   ├── round-1.json      # Review result + findings
│   │   │   ├── round-2.json
│   │   │   └── convergence.json  # Why the loop stopped
│   │   └── ...
│   └── cost-log.jsonl            # Append-only cost tracking
└── checkpoints/
    ├── checkpoint-001.json       # Full state snapshot
    └── checkpoint-002.json
```

**Atomic file writes for concurrency safety:**

```python
import os
import json
import tempfile

def atomic_write_json(path: str, data: dict):
    """Write JSON atomically -- prevents corruption on crash."""
    dir_name = os.path.dirname(path)
    with tempfile.NamedTemporaryFile(
        mode='w', 
        dir=dir_name, 
        suffix='.tmp', 
        delete=False
    ) as tmp:
        json.dump(data, tmp, indent=2)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = tmp.name
    
    os.replace(tmp_path, path)  # Atomic on POSIX

def append_jsonl(path: str, entry: dict):
    """Append to JSONL log -- append is atomic on most filesystems."""
    with open(path, 'a') as f:
        f.write(json.dumps(entry) + '\n')
```

### 4.4 Recovery After Interruption

When a multi-turn exchange is interrupted (network drop, process kill, API timeout), the system must resume without re-executing completed work.

**Recovery strategy hierarchy:**

| Framework | Recovery Mechanism | Complexity | Best For |
|-----------|-------------------|-----------|----------|
| **File-based checkpoints** | Read last checkpoint, resume from there | Low | Bash/Python scripts from Claude Code |
| **LangGraph checkpointing** | Node-level state saved to PostgreSQL/SQLite | Medium | Python agent loops |
| **Temporal durable execution** | Event history replay, automatic resume | High | Mission-critical, long-running workflows |

**Lightweight checkpoint/resume for Claude Code scripts:**

```python
import json
import os
from pathlib import Path
from datetime import datetime, timezone

class CheckpointManager:
    """Simple file-based checkpoint/resume for agent workflows."""
    
    def __init__(self, checkpoint_dir: str = ".startup-engine/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, workflow_id: str, step: str, state: dict):
        """Save a checkpoint at the current step."""
        checkpoint = {
            "workflow_id": workflow_id,
            "step": step,
            "state": state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": 1,
        }
        
        path = self.checkpoint_dir / f"{workflow_id}.json"
        atomic_write_json(str(path), checkpoint)
    
    def load(self, workflow_id: str) -> dict | None:
        """Load the latest checkpoint for a workflow."""
        path = self.checkpoint_dir / f"{workflow_id}.json"
        if not path.exists():
            return None
        
        with open(path) as f:
            return json.load(f)
    
    def resume_or_start(self, workflow_id: str, steps: list[str]) -> tuple[str, dict]:
        """
        Returns (next_step, state).
        If checkpoint exists, returns the step AFTER the last completed one.
        If no checkpoint, returns the first step with empty state.
        """
        checkpoint = self.load(workflow_id)
        
        if checkpoint is None:
            return steps[0], {}
        
        completed_step = checkpoint["step"]
        state = checkpoint["state"]
        
        try:
            completed_index = steps.index(completed_step)
            if completed_index + 1 < len(steps):
                return steps[completed_index + 1], state
            else:
                return "complete", state  # All steps done
        except ValueError:
            # Unknown step; start over
            return steps[0], {}

# Usage example for a multi-step agent workflow:
async def run_resumable_workflow():
    checkpointer = CheckpointManager()
    workflow_id = "startup-feature-auth-system"
    steps = ["research", "requirements", "design", "implement", "test", "deploy"]
    
    next_step, state = checkpointer.resume_or_start(workflow_id, steps)
    
    if next_step == "complete":
        print("Workflow already complete.")
        return state
    
    print(f"Resuming from step: {next_step}")
    
    for step in steps[steps.index(next_step):]:
        print(f"Executing step: {step}")
        
        # Execute the step (each step is an agent call)
        result = await execute_step(step, state)
        state[step] = result
        
        # Checkpoint after each step
        checkpointer.save(workflow_id, step, state)
    
    return state
```

**Temporal for production-critical recovery:**

For workflows that absolutely cannot lose progress, Temporal provides event-history replay:

```python
from temporalio import workflow
from temporalio.common import RetryPolicy
import asyncio

@workflow.defn
class AgentReviewWorkflow:
    """Durable multi-turn review loop with automatic recovery."""
    
    @workflow.run
    async def run(self, task: dict) -> dict:
        code = task["code"]
        max_rounds = task.get("max_rounds", 3)
        
        for round_num in range(1, max_rounds + 1):
            # Each activity is a checkpoint -- if the worker crashes,
            # Temporal replays and skips completed activities
            
            review = await workflow.execute_activity(
                run_code_review,
                args=[code, round_num],
                start_to_close_timeout=asyncio.timedelta(seconds=120),
                retry_policy=RetryPolicy(
                    initial_interval=asyncio.timedelta(seconds=2),
                    backoff_coefficient=2.0,
                    maximum_interval=asyncio.timedelta(seconds=30),
                    maximum_attempts=3,
                ),
            )
            
            if review["verdict"] == "pass":
                return {"code": code, "rounds": round_num, "verdict": "pass"}
            
            # Apply fixes
            code = await workflow.execute_activity(
                apply_review_fixes,
                args=[code, review["findings"]],
                start_to_close_timeout=asyncio.timedelta(seconds=120),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
        
        return {"code": code, "rounds": max_rounds, "verdict": "max_rounds_reached"}
```

---

## 5. Recommended Architecture for Startup-Engine

Based on all research findings, here is the recommended architecture combining all patterns:

### 5.1 Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                 Claude Orchestrator                    │
│  (startup-engine COO agent)                           │
│                                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │
│  │ Cost     │  │ Kill     │  │ Checkpoint        │    │
│  │ Monitor  │  │ Switch   │  │ Manager           │    │
│  └──────────┘  └──────────┘  └──────────────────┘    │
│                                                        │
│  ┌──────────────────────────────────────────────┐     │
│  │           Fallback Chain Router                │     │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐       │     │
│  │  │ Claude  │→ │ GPT-4o  │→ │ Gemini  │       │     │
│  │  │ breaker │  │ breaker │  │ breaker │       │     │
│  │  └─────────┘  └─────────┘  └─────────┘       │     │
│  └──────────────────────────────────────────────┘     │
│                                                        │
│  ┌──────────────────────────────────────────────┐     │
│  │           Review Loop Controller              │     │
│  │  Reviewer → Developer → Reviewer (max N)      │     │
│  │  + ConvergenceDetector                        │     │
│  │  + OutputValidator                            │     │
│  └──────────────────────────────────────────────┘     │
│                                                        │
│  ┌──────────────────────────────────────────────┐     │
│  │           Context Window Manager              │     │
│  │  Observation masking + selective summary       │     │
│  └──────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────┘
         ↕ File-based state (.startup-engine/state/)
         ↕ Git commits as durable checkpoints
```

### 5.2 Configuration Presets

```python
# config/resilience.py -- Import in startup-engine scripts

RESILIENCE_CONFIG = {
    "circuit_breaker": {
        "fail_max": 5,
        "reset_timeout_seconds": 30,
        "success_threshold": 2,
        "exclude_status_codes": [400, 401, 403, 404],
    },
    "retry": {
        "max_retries": 3,
        "base_delay_seconds": 1.0,
        "max_delay_seconds": 30.0,
        "jitter": True,
        "retryable_status_codes": [429, 500, 502, 503, 504],
    },
    "timeout": {
        "simple_task_seconds": 30,
        "complex_task_seconds": 60,
        "long_generation_seconds": 120,
        "agent_wall_clock_seconds": 300,
    },
    "budget": {
        "default_max_cost_per_task_usd": 1.00,
        "daily_budget_usd": 50.00,
        "alert_thresholds": [0.50, 0.75, 0.90],
    },
    "review_loop": {
        "default_max_rounds": 3,
        "min_rounds": 2,
        "convergence_similarity_threshold": 0.85,
        "improvement_floor_pct": 0.10,
    },
    "output_validation": {
        "similarity_threshold": 0.85,
        "min_output_length": 10,
        "max_consecutive_similar": 2,
        "max_tool_call_repeats": 3,
    },
    "context_management": {
        "compression_trigger_pct": 0.70,  # Compress when 70% full
        "keep_recent_turns": 5,           # Always keep last 5 turns verbatim
        "max_summary_tokens": 500,
    },
    "fallback_chains": {
        "strong_reasoning": ["claude-opus-4", "gpt-4o", "gemini-2.5-pro", "claude-sonnet-4"],
        "fast_generation": ["claude-haiku-3.5", "gpt-4o-mini", "gemini-2.0-flash", "claude-sonnet-4"],
        "code_generation": ["claude-sonnet-4", "gpt-4o", "gemini-2.5-pro"],
        "review_evaluation": ["claude-opus-4", "gpt-4o", "claude-sonnet-4"],
    },
}
```

### 5.3 Decision Matrix: When to Use What

| Situation | Primary Pattern | Fallback Pattern |
|-----------|----------------|------------------|
| External API returns 429 | Exponential backoff with jitter | Circuit breaker opens after 5 fails |
| External API returns 500 | Retry once, then fallback chain | Graceful degradation with cached result |
| Agent running > 5 minutes | Wall-clock timeout kills agent | Checkpoint state, queue for resume |
| Token budget exhausted | Switch to cheaper model in fallback chain | Return partial result with degradation flag |
| Review loop not converging | Diminishing returns detector stops at round 3 | Accept current state as "best effort" |
| Agent output is repetitive | OutputValidator detects loop at 2 repeats | Kill agent, return last unique output |
| All models unavailable | Return cached result if available | Queue task, notify orchestrator |
| Network interruption mid-turn | Checkpoint manager saves state | Resume from last checkpoint on reconnect |

---

## 6. Sources

### Framework Documentation
- [PyBreaker - Python Circuit Breaker](https://github.com/danielfm/pybreaker) -- Production Python circuit breaker with Redis backing and event listeners
- [LiteLLM Router & Budget Routing](https://docs.litellm.ai/docs/routing) -- Multi-model routing with cost tracking and per-provider budgets
- [LiteLLM Budget Routing](https://docs.litellm.ai/docs/proxy/provider_budget_routing) -- Per-provider and per-model budget configuration
- [Resilient LLM Library](https://github.com/gitcommitshow/resilient-llm) -- TypeScript multi-LLM orchestration with circuit breakers and rate limiting
- [Anthropic Claude Agent SDK](https://deepwiki.com/anthropics/claude-agent-sdk-python/6.3-resource-limits-and-cost-control) -- max_budget_usd, max_turns, and cost tracking via ResultMessage
- [OpenAI Agents SDK Guardrails](https://openai.github.io/openai-agents-python/guardrails/) -- Input, output, and tool guardrails for agent validation
- [LangGraph Thinking Guide](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph) -- Node-level checkpointing and conditional error routing
- [Temporal Durable AI Agents Tutorial](https://learn.temporal.io/tutorials/ai/durable-ai-agent/) -- Building resumable AI agents with event-history replay

### Engineering Blogs & Research
- [Anthropic: Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) -- Canonical patterns: evaluator-optimizer, orchestrator-worker, routing
- [Portkey: Retries, Fallbacks, and Circuit Breakers](https://portkey.ai/blog/retries-fallbacks-and-circuit-breakers-in-llm-apps/) -- Layered resilience strategy for LLM apps
- [Maxim: Retries, Fallbacks, and Circuit Breakers Production Guide](https://www.getmaxim.ai/articles/retries-fallbacks-and-circuit-breakers-in-llm-apps-a-production-guide/) -- Bifrost fallback chain architecture
- [Maxim: Failover Routing Strategies](https://www.getmaxim.ai/articles/failover-routing-strategies-for-production-ai-systems/) -- Provider-level and model-level degradation chains
- [JetBrains Research: Efficient Context Management](https://blog.jetbrains.com/research/2025/12/efficient-context-management/) -- Observation masking vs. LLM summarization (52% cost savings)
- [SitePoint: Claude API Circuit Breaker](https://www.sitepoint.com/claude-api-circuit-breaker-pattern/) -- Threshold configuration rationale and chaos testing
- [Medium: Circuit Breaker for LLM with Retry](https://medium.com/@spacholski99/circuit-breaker-for-llm-with-retry-and-backoff-anthropic-api-example-typescript-1f99a0a0cf87) -- Complete TypeScript implementation
- [Google Cloud: SRE Best Practices for LLMs](https://medium.com/google-cloud/building-bulletproof-llm-applications-a-guide-to-applying-sre-best-practices-1564b72fd22e) -- SRE patterns applied to LLM systems
- [Kinde: Orchestrating Multi-Step Agents](https://www.kinde.com/learn/ai-for-software-engineering/ai-devops/orchestrating-multi-step-agents-temporal-dagster-langgraph-patterns-for-long-running-work/) -- Temporal vs. Dagster vs. LangGraph comparison with code examples
- [Zylos: AI Agent Workflow Checkpointing](https://zylos.ai/research/2026-03-04-ai-agent-workflow-checkpointing-resumability) -- Production checklist for checkpoint/resume systems

### Convergence & Iteration Research
- [Iterative Review-Fix Loops Remove LLM Hallucinations](https://dev.to/yannick555/iterative-review-fix-loops-remove-llm-hallucinations-and-there-is-a-formula-for-it-4ee8) -- Mathematical formula: Acc_t = Upp - alpha^t * (Upp - Acc_0); rounds 1-2 capture 75% of improvement
- [Ralph Loop Pattern](https://asdlc.io/patterns/ralph-loop/) -- Persistence pattern for autonomous AI agents with convergence mechanism P(C) = 1 - (1 - p_success)^n
- [Anthropic Cookbook: Evaluator-Optimizer Pattern](https://github.com/anthropics/anthropic-cookbook/blob/main/patterns/agents/evaluator_optimizer.ipynb) -- Reference implementation from Anthropic

### Agent Communication Protocols
- [LangChain Agent Protocol](https://github.com/langchain-ai/agent-protocol) -- Framework-agnostic agent API standard
- [Cleanlab: TLM Structured Outputs Benchmark](https://cleanlab.ai/blog/tlm-structured-outputs-benchmark/) -- Trust scoring detects output errors with 25% greater precision than LLM-as-judge

### Cost & Observability
- [AgentPatch: The Real Cost of Running AI Agents](https://agentpatch.ai/blog/cost-of-running-ai-agents/) -- Production cost patterns and budget strategies
- [Braintrust: Best LLM Monitoring Tools 2026](https://www.braintrust.dev/articles/best-llm-monitoring-tools-2026) -- Observability tooling comparison
- [CallSphere: AI Agent Cost Optimization](https://callsphere.tech/blog/ai-agent-cost-optimization-strategies-production) -- Per-task cost caps and spend monitoring
- [Temporal: Durable Execution Meets AI](https://temporal.io/blog/durable-execution-meets-ai-why-temporal-is-the-perfect-foundation-for-ai) -- 1.86 trillion executions from AI companies
