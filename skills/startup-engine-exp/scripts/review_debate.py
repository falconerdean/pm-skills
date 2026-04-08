#!/usr/bin/env python3
"""
review_debate.py — Multi-model code review debate for the Startup Engine.

Implements the Team of Rivals pattern:
1. Independent first response (enforced structurally — no anchoring)
2. Cross-review (each model critiques the other's findings)
3. Synthesis (orchestrator classifies: AGREED / DISPUTED / UNIQUE)
4. Convergence check (stop when no new issues, max 3 rounds)

Based on research:
- Claude + Gemini pair covers 91% of 5-model ceiling (Milvus 2026)
- Independent first response prevents anchoring (Roundtable Principles)
- 2-3 rounds max — diminishing returns after round 2 (ICML 2024)
- Veto, not vote: any finding from either model is included unless disproven

Usage:
    python3 scripts/review_debate.py \
        --input artifacts/code_to_review.py \
        --output artifacts/debate_result.json \
        --agent-id "vp-eng-security-001" \
        --max-rounds 3
"""

import sys
import os
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, timezone
from string import Template

# ─── Venv bootstrap (works on macOS + Ubuntu DO droplets) ─────────────────────
VENV_DIR = Path.home() / ".venvs" / "litellm"
VENV_PYTHON = VENV_DIR / "bin" / "python3"

def _ensure_venv():
    """Create venv and install litellm if not present, then re-exec."""
    if not VENV_DIR.exists():
        print(f"Creating venv at {VENV_DIR}...", file=sys.stderr)
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
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
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

try:
    import litellm
except ImportError:
    _ensure_venv()
    sys.exit(1)

litellm.suppress_debug_info = True

# ─── Load API keys from shell profiles if not in environment ──────────────────
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
# DEBATE CONFIG
# Resolves models at runtime based on available API keys.
# Falls back to Claude-only review if no external keys are set.
# ═══════════════════════════════════════════════════════════════════════════════

def _pick_reviewer_a():
    """GPT-4o preferred for independent perspective; fall back to Claude."""
    if os.environ.get("OPENAI_API_KEY"):
        return "gpt-4o"
    return "claude-sonnet-4-20250514"

def _pick_reviewer_b():
    """Gemini preferred for different training data; fall back to Claude Haiku."""
    if os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"):
        return "gemini/gemini-2.5-flash"
    return "claude-haiku-4-5-20251001"

REVIEWER_A = _pick_reviewer_a()
REVIEWER_B = _pick_reviewer_b()
SYNTHESIZER = "claude-sonnet-4-20250514"  # Claude synthesizes — has full project context

_is_degraded = REVIEWER_A.startswith("claude") and REVIEWER_B.startswith("claude")
if _is_degraded:
    print("WARNING: No OPENAI_API_KEY or GOOGLE_API_KEY set. Running Claude-only review (degraded mode).", file=sys.stderr)
    print("Set OPENAI_API_KEY and/or GOOGLE_API_KEY for full multi-model debate.", file=sys.stderr)

MAX_ROUNDS = 3
TIMEOUT_PER_CALL = 120
MAX_COST_PER_DEBATE = 3.00  # USD

REVIEW_SYSTEM_PROMPT = """You are a senior code reviewer focused on finding real bugs, security issues, and correctness problems.

RULES:
- Only report issues you are confident about. No speculative or hypothetical findings.
- For each issue, provide: id, severity (critical/major/minor), file, line (if known), description, and suggested fix.
- Return valid JSON: {"findings": [...], "questions": [...], "summary": "..."}
- If you find no issues, return: {"findings": [], "questions": [], "summary": "No issues found."}
"""

CROSS_REVIEW_TEMPLATE = """You are reviewing another model's code review findings. For each finding:
1. AGREE if you independently confirm the issue exists
2. DISAGREE if the finding is incorrect or a false positive (explain why)
3. ADD any issues you see that the other reviewer missed

The other reviewer found:
$other_findings

Original code being reviewed:
$code

Return valid JSON with keys: agreements, disagreements, new_findings (each an array).
"""

SYNTHESIS_TEMPLATE = """You are synthesizing a code review debate between two independent reviewers.

Reviewer A (GPT) found: $review_a
Reviewer B (Gemini) found: $review_b
Cross-review A on B's findings: $cross_a
Cross-review B on A's findings: $cross_b

Classify each finding:
- AGREED: Both reviewers found it, or one found it and the other agreed in cross-review
- DISPUTED: One found it, the other disagreed with evidence
- UNIQUE: Only one found it, the other did not address it

For AGREED findings: include in final report with HIGH confidence
For DISPUTED findings: include BOTH perspectives, flag for human review
For UNIQUE findings: include with MEDIUM confidence

Return valid JSON with keys: verdict (pass/fail/needs_human_review), agreed_findings, disputed_findings, unique_findings, open_questions, summary, recommendation.
"""


