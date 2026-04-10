#!/usr/bin/env python3
"""Unit tests for the Silent Observer wrapper script protocol.

These tests are the PROOF that the structural protocol is enforced. Each test
asserts a specific protocol rule that the wrapper must never violate:

1. Inputs are whitelisted (cannot read self-assessment, handoff, or summary files)
2. Fixed paths (cannot be overridden by caller)
3. Goal-before-context-before-task message ordering
4. Fixed model (no fallback to same-family models)
5. Response validation rejects simulation language and schema violations
6. Deterministic decision logic (load-bearing contradicted = BLOCK)
7. Contamination scanning detects suspicious filenames without reading them
8. Halt protocol writes diagnostics and exits with the right code

Run with: pytest tests/test_wrapper_protocol.py -v
Or:       python3 -m unittest tests.test_wrapper_protocol
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts directory to path so we can import the wrapper
SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import invoke_silent_observer as siw  # noqa: E402


# ============================================================================
# Test fixtures — synthetic workspace
# ============================================================================


def build_fixture_workspace(
    root: Path,
    sprint_goal: str = "Increase therapist profile completion rate from 38% to 60% within 14 days",
    product_description: str = "Insite is a website builder for therapists.",
    brief_content: str = "The Stitch SDK has an extractUrl() method that takes a URL and returns metadata.",
    epic: str = "test-epic",
    include_contamination: bool = False,
) -> Path:
    """Build a synthetic startup workspace with the three required files."""
    state_dir = root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "project_config.json").write_text(
        json.dumps({"product_description": product_description, "other_field": "ignored"})
    )
    (state_dir / "sprint_plan.json").write_text(
        json.dumps({"goal": sprint_goal, "other_field": "ignored"})
    )
    (state_dir / "company_state.json").write_text(json.dumps({}))

    research_dir = root / "artifacts" / "research" / epic
    research_dir.mkdir(parents=True, exist_ok=True)
    (research_dir / "discovery_brief.md").write_text(brief_content)

    if include_contamination:
        # These files should NEVER be read by the wrapper
        (research_dir / "vp_product_self_assessment.md").write_text(
            "I am the VP Product agent and here is my reasoning: I believe X because Y"
        )
        (research_dir / "handoff_to_architect.md").write_text(
            "Architect, please use the extractUrl() method I found"
        )
        (research_dir / "summary_for_coo.md").write_text(
            "Summary: all checks passed, ready for next phase"
        )
        (research_dir / "reasoning_trace.md").write_text(
            "My reasoning was based on training data knowledge of the Stitch SDK"
        )

    return root


# ============================================================================
# Test 1: Input whitelisting
# ============================================================================


class TestInputWhitelisting(unittest.TestCase):
    """The wrapper must only read the three whitelisted inputs. Never anything else."""

    def test_load_inputs_reads_only_three_files(self):
        """load_inputs must return only sprint_goal, product_description, discovery_brief."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = build_fixture_workspace(Path(tmp))
            inputs = siw.load_inputs(ws, "test-epic")

            # The ReviewInputs dataclass must contain exactly these fields
            self.assertEqual(
                inputs.sprint_goal,
                "Increase therapist profile completion rate from 38% to 60% within 14 days",
            )
            self.assertEqual(inputs.product_description, "Insite is a website builder for therapists.")
            self.assertIn("extractUrl", inputs.discovery_brief)

    def test_load_inputs_signature_does_not_accept_context(self):
        """The function signature must only accept workspace and epic.

        This is the structural defense: the COO cannot pass additional context
        as an argument because the function does not accept one.
        """
        import inspect
        sig = inspect.signature(siw.load_inputs)
        params = list(sig.parameters.keys())
        # Only workspace and epic — no context, no additional_info, no primary_reasoning
        self.assertEqual(params, ["workspace", "epic"])

    def test_contamination_files_are_detected_but_not_read(self):
        """The wrapper must DETECT contamination files but must NOT read them."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = build_fixture_workspace(Path(tmp), include_contamination=True)
            inputs = siw.load_inputs(ws, "test-epic")

            # The three whitelisted inputs are loaded
            self.assertIn("extractUrl", inputs.discovery_brief)

            # The contamination files are detected
            contamination = siw.scan_for_contamination(ws, "test-epic")
            self.assertEqual(len(contamination), 4)
            contamination_names = {Path(p).name for p in contamination}
            self.assertIn("vp_product_self_assessment.md", contamination_names)
            self.assertIn("handoff_to_architect.md", contamination_names)
            self.assertIn("summary_for_coo.md", contamination_names)
            self.assertIn("reasoning_trace.md", contamination_names)

            # Critical: the inputs object must NOT contain any content from these files
            all_inputs = inputs.sprint_goal + inputs.product_description + inputs.discovery_brief
            self.assertNotIn("self-assessment", all_inputs.lower())
            self.assertNotIn("my reasoning was based on training data", all_inputs.lower())
            self.assertNotIn("summary: all checks passed", all_inputs.lower())
            self.assertNotIn("architect, please use", all_inputs.lower())


# ============================================================================
# Test 2: Fixed paths (cannot be overridden)
# ============================================================================


class TestFixedPaths(unittest.TestCase):
    """The wrapper must read from fixed paths. Calling code cannot redirect it."""

    def test_missing_project_config_halts(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / "state").mkdir()
            (ws / "state" / "sprint_plan.json").write_text(json.dumps({"goal": "X"}))
            (ws / "artifacts" / "research" / "test-epic").mkdir(parents=True)
            (ws / "artifacts" / "research" / "test-epic" / "discovery_brief.md").write_text("brief")

            with self.assertRaises(SystemExit) as cm:
                siw.load_inputs(ws, "test-epic")
            self.assertEqual(cm.exception.code, 1)

    def test_missing_sprint_plan_halts(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / "state").mkdir()
            (ws / "state" / "project_config.json").write_text(json.dumps({"product_description": "X"}))
            (ws / "artifacts" / "research" / "test-epic").mkdir(parents=True)
            (ws / "artifacts" / "research" / "test-epic" / "discovery_brief.md").write_text("brief")

            with self.assertRaises(SystemExit) as cm:
                siw.load_inputs(ws, "test-epic")
            self.assertEqual(cm.exception.code, 1)

    def test_missing_discovery_brief_halts(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (ws / "state").mkdir()
            (ws / "state" / "project_config.json").write_text(
                json.dumps({"product_description": "X"})
            )
            (ws / "state" / "sprint_plan.json").write_text(json.dumps({"goal": "X"}))
            # NO discovery_brief.md

            with self.assertRaises(SystemExit) as cm:
                siw.load_inputs(ws, "test-epic")
            self.assertEqual(cm.exception.code, 1)

    def test_empty_brief_halts(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = build_fixture_workspace(Path(tmp), brief_content="")
            with self.assertRaises(SystemExit) as cm:
                siw.load_inputs(ws, "test-epic")
            self.assertEqual(cm.exception.code, 1)

    def test_empty_goal_halts(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = build_fixture_workspace(Path(tmp), sprint_goal="")
            with self.assertRaises(SystemExit) as cm:
                siw.load_inputs(ws, "test-epic")
            self.assertEqual(cm.exception.code, 1)


# ============================================================================
# Test 3: Goal-before-context-before-task message ordering
# ============================================================================


class TestMessageOrdering(unittest.TestCase):
    """The wrapper must build messages in the protocol order: goal → brief → task."""

    def test_build_messages_ordering(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = build_fixture_workspace(Path(tmp))
            inputs = siw.load_inputs(ws, "test-epic")
            messages, system_prompt = siw.build_messages(inputs)

            # 3 messages if no process learnings available, 4 if memory has them
            # (PROCESS LEARNINGS message is optional and inserted between anchor and brief)
            self.assertIn(len(messages), [3, 4], f"Expected 3 or 4 messages, got {len(messages)}")

            # Message 1 must be the goal, alone (always position 0)
            msg1 = messages[0]["content"]
            self.assertIn("ANCHOR", msg1)
            self.assertIn("Increase therapist profile completion rate from 38% to 60%", msg1)
            self.assertNotIn("extractUrl", msg1)

            # The DISCOVERY BRIEF must come AFTER the anchor and BEFORE the task
            brief_idx = next(
                (i for i, m in enumerate(messages) if "DISCOVERY BRIEF" in m["content"]),
                -1,
            )
            task_idx = next(
                (i for i, m in enumerate(messages) if "TASK" in m["content"] and "verify" in m["content"].lower()),
                -1,
            )
            self.assertGreater(brief_idx, 0, "DISCOVERY BRIEF must come after the anchor")
            self.assertGreater(task_idx, brief_idx, "TASK must come after DISCOVERY BRIEF")

            # Brief must contain the brief content but not the anchor
            brief_msg = messages[brief_idx]["content"]
            self.assertIn("extractUrl", brief_msg)
            self.assertNotIn("ANCHOR", brief_msg)

            # Task must contain the task instruction
            task_msg = messages[task_idx]["content"]
            self.assertIn("TASK", task_msg)
            self.assertNotIn("extractUrl", task_msg)

            # If process learnings present, they must come BEFORE the brief
            process_idx = next(
                (i for i, m in enumerate(messages) if "PROCESS LEARNINGS" in m["content"]),
                -1,
            )
            if process_idx >= 0:
                self.assertLess(process_idx, brief_idx, "PROCESS LEARNINGS must come before DISCOVERY BRIEF")
                self.assertGreater(process_idx, 0, "PROCESS LEARNINGS must come after the anchor")

    def test_system_prompt_loaded_from_disk(self):
        """The system prompt must be loaded from the static file, not constructed dynamically."""
        prompt = siw.load_system_prompt()
        self.assertIn("Silent Observer", prompt)
        self.assertIn("load-bearing", prompt)
        # The prompt should contain the schema definition
        self.assertIn("sprint_goal", prompt)
        self.assertIn("claims", prompt)
        self.assertIn("verdict", prompt)


# ============================================================================
# Test 4: Fixed model
# ============================================================================


class TestFixedModel(unittest.TestCase):
    """The wrapper must use gemini-3-pro and must not fall back to other models."""

    def test_fixed_model_constant(self):
        self.assertEqual(siw.FIXED_MODEL, "gemini-3-pro")

    def test_call_gemini_halts_without_api_key(self):
        """If GEMINI_API_KEY is not set, halt — do not silently fall back."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit) as cm:
                siw.call_gemini("system", [{"role": "user", "content": "test"}])
            self.assertEqual(cm.exception.code, 2)


