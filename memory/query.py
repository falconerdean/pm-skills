#!/usr/bin/env python3
"""Shared memory query script for phase-filtered learning retrieval.

Used by:
    - ~/.claude/hooks/capture_subagent.py  (SubagentStart memory injection for VP agents)
    - skills/startup-engine-exp/agents/*/scripts/invoke_*.py  (wrapper scripts)
    - skills/startup-engine-exp/agents/*/scripts/crag_grader.py  (phase-completion gate)

Design:
    - Backend-pluggable via a simple interface — MarkdownBackend now, ChromaBackend later
    - Deterministic filtering: (project matches OR global_applicable) AND phase in phases
    - Deterministic ranking: severity desc → was_burned_by desc → recency desc
    - Char-budget packing: pack highest-ranked entries until budget is hit

Usage (CLI):
    python3 ~/.claude/memory/query.py \
        --phase tech_design \
        --project insite-v6 \
        --top-n 5 \
        --char-budget 8000 \
        --learning-types process,factual,task_specific \
        --format injection

    Output modes:
        --format injection   Plain-text formatted for SubagentStart additionalContext
        --format json        Structured JSON for programmatic consumers
        --format count       Just the count of matching entries (for debugging)

Usage (import):
    from query import query_learnings
    text = query_learnings(phase="tech_design", project="insite-v6", top_n=5, char_budget=8000)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# ============================================================================
# Constants
# ============================================================================

# Memory directory — the existing pm-skills memory location
MEMORY_DIR = Path.home() / ".claude" / "projects" / "-Users-deanfalconer-GitHub-pm-skills" / "memory"
INDEX_FILE = MEMORY_DIR / "MEMORY.md"

# Severity ranks (higher = more important)
SEVERITY_SCORE = {
    "critical": 3,
    "high": 2,
    "medium": 1,
    "low": 0,
}

# All valid learning types (for --learning-types filter)
ALL_LEARNING_TYPES = {"process", "factual", "task_specific"}

# Default char budget per SubagentStart injection (Claude Code hooks limit is 10K)
DEFAULT_CHAR_BUDGET = 8000
DEFAULT_TOP_N = 5

# Entry format for injection — contextual retrieval style (Anthropic)
INJECTION_ENTRY_TEMPLATE = """[LEARNING-{id}] SEVERITY: {severity} | PHASE: {phases_str} | PROJECT: {project} | TYPE: {learning_type}
{description}
CONSEQUENCE: {consequence}
RULE: {rule}"""


# ============================================================================
# Data structures
# ============================================================================


@dataclass
class MemoryEntry:
    path: Path
    name: str
    description: str
    type: str  # feedback, project, user, reference
    body: str

    # Phase 3 extended schema
    severity: str = "medium"  # critical | high | medium | low
    was_burned_by: bool = False
    project: str = "global"
    global_applicable: bool = False
    phases: list[str] = field(default_factory=list)
    learning_type: str = "task_specific"  # process | factual | task_specific
    sprint: str = ""
    date: str = ""
    files: list[str] = field(default_factory=list)
    consequence: str = ""
    rule: str = ""

    def entry_id(self) -> str:
        """Short identifier derived from the filename."""
        return self.path.stem.upper().replace("_", "-")[:30]

    def phases_str(self) -> str:
        return ",".join(self.phases) if self.phases else "any"

    def format_for_injection(self) -> str:
        return INJECTION_ENTRY_TEMPLATE.format(
            id=self.entry_id(),
            severity=self.severity.upper(),
            phases_str=self.phases_str(),
            project=self.project,
            learning_type=self.learning_type,
            description=self.description.strip(),
            consequence=self.consequence.strip() if self.consequence else "(not documented)",
            rule=self.rule.strip() if self.rule else "(not documented)",
        )


# ============================================================================
# Frontmatter parsing
# ============================================================================


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML-like frontmatter from a markdown file.

    Returns (metadata_dict, body_text). If no frontmatter, returns ({}, text).

    This is a minimal YAML parser that handles only the fields we need:
        - Simple string values
        - Boolean values (true/false)
        - Simple lists (YAML block style: `- item`)
        - Multi-line values (indented continuation)
    """
    if not text.startswith("---"):
        return {}, text

    lines = text.split("\n")
    if len(lines) < 2 or lines[0] != "---":
        return {}, text

    # Find closing ---
    closing_idx = None
    for i in range(1, len(lines)):
        if lines[i] == "---":
            closing_idx = i
            break

    if closing_idx is None:
        return {}, text

    fm_text = "\n".join(lines[1:closing_idx])
    body = "\n".join(lines[closing_idx + 1 :]).strip()

    meta: dict = {}
    current_key: str | None = None
    current_list: list[str] | None = None

    for fm_line in fm_text.split("\n"):
        # Skip blank lines and comments
        stripped = fm_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # List item (must be indented)
        if fm_line.startswith("  - ") or fm_line.startswith("- "):
            item = fm_line.lstrip(" -").strip().strip('"').strip("'")
            if current_list is not None:
                current_list.append(item)
            continue

        # Key: value pair
        if ":" in fm_line and not fm_line.startswith(" "):
            # Flush any pending list
            if current_list is not None and current_key is not None:
                meta[current_key] = current_list
                current_list = None

            key, _, value = fm_line.partition(":")
            key = key.strip()
            value = value.strip()

            if not value:
                # Start of a list or multi-line value
                current_key = key
                current_list = []
                continue

            # Parse inline value
            current_key = key
            current_list = None
            meta[key] = parse_value(value)

    # Flush final list
    if current_list is not None and current_key is not None:
        meta[current_key] = current_list

    return meta, body


