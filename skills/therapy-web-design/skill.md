# Therapy Web Design Skill

## CRITICAL: Who Is the Customer?

**The customer is the therapist — not the patient, not the conversion metric.**

This skill contains research-backed design knowledge. That research is valuable as RECOMMENDATIONS the therapist can see, understand, and override — never as invisible rules that make decisions for them. When generating websites for therapists:

- Present research as rationale ("We recommend X because research shows Y"), not as mandates
- Every default is overridable. Smart defaults guide; mandates alienate.
- Know the therapist (niche, approach, clients, stage, preferences) BEFORE recommending
- Creative decisions (colors, fonts, tone, content emphasis) belong to the therapist
- Technical decisions (HIPAA compliance, page speed, accessibility, semantic HTML) belong to the system
- Follow the informed consent model therapists use with their own clients: explain, recommend, respect the decision

**Why:** Psychological reactance theory predicts therapists — trained to detect influence tactics — will resist tools that remove their autonomy, even when the decisions are "correct."

---

## Core Purpose

Help therapists build websites they're proud of by providing research-informed recommendations, smart defaults, and transparent design rationale. Encodes 50+ sources of therapist buying psychology, content science, and conversion research as guidance — not rules. Produces HTML/CSS/JS that looks professionally designed, not AI-generated.

**When to activate:** Any task involving therapist websites, therapy landing pages, healthcare provider web design, or Site-Wizard product pages.

---

## Design Philosophy: Nervous-System-Aware Design

Prospective therapy clients are rarely calm or browsing casually. They are scanning quickly, uncertain about trust, and comparing multiple providers. The website's job is **not to impress but to regulate**. Beautiful does not automatically mean regulating — and regulation is what builds trust.

Your website does one of two things to the prospective client's brain: it either calms it or it overwhelms it. Design for calm.

This is the OPPOSITE of most AI design advice. Where generic AI guidance says "more motion, more contrast, more visual interest," therapy design needs: **calm, contained, predictable, spacious.**

---

## Anti-Generic Design Rules

You tend to converge toward generic, "on distribution" outputs. In frontend design, this creates what users call the "AI slop" aesthetic. Actively avoid this.

### Fonts — NEVER Use
- Inter, Roboto, Arial, Lato, Open Sans, system-ui defaults
- Space Grotesk (overused by Claude specifically)

### Fonts — USE Instead
For therapy/healthcare contexts, choose ONE distinctive font and pair it with a clean body font:

**Warm editorial (recommended for therapy):**
- Fraunces — variable weight, warm serifs, editorial feeling of trust
- Crimson Pro — elegant, readable, professional warmth
- Newsreader — editorial authority with approachability

**Clean modern pairing (for body text):**
- IBM Plex Sans — professional clarity without coldness
- Source Sans 3 — clean, neutral, excellent readability
- Satoshi — modern without being trendy

**Typography technique:**
- Weight extremes: 200-300 for body vs 700-900 for headings (not 400 vs 600)
- Size jumps: 3x+ scale between body and hero headline (not 1.5x)
- Load from Google Fonts. Pick ONE distinctive font, use it decisively.
- State your font choice before coding.

