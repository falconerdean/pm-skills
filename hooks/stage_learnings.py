#!/usr/bin/env python3
"""
Stage learning data into the pm-skills repo working tree.

Runs at session stop on droplets. Copies curated learning data
from ~/.claude/learning/ into ~/projects/pm-skills/learnings/
so it can be captured by /tools:droplet-upstream.

Only runs on droplets (detected by ~/.golden-image-timestamp).
Idempotent — safe to run multiple times.
"""

import os
import re
import shutil
import json
from pathlib import Path
from datetime import datetime, timezone

# Only run on droplets
TIMESTAMP_FILE = Path.home() / ".golden-image-timestamp"
if not TIMESTAMP_FILE.exists():
    exit(0)

# Paths
LEARNING_DIR = Path.home() / ".claude" / "learning"
PM_SKILLS = Path.home() / "projects" / "pm-skills"
SESSIONS_OUT = PM_SKILLS / "learnings" / "sessions"
RETROS_OUT = PM_SKILLS / "learnings" / "retros"

# Ensure output dirs exist
SESSIONS_OUT.mkdir(parents=True, exist_ok=True)
RETROS_OUT.mkdir(parents=True, exist_ok=True)

# Get baseline timestamp
baseline = TIMESTAMP_FILE.stat().st_mtime

# Token patterns to redact
SECRET_PATTERNS = [
    (re.compile(r'sk-ant-[a-zA-Z0-9_-]{20,}'), '[REDACTED_ANTHROPIC_KEY]'),
    (re.compile(r'ghp_[a-zA-Z0-9]{36,}'), '[REDACTED_GH_TOKEN]'),
    (re.compile(r'github_pat_[a-zA-Z0-9_]{40,}'), '[REDACTED_GH_PAT]'),
    (re.compile(r'nfp_[a-zA-Z0-9]{20,}'), '[REDACTED_NETLIFY]'),
    (re.compile(r'dp\.st\.[a-zA-Z0-9._-]{20,}'), '[REDACTED_DOPPLER]'),
    (re.compile(r'sk_live_[a-zA-Z0-9]{20,}'), '[REDACTED_STRIPE]'),
    (re.compile(r'whsec_[a-zA-Z0-9]{20,}'), '[REDACTED_STRIPE_WEBHOOK]'),
    (re.compile(r'sntrys_[a-zA-Z0-9]{20,}'), '[REDACTED_SENTRY]'),
    (re.compile(r'Bearer [a-zA-Z0-9._-]{20,}'), 'Bearer [REDACTED]'),
]


def redact(text: str) -> str:
    """Remove token-like patterns from text."""
    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def copy_session_learnings():
    """Copy daily session summary markdown files."""
    learnings_dir = LEARNING_DIR / "learnings"
    if not learnings_dir.exists():
        return 0

    count = 0
    for f in learnings_dir.glob("*.md"):
        if f.stat().st_mtime > baseline:
            dest = SESSIONS_OUT / f.name
            if not dest.exists():
                content = redact(f.read_text())
                dest.write_text(content)
                count += 1
    return count


def copy_retro_documents():
    """Find and copy retro documents from project workspaces."""
    projects_dir = Path.home() / "projects"
    if not projects_dir.exists():
        return 0

    count = 0
    for retro_file in projects_dir.rglob("*retro*.md"):
        # Skip node_modules, .git, and already-copied files
        parts = str(retro_file)
        if "node_modules" in parts or "/.git/" in parts:
            continue
        if retro_file.stat().st_mtime > baseline:
            dest = RETROS_OUT / retro_file.name
            if not dest.exists():
                content = redact(retro_file.read_text())
                dest.write_text(content)
                count += 1
    return count


if __name__ == "__main__":
    sessions = copy_session_learnings()
    retros = copy_retro_documents()

    if sessions or retros:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        print(f"[stage_learnings] {timestamp}: staged {sessions} session files, {retros} retro files")