# ============================================================================
# Test 5: Response validation
# ============================================================================


class TestResponseValidation(unittest.TestCase):
    """The wrapper must reject malformed, simulation-language, or mismatched responses."""

    def _build_valid_response(self) -> dict:
        return {
            "sprint_goal": "X",
            "brief_path": "/path/to/brief.md",
            "total_claims_identified": 1,
            "claims": [
                {
                    "claim_id": "C1",
                    "quote": "Stitch SDK has an extractUrl() method",
                    "source_line": "line 5",
                    "claim_type": "api_sdk",
                    "load_bearing": True,
                    "load_bearing_reason": "Architecture depends on this method existing",
                    "verification_method": "WebSearch for stitch sdk extractUrl",
                    "verification_attempts": [
                        {
                            "method": "WebSearch",
                            "query": "stitch sdk extractUrl method",
                            "result_summary": "No method named extractUrl in Stitch SDK docs",
                            "sources_consulted": ["https://stitch.io/docs/sdk"],
                        },
                        {
                            "method": "WebFetch",
                            "query": "https://stitch.io/docs/sdk/reference",
                            "result_summary": "Full SDK reference has scrape() and fetch() methods but no extractUrl",
                            "sources_consulted": ["https://stitch.io/docs/sdk/reference"],
                        },
                        {
                            "method": "WebSearch",
                            "query": "stitch sdk extract url method 2026",
                            "result_summary": "No recent discussion of extractUrl in Stitch community",
                            "sources_consulted": ["https://github.com/stitch/stitch-sdk/issues"],
                        },
                    ],
                    "verdict": "CONTRADICTED",
                    "verdict_evidence_quote": "The Stitch SDK provides scrape(), fetch(), and crawl() methods. No method named extractUrl exists.",
                    "verdict_evidence_source": "https://stitch.io/docs/sdk/reference",
                }
            ],
            "summary": {
                "verified_count": 0,
                "unverifiable_count": 0,
                "contradicted_count": 1,
                "load_bearing_contradicted_count": 1,
                "load_bearing_unverifiable_count": 0,
            },
        }

    def test_valid_response_passes(self):
        response_text = json.dumps(self._build_valid_response())
        data, errors = siw.validate_response(response_text)
        self.assertEqual(errors, [])
        self.assertIsNotNone(data)

    def test_non_json_rejected(self):
        data, errors = siw.validate_response("This is not JSON at all")
        self.assertIsNone(data)
        self.assertEqual(len(errors), 1)
        self.assertIn("not valid JSON", errors[0])

    def test_missing_top_level_field_rejected(self):
        response = self._build_valid_response()
        del response["summary"]
        data, errors = siw.validate_response(json.dumps(response))
        self.assertIsNone(data)
        self.assertTrue(any("summary" in e for e in errors))

    def test_simulation_language_rejected(self):
        response = self._build_valid_response()
        # Inject simulation language into one of the fields
        response["claims"][0]["verdict_evidence_quote"] = "In a real implementation, this method would exist."
        data, errors = siw.validate_response(json.dumps(response))
        self.assertIsNone(data)
        self.assertTrue(
            any("simulation language" in e.lower() for e in errors),
            f"Expected simulation language error, got: {errors}",
        )

    def test_verified_without_evidence_rejected(self):
        response = self._build_valid_response()
        response["claims"][0]["verdict"] = "VERIFIED"
        response["claims"][0]["verdict_evidence_quote"] = ""
        response["summary"]["verified_count"] = 1
        response["summary"]["contradicted_count"] = 0
        response["summary"]["load_bearing_contradicted_count"] = 0
        data, errors = siw.validate_response(json.dumps(response))
        self.assertIsNone(data)
        self.assertTrue(
            any("VERIFIED" in e and "evidence" in e.lower() for e in errors),
            f"Expected VERIFIED-without-evidence error, got: {errors}",
        )

    def test_contradicted_with_fewer_than_three_attempts_rejected(self):
        response = self._build_valid_response()
        # Truncate to 1 attempt
        response["claims"][0]["verification_attempts"] = response["claims"][0]["verification_attempts"][:1]
        data, errors = siw.validate_response(json.dumps(response))
        self.assertIsNone(data)
        self.assertTrue(
            any("CONTRADICTED" in e and "3" in e for e in errors),
            f"Expected 3-attempts error, got: {errors}",
        )

    def test_invalid_verdict_rejected(self):
        response = self._build_valid_response()
        response["claims"][0]["verdict"] = "PROBABLY_TRUE"
        data, errors = siw.validate_response(json.dumps(response))
        self.assertIsNone(data)
        self.assertTrue(any("invalid verdict" in e.lower() for e in errors))

    def test_summary_count_mismatch_rejected(self):
        response = self._build_valid_response()
        response["summary"]["contradicted_count"] = 99  # lie about the count
        data, errors = siw.validate_response(json.dumps(response))
        self.assertIsNone(data)
        self.assertTrue(any("contradicted_count" in e for e in errors))


