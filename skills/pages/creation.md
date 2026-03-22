# Creating Pages Documents From Scratch

## Recommended Approach

For native `.pages` output, use the `create` command followed by `set-body-text`. For broader compatibility, additionally export to `.docx`.

## Creation Workflow

### 1. Create a new document

```bash
# Create with default blank template
python scripts/pages_tool.py create --output report.pages

# Create with a specific template (if available)
python scripts/pages_tool.py create --output report.pages --template "Blank"
```

### 2. Set document content

```bash
# Set the body text
python scripts/pages_tool.py set-body-text report.pages \
  --text "Project Status Report

This document summarizes the current project status.

Key Highlights:
- Milestone 1 completed on schedule
- Budget within 5% of target
- Next review scheduled for April 2026"
```

### 3. Append additional content

```bash
python scripts/pages_tool.py set-body-text report.pages \
  --text "

Conclusion:
The project remains on track for the planned delivery date." \
  --append
```

### 4. Verify content

```bash
python scripts/pages_tool.py dump-text report.pages
python scripts/pages_tool.py get-word-count report.pages
```

### 5. Export and validate

```bash
python scripts/pages_tool.py export report.pages --docx report.docx --pdf report.pdf
python scripts/pages_tool.py render-images report.pages --out-dir rendered
```

## Content Strategy

- Draft the full text content before setting it in Pages.
- Use `set-body-text` for the initial content, then `--append` for additions.
- For documents requiring rich formatting, set the plain text first and note that formatting must be applied manually in Pages.
- Use `replace-text` for subsequent corrections.

## QA Checklist

- Document text is complete and accurate.
- Word count matches expectations.
- Exported `.docx` preserves text content.
- Exported `.pdf` renders correctly.
- No placeholder or draft text remains.

## Notes

- AppleScript text operations produce plain text only; headings, bold, italic, and other formatting must be applied manually in Pages or via a template.
- For complex formatted documents, consider starting from a template and using `replace-text` to update placeholder text.
- The `create` command opens Pages briefly; this is expected behavior.
