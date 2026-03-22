# Editing Numbers Spreadsheets

## Template-Based Workflow

When editing an existing `.numbers` file:

1. **Inspect structure**
   ```bash
   python scripts/numbers_tool.py inspect spreadsheet.numbers --json
   python scripts/numbers_tool.py dump-data spreadsheet.numbers --format csv
   ```

2. **Plan edits before mutation**
   - Identify target sheet, table, row, and column indices.
   - Decide in-place vs copy-edit (`--output`).

3. **Apply cell edits**
   ```bash
   # Set a specific cell value
   python scripts/numbers_tool.py set-cell spreadsheet.numbers \
     --sheet 1 --table 1 --row 1 --column 1 --value "Revenue" \
     --output edited.numbers

   # Set a numeric value (auto-detected)
   python scripts/numbers_tool.py set-cell edited.numbers \
     --row 2 --column 2 --value "42500.75"

   # Global find/replace across all cells
   python scripts/numbers_tool.py replace-text spreadsheet.numbers \
     --find "2025" --replace "2026" \
     --output edited.numbers
   ```

4. **Structural edits**
   ```bash
   # Add a new sheet
   python scripts/numbers_tool.py add-sheet edited.numbers --name "Summary"

   # Add rows to a table
   python scripts/numbers_tool.py add-row edited.numbers --sheet 1 --table 1 --count 5

   # Add columns
   python scripts/numbers_tool.py add-column edited.numbers --sheet 1 --table 1 --count 2
   ```

5. **Export and verify**
   ```bash
   python scripts/numbers_tool.py export edited.numbers --xlsx edited.xlsx --csv edited.csv
   ```

6. **Visual QA**
   ```bash
   python scripts/numbers_tool.py render-images edited.numbers --out-dir rendered
   ```

## Script Reference

| Command | Purpose |
|---------|---------|
| `inspect` | Sheet/table inventory with dimensions |
| `dump-data` | Extract cell values as CSV, TSV, or JSON |
| `set-cell` | Set a specific cell value |
| `replace-text` | Find/replace text across all cells |
| `add-sheet` | Add a new sheet |
| `add-row` | Add row(s) to a table |
| `add-column` | Add column(s) to a table |
| `export` | Export to `.xlsx`, `.csv`, and/or `.pdf` |
| `render-images` | Sheet JPEG rendering for QA |

## Editing Rules

- Prefer `--output` to avoid destructive edits.
- Use `set-cell` for individual cell updates; use `replace-text` for bulk string changes.
- Numeric values are auto-detected: `"42500"` is set as a number, `"Revenue"` as text.
- Always validate by exported artifacts, not just script success output.
- Be careful when editing formula cells: setting a value overwrites the formula.

## Common Pitfalls

- **Document not opened yet**: Numbers automation is async; script already waits.
- **Formula cells**: Setting a value on a formula cell replaces the formula with a static value.
- **Merged cells**: Merged cell ranges may behave unexpectedly; inspect structure first.
- **Large spreadsheets**: Iterating all cells via AppleScript can be slow for thousands of rows.
- **UI interruption**: Numbers may launch briefly; this is expected for native automation.