# ============================================================================
# Test 6: Deterministic decision logic
# ============================================================================


class TestDecisionLogic(unittest.TestCase):
    """The verdict must be deterministic code, not LLM judgment."""

    def test_load_bearing_contradicted_blocks(self):
        data = {
            "claims": [
                {
                    "claim_id": "C1",
                    "quote": "X",
                    "source_line": "1",
                    "claim_type": "api_sdk",
                    "load_bearing": True,
                    "load_bearing_reason": "Y",
                    "verification_method": "WebSearch",
                    "verification_attempts": [{"method": "WebSearch", "query": "q", "result_summary": "r"}],
                    "verdict": "CONTRADICTED",
                    "verdict_evidence_quote": "Z",
                    "verdict_evidence_source": "https://example.com",
                }
            ]
        }
        result = siw.compute_verdict(data)
        self.assertEqual(result.verdict, "BLOCK")
        self.assertEqual(len(result.load_bearing_contradicted), 1)

    def test_load_bearing_unverifiable_blocks(self):
        data = {
            "claims": [
                {
                    "claim_id": "C1",
                    "quote": "X",
                    "source_line": "1",
                    "claim_type": "api_sdk",
                    "load_bearing": True,
                    "load_bearing_reason": "Y",
                    "verification_method": "WebSearch",
                    "verification_attempts": [],
                    "verdict": "UNVERIFIABLE",
                    "verdict_evidence_quote": "",
                    "verdict_evidence_source": "",
                }
            ]
        }
        result = siw.compute_verdict(data)
        self.assertEqual(result.verdict, "BLOCK")
        self.assertEqual(len(result.load_bearing_unverifiable), 1)

    def test_non_load_bearing_contradicted_flags_not_blocks(self):
        data = {
            "claims": [
                {
                    "claim_id": "C1",
                    "quote": "X",
                    "source_line": "1",
                    "claim_type": "market_stat",
                    "load_bearing": False,
                    "load_bearing_reason": "background",
                    "verification_method": "WebSearch",
                    "verification_attempts": [],
                    "verdict": "CONTRADICTED",
                    "verdict_evidence_quote": "Z",
                    "verdict_evidence_source": "https://example.com",
                }
            ]
        }
        result = siw.compute_verdict(data)
        self.assertEqual(result.verdict, "FLAG")
        self.assertEqual(len(result.flag_claims), 1)

    def test_all_verified_approves(self):
        data = {
            "claims": [
                {
                    "claim_id": "C1",
                    "quote": "X",
                    "source_line": "1",
                    "claim_type": "api_sdk",
                    "load_bearing": True,
                    "load_bearing_reason": "Y",
                    "verification_method": "WebSearch",
                    "verification_attempts": [],
                    "verdict": "VERIFIED",
                    "verdict_evidence_quote": "Z",
                    "verdict_evidence_source": "https://example.com",
                }
            ]
        }
        result = siw.compute_verdict(data)
        self.assertEqual(result.verdict, "APPROVE")
        self.assertEqual(len(result.verified_claims), 1)

    def test_no_claims_approves(self):
        """A brief with no factual claims is approved (no verdict issues)."""
        data = {"claims": []}
        result = siw.compute_verdict(data)
        self.assertEqual(result.verdict, "APPROVE")
        self.assertEqual(result.total_claims, 0)


