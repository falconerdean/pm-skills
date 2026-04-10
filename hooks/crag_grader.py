#!/usr/bin/env python3
"""CRAG Grader — PostToolUse hook that blocks phase completions ignoring critical learnings.

This hook fires on every Write tool call. When the written file is
`{workspace}/state/company_state.json` AND the new content sets any
`phases.{phase}.status = "complete"`, the grader runs:

  1. Identify which phase was just completed
  2. Load all critical (severity=critical) learnings for that phase
  3. Read the phase's primary deliverable
  4. For each critical learning, ask Claude Haiku: "does the deliverable
     acknowledge or address this learning?"
  5. If any critical learning returns "no": emit decision=block with the
     specific learning and required action

Design principles:
    - Deterministic detection (Python regex on the JSON write content)
    - Bounded LLM calls (one Haiku call per critical learning, ~$0.01 total)
    - Specific block reasons with citation (the learning ID, the missing rule)
    - Recoverable failure: if Haiku is unreachable, log and ALLOW (do not
      silently block on infrastructure issues)
    - Audit log of every grade attempt

This is the third layer of the memory architecture:
    Layer 1 (push) — SubagentStart hook injects learnings into VP agents
    Layer 2 (pull) — VP phase prompts call query.py via Bash
    Layer 3 (block) — THIS hook catches deliverables that ignored layer 1+2

See: ~/Documents/VectorDB_Agent_Memory_Research_20260410/application_report.md Finding 5
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ============================================================================
# Constants
# ============================================================================

CAPTURE_DIR = Path.home() / ".claude" / "learning" / "captures"
GRADER_LOG = CAPTURE_DIR / "crag_grader.jsonl"
QUERY_SCRIPT = Path.home() / ".claude" / "memory" / "query.py"
HAIKU_MODEL = "claude-haiku-4-5-20251001"
DELIVERABLE_TRUNCATE_CHARS = 6000

# Phase → primary deliverable path pattern under {workspace}/artifacts/
PHASE_DELIVERABLES = {
    "research": "research/{epic}/discovery_brief.md",
    "requirements": "requirements/{epic}/stories.json",
    "ux_design": "designs/{epic}/ui_spec.md",
    "tech_design": "designs/{epic}/tech/architecture.md",
    "development": "code/{epic}/",
    "testing": "tests/{epic}/test_results.json",
    "deployment": "deployments/{epic}/deploy_log.md",
}

CAPTURE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Hook event detection
# ============================================================================


def is_company_state_write(event_data: dict) -> bool:
    """Return True if this PostToolUse event is a Write to company_state.json."""
    tool_name = event_data.get("tool_name", "")
    if tool_name != "Write":
        return False

    tool_input = event_data.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "")
    return "company_state.json" in file_path and "/state/" in file_path


def detect_completed_phase(event_data: dict) -> str:
    """Parse the written content to find which phase was just marked complete.

    Returns the phase name (e.g., 'tech_design') or empty string if no phase
    completion was detected in this write.
    """
    tool_input = event_data.get("tool_input", {}) or {}
    content = tool_input.get("content", "") or ""

    # Try to parse the written JSON
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return ""

    sdlc = data.get("sdlc", {}) or {}
    phases = sdlc.get("phases", {}) or {}

    # Find any phase whose status is "complete"
    # The hook fires on every Write — we want the FIRST completed phase that
    # we have a deliverable mapping for, since that's the one being graded.
    completed_phases = [name for name, info in phases.items() if isinstance(info, dict) and info.get("status") == "complete"]

    if not completed_phases:
        return ""

    # Prefer the most recently transitioned phase if there's a current_phase marker
    current = sdlc.get("current_phase", "")
    if current and current in completed_phases:
        return current

    # Otherwise return the first completed phase that has a deliverable mapping
    for phase in completed_phases:
        if phase in PHASE_DELIVERABLES:
            return phase

    return ""


def detect_workspace(event_data: dict) -> Path | None:
    """Find the workspace from the file_path being written."""
    tool_input = event_data.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "")
    if not file_path:
        return None

    # company_state.json lives at {workspace}/state/company_state.json
    p = Path(file_path)
    if p.name == "company_state.json" and p.parent.name == "state":
        return p.parent.parent

    return None


def detect_epic(workspace: Path) -> str:
    """Try to read the current epic slug from sprint_plan.json."""
    sprint_plan_path = workspace / "state" / "sprint_plan.json"
    if not sprint_plan_path.exists():
        return ""
    try:
        data = json.loads(sprint_plan_path.read_text())
        return str(data.get("epic", "") or data.get("current_epic", ""))
    except (json.JSONDecodeError, OSError):
        return ""


def detect_project(workspace: Path) -> str:
    """Read the project slug from project_config.json."""
    config_path = workspace / "state" / "project_config.json"
    if not config_path.exists():
        return "global"
    try:
        data = json.loads(config_path.read_text())
        return str(data.get("project_slug", "") or data.get("project", "") or "global")
    except (json.JSONDecodeError, OSError):
        return "global"


# ============================================================================
# Critical learnings retrieval
# ============================================================================


def load_critical_learnings(phase: str, project: str) -> list[dict]:
    """Query memory for CRITICAL severity learnings for this phase + project.

    Returns a list of dicts: {id, name, description, consequence, rule, path}
    """
    if not QUERY_SCRIPT.exists():
        return []

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(QUERY_SCRIPT),
                "--phase", phase,
                "--project", project,
                "--format", "critical-only",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return json.loads(result.stdout or "[]")
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, json.JSONDecodeError):
        return []


def load_deliverable(workspace: Path, phase: str, epic: str) -> str:
    """Load the primary deliverable for a phase. Empty string if not found."""
    pattern = PHASE_DELIVERABLES.get(phase, "")
    if not pattern:
        return ""

    rel_path = pattern.format(epic=epic)
    full_path = workspace / "artifacts" / rel_path

    if not full_path.exists():
        return ""

    if full_path.is_dir():
        # For development phase, glob the directory and concatenate
        parts = []
        for fp in sorted(full_path.rglob("*"))[:20]:
            if fp.is_file() and fp.stat().st_size < 50_000:
                try:
                    parts.append(f"--- {fp.name} ---\n{fp.read_text()}")
                except (OSError, UnicodeDecodeError):
                    continue
        return "\n\n".join(parts)[:DELIVERABLE_TRUNCATE_CHARS]

    try:
        return full_path.read_text()[:DELIVERABLE_TRUNCATE_CHARS]
    except (OSError, UnicodeDecodeError):
        return ""


# ============================================================================
# Haiku grader call (one call per critical learning, bounded)
# ============================================================================


def grade_acknowledgment(learning: dict, deliverable_text: str) -> dict:
    """Ask Haiku whether the deliverable acknowledges the learning.

    Returns: {"acknowledged": bool, "evidence": str, "error": str | None}
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"acknowledged": True, "evidence": "", "error": "no_api_key"}

    try:
        import anthropic  # type: ignore
    except ImportError:
        return {"acknowledged": True, "evidence": "", "error": "anthropic_sdk_missing"}

    rule = learning.get("rule", "") or learning.get("description", "")
    consequence = learning.get("consequence", "")

    prompt = f"""You are a quality gate. Answer in this exact JSON format:
{{"acknowledged": true|false, "evidence": "one sentence quoting the relevant line from the deliverable, OR what is missing"}}

LEARNING (a critical lesson from past sprints):
{rule}

CONSEQUENCE IF IGNORED:
{consequence}

DELIVERABLE TO CHECK (truncated):
{deliverable_text}

Question: Does the deliverable acknowledge or address this learning? Look for explicit citation, application, or demonstration that the team considered the lesson. Vague mentions do not count.

Respond with ONLY the JSON object, no preamble."""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()

        # Extract JSON from response (may be wrapped in code fences)
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if not json_match:
            return {"acknowledged": True, "evidence": "grader output unparseable", "error": "unparseable"}

        result = json.loads(json_match.group(0))
        return {
            "acknowledged": bool(result.get("acknowledged", True)),
            "evidence": str(result.get("evidence", "")),
            "error": None,
        }
    except Exception as e:
        return {"acknowledged": True, "evidence": "", "error": f"call_failed: {e}"}


