# Creating Numbers Spreadsheets From Scratch

## Recommended Approach

For native `.numbers` output, use the `create` command followed by structural and cell-setting commands. For broader compatibility, additionally export to `.xlsx`.

## Creation Workflow

### 1. Create a new spreadsheet

```bash
python scripts/numbers_tool.py create --output data.numbers
```

### 2. Set up headers

```bash
# Inspect default structure (1 sheet, 1 table)
python scripts/numbers_tool.py inspect data.numbers --json

# Set header row
python scripts/numbers_tool.py set-cell data.numbers --row 1 --column 1 --value "Name"
python scripts/numbers_tool.py set-cell data.numbers --row 1 --column 2 --value "Department"
python scripts/numbers_tool.py set-cell data.numbers --row 1 --column 3 --value "Salary"
```

### 3. Populate data

```bash
python scripts/numbers_tool.py set-cell data.numbers --row 2 --column 1 --value "Alice"
python scripts/numbers_tool.py set-cell data.numbers --row 2 --column 2 --value "Engineering"
python scripts/numbers_tool.py set-cell data.numbers --row 2 --column 3 --value "95000"

python scripts/numbers_tool.py set-cell data.numbers --row 3 --column 1 --value "Bob"
python scripts/numbers_tool.py set-cell data.numbers --row 3 --column 2 --value "Marketing"
python scripts/numbers_tool.py set-cell data.numbers --row 3 --column 3 --value "82000"
```

### 4. Add additional sheets if needed

```bash
python scripts/numbers_tool.py add-sheet data.numbers --name "Summary"
```

### 5. Expand tables as needed

```bash
python scripts/numbers_tool.py add-row data.numbers --sheet 1 --table 1 --count 10
python scripts/numbers_tool.py add-column data.numbers --sheet 1 --table 1 --count 2
```

### 6. Export and validate

```bash
python scripts/numbers_tool.py export data.numbers --xlsx data.xlsx --pdf data.pdf
python scripts/numbers_tool.py render-images data.numbers --out-dir rendered
```

## Layout Strategy

- Use clear header rows with descriptive column names.
- Keep one data topic per sheet.
- Name sheets and tables descriptively.
- Separate input data from derived/summary data (different sheets or tables).

## Content Strategy

- Set headers first, then populate data row by row.
- Use numeric values for calculations (the script auto-detects numbers).
- For large datasets, consider preparing data externally and importing via `.csv`.
- Add formulas manually in Numbers after structural setup if needed.

## QA Checklist

- All headers are present and spelled correctly.
- Numeric columns contain numbers, not text.
- No empty rows in the middle of data ranges.
- Exported `.xlsx` preserves data integrity.
- Sheet and table names are descriptive.
