#!/usr/bin/env python3
"""Unit tests for the architecture comparison script.

These tests prove the structural diff stages produce correct results and the
verdict computation is deterministic.

Run with: python3 -m unittest tests.test_compare_architectures -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import compare_architectures as cmp  # noqa: E402


# ============================================================================
# Test fixtures — synthetic architectures
# ============================================================================


def make_complete_architecture(variant: str = "primary") -> dict:
    """Build a complete architecture document with all eleven required sections."""
    return {
        "architecture_md": f"""# {variant.title()} Architecture

## Overview
{variant.title()}'s overview of the system.

## Data Model
{variant.title()}'s data model description. References db_schema.sql.

## API Surface
{variant.title()}'s API description. References api_spec.json.

## Authentication
{variant.title()} uses NextAuth with email magic links and JWT in HTTP-only cookies.

## Authorization
{variant.title()} uses RBAC with two roles: therapist and admin.

## Deployment
{variant.title()} deploys to Vercel production with edge functions, Postgres on Neon, Redis on Upstash.

## Observability
{variant.title()} uses Sentry for errors, Datadog for metrics and tracing.

## Concurrency
{variant.title()} concurrency model: optimistic locking with version columns, BullMQ Redis queues with rate limiting at 10 jobs per second, idempotency keys on every POST, distributed locks via Redis RedLock for cross-job operations, FIFO ordering per user, exponential backoff retry semantics with maximum 3 attempts.

## Error Handling
{variant.title()} returns standard JSON error responses with error_code and user_message fields.

## Dependencies
{variant.title()} dependencies: Next.js 15.0, NextAuth 5, Sanity 3, BullMQ 5, Redis 7, Postgres 16, anthropic SDK.

