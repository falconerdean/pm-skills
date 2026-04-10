# Load-Bearing Classification Guide

A claim is "load-bearing" if the sprint's success depends on it being true. Load-bearing CONTRADICTED or UNVERIFIABLE claims trigger a BLOCK verdict; non-load-bearing ones only trigger a FLAG.

This distinction is critical because **false positives (blocking on cosmetic claims) create bottlenecks, and false negatives (missing load-bearing issues) cost sprints.** When in doubt, classify as load-bearing. The cost of a false positive is a review cycle; the cost of a false negative is measured in sprints.

---

## Load-Bearing: YES

A claim is load-bearing if ANY of these are true:

### 1. The sprint's measurable goal depends on it

Example sprint goal: "Import existing therapist website content via URL."
Example claim: "Stitch SDK has an `extractUrl()` method."
Why load-bearing: The sprint goal cannot be achieved without a way to extract content from URLs. If the method does not exist, the goal is not achievable with the current approach.

### 2. A downstream phase will write code that directly uses the claim

Example claim: "Stripe's `PaymentIntent.capture_method = 'manual'` allows deferred capture up to 7 days."
Why load-bearing: If the architecture is designed around 7-day deferred capture and Stripe's actual limit is 24 hours, the architecture must be redone.

### 3. A planned integration or API call relies on the claim being accurate

Example claim: "Sanity CMS supports webhooks on document publish events."
Why load-bearing: If the architecture assumes webhooks will fire on publish and Sanity does not actually support this, the entire synchronization flow breaks.

### 4. A compliance or regulatory boundary is defined by the claim

Example claim: "HIPAA does not apply to therapist marketing websites that don't collect PHI."
Why load-bearing: If this is wrong, the architecture needs BAAs, encryption at rest, access logging, and audit trails — a massively larger scope than a marketing site.

### 5. A cost model or business case uses the claim as an input

Example claim: "Sanity Business plan includes 25 GB of asset storage at $949/month."
Why load-bearing: If the actual price or storage is different, the unit economics of the product change. If the business case requires $0.01 per asset and Sanity charges $0.05, the product is not viable.

### 6. A technical constraint shapes the architecture

Example claim: "Stripe's API rate limit is 100 requests/second."
Why load-bearing: If the system is designed around this limit and the real limit is 25 requests/second, the architecture must include queuing, backpressure, or batching that weren't planned.

### 7. A customer behavior assumption drives the product direction

Example claim: "6 of 10 interviewed therapists explicitly requested templates rather than custom controls."
Why load-bearing: If the product direction is built on this finding and the finding is wrong (e.g., the interviews were misrepresented), the entire product strategy is wrong.

---

## Load-Bearing: NO

A claim is NOT load-bearing if ALL of these are true:

### 1. It's background context

Example: "The website builder market for therapists is estimated at $2.1 billion in 2026."
Why not load-bearing: This is investor-facing color. The sprint's technical approach and customer value do not depend on the exact TAM figure.

### 2. It's supporting detail that could be wrong without breaking the sprint

Example: "Psychology Today's profile completion feature launched in Q3 2024."
Why not load-bearing: The sprint plans do not depend on the exact launch date of a competitor's feature. If the date is slightly off, nothing changes.

### 3. It's a redundant claim

Example: Brief says "Sanity is popular with content teams" AND "Sanity has strong documentation" AND "Sanity is well-suited for structured content."
Why not load-bearing (individually): None of these statements are load-bearing on their own. They're descriptive framing. The load-bearing claim in the same brief would be the specific feature or API used.

### 4. The sprint could proceed unchanged if the claim were slightly different

Example: "Users spend approximately 12 minutes on average completing their profile."
Why not load-bearing: The sprint's goal (reduce time to <5 minutes) does not depend on whether the baseline is exactly 12 minutes or 14 minutes — the direction and magnitude of the target are the same.

### 5. It's a judgment or recommendation, not a verifiable fact

Example: "Using React Hook Form is the right choice for this form complexity."
Why not load-bearing: This is a judgment, not a factual claim. The Silent Observer does not evaluate judgments; it verifies facts. (The Business Reviewer or architectural review handles judgment claims.)

### 6. It's a future projection

Example: "We expect 40% of users to adopt the new feature within 30 days."
Why not load-bearing: This is a prediction, not a fact. It cannot be verified today. The business reviewer will check the falsification test for this prediction separately.

---

## Edge Cases

### A single library that could be replaced

Example claim: "We will use ScrapingBee as the scraping provider."
Is this load-bearing? It depends on whether the architecture is tightly coupled to ScrapingBee or whether the brief explicitly treats it as interchangeable.

If the brief says "We will use ScrapingBee, which has an API that returns structured data, rate-limited at 1000 req/min on the Business tier" — then the rate-limit claim is load-bearing (because the architecture may depend on that throughput), and the existence of ScrapingBee is load-bearing too (if they went out of business, the sprint fails).

If the brief says "We will use a third-party scraping provider such as ScrapingBee, Bright Data, or Apify" — then the specific provider choice is NOT load-bearing because it's presented as interchangeable.

Default: **if the brief names a single specific provider without alternatives, treat the provider's existence and key capabilities as load-bearing.**

### A market size that shapes the go/no-go decision

Example claim: "The TAM for therapist website builders is $2.1 billion."
Is this load-bearing? In most sprints, no — it's background. But if the sprint is a go/no-go decision about whether to enter the market, the TAM is load-bearing because the decision depends on the size of the opportunity.

Default: **market claims are not load-bearing unless the sprint is explicitly a go/no-go or scope decision that depends on market size.**

### A customer research finding

Example claim: "8 of 10 interviewed therapists cited 'too much manual data entry' as their biggest pain point."
Is this load-bearing? Usually yes, if the sprint is building a feature to address that pain point. The specific number is less important than the direction of the finding.

Default: **customer research findings that shape the product direction are load-bearing; customer research findings that are color or supporting context are not.**

### A regulatory requirement

Example claim: "HIPAA requires encryption at rest for PHI."
Is this load-bearing? Almost always yes. Compliance claims are rarely "nice to know" — they either shape the architecture or they don't matter at all.

Default: **regulatory requirements are load-bearing by default unless they are clearly outside the sprint's scope.**

---

## The "When in Doubt" Rule

When you cannot clearly classify a claim, mark it as **load_bearing: true**.

Rationale: the cost of a false positive (marking non-load-bearing as load-bearing) is that a FLAG becomes a BLOCK, which triggers one review cycle to investigate. The cost of a false negative (marking load-bearing as non-load-bearing) is that a fabricated claim passes through to Phase 5 and the architecture is built on it. Sprint 11 is the proof that false negatives cost sprints.

False positive cost: hours.
False negative cost: weeks.

Classify conservatively.

---

## Anti-Pattern: Load-Bearing Inflation

Do NOT classify every claim as load-bearing to "be safe." This creates bikeshedding and reduces the signal-to-noise of the Silent Observer's output. If a claim is clearly background color or redundant descriptive framing, classify it as non-load-bearing.

The test: **if this claim turned out to be wrong, would the sprint need to be redone, or would we just correct the brief and move on?**

- Redone → load-bearing
- Just correct and move on → not load-bearing

Most briefs have 5-15 factual claims, of which 2-5 are load-bearing. If the Silent Observer is classifying 80% of claims as load-bearing, the classification is inflated. Recalibrate.
