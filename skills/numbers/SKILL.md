---
name: numbers
description: "Use this skill any time an Apple Numbers file (.numbers) is involved as input, output, or both. This includes reading and extracting cell data, editing existing spreadsheets, creating spreadsheets from scratch, exporting Numbers to .xlsx/.csv/.pdf, and rendering sheet previews for QA. Trigger whenever the user mentions Numbers, .numbers, spreadsheet, or tabular data work on Apple Numbers files."
license: MIT. LICENSE.txt has complete terms
---

# Numbers Skill

## Quick Reference

| Task | Guide |
|------|-------|
| Read / analyze a `.numbers` file | `python scripts/numbers_tool.py inspect spreadsheet.numbers --json` |
| Dump cell data | `python scripts/numbers_tool.py dump-data spreadsheet.numbers --format csv` |
| Edit existing spreadsheet | Read [editing.md](editing.md) |
| Create spreadsheet from scratch | Read [creation.md](creation.md) |
| Export to XLSX / CSV / PDF | `python scripts/numbers_tool.py export spreadsheet.numbers --xlsx out.xlsx` |
| Render sheet images | `python scripts/numbers_tool.py render-images spreadsheet.numbers --out-dir rendered` |

---

## Reading Content

```bash
# Inspect sheet/table structure
python scripts/numbers_tool.py inspect spreadsheet.numbers --json

# Dump cell data as CSV
python scripts/numbers_tool.py dump-data spreadsheet.numbers --format csv

# Dump specific sheet and table as TSV
python scripts/numbers_tool.py dump-data spreadsheet.numbers --sheet 1 --table 1 --format tsv

# Dump as JSON
python scripts/numbers_tool.py dump-data spreadsheet.numbers --format json --max-rows 50

# Export for downstream tooling
python scripts/numbers_tool.py export spreadsheet.numbers --xlsx output.xlsx --csv output.csv
```

---

## Editing Workflow

**Read [editing.md](editing.md) for full details.**

1. Inspect structure with `inspect` and `dump-data`.
2. Apply edits with `set-cell`, `replace-text`, or structural commands.
3. Export to `.xlsx`/`.csv`/`.pdf` and run QA.

---

## Creating From Scratch

**Read [creation.md](creation.md) for full details.**

Use when no template spreadsheet exists or a new `.numbers` file is required.

---

## Command Reference

| Command | Purpose |
|---------|---------|
| `inspect` | Sheet/table inventory with row and column counts |
| `dump-data` | Extract cell values as CSV, TSV, or JSON |
| `set-cell` | Set a specific cell value (auto-detects numeric) |
| `replace-text` | Find/replace text across all cells in all tables |
| `add-sheet` | Add a new sheet |
| `add-row` | Add row(s) to a table |
| `add-column` | Add column(s) to a table |
| `create` | Create a new empty Numbers document |
| `export` | Export to `.xlsx`, `.csv`, and/or `.pdf` |
| `render-images` | Sheet JPEG rendering for QA |

---

## QA (Required)

- Always export edited spreadsheet to `.xlsx` or `.csv`.
- Verify cell data after edits (`dump-data` or open exported `.xlsx`).
- Check that formulas have been recalculated by Numbers after value changes.

```bash
python scripts/numbers_tool.py render-images spreadsheet.numbers --out-dir rendered
```

---

## Limitations

- Native `.numbers` editing requires macOS + Numbers.app.
- Numbers automation is not truly headless; the app may launch during operations.
- Formulas are computed by Numbers, not by the script; formula-dependent cells update only when Numbers recalculates.
- `.numbers` is a ZIP container; direct binary editing is not recommended.

## Dependencies

- Python 3.10+
- macOS with `Numbers.app`
- `osascript`
- `pdftoppm` (optional, for image rendering)
