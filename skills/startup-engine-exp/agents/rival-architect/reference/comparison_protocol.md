# Architecture Comparison Protocol

This document defines the rules `scripts/compare_architectures.py` follows to compare two independently-produced architectures and produce a verdict. The protocol is designed so that as much of the comparison as possible is **deterministic Python code** (testable, reproducible, no LLM bias) and only the genuinely judgment-based comparison uses an LLM call (constrained to "surface differences, not decide").

---

## Inputs

The compare script reads exactly six files from fixed paths:

| File | Source | Path |
|---|---|---|
| Primary architecture | Claude VP Engineering | `{workspace}/artifacts/designs/{epic}/tech/architecture.md` |
| Primary API spec | Claude VP Engineering | `{workspace}/artifacts/designs/{epic}/tech/api_spec.json` |
| Primary DB schema | Claude VP Engineering | `{workspace}/artifacts/designs/{epic}/tech/db_schema.sql` |
| Rival architecture | Gemini 3 Pro | `{workspace}/artifacts/designs/{epic}/tech/rival/architecture.md` |
| Rival API spec | Gemini 3 Pro | `{workspace}/artifacts/designs/{epic}/tech/rival/api_spec.json` |
| Rival DB schema | Gemini 3 Pro | `{workspace}/artifacts/designs/{epic}/tech/rival/db_schema.sql` |

If any of the six is missing, the compare script halts with `MISSING_INPUT` and the COO escalates.

---

## Comparison Stages

### Stage 1: Structural Validation (deterministic)

Each of the six files must independently pass structural validation:

- `architecture.md` files must contain all eleven canonical sections from `architecture_schema.md`
- `api_spec.json` files must be valid JSON and parse into a recognizable API spec structure (endpoints array or paths object)
- `db_schema.sql` files must parse for CREATE TABLE statements (regex-based — does not require a full SQL parser)

**Verdict impact:**
- If the primary fails validation → BLOCK (return to VP Engineering)
- If the rival fails validation → BLOCK (rival production failed; either retry or escalate to CEO)
- If both pass → continue

### Stage 2: Required Section Coverage (deterministic)

For each architecture's `architecture.md`, parse markdown level-2 headings and map them to canonical sections (case-insensitive, fuzzy match for common variations):

| Canonical section | Match patterns |
|---|---|
| Overview | "overview", "summary", "introduction" |
| Data Model | "data model", "schema", "entities", "data architecture" |
| API Surface | "api", "api surface", "endpoints", "interface" |
| Authentication | "auth", "authentication", "user auth", "identity" |
| Authorization | "authz", "authorization", "permissions", "access control" |
| Deployment | "deployment", "infrastructure", "hosting", "production" |
| Observability | "observability", "monitoring", "logging", "metrics" |
| Concurrency | "concurrency", "concurrent", "race", "locking", "queueing" |
| Error Handling | "error handling", "errors", "failure", "recovery" |
| Dependencies | "dependencies", "libraries", "packages", "third-party" |
| Compatibility | "compatibility", "support", "versions" |

For each architecture, record:
- Which canonical sections are present
- Which are missing
- Word count of each section

**Verdict impact:**
- If either architecture is missing 3 or more required sections → BLOCK (architecture is incomplete)
- If either is missing 1-2 sections → FLAG (note in comparison report, but allow advance)
- If the Concurrency or Compatibility section has fewer than 100 words → FLAG (specialization treatment is shallow)

### Stage 3: Database Schema Diff (deterministic)

Parse both `db_schema.sql` files using regex to extract:

```python
CREATE_TABLE_PATTERN = re.compile(
    r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["`]?(\w+)["`]?\s*\((.*?)\);',
    re.IGNORECASE | re.DOTALL,
)
```

For each architecture, build a set of (table_name, [column_names]). Then compute:

- **Tables in both**: intersection of table names (compare column sets within each)
- **Tables only in primary**: in primary, not in rival
- **Tables only in rival**: in rival, not in primary
- **Column-level diffs for shared tables**: which columns are in both, which are only in one

**Verdict impact:**
- Tables in both with identical or near-identical columns → strong agreement signal (no flag)
- Tables in both with substantially different columns → FLAG (different data shape for same entity)
- Tables only in one architecture → FLAG (one architect modeled an entity the other didn't)
- More than 50% of tables differ → ESCALATE (data models are fundamentally different)

### Stage 4: API Surface Diff (deterministic)

Parse both `api_spec.json` files. Try multiple structures (paths object like OpenAPI, endpoints array, or top-level keys):

```python
def extract_endpoints(spec: dict) -> set[tuple[str, str]]:
    """Returns set of (method, path) tuples."""
    endpoints = set()
    if "paths" in spec:  # OpenAPI-style
        for path, methods in spec["paths"].items():
            for method in methods:
                if method.upper() in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                    endpoints.add((method.upper(), path))
    elif "endpoints" in spec:  # Custom array style
        for ep in spec["endpoints"]:
            endpoints.add((ep["method"].upper(), ep["path"]))
    return endpoints
