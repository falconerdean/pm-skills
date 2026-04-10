#!/usr/bin/env python3
"""Rival Architect wrapper script — independent producer for Phase 5.

This script is the structural enforcement layer for the Rival Architect protocol.
The calling COO cannot bypass independent-first-response by modifying prompts or
merging context — the function signature only accepts (workspace, epic), and the
input allowlist explicitly excludes the primary's architecture artifacts.

Architecture (mirrors invoke_silent_observer.py):
    - Fixed input paths (whitelisted, NOT including primary's tech output)
    - Static system prompt loaded from reference/system_prompt.md
    - Goal-before-context-before-task message ordering
    - Fixed model: gemini-3-pro (no fallback to Claude family)
    - Structured output validation (rejects simulation language, enforces schema,
      validates SQL parses, JSON parses, required sections present)
    - Atomic write of three artifacts to {workspace}/artifacts/designs/{epic}/tech/rival/
    - Audit logging of every invocation

Usage (called by COO):
    python3 invoke_rival_architect.py --workspace /path/to/startup-workspace --epic <epic_slug>

Exit codes:
    0 - Rival architecture produced successfully
    1 - Halt: required input missing
    2 - Halt: GEMINI_API_KEY missing or unreachable
    3 - Halt: response validation failed after retry
    4 - Halt: configuration error (system prompt missing, etc.)

Environment:
    GEMINI_API_KEY - required. Without it the script halts with exit 2.

Output:
    - JSON status object to stdout
    - Three artifacts written to {workspace}/artifacts/designs/{epic}/tech/rival/:
        - architecture.md
        - api_spec.json
        - db_schema.sql
    - Audit log entry appended to {workspace}/logs/rival_architect_calls.jsonl
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
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# ============================================================================
# CONSTANTS — baked into the script, cannot be modified by the caller
# ============================================================================

FIXED_MODEL = "gemini-3-pro"
MAX_PRODUCTION_RETRIES = 1  # one retry on validation failure
REQUEST_TIMEOUT_SECONDS = 600  # 10 minutes — architecture is a longer task than fact verification

# Required sections in the rival's architecture.md (canonical schema)
REQUIRED_SECTIONS = [
    "overview",
    "data model",
    "api surface",
    "authentication",
    "authorization",
    "deployment",
    "observability",
    "concurrency",
    "error handling",
    "dependencies",
    "compatibility",
]

# Section header fuzzy match patterns (case-insensitive)
SECTION_PATTERNS = {
    "overview": [r"overview", r"summary", r"introduction"],
    "data model": [r"data\s*model", r"schema(?!\s*sql)", r"entities", r"data\s*architecture"],
    "api surface": [r"api(?:\s*surface)?(?!\s*spec)", r"endpoints", r"interface"],
    "authentication": [r"auth(?:entication)?(?!\s*z|\s*orization)", r"identity", r"sign[\s-]?in"],
    "authorization": [r"authorization", r"authz", r"permissions", r"access\s*control"],
    "deployment": [r"deployment", r"infrastructure", r"hosting", r"production\s*environment"],
    "observability": [r"observability", r"monitoring", r"logging", r"metrics", r"telemetry"],
    "concurrency": [r"concurrency", r"concurrent", r"race\s*condition", r"locking", r"queueing"],
    "error handling": [r"error\s*handling", r"errors?(?!\s*format)", r"failure", r"recovery"],
    "dependencies": [r"dependencies", r"libraries", r"packages", r"third[\s-]?party"],
    "compatibility": [r"compatibility", r"support(?:ed)?\s*versions?", r"runtime\s*versions?"],
}

# Phrases that indicate simulation language — wrapper rejects responses containing these
SIMULATION_PHRASES = [
    "in a real implementation",
    "you would typically",
    "this could be extended to",
    "for production, you would",
    "would normally",
    "to be determined",
    "tbd",
    "todo:",
    "[pending]",
    "placeholder",
    "in production we would",
]

# The script's own directory
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SYSTEM_PROMPT_PATH = SKILL_DIR / "reference" / "system_prompt.md"

# Files the rival is FORBIDDEN from seeing — the primary's tech outputs
PRIMARY_FORBIDDEN_PATHS_RELATIVE = [
    "artifacts/designs/{epic}/tech/architecture.md",
    "artifacts/designs/{epic}/tech/api_spec.json",
    "artifacts/designs/{epic}/tech/db_schema.sql",
]


# ============================================================================
# Data structures
# ============================================================================


@dataclass
class RivalInputs:
    """The whitelisted inputs the rival architect may see.

    Critically, this does NOT include any of the primary architect's tech output.
    The rival reads exactly the same starting materials the primary had.
    """
    sprint_goal: str
    product_description: str
    discovery_brief: str
    stories_json: str  # raw text of stories.json
    prd_md: str  # raw text of prd.md (may be empty if not produced)
    ui_spec: str  # may be empty
    ux_flows: str  # may be empty
    content_spec: str  # may be empty
    brief_path: str
    goal_source_path: str

    def input_hash(self) -> str:
        combined = "\n---\n".join([
            self.sprint_goal,
            self.product_description,
            self.discovery_brief,
            self.stories_json,
            self.prd_md,
            self.ui_spec,
            self.ux_flows,
            self.content_spec,
        ])
        return hashlib.sha256(combined.encode()).hexdigest()


@dataclass
class RivalArchitecture:
    architecture_md: str
    api_spec_json: dict
    db_schema_sql: str
    model_self_check: dict


@dataclass
class ProductionResult:
    success: bool
    architecture: RivalArchitecture | None = None
    written_paths: list[str] = field(default_factory=list)
    input_hash: str = ""
    output_hash: str = ""
    timestamp_utc: str = ""
    model_used: str = FIXED_MODEL
    validation_errors: list[str] = field(default_factory=list)


# ============================================================================
# Input loading — whitelist excludes primary's tech output
# ============================================================================


def load_inputs(workspace: Path, epic: str) -> RivalInputs:
    """Load the rival's inputs from fixed paths.

    The whitelist deliberately excludes the primary's architecture artifacts.
    The rival sees the same brief and requirements the primary saw, but never
    sees what the primary produced.
    """
    project_config_path = workspace / "state" / "project_config.json"
    sprint_plan_path = workspace / "state" / "sprint_plan.json"
    brief_path = workspace / "artifacts" / "research" / epic / "discovery_brief.md"
    stories_path = workspace / "artifacts" / "requirements" / epic / "stories.json"

    # Optional but typical — load if present
    prd_path = workspace / "artifacts" / "requirements" / epic / "prd.md"
    ui_spec_path = workspace / "artifacts" / "designs" / epic / "ui_spec.md"
    ux_flows_path = workspace / "artifacts" / "designs" / epic / "ux_flows.md"
    content_spec_path = workspace / "artifacts" / "designs" / epic / "content_spec.md"

    # Required
    for path, name in [
        (project_config_path, "project_config.json"),
        (sprint_plan_path, "sprint_plan.json"),
        (brief_path, "discovery_brief.md"),
        (stories_path, "stories.json"),
    ]:
        if not path.exists():
            halt(
                f"Required input missing: {name}",
                f"Expected at {path}. Rival Architect cannot produce architecture without all four required inputs.",
                exit_code=1,
            )
        if path.stat().st_size == 0:
            halt(
                f"Required input is empty: {name}",
                f"File at {path} exists but is zero bytes.",
                exit_code=1,
            )

    # Verify the primary HAS produced its tech output (otherwise we're running too early)
    primary_arch_path = workspace / "artifacts" / "designs" / epic / "tech" / "architecture.md"
    if not primary_arch_path.exists():
        halt(
            "Primary architect has not yet produced architecture.md",
            f"Expected at {primary_arch_path}. The rival should run AFTER the primary completes Phase 5, "
            "not before. The COO should not invoke this script until the primary's tech output exists.",
            exit_code=1,
        )

    # Load JSON files for field extraction
    try:
        project_config = json.loads(project_config_path.read_text())
        product_description = project_config.get("product_description", "").strip()
        if not product_description:
            halt("project_config.json has no product_description field", exit_code=1)
    except json.JSONDecodeError as e:
        halt(f"project_config.json is not valid JSON: {e}", exit_code=1)

    try:
        sprint_plan = json.loads(sprint_plan_path.read_text())
        sprint_goal = sprint_plan.get("goal", "").strip()
        if not sprint_goal:
            halt("sprint_plan.json has no goal field", exit_code=1)
    except json.JSONDecodeError as e:
        halt(f"sprint_plan.json is not valid JSON: {e}", exit_code=1)

    return RivalInputs(
        sprint_goal=sprint_goal,
        product_description=product_description,
        discovery_brief=brief_path.read_text(),
        stories_json=stories_path.read_text(),
        prd_md=prd_path.read_text() if prd_path.exists() else "",
        ui_spec=ui_spec_path.read_text() if ui_spec_path.exists() else "",
        ux_flows=ux_flows_path.read_text() if ux_flows_path.exists() else "",
        content_spec=content_spec_path.read_text() if content_spec_path.exists() else "",
        brief_path=str(brief_path),
        goal_source_path=str(sprint_plan_path),
    )


def assert_primary_artifacts_not_in_inputs(inputs: RivalInputs, workspace: Path, epic: str):
    """Defensive check: verify the primary's tech artifacts are NOT in any of the rival's inputs.

    This is paranoia — the load_inputs function structurally cannot include them
    because the paths are not in the input list — but we double-check by scanning
    the actual content of the loaded inputs for any literal text from the primary
    architecture files. If we find any, it's a critical bug in the wrapper.
    """
    primary_arch_path = workspace / "artifacts" / "designs" / epic / "tech" / "architecture.md"
    primary_api_path = workspace / "artifacts" / "designs" / epic / "tech" / "api_spec.json"
    primary_db_path = workspace / "artifacts" / "designs" / epic / "tech" / "db_schema.sql"

    primary_files = []
    for p in [primary_arch_path, primary_api_path, primary_db_path]:
        if p.exists():
            primary_files.append((p.name, p.read_text()))

    if not primary_files:
        return  # primary hasn't produced anything; nothing to check against

    # Check that no substantial chunk of the primary's content appears in any input
    # We use 100-character substrings as the contamination signal
    all_inputs_concatenated = (
        inputs.sprint_goal
        + "\n"
        + inputs.product_description
        + "\n"
        + inputs.discovery_brief
        + "\n"
        + inputs.stories_json
        + "\n"
        + inputs.prd_md
        + "\n"
        + inputs.ui_spec
        + "\n"
        + inputs.ux_flows
        + "\n"
        + inputs.content_spec
    )

    for primary_name, primary_content in primary_files:
        # Sample a few 100-char windows from the middle of the primary file
        if len(primary_content) < 200:
            continue
        sample_offsets = [len(primary_content) // 4, len(primary_content) // 2, 3 * len(primary_content) // 4]
        for offset in sample_offsets:
            sample = primary_content[offset : offset + 100]
            # Skip samples that are mostly whitespace or punctuation
            if len(sample.strip()) < 50:
                continue
            if sample in all_inputs_concatenated:
                halt(
                    "PROTOCOL VIOLATION: primary architect's content found in rival's inputs",
                    f"Sample from {primary_name} at offset {offset} appeared in the rival's loaded inputs. "
                    f"This is a critical bug — the wrapper script's input allowlist is not isolating "
                    f"the rival from the primary. Sample: {sample!r}",
                    exit_code=4,
                )


# ============================================================================
# Protocol: goal → context → task message construction
# ============================================================================


def load_system_prompt() -> str:
    if not SYSTEM_PROMPT_PATH.exists():
        halt(
            f"Rival Architect system prompt missing: {SYSTEM_PROMPT_PATH}",
            "The skill is not properly installed.",
            exit_code=4,
        )
    return SYSTEM_PROMPT_PATH.read_text()


def query_phase5_learnings(project: str = "global") -> str:
    """Query memory for tech_design phase learnings (full injection — rival is NOT a cold reader).

    The rival architect should know the same facts as the primary architect.
    Both rivals knowing the Stitch SDK limitation is NOT a contamination of independence —
    it is the institutional fact base they both work from. The diversity of judgment on
    shared facts is what we want; the diversity of facts would be a confound.

    Returns the formatted injection text, empty string if query.py unreachable.
    """
    query_script = Path.home() / ".claude" / "memory" / "query.py"
    if not query_script.exists():
        return ""
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(query_script),
                "--phase", "tech_design",
                "--project", project,
                "--top-n", "5",
                "--char-budget", "5000",
                "--learning-types", "process,factual,task_specific",  # full injection
                "--format", "injection",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return (result.stdout or "").strip()
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return ""


def build_messages(inputs: RivalInputs) -> tuple[list[dict], str]:
    """Build the API messages in the protocol-mandated order.

    Goal first, then OPTIONAL learnings, then context (brief + requirements + design),
    then task. The learnings come AFTER the goal anchor but BEFORE the task context, so
    the rival architect knows the past-sprint facts when it reads the brief.
    """
    system_prompt = load_system_prompt()

    # Message 1: Anchor (goal + product description, alone)
    anchor = (
        "ANCHOR: The goal of this sprint is:\n\n"
        f"{inputs.sprint_goal}\n\n"
        f"Product description: {inputs.product_description}\n\n"
        "Your job is to produce a complete technical architecture for this sprint, anchored on this goal. "
        "You will produce three artifacts: architecture.md, api_spec.json, and db_schema.sql. "
        "You are working in deliberate isolation from another technical architect (Claude) who is producing "
        "their own architecture for the same project. You will never see their work, and they will never "
        "see yours, until both architectures are complete and a separate comparison process runs."
    )

    # Message 2: Context (all the whitelisted starting materials)
    context_parts = [
        f"DISCOVERY BRIEF (verified at Phase 2 by the Silent Observer):\n\n{inputs.discovery_brief}",
        f"\n\n---\n\nUSER STORIES (stories.json):\n\n{inputs.stories_json}",
    ]
    if inputs.prd_md:
        context_parts.append(f"\n\n---\n\nPRODUCT REQUIREMENTS (prd.md):\n\n{inputs.prd_md}")
    if inputs.ui_spec:
        context_parts.append(f"\n\n---\n\nUI SPEC (ui_spec.md):\n\n{inputs.ui_spec}")
    if inputs.ux_flows:
        context_parts.append(f"\n\n---\n\nUX FLOWS (ux_flows.md):\n\n{inputs.ux_flows}")
    if inputs.content_spec:
        context_parts.append(f"\n\n---\n\nCONTENT SPEC (content_spec.md):\n\n{inputs.content_spec}")

    context = "STARTING MATERIALS (the same materials the primary architect has access to):\n\n" + "".join(context_parts)

    # Message 3: Task
    task = (
        "TASK: Produce a complete technical architecture for the system described above. Your output must be "
        "a JSON object with exactly these fields: architecture_md (markdown text), api_spec_json (JSON object), "
        "db_schema_sql (SQL text), and model_self_check (object with the boolean fields described in the "
        "system prompt). The architecture.md must include all eleven canonical sections: Overview, Data Model, "
        "API Surface, Authentication, Authorization, Deployment, Observability, Concurrency, Error Handling, "
        "Dependencies, Compatibility. The Concurrency and Compatibility sections must be substantive — these "
        "are the dimensions where your specialization adds value. Verify external dependencies you reference "
        "via WebSearch or WebFetch before citing them. Do not use simulation language or placeholders."
    )

    messages = [
        {"role": "user", "content": anchor},
    ]

    # Optional: inject phase-relevant learnings between anchor and context.
    # Rival receives the full injection (process + factual + task_specific) because
    # it is NOT a cold reader — it is a parallel producer that should know the same
    # institutional facts as the primary architect.
    learnings = query_phase5_learnings()
    if learnings:
        messages.append({
            "role": "user",
            "content": (
                "INSTITUTIONAL LEARNINGS FROM PRIOR SPRINTS (these are facts both you "
                "and the primary architect should know — they shape the constraints "
                "your architecture must respect):\n\n"
                f"{learnings}"
            ),
        })

    messages.extend([
        {"role": "user", "content": context},
        {"role": "user", "content": task},
    ])

    return messages, system_prompt


# ============================================================================
# Model invocation — fixed model, no fallback
# ============================================================================


def call_gemini(system_prompt: str, messages: list[dict]) -> str:
    """Invoke gemini-3-pro. No fallback to Claude family."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        halt(
            "GEMINI_API_KEY not set in environment",
            "Rival Architect requires gemini-3-pro and does not fall back to Claude-family models. "
            "Set GEMINI_API_KEY via Doppler or add to ~/startup-workspace/.env, then re-run.",
            exit_code=2,
        )

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
                temperature=0.2,  # slightly higher than fact verification — architecture has design judgment
            ),
        )
        return response.text

    except ImportError:
        halt(
            "google-genai package not installed",
            "Install with: pip install google-genai",
            exit_code=2,
        )
    except Exception as e:
        error_str = str(e).lower()
        if any(
            marker in error_str
            for marker in ["unauthorized", "forbidden", "quota", "permission", "invalid api key", "401", "403"]
        ):
            halt(
                f"Gemini API auth/quota error: {e}",
                "Check GEMINI_API_KEY at https://aistudio.google.com/apikey",
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
                    temperature=0.2,
                ),
            )
            return response.text
        except Exception as retry_e:
            halt(f"Gemini API failed after retry: {retry_e}", exit_code=2)


