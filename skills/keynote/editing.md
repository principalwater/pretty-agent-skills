# Editing Keynote Presentations

## Template-Based Workflow

When editing an existing `.key` deck:

1. **Inspect structure and text**
   ```bash
   python scripts/keynote_tool.py inspect template.key --json
   python scripts/keynote_tool.py dump-text template.key
   python scripts/keynote_tool.py get-notes template.key --json
   ```

2. **Plan edits before mutation**
   - Identify exact phrases to replace or specific slide/item indices to update.
   - Decide in-place vs copy-edit (`--output`).

3. **Apply text edits**
   ```bash
   # Global find/replace
   python scripts/keynote_tool.py replace-text template.key \
     --find "Old phrase" \
     --replace "New phrase" \
     --output edited.key

   # Set a specific text item directly
   python scripts/keynote_tool.py set-text template.key \
     --slide 1 --item 2 --text "New Title" \
     --output edited.key

   # Format text (font, size, color)
   python scripts/keynote_tool.py format-text edited.key \
     --slide 6 --item 3 --font "Menlo" --size 18 --color "#FFFFFF"

   # Add a new text box (useful when master text items are linked)
   python scripts/keynote_tool.py add-text-item edited.key \
     --slide 6 --text "code here" \
     --x 60 --y 160 --width 1800 --height 800

   # Update presenter notes
   python scripts/keynote_tool.py set-notes edited.key \
     --slide 1 --text "Speaker notes here"
   ```

4. **Structural edits**
   ```bash
   # Add a slide at the end using a specific layout
   python scripts/keynote_tool.py add-slide edited.key --layout "Title & Bullets"

   # Add a slide at position 2
   python scripts/keynote_tool.py add-slide edited.key --position 2

   # Delete slide 5
   python scripts/keynote_tool.py delete-slide edited.key --index 5

   # Insert an image
   python scripts/keynote_tool.py add-image edited.key \
     --slide 1 --image logo.png --x 50 --y 50 --width 200
   ```

5. **Export and verify**
   ```bash
   python scripts/keynote_tool.py export edited.key --pdf edited.pdf --pptx edited.pptx
   python -m markitdown edited.pptx
   ```

6. **Visual QA**
   ```bash
   python scripts/keynote_tool.py render-images edited.key --out-dir rendered
   ```

## Script Reference

| Command | Purpose |
|---------|---------|
| `inspect` | Slide count, layouts, and text-item inventory |
| `dump-text` | Human-readable text by slide with layout info |
| `get-slide-count` | Quick slide count |
| `get-notes` | Read presenter notes |
| `set-notes` | Write presenter notes for a slide |
| `replace-text` | Find/replace text across all text items |
| `set-text` | Set text of a specific text item on a specific slide |
| `format-text` | Set font, size, and/or color of a text item |
| `add-text-item` | Create a new text box on a slide with optional formatting |
| `add-slide` | Add a new slide with optional position and layout |
| `delete-slide` | Delete a slide by index |
| `add-image` | Insert an image on a slide |
| `list-masters` | List master slide layouts in a document |
| `export` | Export `.key` to `.pptx` and/or `.pdf` |
| `render-images` | Slide JPEG rendering for QA (supports `--slides` filter) |

## Editing Rules

- Prefer `--output` to avoid destructive edits.
- Use `set-text` for precise single-item changes; use `replace-text` for global find/replace.
- Keep replacements precise; broad replace can alter repeated labels or hidden text items.
- Always validate by exported artifacts, not just script success output.

## Common Pitfalls

- **Document not opened yet**: Keynote automation is async; script already waits and handles already-open documents.
- **Unexpected repeated replacements**: same phrase can exist in multiple text items and duplicated layers.
- **UI interruption**: Keynote may launch briefly; this is expected for native `.key` automation.
- **Invalid slide/item index**: Use `inspect --json` first to discover valid indices.
- **Image positioning**: If `--x`/`--y` are omitted, Keynote places the image at its default position.
- **Linked text items on master layouts**: Some layouts (e.g., Code) have text items that mirror each other. Setting text on one changes the other. Use `add-text-item` to create independent text boxes when needed.
- **Code slides need manual formatting**: When using Code master layout, new text items may inherit the title's font/color. Always use `format-text` to set monospace font and appropriate color.