```

Compute:
- Endpoints in both
- Endpoints only in primary
- Endpoints only in rival
- Same path with different methods (e.g., one says PATCH /users/:id, other says PUT /users/:id)

**Verdict impact:**
- Endpoints overlapping >70% with no method conflicts → agreement signal
- Endpoints overlapping <40% → ESCALATE (different API design)
- Method conflicts on shared paths → FLAG (RESTful conventions disagreement)
- More than 30% of endpoints unique to one side → FLAG

### Stage 5: Dependency Diff (deterministic)

Regex-extract dependency mentions from both architecture.md files:

```python
DEPENDENCY_PATTERNS = [
    re.compile(r'`([a-zA-Z0-9\-@/]+)@?([0-9.]+)?`'),  # npm-style
    re.compile(r'pip install ([a-zA-Z0-9\-_]+)'),
    re.compile(r'npm install ([a-zA-Z0-9\-@/]+)'),
    re.compile(r'from ([a-zA-Z0-9_.]+) import'),
    re.compile(r'import ([a-zA-Z0-9_.]+)'),
]
```

Build a set of dependencies from each. Compute intersection and differences. Note: this is a heuristic — it will produce some false positives (a code snippet showing an unrelated import) and some false negatives (a dependency mentioned in prose without any code-style marker). The signal is directional, not exact.

**Verdict impact:**
- Most dependencies in common → agreement signal
- A specific high-stakes dependency only in one architecture (database driver, auth library, payment SDK) → FLAG
- Two architectures with completely different dependency sets → ESCALATE (different technology stacks chosen)

### Stage 6: Concurrency / Compatibility Keyword Asymmetry (deterministic)

Per the Milvus 2026 finding that Gemini catches concurrency and compatibility issues Claude misses, count keyword mentions in each architecture's relevant sections:

```python
CONCURRENCY_KEYWORDS = [
    "concurrent", "concurrency", "race condition", "race", "lock", "locking",
    "rate limit", "rate-limit", "throttle", "queue", "queueing", "ordering",
    "idempotent", "idempotency", "deadlock", "atomicity", "consistency",
    "eventual consistency", "strong consistency", "cas", "compare-and-swap",
    "optimistic locking", "pessimistic locking", "advisory lock", "distributed lock",
]

COMPATIBILITY_KEYWORDS = [
    "version", "compatible", "compatibility", "deprecated", "breaking change",
    "migration", "polyfill", "browser support", "node version", "python version",
    "runtime version", "EOL", "end of life", "supported version", "lts",
]
```

For each architecture, count total mentions in the Concurrency and Compatibility sections specifically.

**Verdict impact:**
- Both architectures have substantive concurrency sections (>10 keyword mentions) → agreement signal
- Asymmetric — rival has substantive section, primary has shallow → FLAG ("rival caught concurrency considerations the primary may have missed")
- Asymmetric in the other direction → FLAG (informational)
- Both architectures have shallow concurrency sections → BLOCK (the protocol requires both to address concurrency substantively)

This is the place where the rival's specialization is most likely to add value. The Milvus data shows this is exactly where Claude's blind spots live.

### Stage 7: Constrained LLM Judgment Surface (one bounded LLM call)

After all deterministic stages complete, the compare script makes a single LLM call to surface judgment-level disagreements that the structural diffs cannot capture. The call uses Claude Opus, but with an explicit constraint prompt:

```
You are a comparison facilitator. You will be given summaries of two independently-produced
technical architectures for the same project. Your job is ONLY to surface substantive
disagreements that the structural diff did not catch — architectural pattern choices,
philosophical decisions, technology selection rationales, trade-off framings.

YOU MUST NOT:
- Decide which architecture is better
- Recommend one over the other
- Add your own opinion about either choice
- Pad the response with agreement summaries
- Comment on style, naming, or phrasing

YOU MUST:
- List substantive disagreements as a JSON array
- For each disagreement: state the topic, the primary's position, the rival's position,
  and which type of decision it represents (technology choice, pattern choice, trade-off,
  scope decision)
