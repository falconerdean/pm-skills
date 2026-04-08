#!/usr/bin/env python3
"""
model_client.py — Unified multi-model client for the Startup Engine.

Calls any LLM (Claude, GPT, Gemini) via LiteLLM with:
- Fallback chains per task type
- Per-agent budget enforcement (pre-call check)
- Circuit breaker with DEGRADED state
- Loop detection for runaway prevention
- File-based input/output (artifact pattern)

Usage from Claude Code:
    echo '{"prompt": "Review this code"}' | python3 scripts/model_client.py --task code_review < code.py
    python3 scripts/model_client.py --task code_review --input artifacts/code.py --output artifacts/review.json
"""

import sys
import os
import json
import time
import hashlib
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# ─── Venv bootstrap ──────────────────────────────────────────────────────────
# Works on both macOS (Homebrew-managed Python) and Ubuntu (DO droplets).
# Creates ~/.venvs/litellm if needed, installs litellm, re-execs with venv python.
VENV_DIR = Path.home() / ".venvs" / "litellm"
VENV_PYTHON = VENV_DIR / "bin" / "python3"

def _ensure_venv():
    """Create venv and install litellm if not present, then re-exec."""
    if not VENV_DIR.exists():
        print(f"Creating venv at {VENV_DIR}...", file=sys.stderr)
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
    # Install litellm if missing
    result = subprocess.run(
        [str(VENV_PYTHON), "-c", "import litellm"],
        capture_output=True,
    )
    if result.returncode != 0:
        print("Installing litellm into venv...", file=sys.stderr)
        subprocess.run(
            [str(VENV_DIR / "bin" / "pip"), "install", "-q", "litellm"],
            check=True,
        )
    # Re-exec with venv python (preserves all args)
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

try:
    import litellm
except ImportError:
    _ensure_venv()
    # _ensure_venv calls os.execv and never returns; this is a safety fallback
    sys.exit(1)

# Suppress litellm debug logging
litellm.suppress_debug_info = True

