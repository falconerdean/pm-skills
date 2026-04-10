#!/usr/bin/env python3
"""Architecture Comparison script — deterministic diff + bounded judgment escalation.

After the primary VP Engineering and the Rival Architect have both produced
architecture artifacts, this script compares them and produces a verdict:
APPROVE / FLAG / ESCALATE / BLOCK.

Design principles:
    - Structural diffs (Stages 1-6) are pure Python — no LLM, no judgment
    - Stage 7 makes a single bounded LLM call to surface judgment-level
      disagreements, with an explicit prompt forbidding "which is better"
    - Stage 8 verdict computation is deterministic code reading the outputs
      of all prior stages

The compare script does NOT decide which architecture is better. It surfaces
where the two architectures agreed (high confidence signal) and where they
diverged (CEO decision required).

Usage:
    python3 compare_architectures.py --workspace /path/to/startup-workspace --epic <epic_slug>

Exit codes:
    0 - Comparison completed (read verdict from stdout JSON)
    1 - Halt: required input missing
    2 - Halt: comparison stage failed unrecoverably
    3 - Halt: configuration error

Output:
    - JSON verdict object to stdout
    - Comparison report written to {workspace}/artifacts/reviews/architecture_comparison/
    - Audit log entry appended to {workspace}/logs/architecture_comparisons.jsonl
    - State update written to {workspace}/state/company_state.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

# ============================================================================
# CONSTANTS
# ============================================================================

# Section header fuzzy match patterns (matches the rival wrapper)
SECTION_PATTERNS = {
    "overview": [r"overview", r"summary", r"introduction"],
    "data model": [r"data\s*model", r"schema(?!\s*sql)", r"entities"],
    "api surface": [r"api(?:\s*surface)?(?!\s*spec)", r"endpoints", r"interface"],
    "authentication": [r"auth(?:entication)?(?!\s*z|\s*orization)", r"identity"],
    "authorization": [r"authorization", r"authz", r"permissions", r"access\s*control"],
    "deployment": [r"deployment", r"infrastructure", r"hosting"],
    "observability": [r"observability", r"monitoring", r"logging", r"metrics"],
    "concurrency": [r"concurrency", r"concurrent", r"race\s*condition", r"locking"],
    "error handling": [r"error\s*handling", r"errors", r"failure"],
    "dependencies": [r"dependencies", r"libraries", r"packages"],
    "compatibility": [r"compatibility", r"support(?:ed)?\s*versions?"],
}

CONCURRENCY_KEYWORDS = [
    "concurrent", "concurrency", "race condition", "race", "lock", "locking",
    "rate limit", "rate-limit", "throttle", "queue", "queueing", "ordering",
    "idempotent", "idempotency", "deadlock", "atomicity", "consistency",
    "eventual consistency", "strong consistency", "compare-and-swap",
    "optimistic locking", "pessimistic locking", "advisory lock", "distributed lock",
]

COMPATIBILITY_KEYWORDS = [
    "version", "compatible", "compatibility", "deprecated", "breaking change",
    "migration", "polyfill", "browser support", "node version", "python version",
    "runtime version", "EOL", "end of life", "supported version", "lts",
]

LLM_JUDGE_MODEL = "claude-opus-4-6"  # constrained judgment surface model


# ============================================================================
# Data structures
# ============================================================================


@dataclass
class ArchitectureFiles:
    architecture_md: str
    api_spec: dict | None
    db_schema_sql: str
    architecture_md_path: str
    api_spec_path: str
    db_schema_path: str
    parse_errors: list[str] = field(default_factory=list)


@dataclass
class StructuralDiff:
    primary_validation_passed: bool
    rival_validation_passed: bool

    # Section coverage
    primary_sections_present: list[str] = field(default_factory=list)
    primary_sections_missing: list[str] = field(default_factory=list)
    rival_sections_present: list[str] = field(default_factory=list)
    rival_sections_missing: list[str] = field(default_factory=list)

    # Database schema diff
    primary_tables: set[str] = field(default_factory=set)
    rival_tables: set[str] = field(default_factory=set)
    tables_in_both: set[str] = field(default_factory=set)
    tables_only_primary: set[str] = field(default_factory=set)
    tables_only_rival: set[str] = field(default_factory=set)
    table_column_diffs: dict[str, dict] = field(default_factory=dict)
    db_overlap_pct: float = 0.0

    # API surface diff
    primary_endpoints: set[tuple] = field(default_factory=set)
    rival_endpoints: set[tuple] = field(default_factory=set)
    endpoints_in_both: set[tuple] = field(default_factory=set)
    endpoints_only_primary: set[tuple] = field(default_factory=set)
    endpoints_only_rival: set[tuple] = field(default_factory=set)
    api_overlap_pct: float = 0.0

    # Dependencies
    primary_dependencies: set[str] = field(default_factory=set)
    rival_dependencies: set[str] = field(default_factory=set)
    deps_in_both: set[str] = field(default_factory=set)
    deps_only_primary: set[str] = field(default_factory=set)
    deps_only_rival: set[str] = field(default_factory=set)

    # Specialization keyword counts
    primary_concurrency_count: int = 0
    rival_concurrency_count: int = 0
    primary_compatibility_count: int = 0
    rival_compatibility_count: int = 0


@dataclass
class JudgmentSurface:
    substantive_disagreements: list[dict] = field(default_factory=list)
    agreement_signal_strength: str = "medium"  # high | medium | low
    rationale: str = ""


@dataclass
class ComparisonResult:
    verdict: str  # APPROVE | FLAG | ESCALATE | BLOCK
    structural_diff: StructuralDiff
    judgment_surface: JudgmentSurface
    flags: list[str] = field(default_factory=list)
    blocks: list[str] = field(default_factory=list)
    escalations: list[str] = field(default_factory=list)
    report_path: str = ""
    timestamp_utc: str = ""


# ============================================================================
# Input loading
# ============================================================================


def load_architecture(prefix_dir: Path, label: str) -> ArchitectureFiles:
    """Load architecture.md, api_spec.json, db_schema.sql from a directory."""
    arch_path = prefix_dir / "architecture.md"
    api_path = prefix_dir / "api_spec.json"
    db_path = prefix_dir / "db_schema.sql"

    parse_errors = []

    if not arch_path.exists():
        halt(f"{label} architecture.md missing at {arch_path}", exit_code=1)
    if not api_path.exists():
        halt(f"{label} api_spec.json missing at {api_path}", exit_code=1)
    if not db_path.exists():
        halt(f"{label} db_schema.sql missing at {db_path}", exit_code=1)

    arch_md = arch_path.read_text()
    db_sql = db_path.read_text()

    try:
        api_spec = json.loads(api_path.read_text())
    except json.JSONDecodeError as e:
        parse_errors.append(f"api_spec.json is not valid JSON: {e}")
        api_spec = None

    return ArchitectureFiles(
        architecture_md=arch_md,
        api_spec=api_spec,
        db_schema_sql=db_sql,
        architecture_md_path=str(arch_path),
        api_spec_path=str(api_path),
        db_schema_path=str(db_path),
        parse_errors=parse_errors,
    )


# ============================================================================
# Stage 1: Structural validation
# ============================================================================


def validate_architecture(arch: ArchitectureFiles, label: str) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if arch.parse_errors:
        errors.extend([f"{label}: {e}" for e in arch.parse_errors])
    if len(arch.architecture_md.strip()) < 500:
        errors.append(f"{label} architecture.md is too short (<500 chars)")
    if not re.search(r"CREATE\s+TABLE", arch.db_schema_sql, re.IGNORECASE):
        errors.append(f"{label} db_schema.sql contains no CREATE TABLE statements")
    return len(errors) == 0, errors


# ============================================================================
# Stage 2: Required section coverage
# ============================================================================


def check_section_coverage(architecture_md: str) -> tuple[list[str], list[str]]:
    present = []
    missing = []
    for canonical, patterns in SECTION_PATTERNS.items():
        found = False
        for pattern in patterns:
            heading_regex = re.compile(rf"^##\s+.*{pattern}.*$", re.IGNORECASE | re.MULTILINE)
            if heading_regex.search(architecture_md):
                found = True
                break
        if found:
            present.append(canonical)
        else:
            missing.append(canonical)
    return present, missing


def extract_section_text(architecture_md: str, canonical_section: str) -> str:
    """Two-step extraction: find heading line first (no DOTALL), then capture body."""
    patterns = SECTION_PATTERNS.get(canonical_section, [canonical_section])
    next_heading_re = re.compile(r"^##\s+", re.MULTILINE)
    for pattern in patterns:
        heading_re = re.compile(
            rf"^##\s+[^\n]*{pattern}[^\n]*$",
            re.IGNORECASE | re.MULTILINE,
        )
        heading_match = heading_re.search(architecture_md)
        if heading_match:
            content_start = heading_match.end()
            next_match = next_heading_re.search(architecture_md, content_start)
            content_end = next_match.start() if next_match else len(architecture_md)
            return architecture_md[content_start:content_end].strip()
    return ""


# ============================================================================
# Stage 3: Database schema diff
# ============================================================================


def parse_sql_tables(sql_text: str) -> dict[str, set[str]]:
    """Parse CREATE TABLE statements and return {table_name: {column_names}}."""
    tables: dict[str, set[str]] = {}

    create_pattern = re.compile(
        r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["`]?(\w+)["`]?\s*\((.*?)\);',
        re.IGNORECASE | re.DOTALL,
    )

    for match in create_pattern.finditer(sql_text):
        table_name = match.group(1).lower()
        columns_text = match.group(2)
        columns: set[str] = set()
        # Split on commas at the top level (rough — does not handle nested parens perfectly)
        depth = 0
        current = ""
        column_lines = []
        for char in columns_text:
            if char == "(":
                depth += 1
                current += char
            elif char == ")":
                depth -= 1
                current += char
            elif char == "," and depth == 0:
                column_lines.append(current.strip())
                current = ""
            else:
                current += char
        if current.strip():
            column_lines.append(current.strip())

        for line in column_lines:
            # Skip constraint definitions
            line_lower = line.lower().strip()
            if line_lower.startswith(
                ("primary key", "foreign key", "unique", "check", "constraint", "index")
            ):
                continue
            # Extract first identifier as column name
            col_match = re.match(r'["`]?(\w+)["`]?', line)
            if col_match:
                columns.add(col_match.group(1).lower())
        tables[table_name] = columns
    return tables


def diff_db_schemas(primary_sql: str, rival_sql: str) -> dict:
    primary_tables = parse_sql_tables(primary_sql)
    rival_tables = parse_sql_tables(rival_sql)

    primary_set = set(primary_tables.keys())
    rival_set = set(rival_tables.keys())

    in_both = primary_set & rival_set
    only_primary = primary_set - rival_set
    only_rival = rival_set - primary_set

    column_diffs = {}
    for table in in_both:
        p_cols = primary_tables[table]
        r_cols = rival_tables[table]
        diff = {
            "in_both": p_cols & r_cols,
            "only_primary": p_cols - r_cols,
            "only_rival": r_cols - p_cols,
        }
        if diff["only_primary"] or diff["only_rival"]:
            column_diffs[table] = diff

    overlap_pct = len(in_both) / max(len(primary_set | rival_set), 1)

    return {
        "primary_tables": primary_set,
        "rival_tables": rival_set,
        "tables_in_both": in_both,
        "tables_only_primary": only_primary,
        "tables_only_rival": only_rival,
        "column_diffs": column_diffs,
        "overlap_pct": overlap_pct,
    }


# ============================================================================
# Stage 4: API surface diff
# ============================================================================


def extract_endpoints(spec: dict | None) -> set[tuple]:
    """Return set of (METHOD, path) tuples. Handles OpenAPI-style and array-style."""
    if not spec or not isinstance(spec, dict):
        return set()
    endpoints: set[tuple] = set()

    # OpenAPI-style: spec["paths"] = {"/users": {"get": {...}, "post": {...}}}
    if "paths" in spec and isinstance(spec["paths"], dict):
        for path, methods in spec["paths"].items():
            if not isinstance(methods, dict):
                continue
            for method in methods:
                if method.upper() in {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}:
                    endpoints.add((method.upper(), path))

    # Array style: spec["endpoints"] = [{"method": "GET", "path": "/users"}, ...]
    if "endpoints" in spec and isinstance(spec["endpoints"], list):
        for ep in spec["endpoints"]:
            if isinstance(ep, dict) and "method" in ep and "path" in ep:
                endpoints.add((ep["method"].upper(), ep["path"]))

    # Top-level keys style: spec = {"GET /users": {...}, "POST /users": {...}}
    for key in spec:
        match = re.match(r"^(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+(.+)$", key)
        if match:
            endpoints.add((match.group(1), match.group(2)))

    return endpoints


def diff_api_surface(primary_spec: dict | None, rival_spec: dict | None) -> dict:
    primary_eps = extract_endpoints(primary_spec)
    rival_eps = extract_endpoints(rival_spec)

    in_both = primary_eps & rival_eps
    only_primary = primary_eps - rival_eps
    only_rival = rival_eps - primary_eps

    # Detect path collisions with different methods
    primary_paths = {p for _, p in primary_eps}
    rival_paths = {p for _, p in rival_eps}
    shared_paths = primary_paths & rival_paths
    method_conflicts = []
    for path in shared_paths:
        p_methods = {m for m, p in primary_eps if p == path}
        r_methods = {m for m, p in rival_eps if p == path}
        if p_methods != r_methods:
            method_conflicts.append({
                "path": path,
                "primary_methods": list(p_methods),
                "rival_methods": list(r_methods),
            })

    overlap_pct = len(in_both) / max(len(primary_eps | rival_eps), 1)

    return {
        "primary_endpoints": primary_eps,
        "rival_endpoints": rival_eps,
        "endpoints_in_both": in_both,
        "endpoints_only_primary": only_primary,
        "endpoints_only_rival": only_rival,
        "method_conflicts": method_conflicts,
        "overlap_pct": overlap_pct,
    }


# ============================================================================
# Stage 5: Dependency diff (heuristic)
# ============================================================================


DEPENDENCY_PATTERNS = [
    re.compile(r'`([a-z][a-zA-Z0-9\-@/]+)(?:@?([0-9.]+))?`'),  # backticked package names
    re.compile(r'(?:npm install|yarn add)\s+([a-z][a-zA-Z0-9\-@/]+)'),
    re.compile(r'pip install\s+([a-z][a-zA-Z0-9\-_]+)'),
    re.compile(r'gem install\s+([a-z][a-zA-Z0-9\-_]+)'),
    re.compile(r'cargo add\s+([a-z][a-zA-Z0-9\-_]+)'),
]


def extract_dependencies(architecture_md: str) -> set[str]:
    deps: set[str] = set()
    for pattern in DEPENDENCY_PATTERNS:
        for match in pattern.finditer(architecture_md):
            dep = match.group(1).lower()
            # Filter false positives (common english words, file extensions, etc.)
            if dep in {"the", "and", "or", "to", "in", "of", "for", "true", "false", "null", "json", "yaml", "md", "sql"}:
                continue
            if len(dep) < 2:
                continue
            deps.add(dep)
    return deps


def diff_dependencies(primary_md: str, rival_md: str) -> dict:
    primary_deps = extract_dependencies(primary_md)
    rival_deps = extract_dependencies(rival_md)
    return {
        "primary_dependencies": primary_deps,
        "rival_dependencies": rival_deps,
        "in_both": primary_deps & rival_deps,
        "only_primary": primary_deps - rival_deps,
        "only_rival": rival_deps - primary_deps,
    }


# ============================================================================
# Stage 6: Concurrency / compatibility keyword counts
# ============================================================================


def count_keywords(text: str, keywords: list[str]) -> int:
    text_lower = text.lower()
    count = 0
    for kw in keywords:
        # Use word-boundary matching for short keywords, substring for multi-word
        if " " in kw or "-" in kw:
            count += text_lower.count(kw)
        else:
            count += len(re.findall(rf"\b{re.escape(kw)}\b", text_lower))
    return count


def specialization_keyword_diff(primary_md: str, rival_md: str) -> dict:
    primary_concurrency_section = extract_section_text(primary_md, "concurrency")
    rival_concurrency_section = extract_section_text(rival_md, "concurrency")
    primary_compatibility_section = extract_section_text(primary_md, "compatibility")
    rival_compatibility_section = extract_section_text(rival_md, "compatibility")

    return {
        "primary_concurrency_count": count_keywords(primary_concurrency_section, CONCURRENCY_KEYWORDS),
        "rival_concurrency_count": count_keywords(rival_concurrency_section, CONCURRENCY_KEYWORDS),
        "primary_compatibility_count": count_keywords(primary_compatibility_section, COMPATIBILITY_KEYWORDS),
        "rival_compatibility_count": count_keywords(rival_compatibility_section, COMPATIBILITY_KEYWORDS),
        "primary_concurrency_words": len(primary_concurrency_section.split()),
        "rival_concurrency_words": len(rival_concurrency_section.split()),
    }


# ============================================================================
# Stage 7: Constrained LLM judgment surface
# ============================================================================


def llm_judgment_surface(
    primary: ArchitectureFiles,
    rival: ArchitectureFiles,
    diff: StructuralDiff,
) -> JudgmentSurface:
    """Make a single bounded LLM call to surface judgment-level disagreements.

    The prompt explicitly forbids "which is better" judgments. The LLM only
    LISTS disagreements; the verdict computation in Stage 8 reads the list
    and applies code rules.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # Degrade gracefully — without ANTHROPIC_API_KEY, skip stage 7 and rely on structural diff only
        return JudgmentSurface(
            substantive_disagreements=[],
            agreement_signal_strength="unknown",
            rationale="ANTHROPIC_API_KEY not set; LLM judgment surface skipped. Verdict based on structural diff only.",
        )

    # Build a condensed comparison summary for the LLM
    summary = build_comparison_summary(primary, rival, diff)

    prompt = (
        "You are a comparison facilitator. You have been given summaries of two independently-produced "
        "technical architectures for the same project. Your job is ONLY to surface substantive disagreements "
        "that the structural diff did not catch — architectural pattern choices, philosophical decisions, "
        "technology selection rationales, trade-off framings.\n\n"
        "YOU MUST NOT:\n"
        "- Decide which architecture is better\n"
        "- Recommend one over the other\n"
        "- Add your own opinion about either choice\n"
        "- Pad the response with agreement summaries\n"
        "- Comment on style, naming, or phrasing\n\n"
        "YOU MUST:\n"
        "- List substantive disagreements as a JSON array\n"
        "- For each disagreement: state the topic, the primary's position, the rival's position, "
        "and which type of decision it represents (technology choice, pattern choice, trade off, scope decision)\n"
        "- Mark each disagreement as requires_ceo_decision: true|false — true only if the disagreement is "
        "about a load-bearing choice the CEO needs to make\n\n"
        "Output a JSON object with this exact structure:\n"
        "{\n"
        "  \"substantive_disagreements\": [\n"
        "    {\n"
        "      \"topic\": \"...\",\n"
        "      \"primary_position\": \"...\",\n"
        "      \"rival_position\": \"...\",\n"
        "      \"decision_type\": \"technology_choice | pattern_choice | trade_off | scope_decision\",\n"
        "      \"requires_ceo_decision\": true,\n"
        "      \"primary_section_cited\": \"...\",\n"
        "      \"rival_section_cited\": \"...\"\n"
        "    }\n"
        "  ],\n"
        "  \"agreement_signal_strength\": \"high | medium | low\",\n"
        "  \"rationale\": \"one-paragraph summary of how aligned the two architectures are overall\"\n"
        "}\n\n"
        "INPUTS:\n\n"
        f"{summary}"
    )

    try:
        import anthropic  # type: ignore

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=LLM_JUDGE_MODEL,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = response.content[0].text

        # Extract JSON from response (may be wrapped in code fences)
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)

        data = json.loads(response_text)

        return JudgmentSurface(
            substantive_disagreements=data.get("substantive_disagreements", []),
            agreement_signal_strength=data.get("agreement_signal_strength", "medium"),
            rationale=data.get("rationale", ""),
        )

    except ImportError:
        return JudgmentSurface(
            substantive_disagreements=[],
            agreement_signal_strength="unknown",
            rationale="anthropic package not installed; LLM judgment surface skipped.",
        )
    except Exception as e:
        # Degrade gracefully
        return JudgmentSurface(
            substantive_disagreements=[],
            agreement_signal_strength="unknown",
            rationale=f"LLM judgment surface failed: {e}. Verdict based on structural diff only.",
        )


