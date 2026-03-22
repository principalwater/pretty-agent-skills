---
name: keynote
description: "Use this skill any time an Apple Keynote file (.key) is involved as input, output, or both. This includes reading and extracting slide text, editing existing Keynote decks, creating decks from scratch, exporting Keynote to .pptx/.pdf, and rendering slide previews for QA. Trigger whenever the user mentions Keynote, .key, slides, deck, or presentation work on Apple Keynote files."
license: MIT. LICENSE.txt has complete terms
---

# Keynote Skill

## Quick Reference

| Task | Guide |
|------|-------|
| Read / analyze a `.key` deck | `python scripts/keynote_tool.py inspect presentation.key --json` |
| Dump text by slide | `python scripts/keynote_tool.py dump-text presentation.key` |
| Get slide count | `python scripts/keynote_tool.py get-slide-count presentation.key` |
| Read presenter notes | `python scripts/keynote_tool.py get-notes presentation.key --json` |
| List master layouts | `python scripts/keynote_tool.py list-masters presentation.key --json` |
| Edit existing Keynote deck | Read [editing.md](editing.md) |
| Create deck from scratch | Read [creation.md](creation.md) |
| List available themes | `python scripts/keynote_tool.py list-themes` |
| Export to PPTX / PDF | `python scripts/keynote_tool.py export presentation.key --pptx out.pptx --pdf out.pdf` |
| Render slide images | `python scripts/keynote_tool.py render-images presentation.key --out-dir rendered` |
| Render specific slides | `python scripts/keynote_tool.py render-images presentation.key --out-dir rendered --slides 3,6-8` |

---

## Reading Content

```bash
# Inspect slide structure, layouts, and text item counts
python scripts/keynote_tool.py inspect presentation.key --json

# Dump text grouped by slide (includes layout names)
python scripts/keynote_tool.py dump-text presentation.key

# Quick slide count
python scripts/keynote_tool.py get-slide-count presentation.key

# Read presenter notes (all slides or specific)
python scripts/keynote_tool.py get-notes presentation.key --json
python scripts/keynote_tool.py get-notes presentation.key --slide 3

# List available master slide layouts (essential for template-based work)
python scripts/keynote_tool.py list-masters presentation.key --json

# Export for downstream tooling
python scripts/keynote_tool.py export presentation.key --pptx output.pptx --pdf output.pdf
```

---

## Editing Workflow

**Read [editing.md](editing.md) for full details.**

1. Inspect slide structure with `inspect` and `dump-text`.
2. Apply targeted edits with `replace-text`, `set-text`, `format-text`, or structural commands.
3. Export to `.pdf`/`.pptx` and run visual/content QA.

---

## Creating From Scratch

**Read [creation.md](creation.md) for full details.**

Use when no template deck exists or when a new native `.key` deck is required.
For **template-based** workflows (corporate templates), see the template section in [creation.md](creation.md).

---

## Command Reference

| Command | Purpose |
|---------|---------|
| `inspect` | Slide count, layout names, and text-item inventory |
| `dump-text` | Human-readable text by slide with layout info |
| `get-slide-count` | Quick slide count |
| `get-notes` | Read presenter notes |
| `set-notes` | Write presenter notes |
| `replace-text` | Find/replace text across all text items |
| `set-text` | Set text of a specific text item on a specific slide |
| `format-text` | Set font, size, and/or color of a text item |
| `add-text-item` | Create a new text box on a slide with optional formatting |
| `add-slide` | Add a new slide (optional position and layout) |
| `delete-slide` | Delete a slide by index |
| `add-image` | Insert an image on a slide with optional position/size |
| `list-themes` | List available Keynote themes |
| `list-masters` | List master slide layouts in a document |
| `create` | Create a new empty Keynote document |
| `export` | Export `.key` to `.pptx` and/or `.pdf` |
| `render-images` | Slide image rendering for QA (supports selective slides) |

---

## Design Guidelines

### Color Strategy

- Use 2-3 accent colors plus a neutral background.
- Pick colors from the Keynote theme palette for consistency.
- Ensure sufficient contrast between text and background (4.5:1 minimum).

### Typography

| Element | Font Size | Weight |
|---------|-----------|--------|
| Slide title | 36-44 pt | Bold |
| Section header | 28-32 pt | Bold |
| Body text | 18-24 pt | Regular |
| Code blocks | 14-20 pt | Monospace (Menlo, SF Mono) |
| Captions / footnotes | 12-14 pt | Regular or Light |

- Limit each slide to 2 font families maximum.
- Use the theme's default fonts unless there is a specific reason to override.
- For code slides: use `format-text --font "Menlo" --color "#FFFFFF"` on Code master layouts.

### Layout

- Keep a 40-60 pt margin from all slide edges.
- Align elements to a consistent grid.
- Place one key idea per slide; avoid visual clutter.
- Use visual elements (images, shapes, charts) on most slides to maintain engagement.

---

## QA (Required)

- Always export edited deck to `.pdf` and/or `.pptx`.
- Verify text content after edits (`dump-text` or `markitdown` on exported `.pptx`).
- Render slide images and inspect overlap, clipping, and spacing.
- Use `--slides` to render only changed slides and conserve resources.

```bash
# Render all slides
python scripts/keynote_tool.py render-images presentation.key --out-dir rendered

# Render only specific slides (saves time and tokens)
python scripts/keynote_tool.py render-images presentation.key --out-dir rendered --slides 3,6-8
```

---

## Limitations

- Native `.key` editing requires macOS + Keynote.app.
- Keynote automation is not truly headless; the app may still launch or briefly appear during operations.
- Script avoids forced app focus (`activate`) to reduce UI interruption, but macOS may still surface windows.
- Some master layouts have **linked text items** (e.g., Code layout links t1 and t3). Use `add-text-item` to create independent text boxes when needed.

## Dependencies

- Python 3.10+
- macOS with `Keynote.app`
- `osascript`
- `pdftoppm` (optional, for image rendering)