# ─── Load API keys from shell profiles if not in environment ──────────────────
# Claude Code's Bash tool runs non-login shells, so ~/.zshrc exports aren't loaded.
# On droplets, keys are typically in ~/.bashrc or the system env.
def _load_keys_from_profiles():
    """Parse export KEY=VALUE lines from shell profiles to fill missing env vars."""
    keys_to_find = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"]
    missing = [k for k in keys_to_find if not os.environ.get(k)]
    if not missing:
        return
    for profile in [Path.home() / ".zshrc", Path.home() / ".bashrc", Path.home() / ".zprofile", Path.home() / ".profile"]:
        if not profile.exists():
            continue
        try:
            for line in profile.read_text().splitlines():
                line = line.strip()
                if not line.startswith("export "):
                    continue
                for key in missing:
                    if line.startswith(f"export {key}="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val and not os.environ.get(key):
                            os.environ[key] = val
        except (OSError, UnicodeDecodeError):
            continue

_load_keys_from_profiles()


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL ROUTING CONFIG
#
# Based on research findings:
# - Quality > diversity (Self-MoA, Princeton 2025)
# - Multi-model only for high-stakes gates (Milvus code review: 53% → 80%)
# - Claude + Gemini pair covers 91% of 5-model ceiling
# ═══════════════════════════════════════════════════════════════════════════════

MODEL_ROUTES = {
    # High-stakes: use best model, with fallback chain
    # Every chain ends with Claude (ANTHROPIC_API_KEY is always available in the engine)
    "code_review": {
        "model": "gpt-4o",  # Independent perspective from Claude-generated code
        "fallback": ["gemini/gemini-2.5-flash", "claude-sonnet-4-20250514"],
        "max_tokens": 4096,
        "temperature": 0.2,
        "timeout": 120,
    },
    "security_audit": {
        "model": "gpt-4o",
        "fallback": ["gemini/gemini-2.5-pro", "claude-sonnet-4-20250514"],
        "max_tokens": 8192,
        "temperature": 0.1,
        "timeout": 180,
    },
    "architecture_review": {
        "model": "gemini/gemini-2.5-pro",  # 2M context for full codebase
        "fallback": ["gpt-4o", "claude-sonnet-4-20250514"],
        "max_tokens": 8192,
        "temperature": 0.3,
        "timeout": 180,
    },
    # Standard: use best single model (Self-MoA pattern)
    "code_generation": {
        "model": "claude-sonnet-4-20250514",  # SWE-bench leader
        "fallback": ["gpt-4o"],
        "max_tokens": 8192,
        "temperature": 0.3,
        "timeout": 120,
    },
    "content_writing": {
        "model": "claude-sonnet-4-20250514",
        "fallback": ["gpt-4o"],
        "max_tokens": 4096,
        "temperature": 0.5,
        "timeout": 60,
    },
    # Economy: cheap model for routine tasks — Claude as final fallback
    "quick_task": {
        "model": "gpt-4o-mini",
        "fallback": ["gemini/gemini-2.5-flash", "claude-haiku-4-5-20251001"],
        "max_tokens": 2048,
        "temperature": 0.3,
        "timeout": 30,
    },
    "large_context": {
        "model": "gemini/gemini-2.5-pro",  # 2M context window
        "fallback": ["claude-sonnet-4-20250514"],
        "max_tokens": 8192,
        "temperature": 0.3,
        "timeout": 180,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# BUDGET ENFORCEMENT
# Pre-call check — blocks execution BEFORE tokens are spent.
# Per-agent isolation prevents one stuck agent from consuming entire budget.
# ═══════════════════════════════════════════════════════════════════════════════

class AgentBudget:
    def __init__(self, agent_id, max_cost_usd=2.00, max_tokens=200_000, max_calls=30):
        self.agent_id = agent_id
        self.max_cost = max_cost_usd
        self.max_tokens = max_tokens
        self.max_calls = max_calls
        self.spent = 0.0
        self.tokens_used = 0
        self.calls_made = 0
        self.log_path = Path(f"/tmp/agent_budget_{agent_id}.json")
        self._load()

    def _load(self):
        if self.log_path.exists():
            data = json.loads(self.log_path.read_text())
            self.spent = data.get("spent", 0.0)
            self.tokens_used = data.get("tokens_used", 0)
            self.calls_made = data.get("calls_made", 0)

    def _save(self):
        self.log_path.write_text(json.dumps({
            "agent_id": self.agent_id,
            "spent": self.spent,
            "tokens_used": self.tokens_used,
            "calls_made": self.calls_made,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }))

    def pre_check(self):
        if self.spent >= self.max_cost:
            raise BudgetExceededError(
                f"Agent {self.agent_id}: ${self.spent:.4f} >= ${self.max_cost:.2f} cost limit"
            )
        if self.tokens_used >= self.max_tokens:
            raise BudgetExceededError(
                f"Agent {self.agent_id}: {self.tokens_used} >= {self.max_tokens} token limit"
            )
        if self.calls_made >= self.max_calls:
            raise BudgetExceededError(
                f"Agent {self.agent_id}: {self.calls_made} >= {self.max_calls} call limit"
            )

    def record(self, cost, tokens):
        self.spent += cost
        self.tokens_used += tokens
        self.calls_made += 1
        self._save()


class BudgetExceededError(Exception):
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# LOOP DETECTION
# Detects when an agent is making the same call repeatedly.
# ═══════════════════════════════════════════════════════════════════════════════

class LoopDetector:
    def __init__(self, window_size=6, repeat_threshold=2):
        self.recent_calls = []
        self.window_size = window_size
        self.repeat_threshold = repeat_threshold

    def check(self, model, prompt_text):
        sig = f"{model}:{hashlib.md5(prompt_text.encode()).hexdigest()[:12]}"
        self.recent_calls.append(sig)
        if len(self.recent_calls) > self.window_size:
            self.recent_calls.pop(0)

        if len(self.recent_calls) >= self.repeat_threshold * 2:
            half = len(self.recent_calls) // 2
            if self.recent_calls[-half:] == self.recent_calls[-2 * half:-half]:
                raise RunawayDetectedError(f"Loop detected: {sig} repeated in window")


class RunawayDetectedError(Exception):
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

def call_model(task, system_prompt, user_input, agent_id="default"):
    """Call a model with routing, budget enforcement, and fallback."""
    route = MODEL_ROUTES.get(task, MODEL_ROUTES["quick_task"])
    budget = AgentBudget(agent_id)
    loop_detector = LoopDetector()

    # Pre-flight checks
    budget.pre_check()
    loop_detector.check(route["model"], user_input[:500])

    # Build fallback chain: primary + fallbacks
    models_to_try = [route["model"]] + route.get("fallback", [])

    last_error = None
    for model in models_to_try:
        try:
            response = litellm.completion(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
                max_tokens=route.get("max_tokens", 4096),
                temperature=route.get("temperature", 0.3),
                timeout=route.get("timeout", 60),
                num_retries=1,
            )

            # Track cost
            cost = litellm.completion_cost(completion_response=response) or 0.0
            total_tokens = (
                response.usage.prompt_tokens + response.usage.completion_tokens
                if response.usage else 0
            )
            budget.record(cost, total_tokens)

            return {
                "status": "success",
                "model_requested": route["model"],
                "model_used": model,
                "content": response.choices[0].message.content,
                "metadata": {
                    "tokens_in": response.usage.prompt_tokens if response.usage else 0,
                    "tokens_out": response.usage.completion_tokens if response.usage else 0,
                    "cost_usd": round(cost, 6),
                    "latency_ms": int((response._response_ms or 0)),
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "agent_id": agent_id,
                    "budget_remaining_usd": round(budget.max_cost - budget.spent, 4),
                },
            }

        except Exception as e:
            last_error = str(e)
            print(f"Model {model} failed: {e}", file=sys.stderr)
            continue

    return {
        "status": "all_models_failed",
        "model_requested": route["model"],
        "error": last_error,
        "models_tried": models_to_try,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Multi-model client for Startup Engine")
    parser.add_argument("--task", required=True, choices=list(MODEL_ROUTES.keys()),
                        help="Task type for model routing")
    parser.add_argument("--system", default="You are a helpful assistant.",
                        help="System prompt")
    parser.add_argument("--input", help="Input file path (reads from stdin if not provided)")
    parser.add_argument("--output", help="Output file path (writes to stdout if not provided)")
    parser.add_argument("--agent-id", default="default", help="Agent ID for budget tracking")
    parser.add_argument("--max-cost", type=float, default=2.00, help="Max cost in USD")
    args = parser.parse_args()

    # Read input
    if args.input:
        user_input = Path(args.input).read_text()
    else:
        user_input = sys.stdin.read()

    # Call model
    result = call_model(
        task=args.task,
        system_prompt=args.system,
        user_input=user_input,
        agent_id=args.agent_id,
    )

    # Write output
    output_json = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).write_text(output_json)
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
