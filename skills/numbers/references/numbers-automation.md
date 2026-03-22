# Numbers Automation Notes

## Environment Constraints

- Native `.numbers` operations are supported only on macOS with `Numbers.app` installed.
- AppleScript open is asynchronous; always wait for document count to increase before reading/editing.
- `.numbers` is a ZIP container; direct binary editing is not a stable workflow.
- Numbers hierarchy: `document > sheets > tables > rows > cells`.

## Safe Editing Pattern

1. Copy original file.
2. Apply scripted cell updates to the copy.
3. Export to XLSX/CSV for verification.
4. Compare data before replacing original.

## AppleScript Patterns

### Opening a document
```applescript
tell application "Numbers"
  set docsBefore to count of documents
  open (POSIX file "/path/to/file.numbers") as alias
  repeat while (count of documents) = docsBefore
    delay 0.25
  end repeat
  set d to front document
end tell
```

### Inspecting structure
```applescript
tell application "Numbers"
  tell front document
    set sheetCount to count of sheets
    repeat with i from 1 to sheetCount
      set s to sheet i
      set sName to name of s
      set tableCount to count of tables of s
      repeat with j from 1 to tableCount
        set t to table j of s
        set tName to name of t
        set rCount to row count of t
        set cCount to column count of t
      end repeat
    end repeat
  end tell
end tell
```

### Reading cell values
```applescript
tell application "Numbers"
  tell table 1 of sheet 1 of front document
    set cellVal to value of cell 2 of row 3
  end tell
end tell
```

### Setting cell values
```applescript
tell application "Numbers"
  tell table 1 of sheet 1 of front document
    -- text value
    set value of cell 1 of row 1 to "Header"
    -- numeric value (no quotes)
    set value of cell 2 of row 2 to 42500.75
  end tell
end tell
```

### Adding sheets, rows, columns
```applescript
tell application "Numbers"
  tell front document
    make new sheet at end of sheets with properties {name:"Summary"}
    add row to table 1 of sheet 1
    add column to table 1 of sheet 1
  end tell
end tell
```

### Exporting
```applescript
tell application "Numbers"
  export front document to POSIX file "/path/out.xlsx" as Microsoft Excel
  export front document to POSIX file "/path/out.csv" as CSV
  export front document to POSIX file "/path/out.pdf" as PDF
end tell
```

## Common Failures

- `Invalid index` errors: document not opened yet; add wait loop.
- Export fails silently: verify output path permissions.
- Cell value type mismatch: pass numbers without quotes to keep them numeric.
- Slow performance on large spreadsheets: AppleScript cell iteration is sequential.
- Missing sheet/table: use `inspect` to verify structure before editing.
