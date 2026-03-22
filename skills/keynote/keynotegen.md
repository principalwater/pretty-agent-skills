# Creating Keynote Decks From Scratch

## Recommended Approach

For native `.key` output, use Apple Keynote automation. For broader compatibility, additionally export `.pptx`.

## Minimal Creation Workflow

1. Create initial deck in Keynote (manually or from an empty starter deck).
2. Use `replace-text` and repeated edit cycles for structured content insertion.
3. Export and validate.

```bash
python scripts/keynote_tool.py export draft.key --pptx draft.pptx --pdf draft.pdf
python scripts/keynote_tool.py render-images draft.key --out-dir rendered
```

## Layout Strategy

- Build one strong visual system early (type scale, spacing, color).
- Reuse master-like patterns consistently.
- Keep text editable; avoid flattening text into images.

## Content Strategy

- Start from slide outline (title, section, data, summary).
- Fill text blocks with concise copy first.
- Add graphics and charts after text fit is stable.

## QA Checklist

- No clipped text.
- No overlapping elements.
- Adequate margin from slide edges.
- Contrast is readable.
- Exported `.pptx` preserves essential structure.

## Notes

- Unlike `.pptx` authoring with PptxGenJS, native Keynote automation is app-driven and tied to macOS.
- Fully headless creation is not currently reliable with native `.key` files.