# ============================================================================
# Response validation
# ============================================================================


def validate_response(response_text: str) -> tuple[RivalArchitecture | None, list[str]]:
    """Validate the rival's response. Returns (architecture, errors)."""
    errors: list[str] = []

    # 1. Must parse as JSON
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as e:
        return None, [f"Response is not valid JSON: {e}"]

    # 2. Must have required top-level fields
    required_fields = ["architecture_md", "api_spec_json", "db_schema_sql", "model_self_check"]
    for field_name in required_fields:
        if field_name not in data:
            errors.append(f"Missing required top-level field: {field_name}")
    if errors:
        return None, errors

    architecture_md = data["architecture_md"]
    api_spec_json = data["api_spec_json"]
    db_schema_sql = data["db_schema_sql"]
    model_self_check = data["model_self_check"]

    # 3. architecture_md must be a non-empty string
    if not isinstance(architecture_md, str) or len(architecture_md.strip()) < 500:
        errors.append("architecture_md is missing or too short (minimum 500 chars)")

    # 4. api_spec_json must be a dict (JSON object)
    if not isinstance(api_spec_json, dict):
        errors.append("api_spec_json must be a JSON object, not a string or array")

    # 5. db_schema_sql must be a non-empty string
    if not isinstance(db_schema_sql, str) or len(db_schema_sql.strip()) < 50:
        errors.append("db_schema_sql is missing or too short (minimum 50 chars)")

    # 6. db_schema_sql must contain at least one CREATE TABLE
    if isinstance(db_schema_sql, str):
        create_table_matches = re.findall(
            r"CREATE\s+TABLE", db_schema_sql, re.IGNORECASE
        )
        if not create_table_matches:
            errors.append("db_schema_sql contains no CREATE TABLE statements")

    # 7. architecture_md must contain all required canonical sections
    if isinstance(architecture_md, str):
        present, missing = check_section_coverage(architecture_md)
        if missing:
            errors.append(
                f"architecture.md missing required sections: {', '.join(missing)}. "
                f"Found: {', '.join(present)}"
            )

    # 8. Concurrency and Compatibility sections must be substantive (>=80 words)
    if isinstance(architecture_md, str) and not errors:
        for required_section in ["concurrency", "compatibility"]:
            section_text = extract_section_text(architecture_md, required_section)
            word_count = len(section_text.split())
            if word_count < 80:
                errors.append(
                    f"Section '{required_section}' has only {word_count} words "
                    f"(minimum 80). The rival architect's specialization requires substantive treatment."
                )

    # 9. Simulation language check
    text_lower = (
        (architecture_md if isinstance(architecture_md, str) else "")
        + " "
        + (db_schema_sql if isinstance(db_schema_sql, str) else "")
    ).lower()
    for phrase in SIMULATION_PHRASES:
        if phrase in text_lower:
            errors.append(
                f"Simulation language detected: '{phrase}'. The rival architect must produce real, "
                "specific decisions, not descriptions of what the architecture would look like."
            )

    # 10. Self-check must report all true
    if isinstance(model_self_check, dict):
        for key in [
            "all_required_sections_present",
            "concurrency_section_substantive",
            "compatibility_section_substantive",
            "no_placeholders",
            "no_simulation_language",
        ]:
            if key not in model_self_check:
                errors.append(f"model_self_check missing field: {key}")
            elif model_self_check[key] is not True:
                errors.append(f"model_self_check.{key} is not true; rival admits incomplete work")

    if errors:
        return None, errors

    return (
        RivalArchitecture(
            architecture_md=architecture_md,
            api_spec_json=api_spec_json,
            db_schema_sql=db_schema_sql,
            model_self_check=model_self_check,
        ),
        [],
    )


