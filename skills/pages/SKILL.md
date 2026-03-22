---
name: pages
description: "Use this skill any time an Apple Pages file (.pages) is involved as input, output, or both. This includes reading and extracting document text, editing existing documents, creating documents from scratch, exporting Pages to .docx/.pdf/.epub/.txt, and rendering page previews for QA. Trigger whenever the user mentions Pages, .pages, document, word processing, or document work on Apple Pages files."
license: MIT. LICENSE.txt has complete terms
---

# Pages Skill

## Quick Reference

| Task | Guide |
|------|-------|
| Read / analyze a `.pages` document | `python scripts/pages_tool.py inspect document.pages --json` |
| Dump document text | `python scripts/pages_tool.py dump-text document.pages` |
| Get word count | `python scripts/pages_tool.py get-word-count document.pages` |
| Edit existing document | Read [editing.md](editing.md) |
| Create document from scratch | Read [creation.md](creation.md) |
| Export to DOCX / PDF / EPUB / TXT | `python scripts/pages_tool.py export document.pages --docx out.docx --pdf out.pdf` |
| Render page images | `python scripts/pages_tool.py render-images document.pages --out-dir rendered` |

---

## Reading Content

```bash
# Inspect document properties (type, page count, word count)
python scripts/pages_tool.py inspect document.pages --json

# Dump full document text
python scripts/pages_tool.py dump-text document.pages

# Quick word/character count
python scripts/pages_tool.py get-word-count document.pages

# Export for downstream tooling
python scripts/pages_tool.py export document.pages --docx output.docx --pdf output.pdf
```

---

## Editing Workflow

**Read [editing.md](editing.md) for full details.**

1. Inspect document with `inspect` and `dump-text`.
2. Apply edits with `replace-text` or `set-body-text`.
3. Export to `.docx`/`.pdf` and run QA.

---

## Creating From Scratch

**Read [creation.md](creation.md) for full details.**

Use when no template document exists or a new `.pages` file is required.

---

## Command Reference

| Command | Purpose |
|---------|---------|
| `inspect` | Document properties (type, pages, word count, character count) |
| `dump-text` | Extract full document text |
| `get-word-count` | Quick word and character counts |
| `replace-text` | Find/replace text across the document |
| `set-body-text` | Set or append body text (word processing mode) |
| `create` | Create a new Pages document |
| `export` | Export to `.docx`, `.pdf`, `.epub`, and/or `.txt` |
| `render-images` | Page JPEG rendering for QA |

---

## Document Types

Pages supports two document modes:

- **Word Processing**: Standard document with flowing body text. `body text`, `set-body-text`, and `replace-text` work directly on the document body.
- **Page Layout**: Free-form layout with text boxes. Text is accessed via individual text items. `dump-text` and `replace-text` automatically handle both modes.

Use `inspect --json` to check the `document_type` field.

---

## QA (Required)

- Always export edited document to `.docx` and/or `.pdf`.
- Verify text content after edits (`dump-text` or open exported `.docx`).
- Render page images and check layout, spacing, and readability.

```bash
python scripts/pages_tool.py render-images document.pages --out-dir rendered
```

---

## Limitations

- Native `.pages` editing requires macOS + Pages.app.
- Pages automation is not truly headless; the app may launch during operations.
- `set-body-text` only works in word processing mode, not page layout.
- Rich formatting (bold, italic, headings) cannot be applied via AppleScript text operations; only plain text content is modified.
- `.pages` is a ZIP container; direct binary editing is not recommended.

## Dependencies

- Python 3.10+
- macOS with `Pages.app`
- `osascript`
- `pdftoppm` (optional, for image rendering)
