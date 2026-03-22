---
name: visual-designer
description: "Use this skill when the user wants to create a design system, brand guidelines, visual identity, UI kit, or design tokens. This includes defining color palettes, typography scales, spacing systems, component libraries, and developer handoff specifications. Trigger when the user mentions design system, brand colors, style guide, UI components, design tokens, visual identity, or brand guidelines — for any medium (web, mobile, print, presentations)."
license: MIT. LICENSE.txt has complete terms
---

# Design System

Create comprehensive visual design systems — from brand color palettes to full component libraries with design tokens. Follows Apple Human Interface Guidelines principles: clarity, deference, depth.

## Workflow

1. **Gather brand attributes** — ask the user for:
   - Brand / product name
   - Personality: minimalist, bold, playful, professional, luxury
   - Primary emotion: trust, excitement, calm, urgency
   - Target audience
   - Existing brand assets or constraints (logos, colors already in use)
   - Output medium: web app, mobile app, presentations, print, all

2. **Select a preset** — based on scope and medium:
   - [product](presets/product.md) — full design system for SaaS/web/mobile products (foundations + 30+ components + tokens)
   - [brand-identity](presets/brand-identity.md) — brand guidelines for presentations, documents, marketing (colors + typography + imagery + tone)

3. **Generate the system** following the preset's structure.

4. **Output deliverables** — design tokens JSON, component specs, documentation.

## Preset Selection Guide

| Need | Preset | Scope |
|------|--------|-------|
| Building a web/mobile product | `product` | Full: foundations, 30+ components, patterns, tokens, dev handoff |
| Brand guidelines for docs/slides/marketing | `brand-identity` | Light: colors, typography, imagery, tone of voice |
| Both product and brand | Start with `product`, extract `brand-identity` subset | Full + summary |

## Core Design Principles

These apply regardless of preset:

### 1. Clarity
Content is the focus. Every visual element serves a purpose. Remove anything that doesn't help the user accomplish their goal.

### 2. Consistency
Same problems get same solutions. Reuse patterns, maintain predictable behavior, keep spacing and sizing systematic.

### 3. Accessibility First
- WCAG 2.1 AA minimum (4.5:1 text contrast, 3:1 UI elements)
- All interactive elements keyboard-navigable
- Color is never the only indicator of state
- Minimum touch target: 44x44pt

## Foundations Quick Reference

### Color Architecture
```
Primary     → Brand identity, CTAs, key actions
Secondary   → Supporting elements, hover states
Neutral     → Text, backgrounds, borders, dividers
Semantic    → Success (#22C55E), Warning (#F59E0B), Error (#EF4444), Info (#3B82F6)
```

### Spacing Scale (8px base)
```
4  → Tight: inline spacing, icon gaps
8  → Default: padding within small components
12 → Comfortable: list item padding
16 → Standard: card padding, section gaps
24 → Relaxed: between related groups
32 → Loose: between sections
48 → Spacious: major section breaks
64 → Generous: hero spacing
```

### Typography Scale
```
Display    → 48-64pt  Bold      → Hero headlines
Headline   → 32-40pt  Bold      → Page titles
Title      → 24-28pt  Semibold  → Section headers
Body       → 16-18pt  Regular   → Main content
Callout    → 14-16pt  Medium    → Emphasized body
Caption    → 12-14pt  Regular   → Labels, metadata
Footnote   → 10-12pt  Regular   → Legal, timestamps
```

## Design Token Format

Output tokens as JSON for developer handoff:

```json
{
  "color": {
    "primary": { "value": "#007AFF", "type": "color" },
    "primary-hover": { "value": "#0056B3", "type": "color" }
  },
  "spacing": {
    "xs": { "value": "4px", "type": "spacing" },
    "sm": { "value": "8px", "type": "spacing" }
  },
  "typography": {
    "body": {
      "fontFamily": { "value": "Inter", "type": "fontFamily" },
      "fontSize": { "value": "16px", "type": "fontSize" },
      "lineHeight": { "value": "1.5", "type": "lineHeight" }
    }
  }
}
```

## Integration with Other Skills

- **presentation-designer** — use design-system to define the visual language, then presentation-designer for slide narrative and structure
- **keynote / pptx** — apply the design system's colors and typography when building slides
- **frontend-design** — use tokens directly in CSS/Tailwind configuration

## Limitations

- This skill generates specifications and documentation, not visual mockups or Figma files.
- Component specs are code-ready but not actual React/SwiftUI code — adapt to your framework.
- Dark mode palettes are generated algorithmically; always verify contrast ratios manually.
