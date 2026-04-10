#!/usr/bin/env python3
"""Randomly select 6 questions (one per category) from the question pool.

Usage:
    python3 select_questions.py --pool ../reference/question_pool.md --seed <seed>

Outputs JSON with the 6 selected questions, one per category.

The seed should be deterministic but unpredictable to upstream sub-agents.
A good seed is: f"{epic}_{phase}_{utc_timestamp}_{review_attempt}"

This randomization is the structural defense against story inflation /
sub-agent pre-optimization. If the questions are stable, sub-agents will
learn to pre-answer them. If they rotate, sub-agents must actually do
the underlying work.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


CATEGORIES = [
    ("Q1", "The Goal Anchor"),
    ("Q2", "The Outcome Trace"),
    ("Q3", "The Falsification Test"),
    ("Q4", "The Premortem"),
    ("Q5", "The Most Fragile Assumption"),
    ("Q6", "The Disconfirmation Search"),
]


def parse_pool(pool_path: Path) -> dict[str, list[str]]:
    """Parse the question pool markdown file into {category_id: [questions]}."""
    text = pool_path.read_text()
    pool: dict[str, list[str]] = {cat_id: [] for cat_id, _ in CATEGORIES}

    current_category = None
    for line in text.split("\n"):
        # Detect category headers like "## Q1: The Goal Anchor (20 variants)"
        header_match = re.match(r"^##\s+(Q\d):", line)
        if header_match:
            current_category = header_match.group(1)
            continue

        # Detect numbered list items
        if current_category and current_category in pool:
            list_match = re.match(r"^\d+\.\s+(.+)$", line.strip())
            if list_match:
                question = list_match.group(1).strip()
                pool[current_category].append(question)

    return pool


def select(pool: dict[str, list[str]], seed: str) -> dict[str, dict]:
    """Select one question per category using a deterministic seed."""
    selections: dict[str, dict] = {}

    for cat_id, cat_name in CATEGORIES:
        if cat_id not in pool or not pool[cat_id]:
            raise ValueError(f"No questions found in pool for category {cat_id}")

        # Hash the seed + category id to get a deterministic index
        hash_input = f"{seed}_{cat_id}".encode()
        hash_bytes = hashlib.sha256(hash_input).digest()
        idx = int.from_bytes(hash_bytes[:4], "big") % len(pool[cat_id])

        selections[cat_id] = {
            "category": cat_name,
            "question": pool[cat_id][idx],
            "variant_index": idx,
            "pool_size": len(pool[cat_id]),
        }

    return selections


def main():
    parser = argparse.ArgumentParser(description="Select 6 questions from the pool")
    parser.add_argument("--pool", required=True, help="Path to question_pool.md")
    parser.add_argument(
        "--seed",
        required=True,
        help="Deterministic seed (e.g., epic_phase_timestamp_attempt)",
    )
    args = parser.parse_args()

    pool_path = Path(args.pool)
    if not pool_path.exists():
        print(f"ERROR: pool file not found: {pool_path}", file=sys.stderr)
        sys.exit(1)

    pool = parse_pool(pool_path)

    # Sanity check: every category has at least 1 question
    for cat_id, cat_name in CATEGORIES:
        if not pool[cat_id]:
            print(f"ERROR: pool category {cat_id} ({cat_name}) is empty", file=sys.stderr)
            sys.exit(1)

    selections = select(pool, args.seed)

    output = {
        "seed": args.seed,
        "selections": selections,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
