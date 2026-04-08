#!/usr/bin/env python3
"""
Capture subagent lifecycle events (start and stop).
Tracks which subagents were spawned, their types, and transcript paths.
"""
import json
import sys
import os
from datetime import datetime, timezone

CAPTURE_DIR = os.path.expanduser("~/.claude/learning/captures")
SUBAGENT_LOG = os.path.join(CAPTURE_DIR, "subagent_events.jsonl")

os.makedirs(CAPTURE_DIR, exist_ok=True)

try:
    event_data = json.load(sys.stdin)
except (json.JSONDecodeError, EOFError):
    sys.exit(0)

# Determine if this is start or stop based on the hook type
# The hook name is passed via the environment or inferred from context
hook_type = os.environ.get("CLAUDE_HOOK_EVENT", "subagent_event")

record = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "event_type": hook_type,
    "session_id": event_data.get("session_id", "unknown"),
    "agent_id": event_data.get("agent_id"),
    "agent_type": event_data.get("agent_type"),
    "transcript_path": event_data.get("transcript_path"),
    "stop_reason": event_data.get("stop_reason"),
}

with open(SUBAGENT_LOG, "a") as f:
    f.write(json.dumps(record) + "\n")

sys.exit(0)
