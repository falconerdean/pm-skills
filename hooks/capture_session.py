#!/usr/bin/env python3
"""
Capture session start/stop events.
Records session metadata for the learning pipeline.
"""
import json
import sys
import os
from datetime import datetime, timezone

CAPTURE_DIR = os.path.expanduser("~/.claude/learning/captures")
SESSION_LOG = os.path.join(CAPTURE_DIR, "session_events.jsonl")

os.makedirs(CAPTURE_DIR, exist_ok=True)

try:
    event_data = json.load(sys.stdin)
except (json.JSONDecodeError, EOFError):
    sys.exit(0)

hook_type = os.environ.get("CLAUDE_HOOK_EVENT", "session_event")

record = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "event_type": hook_type,
    "session_id": event_data.get("session_id", "unknown"),
    "cwd": event_data.get("cwd", os.getcwd()),
    "model": event_data.get("model"),
    "source": event_data.get("source"),
    "agent_type": event_data.get("agent_type"),
}

with open(SESSION_LOG, "a") as f:
    f.write(json.dumps(record) + "\n")

sys.exit(0)
