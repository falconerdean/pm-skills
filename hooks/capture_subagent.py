#!/usr/bin/env python3
"""Capture subagent lifecycle events AND inject phase-relevant learnings on SubagentStart.

This hook fires on both SubagentStart and SubagentStop events (distinguished by
the CLAUDE_HOOK_EVENT env var set by settings.json).

Behaviors:
    - SubagentStart: log the event + inject phase-relevant learnings via additionalContext
    - SubagentStop: log the event only

Memory injection rules (SubagentStart only):
    - Read the current phase from the workspace state (if startup-engine-exp is active)
    - Call ~/.claude/memory/query.py to retrieve phase-relevant learnings
    - Return them as hookSpecificOutput.additionalContext for the sub-agent
    - SKIP injection for agents whose description starts with "silent-observer:"
      (the cold-read principle — silent observers must not be anchored by prior context)
    - Fall back to process-only learnings for silent observers (so they still benefit
      from "how to do your job better" knowledge without task-specific contamination)

Failure mode: if any step fails, log the failure and exit cleanly without injection.
The sub-agent still starts, just without injected memory. This is a recoverable
degraded mode, not a halt.

See: ~/.claude/memory/query.py for the filtering/ranking/packing logic.
See: ~/Documents/VectorDB_Agent_Memory_Research_20260410/application_report.md
     for the architectural rationale (Finding 1: SubagentStart Is the Push Layer).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ============================================================================
# Constants
# ============================================================================

CAPTURE_DIR = Path.home() / ".claude" / "learning" / "captures"
SUBAGENT_LOG = CAPTURE_DIR / "subagent_events.jsonl"
INJECTION_LOG = CAPTURE_DIR / "memory_injections.jsonl"

QUERY_SCRIPT = Path.home() / ".claude" / "memory" / "query.py"

# Default injection budget — Claude Code hook limit is 10K chars, leave headroom
INJECTION_CHAR_BUDGET = 8000
INJECTION_TOP_N = 5

# Silent observer naming convention from the research
SILENT_OBSERVER_PREFIX = "silent-observer:"

# Locations to look for current phase + project state
# Primary: running startup workspace
# Fallback: the workspace template path
WORKSPACE_CANDIDATES = [
    Path.home() / "startup-workspace",
    Path("/tmp/startup-workspace"),
]

CAPTURE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Event logging (always runs — preserves existing behavior)
# ============================================================================


def log_subagent_event(hook_type: str, event_data: dict):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": hook_type,
        "session_id": event_data.get("session_id", "unknown"),
        "agent_id": event_data.get("agent_id"),
        "agent_type": event_data.get("agent_type"),
        "agent_description": event_data.get("agent_description"),
        "transcript_path": event_data.get("transcript_path"),
        "stop_reason": event_data.get("stop_reason"),
    }
    with open(SUBAGENT_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")


def log_injection(event_data: dict, outcome: dict):
    """Separate audit log for injections — what was injected, to whom, with what result."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": event_data.get("session_id", "unknown"),
        "agent_id": event_data.get("agent_id"),
        "agent_description": event_data.get("agent_description"),
        **outcome,
    }
    with open(INJECTION_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")


# ============================================================================
# Workspace state detection
# ============================================================================


def detect_workspace() -> Path | None:
    """Find the active startup workspace, if any."""
    for candidate in WORKSPACE_CANDIDATES:
        state_file = candidate / "state" / "company_state.json"
        if state_file.exists():
            return candidate
    return None


def read_current_phase(workspace: Path) -> tuple[str, str]:
    """Return (phase, project_slug) from the workspace state.

    Returns ('', 'global') if state is unreadable or incomplete.
    """
    state_file = workspace / "state" / "company_state.json"
    config_file = workspace / "state" / "project_config.json"

    phase = ""
    project = "global"

    try:
        if state_file.exists():
            state = json.loads(state_file.read_text())
            phase = state.get("sdlc", {}).get("current_phase", "") or state.get("current_phase", "")
    except (json.JSONDecodeError, OSError):
        pass

    try:
        if config_file.exists():
            config = json.loads(config_file.read_text())
            project = config.get("project_slug", "") or config.get("project", "") or "global"
    except (json.JSONDecodeError, OSError):
        pass

    return phase, project


# ============================================================================
# Memory query (delegates to ~/.claude/memory/query.py)
# ============================================================================


def query_memory(
    phase: str,
    project: str,
    learning_types: list[str],
) -> tuple[str, int]:
    """Call query.py as a subprocess and return (injection_text, entry_count).

    Using subprocess rather than import keeps the hook decoupled from the
    query module's internals. If query.py errors, the hook still exits cleanly.
    """
    if not QUERY_SCRIPT.exists():
        return "", 0

    try:
        # First get the injection text
        result = subprocess.run(
            [
                sys.executable,
                str(QUERY_SCRIPT),
                "--phase", phase,
                "--project", project,
                "--top-n", str(INJECTION_TOP_N),
                "--char-budget", str(INJECTION_CHAR_BUDGET),
                "--learning-types", ",".join(learning_types),
                "--format", "injection",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        injection_text = (result.stdout or "").strip()

        # Then get the count for logging
        count_result = subprocess.run(
            [
                sys.executable,
                str(QUERY_SCRIPT),
                "--phase", phase,
                "--project", project,
                "--top-n", str(INJECTION_TOP_N),
                "--char-budget", str(INJECTION_CHAR_BUDGET),
                "--learning-types", ",".join(learning_types),
                "--format", "count",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        try:
            entry_count = int((count_result.stdout or "0").strip())
        except ValueError:
            entry_count = 0

        return injection_text, entry_count
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return "", 0


# ============================================================================
# Silent observer detection
# ============================================================================


def is_silent_observer(event_data: dict) -> bool:
    """Check if this agent is a silent observer (cold-read role).

    The convention from the research is that the COO spawns silent observers
    with description starting with 'silent-observer:'. This hook identifies
    them by that prefix and applies the cold-read protection: inject only
    process-type learnings, not task-specific context.
    """
    desc = (event_data.get("agent_description") or "").strip()
    return desc.lower().startswith(SILENT_OBSERVER_PREFIX)


# ============================================================================
# Main
# ============================================================================


def main():
    try:
        event_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # No valid JSON on stdin — exit cleanly without doing anything
        sys.exit(0)

    hook_type = os.environ.get("CLAUDE_HOOK_EVENT", "subagent_event")

    # Always log the event
    log_subagent_event(hook_type, event_data)

    # Memory injection only fires on SubagentStart
    if hook_type != "subagent_start":
        sys.exit(0)

    # Detect workspace and current phase
    workspace = detect_workspace()
    if workspace is None:
        # No active startup workspace — nothing to inject
        log_injection(event_data, {"status": "skipped", "reason": "no_active_workspace"})
        sys.exit(0)

    phase, project = read_current_phase(workspace)
    if not phase:
        log_injection(event_data, {"status": "skipped", "reason": "no_current_phase"})
        sys.exit(0)

    # Determine learning types based on silent observer rule
    silent = is_silent_observer(event_data)
    if silent:
        learning_types = ["process"]
        injection_mode = "silent_observer_process_only"
    else:
        learning_types = ["process", "factual", "task_specific"]
        injection_mode = "full"

    # Query memory
    injection_text, entry_count = query_memory(
        phase=phase,
        project=project,
        learning_types=learning_types,
    )

    if not injection_text or entry_count == 0:
        log_injection(
            event_data,
            {
                "status": "skipped",
                "reason": "no_matching_entries",
                "phase": phase,
                "project": project,
                "learning_types": learning_types,
                "mode": injection_mode,
            },
        )
        sys.exit(0)

    # Emit the hookSpecificOutput to stdout — Claude Code reads this and
    # injects additionalContext into the sub-agent's context before it
    # processes its first instruction.
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SubagentStart",
            "additionalContext": injection_text,
        }
    }
    print(json.dumps(output))

    # Log successful injection
    log_injection(
        event_data,
        {
            "status": "injected",
            "phase": phase,
            "project": project,
            "learning_types": learning_types,
            "mode": injection_mode,
            "entry_count": entry_count,
            "injection_char_length": len(injection_text),
        },
    )

    sys.exit(0)


if __name__ == "__main__":
    main()