- Mark each disagreement as 'requires_ceo_decision: true|false' — true only if the
  disagreement is about a load-bearing choice the CEO needs to make

Output format:
{
  "substantive_disagreements": [
    {
      "topic": "...",
      "primary_position": "...",
      "rival_position": "...",
      "decision_type": "technology_choice | pattern_choice | trade_off | scope_decision",
      "requires_ceo_decision": true,
      "primary_section_cited": "...",
      "rival_section_cited": "..."
    }
  ],
  "agreement_signal_strength": "high | medium | low",
  "rationale": "one-paragraph summary of how aligned the two architectures are overall"
}
```

The input to this LLM call is NOT the full architectures — it is the structural diff summary from stages 1-6 plus excerpts from the relevant sections of both architecture.md files. This keeps the call focused and bounded.

**Verdict impact:**
- 0 substantive disagreements with `requires_ceo_decision: true` → continue to verdict computation
- 1+ substantive disagreements with `requires_ceo_decision: true` → ESCALATE (CEO must decide)

### Stage 8: Verdict Computation (deterministic)

Combine the outputs of stages 1-7 into a final verdict:

```python
def compute_verdict(stage_results):
    if stage_results["primary_validation_failed"] or stage_results["rival_validation_failed"]:
        return "BLOCK"
    if stage_results["missing_sections_count"] >= 3:
        return "BLOCK"
    if stage_results["both_concurrency_shallow"]:
        return "BLOCK"
    if stage_results["substantive_disagreements_requiring_ceo"] > 0:
        return "ESCALATE"
    if stage_results["data_model_substantially_different"]:
        return "ESCALATE"
    if stage_results["api_surface_substantially_different"]:
        return "ESCALATE"
    if stage_results["any_flags_recorded"]:
        return "FLAG"
    return "APPROVE"
```

The verdict is **deterministic code, not LLM judgment**. The LLM call in stage 7 only PRODUCES inputs (the substantive disagreements list); it does not produce the verdict.

---

## Output

The compare script writes a comparison report to:

```
{workspace}/artifacts/reviews/architecture_comparison/{epic}_{YYYYMMDD_HHMMSSZ}.md
```

The report contains all of stages 1-8 with their findings. The format follows the template at `templates/comparison_report.md`.

The script also returns a JSON verdict object to stdout for the COO to read:

```json
{
  "verdict": "APPROVE | FLAG | ESCALATE | BLOCK",
  "primary_validation": "PASS | FAIL",
  "rival_validation": "PASS | FAIL",
  "data_model_overlap_pct": 0.85,
  "api_surface_overlap_pct": 0.78,
  "missing_sections_primary": [],
  "missing_sections_rival": [],
  "concurrency_keyword_counts": {"primary": 23, "rival": 41},
  "compatibility_keyword_counts": {"primary": 12, "rival": 28},
  "substantive_disagreements_count": 0,
  "ceo_escalations": [],
  "comparison_report_path": "..."
}
```

---

## Why This Protocol Avoids Bias

The structural diff (stages 1-6) is pure code — there is no LLM, no model bias, no judgment. Two architectures with the same tables and the same endpoints get identical structural agreement signals regardless of which model produced them.

The LLM judgment surface (stage 7) is the only place an LLM is involved, and it is constrained:

1. The prompt forbids "which is better" — explicitly
2. The output schema does not have a "winner" field
3. The LLM only LISTS disagreements; the verdict computation in stage 8 reads the list and applies code rules
4. The LLM call uses Claude (the same family as the primary), which would create self-enhancement bias if it were judging which architecture is better — but it isn't. It's only surfacing structured disagreements.

If self-enhancement bias is still a concern in practice, the long-term mitigation is to move stage 7 to a third-party LLM (GPT-5 or local) so that no model judges its own family. For Tier 2, the constraint approach is sufficient.

---

## What This Protocol Does NOT Do

1. **It does not run a build.** The architectures are evaluated as documents, not as buildable systems. Phase 6 (Development) is where buildability is tested.

2. **It does not evaluate code quality.** Code review is a separate skill (`multi-agent-review`).

3. **It does not optimize for cost.** The comparison may surface that one architecture is more expensive than the other — that's a flag for the CEO, not an auto-decision.

4. **It does not score the architectures.** No 1-10 ratings, no winner declarations. The verdict is APPROVE/FLAG/ESCALATE/BLOCK and that's all.

5. **It does not resolve disagreements.** Resolution is the CEO's job. The compare script's job is to surface, not decide.
