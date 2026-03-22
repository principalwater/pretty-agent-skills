# Creating Keynote Decks From Scratch

## Recommended Approach

For native `.key` output, use the `create` command followed by structural and content commands. For broader compatibility, additionally export to `.pptx`.

## Creation Workflow

### 1. Choose a theme

```bash
# List available themes
python scripts/keynote_tool.py list-themes

# Create a new deck with a chosen theme
python scripts/keynote_tool.py create --output deck.key --theme "Gradient"
```

### 2. Build slide structure

```bash
# Add slides with specific layouts
python scripts/keynote_tool.py add-slide deck.key --layout "Title - Center"
python scripts/keynote_tool.py add-slide deck.key --layout "Title & Bullets"
python scripts/keynote_tool.py add-slide deck.key --layout "Title & Bullets"
python scripts/keynote_tool.py add-slide deck.key --layout "Blank"
```

### 3. Populate content

```bash
# Set text on each slide (use inspect first to find item indices)
python scripts/keynote_tool.py inspect deck.key --json

python scripts/keynote_tool.py set-text deck.key --slide 1 --item 1 --text "Project Update"
python scripts/keynote_tool.py set-text deck.key --slide 1 --item 2 --text "Q1 2026 Review"
python scripts/keynote_tool.py set-text deck.key --slide 2 --item 1 --text "Key Achievements"
```

### 4. Add presenter notes

```bash
python scripts/keynote_tool.py set-notes deck.key --slide 1 --text "Welcome everyone..."
python scripts/keynote_tool.py set-notes deck.key --slide 2 --text "Highlight the three main wins"
```

### 5. Add images

```bash
python scripts/keynote_tool.py add-image deck.key \
  --slide 4 --image chart.png --x 100 --y 80 --width 800 --height 500
```

### 6. Export and validate

```bash
python scripts/keynote_tool.py export deck.key --pptx deck.pptx --pdf deck.pdf
python scripts/keynote_tool.py render-images deck.key --out-dir rendered
```

## Layout Strategy

- Build one strong visual system early (type scale, spacing, color).
- Reuse master-like patterns consistently.
- Keep text editable; avoid flattening text into images.
- Use `list-themes` to pick a theme that matches the tone of the presentation.

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
