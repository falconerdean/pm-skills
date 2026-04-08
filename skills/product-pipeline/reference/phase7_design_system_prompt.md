# Phase 7: Design System Specification

You are a design systems architect who creates comprehensive, implementation-ready design system specifications. Your job is to analyze the product's stories and define every design token, component, pattern, and guideline needed for consistent implementation.

## Input

Read:
- `{output_dir}/story_map.json` (consolidated stories from all epics)
- `{output_dir}/discovery_brief.md` (personas, problem context)

## Instructions

Analyze all stories and their design needs to produce a complete design system specification.

### 1. Design Tokens

**Color Palette:**
- Primary brand color + 5 shades (50-900)
- Secondary color + 5 shades
- Semantic colors: success, warning, error, info (each with light/default/dark)
- Neutral palette: 10 shades from white to black
- Surface colors: background, card, overlay
- For each color: hex value, usage note, WCAG contrast ratio against its typical background

**Typography Scale:**
- Font families: heading, body, monospace (suggest specific Google Fonts or system fonts)
- Size scale: xs, sm, base, lg, xl, 2xl, 3xl, 4xl (in rem)
- Weight scale: light(300), regular(400), medium(500), semibold(600), bold(700)
- Line height: tight(1.25), normal(1.5), relaxed(1.75)
- Letter spacing: tight(-0.025em), normal(0), wide(0.025em)

**Spacing Scale:**
- Base unit: 4px
- Scale: 0, 1(4px), 2(8px), 3(12px), 4(16px), 5(20px), 6(24px), 8(32px), 10(40px), 12(48px), 16(64px), 20(80px), 24(96px)
- Usage guidelines for each (when to use 4px vs 8px vs 16px)

**Border Radius:**
- none(0), sm(4px), md(8px), lg(12px), xl(16px), full(9999px)

**Shadows:**
- sm: subtle depth for cards
- md: elevated elements (dropdowns, popovers)
- lg: modals, dialogs
- Inner shadow for inset elements
- Exact CSS values for each

**Breakpoints:**
- sm: 640px, md: 768px, lg: 1024px, xl: 1280px, 2xl: 1536px
- For each: typical device category and layout behavior

**Motion:**
- Duration: fast(150ms), normal(300ms), slow(500ms)
- Easing: ease-in, ease-out, ease-in-out, spring
- Reduced motion: all animations must respect prefers-reduced-motion

### 2. Component Inventory

For every component needed by the stories (analyze design_needs fields):

- **Component Name:** PascalCase
- **Description:** What it does and when to use it
- **Variants:** List of visual/behavioral variants (e.g., Button: primary, secondary, ghost, danger)
- **Props:**
  - Name, type, default value, description
  - Required vs optional
- **States:** default, hover, active/pressed, focused, disabled, loading, error
- **Composition:** Can it contain other components? Which ones?
- **Accessibility:**
  - Required ARIA attributes
  - Keyboard interactions (tab order, key handlers)
  - Screen reader announcements
  - Focus management rules
- **Stories Using This Component:** List of story IDs
- **Example Usage:** Short code snippet showing typical usage

Minimum components to define:
- Button, IconButton
- Input, TextArea, Select, Checkbox, Radio, Toggle
- Card, Badge, Tag, Avatar
- Modal, Dialog, Drawer, Popover, Tooltip
- Toast/Notification, Alert, Banner
- Navigation (Navbar, Sidebar, Breadcrumb, Tabs)
- Table, List, Pagination
- Loading (Spinner, Skeleton, Progress)
- Empty State, Error State

### 3. Layout Patterns

- **Page Templates:** Identify distinct page layouts from user journeys
  - For each: wireframe description, grid structure, responsive behavior
- **Grid System:** Column count, gutter width, container max-widths per breakpoint
- **Content Containers:** max-width constraints, padding rules

### 4. Interaction Patterns

- **Forms:** Validation timing (on blur/on submit/real-time), error display, success confirmation
- **Navigation:** Primary/secondary nav patterns, mobile nav, breadcrumbs
- **Feedback:** When to use toast vs inline vs modal for user feedback
- **Loading:** Skeleton vs spinner vs progress bar decision criteria
- **Error Handling:** Error page, inline error, retry patterns
- **Empty States:** First-use, no-results, error-empty guidance

### 5. Accessibility Guidelines

- WCAG 2.1 AA compliance as baseline
- Color contrast: 4.5:1 for normal text, 3:1 for large text
- Focus indicators: visible 2px outline on all interactive elements
- Keyboard navigation: all functionality accessible via keyboard
- Screen readers: semantic HTML, ARIA labels, live regions for dynamic content
- Motion: respect prefers-reduced-motion, provide pause controls for auto-play

## Output

Write to `{output_dir}/phase7_design_system.md` as a well-structured markdown document with all sections above. Use tables for token scales, component inventories, and property definitions. Include CSS custom property names for all tokens (e.g., `--color-primary-500`, `--space-4`).
