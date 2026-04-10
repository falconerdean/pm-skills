#!/usr/bin/env python3
"""Validate a Business Reviewer report against the output contract.

Usage:
    python3 validate_review.py --report path/to/report.md

Exits 0 if valid, 1 if invalid (with errors printed).

This is the structural enforcement layer for the agent. The reviewer's prompt
tells it the rules; this script verifies the rules were followed.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone


REQUIRED_SECTIONS = [
    "Goal Anchor",
    "Outcome Trace",
    "Falsification Test",
    "Premortem",
    "Most Fragile Assumption",
    "Disconfirmation Search",
    "Verdict",
]

VALID_VERDICTS = {"APPROVE", "APPROVE WITH CONDITIONS", "BLOCK"}

FORBIDDEN_TOPICS = [
    # Code style and formatting concerns the reviewer should not raise
    "code style",
    "naming convention",
    "file organization",
    "framework choice",
    "tab vs space",
    "snake_case vs camelCase",
]

SIMULATION_PHRASES = [
    "in a real implementation",
    "you would typically",
    "this could be extended to",
    "the team should consider",
    "generally seems to",
    "for production, you would",
]


def validate(report_path: Path) -> tuple[bool, list[str]]:
    """Returns (is_valid, errors)."""
    if not report_path.exists():
        return False, [f"Report file does not exist: {report_path}"]

    text = report_path.read_text()
    errors: list[str] = []

    # 1. All 6 question sections present
    for section in REQUIRED_SECTIONS:
        if section.lower() not in text.lower():
            errors.append(f"Missing required section: {section}")

    # 2. Verdict is one of the valid values
    verdict_match = re.search(
        r"verdict\s*[:*]+\s*\**\s*(APPROVE WITH CONDITIONS|APPROVE|BLOCK)",
        text,
        re.IGNORECASE,
    )
    if not verdict_match:
        errors.append("No clear verdict line found. Verdict must be APPROVE, APPROVE WITH CONDITIONS, or BLOCK.")
    else:
        verdict = verdict_match.group(1).upper()
        if verdict not in VALID_VERDICTS:
            errors.append(f"Invalid verdict: '{verdict}'. Must be one of {VALID_VERDICTS}")

    # 3. Citations: at least 6 source citations (one per question minimum)
    citation_pattern = re.compile(
        r"Source:\s*\S+.*\n\s*Quote:\s*\".*\"",
        re.MULTILINE | re.IGNORECASE,
    )
    citations = citation_pattern.findall(text)
    if len(citations) < 6:
        errors.append(
            f"Insufficient citations: found {len(citations)}, need at least 6 "
            "(one per core question minimum). Each finding must cite specific source + quote."
        )

    # 4. Disconfirmation Search section is non-empty
    discon_match = re.search(
        r"Disconfirmation Search.*?(?=\n##|\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if discon_match:
        discon_section = discon_match.group(0)
        # Look for at least one search attempt described
        if len(discon_section.strip()) < 100:
            errors.append("Disconfirmation Search section is too short — at least 3 distinct searches required")
        # The word "Searched" or "Search" should appear at least 3 times in the section
        if discon_section.lower().count("search") < 3:
            errors.append(
                "Disconfirmation Search section must report at least 3 distinct disconfirmation attempts. "
                "Empty disconfirmation = automatic flag."
            )

    # 5. Forbidden topics
    text_lower = text.lower()
    for topic in FORBIDDEN_TOPICS:
        if topic in text_lower:
            errors.append(
                f"Forbidden topic raised: '{topic}'. The reviewer is not allowed to raise concerns about "
                "code style, naming, file organization, or framework choice. Use code-review for those."
            )

    # 6. Simulation language
    for phrase in SIMULATION_PHRASES:
        if phrase in text_lower:
            errors.append(
                f"Simulation language detected: '{phrase}'. Findings must be specific and grounded in artifacts, "
                "not generic 'consider X' suggestions."
            )

    # 7. UTC timestamp present
    timestamp_pattern = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?\s*(UTC|Z)")
    if not timestamp_pattern.search(text):
        errors.append("No UTC timestamp found. Reports must include UTC timestamp (YYYY-MM-DD HH:MM UTC or ISO Z).")

    # 8. Premortem must have at least 5 numbered causes
    premortem_match = re.search(
        r"Premortem.*?(?=\n##|\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if premortem_match:
        premortem_section = premortem_match.group(0)
        # Count numbered list items (1. through 5. minimum)
        numbered_items = re.findall(r"^\s*\d+\.\s", premortem_section, re.MULTILINE)
        if len(numbered_items) < 5:
            errors.append(
                f"Premortem section has {len(numbered_items)} numbered causes; at least 5 required. "
                "5 distinct causes from at least 3 different categories."
            )

    is_valid = len(errors) == 0
    return is_valid, errors


def main():
    parser = argparse.ArgumentParser(description="Validate a Business Reviewer report")
    parser.add_argument("--report", required=True, help="Path to the report file")
    args = parser.parse_args()

    report_path = Path(args.report)
    is_valid, errors = validate(report_path)

    timestamp = datetime.now(timezone.utc).isoformat()

    if is_valid:
        print(f"[{timestamp}] VALIDATION PASSED: {report_path}")
        sys.exit(0)
    else:
        print(f"[{timestamp}] VALIDATION FAILED: {report_path}")
        print()
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        print()
        print(f"Total errors: {len(errors)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