# ============================================================================
# Test 7: Dry run (end-to-end protocol check without API call)
# ============================================================================


class TestDryRun(unittest.TestCase):
    """End-to-end check that the full protocol runs without calling the API."""

    def test_dry_run_produces_structured_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = build_fixture_workspace(Path(tmp))
            # Call main() with --dry-run
            test_argv = [
                "invoke_silent_observer.py",
                "--workspace",
                str(ws),
                "--epic",
                "test-epic",
                "--dry-run",
            ]
            with patch.object(sys, "argv", test_argv):
                with patch("builtins.print") as mock_print:
                    siw.main()

            # Extract the printed JSON
            printed = mock_print.call_args[0][0]
            output = json.loads(printed)

            self.assertTrue(output["dry_run"])
            self.assertEqual(output["model"], "gemini-3-pro")
            # 3 if no process learnings injected, 4 if memory injection is active
            self.assertIn(output["message_count"], [3, 4])
            # Goal must always be first
            self.assertIn("ANCHOR", output["messages_preview"][0]["content_preview"])
            # Find the brief and task in the message list
            previews = [m["content_preview"] for m in output["messages_preview"]]
            brief_idx = next((i for i, p in enumerate(previews) if "DISCOVERY BRIEF" in p), -1)
            task_idx = next((i for i, p in enumerate(previews) if "TASK" in p), -1)
            self.assertGreater(brief_idx, 0, "DISCOVERY BRIEF must come after the anchor")
            self.assertGreater(task_idx, brief_idx, "TASK must come after the brief")

    def test_dry_run_with_contamination_detects_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = build_fixture_workspace(Path(tmp), include_contamination=True)
            test_argv = [
                "invoke_silent_observer.py",
                "--workspace",
                str(ws),
                "--epic",
                "test-epic",
                "--dry-run",
            ]
            with patch.object(sys, "argv", test_argv):
                with patch("builtins.print") as mock_print:
                    siw.main()

            printed = mock_print.call_args[0][0]
            output = json.loads(printed)

            self.assertEqual(len(output["contamination_found"]), 4)


# ============================================================================
# Entry point
# ============================================================================


if __name__ == "__main__":
    unittest.main(verbosity=2)
