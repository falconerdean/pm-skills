#!/usr/bin/env python3
"""
SDLC Phase State Machine for the AI Startup Engine.
Determines the next phase based on current state and artifact existence.
Detects artifacts, marks complete, AND advances in a single invocation.

Usage: python3 advance_phase.py --workspace ~/startup-workspace
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone


# Phase sequence (excluding continuous_intel which runs independently)
PHASE_ORDER = [
    "planning",
    "research",
    "requirements",
    "ux_design",
    "tech_design",
    "development",
    "testing",
    "deployment",
    "growth",
    "evolution",
]

# What artifact each phase must produce to be considered complete
PHASE_ARTIFACTS = {
    "planning":     ["state/sprint_plan.json"],
    "research":     ["artifacts/research/{epic}/discovery_brief.md"],
    "requirements": ["artifacts/requirements/{epic}/stories.json"],
    "ux_design":    ["artifacts/designs/{epic}/ux_flows.md", "artifacts/designs/{epic}/ui_spec.md"],
    "tech_design":  ["artifacts/designs/{epic}/tech/architecture.md", "artifacts/designs/{epic}/tech/api_spec.json"],
    "development":  [],  # Checked via git branch/PR existence
    "testing":      ["artifacts/tests/{epic}/test_results.json"],
    "deployment":   ["artifacts/deployments/{epic}/deploy_log.md"],
    "growth":       ["intel/growth/launch_{epic}.md"],
    "evolution":    ["reviews/retrospectives/sprint_{sprint}.md"],
}

# Phases that require CEO approval before advancing
CEO_GATES = {"deployment"}

# Phases that are optional CEO checkpoints
CEO_CHECKPOINTS = {"ux_design"}


def load_state(workspace: Path) -> dict:
    state_file = workspace / "state" / "company_state.json"
    if not state_file.exists():
        print("ERROR: company_state.json not found. Run /startup-engine to initialize.")
        sys.exit(1)
    with open(state_file) as f:
        return json.load(f)


def save_state(workspace: Path, state: dict):
    state_file = workspace / "state" / "company_state.json"
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)


def check_artifacts(workspace: Path, phase: str, epic: str, sprint: int) -> bool:
    """Check if all required artifacts for a phase exist."""
    artifacts = PHASE_ARTIFACTS.get(phase, [])
    if not artifacts:
        return True  # No artifact requirement (e.g., development checked differently)

    for artifact_pattern in artifacts:
        artifact_path = artifact_pattern.format(epic=epic, sprint=sprint)
        full_path = workspace / artifact_path
        if not full_path.exists():
            return False
    return True


def get_next_phase(current: str) -> str:
    """Get the next phase in the SDLC loop."""
    idx = PHASE_ORDER.index(current)
    next_idx = (idx + 1) % len(PHASE_ORDER)
    return PHASE_ORDER[next_idx]


def advance_to_next(state: dict, current_phase: str, workspace: Path) -> dict:
    """Mark current phase complete and advance to next phase in one step."""
    now = datetime.now(timezone.utc).isoformat()
    next_phase = get_next_phase(current_phase)

    # Check CEO gates before advancing
    if current_phase in CEO_GATES:
        awaiting = state["sdlc"]["phases"][current_phase].get("awaiting_ceo_approval", False)
        if awaiting:
            print(f"BLOCKED: Phase '{current_phase}' awaiting CEO approval.")
            print(f"  Review: reviews/ceo_reviews/deploy_{state['sprint'].get('epic', 'unknown')}.md")
            return state

    # Mark current phase complete
    state["sdlc"]["phases"][current_phase]["status"] = "complete"
    state["sdlc"]["phases"][current_phase]["completed_at"] = now

    # Advance to next phase
    state["sdlc"]["current_phase"] = next_phase
    state["sdlc"]["phase_number"] = PHASE_ORDER.index(next_phase) + 1
    state["sdlc"]["phases"][next_phase]["status"] = "in_progress"
    state["sdlc"]["phases"][next_phase]["started_at"] = now

    # If looping back to planning, increment sprint
    if next_phase == "planning" and current_phase == "evolution":
        state["sprint"]["number"] += 1
        print(f"NEW SPRINT: #{state['sprint']['number']}")

    print(f"ADVANCE: {current_phase} → {next_phase}")
    print(f"State updated. Next agent should be spawned for: {next_phase}")

    return state


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "--workspace":
        print("Usage: python3 advance_phase.py --workspace ~/startup-workspace")
        sys.exit(1)

    workspace = Path(sys.argv[2]).expanduser()
    state = load_state(workspace)

    current_phase = state["sdlc"]["current_phase"]
    epic = state["sprint"].get("epic", "unknown")
    sprint = state["sprint"].get("number", 1)
    phase_status = state["sdlc"]["phases"].get(current_phase, {}).get("status", "pending")

    print(f"Current phase: {current_phase} (status: {phase_status})")
    print(f"Sprint #{sprint}, Epic: {epic}")

    if phase_status == "complete":
        # Already marked complete — just advance
        state = advance_to_next(state, current_phase, workspace)
        save_state(workspace, state)

    elif phase_status in ("pending", "in_progress"):
        # Check if artifacts exist — if so, mark complete AND advance in one step
        if check_artifacts(workspace, current_phase, epic, sprint):
            print(f"COMPLETE: Artifacts found for '{current_phase}'.")
            state = advance_to_next(state, current_phase, workspace)
            save_state(workspace, state)
        else:
            missing = []
            for art in PHASE_ARTIFACTS.get(current_phase, []):
                path = workspace / art.format(epic=epic, sprint=sprint)
                if not path.exists():
                    missing.append(str(path))
            print(f"WAITING: Phase '{current_phase}' not yet complete.")
            if missing:
                print(f"  Missing artifacts:")
                for m in missing:
                    print(f"    - {m}")

    else:
        print(f"UNKNOWN status: {phase_status}")


if __name__ == "__main__":
    main()
