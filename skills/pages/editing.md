# Editing Pages Documents

## Template-Based Workflow

When editing an existing `.pages` document:

1. **Inspect document**
   ```bash
   python scripts/pages_tool.py inspect document.pages --json
   python scripts/pages_tool.py dump-text document.pages
   python scripts/pages_tool.py get-word-count document.pages
   ```

2. **Plan edits before mutation**
   - Check the document type (word processing vs page layout).
   - Identify exact phrases to replace.
   - Decide in-place vs copy-edit (`--output`).

3. **Apply text edits**
   ```bash
   # Global find/replace
   python scripts/pages_tool.py replace-text document.pages \
     --find "Draft" \
     --replace "Final" \
     --output edited.pages

   # Replace body text entirely (word processing mode)
   python scripts/pages_tool.py set-body-text document.pages \
     --text "New document content here." \
     --output edited.pages

   # Append text to existing body
   python scripts/pages_tool.py set-body-text document.pages \
     --text "\n\nAdditional paragraph." \
     --append
   ```

4. **Export and verify**
   ```bash
   python scripts/pages_tool.py export edited.pages --docx edited.docx --pdf edited.pdf
   ```

5. **Visual QA**
   ```bash
   python scripts/pages_tool.py render-images edited.pages --out-dir rendered
   ```

## Script Reference

| Command | Purpose |
|---------|---------|
| `inspect` | Document properties and metadata |
| `dump-text` | Extract full document text |
| `get-word-count` | Word and character counts |
| `replace-text` | Find/replace across the document |
| `set-body-text` | Set or append body text |
| `export` | Export to `.docx`, `.pdf`, `.epub`, `.txt` |
| `render-images` | Page JPEG rendering for QA |

## Editing Rules

- Prefer `--output` to avoid destructive edits.
- Use `replace-text` for targeted changes; use `set-body-text` only when replacing the entire content.
- `set-body-text` strips all formatting; use only when plain text replacement is acceptable.
- Always validate by exported artifacts, not just script success output.

## Common Pitfalls

- **Document not opened yet**: Pages automation is async; script already waits.
- **Page layout documents**: `set-body-text` does not work in page layout mode; use `replace-text` instead.
- **Formatting loss**: Setting body text replaces all rich formatting with plain text.
- **UI interruption**: Pages may launch briefly; this is expected for native automation.
- **Large documents**: AppleScript text operations on very large documents may be slow.