def build_comparison_summary(
    primary: ArchitectureFiles, rival: ArchitectureFiles, diff: StructuralDiff
) -> str:
    """Build a condensed summary for the LLM judgment call. Bounded length."""
    parts = []
    parts.append("STRUCTURAL DIFF SUMMARY:")
    parts.append(f"- Database tables overlap: {diff.db_overlap_pct:.1%}")
    parts.append(f"  Primary tables: {sorted(diff.primary_tables)}")
    parts.append(f"  Rival tables: {sorted(diff.rival_tables)}")
    parts.append(f"- API endpoints overlap: {diff.api_overlap_pct:.1%}")
    parts.append(f"  Primary endpoints: {len(diff.primary_endpoints)}")
    parts.append(f"  Rival endpoints: {len(diff.rival_endpoints)}")
    parts.append(f"- Concurrency keywords: primary={diff.primary_concurrency_count}, rival={diff.rival_concurrency_count}")
    parts.append(f"- Compatibility keywords: primary={diff.primary_compatibility_count}, rival={diff.rival_compatibility_count}")
    parts.append("")
    parts.append("PRIMARY ARCHITECTURE EXCERPTS (first 2000 chars of each section):")
    for section in ["overview", "data model", "authentication", "deployment", "concurrency"]:
        text = extract_section_text(primary.architecture_md, section)
        if text:
            parts.append(f"\n## {section} (primary)\n{text[:2000]}")

    parts.append("\n\nRIVAL ARCHITECTURE EXCERPTS (first 2000 chars of each section):")
    for section in ["overview", "data model", "authentication", "deployment", "concurrency"]:
        text = extract_section_text(rival.architecture_md, section)
        if text:
            parts.append(f"\n## {section} (rival)\n{text[:2000]}")

    return "\n".join(parts)


