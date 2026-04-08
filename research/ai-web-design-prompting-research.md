# AI Web Design Prompting: Deep Research Report

**Date:** 2026-04-06 UTC
**Research scope:** Techniques for producing high-quality, unique, conversion-optimized web design through AI prompting -- not generic template output.

---

## Executive Summary

AI-generated web design defaults to generic output because LLMs learned from the same training data (Tailwind UI, shadcn/ui templates) and fill ambiguity with statistical averages. The single biggest lever for quality is **constraint specificity** -- providing explicit design systems, real copy, user research, and aesthetic references rather than vague descriptors like "modern" or "clean." A documented A/B test showed an AI-generated landing page beating a human-designed version by 44.83% conversion lift at 99% confidence, but the AI version succeeded specifically because it was fed detailed brand context, used proven copywriting frameworks (PAS), and received structured iterative critique -- not because AI is inherently better at design.

**Key finding:** The competitive advantage has shifted from execution speed to **articulation clarity**. Designers who provide precise constraints, real content, and behavioral intent get dramatically better AI output than those who provide aesthetic adjectives.

---

## 1. Design System Prompting: Feeding AI Specific Constraints

### Why AI Defaults to Generic Output

**Confidence: HIGH** -- Multiple independent sources confirm the same root cause.

LLMs produce identical "AI slop" because they converge on statistical averages from training data. The default AI UI starter pack is:
- Inter font (always)
- Purple/violet gradients on white backgrounds
- Cards nested inside cards
- Gray text on colored backgrounds
- Three-box-with-icons layouts
- Bounce/elastic animations

> "All LLMs learned from the same generic templates like Tailwind UI and shadcn/ui."
> -- [Why Your AI Keeps Building the Same Purple Gradient Website](https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website)

### The Anthropic Cookbook's Distilled Aesthetics Prompt

The most authoritative source on this is Anthropic's own published cookbook, which provides a tested system prompt for frontend aesthetics:

```
<frontend_aesthetics>
You tend to converge toward generic, "on distribution" outputs. In frontend design, this
creates what users call the "AI slop" aesthetic. Avoid this: make creative, distinctive
frontends that surprise and delight. Focus on:

Typography: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts
like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics.

Color & Theme: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant
colors with sharp accents outperform timid, evenly-distributed palettes.

Motion: Use animations for effects and micro-interactions. Prioritize CSS-only solutions.
Focus on high-impact moments: one well-orchestrated page load with staggered reveals
creates more delight than scattered micro-interactions.

Backgrounds: Create atmosphere and depth rather than defaulting to solid colors. Layer CSS
gradients, use geometric patterns, or add contextual effects.

Avoid generic AI-generated aesthetics:
- Overused font families (Inter, Roboto, Arial, system fonts)
- Cliched color schemes (particularly purple gradients on white backgrounds)
- Predictable layouts and component patterns
- Cookie-cutter design that lacks context-specific character
</frontend_aesthetics>
```

