---
name: presentation-designer
description: "Use this skill when the user wants to plan, structure, or design a presentation before building it. This includes choosing a narrative arc, defining slide-by-slide specifications, selecting a visual design system, and writing speaker notes. Trigger when the user mentions presentation planning, slide outline, talk structure, pitch deck design, or asks to design/plan a presentation (as opposed to building the .key/.pptx file itself)."
license: MIT. LICENSE.txt has complete terms
---

# Presentation Designer

Plan and structure presentations before building them. This skill produces a detailed blueprint — narrative arc, slide specs, visual system, speaker notes — that you then execute with the `keynote` or `pptx` skill.

## Workflow

1. **Gather requirements** — ask the user for:
   - Topic / purpose
   - Audience (executives, investors, academic, team, general)
   - Duration (minutes)
   - Objective (inform, persuade, inspire, educate)
   - Existing template or brand constraints

2. **Select a preset** — based on audience and objective, read the matching preset:
   - [business-pitch](presets/business-pitch.md) — executive/investor decks, Apple-style impact
   - [academic](presets/academic.md) — conference talks, research presentations, lectures

3. **Generate the blueprint** following the preset's structure. Output:
   - Narrative architecture (story arc, opening hook, key messages, CTA)
   - Slide-by-slide specs (title, layout type, copy, speaker notes)
   - Visual design system (colors, typography, imagery style)
   - Presenter guidelines (pacing, transitions, interaction moments)

4. **Hand off to build skill** — once the user approves the blueprint, use `keynote` or `pptx` skill to create the actual file.

## Preset Selection Guide

| Audience / Goal | Preset | Key Characteristics |
|----------------|--------|-------------------|
| Investors, C-suite, customers | `business-pitch` | Emotional impact, minimal text, dark backgrounds, 20-30 slides |
| Conference, academic defense, lecture | `academic` | Data-driven, structured sections, light backgrounds, 15-25 slides |

## Slide Spec Format

For each slide in the blueprint, provide:

```
### Slide N: [Title]
- **Layout:** title / content / data / image / split / quote / transition / code
- **Headline:** (6 words max)
- **Body:** (25 words max)
- **Visual:** description of imagery, chart, or diagram
- **Speaker notes:** (60-90 seconds of spoken content)
- **Build/transition:** (animation notes if any)
```

## General Design Principles

- Every slide must earn its place — if it doesn't advance the narrative, cut it.
- One idea per slide. No walls of text.
- Headlines tell the story — a reader skimming only headlines should understand the arc.
- Data needs context — never show a number without comparison or trend.
- Contrast drives attention — use size, color, and whitespace deliberately.
- Speaker notes carry the detail — slides are visual anchors, not teleprompters.

## Typography Guidelines

| Element | Size Range | Weight |
|---------|-----------|--------|
| Slide title | 36-48 pt | Bold |
| Section header | 28-36 pt | Bold |
| Body text | 18-24 pt | Regular |
| Data callout | 48-72 pt | Bold |
| Caption / source | 12-14 pt | Light |
| Code | 14-20 pt | Monospace |

## Color Strategy

- **2-3 accent colors** + neutral background
- Dark background (dark gray, not pure black) for emotional impact presentations
- Light background (white or off-white) for data-heavy or academic presentations
- One highlight color for emphasis — use sparingly
- Ensure 4.5:1 contrast ratio minimum for readability

## Limitations

- This skill plans presentations; it does not create .key or .pptx files directly.
- For file creation, hand off to `keynote` (native .key) or `pptx` (.pptx) skill.
- Presets are starting points — always adapt to the user's specific needs and brand.
