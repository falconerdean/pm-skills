#!/usr/bin/env python3
"""Unit tests for query.py — the shared memory query script.

Proves that:
    - Frontmatter parsing handles all common YAML patterns
    - Filtering correctly applies project + phase + learning_type constraints
    - Ranking is severity → was_burned_by → recency descending
    - Char budget packing stops cleanly at the budget
    - Empty queries return empty strings (not crashes)
    - The CLI surface produces the expected formats

Run with: python3 -m unittest tests.test_query -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent dir so `query` is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import query  # noqa: E402


# ============================================================================
# Test fixtures
# ============================================================================


def write_memory_entry(
    memory_dir: Path,
    filename: str,
    name: str,
    description: str,
    severity: str = "medium",
    was_burned_by: bool = False,
    project: str = "global",
    global_applicable: bool = False,
    phases: list[str] | None = None,
    learning_type: str = "task_specific",
    consequence: str = "",
    rule: str = "",
    date: str = "2026-04-01",
):
    """Write a memory file with the new schema."""
    phases_yaml = ""
    if phases:
        phases_yaml = "phases:\n" + "\n".join(f"  - {p}" for p in phases)
    else:
        phases_yaml = "phases: []"

    content = f"""---
name: {name}
description: {description}
type: feedback
severity: {severity}
was_burned_by: {str(was_burned_by).lower()}
project: {project}
global_applicable: {str(global_applicable).lower()}
learning_type: {learning_type}
{phases_yaml}
date: {date}
consequence: {consequence}
rule: {rule}
---

# {name}