## Compatibility
{variant.title()} compatibility: Node.js 20 LTS required. Postgres 14+ supported, 16+ recommended for performance. Browsers Chrome 110+, Firefox 110+, Safari 16+. Mobile Safari iOS 16+. Sanity SDK 3.x required, do not use 2.x. NextAuth 5 has breaking changes from 4.x.
""",
        "api_spec": {
            "paths": {
                "/api/imports": {
                    "post": {"summary": "Create import job"},
                    "get": {"summary": "List imports"},
                },
                "/api/users/me": {
                    "get": {"summary": "Get current user"},
                },
            }
        },
        "db_schema_sql": """CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE imports (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  url TEXT NOT NULL,
  status TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1
);
""",
    }


def write_architectures(workspace: Path, epic: str, primary: dict, rival: dict):
    """Write both architectures to the standard paths."""
    primary_dir = workspace / "artifacts" / "designs" / epic / "tech"
    rival_dir = primary_dir / "rival"
    primary_dir.mkdir(parents=True, exist_ok=True)
    rival_dir.mkdir(parents=True, exist_ok=True)

    (primary_dir / "architecture.md").write_text(primary["architecture_md"])
    (primary_dir / "api_spec.json").write_text(json.dumps(primary["api_spec"]))
    (primary_dir / "db_schema.sql").write_text(primary["db_schema_sql"])

    (rival_dir / "architecture.md").write_text(rival["architecture_md"])
    (rival_dir / "api_spec.json").write_text(json.dumps(rival["api_spec"]))
    (rival_dir / "db_schema.sql").write_text(rival["db_schema_sql"])


# ============================================================================
# Test 1: SQL parsing
# ============================================================================


class TestSqlParsing(unittest.TestCase):

    def test_parse_simple_create_table(self):
        sql = "CREATE TABLE users (id INT PRIMARY KEY, email TEXT NOT NULL);"
        tables = cmp.parse_sql_tables(sql)
        self.assertIn("users", tables)
        self.assertEqual(tables["users"], {"id", "email"})

    def test_parse_multiple_tables(self):
        sql = """
        CREATE TABLE users (id INT PRIMARY KEY, email TEXT);
        CREATE TABLE imports (id INT PRIMARY KEY, user_id INT, url TEXT);
        """
        tables = cmp.parse_sql_tables(sql)
        self.assertEqual(set(tables.keys()), {"users", "imports"})
        self.assertEqual(tables["users"], {"id", "email"})
        self.assertEqual(tables["imports"], {"id", "user_id", "url"})

    def test_parse_skips_constraints(self):
        sql = """
        CREATE TABLE users (
            id INT PRIMARY KEY,
            email TEXT NOT NULL,
            FOREIGN KEY (group_id) REFERENCES groups(id),
            UNIQUE (email)
        );
        """
        tables = cmp.parse_sql_tables(sql)
        self.assertEqual(tables["users"], {"id", "email"})

    def test_parse_handles_if_not_exists(self):
        sql = "CREATE TABLE IF NOT EXISTS users (id INT, name TEXT);"
        tables = cmp.parse_sql_tables(sql)
        self.assertIn("users", tables)


# ============================================================================
# Test 2: DB schema diff
# ============================================================================


class TestDbDiff(unittest.TestCase):

    def test_identical_schemas_full_overlap(self):
        sql = "CREATE TABLE users (id INT, email TEXT); CREATE TABLE imports (id INT, url TEXT);"
        diff = cmp.diff_db_schemas(sql, sql)
        self.assertEqual(diff["overlap_pct"], 1.0)
        self.assertEqual(len(diff["tables_only_primary"]), 0)
        self.assertEqual(len(diff["tables_only_rival"]), 0)
        self.assertEqual(len(diff["column_diffs"]), 0)

    def test_disjoint_schemas_zero_overlap(self):
        primary = "CREATE TABLE users (id INT);"
        rival = "CREATE TABLE products (id INT);"
        diff = cmp.diff_db_schemas(primary, rival)
        self.assertEqual(diff["overlap_pct"], 0.0)
        self.assertEqual(diff["tables_only_primary"], {"users"})
        self.assertEqual(diff["tables_only_rival"], {"products"})

    def test_partial_overlap(self):
        primary = "CREATE TABLE users (id INT, email TEXT); CREATE TABLE imports (id INT);"
        rival = "CREATE TABLE users (id INT, email TEXT); CREATE TABLE jobs (id INT);"
        diff = cmp.diff_db_schemas(primary, rival)
        self.assertEqual(diff["tables_in_both"], {"users"})
        self.assertEqual(diff["tables_only_primary"], {"imports"})
        self.assertEqual(diff["tables_only_rival"], {"jobs"})
        # 1 in both / 3 total = 0.33...
        self.assertAlmostEqual(diff["overlap_pct"], 1 / 3, places=2)

    def test_column_diff_for_shared_table(self):
        primary = "CREATE TABLE users (id INT, email TEXT);"
        rival = "CREATE TABLE users (id INT, email TEXT, name TEXT);"
        diff = cmp.diff_db_schemas(primary, rival)
        self.assertIn("users", diff["column_diffs"])
        self.assertEqual(diff["column_diffs"]["users"]["only_rival"], {"name"})
        self.assertEqual(diff["column_diffs"]["users"]["only_primary"], set())


# ============================================================================
# Test 3: API endpoint extraction
# ============================================================================


class TestApiExtraction(unittest.TestCase):

    def test_openapi_style(self):
        spec = {
            "paths": {
                "/users": {"get": {}, "post": {}},
                "/users/{id}": {"get": {}, "delete": {}},
            }
        }
        endpoints = cmp.extract_endpoints(spec)
        self.assertIn(("GET", "/users"), endpoints)
        self.assertIn(("POST", "/users"), endpoints)
        self.assertIn(("GET", "/users/{id}"), endpoints)
        self.assertIn(("DELETE", "/users/{id}"), endpoints)

    def test_array_style(self):
        spec = {
            "endpoints": [
                {"method": "GET", "path": "/users"},
                {"method": "POST", "path": "/imports"},
            ]
        }
        endpoints = cmp.extract_endpoints(spec)
        self.assertEqual(endpoints, {("GET", "/users"), ("POST", "/imports")})

    def test_top_level_keys_style(self):
        spec = {
            "GET /users": {"summary": "List users"},
            "POST /imports": {"summary": "Create import"},
        }
        endpoints = cmp.extract_endpoints(spec)
        self.assertEqual(endpoints, {("GET", "/users"), ("POST", "/imports")})

    def test_empty_spec(self):
        self.assertEqual(cmp.extract_endpoints({}), set())
        self.assertEqual(cmp.extract_endpoints(None), set())


# ============================================================================
# Test 4: API surface diff
# ============================================================================


class TestApiDiff(unittest.TestCase):

    def test_full_overlap(self):
        spec = {"paths": {"/a": {"get": {}}, "/b": {"post": {}}}}
        diff = cmp.diff_api_surface(spec, spec)
        self.assertEqual(diff["overlap_pct"], 1.0)

    def test_method_conflict_detected(self):
        primary = {"paths": {"/users": {"post": {}}}}
        rival = {"paths": {"/users": {"put": {}}}}
        diff = cmp.diff_api_surface(primary, rival)
        self.assertEqual(len(diff["method_conflicts"]), 1)
        self.assertEqual(diff["method_conflicts"][0]["path"], "/users")
        self.assertIn("POST", diff["method_conflicts"][0]["primary_methods"])
        self.assertIn("PUT", diff["method_conflicts"][0]["rival_methods"])

    def test_disjoint_endpoints(self):
        primary = {"paths": {"/a": {"get": {}}}}
        rival = {"paths": {"/b": {"get": {}}}}
        diff = cmp.diff_api_surface(primary, rival)
        self.assertEqual(diff["overlap_pct"], 0.0)


# ============================================================================
# Test 5: Section coverage
# ============================================================================


class TestSectionCoverage(unittest.TestCase):

    def test_complete_architecture_no_missing(self):
        arch = make_complete_architecture()
        present, missing = cmp.check_section_coverage(arch["architecture_md"])
        self.assertEqual(missing, [])

    def test_missing_concurrency(self):
        md = "## Overview\n## Data Model\n## API Surface"
        present, missing = cmp.check_section_coverage(md)
        self.assertIn("concurrency", missing)


# ============================================================================
# Test 6: Specialization keyword counts
# ============================================================================


class TestSpecializationKeywords(unittest.TestCase):

    def test_concurrency_keyword_counting(self):
        text = "We use locking and a queue. Race condition handling is critical."
        count = cmp.count_keywords(text, cmp.CONCURRENCY_KEYWORDS)
        # "locking", "queue", "race condition", "race" — at least 3 distinct mentions
        self.assertGreaterEqual(count, 3)

    def test_compatibility_keyword_counting(self):
        text = "Node.js version 20 required. Browser support: Chrome 110+. Postgres 14 compatible."
        count = cmp.count_keywords(text, cmp.COMPATIBILITY_KEYWORDS)
        self.assertGreaterEqual(count, 3)

    def test_specialization_diff_substantive_rival(self):
        primary_md = "## Concurrency\nWe use a queue."
        rival_md = """## Concurrency