Source: [Anthropic Cookbook -- Prompting for Frontend Aesthetics](https://platform.claude.com/cookbook/coding-prompting-for-frontend-aesthetics)

### Concrete Font Alternatives

| Category | Never Use | Use Instead |
|----------|-----------|-------------|
| Code aesthetic | Inter, Roboto | JetBrains Mono, Fira Code, Space Grotesk |
| Editorial | Arial, Open Sans | Playfair Display, Crimson Pro, Fraunces |
| Startup/SaaS | Lato, system fonts | Clash Display, Satoshi, Cabinet Grotesk |
| Technical | default sans | IBM Plex family, Source Sans 3 |
| Distinctive | any default | Bricolage Grotesque, Obviously, Newsreader |

**Pairing principle:** High contrast = interesting. Display + monospace, serif + geometric sans. Use weight extremes (100/200 vs 800/900, not 400 vs 600). Size jumps of 3x+, not 1.5x.

### The "Impeccable Design" Skill

An open-source tool (8,000+ GitHub stars) that bolts onto Claude Code, Cursor, and other AI coding tools to enforce design quality through seven domains of anti-patterns and 20 actionable commands:

- `/audit` -- Technical quality review
- `/normalize` -- Design system alignment  
- `/polish` -- Pre-launch refinement
- `/typeset` -- Typography optimization
- `/colorize` -- Strategic color application

It explicitly prohibits: Inter, Roboto, Arial, gray text on colored backgrounds, pure black (#000), nested card structures, and bounce/elastic easing.

Source: [Stop Your AI Coding Tool from Generating Generic UI](https://dev.to/_46ea277e677b888e0cd13/stop-your-ai-coding-tool-from-generating-generic-ui-impeccable-design-skill-4g1l)

---

## 2. Reference-Based Prompting: Visual Anchors Beat Aesthetic Words

**Confidence: HIGH** -- Consistent across multiple practitioner sources.

### The Core Principle

> "Never input prompts without reference screenshots."

Rather than asking AI to *invent* aesthetics, ask it to *analyze and extract* design systems from reference screenshots. This makes AI a **translator of existing taste** rather than an inventor of aesthetics.

### Reference-Based Workflow (7 Steps)

1. **Gather 2-4 screenshots** from Pinterest/Dribbble/Awwwards with consistent styling
2. **Upload to AI tool** (Figma Make, v0, etc.)
3. **Deploy analysis prompt:** "Deeply analyze the design of the attached screenshot to create a design system layout of every UI component. Pay close attention to spacing, fonts, colors, design styles, and design principles."
4. **Extract the design system:** colors with semantic usage, typography scales, spacing rules, component states
5. **Define variables:** spacing (4/8/16/24pt), typography hierarchy, color tokens
6. **Build reusable components** from the extracted system
7. **Generate new screens** referencing the established system

Source: [How to Get Better UI Design with Figma Make](https://sergeichyrkov.com/blog/how-to-get-better-ui-design-with-figma-make-and-ai-(without-generic-results))

### Cultural/Stylistic Anchors for Prompting

Instead of "make it modern," use specific cultural references:
- "1970s ski lodge: burnt orange, avocado green, warm browns"
- "Art deco typography: high contrast, geometric, bold"
- "Japanese print design: asymmetric, plenty of negative space"
- "Inspired by Linear's aesthetic" or "Stripe's header style"

These target patterns beyond the training median where AI defaults live.

### Figma Make: Guidelines.md and Make Kits

Figma Make accepts a `Guidelines.md` file with rules like:
- "Only use absolute positioning when necessary. Opt for flexbox and grid by default."
- "Never use the floating action button with the bottom toolbar."
- "Chips should always come in sets of 3 or more."

Make Kits allow design system authors to package components, styles, and guidelines so AI prototypes begin production-aligned from the start.

> "More context isn't always better. It can confuse the LLM. Try and add the most important rules you need."
> -- [Figma Help: Add Guidelines to Figma Make](https://help.figma.com/hc/en-us/articles/33665861260823-Add-guidelines-to-Figma-Make)

---

## 3. Research-to-Design Pipelines: Feeding User Data Into AI

**Confidence: HIGH** -- Supported by academic research and practitioner evidence.

### The Evidence: Research Data Improves AI Design Output

Multiple studies confirm that feeding real user research into AI prompts produces dramatically better output than generic briefs:

- **LLM-generated personas** from real data were perceived as "more consistent, useful, and empathy-evoking" than those created by designers alone (Human-AI persona workflow study, Joongi Shin et al.)
- Proto-persona generation via prompt engineering "reduced time and effort while improving quality and reusability" (arXiv case study)
- The RTCF framework (Role, Task, Context, Format) transforms vague AI requests into precise instructions that deliver actionable personas

Source: [AI for Personas -- IxDF](https://ixdf.org/literature/article/ai-for-personas)

### What Research Data to Feed AI

Your knowledge base for AI prompting should include:
- User interview transcripts
- Survey responses and behavioral data
- Direct quotes and pain points
- Customer support tickets
- Feature requests
- Competitive analysis data
- Conversion funnel analytics

> "Your best personas emerge from real data, not assumptions. Instead of feeding AI generic prompts, use actual research data as a comprehensive knowledge base."

### Synthetic Personas for Landing Page Testing

The SSR (Semantic Similarity Rating) framework from PyMC Labs achieves ~90% of human test-retest reliability. Validated across 57 consumer surveys with 9,300+ human responses. The method:

1. Create diverse synthetic personas with demographic attributes
2. Have each persona evaluate landing page content from their perspective
3. Measure semantic similarity to reference scale statements
4. Produce actionable scores with 95% confidence intervals

**Use case:** Test landing page messaging against 25 different persona types before launch, identifying which segments respond to which copy variations.

Source: [Synthetic Personas for Landing Page Optimization](https://locomotive.agency/blog/synthetic-personas-landing-page-optimization-llm-focus-groups/)

### The DESIGNER MODE Framework

A seven-point checklist that replaces aesthetic descriptors with design logic:

| Step | Focus | What to Provide |
|------|-------|-----------------|
| D -- Decision Context | Who uses this? What problem? | User role, scenario, pain points |
| E -- Environment | Device, screen, conditions | Technical constraints, usage context |
| S -- System | Design patterns, mental models | Existing design system references |
| I -- Intent | Behavioral outcomes, not aesthetics | "What should feel obvious" not "clean" |
| G -- Guardrails | Explicit failure definitions | "What must NOT happen" |
| N -- Narrative | Attention flow progression | What appears first, what reveals later |
| E -- Evaluation | Success metrics | Criteria before seeing results |
| R -- Refinement | Iterative feedback | Specific critique, not vague reactions |

Source: [Prompting AI Like a Designer](https://medium.com/design-bootcamp/prompting-ai-like-a-designer-why-most-ai-generated-ui-designs-look-generic-945eccd35b7f)

---

## 4. Iterative Refinement Workflows

**Confidence: HIGH** -- The most consistently cited technique across all sources.

### The Two-Phase Faithful Implementation Protocol

From the "Your AI Agent Can Code, It Can't Design" methodology:

**Phase 1: Read & Confirm**
> "Clone the reference repo and read through the components. Summarize color palette, typography, layout approach."

**Phase 2: Implement with Precision**
> "Match layout, colors, typography, and spacing exactly. Any differences are bugs."

This prevents AI from filling gaps with its own assumptions. Agent deliverables include:
- Colors matched with precision (e.g., `hsl(153, 50%, 32%)` not "forest green")
- Exact font specifications (DM Sans, DM Serif Display)
- Pixel-perfect spacing replication

Source: [Your AI Agent Can Code. It Can't Design.](https://medium.com/@ssbob98/your-ai-agent-can-code-it-cant-design-here-s-how-i-fixed-that-e1ced4c444ca)

### The Design System Document Approach

Create two files that persist across all AI interactions:

**DESIGN-SYSTEM.md** (workspace-level philosophy):
```markdown
# Color Philosophy
- Primary: Bold, natural tones (forest green, deep blue)
- Accent: Warm, inviting (terracotta, amber)
- Neutrals: Warm grays, never pure black/white

# Typography Scale
xs: 0.75rem | sm: 0.875rem | base: 1rem | lg: 1.125rem | xl: 1.25rem
```

**DESIGN-TOKENS.md** (project-level specifics):
```markdown
primary: hsl(153, 50%, 32%)
accent: hsl(24, 70%, 55%)
neutral-50: hsl(30, 25%, 97%)
heading-font: 'DM Serif Display'
body-font: 'DM Sans'
```

> "More rules produce better output. Unconstrained agents regress to mediocrity; bounded agents with locked defaults generate consistency."

### The Crazy Egg Workflow (4 Stages)

The documented A/B test winner used this iterative process:

1. **Stage 1:** Claude generates detailed page structure + copy (2,300-word structured prompt similar to a product requirements brief)
2. **Stage 2:** Paste Claude's prompt into Base44 (vibe-coding platform) for full-page design
3. **Stage 3:** Screenshot the design, feed back to Claude for critique and revision -- Claude generates a second prompt with improvements
4. **Stage 4:** Brand-safety review by humans (logos, product details, factual accuracy)

> "I did not edit the content or the prompt. I didn't even read either before prompting Base44."

Source: [Crazy Egg: AI vs Human Landing Page A/B Test](https://www.crazyegg.com/blog/ai-vs-human-landing-page/)

### v0 Iteration Strategy

- Use **prompts** for functional changes, feature additions, structural modifications
- Use **Design Mode** for visual tweaks (colors, spacing, typography) -- faster iteration
- Specific prompts produced 19 seconds faster generation, 152 fewer lines of code, and lower token usage vs. generic prompts

Source: [How to Prompt v0 -- Vercel](https://vercel.com/blog/how-to-prompt-v0)

---

## 5. Component-Level vs Page-Level Generation

**Confidence: MEDIUM-HIGH** -- Practitioner consensus is clear, though controlled studies are limited.

### Component-Level is Superior for Quality

The evidence consistently favors component-level generation for several reasons:

1. **Modularity:** Component-level supports better code reuse and design system alignment
2. **Consistency:** Easier to maintain design tokens across components than across full pages
3. **Iteration speed:** Can fix one component without regenerating the entire page
4. **Production-readiness:** Component-level output maps more directly to production codebases

> "One of the major limitations of AI-generated sites is the lack of reusable components. While page builders offer systems for managing global components, AI platforms often require users to manually copy and paste code across different pages."

### Recommended Approach: Component-First Assembly

From the 0xMinds prompt collection:

> "Generate each section separately, then assemble. Maintain consistent color palette across all sections. Include responsive breakpoints in every prompt. Specify mobile behavior explicitly."

**Practical template library approach:**
- Create pre-crafted prompt templates for each component type (hero, features grid, testimonials, pricing, CTA)
- Each template includes design system constraints, interaction patterns, and mobile behavior
- Assemble components into pages after individual generation and review

Source: [AI UI Prompts: 300+ Templates](https://0xminds.com/blog/guides/ai-prompt-templates-complete-collection)

### The Relume Pipeline: Sitemap-First, Then Components

Relume demonstrates an effective middle ground:

1. Generate complete sitemap from 2-3 sentence brief (60 seconds)
2. AI generates section-level components with real copy for each page
3. Each section maps to a real component from 1,000+ component library
4. Export to Figma/Webflow/React for refinement

This produces logically structured pages faster than either pure component-level or pure page-level approaches.

Source: [Relume Resources](https://www.relume.io/resources)

---

## 6. The Role of Detailed Copy in AI Design Output

**Confidence: HIGH** -- Strong evidence from both the Crazy Egg A/B test and design practitioner sources.

### Real Copy Dramatically Improves Design Quality

The Crazy Egg A/B test provides the strongest evidence: the AI-generated page won not because of visual design, but because of **copy quality and structure.** The AI version:

1. Used the PAS (Problem-Agitation-Solution) copywriting framework systematically
2. Led with visitor outcomes instead of product features
3. Maintained consistent narrative progression toward conversion
4. Used color strategically to reinforce copy hierarchy (green = benefits = CTA)

> "The AI page follows a clear version of the PAS framework, one of the most widely used structures in direct response copywriting."

### Content-First vs Placeholder: The Quality Gap

When AI generates design with real, strategic copy vs placeholder text:

**With real copy:**
- Layout hierarchy naturally follows content priority
- CTA placement aligns with persuasion flow
- Section sizing reflects actual content needs
- Visual rhythm supports the reading experience

**With placeholder/Lorem Ipsum:**
- Layouts optimize for visual symmetry, not communication
- All sections get equal weight regardless of importance
- CTAs appear decorative rather than strategic
- Design and content must be re-aligned later

### The Crazy Egg AI Page's Copy Architecture

The winning page followed this precise narrative sequence:

1. **Hook with problem:** "Tired of analytics tools that create more confusion than clarity?"
2. **Agitate with specifics:** Three named pain points (Hours of Setup, Drowning in Data, Too Technical)
3. **Solution introduction:** "Analytics designed for real marketers, not data scientists"
4. **Show product in use:** UI screenshots with plain-language explanations
5. **Handle setup objection:** Integrations section (WordPress, Wix, Shopify)
6. **Prove with numbers:** Social proof, stats, brand logos
7. **Catch stragglers:** FAQ section
8. **Final CTA:** After every objection has been addressed

> "Each section earns the next. The visitor is never asked to convert before they've been given a reason to."

### CTA Color Psychology

The AI page used green consistently for all conversion-related elements. Reading only the green elements tells the complete value story:
- "real marketers"
- "Clear and actionable"
- "All in one place"
- Insights that "tell you what to do"
- "with one click"
- Questions "that actually matter"

Source: [Crazy Egg: AI vs Human Landing Page](https://www.crazyegg.com/blog/ai-vs-human-landing-page/)

---

## 7. Healthcare/Therapy Specific AI Design

**Confidence: HIGH** -- Research-backed with specific metrics and citations.

### Psychology-Backed Design Principles for Therapy Sites

Based on published research with specific citations (Stanford, Nielsen Norman Group, SAMHSA, Baymard Institute):

#### Color Psychology (Research-Backed)

Blue and green tones in healthcare websites **reduce anxiety by 23%** and **increase perceived trustworthiness by 31%** (BMC Medical Informatics and Decision Making).

| Color | Hex Values | Application |
|-------|-----------|-------------|
| Trust Blues | #4A90A4, #6B9AC4, #2C4A6B | Primary brand, credentials sections, low-anxiety CTAs |
| Healing Greens | #8B9D83, #A8B89F, #6B8E6F | Growth-focused sections, testimonials, resources |
| Safety Neutrals | #F5F3EF, #E8E6E1, #D4CFC9 | Backgrounds, text containers, section dividers |

**Colors to AVOID on therapy sites:**
- Bright Red -- increases anxiety, raises blood pressure
- Pure Black -- feels cold/impersonal, can trigger depressive associations
- Bright Yellow -- overstimulating, increases eye strain
- Pure White -- clinical coldness, feels sterile rather than safe
- High-contrast "corporate" or "medical" palettes

Source: [Psychology-Backed Web Design for Therapists](https://bethanyworks.com/psychology-backed-web-design-therapists-mental-health/)

#### Trust Signal Hierarchy

Trust signals "above the fold" **increase perceived credibility by 48%** (MIT Human-Computer Interaction Lab). Visitors spend **2.6 seconds** evaluating credibility before deciding to stay (Missouri University of Science and Technology).

Above-the-fold essentials for therapy sites:
1. **Credentials** (LMFT, PsyD, etc.) -- 89% of visitors look for this first
2. **Photo** (professional, warm, real -- not stock) -- increases trust by 34%
3. **Specialty/niche** ("Anxiety Specialist") -- reduces bounce by 28%
4. **Location/telehealth clarity** -- primary practical concern
5. **Insurance/payment info** -- addresses 63% of first objections

#### Trauma-Informed Design Principles (SAMHSA-Based)

Many therapy seekers have experienced trauma. Design adaptations:
- Clear exit paths (visible "X" on all modals, predictable back buttons)
- No autoplay video/audio (control = safety)
- Gentle transitions (no jarring animations)
- Text alternatives for all content
- Consistent layout (predictability reduces hypervigilance)

**Result:** Trauma-informed therapy websites see **34% lower bounce rates** among visitors who later disclose trauma history.

#### Readability Level

Pages written at **5th-7th grade reading level** achieve **10.8% median conversion rate.** At 10th-12th grade level, conversion drops by **55.6%**.

Replace clinical jargon: "anxiety disorder" becomes "feeling anxious or worried." Keep sentences under 20 words. Use active voice.

#### Form Design

Each additional form field **reduces completion by 4-5%** (Baymard Institute).

Optimal therapy contact form (4 fields): Name, Email, Phone, "What brings you to therapy?" (open text). Achieves **67% completion** vs 23% for 8+ field forms.

#### Mobile-First is Non-Negotiable

- 68% of therapy searches happen on mobile, often during moments of crisis
- Tap targets: 48px minimum (crisis moments = shaky hands)
- Click-to-call prominence
- 3 menu items max on mobile
- 16px minimum body text
- Load times under 2 seconds (each additional second = 11% fewer bookings)

#### What Actually Converts

> "Real headshots of the actual therapist in a real space doing real things does more conversion work than any amount of clever copywriting."

- Real photography over stock photos
- Vulnerability from the therapist as a trust signal
- Reducing navigation from 10 to 5 options increases conversion by 35%
- Multi-CTA strategy increases overall conversion by 38% vs single-CTA
- Detailed therapist profiles produce 34% better client-therapist match rates

Source: [Therapy Website Conversion Rate Optimization](https://alwaysopen.design/therapy-practices-cro-wins/), [Bethany Works](https://bethanyworks.com/psychology-backed-web-design-therapists-mental-health/)

---

## Key Questions Answered

### Q: What makes AI-generated design look "generic" and how do people overcome it?

**Answer:** Generic output comes from three sources: (1) LLMs converging on statistical averages from training data, (2) vague prompts that force AI to guess, and (3) missing design constraints. People overcome it by:

- Providing explicit design tokens (exact hex colors, specific font names, spacing scales)
- Using reference screenshots instead of aesthetic adjectives
- Adding one unexpected element per design (unusual typography weight, distinctive color combination, named design inspiration)
- Explicitly prohibiting defaults ("Never use Inter, Roboto, or purple gradients")
- Using the Anthropic Cookbook's `<frontend_aesthetics>` system prompt as a baseline

### Q: Does providing research data (personas, user psychology, conversion data) to AI improve design output?

**Answer:** Yes, strongly supported. LLM-generated personas from real data are perceived as more consistent, useful, and empathy-evoking than those from designers alone. The Crazy Egg A/B test showed that feeding AI detailed brand context and audience information produced a page that outperformed a human-designed version by 44.83%. The critical factor is providing **behavioral intent** ("visitors who are confused by complex analytics tools") rather than **demographic labels** ("marketers aged 25-45").

### Q: What's the optimal prompt structure for landing page generation?

**Answer:** The v0 framework is the most tested:

```
Build [product surface: components, data, actions].
Used by [who],
in [what moment],
to [what decision or outcome].
Constraints:
- platform / device
- visual tone / design system reference
- layout assumptions
- specific colors (hex, not names)
- fonts (specific names, not categories)
- what to avoid explicitly
```

For conversion-optimized copy, add:
- Target audience pain points (specific, not generic)
- Copywriting framework to follow (PAS, AIDA)
- CTA text (exact words)
- Social proof elements (specific numbers)
- Objection-handling sequence

### Q: Are there documented cases of AI-generated landing pages outperforming human-designed ones?

**Answer:** Yes. The Crazy Egg A/B test (March 2026) is the strongest documented case:

- **AI page:** 80.65% conversion rate (100 signups from 124 visitors)
- **Human page:** 55.68% conversion rate (98 signups from 176 visitors)
- **Lift:** 44.83% at 99% statistical confidence
- **~54,000 visitors per variant** in total test traffic

The AI version won because it: led with visitor outcomes instead of features, used the PAS copywriting framework, included a competitive comparison table, maintained consistent CTA color psychology, and followed a deliberate narrative sequence toward conversion.

**Important caveat:** The AI was given detailed brand context and the output was iterated through a critique-revise cycle. It was not a zero-shot generation.

Source: [Crazy Egg Blog](https://www.crazyegg.com/blog/ai-vs-human-landing-page/)

### Q: How do professional designers use AI differently than non-designers?

**Answer:** The key differences:

| Aspect | Professionals | Non-Designers |
|--------|--------------|---------------|
| Tool selection | Solve specific friction points | Grab the most impressive-sounding tool |
| Design systems | Build systems FOR AI consumption | Skip systems entirely |
| Evaluation | Product impact, problem framing | Speed of execution |
| Workflow | Chain multiple AI tools (ideation + generation + code) | Single-tool generation |
| Quality control | AI as junior designer requiring direction | AI as autonomous generator |
| Iteration | Specific critique-adjust-repeat cycles | Accept first output or give up |
| Constraints | More rules = better output | Fewer rules = more freedom (wrong) |

> "The better your taste, references, feedback, and product thinking, the better results will be. AI makes execution faster, but it still depends on design judgment."

---

## Optimal AI Web Design Workflow (Synthesis)

Based on all evidence gathered, the highest-quality AI web design workflow is:

### Phase 1: Research & Strategy (Human-Led)
1. Gather real user research (interviews, analytics, support tickets)
2. Define target personas with behavioral attributes
3. Choose copywriting framework (PAS for landing pages)
4. Write or commission real copy (not placeholder)
5. Identify 2-4 reference designs from inspiration sources

### Phase 2: Design System Definition (Human + AI)
6. Extract design system from reference screenshots using AI
7. Define design tokens in a DESIGN-TOKENS.md file (exact hex colors, font names, spacing scale)
8. Create DESIGN-SYSTEM.md with philosophy and anti-patterns
9. Set up `<frontend_aesthetics>` constraints in system prompt

### Phase 3: Component-Level Generation (AI-Led, Human-Directed)
10. Generate each section/component separately with design system constraints
11. Provide real copy, not Lorem Ipsum, for each component
12. Specify mobile behavior explicitly in each prompt
13. Include interaction states (hover, loading, error)

### Phase 4: Iterative Refinement (Human-AI Loop)
14. Screenshot the assembled page
15. Feed screenshot back to AI for structured critique
16. Apply critique as a second-pass prompt
17. Human brand-safety review (logos, facts, compliance)
18. Test with synthetic personas before launch

### Phase 5: Testing & Optimization
19. A/B test AI variant against existing page
20. Use conversion analytics to identify weak sections
21. Iterate at the component level based on data

---

## Sources

### Primary Sources (Directly Fetched and Verified)
- [Anthropic Cookbook: Prompting for Frontend Aesthetics](https://platform.claude.com/cookbook/coding-prompting-for-frontend-aesthetics)
- [Why Your AI Keeps Building the Same Purple Gradient Website](https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website)
- [Crazy Egg: AI vs Human Landing Page A/B Test (44% lift)](https://www.crazyegg.com/blog/ai-vs-human-landing-page/)
- [Your AI Agent Can Code. It Can't Design. Here's How I Fixed That.](https://medium.com/@ssbob98/your-ai-agent-can-code-it-cant-design-here-s-how-i-fixed-that-e1ced4c444ca)
- [Stop Your AI Coding Tool from Generating Generic UI: Impeccable Design Skill](https://dev.to/_46ea277e677b888e0cd13/stop-your-ai-coding-tool-from-generating-generic-ui-impeccable-design-skill-4g1l)
- [How to Get Better UI Design with Figma Make (Without Generic Results)](https://sergeichyrkov.com/blog/how-to-get-better-ui-design-with-figma-make-and-ai-(without-generic-results))
- [Prompting AI Like a Designer: DESIGNER MODE Framework](https://medium.com/design-bootcamp/prompting-ai-like-a-designer-why-most-ai-generated-ui-designs-look-generic-945eccd35b7f)
- [Synthetic Personas for Landing Page Optimization (LLM Focus Groups)](https://locomotive.agency/blog/synthetic-personas-landing-page-optimization-llm-focus-groups/)
- [Psychology-Backed Web Design for Therapists](https://bethanyworks.com/psychology-backed-web-design-therapists-mental-health/)
- [AI UI Prompts: 300+ Templates That Actually Work](https://0xminds.com/blog/guides/ai-prompt-templates-complete-collection)

### Secondary Sources (Search Results, Partial Verification)
- [How to Prompt v0 -- Vercel](https://vercel.com/blog/how-to-prompt-v0)
- [Working with Figma and Custom Design Systems in v0](https://vercel.com/blog/working-with-figma-and-custom-design-systems-in-v0)
- [Figma Help: Add Guidelines to Figma Make](https://help.figma.com/hc/en-us/articles/33665861260823-Add-guidelines-to-Figma-Make)
- [Figma Developer Docs: Create Design System Rules](https://developers.figma.com/docs/figma-mcp-server/skill-figma-create-design-system-rules/)
- [Relume: AI Website Builder](https://www.relume.io/)
- [Automating Design Systems with AI: 2026 Workflow Guide](https://www.parallelhq.com/blog/automating-design-systems-with-ai)
- [AI in Product Design: Where We Are Now in 2026](https://davidrdesign.medium.com/ai-in-product-design-where-we-are-now-in-2026-a71bceada2d8)
- [Therapy Website CRO -- Always Open Design](https://alwaysopen.design/therapy-practices-cro-wins/)
- [Therapy Website Not Converting? 5 Proven Fixes](https://mentalhealthitsolutions.com/blog/therapy-website-is-not-converting/)
- [AI for Persona Research -- IxDF](https://ixdf.org/literature/article/ai-for-personas)
- [Using AI for User Representation: Analysis of 83 Persona Prompts (arXiv)](https://arxiv.org/html/2508.13047v1)
- [RGD: AI Tools for Designers in 2026](https://rgd.ca/articles/2026-amplifying-creativity-with-ai-tools-for-designers-in-2026)
- [Copy Hackers: Write Landing Page with AI](https://copyhackers.com/ai-prompt/write-landing-page-with-ai/)