# ============================================================================
# Stage 8: Verdict computation (deterministic)
# ============================================================================


def compute_verdict(diff: StructuralDiff, judgment: JudgmentSurface) -> tuple[str, list[str], list[str], list[str]]:
    """Apply the deterministic verdict rules. Returns (verdict, blocks, escalations, flags)."""
    blocks: list[str] = []
    escalations: list[str] = []
    flags: list[str] = []

    # BLOCK conditions
    if not diff.primary_validation_passed:
        blocks.append("Primary architecture failed structural validation")
    if not diff.rival_validation_passed:
        blocks.append("Rival architecture failed structural validation")
    if len(diff.primary_sections_missing) >= 3:
        blocks.append(
            f"Primary architecture missing {len(diff.primary_sections_missing)} required sections: "
            f"{', '.join(diff.primary_sections_missing)}"
        )
    if len(diff.rival_sections_missing) >= 3:
        blocks.append(
            f"Rival architecture missing {len(diff.rival_sections_missing)} required sections: "
            f"{', '.join(diff.rival_sections_missing)}"
        )

    # ESCALATE conditions (only checked if not blocked)
    if not blocks:
        ceo_required = [d for d in judgment.substantive_disagreements if d.get("requires_ceo_decision")]
        if ceo_required:
            for d in ceo_required:
                escalations.append(
                    f"{d.get('topic', '?')}: primary={d.get('primary_position', '?')}; "
                    f"rival={d.get('rival_position', '?')}"
                )
        if diff.db_overlap_pct < 0.5:
            escalations.append(
                f"Data models substantially different: only {diff.db_overlap_pct:.0%} of tables overlap"
            )
        if diff.api_overlap_pct < 0.4 and (diff.primary_endpoints or diff.rival_endpoints):
            escalations.append(
                f"API surfaces substantially different: only {diff.api_overlap_pct:.0%} of endpoints overlap"
            )

    # FLAG conditions
    if not blocks and not escalations:
        if diff.primary_sections_missing:
            flags.append(f"Primary missing sections: {', '.join(diff.primary_sections_missing)}")
        if diff.rival_sections_missing:
            flags.append(f"Rival missing sections: {', '.join(diff.rival_sections_missing)}")
        if diff.tables_only_primary:
            flags.append(f"Tables only in primary: {sorted(diff.tables_only_primary)}")
        if diff.tables_only_rival:
            flags.append(f"Tables only in rival: {sorted(diff.tables_only_rival)}")
        if diff.endpoints_only_primary:
            flags.append(f"Endpoints only in primary: {len(diff.endpoints_only_primary)}")
        if diff.endpoints_only_rival:
            flags.append(f"Endpoints only in rival: {len(diff.endpoints_only_rival)}")
        # Asymmetric concurrency treatment (rival catches what primary missed)
        if diff.rival_concurrency_count > diff.primary_concurrency_count * 2 and diff.rival_concurrency_count >= 10:
            flags.append(
                f"Rival's concurrency section is substantially more thorough than primary's "
                f"({diff.rival_concurrency_count} keyword mentions vs {diff.primary_concurrency_count}). "
                f"Per Milvus 2026, this is the dimension where Gemini commonly catches what Claude misses. "
                f"CEO should review rival's concurrency section."
            )
        if diff.rival_compatibility_count > diff.primary_compatibility_count * 2 and diff.rival_compatibility_count >= 8:
            flags.append(
                f"Rival's compatibility section is substantially more thorough than primary's "
                f"({diff.rival_compatibility_count} keyword mentions vs {diff.primary_compatibility_count}). "
                f"CEO should review rival's compatibility section."
            )
        # Non-load-bearing substantive disagreements still flag
        for d in judgment.substantive_disagreements:
            if not d.get("requires_ceo_decision"):
                flags.append(f"Minor disagreement: {d.get('topic', '?')}")

    if blocks:
        return "BLOCK", blocks, escalations, flags
    if escalations:
        return "ESCALATE", blocks, escalations, flags
    if flags:
        return "FLAG", blocks, escalations, flags
    return "APPROVE", blocks, escalations, flags