def parse_value(raw: str) -> Any:
    """Parse a single frontmatter value."""
    raw = raw.strip()

    # Quoted strings
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]

    # Inline lists like [a, b, c]
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip('"').strip("'") for item in inner.split(",")]

    # Booleans
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False

    # Numbers
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        pass

    return raw


# ============================================================================
# Backend interface
# ============================================================================


class MarkdownBackend:
    """Load memory entries from individual .md files with YAML frontmatter.

    Appropriate for corpora up to ~500 entries per the research.
    """

    def __init__(self, memory_dir: Path = MEMORY_DIR):
        self.memory_dir = memory_dir

    def load_all(self) -> list[MemoryEntry]:
        """Load every .md file in the memory directory (except MEMORY.md index)."""
        entries: list[MemoryEntry] = []
        if not self.memory_dir.exists():
            return entries

        for path in sorted(self.memory_dir.glob("*.md")):
            if path.name == "MEMORY.md":
                continue
            try:
                text = path.read_text()
            except (OSError, UnicodeDecodeError):
                continue

            meta, body = parse_frontmatter(text)
            if not meta:
                # File has no frontmatter — skip
                continue

            entry = MemoryEntry(
                path=path,
                name=meta.get("name", path.stem),
                description=meta.get("description", ""),
                type=meta.get("type", "unknown"),
                body=body,
                severity=str(meta.get("severity", "medium")).lower(),
                was_burned_by=bool(meta.get("was_burned_by", False)),
                project=str(meta.get("project", "global")),
                global_applicable=bool(meta.get("global_applicable", False)),
                phases=list(meta.get("phases") or []),
                learning_type=str(meta.get("learning_type", "task_specific")).lower(),
                sprint=str(meta.get("sprint", "")),
                date=str(meta.get("date", "")),
                files=list(meta.get("files") or []),
                consequence=str(meta.get("consequence", "")),
                rule=str(meta.get("rule", "")),
            )
            entries.append(entry)

        return entries

    def query(
        self,
        phase: str,
        project: str,
        top_n: int,
        char_budget: int,
        learning_types: set[str] | None = None,
    ) -> list[MemoryEntry]:
        """Filter, rank, and pack entries."""
        if learning_types is None:
            learning_types = ALL_LEARNING_TYPES

        all_entries = self.load_all()

        # Filter:
        # - Project: entry.project matches OR global OR global_applicable override
        # - Phase: if phase specified, entry.phases MUST explicitly contain it.
        #   Entries with empty phases list are NOT universal fallback — they
        #   are uncategorized and excluded from phase-filtered queries. This
        #   prevents uncategorized entries from contaminating every injection.
        #   If phase="" (empty), no phase filter is applied (used for global audits).
        # - Learning type: must be in the requested set
        candidates = [
            e
            for e in all_entries
            if (e.project == project or e.global_applicable or e.project == "global")
            and (not phase or phase in e.phases)
            and e.learning_type in learning_types
        ]

        # Rank: severity desc → was_burned_by desc → recency desc
        candidates.sort(
            key=lambda e: (
                SEVERITY_SCORE.get(e.severity, 0),
                int(e.was_burned_by),
                e.date,
            ),
            reverse=True,
        )

        # Pack within budget
        packed: list[MemoryEntry] = []
        chars_used = 0
        for entry in candidates[:top_n]:
            formatted = entry.format_for_injection()
            entry_len = len(formatted) + 2  # +2 for \n\n separator
            if chars_used + entry_len > char_budget and packed:
                break
            packed.append(entry)
            chars_used += entry_len

        return packed