### Colors — NEVER Use
- Purple gradients on white backgrounds (the #1 AI design cliche)
- Evenly-distributed palettes where every color gets equal weight
- Neon accents or high-saturation combinations (creates anxiety, not calm)

### Colors — USE Instead
**Therapy-optimized palette (research-backed):**
- Blue tones increase trust perception by 34%
- Green elements improve perceptions of wellness and growth
- Blue-green (teal) captures both signals simultaneously

**Dominant + accent strategy:**
One dominant color with one sharp accent outperforms timid, evenly-distributed palettes. For therapy:
- Dominant: Deep teal (#1a6b6a) or similar blue-green — trust + wellness
- Accent: Warm coral (#e8735a) or warm gold — action + warmth + humanity
- Background: Warm off-white (#f7f5f2) — NOT pure white (too clinical)
- Text: Warm dark (#2d2d2d) — NOT pure black (too harsh)

Use CSS custom properties for the entire color system.

### Motion — NEVER Use
- Bounce or elastic easing (creates startlement for anxious visitors)
- Auto-playing video or audio (creates loss of control)
- Parallax scrolling (creates disorientation)
- Multiple competing animations (creates overwhelm)
- Glassmorphism effects (feels gimmicky, not professional)

### Motion — USE Instead
- ONE orchestrated page-load animation with staggered reveals (animation-delay)
- Subtle opacity + translateY transitions on scroll-into-view
- CSS-only solutions (no heavy JS animation libraries)
- Always respect `prefers-reduced-motion`
- Focus on moments of *reassurance*, not *delight*

### Backgrounds — NEVER Use
- Flat solid white (too clinical, creates sterile feeling)
- Complex geometric patterns (too busy for anxious visitors)
- Stock photo hero backgrounds (immediately undermines credibility)

### Backgrounds — USE Instead
- Warm off-white with subtle texture or very slight gradient
- Alternating section backgrounds (warm gray / white / warm gray) for visual rhythm
- Layered CSS gradients for subtle depth in hero sections
- Contextual warmth that says "you can relax here"

### Layouts — NEVER Use
- Dense text blocks (creates overwhelm)
- Complex multi-column layouts on mobile (creates confusion)
- Hidden navigation or hamburger menus on desktop (creates anxiety about finding things)
- Carousel/slider components (creates loss of control)

### Layouts — USE Instead
- Generous white space between sections (64px mobile, 96px desktop minimum)
- Single-column flow on mobile, max two columns on desktop
- Predictable top-to-bottom scroll flow (creates safety)
- One clear CTA per viewport (creates clarity)
- Maximum content width: 1120px centered

---

## Content Rules (Research-Backed)

These rules are derived from 32 sources on therapist website content and 25 sources on therapist buying psychology.

### The Six Stated-vs-Revealed Preference Gaps

Therapists say one thing but buy/praise another. Design for what they ACTUALLY respond to:

| What They Say | What They Buy | Design Implication |
|---|---|---|
| "I want custom design" | Templates and managed services | Make choices feel customized but use proven structures |
| "I'll write my own copy" | Content becomes the bottleneck | Minimize content creation burden, auto-populate where possible |
| "I want to be involved" | They get overwhelmed and disengage | Make choices feel low-stakes and reversible |
| "Aesthetics are my top priority" | Results drive satisfaction | Frame outcomes (clients), not beauty |
| "Price doesn't matter if good" | They choose the most affordable | Anchor pricing against expensive alternatives |
| "I want something different" | They want something safe | Provide "safe uniqueness" — controlled variation, not radical creativity |

### The Word "Custom" Is Banned

The word "custom" has been so abused by Brighter Vision and TherapySites that it is now a red flag for many therapists. NEVER use it. Instead use: "unique," "yours," "one-of-a-kind," "no two sites look alike," "made for you."

### Content Hierarchy: The Reverse Therapy Session

Structure landing pages and homepages to mirror the psychological arc of a therapy intake session:

1. **Acknowledge** — Name the visitor's pain or situation (hero section)
2. **Validate** — Show you understand their emotional experience (empathy block)
3. **Explain** — Describe how the solution works (how-it-works section)
4. **Qualify** — Establish trust and credibility (trust signals, pricing)
5. **Next Step** — Remove every barrier to action (CTA)

This structure "feels right" to therapists because it mirrors the therapeutic process they know and trust.

### Reading Level = Conversion Rate

Pages written at 5th-7th grade reading level achieve 10.8% median conversion. Content at 10th-12th grade level sees conversion drop by 55.6%. This means:
- Short paragraphs (2-3 sentences max)
- One idea per sentence
- Common words, not clinical jargon
- Generous white space between content blocks
- Large, scannable headings that communicate the key point even if body text is skipped

### Lead with Pain Points, Not Credentials

"You've been carrying this weight for too long" connects immediately.
"Dr. Smith is a licensed clinical psychologist with 15 years of experience" does not.

Credentials go in a separate, scannable section BELOW the emotional connection — never in the hero, never as the lead.

### CTA Language That Converts

- "Schedule Your Free Consultation" > "Learn More" > "Contact Us"
- Action-oriented, specific text always outperforms vague text
- 1-3 CTAs per landing page, 3-5 max per homepage
- Place CTAs: above the fold, after bio section, after each service description, at page footer

### FAQ Sections Increase Engagement by 22%

Always include FAQ sections. They reduce the cognitive load of reaching out while capturing long-tail SEO queries.

---

## Conversion Optimization Rules

### Form Design
- 4-5 fields MAXIMUM: name, email, phone, brief message
- 4-field forms: 67% completion rate. 8+ fields: 23% completion rate.
- Offer multiple contact options: online booking, phone, email, form
- Display estimated response time ("I typically respond within 24 hours")
- Phone number must be clickable on mobile

### Page Speed
- LCP under 2 seconds on mobile (a documented 35% inquiry increase from speed optimization alone)
- PageSpeed score 90+ on mobile
- Total page weight under 800KB
- Hero images under 150KB (WebP format)
- Lazy load all below-fold images
- Minimize third-party scripts

### Mobile-First (Non-Negotiable)
- 88% of therapy searches happen on mobile (often during emotional distress)
- 68% of therapy searches are mobile, often during crisis moments
- All touch targets minimum 44x44px
- Click-to-call phone numbers
- Full-width CTAs on mobile
- Simplified navigation

### Trust Signals
- 75% of people judge credibility based on website design alone
- Display as a distinct visual band: HIPAA | No Lock-In | Own Everything | Cancel Anytime
- Professional headshot is the single most important image (92% of patients read the bio before booking)
- Never use stock photos (immediately undermines credibility)
- License number and credentials in scannable format
- Association logos provide third-party validation

### HIPAA Compliance in Design
- Contact forms must note whether they are HIPAA-compliant or not
- Email addresses must include a disclaimer about not sharing PHI
- Good Faith Estimate notice must be prominently displayed (federal requirement)
- Privacy Policy must be linked in footer

---

## Therapy-Specific SEO in Design

When generating page HTML, include these structural SEO elements:

- H1 headline on every page containing primary keyword + location
- H2 tags for each service or subtopic
- Meta description written for click-through (therapy-specific, empathetic)
- Alt text on all images describing actual content
- Schema markup: MedicalBusiness, Physician, FAQPage (JSON-LD)
- Each specialty gets its own page targeting one primary keyword
- Internal links between related service pages

---

## Competitive Positioning (for Landing Pages)

When building comparison sections, use verified data:

| Feature | Site-Wizard | Brighter Vision | TherapySites | Squarespace |
|---|---|---|---|---|
| Setup time | 15 min | 2-3 weeks | 2-4 weeks | 4-10 hours |
| Price (entry) | $49-79/mo | $99-349/mo + $100 setup | $69-237/mo + $199 setup | $16-36/mo |
| PT profile import | Yes | No | No | No |
| Theme switching | Yes (no re-entry) | No (full rebuild) | No (full rebuild) | Yes |
| HIPAA forms | Yes | Add-on (Hushmail) | Yes | No (3rd party) |
| Content ownership | Yes | No (BV retains) | No (IB retains) | Yes |
| Mobile-first | Yes | Partial (complaints) | Partial | Yes |

Never attack competitors by name in hero sections. Use comparison tables in mid-page pricing sections where the visitor is evaluating options.

---

## Output Standards

When generating HTML/CSS/JS for therapy web pages:

1. **Semantic HTML5** — header, main, section, footer, nav with ARIA landmarks
2. **Responsive breakpoints** — 320px (mobile), 768px (tablet), 1024px (desktop), 1440px (wide)
3. **Accessibility** — WCAG 2.1 AA minimum: 4.5:1 contrast, 16px minimum body font, keyboard navigation, screen reader labels, focus indicators
4. **Performance** — under 800KB total, WebP images with JPEG fallback, lazy loading below fold, minimal JS
5. **No frameworks required** — vanilla HTML/CSS/JS unless specifically requested. Self-contained files that can be pasted into any platform (Unbounce, WordPress, Webflow, etc.)
6. **CSS custom properties** for the full design system (colors, typography, spacing)
7. **GA4-ready** — all CTA buttons should have `data-cta` and `data-cta-position` attributes for event tracking