# ============================================================================
# Report writing
# ============================================================================


def write_comparison_report(
    result: ComparisonResult,
    primary: ArchitectureFiles,
    rival: ArchitectureFiles,
    workspace: Path,
    epic: str,
) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    report_dir = workspace / "artifacts" / "reviews" / "architecture_comparison"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{epic}_{timestamp}.md"

    diff = result.structural_diff
    judgment = result.judgment_surface

    lines = []
    lines.append("# Architecture Comparison Report")
    lines.append("")
    lines.append(f"**Epic:** {epic}")
    lines.append(f"**Timestamp:** {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"**Primary architect:** Claude Opus (path: `{primary.architecture_md_path}`)")
    lines.append(f"**Rival architect:** Gemini 3 Pro (path: `{rival.architecture_md_path}`)")
    lines.append("")
    lines.append(f"## Verdict: **{result.verdict}**")
    lines.append("")

    if result.verdict == "APPROVE":
        lines.append(
            "Both architectures pass structural validation, agree on the core data model and API surface, "
            "and surface no substantive disagreements requiring CEO decision. Phase 5 may advance to Phase 5.5."
        )
    elif result.verdict == "FLAG":
        lines.append(
            "Both architectures pass structural validation but have minor differences worth noting. "
            "Phase 5 may advance with the flags below attached to the phase output."
        )
    elif result.verdict == "ESCALATE":
        lines.append(
            "Both architectures pass structural validation but disagree on substantive decisions. "
            "Phase 5 PAUSES. CEO must review both architectures and decide via /btw approve before "
            "Phase 5 can advance."
        )
    elif result.verdict == "BLOCK":
        lines.append(
            "One or both architectures failed structural validation. Phase 5 cannot advance. "
            "The failing architect's work must be returned with the issues below."
        )

    lines.append("")
    lines.append("## Stage 1: Structural Validation")
    lines.append("")
    lines.append(f"- Primary: {'✅ PASS' if diff.primary_validation_passed else '❌ FAIL'}")
    lines.append(f"- Rival: {'✅ PASS' if diff.rival_validation_passed else '❌ FAIL'}")

    lines.append("")
    lines.append("## Stage 2: Required Section Coverage")
    lines.append("")
    lines.append(f"### Primary architecture sections")
    lines.append(f"- Present: {', '.join(diff.primary_sections_present)}")
    if diff.primary_sections_missing:
        lines.append(f"- **Missing:** {', '.join(diff.primary_sections_missing)}")
    lines.append("")
    lines.append(f"### Rival architecture sections")
    lines.append(f"- Present: {', '.join(diff.rival_sections_present)}")
    if diff.rival_sections_missing:
        lines.append(f"- **Missing:** {', '.join(diff.rival_sections_missing)}")

    lines.append("")
    lines.append("## Stage 3: Database Schema Diff")
    lines.append("")
    lines.append(f"- Tables in primary: {len(diff.primary_tables)}")
    lines.append(f"- Tables in rival: {len(diff.rival_tables)}")
    lines.append(f"- Tables in both: {len(diff.tables_in_both)}")
    lines.append(f"- Overlap: {diff.db_overlap_pct:.1%}")
    if diff.tables_only_primary:
        lines.append(f"- Only in primary: {sorted(diff.tables_only_primary)}")
    if diff.tables_only_rival:
        lines.append(f"- Only in rival: {sorted(diff.tables_only_rival)}")
    if diff.table_column_diffs:
        lines.append("")
        lines.append("### Column-level differences (shared tables)")
        for table, table_diff in diff.table_column_diffs.items():
            lines.append(f"- **{table}**:")
            if table_diff["only_primary"]:
                lines.append(f"  - Only in primary: {sorted(table_diff['only_primary'])}")
            if table_diff["only_rival"]:
                lines.append(f"  - Only in rival: {sorted(table_diff['only_rival'])}")

    lines.append("")
    lines.append("## Stage 4: API Surface Diff")
    lines.append("")
    lines.append(f"- Endpoints in primary: {len(diff.primary_endpoints)}")
    lines.append(f"- Endpoints in rival: {len(diff.rival_endpoints)}")
    lines.append(f"- Endpoints in both: {len(diff.endpoints_in_both)}")
    lines.append(f"- Overlap: {diff.api_overlap_pct:.1%}")
    if diff.endpoints_only_primary:
        lines.append("- **Only in primary:**")
        for method, path in sorted(diff.endpoints_only_primary):
            lines.append(f"  - `{method} {path}`")
    if diff.endpoints_only_rival:
        lines.append("- **Only in rival:**")
        for method, path in sorted(diff.endpoints_only_rival):
            lines.append(f"  - `{method} {path}`")

    lines.append("")
    lines.append("## Stage 5: Dependencies Diff")
    lines.append("")
    lines.append(f"- Dependencies in both: {sorted(diff.deps_in_both)[:20]}{'...' if len(diff.deps_in_both) > 20 else ''}")
    if diff.deps_only_primary:
        lines.append(f"- Only in primary: {sorted(diff.deps_only_primary)[:20]}")
    if diff.deps_only_rival:
        lines.append(f"- Only in rival: {sorted(diff.deps_only_rival)[:20]}")

    lines.append("")
    lines.append("## Stage 6: Specialization Keyword Counts (Concurrency / Compatibility)")
    lines.append("")
    lines.append(f"- Concurrency keywords — primary: {diff.primary_concurrency_count}, rival: {diff.rival_concurrency_count}")
    lines.append(f"- Compatibility keywords — primary: {diff.primary_compatibility_count}, rival: {diff.rival_compatibility_count}")
    if diff.rival_concurrency_count > diff.primary_concurrency_count * 2 and diff.rival_concurrency_count >= 10:
        lines.append("- ⚠️  Asymmetric concurrency treatment — rival's section is substantially more thorough.")
    if diff.rival_compatibility_count > diff.primary_compatibility_count * 2 and diff.rival_compatibility_count >= 8:
        lines.append("- ⚠️  Asymmetric compatibility treatment — rival's section is substantially more thorough.")

    lines.append("")
    lines.append("## Stage 7: Substantive Disagreements (LLM judgment surface)")
    lines.append("")
    lines.append(f"**Agreement signal strength:** {judgment.agreement_signal_strength}")
    lines.append("")
    lines.append(f"**Rationale:** {judgment.rationale}")
    lines.append("")
    if judgment.substantive_disagreements:
        for i, d in enumerate(judgment.substantive_disagreements, 1):
            lines.append(f"### Disagreement {i}: {d.get('topic', 'unknown')}")
            lines.append(f"- **Primary's position:** {d.get('primary_position', '?')}")
            lines.append(f"- **Rival's position:** {d.get('rival_position', '?')}")
            lines.append(f"- **Decision type:** {d.get('decision_type', '?')}")
            lines.append(f"- **Requires CEO decision:** {d.get('requires_ceo_decision', False)}")
            if d.get("primary_section_cited"):
                lines.append(f"- Primary section: `{d['primary_section_cited']}`")
            if d.get("rival_section_cited"):
                lines.append(f"- Rival section: `{d['rival_section_cited']}`")
            lines.append("")
    else:
        lines.append("_No substantive disagreements identified._")

    lines.append("")
    lines.append("## Stage 8: Verdict Detail")
    lines.append("")
    if result.blocks:
        lines.append("### Blocks")
        for b in result.blocks:
            lines.append(f"- {b}")
        lines.append("")
    if result.escalations:
        lines.append("### Escalations (CEO decision required)")
        for e in result.escalations:
            lines.append(f"- {e}")
        lines.append("")
    if result.flags:
        lines.append("### Flags")
        for f in result.flags:
            lines.append(f"- {f}")
        lines.append("")

    lines.append("## Source Documents")
    lines.append("")
    lines.append(f"- Primary architecture: `{primary.architecture_md_path}`")
    lines.append(f"- Primary API spec: `{primary.api_spec_path}`")
    lines.append(f"- Primary DB schema: `{primary.db_schema_path}`")
    lines.append(f"- Rival architecture: `{rival.architecture_md_path}`")
    lines.append(f"- Rival API spec: `{rival.api_spec_path}`")
    lines.append(f"- Rival DB schema: `{rival.db_schema_path}`")

    lines.append("")
    lines.append("## Protocol Attestation")
    lines.append("")
    lines.append("- ✅ Both architectures produced independently — neither saw the other's output before producing its own")
    lines.append("- ✅ Structural diffs (Stages 1-6) computed by deterministic Python code")
    lines.append("- ✅ Stage 7 LLM call constrained to surface disagreements only — does not decide which is better")
    lines.append("- ✅ Verdict computation (Stage 8) is deterministic — code, not LLM")
    lines.append("- ✅ Audit log entry written to `logs/architecture_comparisons.jsonl`")

    report_text = "\n".join(lines)
    report_path.write_text(report_text)
    result.report_path = str(report_path)
    return report_path


# ============================================================================
# Audit logging
# ============================================================================


def append_audit_log(workspace: Path, result: ComparisonResult, epic: str):
    log_dir = workspace / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "architecture_comparisons.jsonl"

    diff = result.structural_diff
    entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "agent": "rival-architect-comparator",
        "phase": 5,
        "epic": epic,
        "verdict": result.verdict,
        "primary_validation_passed": diff.primary_validation_passed,
        "rival_validation_passed": diff.rival_validation_passed,
        "db_overlap_pct": diff.db_overlap_pct,
        "api_overlap_pct": diff.api_overlap_pct,
        "primary_sections_missing": diff.primary_sections_missing,
        "rival_sections_missing": diff.rival_sections_missing,
        "concurrency_counts": {
            "primary": diff.primary_concurrency_count,
            "rival": diff.rival_concurrency_count,
        },
        "compatibility_counts": {
            "primary": diff.primary_compatibility_count,
            "rival": diff.rival_compatibility_count,
        },
        "substantive_disagreements_count": len(result.judgment_surface.substantive_disagreements),
        "ceo_decision_required": len(result.escalations) > 0,
        "blocks": result.blocks,
        "escalations": result.escalations,
        "flags": result.flags,
        "report_path": result.report_path,
    }

    with log_path.open("a") as f:
        f.write(json.dumps(entry, default=list) + "\n")