def get_backend() -> MarkdownBackend:
    """Return the active backend. Future: check for Chroma and prefer it if present."""
    return MarkdownBackend()


# ============================================================================
# Public API
# ============================================================================


def query_learnings(
    phase: str = "",
    project: str = "global",
    top_n: int = DEFAULT_TOP_N,
    char_budget: int = DEFAULT_CHAR_BUDGET,
    learning_types: set[str] | None = None,
) -> str:
    """High-level query returning the formatted injection text.

    Empty string if no matches. Plain text suitable for direct injection into
    the SubagentStart hook's additionalContext or into a wrapper script's
    message payload.
    """
    backend = get_backend()
    entries = backend.query(
        phase=phase,
        project=project,
        top_n=top_n,
        char_budget=char_budget,
        learning_types=learning_types,
    )

    if not entries:
        return ""

    header = f"Sprint learnings relevant to phase '{phase or 'any'}' for project '{project}':\n\n"
    body = "\n\n".join(e.format_for_injection() for e in entries)
    return header + body


def query_raw(
    phase: str = "",
    project: str = "global",
    top_n: int = DEFAULT_TOP_N,
    char_budget: int = DEFAULT_CHAR_BUDGET,
    learning_types: set[str] | None = None,
) -> list[MemoryEntry]:
    """Return the raw MemoryEntry list (for programmatic consumers like the CRAG grader)."""
    backend = get_backend()
    return backend.query(
        phase=phase,
        project=project,
        top_n=top_n,
        char_budget=char_budget,
        learning_types=learning_types,
    )


def query_critical_for_phase(phase: str, project: str = "global") -> list[MemoryEntry]:
    """Return only CRITICAL severity entries for a phase — used by the CRAG grader."""
    backend = get_backend()
    entries = backend.query(
        phase=phase,
        project=project,
        top_n=50,
        char_budget=100_000,
        learning_types=ALL_LEARNING_TYPES,
    )
    return [e for e in entries if e.severity == "critical"]


# ============================================================================
# CLI
# ============================================================================


def main():
    parser = argparse.ArgumentParser(description="Query memory learnings with filters and ranking")
    parser.add_argument("--phase", default="", help="Current phase (e.g., tech_design, research)")
    parser.add_argument("--project", default="global", help="Current project slug (default: global)")
    parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N)
    parser.add_argument("--char-budget", type=int, default=DEFAULT_CHAR_BUDGET)
    parser.add_argument(
        "--learning-types",
        default="process,factual,task_specific",
        help="Comma-separated list: process,factual,task_specific",
    )
    parser.add_argument(
        "--format",
        choices=["injection", "json", "count", "critical-only"],
        default="injection",
    )
    args = parser.parse_args()

    learning_types = {lt.strip() for lt in args.learning_types.split(",") if lt.strip()}
    invalid = learning_types - ALL_LEARNING_TYPES
    if invalid:
        print(f"ERROR: invalid learning_types: {invalid}", file=sys.stderr)
        sys.exit(1)

    if args.format == "injection":
        text = query_learnings(
            phase=args.phase,
            project=args.project,
            top_n=args.top_n,
            char_budget=args.char_budget,
            learning_types=learning_types,
        )
        print(text)
    elif args.format == "json":
        entries = query_raw(
            phase=args.phase,
            project=args.project,
            top_n=args.top_n,
            char_budget=args.char_budget,
            learning_types=learning_types,
        )
        serialized = [
            {
                "id": e.entry_id(),
                "name": e.name,
                "description": e.description,
                "type": e.type,
                "severity": e.severity,
                "was_burned_by": e.was_burned_by,
                "project": e.project,
                "learning_type": e.learning_type,
                "phases": e.phases,
                "sprint": e.sprint,
                "date": e.date,
                "consequence": e.consequence,
                "rule": e.rule,
                "path": str(e.path),
            }
            for e in entries
        ]
        print(json.dumps(serialized, indent=2))
    elif args.format == "count":
        entries = query_raw(
            phase=args.phase,
            project=args.project,
            top_n=10_000,
            char_budget=10_000_000,
            learning_types=learning_types,
        )
        print(len(entries))
    elif args.format == "critical-only":
        entries = query_critical_for_phase(args.phase, args.project)
        serialized = [
            {
                "id": e.entry_id(),
                "name": e.name,
                "description": e.description,
                "consequence": e.consequence,
                "rule": e.rule,
                "path": str(e.path),
            }
            for e in entries
        ]
        print(json.dumps(serialized, indent=2))


if __name__ == "__main__":
    main()