We use optimistic locking with version columns. BullMQ queues handle the import job
queue with rate limiting. Idempotency keys ensure retry safety. Distributed locks
via Redis prevent race conditions. Ordering is FIFO. Compare-and-swap on critical paths."""
        diff = cmp.specialization_keyword_diff(primary_md, rival_md)
        self.assertGreater(diff["rival_concurrency_count"], diff["primary_concurrency_count"])


# ============================================================================
# Test 7: Verdict computation
# ============================================================================


class TestVerdictComputation(unittest.TestCase):

    def _make_diff(self, **overrides) -> cmp.StructuralDiff:
        defaults = {
            "primary_validation_passed": True,
            "rival_validation_passed": True,
            "primary_sections_present": list(cmp.SECTION_PATTERNS.keys()),
            "primary_sections_missing": [],
            "rival_sections_present": list(cmp.SECTION_PATTERNS.keys()),
            "rival_sections_missing": [],
            "primary_tables": {"users", "imports"},
            "rival_tables": {"users", "imports"},
            "tables_in_both": {"users", "imports"},
            "tables_only_primary": set(),
            "tables_only_rival": set(),
            "db_overlap_pct": 1.0,
            "primary_endpoints": {("GET", "/users"), ("POST", "/imports")},
            "rival_endpoints": {("GET", "/users"), ("POST", "/imports")},
            "endpoints_in_both": {("GET", "/users"), ("POST", "/imports")},
            "endpoints_only_primary": set(),
            "endpoints_only_rival": set(),
            "api_overlap_pct": 1.0,
            "primary_concurrency_count": 15,
            "rival_concurrency_count": 18,
            "primary_compatibility_count": 10,
            "rival_compatibility_count": 12,
        }
        defaults.update(overrides)
        return cmp.StructuralDiff(**defaults)

    def _make_judgment(self, disagreements=None) -> cmp.JudgmentSurface:
        return cmp.JudgmentSurface(
            substantive_disagreements=disagreements or [],
            agreement_signal_strength="high",
            rationale="",
        )

    def test_full_agreement_approves(self):
        diff = self._make_diff()
        judgment = self._make_judgment()
        verdict, blocks, escalations, flags = cmp.compute_verdict(diff, judgment)
        self.assertEqual(verdict, "APPROVE")
        self.assertEqual(blocks, [])
        self.assertEqual(escalations, [])
        self.assertEqual(flags, [])

    def test_validation_failure_blocks(self):
        diff = self._make_diff(primary_validation_passed=False)
        verdict, blocks, _, _ = cmp.compute_verdict(diff, self._make_judgment())
        self.assertEqual(verdict, "BLOCK")
        self.assertTrue(any("Primary" in b for b in blocks))

    def test_three_missing_sections_blocks(self):
        diff = self._make_diff(primary_sections_missing=["a", "b", "c"])
        verdict, blocks, _, _ = cmp.compute_verdict(diff, self._make_judgment())
        self.assertEqual(verdict, "BLOCK")

    def test_substantive_disagreement_escalates(self):
        diff = self._make_diff()
        judgment = self._make_judgment([
            {
                "topic": "Database choice",
                "primary_position": "PostgreSQL",
                "rival_position": "MongoDB",
                "decision_type": "technology_choice",
                "requires_ceo_decision": True,
            }
        ])
        verdict, _, escalations, _ = cmp.compute_verdict(diff, judgment)
        self.assertEqual(verdict, "ESCALATE")
        self.assertTrue(any("Database choice" in e for e in escalations))

    def test_low_db_overlap_escalates(self):
        diff = self._make_diff(db_overlap_pct=0.3, tables_in_both={"users"}, tables_only_primary={"a", "b"}, tables_only_rival={"c", "d"})
        verdict, _, escalations, _ = cmp.compute_verdict(diff, self._make_judgment())
        self.assertEqual(verdict, "ESCALATE")

    def test_minor_differences_flag(self):
        diff = self._make_diff(
            tables_only_rival={"audit_log"},
            db_overlap_pct=0.66,  # 2 of 3 tables shared (above 0.5 escalation threshold)
        )
        verdict, _, _, flags = cmp.compute_verdict(diff, self._make_judgment())
        self.assertEqual(verdict, "FLAG")
        self.assertTrue(any("audit_log" in f for f in flags))

    def test_asymmetric_concurrency_flagged(self):
        diff = self._make_diff(
            primary_concurrency_count=3,
            rival_concurrency_count=20,
        )
        verdict, _, _, flags = cmp.compute_verdict(diff, self._make_judgment())
        self.assertEqual(verdict, "FLAG")
        self.assertTrue(any("concurrency" in f.lower() and "rival" in f.lower() for f in flags))

    def test_non_load_bearing_disagreement_flags_not_escalates(self):
        judgment = self._make_judgment([
            {
                "topic": "Logging library",
                "primary_position": "winston",
                "rival_position": "pino",
                "decision_type": "technology_choice",
                "requires_ceo_decision": False,
            }
        ])
        verdict, _, escalations, flags = cmp.compute_verdict(self._make_diff(), judgment)
        self.assertEqual(verdict, "FLAG")
        self.assertEqual(escalations, [])


# ============================================================================
# Test 8: End-to-end (with --no-llm to skip the LLM call)
# ============================================================================


class TestEndToEnd(unittest.TestCase):

    def test_identical_architectures_approve(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / "state").mkdir()
            (ws / "state" / "company_state.json").write_text("{}")
            arch = make_complete_architecture()
            write_architectures(ws, "test-epic", arch, arch)

            test_argv = [
                "compare_architectures.py",
                "--workspace", str(ws),
                "--epic", "test-epic",
                "--no-llm",
            ]
            with patch.object(sys, "argv", test_argv):
                with patch("builtins.print") as mock_print:
                    cmp.main()

            printed = mock_print.call_args[0][0]
            output = json.loads(printed)
            self.assertEqual(output["verdict"], "APPROVE")
            self.assertEqual(output["primary_validation"], "PASS")
            self.assertEqual(output["rival_validation"], "PASS")
            self.assertEqual(output["data_model_overlap_pct"], 1.0)

    def test_different_data_models_escalate(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / "state").mkdir()
            (ws / "state" / "company_state.json").write_text("{}")

            primary = make_complete_architecture("primary")
            rival = make_complete_architecture("rival")
            # Make rival's schema substantially different
            rival["db_schema_sql"] = """CREATE TABLE workers (id INT, name TEXT);
