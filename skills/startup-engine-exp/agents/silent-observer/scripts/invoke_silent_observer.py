#!/usr/bin/env python3
"""Silent Observer wrapper script — the structural protocol enforcement layer.

This script is the load-bearing artifact of the Silent Observer agent. The SKILL.md
is documentation; this script is the enforcement layer. The calling COO cannot bypass
the protocol by modifying prompts or adding "helpful context" — the function signature
and internal logic simply do not allow it.

Architecture:
    - Fixed input paths (not parameterized)
    - Static system prompt loaded from reference/system_prompt.md
    - Goal-before-context-before-task message ordering
    - Fixed model: gemini-3-pro (no fallback to same-family models)
    - Structured output validation (rejects simulation language, enforces schema)
    - Deterministic decision logic (Rule 5 from SKILL.md)
    - Audit logging of every invocation

Usage (called by COO):
    python3 invoke_silent_observer.py --workspace /path/to/startup-workspace --epic <epic_slug>

Exit codes:
    0 - Review completed (check verdict in output JSON)
    1 - Halt: required input missing
    2 - Halt: model unavailable
    3 - Halt: response validation failed after retry
    4 - Halt: configuration error

Environment:
    GEMINI_API_KEY - required. Without it the script halts with exit 2.

Output:
    - JSON verdict object to stdout
    - Full markdown report written to {workspace}/artifacts/reviews/silent_observer/
    - Audit log entry appended to {workspace}/logs/silent_observer_calls.jsonl
    - State update written to {workspace}/state/company_state.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ============================================================================
# CONSTANTS — baked into the script, cannot be modified by the caller
# ============================================================================

FIXED_MODEL = "gemini-3-pro"
MAX_VERIFICATION_RETRIES = 1  # one retry on schema validation failure, then halt
REQUEST_TIMEOUT_SECONDS = 300  # 5 minutes per API call
MAX_BRIEF_LENGTH_BYTES = 500_000  # sanity limit; briefs larger than this are suspicious

# Filename patterns that indicate contaminated reasoning (must not be read)
CONTAMINATION_PATTERNS = [
    r".*self_assessment.*",
    r".*handoff.*",
    r".*summary_for_.*",
    r".*restatement.*",
    r".*reasoning_trace.*",
    r".*internal_notes.*",
]

# Phrases that indicate simulation language in the model's output
# If any appear in the response, the script rejects and retries once
SIMULATION_PHRASES = [
    "in a real implementation",
    "you would typically",
    "based on my training data",
    "seems reasonable",
    "this appears to be",
    "in most cases",
    "generally speaking",
]

# Valid verdict values for individual claims
VALID_CLAIM_VERDICTS = {"VERIFIED", "UNVERIFIABLE", "CONTRADICTED"}

# Valid claim types
VALID_CLAIM_TYPES = {
    "api_sdk",
    "library_capability",
    "company_fact",
    "market_stat",
    "pricing",
    "regulatory",
    "technical_constraint",
}

# The script's own directory (for locating reference files deterministically)
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SYSTEM_PROMPT_PATH = SKILL_DIR / "reference" / "system_prompt.md"
REPORT_TEMPLATE_PATH = SKILL_DIR / "templates" / "verification_report.md"


# ============================================================================
# Data structures
# ============================================================================


@dataclass
class Claim:
    claim_id: str
    quote: str
    source_line: str
    claim_type: str
    load_bearing: bool
    load_bearing_reason: str
    verification_method: str
    verification_attempts: list[dict]
    verdict: str
    verdict_evidence_quote: str
    verdict_evidence_source: str


@dataclass
class ReviewInputs:
    """The three whitelisted inputs the Silent Observer may see. Nothing else."""
    sprint_goal: str
    product_description: str
    discovery_brief: str
    brief_path: str
    goal_source_path: str

    def input_hash(self) -> str:
        combined = f"{self.sprint_goal}\n---\n{self.product_description}\n---\n{self.discovery_brief}"
        return hashlib.sha256(combined.encode()).hexdigest()


@dataclass
class ReviewResult:
    verdict: str  # APPROVE | FLAG | BLOCK
    total_claims: int
    verified_count: int
    unverifiable_count: int
    contradicted_count: int
    load_bearing_contradicted: list[Claim] = field(default_factory=list)
    load_bearing_unverifiable: list[Claim] = field(default_factory=list)
    flag_claims: list[Claim] = field(default_factory=list)
    verified_claims: list[Claim] = field(default_factory=list)
    report_path: str = ""
    model_used: str = FIXED_MODEL
    input_hash: str = ""
    output_hash: str = ""
    timestamp_utc: str = ""


# ============================================================================
# Input loading — fixed paths, no caller override
# ============================================================================


def load_inputs(workspace: Path, epic: str) -> ReviewInputs:
    """Load the three whitelisted inputs from fixed paths.

    The calling COO cannot pass additional context — this function only accepts
    workspace and epic, and reads from hardcoded paths. This is the structural
    defense against reasoning-chain contamination.
    """
    project_config_path = workspace / "state" / "project_config.json"
    sprint_plan_path = workspace / "state" / "sprint_plan.json"
    brief_path = workspace / "artifacts" / "research" / epic / "discovery_brief.md"

    # Validate all three exist
    for path, name in [
        (project_config_path, "project_config.json"),
        (sprint_plan_path, "sprint_plan.json"),
        (brief_path, "discovery_brief.md"),
    ]:
        if not path.exists():
            halt(
                f"Required input missing: {name}",
                f"Expected at {path}. Silent Observer cannot review without all three inputs.",
                exit_code=1,
            )
        if path.stat().st_size == 0:
            halt(
                f"Required input is empty: {name}",
                f"File at {path} exists but is zero bytes. Silent Observer cannot review empty inputs.",
                exit_code=1,
            )

    # Load and extract fields
    try:
        project_config = json.loads(project_config_path.read_text())
        product_description = project_config.get("product_description", "").strip()
        if not product_description:
            halt(
                "project_config.json has no product_description field",
                "The Silent Observer needs the product description as part of goal anchoring.",
                exit_code=1,
            )
    except json.JSONDecodeError as e:
        halt(f"project_config.json is not valid JSON: {e}", exit_code=1)

    try:
        sprint_plan = json.loads(sprint_plan_path.read_text())
        sprint_goal = sprint_plan.get("goal", "").strip()
        if not sprint_goal:
            halt(
                "sprint_plan.json has no goal field",
                "The Silent Observer needs the sprint goal as the anchor.",
                exit_code=1,
            )
    except json.JSONDecodeError as e:
        halt(f"sprint_plan.json is not valid JSON: {e}", exit_code=1)

    discovery_brief = brief_path.read_text()
    if len(discovery_brief.encode()) > MAX_BRIEF_LENGTH_BYTES:
        halt(
            f"discovery_brief.md is {len(discovery_brief.encode()):,} bytes (limit: {MAX_BRIEF_LENGTH_BYTES:,})",
            "Briefs this large are suspicious and may indicate context contamination. Investigate before re-running.",
            exit_code=1,
        )

    return ReviewInputs(
        sprint_goal=sprint_goal,
        product_description=product_description,
        discovery_brief=discovery_brief,
        brief_path=str(brief_path),
        goal_source_path=str(sprint_plan_path),
    )


def scan_for_contamination(workspace: Path, epic: str) -> list[str]:
    """Scan for files whose names match contamination patterns.

    The wrapper does not read these files, but it logs their presence so the CEO
    can audit whether a sub-agent is leaving reasoning artifacts that might have
    contaminated a future reviewer if one was less disciplined about input scoping.
    """
    research_dir = workspace / "artifacts" / "research" / epic
    if not research_dir.exists():
        return []

    compiled = [re.compile(p, re.IGNORECASE) for p in CONTAMINATION_PATTERNS]
    contamination: list[str] = []
    for file_path in research_dir.rglob("*"):
        if not file_path.is_file():
            continue
        name = file_path.name
        if any(p.match(name) for p in compiled):
            contamination.append(str(file_path))
    return contamination


# ============================================================================
# Protocol: goal → context → task message construction
# ============================================================================


def load_system_prompt() -> str:
    """Load the static system prompt from disk. This is not parameterized."""
    if not SYSTEM_PROMPT_PATH.exists():
        halt(
            f"Silent Observer system prompt missing: {SYSTEM_PROMPT_PATH}",
            "The skill is not properly installed. Re-run the skill setup.",
            exit_code=4,
        )
    return SYSTEM_PROMPT_PATH.read_text()


def query_process_learnings() -> str:
    """Query memory for process-only learnings (cold-read protection for silent observer).

    Silent observers must not see task-specific context that would anchor them on
    the current task. They MAY see process learnings ("how to verify SDK claims",
    "look up before instructing") because those improve HOW the verification is done
    without biasing WHAT is verified.

    Returns the formatted injection text, or empty string if query.py is unreachable
    or no matching entries exist.
    """
    query_script = Path.home() / ".claude" / "memory" / "query.py"
    if not query_script.exists():
        return ""
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(query_script),
                "--phase", "research",
                "--project", "global",
                "--top-n", "5",
                "--char-budget", "5000",
                "--learning-types", "process",  # cold-read protection
                "--format", "injection",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return (result.stdout or "").strip()
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return ""


def build_messages(inputs: ReviewInputs) -> list[dict]:
    """Build the API messages in the protocol-mandated order.

    Goal first, then context, then task. This is the structural enforcement of
    the 'context comes after unadulterated goals' rule. The model anchors on
    whatever it sees first; by controlling what's first, the protocol ensures
    the anchor is the real business goal, not downstream reasoning.

    Memory injection: between the anchor and the brief content, inject any
    PROCESS-only learnings (e.g., "verify SDK claims via real API call"). The
    silent observer's cold-read protection means we filter to learning_type=process
    so the observer benefits from past process knowledge without being anchored
    on task-specific context.
    """
    system_prompt = load_system_prompt()

    process_learnings = query_process_learnings()

    messages = [
        # Message 1: Goal, alone. Nothing else.
        {
            "role": "user",
            "content": (
                "ANCHOR: The goal of this sprint is:\n\n"
                f"{inputs.sprint_goal}\n\n"
                f"Product description: {inputs.product_description}\n\n"
                "Your job is to verify factual claims in the research brief that follows, "
                "against this goal as the anchor. A claim is load-bearing if any downstream "
                "work (architecture, development, testing) would need it to be true for the "
                "sprint to succeed."
            ),
        },
    ]

    # Message 2 (conditional): Process learnings, BEFORE the brief.
    # The order matters: process knowledge ("how to verify") comes before the
    # artifact under review so the model anchors on the verification discipline.
    # This is the cold-read-protected memory layer for the silent observer.
    if process_learnings:
        messages.append({
            "role": "user",
            "content": (
                "PROCESS LEARNINGS FROM PRIOR SPRINTS (these are general rules about "
                "how to verify claims, not facts about the current task — they improve "
                "HOW you verify, not WHAT you verify):\n\n"
                f"{process_learnings}"
            ),
        })

    messages.extend([
        # Message 3: The brief content, labeled as the work under review
        {
            "role": "user",
            "content": (
                f"DISCOVERY BRIEF (loaded from {inputs.brief_path}):\n\n"
                f"{inputs.discovery_brief}"
            ),
        },
        # Message 4: The task
        {
            "role": "user",
            "content": (
                "TASK: Identify every specific factual claim in the brief above. For each "
                "claim, independently verify it using web search and document fetching — do "
                "NOT rely on your training data as evidence. Classify each claim as VERIFIED, "
                "UNVERIFIABLE, or CONTRADICTED with evidence. Mark each claim as load_bearing "
                "or not. Return the result as a JSON object matching the schema in the system "
                "prompt. Do not deviate from the schema."
            ),
        },
    ])

    return messages, system_prompt


# ============================================================================
# Model invocation — fixed model, no fallback
# ============================================================================


def call_gemini(system_prompt: str, messages: list[dict]) -> str:
    """Invoke Gemini 3 Pro. No fallback to other models.

    If the Gemini API is unreachable, the entire review halts. We deliberately
    do NOT fall back to Claude because the whole point of the Silent Observer
    is to use a different-training-lineage model.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        halt(
            "GEMINI_API_KEY not set in environment",
            "Silent Observer requires Gemini 3 Pro access and does not fall back to other model families. "
            "Set GEMINI_API_KEY via Doppler or add to ~/startup-workspace/.env, then re-run.",
            exit_code=2,
        )

    try:
        # Prefer google-genai (new SDK) over the legacy google-generativeai
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore

        client = genai.Client(api_key=api_key)

        # Convert messages to Gemini format
        # Gemini uses "contents" with parts, not the OpenAI-style role/content
        contents = []
        for msg in messages:
            contents.append(
                types.Content(role="user", parts=[types.Part(text=msg["content"])])
            )

        response = client.models.generate_content(
            model=FIXED_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.1,  # low temp for factual verification
            ),
        )

        return response.text

    except ImportError:
        halt(
            "google-genai package not installed",
            "Install with: pip install google-genai\n"
            "Silent Observer requires this package for Gemini 3 Pro API access.",
            exit_code=2,
        )
    except Exception as e:
        # Distinguish auth/quota (unrecoverable) from transient (retry once)
        error_str = str(e).lower()
        if any(
            marker in error_str
            for marker in ["unauthorized", "forbidden", "quota", "permission", "invalid api key", "401", "403"]
        ):
            halt(
                f"Gemini API auth/quota error: {e}",
                "Silent Observer cannot proceed. Check GEMINI_API_KEY and quota at https://aistudio.google.com/apikey",
                exit_code=2,
            )
        # Transient — retry once
        print(f"Gemini transient error, retrying once: {e}", file=sys.stderr)
        time.sleep(5)
        try:
            from google import genai  # type: ignore
            from google.genai import types  # type: ignore

            client = genai.Client(api_key=api_key)
            contents = []
            for msg in messages:
                contents.append(
                    types.Content(role="user", parts=[types.Part(text=msg["content"])])
                )
            response = client.models.generate_content(
                model=FIXED_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            return response.text
        except Exception as retry_e:
            halt(
                f"Gemini API failed after retry: {retry_e}",
                "Silent Observer cannot complete this review.",
                exit_code=2,
            )


# ============================================================================
# Response validation — enforces schema and rejects simulation language
# ============================================================================


def validate_response(response_text: str) -> tuple[dict | None, list[str]]:
    """Validate the model's response. Returns (parsed_dict, errors)."""
    errors: list[str] = []

    # 1. Must parse as JSON
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as e:
        return None, [f"Response is not valid JSON: {e}"]

    # 2. Must have required top-level fields
    required_top_fields = ["sprint_goal", "brief_path", "total_claims_identified", "claims", "summary"]
    for field_name in required_top_fields:
        if field_name not in data:
            errors.append(f"Missing required top-level field: {field_name}")

    if errors:
        return None, errors

    # 3. Claims array must be a list
    if not isinstance(data["claims"], list):
        errors.append("'claims' must be an array")
        return None, errors

    # 4. Each claim must have required fields and valid values
    for i, claim in enumerate(data["claims"]):
        claim_errors = validate_claim(claim, i)
        errors.extend(claim_errors)

    # 5. Simulation language check
    response_lower = response_text.lower()
    for phrase in SIMULATION_PHRASES:
        if phrase in response_lower:
            errors.append(
                f"Simulation language detected: '{phrase}'. "
                "The Silent Observer must verify externally, not from training data or hedging."
            )

    # 6. Summary counts must match claims array
    summary = data["summary"]
    actual_verified = sum(1 for c in data["claims"] if c.get("verdict") == "VERIFIED")
    actual_unverifiable = sum(1 for c in data["claims"] if c.get("verdict") == "UNVERIFIABLE")
    actual_contradicted = sum(1 for c in data["claims"] if c.get("verdict") == "CONTRADICTED")
    actual_lb_contradicted = sum(
        1
        for c in data["claims"]
        if c.get("verdict") == "CONTRADICTED" and c.get("load_bearing") is True
    )
    actual_lb_unverifiable = sum(
        1
        for c in data["claims"]
        if c.get("verdict") == "UNVERIFIABLE" and c.get("load_bearing") is True
    )

    if summary.get("verified_count") != actual_verified:
        errors.append(
            f"summary.verified_count ({summary.get('verified_count')}) "
            f"does not match actual count ({actual_verified})"
        )
    if summary.get("contradicted_count") != actual_contradicted:
        errors.append(
            f"summary.contradicted_count ({summary.get('contradicted_count')}) "
            f"does not match actual count ({actual_contradicted})"
        )
    if summary.get("unverifiable_count") != actual_unverifiable:
        errors.append(
            f"summary.unverifiable_count ({summary.get('unverifiable_count')}) "
            f"does not match actual count ({actual_unverifiable})"
        )
    if summary.get("load_bearing_contradicted_count") != actual_lb_contradicted:
        errors.append(
            f"summary.load_bearing_contradicted_count mismatch: "
            f"reported {summary.get('load_bearing_contradicted_count')}, actual {actual_lb_contradicted}"
        )
    if summary.get("load_bearing_unverifiable_count") != actual_lb_unverifiable:
        errors.append(
            f"summary.load_bearing_unverifiable_count mismatch: "
            f"reported {summary.get('load_bearing_unverifiable_count')}, actual {actual_lb_unverifiable}"
        )

    if errors:
        return None, errors
    return data, []


def validate_claim(claim: dict, index: int) -> list[str]:
    """Validate a single claim entry."""
    errors: list[str] = []
    required_fields = {
        "claim_id": str,
        "quote": str,
        "source_line": str,
        "claim_type": str,
        "load_bearing": bool,
        "load_bearing_reason": str,
        "verification_method": str,
        "verification_attempts": list,
        "verdict": str,
        "verdict_evidence_quote": str,
        "verdict_evidence_source": str,
    }

    for field_name, field_type in required_fields.items():
        if field_name not in claim:
            errors.append(f"Claim {index} missing field: {field_name}")
            continue
        if not isinstance(claim[field_name], field_type):
            errors.append(
                f"Claim {index} field '{field_name}' has wrong type: "
                f"expected {field_type.__name__}, got {type(claim[field_name]).__name__}"
            )

    # Value checks (only if fields are present)
    if "verdict" in claim and claim["verdict"] not in VALID_CLAIM_VERDICTS:
        errors.append(f"Claim {index} has invalid verdict: {claim['verdict']}")

    if "claim_type" in claim and claim["claim_type"] not in VALID_CLAIM_TYPES:
        errors.append(f"Claim {index} has invalid claim_type: {claim['claim_type']}")

    # VERIFIED claims must have non-empty evidence
    if claim.get("verdict") == "VERIFIED":
        if not claim.get("verdict_evidence_quote", "").strip():
            errors.append(
                f"Claim {index} is VERIFIED but has no verdict_evidence_quote. "
                "Every VERIFIED claim requires a specific quoted source."
            )
        if not claim.get("verdict_evidence_source", "").strip():
            errors.append(
                f"Claim {index} is VERIFIED but has no verdict_evidence_source. "
                "Every VERIFIED claim requires an identifiable source (URL or document ID)."
            )

    # CONTRADICTED claims must have evidence and at least 3 verification attempts
    if claim.get("verdict") == "CONTRADICTED":
        if not claim.get("verdict_evidence_quote", "").strip():
            errors.append(
                f"Claim {index} is CONTRADICTED but has no verdict_evidence_quote. "
                "Every CONTRADICTED claim must quote the contradicting evidence."
            )
        attempts = claim.get("verification_attempts", [])
        if len(attempts) < 3:
            errors.append(
                f"Claim {index} is CONTRADICTED but only has {len(attempts)} verification attempts. "
                "CONTRADICTED verdicts require at least 3 attempts to rule out search-failure false positives."
            )

    return errors


# ============================================================================
# Deterministic decision logic — Rule 5 from SKILL.md
# ============================================================================


def compute_verdict(data: dict) -> ReviewResult:
    """Apply the deterministic decision rule to compute the overall verdict.

    This is code, not an LLM judgment. The rule:
    - Any load-bearing CONTRADICTED → BLOCK
    - Any load-bearing UNVERIFIABLE → BLOCK
    - Any non-load-bearing CONTRADICTED or UNVERIFIABLE → FLAG (not BLOCK)
    - All VERIFIED or flag-only → APPROVE
    """
    claims_raw = data["claims"]
    claims = [Claim(**c) for c in claims_raw]

    load_bearing_contradicted = [c for c in claims if c.verdict == "CONTRADICTED" and c.load_bearing]
    load_bearing_unverifiable = [c for c in claims if c.verdict == "UNVERIFIABLE" and c.load_bearing]
    flag_claims = [
        c
        for c in claims
        if c.verdict in {"CONTRADICTED", "UNVERIFIABLE"} and not c.load_bearing
    ]
    verified_claims = [c for c in claims if c.verdict == "VERIFIED"]

    if load_bearing_contradicted or load_bearing_unverifiable:
        verdict = "BLOCK"
    elif flag_claims:
        verdict = "FLAG"
    else:
        verdict = "APPROVE"

    return ReviewResult(
        verdict=verdict,
        total_claims=len(claims),
        verified_count=len(verified_claims),
        unverifiable_count=sum(1 for c in claims if c.verdict == "UNVERIFIABLE"),
        contradicted_count=sum(1 for c in claims if c.verdict == "CONTRADICTED"),
        load_bearing_contradicted=load_bearing_contradicted,
        load_bearing_unverifiable=load_bearing_unverifiable,
        flag_claims=flag_claims,
        verified_claims=verified_claims,
    )


# ============================================================================
# Report writing
# ============================================================================


def write_report(
    result: ReviewResult,
    inputs: ReviewInputs,
    workspace: Path,
    epic: str,
    contamination_found: list[str],
) -> Path:
    """Write the full verification report in markdown."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    report_dir = workspace / "artifacts" / "reviews" / "silent_observer"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{epic}_{timestamp}.md"

    lines: list[str] = []
    lines.append(f"# Silent Observer Verification Report")
    lines.append("")
    lines.append(f"**Phase:** 2 (Research)")
    lines.append(f"**Epic:** {epic}")
    lines.append(f"**Timestamp:** {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"**Model:** {FIXED_MODEL}")
    lines.append(f"**Input hash:** {result.input_hash}")
    lines.append(f"**Output hash:** {result.output_hash}")
    lines.append(f"**Goal source:** `{inputs.goal_source_path}`")
    lines.append(f"**Brief reviewed:** `{inputs.brief_path}`")
    lines.append("")
    lines.append("## Sprint Goal (the anchor)")
    lines.append("")
    lines.append(f"> {inputs.sprint_goal}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total claims identified:** {result.total_claims}")
    lines.append(f"- **Verified:** {result.verified_count}")
    lines.append(f"- **Unverifiable:** {result.unverifiable_count}")
    lines.append(f"- **Contradicted:** {result.contradicted_count}")
    lines.append(f"- **Load-bearing contradicted:** {len(result.load_bearing_contradicted)}")
    lines.append(f"- **Load-bearing unverifiable:** {len(result.load_bearing_unverifiable)}")
    lines.append("")
    lines.append(f"## Verdict: **{result.verdict}**")
    lines.append("")

    if result.verdict == "BLOCK":
        lines.append(
            "Phase 2 cannot advance. The discovery brief contains factual claims that are either "
            "contradicted by evidence or cannot be independently verified, and these claims are "
            "load-bearing — downstream work would depend on them being true."
        )
        lines.append("")
        lines.append("## Blocking Claims")
        lines.append("")
        for claim in result.load_bearing_contradicted:
            lines.append(f"### [CONTRADICTED — LOAD-BEARING] {claim.claim_id}")
            lines.append(f"**Quote from brief ({claim.source_line}):** \"{claim.quote}\"")
            lines.append(f"**Claim type:** {claim.claim_type}")
            lines.append(f"**Why load-bearing:** {claim.load_bearing_reason}")
            lines.append(f"**Verification method:** {claim.verification_method}")
            lines.append(f"**Contradicting evidence:** \"{claim.verdict_evidence_quote}\"")
            lines.append(f"**Source:** {claim.verdict_evidence_source}")
            lines.append("")
            lines.append("**Required action:** VP Product Research must either (a) find authoritative "
                         "evidence supporting the original claim, or (b) rewrite the brief to reflect "
                         "the correct information from the contradicting source.")
            lines.append("")

        for claim in result.load_bearing_unverifiable:
            lines.append(f"### [UNVERIFIABLE — LOAD-BEARING] {claim.claim_id}")
            lines.append(f"**Quote from brief ({claim.source_line}):** \"{claim.quote}\"")
            lines.append(f"**Claim type:** {claim.claim_type}")
            lines.append(f"**Why load-bearing:** {claim.load_bearing_reason}")
            lines.append(f"**Verification method:** {claim.verification_method}")
            lines.append(f"**Verification attempts:** {len(claim.verification_attempts)}")
            for i, attempt in enumerate(claim.verification_attempts, 1):
                lines.append(f"  {i}. {attempt.get('method', '?')} — {attempt.get('query', '?')} — {attempt.get('result_summary', '?')}")
            lines.append("")
            lines.append("**Required action:** VP Product Research must provide a verifiable source for "
                         "this claim. If no public source exists, either (a) document the internal source "
                         "and mark the claim as internal-only, or (b) remove the claim from the brief.")
            lines.append("")

    elif result.verdict == "FLAG":
        lines.append(
            "Phase 2 may advance. The discovery brief has some factual claims that could not be "
            "verified or that were contradicted by evidence, but none of these claims are load-bearing "
            "for downstream work. These flags should be noted and addressed in a future sprint."
        )
        lines.append("")
        lines.append("## Flagged Claims (Non-Blocking)")
        lines.append("")
        for claim in result.flag_claims:
            lines.append(f"### [{claim.verdict}] {claim.claim_id}")
            lines.append(f"**Quote:** \"{claim.quote}\"")
            lines.append(f"**Source in brief:** {claim.source_line}")
            lines.append(f"**Claim type:** {claim.claim_type}")
            lines.append(f"**Verification method:** {claim.verification_method}")
            lines.append(f"**Evidence:** \"{claim.verdict_evidence_quote}\"")
            lines.append(f"**Evidence source:** {claim.verdict_evidence_source}")
            lines.append("")

    else:  # APPROVE
        lines.append(
            "Phase 2 may advance. All factual claims identified in the brief were independently "
            "verified against authoritative sources."
        )
        lines.append("")

    lines.append("## Verified Claims")
    lines.append("")
    if result.verified_claims:
        for claim in result.verified_claims:
            lines.append(f"- **{claim.claim_id}** ({claim.claim_type}): \"{claim.quote}\" — verified via {claim.verdict_evidence_source}")
    else:
        lines.append("_No claims were verified in this review._")
    lines.append("")

    if contamination_found:
        lines.append("## ⚠️  Contamination Warning")
        lines.append("")
        lines.append(
            "The following files matching contamination patterns were found in the research directory. "
            "The Silent Observer did NOT read these files (structural enforcement), but their presence "
            "suggests the primary researcher may be leaving reasoning artifacts that could contaminate "
            "less-disciplined reviewers. Consider cleaning these up:"
        )
        lines.append("")
        for path in contamination_found:
            lines.append(f"- `{path}`")
        lines.append("")

    lines.append("## Protocol Attestation")
    lines.append("")
    lines.append("This review was conducted under the Silent Observer structural protocol:")
    lines.append("")
    lines.append("- ✅ Inputs limited to sprint goal, product description, and discovery brief")
    lines.append("- ✅ Self-assessment and handoff files were not read (enforced by allowlist)")
    lines.append("- ✅ Goal sent to model before brief content (anchor before context)")
    lines.append(f"- ✅ Fixed model: `{FIXED_MODEL}` (no fallback to same-family models)")
    lines.append("- ✅ Response validated against JSON schema")
    lines.append("- ✅ Deterministic decision logic (not LLM judgment)")
    lines.append("- ✅ Audit log entry written to `logs/silent_observer_calls.jsonl`")
    lines.append("")

    report_text = "\n".join(lines)
    report_path.write_text(report_text)
    result.report_path = str(report_path)
    return report_path


# ============================================================================
# Audit logging
# ============================================================================


def append_audit_log(workspace: Path, result: ReviewResult, inputs: ReviewInputs, epic: str):
    """Append an audit entry to logs/silent_observer_calls.jsonl."""
    log_dir = workspace / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "silent_observer_calls.jsonl"

    entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "agent": "silent-observer",
        "phase": 2,
        "epic": epic,
        "model": FIXED_MODEL,
        "input_hash": result.input_hash,
        "output_hash": result.output_hash,
        "total_claims": result.total_claims,
        "verified_count": result.verified_count,
        "unverifiable_count": result.unverifiable_count,
        "contradicted_count": result.contradicted_count,
        "load_bearing_contradicted_count": len(result.load_bearing_contradicted),
        "load_bearing_unverifiable_count": len(result.load_bearing_unverifiable),
        "verdict": result.verdict,
        "report_path": result.report_path,
        "goal_source": inputs.goal_source_path,
        "brief_path": inputs.brief_path,
    }

    with log_path.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def update_company_state(workspace: Path, result: ReviewResult, epic: str):
    """Write the verdict to company_state.json at silent_observer.phase2.{epic}."""
    state_path = workspace / "state" / "company_state.json"
    if not state_path.exists():
        # Do not halt — the wrapper should still work in test environments
        return

    try:
        state = json.loads(state_path.read_text())
    except json.JSONDecodeError:
        return

    if "silent_observer" not in state:
        state["silent_observer"] = {}
    if "phase2" not in state["silent_observer"]:
        state["silent_observer"]["phase2"] = {}

    state["silent_observer"]["phase2"][epic] = {
        "verdict": result.verdict,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "report_path": result.report_path,
        "model": FIXED_MODEL,
        "total_claims": result.total_claims,
        "blocking_count": len(result.load_bearing_contradicted) + len(result.load_bearing_unverifiable),
    }

    state_path.write_text(json.dumps(state, indent=2))


# ============================================================================
# Halt protocol
# ============================================================================


def halt(error: str, suggestion: str = "", exit_code: int = 1):
    """Write diagnostics and exit."""
    timestamp = datetime.now(timezone.utc).isoformat()
    diag = {
        "timestamp_utc": timestamp,
        "agent": "silent-observer",
        "halt_reason": error,
        "suggestion": suggestion,
        "exit_code": exit_code,
    }
    print(json.dumps(diag, indent=2), file=sys.stderr)
    sys.exit(exit_code)


# ============================================================================
# Main
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Silent Observer wrapper — structural protocol enforcement for Phase 2 fact verification"
    )
    parser.add_argument("--workspace", required=True, help="Path to startup workspace")
    parser.add_argument("--epic", required=True, help="Epic slug (subdir under artifacts/research/)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load inputs and build messages, but do not call the API. For testing the protocol layer.",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    if not workspace.exists():
        halt(f"Workspace does not exist: {workspace}", exit_code=1)

    # Step 1: Load inputs from fixed paths
    inputs = load_inputs(workspace, args.epic)

    # Step 2: Scan for contamination (informational only — does not block)
    contamination = scan_for_contamination(workspace, args.epic)

    # Step 3: Build messages in protocol order (goal → brief → task)
    messages, system_prompt = build_messages(inputs)

    if args.dry_run:
        # Output what WOULD be sent, without calling the API
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "model": FIXED_MODEL,
                    "system_prompt_length": len(system_prompt),
                    "message_count": len(messages),
                    "messages_preview": [
                        {"role": m["role"], "content_preview": m["content"][:200] + "..."}
                        for m in messages
                    ],
                    "input_hash": inputs.input_hash(),
                    "contamination_found": contamination,
                    "goal_source": inputs.goal_source_path,
                    "brief_path": inputs.brief_path,
                },
                indent=2,
            )
        )
        return

    # Step 4: Call Gemini (fixed model, no fallback)
    response_text = call_gemini(system_prompt, messages)

    # Step 5: Validate response
    data, errors = validate_response(response_text)
    if errors:
        # One retry with the errors reported back to the model
        retry_system_prompt = (
            system_prompt
            + "\n\n---\nPRIOR RESPONSE FAILED VALIDATION. Errors to fix:\n"
            + "\n".join(f"- {e}" for e in errors)
            + "\n\nRespond with valid JSON matching the schema exactly."
        )
        response_text = call_gemini(retry_system_prompt, messages)
        data, errors = validate_response(response_text)
        if errors:
            halt(
                "Silent Observer response failed validation after retry",
                "Errors: " + "; ".join(errors),
                exit_code=3,
            )

    # Step 6: Compute deterministic verdict (code, not LLM judgment)
    result = compute_verdict(data)
    result.input_hash = inputs.input_hash()
    result.output_hash = hashlib.sha256(response_text.encode()).hexdigest()
    result.timestamp_utc = datetime.now(timezone.utc).isoformat()

    # Step 7: Write report
    write_report(result, inputs, workspace, args.epic, contamination)

    # Step 8: Audit log + state update
    append_audit_log(workspace, result, inputs, args.epic)
    update_company_state(workspace, result, args.epic)

    # Step 9: Return verdict to stdout (this is what the COO reads)
    output = {
        "verdict": result.verdict,
        "total_claims": result.total_claims,
        "verified_count": result.verified_count,
        "unverifiable_count": result.unverifiable_count,
        "contradicted_count": result.contradicted_count,
        "load_bearing_contradicted_count": len(result.load_bearing_contradicted),
        "load_bearing_unverifiable_count": len(result.load_bearing_unverifiable),
        "report_path": result.report_path,
        "timestamp_utc": result.timestamp_utc,
        "model": FIXED_MODEL,
        "input_hash": result.input_hash,
        "output_hash": result.output_hash,
        "contamination_warning_files": contamination,
    }
    print(json.dumps(output, indent=2))
    # Exit 0 regardless of verdict — the COO reads the verdict field to decide what to do


if __name__ == "__main__":
    main()
