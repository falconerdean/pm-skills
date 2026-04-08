---
name: proof-of-change
description: >
  Verify that code changes actually worked in the rendered output.
  Extracts computed styles, takes screenshots, runs assertions, and
  produces evidence that the change had the intended effect. Prevents
  agents from declaring "done" without visual/structural confirmation.
triggers:
  - verify
  - proof of change
  - check your work
  - did it actually change
  - screenshot
  - visual verify
  - confirm the change
---

# Proof of Change

## Core Rule

**NEVER declare a change "done" based on code modifications alone.** Every change must have evidence that it worked in the actual rendered output — computed CSS values, DOM assertions, screenshots, or Lighthouse scores. If you can't prove it changed, it didn't change.

## Why This Exists

Sprint 7 shipped 1,406 passing tests and zero viewable websites. Colors were "changed" in CSS but never verified in a browser. Layouts were "fixed" in code but never screenshot-confirmed. When AI writes both the code AND the tests, the tests are not independent evidence (Carnegie Mellon, 2025). The rendered output is the only truth.

---

## When to Use

After ANY change to:
- Colors, fonts, spacing, borders, shadows
- Layout, positioning, responsive behavior
- Content, text, images
- API integrations (verify the response, not just the code)
- Performance optimizations
- Accessibility fixes

## Arguments

Parse `$ARGUMENTS` for:
- `--url URL` : page to verify (default: detect from dev server or WORKING_CONTEXT.md)
- `--type color|layout|content|performance|accessibility|all` : what to verify
- `--before PATH` : path to "before" screenshot for comparison
- `--selector SELECTOR` : CSS selector to focus verification on
- `--expected KEY=VALUE` : expected values (e.g., `background-color=#2563eb`)

---

## Phase 1: Determine Verification Tool

Check what's available, in this order:

```
1. Chrome DevTools MCP available?
   → YES: Use it (preferred — richest API, already connected)
   → NO: Continue

2. Playwright installed? (`npx playwright --version`)
   → YES: Use it
   → NO: Install minimal: `npm init -y && npm install -D @playwright/test && npx playwright install chromium`

3. Neither available?
   → Use curl + DOM parsing as last resort (limited but better than nothing)
```

---

## Phase 2: Capture "Before" State (if not provided)

Before making the change, capture evidence of the current state:

```javascript
// Screenshot
mcp__chrome-devtools__take_screenshot  // or: await page.screenshot()

// Computed styles of target element
mcp__chrome-devtools__evaluate_script({
  expression: `(() => {
    const el = document.querySelector('${SELECTOR}');
    if (!el) return null;
    const cs = getComputedStyle(el);
    return {
      backgroundColor: cs.backgroundColor,
      color: cs.color,
      fontSize: cs.fontSize,
      fontFamily: cs.fontFamily,
      padding: cs.padding,
      margin: cs.margin,
      borderRadius: cs.borderRadius,
      width: el.getBoundingClientRect().width,
      height: el.getBoundingClientRect().height,
      x: el.getBoundingClientRect().x,
      y: el.getBoundingClientRect().y
    };
  })()`
})
```

Save both the screenshot and the style object for comparison.

---

## Phase 3: Make the Change

Apply the code change normally. Wait for hot reload or rebuild.

---

## Phase 4: Verify — Per Change Type

### Color Changes

**DO NOT trust CSS source files.** Specificity, cascade, and overrides can prevent your change from taking effect. Verify the COMPUTED value:

```javascript
// Extract computed color from the rendered page
const actual = await page.$eval(SELECTOR, el =>
  getComputedStyle(el).backgroundColor
);
// Returns "rgb(37, 99, 235)" — compare to expected

// Convert RGB to hex for comparison
function rgbToHex(rgb) {
  const [r, g, b] = rgb.match(/\d+/g).map(Number);
  return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('');
}

// Compare with tolerance (CIEDE2000 perceptual distance)
// deltaE < 1.0 = imperceptible, < 3.0 = barely noticeable, > 5.0 = clearly different
```

**Evidence required:** Before hex value → After hex value → Expected hex value → Match: yes/no

### Layout Changes

```javascript
// Measure element dimensions and position
const box = await page.locator(SELECTOR).boundingBox();
// Returns { x, y, width, height }

// Check no horizontal overflow (responsive fix)
const hasOverflow = await page.evaluate(() =>
  document.documentElement.scrollWidth > document.documentElement.clientWidth
);

// Check element is visible in viewport
await expect(page.locator(SELECTOR)).toBeInViewport();

// Check no overlap between elements
function overlaps(a, b) {
  return !(a.x + a.width <= b.x || b.x + b.width <= a.x ||
           a.y + a.height <= b.y || b.y + b.height <= a.y);
}
```

**Evidence required:** Before position/size → After position/size → Expected → Match: yes/no + screenshot

### Content Changes

```javascript
// Verify text appears on page
await expect(page.locator(SELECTOR)).toContainText('Expected content');

// Verify no placeholder text remains
const body = await page.locator('body').textContent();
expect(body).not.toContain('Lorem ipsum');
expect(body).not.toContain('[placeholder]');
expect(body).not.toContain('[object Object]');
expect(body).not.toContain('undefined');

// Verify all required sections exist
for (const section of ['About', 'Services', 'Contact']) {
  await expect(page.getByRole('heading', { name: section })).toBeVisible();
}
```

**Evidence required:** Expected text → Found on page: yes/no → Screenshot showing the content

### API Integration Changes

