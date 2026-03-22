# Creating Keynote Decks

## Two Approaches

1. **From scratch** — use `create --theme` to start with a blank Keynote theme.
2. **From template** — copy a corporate/custom `.key` template, discover its layouts, then build slides using those layouts.

---

## Approach 1: From Scratch

### 1. Choose a theme

```bash
python scripts/keynote_tool.py list-themes
python scripts/keynote_tool.py create --output deck.key --theme "Gradient"
```

### 2. Build slide structure

```bash
python scripts/keynote_tool.py add-slide deck.key --layout "Title - Center"
python scripts/keynote_tool.py add-slide deck.key --layout "Title & Bullets"
python scripts/keynote_tool.py add-slide deck.key --layout "Blank"
```

### 3. Continue with [Populate Content](#populate-content) below.

---

## Approach 2: From Corporate Template (Recommended)

When you have a corporate or custom `.key` template with predefined master layouts, colors, fonts, and branding:

### 1. Copy the template

```bash
cp "Corporate Template.key" presentation.key
```

### 2. Discover available master layouts

```bash
python scripts/keynote_tool.py list-masters presentation.key --json
```

This returns all master slides with their names and indices. Example output:
```
1: Title
9: Title & Photo Alt
11: Title & Bullets
22: Title Only
24: Code
25: Statement
27: Many Fact
30: finish
```

### 3. Inspect template example slides

```bash
python scripts/keynote_tool.py inspect presentation.key --json
```

This shows each slide's layout name, text item count, and text content. Use this to understand which text items correspond to titles, subtitles, body text, etc.

### 4. Plan your slide mapping

Map your content to the template's master layouts:

| Your Slide | Template Layout | Why |
|-----------|----------------|-----|
| Title | Title | Branded title with logo |
| Key point | Statement | Centered impactful text |
| Architecture | Title Only | Clean white for diagrams |
| Code demo | Code | Dark background for code |
| Metrics | Many Fact | 3-column numbers layout |
| Thank you | finish | Branded closing |

### 5. Delete template examples, add your slides

```bash
# Delete template's example slides (from last to first to keep indices stable)
python scripts/keynote_tool.py delete-slide presentation.key --index 18
python scripts/keynote_tool.py delete-slide presentation.key --index 17
# ... continue until all example slides are removed

# Add your slides with the right layouts
python scripts/keynote_tool.py add-slide presentation.key --layout "Title"
python scripts/keynote_tool.py add-slide presentation.key --layout "Statement"
python scripts/keynote_tool.py add-slide presentation.key --layout "Title Only"
python scripts/keynote_tool.py add-slide presentation.key --layout "Code"
```

### 6. Continue with [Populate Content](#populate-content) below.

---

## Populate Content

### Set text on slides

```bash
# Inspect to find text item indices
python scripts/keynote_tool.py inspect presentation.key --json

# Set text by slide and item index
python scripts/keynote_tool.py set-text presentation.key --slide 1 --item 1 --text "Project Update"
python scripts/keynote_tool.py set-text presentation.key --slide 1 --item 2 --text "Q1 2026 Review"
```

### Format text (font, size, color)

```bash
# Set monospace white font for code slides
python scripts/keynote_tool.py format-text presentation.key \
  --slide 6 --item 3 --font "Menlo" --size 18 --color "#FFFFFF"
```

### Add new text boxes

When master layout text items are insufficient (e.g., Code layout has linked items), create independent text boxes:

```bash
python scripts/keynote_tool.py add-text-item presentation.key \
  --slide 6 --text "def main():\n    print('hello')" \
  --x 60 --y 160 --width 1800 --height 800 \
  --font "Menlo" --size 18 --color "#FFFFFF"
```

### Add presenter notes

```bash
python scripts/keynote_tool.py set-notes presentation.key --slide 1 --text "Welcome everyone..."
```

### Add images

```bash
python scripts/keynote_tool.py add-image presentation.key \
  --slide 4 --image chart.png --x 100 --y 80 --width 800 --height 500
```

### Export and validate

```bash
python scripts/keynote_tool.py export presentation.key --pptx deck.pptx --pdf deck.pdf
python scripts/keynote_tool.py render-images presentation.key --out-dir rendered --slides 1,3,6
```

## Layout Strategy

- Build one strong visual system early (type scale, spacing, color).
- Reuse master-like patterns consistently.
- Keep text editable; avoid flattening text into images.
- Use `list-masters` to discover all available layouts before building.

## Content Strategy

- Start from a slide outline (title, section, data, summary).
- Fill text blocks with concise copy first.
- Add graphics and charts after text fit is stable.
- Use presenter notes for speaking points rather than cramming text onto slides.

## QA Checklist

- No clipped text.
- No overlapping elements.
- Adequate margin from slide edges.
- Contrast is readable.
- Exported `.pptx` preserves essential structure.
- Presenter notes are complete.

## Notes

- Unlike `.pptx` authoring with PptxGenJS, native Keynote automation is app-driven and tied to macOS.
- The `create` command opens Keynote briefly to generate the file; this is expected behavior.
- Theme names are case-sensitive; use `list-themes` to get exact names.
- Layout names are case-sensitive; use `list-masters` to get exact names.
