#!/usr/bin/env python3
"""Automate Apple Numbers (.numbers) files via AppleScript.

Commands:
- inspect
- dump-data
- set-cell
- replace-text
- add-sheet
- add-row
- add-column
- create
- export
- render-images
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TableInfo:
    index: int
    name: str
    row_count: int = 0
    column_count: int = 0


@dataclass
class SheetInfo:
    index: int
    name: str
    tables: list[TableInfo] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_macos() -> None:
    if sys.platform != "darwin":
        raise RuntimeError("This tool requires macOS because it automates Numbers via AppleScript.")


def _require_osascript() -> None:
    if shutil.which("osascript") is None:
        raise RuntimeError("`osascript` not found. Install Xcode Command Line Tools or verify PATH.")


def _escape_apple_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _run_osascript(script: str) -> str:
    proc = subprocess.run(
        ["osascript", "-"],
        input=script,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.strip() or "Unknown AppleScript error"
        raise RuntimeError(stderr)
    return proc.stdout.strip()


def _build_opening_block(in_path: Path) -> str:
    """AppleScript block that opens a .numbers file and sets ``d`` to the front document.

    Handles already-open documents by checking name + POSIX path before attempting open.
    """
    in_path_escaped = _escape_apple_string(str(in_path.resolve()))
    in_name = _escape_apple_string(in_path.name)
    return f'''
set inPath to "{in_path_escaped}"
set inName to "{in_name}"
set inAlias to (POSIX file inPath) as alias

tell application "Numbers"
  set alreadyOpen to false
  repeat with existingDoc in documents
    try
      if name of existingDoc is inName then
        set hfsPath to file of existingDoc as text
        set posixFromHfs to POSIX path of (hfsPath as alias)
        if posixFromHfs is inPath then
          set d to existingDoc
          set alreadyOpen to true
          exit repeat
        end if
      end if
    end try
  end repeat
  if not alreadyOpen then
    set docsBefore to count of documents
    open inAlias
    set waited to 0
    repeat while (count of documents) = docsBefore and waited < 120
      delay 0.25
      set waited to waited + 1
    end repeat
    if (count of documents) = docsBefore then error "Failed to open Numbers document"
    set d to front document
  end if
'''


def _build_app_only_block() -> str:
    """AppleScript block that addresses Numbers without opening a document."""
    return '''
tell application "Numbers"
'''


def _build_common_handlers() -> str:
    return r'''
on replaceAll(sourceText, findText, replacementText)
  if findText is "" then return sourceText
  set oldTID to AppleScript's text item delimiters
  set AppleScript's text item delimiters to findText
  set chunks to text items of sourceText
  set AppleScript's text item delimiters to replacementText
  set outputText to chunks as text
  set AppleScript's text item delimiters to oldTID
  return outputText
end replaceAll

on sanitizeText(sourceText)
  set t1 to my replaceAll(sourceText, return, " ")
  set t2 to my replaceAll(t1, linefeed, " ")
  set t3 to my replaceAll(t2, tab, " ")
  return t3
end sanitizeText
'''


def _prepare_output(args: argparse.Namespace) -> Path:
    """If ``--output`` is set, copy input there and return the copy path; otherwise return input."""
    if not hasattr(args, "output") or not args.output:
        return args.input
    target = args.output
    if target.resolve() != args.input.resolve():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.input, target)
    return target


def _resolve_sheet_index(arg_value: str | None) -> str:
    """Return AppleScript expression for sheet selection. Accepts index (int) or name."""
    if arg_value is None:
        return "1"
    try:
        return str(int(arg_value))
    except ValueError:
        return f'(name of every sheet of d)'  # caller handles by name


def _sheet_accessor(arg_value: str | None) -> str:
    """Return AppleScript accessor like ``sheet 1 of d`` or ``sheet \"Name\" of d``."""
    if arg_value is None:
        return "sheet 1 of d"
    try:
        idx = int(arg_value)
        return f"sheet {idx} of d"
    except ValueError:
        escaped = _escape_apple_string(arg_value)
        return f'sheet "{escaped}" of d'


def _table_accessor(arg_value: str | None, sheet_expr: str) -> str:
    """Return AppleScript accessor for a table within a sheet expression."""
    if arg_value is None:
        return f"table 1 of {sheet_expr}"
    try:
        idx = int(arg_value)
        return f"table {idx} of {sheet_expr}"
    except ValueError:
        escaped = _escape_apple_string(arg_value)
        return f'table "{escaped}" of {sheet_expr}'