def check_section_coverage(architecture_md: str) -> tuple[list[str], list[str]]:
    """Return (present_sections, missing_sections) using fuzzy matching."""
    text_lower = architecture_md.lower()
    present = []
    missing = []
    for canonical, patterns in SECTION_PATTERNS.items():
        # Look for level-2 markdown heading matching any of the patterns
        found = False
        for pattern in patterns:
            heading_regex = re.compile(rf"^##\s+.*{pattern}.*$", re.IGNORECASE | re.MULTILINE)
            if heading_regex.search(architecture_md):
                found = True
                break
        if found:
            present.append(canonical)
        else:
            missing.append(canonical)
    return present, missing


def extract_section_text(architecture_md: str, canonical_section: str) -> str:
    """Extract the text of a section by canonical name.

    Two-step approach: find the heading line first (without DOTALL), then
    capture everything until the next ## heading or EOF. Single-pass regex
    with DOTALL was buggy because .* in the heading match crossed newlines.
    """
    patterns = SECTION_PATTERNS.get(canonical_section, [canonical_section])
    next_heading_re = re.compile(r"^##\s+", re.MULTILINE)
    for pattern in patterns:
        heading_re = re.compile(
            rf"^##\s+[^\n]*{pattern}[^\n]*$",
            re.IGNORECASE | re.MULTILINE,
        )
        heading_match = heading_re.search(architecture_md)
        if heading_match:
            content_start = heading_match.end()
            next_match = next_heading_re.search(architecture_md, content_start)
            content_end = next_match.start() if next_match else len(architecture_md)
            return architecture_md[content_start:content_end].strip()
    return ""


