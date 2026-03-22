# Editing Keynote Presentations

## Template-Based Workflow

When editing an existing `.key` deck:

1. **Inspect structure and text**
   ```bash
   python scripts/keynote_tool.py inspect template.key --json
   python scripts/keynote_tool.py dump-text template.key
   ```

2. **Plan edits before mutation**
   - Identify exact phrases to replace.
   - Decide in-place vs copy-edit (`--output`).

3. **Apply text edits**
   ```bash
   python scripts/keynote_tool.py replace-text template.key \
     --find "Old phrase" \
     --replace "New phrase" \
     --output edited.key
   ```

4. **Export and verify**
   ```bash
   python scripts/keynote_tool.py export edited.key --pdf edited.pdf --pptx edited.pptx
   python -m markitdown edited.pptx
   ```

5. **Visual QA**
   ```bash
   python scripts/keynote_tool.py render-images edited.key --out-dir rendered
   ```

## Script Reference

| Script | Purpose |
|--------|---------|
| `scripts/keynote_tool.py inspect` | Slide count and text-item inventory |
| `scripts/keynote_tool.py dump-text` | Human-readable text by slide |
| `scripts/keynote_tool.py replace-text` | Replace text across text items |
| `scripts/keynote_tool.py export` | Export `.key` to `.pptx` and/or `.pdf` |
| `scripts/keynote_tool.py render-images` | Slide JPEG rendering for QA |

## Editing Rules

- Prefer `--output` to avoid destructive edits.
- Keep replacements precise; broad replace can alter repeated labels or hidden text items.
- Always validate by exported artifacts, not just script success output.

## Common Pitfalls

- **Document not opened yet**: Keynote automation is async; script already waits.
- **Unexpected repeated replacements**: same phrase can exist in multiple text items and duplicated layers.
- **UI interruption**: Keynote may launch briefly; this is expected for native `.key` automation.