# ---------------------------------------------------------------------------
# Core AppleScript operations
# ---------------------------------------------------------------------------

def _collect_structure(in_path: Path) -> dict[str, Any]:
    script = (
        _build_opening_block(in_path)
        + r'''
  set sheetCount to count of sheets of d
  set outputText to "SHEETS" & tab & sheetCount & linefeed

  repeat with i from 1 to sheetCount
    set s to sheet i of d
    set sName to name of s
    set tableCount to count of tables of s
    set outputText to outputText & "SHEET" & tab & i & tab & sName & tab & tableCount & linefeed

    repeat with j from 1 to tableCount
      set t to table j of s
      set tName to name of t
      set rCount to row count of t
      set cCount to column count of t
      set outputText to outputText & "TABLE" & tab & i & tab & j & tab & tName & tab & rCount & tab & cCount & linefeed
    end repeat
  end repeat

  close d saving no
  return outputText
end tell
'''
    )

    raw = _run_osascript(script)
    sheets: dict[int, SheetInfo] = {}
    sheet_count = 0

    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        tag = parts[0]
        if tag == "SHEETS" and len(parts) >= 2:
            sheet_count = int(parts[1])
        elif tag == "SHEET" and len(parts) >= 4:
            idx = int(parts[1])
            sheets[idx] = SheetInfo(index=idx, name=parts[2], tables=[])
        elif tag == "TABLE" and len(parts) >= 6:
            sheet_idx = int(parts[1])
            table_idx = int(parts[2])
            sheet = sheets.get(sheet_idx)
            if sheet is not None:
                sheet.tables.append(
                    TableInfo(
                        index=table_idx,
                        name=parts[3],
                        row_count=int(parts[4]),
                        column_count=int(parts[5]),
                    )
                )

    ordered = [sheets[i] for i in sorted(sheets)]
    return {
        "sheet_count": sheet_count,
        "sheets": [
            {
                "index": s.index,
                "name": s.name,
                "tables": [
                    {
                        "index": t.index,
                        "name": t.name,
                        "row_count": t.row_count,
                        "column_count": t.column_count,
                    }
                    for t in s.tables
                ],
            }
            for s in ordered
        ],
    }


def _dump_data(
    in_path: Path,
    sheet: str | None,
    table: str | None,
    max_rows: int | None,
) -> list[list[str]]:
    sheet_expr = _sheet_accessor(sheet)
    table_expr = _table_accessor(table, sheet_expr)

    limit_clause = ""
    if max_rows is not None:
        limit_clause = f"""
    if i > {max_rows} then exit repeat"""

    script = (
        _build_opening_block(in_path)
        + f'''
  set t to {table_expr}
  set rCount to row count of t
  set cCount to column count of t
  set outputText to ""

  repeat with i from 1 to rCount{limit_clause}
    set rowText to ""
    repeat with j from 1 to cCount
      try
        set cellVal to value of cell j of row i of t
        if cellVal is missing value then
          set cellStr to ""
        else
          set cellStr to cellVal as string
        end if
      on error
        set cellStr to ""
      end try
      set cellStr to my sanitizeText(cellStr)
      if j > 1 then set rowText to rowText & tab
      set rowText to rowText & cellStr
    end repeat
    set outputText to outputText & rowText & linefeed
  end repeat

  close d saving no
  return outputText
end tell
'''
        + _build_common_handlers()
    )

    raw = _run_osascript(script)
    rows: list[list[str]] = []
    for line in raw.splitlines():
        if line == "":
            continue
        rows.append(line.split("\t"))
    return rows


def _set_cell(
    in_path: Path,
    sheet: str | None,
    table: str | None,
    row: int,
    column: int,
    value: str,
) -> None:
    sheet_expr = _sheet_accessor(sheet)
    table_expr = _table_accessor(table, sheet_expr)

    # Auto-detect numeric values
    try:
        float(value)
        val_expr = value
    except ValueError:
        val_escaped = _escape_apple_string(value)
        val_expr = f'"{val_escaped}"'

    script = (
        _build_opening_block(in_path)
        + f'''
  set value of cell {column} of row {row} of {table_expr} to {val_expr}
  save d
  close d saving yes
  return "OK"
end tell
'''
    )
    _run_osascript(script)


