# Academic Preset

Structured presentation design for conference talks, thesis defenses, research seminars, and university lectures. Prioritizes clarity, rigor, and data over emotional impact.

## Narrative Architecture

Use the **research narrative** framework:

1. **Motivation** — why this problem matters, who cares
2. **Background** — what has been done, what gap remains
3. **Approach** — your method, why this approach
4. **Results** — what you found, with evidence
5. **Implications** — what it means, what comes next

### Opening (first 60 seconds)
Start with ONE of:
- A real-world example that illustrates the problem
- A key result teaser — "We found that X, which challenges the assumption that Y"
- A question the audience has likely encountered in their own work
- A brief motivating scenario (not a sales pitch)

### Key Message Hierarchy
- **1 main contribution** — the single thing the audience should remember
- **2-3 supporting findings** — evidence that backs the main contribution
- Test: can a colleague summarize your talk in one sentence after hearing it?

### Closing
- Restate the main contribution in one sentence
- Explicitly list limitations (builds credibility)
- Future work as open questions, not promises
- End with "Questions?" slide that shows contact + paper/repo link

## Slide Structure (15-25 slides)

### Introduction (slides 1-4)
| # | Purpose | Layout | Notes |
|---|---------|--------|-------|
| 1 | Title | title | Title, authors, affiliations, venue/date |
| 2 | Motivation | content/image | Why this problem matters. Real-world example |
| 3 | Problem Statement | content | Formal problem definition. Key terms |
| 4 | Outline | content | Talk structure overview (4-5 sections) |

### Background & Related Work (slides 5-7)
| # | Purpose | Layout | Notes |
|---|---------|--------|-------|
| 5 | Related Work | content | Key prior approaches (3-5 papers max) |
| 6 | Gap / Limitation | content | What hasn't been solved. Your niche |
| 7 | Research Questions | content | 1-3 explicit RQs or hypotheses |

### Method (slides 8-12)
| # | Purpose | Layout | Notes |
|---|---------|--------|-------|
| 8 | Approach Overview | split/image | High-level architecture or pipeline diagram |
| 9 | Method Detail 1 | content/code | Key technique, algorithm, or model |
| 10 | Method Detail 2 | content/code | Second key component if needed |
| 11 | Experimental Setup | content | Dataset, metrics, baselines, hardware |
| 12 | Transition | content | "Now let's see what this produces..." |

### Results (slides 13-18)
| # | Purpose | Layout | Notes |
|---|---------|--------|-------|
| 13 | Main Result | data | Hero chart/table. Your strongest finding |
| 14 | Result Detail 1 | data | Breakdown, ablation, or comparison |
| 15 | Result Detail 2 | data | Second angle on results |
| 16 | Qualitative Examples | image | Visual examples, case studies, outputs |
| 17 | Comparison with Baselines | data | Table or chart vs. prior work |
| 18 | Statistical Significance | data | Confidence intervals, p-values if applicable |

### Discussion & Conclusion (slides 19-22)
| # | Purpose | Layout | Notes |
|---|---------|--------|-------|
| 19 | Discussion | content | Interpretation of results. Why it works |
| 20 | Limitations | content | Honest assessment. Shows rigor |
| 21 | Future Work | content | Open questions, next steps |
| 22 | Conclusion | content | Main contribution restated. Key takeaway |

### Closing (slides 23-25)
| # | Purpose | Layout | Notes |
|---|---------|--------|-------|
| 23 | Summary | content | Bullet recap of contributions |
| 24 | References | content | Key citations (5-8 most important) |
| 25 | Questions | title | "Questions?" + contact info + paper/code link |

## Visual Design System

### Color Palette
- **Background:** white (#FFFFFF) or very light gray (#F5F5F7)
- **Primary text:** near-black (#1D1D1F)
- **Accent 1:** institutional/conference color or muted blue (#2563EB)
- **Accent 2:** muted orange or green for secondary data series
- **Muted text:** gray (#6B7280) for captions and sources
- **Code background:** light gray (#F3F4F6)

### Typography
- **Display:** system sans-serif (Helvetica Neue, SF Pro, Calibri)
- **Body:** same family, regular weight
- **Code:** Menlo, SF Mono, or Consolas
- **Headlines:** 36pt Bold
- **Body:** 20pt Regular
- **Code:** 16pt Monospace
- **Citations:** 14pt Regular

### Imagery
- Diagrams and architecture figures (clean, vector-style)
- Plots with clear labels and legends
- Minimal decorative imagery — every image must convey information
- Screenshots of tools/interfaces when relevant

### Data Visualization
- Clear axis labels with units
- Legends outside the plot area when possible
- Error bars or confidence intervals where applicable
- Consistent color mapping across all charts
- Source/citation below each chart
- Prefer bar charts for comparisons, line charts for trends, tables for exact numbers

## Presenter Guidelines

### Pacing (~20 minute conference talk)
| Section | Slides | Time |
|---------|--------|------|
| Introduction | 1-4 | 3 min |
| Background | 5-7 | 3 min |
| Method | 8-12 | 5 min |
| Results | 13-18 | 6 min |
| Discussion + Close | 19-25 | 3 min |

### Academic Presentation Tips
- State your contribution explicitly: "Our main contribution is..."
- When showing related work, explain what each paper does AND what it doesn't do
- For every chart: "This shows X. The key takeaway is Y."
- Anticipate the top 3 questions and prepare backup slides
- Time yourself — conference talks have hard cutoffs
- Speak to the back of the room, not to the slides

### Common Mistakes to Avoid
- Too many slides for the time slot (rule of thumb: 1 slide per minute)
- Unreadable tables (if it has >5 columns or >8 rows, simplify or split)
- Equations without explanation — always give intuition first
- Skipping limitations (reviewers and audience notice)
- "I'll skip this slide" — if you'll skip it, remove it

## Backup Slides (for Q&A)
Prepare 3-5 deep-dive slides:
1. Full results table with all metrics
2. Ablation study details
3. Additional qualitative examples
4. Hyperparameter sensitivity analysis
5. Broader impact / ethical considerations
