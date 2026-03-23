# Tech Talk Preset

Internal engineering meetup and tech talk design for presenting technical work to fellow engineers. Collegial, technical, direct — no marketing BS. Speak engineer-to-engineer.

## Narrative Architecture

Use the **Problem → Context → Solution → Deep Dive → Results → Takeaways** framework:

1. **Problem / Motivation** — what broke, what was missing, what hurt
2. **Context** — why existing solutions didn't work for your case
3. **Solution Overview** — architecture, pipeline, system design at a high level
4. **Deep Dive** — code, configs, interesting technical decisions and tradeoffs
5. **Results** — metrics, before/after, what improved
6. **Takeaways** — lessons learned, useful links, what you'd do differently

### Opening (first 30 seconds)
Start with ONE of:
- The pain point everyone on the team has felt — "You know when X breaks at 3am?"
- A concrete number that shows the problem — "We were losing 40% of events"
- A screenshot of something ugly — a dashboard on fire, an error log, a Slack thread
- A direct statement — "We built X because Y was unacceptable"

### Key Message Hierarchy
- **1 main technical insight** — the core thing the audience should walk away understanding
- **2-3 supporting details** — architecture decisions, tradeoff reasoning, surprising findings
- Test: could a teammate who missed the talk get the point from your slides alone?

### Closing
- Summarize takeaways as a numbered list (3-5 items)
- Share useful links: repo, docs, dashboard, config examples
- End with Q&A slide — your name, team, Slack handle

## Slide Structure (10-15 slides)

### Opening (slides 1-3)
| # | Purpose | Layout | Notes |
|---|---------|--------|-------|
| 1 | Title | title | Talk title, your name, team, date. Keep it short — no corporate subtitle soup |
| 2 | Problem / Motivation | content | What broke or what was missing. Use a real example, screenshot, or error message |
| 3 | Context | content | Why existing tools/solutions didn't solve this. 3-4 bullet points max |

### Solution (slides 4-8)
| # | Purpose | Layout | Notes |
|---|---------|--------|-------|
| 4 | Section Divider | transition | Bold phrase: "Our solution" or the system name |
| 5 | Architecture Overview | image | Pipeline/architecture diagram using colored shapes (see Visual Design) |
| 6 | Architecture Detail | image | Zoom into the most interesting component. Data flow, connections |
| 7 | Code / Config 1 | code | Key code snippet or config. Monospace, syntax-highlighted. Highlight the important lines |
| 8 | Code / Config 2 | code | Second snippet if needed. Show the clever part, not boilerplate |

### Results & Close (slides 9-12)
| # | Purpose | Layout | Notes |
|---|---------|--------|-------|
| 9 | Results / Metrics | data | Big numbers. Before/after comparison. Keep it to 2-4 KPIs |
| 10 | Before/After | split | Side-by-side: old vs. new. Dashboards, latency charts, error rates |
| 11 | Takeaways | content | 3-5 numbered lessons. What you learned, what you'd do differently |
| 12 | Links + Q&A | title | Repo URL, docs, dashboard link. Your name + Slack handle. "Questions?" |

> Adjust to 10-15 slides based on depth needed. Add slides 13-15 for additional deep-dive or demo sections if the topic warrants it.

## Visual Design System

