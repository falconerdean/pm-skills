#!/usr/bin/env python3
"""Validate skill output meets quality contract.

Usage: python3 validate_output.py <output_file> [--strict]

Checks:
- Minimum content length
- No placeholder/simulation language
- Required sections present (customize REQUIRED_SECTIONS)
- No TODO markers in final output
"""
import sys
import re

# Customize these for your skill
MIN_CHARS = 500
REQUIRED_SECTIONS = []  # e.g., ["Executive Summary", "Findings", "Recommendations"]
SIMULATION_PHRASES = [
    "in a real implementation",
    "you would typically",
    "this could be extended",
    "for production, you'd want",
    "in practice, you would",
    "a real-world version would",
]
PLACEHOLDER_MARKERS = ["TODO", "FIXME", "PLACEHOLDER", "TBD", "[insert", "[your"]


def validate(filepath, strict=False):
    with open(filepath) as f:
        content = f.read()

    errors = []
    warnings = []

    # Length check
    if len(content) < MIN_CHARS:
        errors.append(f"Output too short: {len(content)} chars (min {MIN_CHARS})")

    # Simulation language
    content_lower = content.lower()
    for phrase in SIMULATION_PHRASES:
        if phrase in content_lower:
            errors.append(f"Simulation language detected: '{phrase}'")

    # Placeholder markers
    for marker in PLACEHOLDER_MARKERS:
        if marker.lower() in content_lower:
            (errors if strict else warnings).append(f"Placeholder marker: '{marker}'")

    # Required sections
    for section in REQUIRED_SECTIONS:
        if section.lower() not in content_lower:
            errors.append(f"Missing required section: '{section}'")

    # Report
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <output_file> [--strict]")
        sys.exit(2)

    strict = "--strict" in sys.argv
    sys.exit(validate(sys.argv[1], strict))
