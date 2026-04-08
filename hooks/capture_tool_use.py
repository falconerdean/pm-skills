#!/usr/bin/env python3
"""
Capture all tool use events (fires for BOTH parent agents and subagents).
Appends structured JSONL to ~/.claude/learning/captures/tool_events.jsonl
"""
import json
import sys
import os
from datetime import datetime, timezone

CAPTURE_DIR = os.path.expanduser("~/.claude/learning/captures")
TOOL_LOG = os.path.join(CAPTURE_DIR, "tool_events.jsonl")

os.makedirs(CAPTURE_DIR, exist_ok=True)

try:
    event_data = json.load(sys.stdin)
except (json.JSONDecodeError, EOFError):
    sys.exit(0)

record = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "event_type": "post_tool_use",
    "session_id": event_data.get("session_id", "unknown"),
    "tool_name": event_data.get("tool_name", "unknown"),
    "agent_id": event_data.get("agent_id"),
    "agent_type": event_data.get("agent_type"),
    "tool_input_summary": None,
    "tool_response_summary": None,
}

# Capture tool input (truncated for storage)
tool_input = event_data.get("tool_input", {})
if isinstance(tool_input, dict):
    # For Bash, capture the command
    if "command" in tool_input:
        record["tool_input_summary"] = tool_input["command"][:500]
    # For Read/Write/Edit, capture the file path
    elif "file_path" in tool_input:
        record["tool_input_summary"] = tool_input["file_path"]
    # For Grep/Glob, capture the pattern
    elif "pattern" in tool_input:
        record["tool_input_summary"] = tool_input["pattern"][:200]
    else:
        record["tool_input_summary"] = json.dumps(tool_input)[:300]

# Capture response summary (truncated)
tool_response = event_data.get("tool_response", "")
if isinstance(tool_response, str):
    record["tool_response_summary"] = tool_response[:200]
elif isinstance(tool_response, dict):
    record["tool_response_summary"] = json.dumps(tool_response)[:200]

with open(TOOL_LOG, "a") as f:
    f.write(json.dumps(record) + "\n")

sys.exit(0)