### Color Palette
- **Background:** dark charcoal (#1E1E1E) or VS Code dark (#1E1E2E)
- **Primary text:** off-white (#D4D4D4)
- **Accent — new/custom components:** orange (#E8863A)
- **Accent — databases/storage:** green (#4EC9B0)
- **Accent — dashboards/UI:** blue (#569CD6)
- **Accent — external/existing systems:** gray (#808080)
- **Highlight text:** yellow (#DCDCAA) for emphasis in code and key terms
- **Muted text:** medium gray (#6A6A6A) for captions and sources

### Architecture Diagram Color Convention
Use native shapes (`add-shape` + `style-shape`) with this consistent mapping:
| Color | Hex | Meaning |
|-------|-----|---------|
| Gray | #808080 | External / existing systems |
| Orange | #E8863A | New / custom-built components |
| Green | #4EC9B0 | Databases, storage, queues |
| Blue | #569CD6 | Dashboards, UI, monitoring |

Arrows between components: white (#D4D4D4) or light gray, 2pt weight.

### Typography
- **Display/Headlines:** system sans-serif (SF Pro, Helvetica Neue, Calibri) — 36pt Bold
- **Body:** same family — 20pt Regular
- **Code:** SF Mono, Menlo, Consolas, or JetBrains Mono — 16-18pt
- **Metrics/KPI numbers:** 48-72pt Bold
- **Captions:** 14pt Regular

### Code Slides
- Dark background matching the slide background
- Monospace font, 16-18pt
- Use syntax-highlighting colors: keywords in blue (#569CD6), strings in orange (#CE9178), comments in green (#6A9955), functions in yellow (#DCDCAA)
- Highlight key lines with a subtle lighter background strip or a left-border accent
- Maximum 15-20 lines of code per slide — if it's longer, split or simplify
- Add a brief title above the code block explaining what the audience is looking at

### Metrics Slides
- Hero numbers: 48-72pt Bold, accent color
- Minimal surrounding text — one line of context per number
- Before/after layout: old number on the left (muted gray), new number on the right (green or orange)
- Use arrows or delta indicators (▲ ▼) for change direction

### Section Dividers
- Bold short phrase centered on dark background
- 44pt Bold, white text
- Optional: thin accent-colored line above or below the phrase

## Slide Types Unique to Tech Talks

### Architecture Diagram
- Built with native shapes (`add-shape` + `style-shape`), not imported images
- Colored boxes per the convention above
- Labels inside or below each box
- Arrows showing data flow direction
- Keep to 5-8 components max per diagram — split into overview + detail if more

### Code Walkthrough
- Monospace font on dark background
- Key lines highlighted with a subtle background color or border
- Title explains what the code does
- Speaker notes walk through the logic line by line

### Before/After Comparison
- Split layout: left = before, right = after
- Use the same metric/visual in both halves for direct comparison
- Label clearly: "Before" / "After" or specific dates
- Highlight the improvement with accent color

### Pipeline / Flow Diagram
- Horizontal or vertical flow of colored boxes connected by arrows
- Each box: component name + brief role (3-5 words)
- Show data flow direction with arrow labels if needed

### Metrics / KPI Highlight
- 1-3 big numbers per slide
- Each number: value + unit + one-line context
- Use accent colors to draw attention to the most important metric

## Presenter Guidelines

### Pacing (~12 minute talk)
| Section | Slides | Time |
|---------|--------|------|
| Title + Problem + Context | 1-3 | 2 min |
| Solution overview | 4-6 | 3 min |
| Deep dive (code/config) | 7-8 | 3 min |
| Results + Takeaways + Q&A | 9-12 | 4 min |

### Tech Talk Tips
- Know your audience's baseline — skip basics your team already knows
- For code slides: don't read the code aloud line-by-line. Explain the intent, then point to the key lines
- For architecture diagrams: walk through the data flow, not the box labels
- Anticipate "why didn't you use X?" questions — have a one-sentence answer ready for each alternative you considered
- If you have a live demo, keep it under 2 minutes and have a screenshot fallback
- Speak in concrete specifics, not abstractions — "latency dropped from 800ms to 120ms" beats "performance improved significantly"

### Common Mistakes to Avoid
- Too much code — show only the interesting parts, link to the repo for the rest
- No context for metrics — a number means nothing without a baseline or comparison
- Spending too long on "how it was before" — the audience gets it faster than you think
- Skipping the "why not X?" question — address alternatives proactively
- Walls of text — if a slide has more than 5 bullet points, split it

## Backup Slides (for Q&A)
Prepare 2-3 deep-dive slides:
1. Full architecture with all edge cases and error handling
2. Performance benchmarks with methodology details
3. Alternative approaches you evaluated and why you rejected them
