# Skills Registry

Living catalog of all skills in the pm-skills repository. Updated as skills are created, modified, or retired.

**Last audit:** 2026-04-09 UTC

---

## Skill Inventory

| Skill | Maturity | Lines | Structure | Description Quality | Key Gap |
|-------|----------|-------|-----------|-------------------|---------|
| [deep-research](#deep-research) | Production | 103 | Full (ref, scripts, templates, tests) | 5/5 | None — gold standard |
| [startup-engine](#startup-engine) | Production | 706 | Full (ref, scripts, templates) | 4/5 | SKILL.md over 500 lines |
| [product-pipeline](#product-pipeline) | Production | 168 | Good (ref, scripts, templates) | 4/5 | No negative boundaries in description |
| [sprint-retro](#sprint-retro) | Production | 279 | Partial (ref only) | 4/5 | No scripts or validation |
| [cross-system-search](#cross-system-search) | Production | 362 | Partial (ref only) | 3/5 | No trigger keywords, no scripts |
| [proof-of-change](#proof-of-change) | Production | 353 | Partial (ref only) | 3/5 | No scripts despite validation focus |
| [therapy-web-design](#therapy-web-design) | Production | 270 | Partial (ref only) | 2/5 | No frontmatter, no triggers, no scripts |
| [startup-engine-exp](#startup-engine-exp) | Experimental | 706 | Full (ref, scripts, templates) | 4/5 | Duplicate of production — needs diff tracking |

---

## Detailed Assessments

### deep-research
**Status:** Production — Gold Standard  
**Invoke:** `/deep-research`  
**Description quality:** 5/5 — Includes trigger keywords ("deep research", "comprehensive analysis", "compare X vs Y"), negative boundary ("Not for simple lookups, debugging"), and specific output description.  
**Structure:** Exemplary. SKILL.md is 103 lines (routing hub). 8 scripts including `verify_citations.py`. Templates for report output. Tests directory. Reference files for methodology.  
**Progressive disclosure:** Yes — SKILL.md references external files for detail.  
**Output contract:** Defined — McKinsey-style reports with executive summary, findings, citations.  
**Self-validation:** `verify_citations.py` and other scripts.  
**Improvement backlog:** None critical. Consider adding numeric quality rubric.

### startup-engine
**Status:** Production  
**Invoke:** `/startup-engine`  
**Description quality:** 4/5 — Good trigger keywords, describes phases and agent structure. Missing negative boundaries.  
**Structure:** Full directory with reference/, scripts/, templates/. 6 scripts.  
**Progressive disclosure:** Yes — phase prompts in `reference/phase_prompts/`.  
**Output contract:** Strong — defines deliverables per phase.  
**Self-validation:** 40 validation mentions. Quality gates built into SDLC protocol.  
**Error handling:** 27 mentions — best in the library.  
**Anti-simulation:** Has guards against hand-waving.  
**Improvement backlog:**
- [ ] SKILL.md is 706 lines — extract more to reference files to get under 500
- [ ] Add negative boundaries to description ("Not for simple scripts, one-off tasks")

### product-pipeline
**Status:** Production  
**Invoke:** `/product-pipeline`  
**Description quality:** 4/5 — Good trigger keywords ("product pipeline", "idea to epic", "full product spec"). Missing negative boundaries.  
**Structure:** Good — reference/, scripts/, templates/.  
**Progressive disclosure:** Strong — 11 references to external files.  
**Output contract:** Strong — 18 output mentions. Defines epics, stories, design system spec, technical architecture.  
**Self-validation:** 12 validation mentions. Quality gates in orchestration protocol.  
**Improvement backlog:**
- [ ] Add negative boundaries ("Not for bug fixes, technical tasks without product context")
- [ ] Add test scenarios

### sprint-retro
**Status:** Production  
**Invoke:** `/sprint-retro`  
**Description quality:** 4/5 — Excellent trigger keywords ("retro", "retrospective", "post-mortem", "what went wrong"). No negative boundaries.  
**Structure:** Partial — reference/ only. No scripts or templates.  
**Output contract:** Good — 11 output mentions defining report structure.  
**Self-validation:** Minimal — 4 mentions.  
**Improvement backlog:**
- [ ] Add scripts for automated SpecStory parsing
- [ ] Add negative boundaries ("Not for code review, debugging, or feature planning")
- [ ] Add output templates

### cross-system-search
**Status:** Production  
**Invoke:** `/cross-system-search`  
**Description quality:** 3/5 — Describes capability well but lacks trigger keywords and negative boundaries.  
**Structure:** Partial — reference/ only. No scripts.  
**Output contract:** Weak — 1 mention.  
**Self-validation:** Strong — 17 validation mentions (search exhaustion tracking).  
**Error handling:** Good — 9 mentions.  
**Improvement backlog:**
- [ ] Add trigger keywords ("find entity", "search everywhere", "where is X")
- [ ] Add negative boundaries ("Not for single-system lookups, code search, file search")
- [ ] Define explicit output contract (search report format)
- [ ] Add scripts for result deduplication

### proof-of-change
**Status:** Production  
**Invoke:** `/proof-of-change`  
**Description quality:** 3/5 — Good capability description. Missing trigger keywords and negative boundaries.  
**Structure:** Partial — reference/ only. No scripts despite heavy validation focus (40 mentions).  
**Output contract:** Good — 7 mentions.  
**Anti-simulation:** 3 mentions — explicitly prevents "done" declarations without evidence.  
**Improvement backlog:**
- [ ] Add trigger keywords ("verify change", "prove it worked", "screenshot evidence")
- [ ] Add negative boundaries ("Not for unit testing, code review, or pre-change validation")
- [ ] Extract validation scripts to scripts/ directory
- [ ] Add progressive disclosure — 353 lines with no external file references

### therapy-web-design
**Status:** Production  
**Invoke:** `/therapy-web-design`  
**Description quality:** 2/5 — No YAML frontmatter at all. No trigger keywords. No negative boundaries. Relies entirely on manual invocation or lucky keyword match.  
**Structure:** Partial — reference/ only. No scripts, templates, or examples.  
**Output contract:** Moderate — defines design rules but not specific deliverable formats.  
**Self-validation:** Minimal — 2 mentions.  
**Improvement backlog:**
- [ ] **Critical:** Add YAML frontmatter with name, description, trigger keywords
- [ ] Add trigger keywords ("therapist website", "therapy landing page", "healthcare web design")
- [ ] Add negative boundaries ("Not for non-healthcare websites, backend development")
- [ ] Add output templates (HTML/CSS starter, design token file)
- [ ] Add validation scripts for accessibility, contrast ratios
- [ ] Add example outputs

### startup-engine-exp
**Status:** Experimental  
**Invoke:** `/startup-engine-exp`  
**Description quality:** 4/5 — Same as production.  
**Notes:** Sandbox copy of startup-engine for testing changes before promoting. Should maintain a CHANGELOG tracking divergence from production.  
**Improvement backlog:**
- [ ] Add CHANGELOG.md tracking differences from production
- [ ] Add promote-to-production script

---

## Quality Scoring Rubric

Each skill is scored across 8 dimensions (1-5 scale):

| Dimension | 1 (Poor) | 3 (Adequate) | 5 (Exemplary) |
|-----------|----------|---------------|----------------|
| **Description** | Vague, no triggers | Describes capability | Triggers + negatives + examples |
| **Structure** | SKILL.md only | SKILL.md + reference/ | Full directory (ref, scripts, templates, tests) |
| **Progressive Disclosure** | Everything inline | Some external refs | Hub pattern, all detail in ref files |
| **Output Contract** | Undefined | Describes outputs | Exact sections, formats, word counts |
| **Error Handling** | None | Basic retry/skip | Recoverable vs unrecoverable with protocols |
| **Self-Validation** | None | Manual checks | Automated scripts with quality gates |
| **Anti-Simulation** | None | Some guards | Explicit "write code, don't describe" with enforcement |
| **Documentation** | None | Inline comments | README + examples + test scenarios |

### Current Scores

| Skill | Desc | Structure | Prog. Disc. | Output | Errors | Validation | Anti-Sim | Docs | **Total** |
|-------|------|-----------|-------------|--------|--------|------------|----------|------|-----------|
| deep-research | 5 | 5 | 5 | 4 | 2 | 4 | 2 | 4 | **31/40** |
| startup-engine | 4 | 5 | 4 | 5 | 5 | 5 | 3 | 3 | **34/40** |
| product-pipeline | 4 | 4 | 5 | 5 | 1 | 4 | 1 | 3 | **27/40** |
| sprint-retro | 4 | 2 | 1 | 4 | 3 | 2 | 2 | 2 | **20/40** |
| cross-system-search | 3 | 2 | 1 | 1 | 3 | 4 | 1 | 2 | **17/40** |
| proof-of-change | 3 | 2 | 1 | 3 | 1 | 5 | 3 | 2 | **20/40** |
| therapy-web-design | 2 | 2 | 1 | 3 | 1 | 1 | 2 | 2 | **14/40** |

---

## Skill Development Backlog (Priority Order)

### High Priority
1. **therapy-web-design:** Add frontmatter — currently invisible to auto-activation
2. **All skills:** Add negative boundaries to descriptions
3. **proof-of-change:** Extract scripts, add progressive disclosure

### Medium Priority
4. **startup-engine:** Reduce SKILL.md from 706 to <500 lines
5. **cross-system-search:** Add trigger keywords and output contract
6. **sprint-retro:** Add scripts for automated SpecStory parsing

### New Skills Needed
7. **e2e-testing:** End-to-end testing orchestration (identified gap)
8. **skill-review:** Meta-skill that audits other skills against this registry's rubric

---

## How to Use This Registry

1. **Before building a new skill:** Check this registry for overlap
2. **After modifying a skill:** Update the assessment and scores
3. **During retros:** Reference quality scores to identify systemic gaps
4. **For prioritization:** Use the backlog section to pick improvement work