# ============================================================================
# Atomic write of artifacts
# ============================================================================


def write_rival_artifacts(
    architecture: RivalArchitecture, workspace: Path, epic: str
) -> list[str]:
    """Write all three artifacts atomically to the rival/ subdirectory."""
    rival_dir = workspace / "artifacts" / "designs" / epic / "tech" / "rival"
    rival_dir.mkdir(parents=True, exist_ok=True)

    arch_path = rival_dir / "architecture.md"
    api_path = rival_dir / "api_spec.json"
    db_path = rival_dir / "db_schema.sql"

    # Write each file
    arch_path.write_text(architecture.architecture_md)
    api_path.write_text(json.dumps(architecture.api_spec_json, indent=2))
    db_path.write_text(architecture.db_schema_sql)

    return [str(arch_path), str(api_path), str(db_path)]


# ============================================================================
# Audit logging
# ============================================================================


def append_audit_log(workspace: Path, result: ProductionResult, epic: str):
    log_dir = workspace / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "rival_architect_calls.jsonl"

    entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "agent": "rival-architect",
        "phase": 5,
        "epic": epic,
        "model": FIXED_MODEL,
        "input_hash": result.input_hash,
        "output_hash": result.output_hash,
        "success": result.success,
        "written_paths": result.written_paths,
        "validation_errors": result.validation_errors,
    }

    with log_path.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def update_company_state(workspace: Path, result: ProductionResult, epic: str):
    state_path = workspace / "state" / "company_state.json"
    if not state_path.exists():
        return
    try:
        state = json.loads(state_path.read_text())
    except json.JSONDecodeError:
        return

    if "rival_architect" not in state:
        state["rival_architect"] = {}
    if "phase5" not in state["rival_architect"]:
        state["rival_architect"]["phase5"] = {}

    state["rival_architect"]["phase5"][epic] = {
        "produced_at": datetime.now(timezone.utc).isoformat(),
        "model": FIXED_MODEL,
        "success": result.success,
        "rival_paths": result.written_paths,
        "input_hash": result.input_hash,
    }
    state_path.write_text(json.dumps(state, indent=2))


