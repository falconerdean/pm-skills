#!/usr/bin/env python3
"""Unit tests for the Rival Architect wrapper script protocol.

These tests prove the structural protocol holds — the rival is epistemically
isolated from the primary's tech output, the message ordering enforces goal
anchoring, the model is fixed, and the response validation rejects placeholders.

Run with: python3 -m unittest tests.test_rival_wrapper_protocol -v
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import invoke_rival_architect as rwa  # noqa: E402


# ============================================================================
# Fixtures
# ============================================================================


def build_phase5_workspace(
    root: Path,
    sprint_goal: str = "Enable therapists to import existing site content via URL within 14 days",
    product_description: str = "Insite is a website builder for therapists.",
    discovery_brief: str = "Therapists need to import existing site content. Multiple scrapers exist (ScrapingBee, Bright Data, Apify). Use a third-party scraping provider with a documented API.",
    stories: list[dict] | None = None,
    include_primary_arch: bool = True,
    primary_arch_content: str = "# Architecture\n\n## Overview\nClaude's overview.\n\n## Data Model\nClaude's data model.\n\n## Concurrency\nClaude's concurrency section. Uses optimistic locking and a Bull MQ Redis-backed queue with idempotency keys for retry safety.",
    primary_api_content: dict | None = None,
    primary_db_content: str = "CREATE TABLE imports (id SERIAL PRIMARY KEY, url TEXT NOT NULL);",
    epic: str = "stitch-test",
):
    """Build a synthetic Phase 5 workspace with brief, requirements, and (optionally) primary tech output."""
    state_dir = root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "project_config.json").write_text(
        json.dumps({"product_description": product_description})
    )
    (state_dir / "sprint_plan.json").write_text(
        json.dumps({"goal": sprint_goal, "epic": epic, "sprint_number": 12})
    )
    (state_dir / "company_state.json").write_text(json.dumps({}))

    research_dir = root / "artifacts" / "research" / epic
    research_dir.mkdir(parents=True, exist_ok=True)
    (research_dir / "discovery_brief.md").write_text(discovery_brief)

    req_dir = root / "artifacts" / "requirements" / epic
    req_dir.mkdir(parents=True, exist_ok=True)
    (req_dir / "stories.json").write_text(
        json.dumps(stories or [{"id": "S1", "story": "As a therapist, I want to import my existing site"}])
    )

    design_dir = root / "artifacts" / "designs" / epic
    design_dir.mkdir(parents=True, exist_ok=True)
    (design_dir / "ui_spec.md").write_text("# UI Spec\nA URL input field and a submit button.")
    (design_dir / "ux_flows.md").write_text("# UX Flows\n1. User enters URL\n2. System imports\n3. Preview shown")

    if include_primary_arch:
        tech_dir = design_dir / "tech"
        tech_dir.mkdir(parents=True, exist_ok=True)
        (tech_dir / "architecture.md").write_text(primary_arch_content)
        (tech_dir / "api_spec.json").write_text(
            json.dumps(primary_api_content or {"paths": {"/import": {"post": {}}}})
        )
        (tech_dir / "db_schema.sql").write_text(primary_db_content)

    return root


# ============================================================================
# Test 1: Input whitelisting — primary's tech output is structurally excluded
# ============================================================================


class TestInputWhitelisting(unittest.TestCase):

    def test_load_inputs_does_not_include_primary_architecture(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = build_phase5_workspace(
                Path(tmp),
                primary_arch_content="THIS IS CLAUDE'S ARCHITECTURE WITH SECRET PATTERNS",
            )
            inputs = rwa.load_inputs(ws, "stitch-test")
            all_inputs = (
                inputs.sprint_goal
                + inputs.product_description
                + inputs.discovery_brief
                + inputs.stories_json
                + inputs.prd_md
                + inputs.ui_spec
                + inputs.ux_flows
                + inputs.content_spec
            )
            # Critical: the primary's architecture content must not appear in the rival's inputs
            self.assertNotIn("CLAUDE'S ARCHITECTURE", all_inputs)
            self.assertNotIn("SECRET PATTERNS", all_inputs)

    def test_load_inputs_does_not_include_primary_db_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = build_phase5_workspace(
                Path(tmp),
                primary_db_content="CREATE TABLE secret_table_only_claude_thought_of (id INT);",
            )
            inputs = rwa.load_inputs(ws, "stitch-test")
            all_inputs = (
                inputs.sprint_goal + inputs.discovery_brief + inputs.stories_json
                + inputs.ui_spec + inputs.ux_flows
            )
            self.assertNotIn("secret_table_only_claude_thought_of", all_inputs)

    def test_load_inputs_does_not_include_primary_api_spec(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = build_phase5_workspace(
                Path(tmp),
                primary_api_content={"paths": {"/secret-claude-endpoint": {"get": {}}}},
            )
            inputs = rwa.load_inputs(ws, "stitch-test")
            all_inputs = (
                inputs.sprint_goal + inputs.discovery_brief + inputs.stories_json
                + inputs.ui_spec + inputs.ux_flows
            )
            self.assertNotIn("secret-claude-endpoint", all_inputs)

    def test_load_inputs_signature_only_takes_workspace_and_epic(self):
        """Function signature is the structural defense — caller cannot pass extra context."""
        import inspect
        sig = inspect.signature(rwa.load_inputs)
        params = list(sig.parameters.keys())
        self.assertEqual(params, ["workspace", "epic"])

    def test_assert_primary_artifacts_not_in_inputs_passes_clean(self):
        """The defensive check should pass when inputs are properly isolated."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = build_phase5_workspace(Path(tmp))
            inputs = rwa.load_inputs(ws, "stitch-test")
            # Should not raise SystemExit
            rwa.assert_primary_artifacts_not_in_inputs(inputs, ws, "stitch-test")


