# Keynote Automation Notes

## Environment Constraints

- Native `.key` operations are supported only on macOS with `Keynote.app` installed.
- AppleScript open is asynchronous; always wait for document count to increase before reading/editing.
- `.key` is a ZIP container with `.iwa` payloads; direct binary editing is not a stable workflow for production updates.

## Safe Editing Pattern

1. Copy original file.
2. Apply scripted text updates to the copy.
3. Export to PDF/PPTX for verification.
4. Compare text and visuals before replacing original.

## Common Failures

- `Invalid index` / `document 1` errors: document not opened yet; add wait loop.
- Export fails silently: verify output path permissions and that Keynote has completed opening the file.
- Missing slide images: `pdftoppm` is not installed.