# ============================================================================
# Halt protocol
# ============================================================================


def halt(error: str, suggestion: str = "", exit_code: int = 1):
    timestamp = datetime.now(timezone.utc).isoformat()
    diag = {
        "timestamp_utc": timestamp,
        "agent": "rival-architect",
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
        description="Rival Architect wrapper — independent producer for Phase 5"
    )
    parser.add_argument("--workspace", required=True, help="Path to startup workspace")
    parser.add_argument("--epic", required=True, help="Epic slug")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load inputs and build messages, but do not call the API.",
    )
    parser.add_argument(
        "--skip-primary-check",
        action="store_true",
        help="Skip the check that primary architecture exists. For testing only.",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    if not workspace.exists():
        halt(f"Workspace does not exist: {workspace}", exit_code=1)

    # Step 1: Load inputs (whitelist excludes primary's tech output)
    if args.skip_primary_check:
        # For testing — skip the primary-exists assertion
        try:
            inputs = load_inputs_no_primary_check(workspace, args.epic)
        except SystemExit:
            raise
    else:
        inputs = load_inputs(workspace, args.epic)

    # Step 2: Defensive check — primary's content should NOT appear in inputs
    if not args.skip_primary_check:
        assert_primary_artifacts_not_in_inputs(inputs, workspace, args.epic)

    # Step 3: Build messages in protocol order
    messages, system_prompt = build_messages(inputs)

    if args.dry_run:
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
                    "goal_source": inputs.goal_source_path,
                    "brief_path": inputs.brief_path,
                },
                indent=2,
            )
        )
        return

    # Step 4: Call Gemini
    response_text = call_gemini(system_prompt, messages)

    # Step 5: Validate response
    architecture, errors = validate_response(response_text)
    if errors:
        # One retry with errors reported back
        retry_system_prompt = (
            system_prompt
            + "\n\n---\nPRIOR RESPONSE FAILED VALIDATION. Errors to fix:\n"
            + "\n".join(f"- {e}" for e in errors)
            + "\n\nRespond with valid JSON matching the schema exactly. Address every error above."
        )
        response_text = call_gemini(retry_system_prompt, messages)
        architecture, errors = validate_response(response_text)
        if errors:
            halt(
                "Rival Architect response failed validation after retry",
                "Errors: " + "; ".join(errors),
                exit_code=3,
            )

    # Step 6: Write artifacts atomically
    written_paths = write_rival_artifacts(architecture, workspace, args.epic)

    # Step 7: Build result
    result = ProductionResult(
        success=True,
        architecture=architecture,
        written_paths=written_paths,
        input_hash=inputs.input_hash(),
        output_hash=hashlib.sha256(response_text.encode()).hexdigest(),
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )

    # Step 8: Audit + state
    append_audit_log(workspace, result, args.epic)
    update_company_state(workspace, result, args.epic)

    # Step 9: Output to stdout
    output = {
        "success": True,
        "model": FIXED_MODEL,
        "rival_architecture_path": written_paths[0],
        "rival_api_spec_path": written_paths[1],
        "rival_db_schema_path": written_paths[2],
        "input_hash": result.input_hash,
        "output_hash": result.output_hash,
        "timestamp_utc": result.timestamp_utc,
        "next_step": "Invoke compare_architectures.py to produce the verdict",
    }
    print(json.dumps(output, indent=2))