# ═══════════════════════════════════════════════════════════════════════════════
# DEBATE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def call(model, system, user, timeout=TIMEOUT_PER_CALL):
    """Single model call with error handling."""
    try:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=4096,
            temperature=0.2,
            timeout=timeout,
            num_retries=1,
        )
        cost = litellm.completion_cost(completion_response=response) or 0.0
        tokens = (response.usage.prompt_tokens + response.usage.completion_tokens) if response.usage else 0
        return {
            "content": response.choices[0].message.content,
            "cost": cost,
            "tokens": tokens,
            "model": model,
        }
    except Exception as e:
        return {"content": json.dumps({"findings": [], "error": str(e)}), "cost": 0, "tokens": 0, "model": model}


def run_debate(code, max_rounds=MAX_ROUNDS, max_cost=MAX_COST_PER_DEBATE):
    """Run the full debate protocol."""
    total_cost = 0.0
    total_tokens = 0
    rounds = []

    for round_num in range(1, max_rounds + 1):
        round_data = {"round": round_num, "timestamp_utc": datetime.now(timezone.utc).isoformat()}

        # ── Step 1: Independent First Response (structural isolation) ──
        review_a = call(REVIEWER_A, REVIEW_SYSTEM_PROMPT, f"Review this code:\n\n{code}")
        review_b = call(REVIEWER_B, REVIEW_SYSTEM_PROMPT, f"Review this code:\n\n{code}")
        total_cost += review_a["cost"] + review_b["cost"]
        total_tokens += review_a["tokens"] + review_b["tokens"]

        round_data["review_a"] = {"model": REVIEWER_A, "content": review_a["content"]}
        round_data["review_b"] = {"model": REVIEWER_B, "content": review_b["content"]}

        # ── Step 2: Cross-Review (informed deliberation) ──
        cross_a = call(REVIEWER_A, "You are cross-reviewing another reviewer's findings.",
                       Template(CROSS_REVIEW_TEMPLATE).safe_substitute(other_findings=review_b["content"], code=code))
        cross_b = call(REVIEWER_B, "You are cross-reviewing another reviewer's findings.",
                       Template(CROSS_REVIEW_TEMPLATE).safe_substitute(other_findings=review_a["content"], code=code))
        total_cost += cross_a["cost"] + cross_b["cost"]
        total_tokens += cross_a["tokens"] + cross_b["tokens"]

        round_data["cross_review_a"] = cross_a["content"]
        round_data["cross_review_b"] = cross_b["content"]

        # ── Step 3: Synthesis (orchestrator decides) ──
        synthesis = call(SYNTHESIZER, "You are a lead engineer synthesizing a code review debate.",
                         Template(SYNTHESIS_TEMPLATE).safe_substitute(
                             review_a=review_a["content"],
                             review_b=review_b["content"],
                             cross_a=cross_a["content"],
                             cross_b=cross_b["content"],
                         ))
        total_cost += synthesis["cost"]
        total_tokens += synthesis["tokens"]

        round_data["synthesis"] = synthesis["content"]
        rounds.append(round_data)

        # ── Step 4: Convergence Check ──
        try:
            synthesis_data = json.loads(synthesis["content"])
            verdict = synthesis_data.get("verdict", "")
            if verdict == "pass":
                break
            # If no new findings compared to previous round, converged
            if round_num >= 2:
                prev_findings = _count_findings(rounds[-2].get("synthesis", "{}"))
                curr_findings = _count_findings(synthesis["content"])
                if curr_findings <= prev_findings:
                    break  # No new issues — converged
        except json.JSONDecodeError:
            pass  # Synthesis wasn't valid JSON, continue

        # Budget check
        if total_cost >= max_cost:
            print(f"Budget limit reached: ${total_cost:.4f}", file=sys.stderr)
            break

    return {
        "status": "complete",
        "rounds_completed": len(rounds),
        "max_rounds": max_rounds,
        "total_cost_usd": round(total_cost, 6),
        "total_tokens": total_tokens,
        "reviewer_a": REVIEWER_A,
        "reviewer_b": REVIEWER_B,
        "synthesizer": SYNTHESIZER,
        "rounds": rounds,
        "final_synthesis": rounds[-1]["synthesis"] if rounds else None,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


def _count_findings(synthesis_json_str):
    """Count total findings in a synthesis result."""
    try:
        data = json.loads(synthesis_json_str)
        return (len(data.get("agreed_findings", [])) +
                len(data.get("disputed_findings", [])) +
                len(data.get("unique_findings", [])))
    except (json.JSONDecodeError, TypeError):
        return 0


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Multi-model code review debate")
    parser.add_argument("--input", required=True, help="Code file to review")
    parser.add_argument("--output", help="Output file (stdout if not provided)")
    parser.add_argument("--agent-id", default="debate", help="Agent ID for tracking")
    parser.add_argument("--max-rounds", type=int, default=MAX_ROUNDS, help="Max debate rounds")
    parser.add_argument("--max-cost", type=float, default=MAX_COST_PER_DEBATE, help="Max cost USD")
    args = parser.parse_args()

    max_cost = args.max_cost

    code = Path(args.input).read_text()
    result = run_debate(code, max_rounds=args.max_rounds, max_cost=max_cost)

    output_json = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).write_text(output_json)
        print(f"Debate complete: {result['rounds_completed']} rounds, ${result['total_cost_usd']:.4f}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