def _replace_text_numbers(in_path: Path, find_text: str, replace_text: str) -> int:
    find_escaped = _escape_apple_string(find_text)
    replace_escaped = _escape_apple_string(replace_text)

    script = (
        _build_opening_block(in_path)
        + f'''
  set findText to "{find_escaped}"
  set replText to "{replace_escaped}"
  set changedCount to 0

  repeat with s in sheets of d
    repeat with t in tables of s
      set rCount to row count of t
      set cCount to column count of t
      repeat with i from 1 to rCount
        repeat with j from 1 to cCount
          try
            set cellVal to value of cell j of row i of t
            if cellVal is not missing value then
              set cellStr to cellVal as string
              if cellStr contains findText then
                set newVal to my replaceAll(cellStr, findText, replText)
                set value of cell j of row i of t to newVal
                set changedCount to changedCount + 1
              end if
            end if
          end try
        end repeat
      end repeat
    end repeat
  end repeat

  save d
  close d saving yes
  return "UPDATED" & tab & changedCount
end tell
'''
        + _build_common_handlers()
    )

    raw = _run_osascript(script)
    parts = raw.split("\t")
    if len(parts) == 2 and parts[0] == "UPDATED":
        return int(parts[1])
    raise RuntimeError(f"Unexpected response from AppleScript: {raw}")


def _add_sheet(in_path: Path, name: str | None) -> str:
    name_prop = ""
    if name:
        name_escaped = _escape_apple_string(name)
        name_prop = f' with properties {{name:"{name_escaped}"}}'
    script = (
        _build_opening_block(in_path)
        + f'''
  set newSheet to make new sheet at end of sheets of d{name_prop}
  set sheetName to name of newSheet
  save d
  close d saving yes
  return sheetName
end tell
'''
    )
    return _run_osascript(script)


def _add_row(in_path: Path, sheet: str | None, table: str | None, count: int) -> int:
    sheet_expr = _sheet_accessor(sheet)
    table_expr = _table_accessor(table, sheet_expr)
    script = (
        _build_opening_block(in_path)
        + f'''
  set t to {table_expr}
  repeat {count} times
    add row to t
  end repeat
  set newRowCount to row count of t
  save d
  close d saving yes
  return newRowCount
end tell
'''
    )
    return int(_run_osascript(script))


def _add_column(in_path: Path, sheet: str | None, table: str | None, count: int) -> int:
    sheet_expr = _sheet_accessor(sheet)
    table_expr = _table_accessor(table, sheet_expr)
    script = (
        _build_opening_block(in_path)
        + f'''
  set t to {table_expr}
  repeat {count} times
    add column to t
  end repeat
  set newColCount to column count of t
  save d
  close d saving yes
  return newColCount
end tell
'''
    )
    return int(_run_osascript(script))


def _create_document(output_path: Path) -> None:
    out_escaped = _escape_apple_string(str(output_path.resolve()))
    script = (
        _build_app_only_block()
        + f'''
  set d to make new document
  save d in POSIX file "{out_escaped}"
  close d saving yes
  return "OK"
end tell
'''
    )
    _run_osascript(script)


def _export(in_path: Path, xlsx_path: Path | None, csv_path: Path | None, pdf_path: Path | None) -> None:
    parts: list[str] = []
    if xlsx_path:
        xlsx_escaped = _escape_apple_string(str(xlsx_path.resolve()))
        parts.append(f'''
  export d to POSIX file "{xlsx_escaped}" as Microsoft Excel''')
    if csv_path:
        csv_escaped = _escape_apple_string(str(csv_path.resolve()))
        parts.append(f'''
  export d to POSIX file "{csv_escaped}" as CSV''')
    if pdf_path:
        pdf_escaped = _escape_apple_string(str(pdf_path.resolve()))
        parts.append(f'''
  export d to POSIX file "{pdf_escaped}" as PDF''')

    script = (
        _build_opening_block(in_path)
        + "".join(parts)
        + '''
  close d saving no
  return "OK"
end tell
'''
    )
    _run_osascript(script)


# ---------------------------------------------------------------------------
# CLI command handlers
# ---------------------------------------------------------------------------