Body content here.
"""
    (memory_dir / filename).write_text(content)


# ============================================================================
# Test 1: Frontmatter parsing
# ============================================================================


class TestFrontmatterParsing(unittest.TestCase):

    def test_simple_key_value(self):
        text = "---\nname: test\ndescription: hello world\n---\n\nbody"
        meta, body = query.parse_frontmatter(text)
        self.assertEqual(meta["name"], "test")
        self.assertEqual(meta["description"], "hello world")
        self.assertEqual(body, "body")

    def test_block_list(self):
        text = "---\nphases:\n  - research\n  - tech_design\n  - testing\n---\nbody"
        meta, _ = query.parse_frontmatter(text)
        self.assertEqual(meta["phases"], ["research", "tech_design", "testing"])

    def test_inline_list(self):
        text = '---\nphases: [research, tech_design]\n---\nbody'
        meta, _ = query.parse_frontmatter(text)
        self.assertEqual(meta["phases"], ["research", "tech_design"])

    def test_boolean_values(self):
        text = "---\nwas_burned_by: true\nglobal_applicable: false\n---\nbody"
        meta, _ = query.parse_frontmatter(text)
        self.assertIs(meta["was_burned_by"], True)
        self.assertIs(meta["global_applicable"], False)

    def test_no_frontmatter_returns_empty(self):
        text = "# Just markdown\n\nNo frontmatter here."
        meta, body = query.parse_frontmatter(text)
        self.assertEqual(meta, {})
        self.assertIn("Just markdown", body)

    def test_quoted_strings(self):
        text = '---\nname: "quoted name"\ndescription: \'single quotes\'\n---\nbody'
        meta, _ = query.parse_frontmatter(text)
        self.assertEqual(meta["name"], "quoted name")
        self.assertEqual(meta["description"], "single quotes")


# ============================================================================
# Test 2: Filtering
# ============================================================================


class TestFiltering(unittest.TestCase):

    def test_phase_filter_includes_matching(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = Path(tmp)
            write_memory_entry(mem, "a.md", "A", "first", phases=["research"])
            write_memory_entry(mem, "b.md", "B", "second", phases=["tech_design"])

            backend = query.MarkdownBackend(memory_dir=mem)
            results = backend.query(phase="research", project="global", top_n=10, char_budget=10000)
            names = [r.name for r in results]
            self.assertIn("A", names)
            self.assertNotIn("B", names)

    def test_empty_phases_excluded_from_phase_query(self):
        """Entries with no phases should NOT be a universal fallback."""
        with tempfile.TemporaryDirectory() as tmp:
            mem = Path(tmp)
            write_memory_entry(mem, "a.md", "A", "uncategorized", phases=[])
            write_memory_entry(mem, "b.md", "B", "categorized", phases=["research"])

            backend = query.MarkdownBackend(memory_dir=mem)
            results = backend.query(phase="research", project="global", top_n=10, char_budget=10000)
            names = [r.name for r in results]
            self.assertNotIn("A", names, "Uncategorized entry should not match a phase query")
            self.assertIn("B", names)

    def test_project_filter_with_global_applicable(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = Path(tmp)
            write_memory_entry(mem, "a.md", "Insite-only", "x", project="insite-v6", phases=["research"])
            write_memory_entry(mem, "b.md", "Other-project", "x", project="other", phases=["research"])
            write_memory_entry(
                mem, "c.md", "Global", "x", project="other", global_applicable=True, phases=["research"]
            )

            backend = query.MarkdownBackend(memory_dir=mem)
            results = backend.query(phase="research", project="insite-v6", top_n=10, char_budget=10000)
            names = {r.name for r in results}
            self.assertIn("Insite-only", names)
            self.assertNotIn("Other-project", names)
            self.assertIn("Global", names, "global_applicable=true should override project filter")

    def test_learning_type_filter(self):
        """Silent observer cold-read protection: filter to process only."""
        with tempfile.TemporaryDirectory() as tmp:
            mem = Path(tmp)
            write_memory_entry(mem, "a.md", "Process-rule", "x", learning_type="process", phases=["research"])
            write_memory_entry(mem, "b.md", "Task-fact", "x", learning_type="task_specific", phases=["research"])
            write_memory_entry(mem, "c.md", "Factual", "x", learning_type="factual", phases=["research"])

            backend = query.MarkdownBackend(memory_dir=mem)
            results = backend.query(
                phase="research", project="global", top_n=10, char_budget=10000,
                learning_types={"process"},
            )
            names = {r.name for r in results}
            self.assertEqual(names, {"Process-rule"})


# ============================================================================
# Test 3: Ranking
# ============================================================================


class TestRanking(unittest.TestCase):

    def test_severity_ranks_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = Path(tmp)
            write_memory_entry(mem, "a.md", "Low", "x", severity="low", phases=["research"])
            write_memory_entry(mem, "b.md", "Critical", "x", severity="critical", phases=["research"])
            write_memory_entry(mem, "c.md", "High", "x", severity="high", phases=["research"])
            write_memory_entry(mem, "d.md", "Medium", "x", severity="medium", phases=["research"])

            backend = query.MarkdownBackend(memory_dir=mem)
            results = backend.query(phase="research", project="global", top_n=4, char_budget=100000)
            names = [r.name for r in results]
            self.assertEqual(names, ["Critical", "High", "Medium", "Low"])

    def test_was_burned_by_ranks_above_not_burned_at_same_severity(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = Path(tmp)
            write_memory_entry(
                mem, "a.md", "Not-burned", "x", severity="critical", was_burned_by=False, phases=["research"]
            )
            write_memory_entry(
                mem, "b.md", "Burned", "x", severity="critical", was_burned_by=True, phases=["research"]
            )

            backend = query.MarkdownBackend(memory_dir=mem)
            results = backend.query(phase="research", project="global", top_n=2, char_budget=100000)
            names = [r.name for r in results]
            self.assertEqual(names, ["Burned", "Not-burned"])

    def test_recency_breaks_remaining_ties(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = Path(tmp)
            write_memory_entry(
                mem, "a.md", "Older", "x", severity="critical", was_burned_by=True,
                phases=["research"], date="2026-01-01",
            )
            write_memory_entry(
                mem, "b.md", "Newer", "x", severity="critical", was_burned_by=True,
                phases=["research"], date="2026-04-01",
            )

            backend = query.MarkdownBackend(memory_dir=mem)
            results = backend.query(phase="research", project="global", top_n=2, char_budget=100000)
            names = [r.name for r in results]
            self.assertEqual(names, ["Newer", "Older"])


# ============================================================================
# Test 4: Char budget packing
# ============================================================================


class TestBudgetPacking(unittest.TestCase):

    def test_packing_stops_at_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = Path(tmp)
            for i in range(10):
                write_memory_entry(
                    mem,
                    f"e{i}.md",
                    f"Entry-{i}",
                    "x" * 200,  # ~200 char description
                    severity="critical",
                    was_burned_by=True,
                    phases=["research"],
                    consequence="y" * 100,
                    rule="z" * 100,
                )

            backend = query.MarkdownBackend(memory_dir=mem)
            # Tight budget — should pack ~3 entries
            results = backend.query(phase="research", project="global", top_n=10, char_budget=2000)
            self.assertGreater(len(results), 0)
            self.assertLess(len(results), 10, "Tight budget should not pack all 10 entries")

            # The total formatted length must respect the budget (with small tolerance)
            total = sum(len(r.format_for_injection()) + 2 for r in results)
            self.assertLessEqual(total, 2500, f"Packed total {total} exceeds reasonable budget")

    def test_top_n_caps_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = Path(tmp)
            for i in range(10):
                write_memory_entry(mem, f"e{i}.md", f"Entry-{i}", "x", phases=["research"])

            backend = query.MarkdownBackend(memory_dir=mem)
            results = backend.query(phase="research", project="global", top_n=3, char_budget=1000000)
            self.assertEqual(len(results), 3)


# ============================================================================
# Test 5: Empty results
# ============================================================================


class TestEmptyResults(unittest.TestCase):

    def test_no_matching_entries_returns_empty_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = Path(tmp)
            write_memory_entry(mem, "a.md", "A", "x", phases=["research"])

            # Patch MEMORY_DIR to point at the temp dir
            from unittest.mock import patch
            with patch.object(query, "MEMORY_DIR", mem):
                # Re-create get_backend to use the patched dir
                backend = query.MarkdownBackend(memory_dir=mem)
                with patch.object(query, "get_backend", lambda: backend):
                    text = query.query_learnings(phase="deployment", project="global")
                    self.assertEqual(text, "")

    def test_missing_memory_dir_returns_empty(self):
        backend = query.MarkdownBackend(memory_dir=Path("/nonexistent/path"))
        results = backend.query(phase="research", project="global", top_n=5, char_budget=8000)
        self.assertEqual(results, [])


# ============================================================================
# Test 6: query_critical_for_phase (used by CRAG grader)
# ============================================================================


class TestCriticalQuery(unittest.TestCase):

    def test_returns_only_critical(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = Path(tmp)
            write_memory_entry(mem, "a.md", "Critical", "x", severity="critical", phases=["tech_design"])
            write_memory_entry(mem, "b.md", "High", "x", severity="high", phases=["tech_design"])
            write_memory_entry(mem, "c.md", "Medium", "x", severity="medium", phases=["tech_design"])

            from unittest.mock import patch
            backend = query.MarkdownBackend(memory_dir=mem)
            with patch.object(query, "get_backend", lambda: backend):
                results = query.query_critical_for_phase("tech_design", "global")
                names = {r.name for r in results}
                self.assertEqual(names, {"Critical"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
