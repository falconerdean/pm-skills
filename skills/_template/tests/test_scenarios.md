# Test Scenarios

Define 3+ test scenarios for this skill. Run these before marking the skill as production-ready.

---

## Test 1: [Happy Path — Standard Use Case]

**Input:** [What the user says or provides]
**Expected behavior:** [What the skill should do, step by step]
**Expected output:** [What the deliverable looks like]
**Success criteria:**
- [ ] Output matches contract (all required sections, formats, word counts)
- [ ] No simulation language
- [ ] Completed in reasonable time
- [ ] No unnecessary tool calls or subagent spawns
**Known edge cases:** [What might go wrong]

---

## Test 2: [Edge Case — Minimal Input]

**Input:** [Minimal or ambiguous user input]
**Expected behavior:** [Should the skill ask for clarification? Proceed with defaults?]
**Expected output:** [What should happen]
**Success criteria:**
- [ ] Handles gracefully without hallucinating missing context
- [ ] Asks for clarification if input is truly insufficient
- [ ] Does not produce placeholder-heavy output
**Known edge cases:** [What might go wrong]

---

## Test 3: [Failure Case — Expected Error]

**Input:** [Input that should trigger error handling]
**Expected behavior:** [Should follow error recovery protocol]
**Expected output:** [Diagnostics file or user-facing error message]
**Success criteria:**
- [ ] Error classified correctly (recoverable vs unrecoverable)
- [ ] Appropriate recovery action taken
- [ ] User informed of what happened and suggested next steps
**Known edge cases:** [What might go wrong]