def cmd_inspect(args: argparse.Namespace) -> int:
    data = _collect_structure(args.input)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    print(f"Sheets: {data['sheet_count']}")
    for sheet in data["sheets"]:
        print(f"\nSheet {sheet['index']}: {sheet['name']}")
        for table in sheet["tables"]:
            print(f"  Table {table['index']}: {table['name']} ({table['row_count']} rows x {table['column_count']} cols)")
    return 0


def cmd_dump_data(args: argparse.Namespace) -> int:
    rows = _dump_data(args.input, args.sheet, args.table, args.max_rows)

    fmt = args.format
    if fmt == "json":
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif fmt == "tsv":
        for row in rows:
            print("\t".join(row))
    else:  # csv
        writer = csv.writer(sys.stdout)
        for row in rows:
            writer.writerow(row)
    return 0


def cmd_set_cell(args: argparse.Namespace) -> int:
    target = _prepare_output(args)
    _set_cell(target, args.sheet, args.table, args.row, args.column, args.value)
    print(f"Set cell row={args.row} col={args.column}")
    print(f"Target file: {target}")
    return 0


def cmd_replace_text(args: argparse.Namespace) -> int:
    target = _prepare_output(args)
    updated = _replace_text_numbers(target, args.find, args.replace)
    print(f"Updated cells: {updated}")
    print(f"Target file: {target}")
    return 0


def cmd_add_sheet(args: argparse.Namespace) -> int:
    target = _prepare_output(args)
    sheet_name = _add_sheet(target, args.name)
    print(f"Added sheet: {sheet_name}")
    print(f"Target file: {target}")
    return 0


def cmd_add_row(args: argparse.Namespace) -> int:
    target = _prepare_output(args)
    new_count = _add_row(target, args.sheet, args.table, args.count)
    print(f"Added {args.count} row(s). Total rows: {new_count}")
    print(f"Target file: {target}")
    return 0


