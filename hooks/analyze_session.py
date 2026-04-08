#!/usr/bin/env python3
"""
Session Analysis Pipeline — runs at the end of each Claude Code session (Stop hook).
Analyzes captured tool events and subagent activity from the session,
extracts patterns, and writes learnings to the memory system.

This is the core self-learning loop:
  Capture (hooks) → Analyze (this script) → Learn (memory files) → Apply (CLAUDE.md loads memories)
"""
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict
from pathlib import Path

# Paths
CAPTURE_DIR = Path.home() / ".claude" / "learning" / "captures"
ANALYSIS_DIR = Path.home() / ".claude" / "learning" / "analysis"
LEARNINGS_DIR = Path.home() / ".claude" / "learning" / "learnings"
# Memory dir is project-scoped in Claude Code; learnings go to the global learning dir instead
MEMORY_DIR = None  # Not used — learnings written to LEARNINGS_DIR

TOOL_LOG = CAPTURE_DIR / "tool_events.jsonl"
SUBAGENT_LOG = CAPTURE_DIR / "subagent_events.jsonl"
SESSION_LOG = CAPTURE_DIR / "session_events.jsonl"

ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
LEARNINGS_DIR.mkdir(parents=True, exist_ok=True)

def load_jsonl(path, since_hours=24):
    """Load JSONL entries from the last N hours."""
    if not path.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                ts = entry.get("timestamp", "")
                if ts:
                    entry_time = datetime.fromisoformat(ts)
                    if entry_time > cutoff:
                        entries.append(entry)
            except (json.JSONDecodeError, ValueError):
                continue
    return entries


def analyze_tool_patterns(events):
    """Analyze tool usage patterns for learning opportunities."""
    patterns = {
        "tool_frequency": Counter(),
        "error_tools": [],
        "most_edited_files": Counter(),
        "bash_commands": Counter(),
        "subagent_count": 0,
        "total_events": len(events),
    }

    for event in events:
        tool = event.get("tool_name", "unknown")
        patterns["tool_frequency"][tool] += 1

        # Track file edits
        summary = event.get("tool_input_summary", "")
        if tool in ("Edit", "Write", "Read") and summary:
            patterns["most_edited_files"][summary] += 1

        # Track bash commands
        if tool == "Bash" and summary:
            # Extract just the command name
            cmd = summary.split()[0] if summary else "unknown"
            patterns["bash_commands"][cmd] += 1

        # Track errors
        response = event.get("tool_response_summary", "")
        if response and ("error" in response.lower() or "failed" in response.lower()):
            patterns["error_tools"].append({
                "tool": tool,
                "input": summary[:100] if summary else "",
                "error": response[:100] if response else "",
            })

        # Count subagent activity
        if event.get("agent_id"):
            patterns["subagent_count"] += 1

    return patterns


def analyze_subagent_patterns(events):
    """Analyze subagent spawning patterns."""
    agents = defaultdict(lambda: {"starts": 0, "stops": 0, "types": set()})

    for event in events:
        agent_id = event.get("agent_id", "unknown")
        event_type = event.get("event_type", "")

        if "start" in event_type:
            agents[agent_id]["starts"] += 1
        elif "stop" in event_type:
            agents[agent_id]["stops"] += 1

        if event.get("agent_type"):
            agents[agent_id]["types"].add(event["agent_type"])

    return {
        "total_subagents": len(agents),
        "orphaned": sum(1 for a in agents.values() if a["starts"] > a["stops"]),
    }


