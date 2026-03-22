---
name: keynote
description: "Use this skill any time an Apple Keynote file (.key) is involved as input, output, or both. This includes reading and extracting slide text, editing existing Keynote decks, creating decks from scratch, exporting Keynote to .pptx/.pdf, and rendering slide previews for QA. Trigger whenever the user mentions Keynote, .key, slides, deck, or presentation work on Apple Keynote files."
license: MIT. LICENSE.txt has complete terms
---

# Keynote Skill

## Quick Reference

| Task | Guide |
|------|-------|
| Read/analyze a `.key` deck | `python scripts/keynote_tool.py inspect presentation.key --json` |
| Edit existing Keynote deck | Read [editing.md](editing.md) |
| Create deck from scratch | Read [keynotegen.md](keynotegen.md) |

---

## Reading Content

```bash
# Inspect slide structure and text item counts
python scripts/keynote_tool.py inspect presentation.key --json

# Dump text grouped by slide
python scripts/keynote_tool.py dump-text presentation.key

# Export for downstream tooling
python scripts/keynote_tool.py export presentation.key --pptx output.pptx --pdf output.pdf
```

---

## Editing Workflow

**Read [editing.md](editing.md) for full details.**

1. Inspect slide structure with `inspect` and `dump-text`.
2. Apply targeted edits with `replace-text` (prefer writing to `--output`).
3. Export to `.pdf`/`.pptx` and run visual/content QA.

---

## Creating From Scratch

**Read [keynotegen.md](keynotegen.md) for full details.**

Use when no template deck exists or when a new native `.key` deck is required.

---

## QA (Required)

- Always export edited deck to `.pdf` and/or `.pptx`.
- Verify text content after edits (`dump-text` or `markitdown` on exported `.pptx`).
- Render slide images and inspect overlap, clipping, and spacing.

```bash
# Render slide images from .key
python scripts/keynote_tool.py render-images presentation.key --out-dir rendered
```

## Converting To Images

`render-images` exports temporary PDF then runs `pdftoppm`.

```bash
python scripts/keynote_tool.py render-images presentation.key --out-dir slides --dpi 150
```

## Limitations

- Native `.key` editing requires macOS + Keynote.app.
- Keynote automation is not truly headless; the app may still launch or briefly appear during operations.
- Script avoids forced app focus (`activate`) to reduce UI interruption, but macOS may still surface windows.

## Dependencies

- Python 3.10+
- macOS with `Keynote.app`
- `osascript`
- `pdftoppm` (optional, for image rendering)