```javascript
// Verify the API actually returns data
const response = await page.request.get('/api/endpoint');
expect(response.status()).toBe(200);
const data = await response.json();

// Verify response shape (not just status)
expect(data).toHaveProperty('id');
expect(data.items.length).toBeGreaterThan(0);

// Verify the rendered page uses the API data (not mock/fallback)
const renderedName = await page.locator('.profile-name').textContent();
expect(renderedName).toBe(data.name); // actual API data matches what's on screen
```

**Evidence required:** API response status + shape → Rendered content matches API data: yes/no

### Performance Changes

```javascript
// Run Lighthouse audit
// Via Chrome DevTools MCP:
mcp__chrome-devtools__lighthouse_audit

// Or programmatically:
import lighthouse from 'lighthouse';
const { lhr } = await lighthouse(url, { port: chrome.port });

const scores = {
  performance: lhr.categories.performance.score * 100,
  accessibility: lhr.categories.accessibility.score * 100,
  bestPractices: lhr.categories['best-practices'].score * 100,
  seo: lhr.categories.seo.score * 100,
};

// Core Web Vitals
const lcp = lhr.audits['largest-contentful-paint'].numericValue; // ms, target <= 2500
const cls = lhr.audits['cumulative-layout-shift'].numericValue;  // target <= 0.1
const tbt = lhr.audits['total-blocking-time'].numericValue;      // ms, target <= 200
```

**Evidence required:** Before scores → After scores → Improvement/regression per metric

### Accessibility Changes

```javascript
// Via @axe-core/playwright
import AxeBuilder from '@axe-core/playwright';

const results = await new AxeBuilder({ page })
  .withTags(['wcag2a', 'wcag2aa'])
  .analyze();

const critical = results.violations.filter(
  v => v.impact === 'critical' || v.impact === 'serious'
);
expect(critical).toHaveLength(0);
```

**Evidence required:** Before violation count → After violation count → Zero critical/serious violations

---

## Phase 5: Screenshot Comparison (Always)

Regardless of change type, ALWAYS take before/after screenshots and compare:

### Using Chrome DevTools MCP
```
1. mcp__chrome-devtools__take_screenshot  (before — save path)
2. [make the change, wait for reload]
3. mcp__chrome-devtools__take_screenshot  (after — save path)
4. Compare visually (describe what changed in the screenshot)
```

### Using Playwright
```javascript
// Take before screenshot, save
await page.screenshot({ path: 'before.png', fullPage: true });

// [make change]

// Take after screenshot and compare
await page.screenshot({ path: 'after.png', fullPage: true });

// Programmatic diff
const pixelmatch = require('pixelmatch');
const { PNG } = require('pngjs');
// ... load both PNGs, compare, output diff percentage
```

### Responsive Verification
```javascript
// Check at 3 breakpoints minimum
for (const vp of [
  { width: 375, height: 812, name: 'mobile' },
  { width: 768, height: 1024, name: 'tablet' },
  { width: 1440, height: 900, name: 'desktop' },
]) {
  await page.setViewportSize(vp);
  await page.screenshot({ path: `after-${vp.name}.png`, fullPage: true });
  // Verify no horizontal overflow
  const overflow = await page.evaluate(() =>
    document.documentElement.scrollWidth > document.documentElement.clientWidth
  );
  expect(overflow).toBe(false);
}
```

---

## Phase 6: Produce Evidence Report

Every proof-of-change must include:

```markdown
## Proof of Change: {description}

**Change:** {what was changed}
**URL:** {url verified}
**Date:** {UTC timestamp}

### Assertions
| Check | Expected | Actual | Pass |
|-------|----------|--------|------|
| background-color | #2563eb | #2563eb | ✓ |
| font-size | 18px | 18px | ✓ |
| element visible | true | true | ✓ |
| no overflow | false | false | ✓ |

### Screenshots
- Before: {path}
- After: {path}
- Diff: {path} ({N}% pixels changed)

### Lighthouse (if applicable)
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Performance | 72 | 85 | +13 |
| Accessibility | 91 | 98 | +7 |

### Verdict: VERIFIED / NOT VERIFIED
```

---

## Quick Reference: Verification Matrix

| Change Type | Primary Check | Secondary Check | Tool |
|-------------|--------------|-----------------|------|
| Color | `getComputedStyle().backgroundColor` | Screenshot diff | Chrome DevTools / Playwright |
| Font | `getComputedStyle().fontFamily, fontSize` | Screenshot | Chrome DevTools / Playwright |
| Spacing | `getBoundingClientRect()` | Screenshot diff | Chrome DevTools / Playwright |
| Layout | `boundingBox()` + overflow check | Responsive screenshots | Playwright |
| Content | `textContent()` / `toContainText()` | Screenshot | Playwright |
| Images | `img.naturalWidth > 0` + `src` check | Screenshot | Chrome DevTools |
| API data | Response status + shape | Rendered content matches | Playwright / curl |
| Performance | Lighthouse scores | Core Web Vitals | Lighthouse MCP / CLI |
| Accessibility | axe-core violations | Lighthouse a11y score | @axe-core/playwright |
| Responsive | Viewport loop + overflow | Multi-breakpoint screenshots | Playwright |

---

## Anti-Patterns

1. **"I changed the CSS file, so the color changed"** — No. Specificity, cascade, !important, inline styles, and JS overrides can all prevent your change from taking effect. Check the COMPUTED value.
2. **"Tests pass, so it works"** — No. When AI writes both code and tests, tests are not independent evidence. The rendered output is the truth.
3. **"I deployed it, so it's working"** — No. Deployment ≠ rendering. Check the live URL in a browser.
4. **"PARTIAL verification"** — No. Either you verified the change or you didn't. There is no partial.
5. **"I'll verify later"** — No. Verify immediately after the change, before moving on.
6. **Screenshot without assertions** — A screenshot alone is not proof. Extract the actual values and compare to expected.