# ============================================================================
# Audit logging
# ============================================================================


def log_grade(record: dict):
    record["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(GRADER_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")


# ============================================================================
# Main
# ============================================================================


def main():
    try:
        event_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    # Filter: only fire on Write to company_state.json
    if not is_company_state_write(event_data):
        sys.exit(0)

    # Filter: only fire when a phase is being marked complete
    completed_phase = detect_completed_phase(event_data)
    if not completed_phase:
        sys.exit(0)

    workspace = detect_workspace(event_data)
    if workspace is None:
        log_grade({"status": "skipped", "reason": "no_workspace_detected"})
        sys.exit(0)

    epic = detect_epic(workspace)
    project = detect_project(workspace)

    # Load critical learnings for this phase
    critical_learnings = load_critical_learnings(completed_phase, project)
    if not critical_learnings:
        log_grade({
            "status": "passed_no_learnings",
            "phase": completed_phase,
            "epic": epic,
            "project": project,
        })
        sys.exit(0)

    # Load the deliverable
    deliverable = load_deliverable(workspace, completed_phase, epic)
    if not deliverable:
        log_grade({
            "status": "skipped_no_deliverable",
            "phase": completed_phase,
            "epic": epic,
            "expected_path": PHASE_DELIVERABLES.get(completed_phase, "unknown"),
        })
        sys.exit(0)

    # Grade each critical learning
    blocking_learnings = []
    grading_errors = []
    for learning in critical_learnings:
        result = grade_acknowledgment(learning, deliverable)
        if result.get("error"):
            grading_errors.append({"learning_id": learning.get("id"), "error": result["error"]})
            continue
        if not result.get("acknowledged"):
            blocking_learnings.append({
                "learning_id": learning.get("id"),
                "name": learning.get("name", ""),
                "rule": learning.get("rule", "")[:500],
                "consequence": learning.get("consequence", "")[:500],
                "evidence": result.get("evidence", ""),
            })

    # Recoverable infrastructure failure: if Haiku errored on every learning,
    # ALLOW the write through but log loudly. Do not silently block on infra.
    if grading_errors and len(grading_errors) == len(critical_learnings):
        log_grade({
            "status": "skipped_grader_unavailable",
            "phase": completed_phase,
            "epic": epic,
            "errors": grading_errors,
        })
        sys.exit(0)

    if not blocking_learnings:
        log_grade({
            "status": "approved",
            "phase": completed_phase,
            "epic": epic,
            "checked_learnings": len(critical_learnings),
            "errors": grading_errors,
        })
        sys.exit(0)

    # BLOCK — emit decision=block with cited reason
    reason_lines = [
        f"Phase '{completed_phase}' cannot advance — the deliverable does not acknowledge "
        f"{len(blocking_learnings)} critical learning(s) that the team has previously been burned by:",
        "",
    ]
    for bl in blocking_learnings:
        reason_lines.append(f"  • [{bl['learning_id']}] {bl['name']}")
        reason_lines.append(f"    Rule: {bl['rule']}")
        reason_lines.append(f"    Consequence if ignored: {bl['consequence']}")
        reason_lines.append(f"    Grader finding: {bl['evidence']}")
        reason_lines.append("")
    reason_lines.append(
        "Required: revise the deliverable to explicitly acknowledge each learning above "
        "with a specific citation (where in the deliverable the lesson is applied), then "
        "re-write the phase completion."
    )

    block_output = {
        "decision": "block",
        "reason": "\n".join(reason_lines),
    }

    log_grade({
        "status": "blocked",
        "phase": completed_phase,
        "epic": epic,
        "blocking_count": len(blocking_learnings),
        "blocking_learnings": [bl["learning_id"] for bl in blocking_learnings],
    })

    print(json.dumps(block_output))
    sys.exit(0)


if __name__ == "__main__":
    main()