def extract_learnings(tool_patterns, subagent_patterns):
    """Extract actionable learnings from analysis."""
    learnings = []

    # Learning: Frequent errors with specific tools
    if tool_patterns["error_tools"]:
        error_summary = Counter(e["tool"] for e in tool_patterns["error_tools"])
        for tool, count in error_summary.most_common(3):
            if count >= 2:
                examples = [e for e in tool_patterns["error_tools"] if e["tool"] == tool][:2]
                learnings.append({
                    "type": "error_pattern",
                    "severity": "medium",
                    "finding": f"Tool '{tool}' failed {count} times in last 24h",
                    "examples": examples,
                    "suggestion": f"Review recent {tool} failures for recurring issues",
                })

    # Learning: Heavy file churn (potential refactoring signal)
    hot_files = tool_patterns["most_edited_files"].most_common(5)
    for filepath, count in hot_files:
        if count >= 5:
            learnings.append({
                "type": "hot_file",
                "severity": "low",
                "finding": f"File '{filepath}' was accessed {count} times",
                "suggestion": "Consider if this file needs refactoring or better documentation",
            })

    # Learning: Subagent usage patterns
    if subagent_patterns["total_subagents"] > 0:
        learnings.append({
            "type": "subagent_usage",
            "severity": "info",
            "finding": f"{subagent_patterns['total_subagents']} subagents spawned, {subagent_patterns['orphaned']} may have been orphaned",
        })

    return learnings


def write_analysis_report(tool_patterns, subagent_patterns, learnings):
    """Write analysis report to file."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = ANALYSIS_DIR / f"analysis_{timestamp}.json"

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "period": "last_24h",
        "tool_patterns": {
            "frequency": dict(tool_patterns["tool_frequency"].most_common(20)),
            "total_events": tool_patterns["total_events"],
            "error_count": len(tool_patterns["error_tools"]),
            "subagent_event_count": tool_patterns["subagent_count"],
            "top_files": dict(tool_patterns["most_edited_files"].most_common(10)),
            "top_commands": dict(tool_patterns["bash_commands"].most_common(10)),
        },
        "subagent_patterns": subagent_patterns,
        "learnings": learnings,
        "learning_count": len(learnings),
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report_path


def update_memory_if_significant(learnings):
    """Write significant learnings to Claude Code memory system."""
    if not learnings:
        return

    significant = [l for l in learnings if l.get("severity") in ("medium", "high")]
    if not significant:
        return

    # Write to a learning summary file
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    learning_path = LEARNINGS_DIR / f"session_learnings_{timestamp}.md"

    content_parts = []
    if learning_path.exists():
        content_parts.append(learning_path.read_text())

    content_parts.append(f"\n## Session Analysis — {datetime.now(timezone.utc).isoformat()}\n")
    for learning in significant:
        content_parts.append(f"- **{learning['type']}**: {learning['finding']}")
        if learning.get("suggestion"):
            content_parts.append(f"  - Suggestion: {learning['suggestion']}")
        if learning.get("examples"):
            for ex in learning["examples"][:2]:
                content_parts.append(f"  - Example: {ex.get('input', '')} -> {ex.get('error', '')}")

    learning_path.write_text("\n".join(content_parts))


def cleanup_old_captures(days=7):
    """Remove capture entries older than N days to prevent unbounded growth."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    for log_path in [TOOL_LOG, SUBAGENT_LOG, SESSION_LOG]:
        if not log_path.exists():
            continue

        kept = []
        with open(log_path) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    ts = entry.get("timestamp", "")
                    if ts and datetime.fromisoformat(ts) > cutoff:
                        kept.append(line)
                except (json.JSONDecodeError, ValueError):
                    continue

        with open(log_path, "w") as f:
            f.writelines(kept)


def main():
    # Load recent events
    tool_events = load_jsonl(TOOL_LOG, since_hours=24)
    subagent_events = load_jsonl(SUBAGENT_LOG, since_hours=24)

    if not tool_events and not subagent_events:
        return  # Nothing to analyze

    # Analyze
    tool_patterns = analyze_tool_patterns(tool_events)
    subagent_patterns = analyze_subagent_patterns(subagent_events)
    learnings = extract_learnings(tool_patterns, subagent_patterns)

    # Write report
    report_path = write_analysis_report(tool_patterns, subagent_patterns, learnings)

    # Update memory if significant findings
    update_memory_if_significant(learnings)

    # Cleanup old data (keep 7 days)
    cleanup_old_captures(days=7)


if __name__ == "__main__":
    main()