CREATE TABLE jobs (id INT, worker_id INT);
CREATE TABLE outputs (id INT, job_id INT);
CREATE TABLE logs (id INT, worker_id INT, message TEXT);"""

            write_architectures(ws, "test-epic", primary, rival)

            test_argv = [
                "compare_architectures.py",
                "--workspace", str(ws),
                "--epic", "test-epic",
                "--no-llm",
            ]
            with patch.object(sys, "argv", test_argv):
                with patch("builtins.print") as mock_print:
                    cmp.main()

            printed = mock_print.call_args[0][0]
            output = json.loads(printed)
            self.assertEqual(output["verdict"], "ESCALATE")
            self.assertLess(output["data_model_overlap_pct"], 0.5)

    def test_invalid_primary_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / "state").mkdir()
            (ws / "state" / "company_state.json").write_text("{}")

            primary = make_complete_architecture("primary")
            # Break primary by removing CREATE TABLE statements
            primary["db_schema_sql"] = "-- empty schema"
            rival = make_complete_architecture("rival")

            write_architectures(ws, "test-epic", primary, rival)

            test_argv = [
                "compare_architectures.py",
                "--workspace", str(ws),
                "--epic", "test-epic",
                "--no-llm",
            ]
            with patch.object(sys, "argv", test_argv):
                with patch("builtins.print") as mock_print:
                    cmp.main()

            printed = mock_print.call_args[0][0]
            output = json.loads(printed)
            self.assertEqual(output["verdict"], "BLOCK")
            self.assertEqual(output["primary_validation"], "FAIL")


if __name__ == "__main__":
    unittest.main(verbosity=2)