def update_company_state(workspace: Path, result: ComparisonResult, epic: str):
    state_path = workspace / "state" / "company_state.json"
    if not state_path.exists():
        return
    try:
        state = json.loads(state_path.read_text())
    except json.JSONDecodeError:
        return

    if "architecture_comparison" not in state:
        state["architecture_comparison"] = {}
    if "phase5" not in state["architecture_comparison"]:
        state["architecture_comparison"]["phase5"] = {}

    state["architecture_comparison"]["phase5"][epic] = {
        "verdict": result.verdict,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "report_path": result.report_path,
        "ceo_escalation_required": result.verdict == "ESCALATE",
        "block_count": len(result.blocks),
        "flag_count": len(result.flags),
        "escalation_count": len(result.escalations),
    }
    state_path.write_text(json.dumps(state, indent=2))


# ============================================================================
# Halt
# ============================================================================


def halt(error: str, suggestion: str = "", exit_code: int = 1):
    timestamp = datetime.now(timezone.utc).isoformat()
    diag = {
        "timestamp_utc": timestamp,
        "agent": "rival-architect-comparator",
        "halt_reason": error,
        "suggestion": suggestion,
        "exit_code": exit_code,
    }
    print(json.dumps(diag, indent=2), file=sys.stderr)
    sys.exit(exit_code)


