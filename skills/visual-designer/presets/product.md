# Product Design System Preset

Full design system for SaaS, web, and mobile products. Follows Apple HIG structure: foundations first, then components, then patterns.

## Input Parameters

Before generating, confirm with the user:

```
Brand/Product:    [name]
Personality:      [minimalist / bold / playful / professional / luxury]
Primary emotion:  [trust / excitement / calm / urgency]
Target audience:  [demographics]
Platform:         [web / iOS / Android / cross-platform]
Existing assets:  [logo colors, fonts, constraints]
```

---

## 1. Foundations

### Color System

Generate a complete palette:

| Token | Purpose | Light Mode | Dark Mode | Contrast (on bg) |
|-------|---------|-----------|-----------|-------------------|
| `primary` | Brand identity, CTAs | hex | hex | AA ratio |
| `primary-hover` | Hover state | hex | hex | — |
| `primary-active` | Pressed state | hex | hex | — |
| `secondary` | Supporting actions | hex | hex | AA ratio |
| `background` | Page background | hex | hex | — |
| `surface` | Cards, panels | hex | hex | — |
| `text-primary` | Main content | hex | hex | AA ratio |
| `text-secondary` | Captions, labels | hex | hex | AA ratio |
| `border` | Dividers, outlines | hex | hex | 3:1 min |
| `success` | Positive feedback | hex | hex | AA ratio |
| `warning` | Caution states | hex | hex | AA ratio |
| `error` | Error feedback | hex | hex | AA ratio |
| `info` | Informational | hex | hex | AA ratio |

**Color rules:**
- Primary color used for maximum 10% of UI surface area
- Never use color as the sole indicator of state
- Dark mode: lighten saturated colors by 15-20% to maintain vibrancy
- Provide each color in hex, RGB, and HSL formats

### Typography

**Font stack:**
```
Primary:    [Selected font], -apple-system, BlinkMacSystemFont, sans-serif
Monospace:  [Selected mono], ui-monospace, "SF Mono", monospace
```

**Type scale:**

| Level | Size (desktop) | Size (mobile) | Weight | Line Height | Letter Spacing | Usage |
|-------|---------------|---------------|--------|-------------|----------------|-------|
| Display | 56px | 40px | Bold (700) | 1.1 | -0.02em | Hero sections |
| Headline 1 | 40px | 32px | Bold (700) | 1.2 | -0.01em | Page titles |
| Headline 2 | 32px | 28px | Semibold (600) | 1.25 | 0 | Section headers |
| Title | 24px | 22px | Semibold (600) | 1.3 | 0 | Card titles |
| Body Large | 18px | 18px | Regular (400) | 1.6 | 0 | Lead paragraphs |
| Body | 16px | 16px | Regular (400) | 1.5 | 0 | Main content |
| Callout | 14px | 14px | Medium (500) | 1.4 | 0.01em | Emphasized small text |
| Caption | 12px | 12px | Regular (400) | 1.4 | 0.02em | Labels, metadata |
| Footnote | 10px | 10px | Regular (400) | 1.3 | 0.02em | Legal, timestamps |

**Rules:**
- Maximum 2 font families per project
- Minimum body size: 16px (web), 17px (iOS), 14sp (Android)
- Line length: 45-75 characters for readability

### Layout Grid

| Breakpoint | Width | Columns | Gutter | Margin |
|-----------|-------|---------|--------|--------|
| Desktop XL | 1440px+ | 12 | 24px | 80px |
| Desktop | 1024-1439px | 12 | 24px | 48px |
| Tablet | 768-1023px | 8 | 16px | 32px |
| Mobile | 375-767px | 4 | 16px | 16px |

### Spacing Scale

```
--space-0:   0px     (none)
--space-1:   4px     (tight — icon gaps, inline elements)
--space-2:   8px     (compact — inside small components)
--space-3:   12px    (comfortable — list items, small padding)
--space-4:   16px    (standard — default component padding)
--space-5:   24px    (relaxed — between related elements)
--space-6:   32px    (loose — between groups)
--space-7:   48px    (spacious — between sections)
--space-8:   64px    (generous — major sections)
--space-9:   96px    (expansive — hero spacing)
--space-10:  128px   (maximum — page-level spacing)
```

### Elevation / Shadows

| Level | Shadow | Usage |
|-------|--------|-------|
| 0 | none | Flat elements |
| 1 | `0 1px 3px rgba(0,0,0,0.1)` | Cards, inputs |
| 2 | `0 4px 12px rgba(0,0,0,0.1)` | Dropdowns, popovers |
| 3 | `0 8px 24px rgba(0,0,0,0.12)` | Modals, floating panels |
| 4 | `0 16px 48px rgba(0,0,0,0.15)` | Full-screen overlays |

### Border Radius

```
--radius-sm:   4px    (inputs, small buttons)
--radius-md:   8px    (cards, panels)
--radius-lg:   12px   (modals, large cards)
--radius-xl:   16px   (hero sections, images)
--radius-full: 9999px (pills, avatars)
```

---

## 2. Components (30+)

For each component, provide:

### Component Spec Template

```
## [Component Name]

**Purpose:** One-line description of when to use this component.

### Anatomy
- [Part 1]: description
- [Part 2]: description

### Variants
- Default / Primary / Secondary / Ghost / Danger

### States
| State | Visual Change |
|-------|--------------|
| Default | base appearance |
| Hover | [describe] |
| Active/Pressed | [describe] |
| Focused | 2px outline, offset 2px, primary color |
| Disabled | 40% opacity, no pointer events |
| Loading | spinner replaces label or shows inline |
| Error | error border color, error text below |

### Sizing
| Size | Height | Padding | Font Size |
|------|--------|---------|-----------|
| Small | 32px | 8px 12px | 14px |
| Medium | 40px | 10px 16px | 16px |
| Large | 48px | 12px 24px | 18px |

### Accessibility
- Role: [ARIA role]
- Keyboard: [Tab, Enter, Space, Escape behaviors]
- Screen reader: [label strategy]

### Do's and Don'ts
- Do: [correct usage]
- Don't: [anti-pattern]
```