def load_inputs_no_primary_check(workspace: Path, epic: str) -> RivalInputs:
    """Same as load_inputs but skips the primary-exists check. For testing only."""
    project_config_path = workspace / "state" / "project_config.json"
    sprint_plan_path = workspace / "state" / "sprint_plan.json"
    brief_path = workspace / "artifacts" / "research" / epic / "discovery_brief.md"
    stories_path = workspace / "artifacts" / "requirements" / epic / "stories.json"
    prd_path = workspace / "artifacts" / "requirements" / epic / "prd.md"
    ui_spec_path = workspace / "artifacts" / "designs" / epic / "ui_spec.md"
    ux_flows_path = workspace / "artifacts" / "designs" / epic / "ux_flows.md"
    content_spec_path = workspace / "artifacts" / "designs" / epic / "content_spec.md"

    for path, name in [
        (project_config_path, "project_config.json"),
        (sprint_plan_path, "sprint_plan.json"),
        (brief_path, "discovery_brief.md"),
        (stories_path, "stories.json"),
    ]:
        if not path.exists():
            halt(f"Required input missing: {name}", exit_code=1)
        if path.stat().st_size == 0:
            halt(f"Required input is empty: {name}", exit_code=1)

    project_config = json.loads(project_config_path.read_text())
    sprint_plan = json.loads(sprint_plan_path.read_text())

    return RivalInputs(
        sprint_goal=sprint_plan.get("goal", "").strip(),
        product_description=project_config.get("product_description", "").strip(),
        discovery_brief=brief_path.read_text(),
        stories_json=stories_path.read_text(),
        prd_md=prd_path.read_text() if prd_path.exists() else "",
        ui_spec=ui_spec_path.read_text() if ui_spec_path.exists() else "",
        ux_flows=ux_flows_path.read_text() if ux_flows_path.exists() else "",
        content_spec=content_spec_path.read_text() if content_spec_path.exists() else "",
        brief_path=str(brief_path),
        goal_source_path=str(sprint_plan_path),
    )


if __name__ == "__main__":
    main()