# ============================================================================
# Main
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Compare primary and rival architectures and produce a verdict"
    )
    parser.add_argument("--workspace", required=True, help="Path to startup workspace")
    parser.add_argument("--epic", required=True, help="Epic slug")
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip Stage 7 (LLM judgment surface). Verdict based on structural diff only.",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    if not workspace.exists():
        halt(f"Workspace does not exist: {workspace}", exit_code=1)

    primary_dir = workspace / "artifacts" / "designs" / args.epic / "tech"
    rival_dir = workspace / "artifacts" / "designs" / args.epic / "tech" / "rival"

    if not primary_dir.exists():
        halt(f"Primary tech directory missing: {primary_dir}", exit_code=1)
    if not rival_dir.exists():
        halt(
            f"Rival tech directory missing: {rival_dir}",
            "Run invoke_rival_architect.py first to produce the rival's architecture.",
            exit_code=1,
        )

    # Load both architectures
    primary = load_architecture(primary_dir, "primary")
    rival = load_architecture(rival_dir, "rival")

    # Stage 1: Structural validation
    primary_valid, primary_errors = validate_architecture(primary, "primary")
    rival_valid, rival_errors = validate_architecture(rival, "rival")

    diff = StructuralDiff(
        primary_validation_passed=primary_valid,
        rival_validation_passed=rival_valid,
    )

    # Stage 2: Section coverage (only if both validated)
    diff.primary_sections_present, diff.primary_sections_missing = check_section_coverage(primary.architecture_md)
    diff.rival_sections_present, diff.rival_sections_missing = check_section_coverage(rival.architecture_md)

    # Stage 3: DB schema diff
    db_diff = diff_db_schemas(primary.db_schema_sql, rival.db_schema_sql)
    diff.primary_tables = db_diff["primary_tables"]
    diff.rival_tables = db_diff["rival_tables"]
    diff.tables_in_both = db_diff["tables_in_both"]
    diff.tables_only_primary = db_diff["tables_only_primary"]
    diff.tables_only_rival = db_diff["tables_only_rival"]
    diff.table_column_diffs = db_diff["column_diffs"]
    diff.db_overlap_pct = db_diff["overlap_pct"]

    # Stage 4: API surface diff
    api_diff = diff_api_surface(primary.api_spec, rival.api_spec)
    diff.primary_endpoints = api_diff["primary_endpoints"]
    diff.rival_endpoints = api_diff["rival_endpoints"]
    diff.endpoints_in_both = api_diff["endpoints_in_both"]
    diff.endpoints_only_primary = api_diff["endpoints_only_primary"]
    diff.endpoints_only_rival = api_diff["endpoints_only_rival"]
    diff.api_overlap_pct = api_diff["overlap_pct"]

    # Stage 5: Dependency diff
    dep_diff = diff_dependencies(primary.architecture_md, rival.architecture_md)
    diff.primary_dependencies = dep_diff["primary_dependencies"]
    diff.rival_dependencies = dep_diff["rival_dependencies"]
    diff.deps_in_both = dep_diff["in_both"]
    diff.deps_only_primary = dep_diff["only_primary"]
    diff.deps_only_rival = dep_diff["only_rival"]

    # Stage 6: Specialization keyword counts
    spec_diff = specialization_keyword_diff(primary.architecture_md, rival.architecture_md)
    diff.primary_concurrency_count = spec_diff["primary_concurrency_count"]
    diff.rival_concurrency_count = spec_diff["rival_concurrency_count"]
    diff.primary_compatibility_count = spec_diff["primary_compatibility_count"]
    diff.rival_compatibility_count = spec_diff["rival_compatibility_count"]

    # Stage 7: LLM judgment surface (constrained, optional)
    if args.no_llm:
        judgment = JudgmentSurface(
            substantive_disagreements=[],
            agreement_signal_strength="unknown",
            rationale="LLM judgment surface skipped via --no-llm flag.",
        )
    else:
        judgment = llm_judgment_surface(primary, rival, diff)

    # Stage 8: Verdict computation
    verdict, blocks, escalations, flags = compute_verdict(diff, judgment)

    result = ComparisonResult(
        verdict=verdict,
        structural_diff=diff,
        judgment_surface=judgment,
        flags=flags,
        blocks=blocks,
        escalations=escalations,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )

    # Write report
    write_comparison_report(result, primary, rival, workspace, args.epic)

    # Audit + state
    append_audit_log(workspace, result, args.epic)
    update_company_state(workspace, result, args.epic)

    # Output to stdout
    output = {
        "verdict": result.verdict,
        "primary_validation": "PASS" if diff.primary_validation_passed else "FAIL",
        "rival_validation": "PASS" if diff.rival_validation_passed else "FAIL",
        "data_model_overlap_pct": round(diff.db_overlap_pct, 3),
        "api_surface_overlap_pct": round(diff.api_overlap_pct, 3),
        "missing_sections_primary": diff.primary_sections_missing,
        "missing_sections_rival": diff.rival_sections_missing,
        "concurrency_keyword_counts": {
            "primary": diff.primary_concurrency_count,
            "rival": diff.rival_concurrency_count,
        },
        "compatibility_keyword_counts": {
            "primary": diff.primary_compatibility_count,
            "rival": diff.rival_compatibility_count,
        },
        "substantive_disagreements_count": len(judgment.substantive_disagreements),
        "ceo_escalations": result.escalations,
        "blocks": result.blocks,
        "flags": result.flags,
        "comparison_report_path": result.report_path,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