### Component Checklist

**Navigation:**
- [ ] Header / App bar
- [ ] Tab bar / Navigation tabs
- [ ] Sidebar / Drawer
- [ ] Breadcrumbs
- [ ] Pagination
- [ ] Bottom navigation (mobile)

**Actions:**
- [ ] Button (primary, secondary, ghost, danger, icon-only, loading)
- [ ] Icon button
- [ ] Link / Text button
- [ ] Floating action button
- [ ] Button group

**Inputs:**
- [ ] Text field (single line, multiline, with prefix/suffix)
- [ ] Select / Dropdown
- [ ] Checkbox
- [ ] Radio button
- [ ] Toggle / Switch
- [ ] Slider / Range
- [ ] Date picker
- [ ] File upload
- [ ] Search field

**Feedback:**
- [ ] Alert / Banner
- [ ] Toast / Snackbar
- [ ] Modal / Dialog
- [ ] Progress bar
- [ ] Progress spinner
- [ ] Skeleton screen
- [ ] Empty state
- [ ] Tooltip

**Data Display:**
- [ ] Card
- [ ] Table
- [ ] List / List item
- [ ] Stat / Metric card
- [ ] Badge / Tag
- [ ] Avatar
- [ ] Divider

**Media:**
- [ ] Image container (with aspect ratio, fallback, loading)
- [ ] Video player
- [ ] Icon (sizing: 16, 20, 24, 32)

---

## 3. Patterns

### Page Templates

Define layout and component composition for:

1. **Landing page** — hero, features, social proof, CTA
2. **Dashboard** — stats bar, charts area, activity feed, sidebar nav
3. **Settings** — sidebar sections, form groups, save/cancel actions
4. **Profile** — avatar, info card, activity tabs
5. **List/Table view** — filters, search, bulk actions, pagination
6. **Detail view** — header, content sections, related items, actions
7. **Authentication** — login, register, forgot password, 2FA
8. **Checkout** — steps, summary, payment, confirmation
9. **Error pages** — 404, 500, maintenance

### User Flow Patterns

For each flow, specify:
- Entry points
- Steps with component composition
- Success state
- Error/edge cases
- Loading states

Key flows:
1. **Onboarding** — welcome → setup → activation → first value
2. **Search & filter** — input → suggestions → results → refinement
3. **CRUD** — create → read → update → delete → confirmation
4. **Notification** — trigger → display → action → dismiss

---

## 4. Design Tokens (JSON)

Output a complete token file:

```json
{
  "color": {
    "primary": { "value": "#___", "type": "color" },
    "primary-hover": { "value": "#___", "type": "color" },
    "primary-active": { "value": "#___", "type": "color" },
    "secondary": { "value": "#___", "type": "color" },
    "background": { "value": "#___", "type": "color" },
    "surface": { "value": "#___", "type": "color" },
    "text-primary": { "value": "#___", "type": "color" },
    "text-secondary": { "value": "#___", "type": "color" },
    "border": { "value": "#___", "type": "color" },
    "success": { "value": "#___", "type": "color" },
    "warning": { "value": "#___", "type": "color" },
    "error": { "value": "#___", "type": "color" },
    "info": { "value": "#___", "type": "color" }
  },
  "spacing": {
    "1": { "value": "4px" },
    "2": { "value": "8px" },
    "3": { "value": "12px" },
    "4": { "value": "16px" },
    "5": { "value": "24px" },
    "6": { "value": "32px" },
    "7": { "value": "48px" },
    "8": { "value": "64px" }
  },
  "typography": {
    "display": {
      "fontFamily": "___",
      "fontSize": "56px",
      "fontWeight": "700",
      "lineHeight": "1.1",
      "letterSpacing": "-0.02em"
    },
    "body": {
      "fontFamily": "___",
      "fontSize": "16px",
      "fontWeight": "400",
      "lineHeight": "1.5",
      "letterSpacing": "0"
    }
  },
  "radius": {
    "sm": { "value": "4px" },
    "md": { "value": "8px" },
    "lg": { "value": "12px" },
    "xl": { "value": "16px" },
    "full": { "value": "9999px" }
  },
  "shadow": {
    "sm": { "value": "0 1px 3px rgba(0,0,0,0.1)" },
    "md": { "value": "0 4px 12px rgba(0,0,0,0.1)" },
    "lg": { "value": "0 8px 24px rgba(0,0,0,0.12)" },
    "xl": { "value": "0 16px 48px rgba(0,0,0,0.15)" }
  }
}
```

---

## 5. Documentation

### Design Principles
Define 3 core principles with examples:

```
1. [Principle Name]
   Definition: One sentence.
   Example: How this applies in the UI.
   Anti-pattern: What violating this looks like.

2. [Principle Name]
   ...

3. [Principle Name]
   ...
```

### Do's and Don'ts (10 minimum)

For each, describe:
- The scenario
- The correct approach (Do)
- The incorrect approach (Don't)
- Why it matters

### Developer Implementation Guide

- Token consumption pattern (CSS custom properties, Tailwind config, or styled-components theme)
- Component API conventions (prop naming, composition patterns)
- Responsive behavior rules
- Animation guidelines (duration: 150-300ms, easing: ease-out for enters, ease-in for exits)