def cmd_add_column(args: argparse.Namespace) -> int:
    target = _prepare_output(args)
    new_count = _add_column(target, args.sheet, args.table, args.count)
    print(f"Added {args.count} column(s). Total columns: {new_count}")
    print(f"Target file: {target}")
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    _create_document(args.output)
    print(f"Created: {args.output}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    if not args.xlsx and not args.csv and not args.pdf:
        raise RuntimeError("Provide at least one target: --xlsx, --csv, and/or --pdf")

    if args.xlsx:
        args.xlsx.parent.mkdir(parents=True, exist_ok=True)
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
    if args.pdf:
        args.pdf.parent.mkdir(parents=True, exist_ok=True)

    _export(args.input, args.xlsx, args.csv, args.pdf)
    if args.xlsx:
        print(f"Exported XLSX: {args.xlsx}")
    if args.csv:
        print(f"Exported CSV: {args.csv}")
    if args.pdf:
        print(f"Exported PDF: {args.pdf}")
    return 0


def cmd_render_images(args: argparse.Namespace) -> int:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("`pdftoppm` not found. Install poppler to use render-images.")

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="numbers_render_") as tmp:
        pdf_path = Path(tmp) / "render.pdf"
        _export(args.input, None, None, pdf_path)
        prefix = out_dir / "sheet"
        proc = subprocess.run(
            [pdftoppm, "-jpeg", "-r", str(args.dpi), str(pdf_path), str(prefix)],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or "pdftoppm failed")

    print(f"Rendered images into: {out_dir}")
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automate Apple Numbers spreadsheets (.numbers)")
    sub = parser.add_subparsers(dest="command", required=True)

    # --- inspect ---
    p_inspect = sub.add_parser("inspect", help="Inspect sheet/table structure")
    p_inspect.add_argument("input", type=Path, help="Path to .numbers file")
    p_inspect.add_argument("--json", action="store_true", help="Print JSON output")
    p_inspect.set_defaults(func=cmd_inspect)

    # --- dump-data ---
    p_dump = sub.add_parser("dump-data", help="Extract cell data from a table")
    p_dump.add_argument("input", type=Path, help="Path to .numbers file")
    p_dump.add_argument("--sheet", default=None, help="Sheet index (1-based) or name")
    p_dump.add_argument("--table", default=None, help="Table index (1-based) or name")
    p_dump.add_argument("--format", choices=["csv", "tsv", "json"], default="csv", help="Output format (default: csv)")
    p_dump.add_argument("--max-rows", type=int, default=None, help="Limit output to first N rows")
    p_dump.set_defaults(func=cmd_dump_data)

    # --- set-cell ---
    p_set = sub.add_parser("set-cell", help="Set value of a specific cell")
    p_set.add_argument("input", type=Path, help="Path to .numbers file")
    p_set.add_argument("--sheet", default=None, help="Sheet index or name")
    p_set.add_argument("--table", default=None, help="Table index or name")
    p_set.add_argument("--row", type=int, required=True, help="Row index (1-based)")
    p_set.add_argument("--column", type=int, required=True, help="Column index (1-based)")
    p_set.add_argument("--value", required=True, help="Cell value (auto-detects numeric)")
    p_set.add_argument("--output", type=Path, help="Optional output file (copy + edit)")
    p_set.set_defaults(func=cmd_set_cell)

    # --- replace-text ---
    p_replace = sub.add_parser("replace-text", help="Find/replace text across all cells")
    p_replace.add_argument("input", type=Path, help="Path to .numbers file")
    p_replace.add_argument("--find", required=True, help="Text to find")
    p_replace.add_argument("--replace", required=True, help="Replacement text")
    p_replace.add_argument("--output", type=Path, help="Optional output file (copy + edit)")
    p_replace.set_defaults(func=cmd_replace_text)

    # --- add-sheet ---
    p_add_sheet = sub.add_parser("add-sheet", help="Add a new sheet")
    p_add_sheet.add_argument("input", type=Path, help="Path to .numbers file")
    p_add_sheet.add_argument("--name", default=None, help="Sheet name")
    p_add_sheet.add_argument("--output", type=Path, help="Optional output file (copy + edit)")
    p_add_sheet.set_defaults(func=cmd_add_sheet)

    # --- add-row ---
    p_add_row = sub.add_parser("add-row", help="Add row(s) to a table")
    p_add_row.add_argument("input", type=Path, help="Path to .numbers file")
    p_add_row.add_argument("--sheet", default=None, help="Sheet index or name")
    p_add_row.add_argument("--table", default=None, help="Table index or name")
    p_add_row.add_argument("--count", type=int, default=1, help="Number of rows to add (default: 1)")
    p_add_row.add_argument("--output", type=Path, help="Optional output file (copy + edit)")
    p_add_row.set_defaults(func=cmd_add_row)

    # --- add-column ---
    p_add_col = sub.add_parser("add-column", help="Add column(s) to a table")
    p_add_col.add_argument("input", type=Path, help="Path to .numbers file")
    p_add_col.add_argument("--sheet", default=None, help="Sheet index or name")
    p_add_col.add_argument("--table", default=None, help="Table index or name")
    p_add_col.add_argument("--count", type=int, default=1, help="Number of columns to add (default: 1)")
    p_add_col.add_argument("--output", type=Path, help="Optional output file (copy + edit)")
    p_add_col.set_defaults(func=cmd_add_column)

    # --- create ---
    p_create = sub.add_parser("create", help="Create a new Numbers document")
    p_create.add_argument("--output", type=Path, required=True, help="Output .numbers file path")
    p_create.set_defaults(func=cmd_create)

    # --- export ---
    p_export = sub.add_parser("export", help="Export Numbers to XLSX/CSV/PDF")
    p_export.add_argument("input", type=Path, help="Path to .numbers file")
    p_export.add_argument("--xlsx", type=Path, help="Output .xlsx path")
    p_export.add_argument("--csv", type=Path, help="Output .csv path")
    p_export.add_argument("--pdf", type=Path, help="Output .pdf path")
    p_export.set_defaults(func=cmd_export)

    # --- render-images ---
    p_render = sub.add_parser("render-images", help="Render sheet images via PDF + pdftoppm")
    p_render.add_argument("input", type=Path, help="Path to .numbers file")
    p_render.add_argument("--out-dir", type=Path, required=True, help="Output directory for JPEG images")
    p_render.add_argument("--dpi", type=int, default=150, help="Render DPI (default: 150)")
    p_render.set_defaults(func=cmd_render_images)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    try:
        _require_macos()
        _require_osascript()
        parser = build_parser()
        args = parser.parse_args()
        if hasattr(args, "input") and not args.input.exists():
            raise RuntimeError(f"Input file does not exist: {args.input}")
        return int(args.func(args))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