# ============================================================================
# Test 2: Required input validation
# ============================================================================


class TestRequiredInputs(unittest.TestCase):

    def test_missing_discovery_brief_halts(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / "state").mkdir()
            (ws / "state" / "project_config.json").write_text(json.dumps({"product_description": "X"}))
            (ws / "state" / "sprint_plan.json").write_text(json.dumps({"goal": "X"}))
            (ws / "artifacts" / "requirements" / "test").mkdir(parents=True)
            (ws / "artifacts" / "requirements" / "test" / "stories.json").write_text("[]")
            with self.assertRaises(SystemExit) as cm:
                rwa.load_inputs(ws, "test")
            self.assertEqual(cm.exception.code, 1)

    def test_missing_stories_halts(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / "state").mkdir()
            (ws / "state" / "project_config.json").write_text(json.dumps({"product_description": "X"}))
            (ws / "state" / "sprint_plan.json").write_text(json.dumps({"goal": "X"}))
            (ws / "artifacts" / "research" / "test").mkdir(parents=True)
            (ws / "artifacts" / "research" / "test" / "discovery_brief.md").write_text("brief")
            with self.assertRaises(SystemExit) as cm:
                rwa.load_inputs(ws, "test")
            self.assertEqual(cm.exception.code, 1)

    def test_missing_primary_architecture_halts(self):
        """Rival should not run before primary completes Phase 5."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = build_phase5_workspace(Path(tmp), include_primary_arch=False)
            with self.assertRaises(SystemExit) as cm:
                rwa.load_inputs(ws, "stitch-test")
            self.assertEqual(cm.exception.code, 1)


# ============================================================================
# Test 3: Message ordering — goal first, then context, then task
# ============================================================================


class TestMessageOrdering(unittest.TestCase):

    def test_build_messages_goal_anchor_first(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = build_phase5_workspace(Path(tmp))
            inputs = rwa.load_inputs(ws, "stitch-test")
            messages, system_prompt = rwa.build_messages(inputs)

            # 3 messages if no memory injection, 4 if INSTITUTIONAL LEARNINGS injected
            self.assertIn(len(messages), [3, 4])

            # Message 1 must contain ANCHOR and the goal text (always position 0)
            msg1 = messages[0]["content"]
            self.assertIn("ANCHOR", msg1)
            self.assertIn("Enable therapists to import", msg1)
            self.assertNotIn("scraping provider", msg1.lower())

            # The DISCOVERY BRIEF must come AFTER the anchor and BEFORE the task
            brief_idx = next(
                (i for i, m in enumerate(messages) if "DISCOVERY BRIEF" in m["content"]),
                -1,
            )
            task_idx = next(
                (i for i, m in enumerate(messages) if "TASK" in m["content"] and "architecture_md" in m["content"]),
                -1,
            )
            self.assertGreater(brief_idx, 0, "DISCOVERY BRIEF must come after the anchor")
            self.assertGreater(task_idx, brief_idx, "TASK must come after DISCOVERY BRIEF")

            # The brief content message must contain brief + stories + ui_spec
            brief_msg = messages[brief_idx]["content"]
            self.assertIn("DISCOVERY BRIEF", brief_msg)
            self.assertIn("USER STORIES", brief_msg)
            self.assertIn("UI SPEC", brief_msg)
            self.assertNotIn("ANCHOR", brief_msg)

            # Task message must contain the artifact field names
            task_msg = messages[task_idx]["content"]
            self.assertIn("TASK", task_msg)
            self.assertIn("architecture_md", task_msg)
            self.assertIn("api_spec_json", task_msg)
            self.assertIn("db_schema_sql", task_msg)

            # If institutional learnings injected, they must come BEFORE the brief context
            learning_idx = next(
                (i for i, m in enumerate(messages) if "INSTITUTIONAL LEARNINGS" in m["content"]),
                -1,
            )
            if learning_idx >= 0:
                self.assertLess(learning_idx, brief_idx, "Learnings must come before brief")
                self.assertGreater(learning_idx, 0, "Learnings must come after the anchor")


# ============================================================================
# Test 4: Fixed model
# ============================================================================


class TestFixedModel(unittest.TestCase):

    def test_fixed_model_constant(self):
        self.assertEqual(rwa.FIXED_MODEL, "gemini-3-pro")

    def test_call_gemini_halts_without_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit) as cm:
                rwa.call_gemini("system", [{"role": "user", "content": "test"}])
            self.assertEqual(cm.exception.code, 2)


# ============================================================================
# Test 5: Response validation
# ============================================================================


class TestResponseValidation(unittest.TestCase):

    def _build_valid_response(self) -> dict:
        return {
            "architecture_md": (
                "# Architecture\n\n"
                "## Overview\nNext.js 15 monolith on Vercel with Sanity CMS.\n\n"
                "## Data Model\nUser, Profile, ImportJob entities. See db_schema.sql.\n\n"
                "## API Surface\nREST endpoints. See api_spec.json.\n\n"
                "## Authentication\nNextAuth with email magic links. JWT in HTTP-only cookies.\n\n"
                "## Authorization\nRBAC with two roles: therapist and admin. Enforced in middleware.\n\n"
                "## Deployment\nVercel production with edge functions. Postgres on Neon. Redis on Upstash.\n\n"
                "## Observability\nSentry for errors, Datadog for metrics, structured logs to Datadog.\n\n"
                "## Concurrency\n"
                "We use optimistic locking on ImportJob updates with version columns. "
                "BullMQ handles the import queue with rate limiting at 10 jobs per second to "
                "avoid being throttled by Stitch's API. Idempotency keys are required on "
                "every import POST so retries are safe. We use distributed locks via Redis "
                "RedLock for any cross-job operations to prevent race conditions when two "
                "users import the same URL simultaneously. Queue ordering is FIFO per user "
                "but parallel across users. Dead letters go to a separate Redis stream that "
                "is polled hourly for manual review. We have explicit retry semantics: 3 "
                "attempts with exponential backoff (1s, 5s, 30s).\n\n"
                "## Error Handling\nStandard JSON error responses with error_code and user_message.\n\n"
                "## Dependencies\nNext.js 15.0, NextAuth 5, Sanity 3, BullMQ 5, Redis 7, Postgres 16.\n\n"
                "## Compatibility\n"
                "Node.js 20 LTS required as the minimum runtime version. Postgres 14+ "
                "supported, 16+ recommended for performance because of improved query "
                "planner heuristics. Browser support: Chrome 110+, Firefox 110+, Safari "
                "16+, Edge 110+, all current as of 2026-04. Mobile Safari iOS 16+ is "
                "supported but iOS 15 is not because of CSS container query usage. "
                "Sanity SDK 3.x is the only compatible version with Sanity Studio 3.x; "
                "do not use Sanity 2.x with this codebase under any circumstances. "
                "NextAuth 5 has breaking changes from 4.x including the move to Auth.js "
                "naming and the new middleware API. Migration from NextAuth 4 is "
                "documented in MIGRATIONS.md and requires updating all session callbacks. "
                "Redis 7 is required for stream consumer groups support; Redis 6 will "
                "not work for the BullMQ queue patterns used by this architecture."
            ),
            "api_spec_json": {
                "paths": {
                    "/api/imports": {
                        "post": {
                            "summary": "Create import job",
                            "request": {"url": "string"},
                            "response": {"id": "string", "status": "string"},
                        },
                    },
                },
            },
            "db_schema_sql": (
                "CREATE TABLE imports (\n"
                "  id SERIAL PRIMARY KEY,\n"
                "  user_id INTEGER NOT NULL REFERENCES users(id),\n"
                "  url TEXT NOT NULL,\n"
                "  status TEXT NOT NULL DEFAULT 'pending',\n"
                "  version INTEGER NOT NULL DEFAULT 1,\n"
                "  created_at TIMESTAMP NOT NULL DEFAULT NOW()\n"
                ");\n\n"
                "CREATE TABLE users (\n"
                "  id SERIAL PRIMARY KEY,\n"
                "  email TEXT NOT NULL UNIQUE\n"
                ");"
            ),
            "model_self_check": {
                "all_required_sections_present": True,
                "concurrency_section_substantive": True,
                "compatibility_section_substantive": True,
                "no_placeholders": True,
                "no_simulation_language": True,
                "external_dependencies_verified": ["next@15.0", "@sanity/client@3"],
            },
        }

    def test_valid_response_passes(self):
        response = self._build_valid_response()
        arch, errors = rwa.validate_response(json.dumps(response))
        self.assertEqual(errors, [], f"Expected no errors, got: {errors}")
        self.assertIsNotNone(arch)

    def test_missing_top_field_rejected(self):
        response = self._build_valid_response()
        del response["db_schema_sql"]
        arch, errors = rwa.validate_response(json.dumps(response))
        self.assertIsNone(arch)
        self.assertTrue(any("db_schema_sql" in e for e in errors))

    def test_missing_required_section_rejected(self):
        response = self._build_valid_response()
        # Remove the Authentication section
        response["architecture_md"] = response["architecture_md"].replace(
            "## Authentication\nNextAuth with email magic links. JWT in HTTP-only cookies.\n\n", ""
        )
        arch, errors = rwa.validate_response(json.dumps(response))
        self.assertIsNone(arch)
        self.assertTrue(any("authentication" in e.lower() for e in errors))

    def test_shallow_concurrency_section_rejected(self):
        response = self._build_valid_response()
        response["architecture_md"] = response["architecture_md"].replace(
            response["architecture_md"][response["architecture_md"].find("## Concurrency"):response["architecture_md"].find("## Error Handling")],
            "## Concurrency\nWe use a queue.\n\n"
        )
        arch, errors = rwa.validate_response(json.dumps(response))
        self.assertIsNone(arch)
        self.assertTrue(any("concurrency" in e.lower() and "words" in e.lower() for e in errors))

    def test_simulation_language_rejected(self):
        response = self._build_valid_response()
        response["architecture_md"] += "\n\nIn a real implementation, you would also add caching."
        arch, errors = rwa.validate_response(json.dumps(response))
        self.assertIsNone(arch)
        self.assertTrue(any("simulation language" in e.lower() for e in errors))

    def test_no_create_table_rejected(self):
        response = self._build_valid_response()
        # SQL with no CREATE statements at all — just a comment that's long enough to pass the length check
        response["db_schema_sql"] = "-- This file is intentionally left empty for the purposes of this test fixture and contains no SQL statements."
        arch, errors = rwa.validate_response(json.dumps(response))
        self.assertIsNone(arch)
        self.assertTrue(any("CREATE TABLE" in e for e in errors))

    def test_self_check_false_rejected(self):
        response = self._build_valid_response()
        response["model_self_check"]["no_placeholders"] = False
        arch, errors = rwa.validate_response(json.dumps(response))
        self.assertIsNone(arch)
        self.assertTrue(any("model_self_check" in e and "no_placeholders" in e for e in errors))

    def test_invalid_json_rejected(self):
        arch, errors = rwa.validate_response("not json")
        self.assertIsNone(arch)
        self.assertTrue(any("not valid JSON" in e for e in errors))


# ============================================================================
# Test 6: Section coverage detection
# ============================================================================


class TestSectionCoverage(unittest.TestCase):

    def test_all_sections_present(self):
        md = "\n".join([
            "## Overview",
            "## Data Model",
            "## API Surface",
            "## Authentication",
            "## Authorization",
            "## Deployment",
            "## Observability",
            "## Concurrency",
            "## Error Handling",
            "## Dependencies",
            "## Compatibility",
        ])
        present, missing = rwa.check_section_coverage(md)
        self.assertEqual(missing, [])
        self.assertEqual(len(present), 11)

    def test_missing_concurrency_detected(self):
        md = "\n".join([
            "## Overview", "## Data Model", "## API Surface",
            "## Authentication", "## Authorization", "## Deployment",
            "## Observability", "## Error Handling", "## Dependencies",
            "## Compatibility",
        ])
        present, missing = rwa.check_section_coverage(md)
        self.assertIn("concurrency", missing)

    def test_fuzzy_match_works(self):
        md = "\n".join([
            "## Project Overview",
            "## Data Schema",  # matches "data model" pattern via "schema"
            "## API Endpoints",  # matches "api surface" pattern via "endpoints"
            "## User Identity",  # matches "authentication" via "identity"
            "## Permissions",  # matches "authorization" via "permissions"
            "## Hosting and Infrastructure",  # matches "deployment"
            "## Monitoring",  # matches "observability"
            "## Locking and Concurrency",
            "## Error Recovery",  # matches "error handling" via "recovery"
            "## Third-party Libraries",
            "## Supported Versions",
        ])
        present, missing = rwa.check_section_coverage(md)
        self.assertEqual(missing, [], f"Expected no missing sections, got: {missing}")


# ============================================================================
# Test 7: Dry run end-to-end
# ============================================================================


class TestDryRun(unittest.TestCase):

    def test_dry_run_full_protocol(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = build_phase5_workspace(Path(tmp))
            test_argv = [
                "invoke_rival_architect.py",
                "--workspace", str(ws),
                "--epic", "stitch-test",
                "--dry-run",
            ]
            with patch.object(sys, "argv", test_argv):
                with patch("builtins.print") as mock_print:
                    rwa.main()
            printed = mock_print.call_args[0][0]
            output = json.loads(printed)
            self.assertTrue(output["dry_run"])
            self.assertEqual(output["model"], "gemini-3-pro")
            # 3 if no learnings injected, 4 if memory injection active
            self.assertIn(output["message_count"], [3, 4])
            # First message must always contain ANCHOR
            self.assertIn("ANCHOR", output["messages_preview"][0]["content_preview"])
            # Find brief and task in the previews
            previews = [m["content_preview"] for m in output["messages_preview"]]
            brief_idx = next((i for i, p in enumerate(previews) if "DISCOVERY BRIEF" in p), -1)
            task_idx = next((i for i, p in enumerate(previews) if "TASK" in p), -1)
            self.assertGreater(brief_idx, 0, "DISCOVERY BRIEF must come after the anchor")
            self.assertGreater(task_idx, brief_idx, "TASK must come after the brief")


if __name__ == "__main__":
    unittest.main(verbosity=2)
