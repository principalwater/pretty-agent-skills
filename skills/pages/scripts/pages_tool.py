#!/usr/bin/env python3
"""Automate Apple Pages (.pages) files via AppleScript.

Commands:
- inspect
- dump-text
- replace-text
- set-body-text
- get-word-count
- create
- export
- render-images
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_macos() -> None:
    if sys.platform != "darwin":
        raise RuntimeError("This tool requires macOS because it automates Pages via AppleScript.")


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
    """AppleScript block that opens a .pages file and sets ``d`` to the front document.

    Handles already-open documents by checking name + POSIX path before attempting open.
    """
    in_path_escaped = _escape_apple_string(str(in_path.resolve()))
    in_name = _escape_apple_string(in_path.name)
    return f'''
set inPath to "{in_path_escaped}"
set inName to "{in_name}"
set inAlias to (POSIX file inPath) as alias

tell application "Pages"
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
    if (count of documents) = docsBefore then error "Failed to open Pages document"
    set d to front document
  end if
'''


def _build_app_only_block() -> str:
    """AppleScript block that addresses Pages without opening a document."""
    return '''
tell application "Pages"
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


# ---------------------------------------------------------------------------
# Core AppleScript operations
# ---------------------------------------------------------------------------

def _inspect(in_path: Path) -> dict[str, Any]:
    script = (
        _build_opening_block(in_path)
        + r'''
  set docName to name of d

  -- Detect document type
  set docType to "word-processing"
  try
    set bt to body text of d
  on error
    set docType to "page-layout"
  end try

  set pCount to count of pages of d
  set wCount to word count of d
  set cCount to character count of d

  -- Count text items (available in page-layout mode, also present in word-processing)
  set tiCount to 0
  try
    set tiCount to count of text items of d
  end try

  set outputText to "NAME" & tab & docName & linefeed
  set outputText to outputText & "TYPE" & tab & docType & linefeed
  set outputText to outputText & "PAGES" & tab & pCount & linefeed
  set outputText to outputText & "WORDS" & tab & wCount & linefeed
  set outputText to outputText & "CHARS" & tab & cCount & linefeed
  set outputText to outputText & "TEXTITEMS" & tab & tiCount & linefeed

  close d saving no
  return outputText
end tell
'''
    )

    raw = _run_osascript(script)
    result: dict[str, Any] = {}

    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 1)
        if len(parts) < 2:
            continue
        tag, val = parts
        if tag == "NAME":
            result["name"] = val
        elif tag == "TYPE":
            result["document_type"] = val
        elif tag == "PAGES":
            result["page_count"] = int(val)
        elif tag == "WORDS":
            result["word_count"] = int(val)
        elif tag == "CHARS":
            result["character_count"] = int(val)
        elif tag == "TEXTITEMS":
            result["text_item_count"] = int(val)

    return result


def _dump_text(in_path: Path) -> str:
    # Try word-processing mode first (body text), fall back to text items
    script = (
        _build_opening_block(in_path)
        + r'''
  set outputText to ""
  try
    set bt to body text of d
    set outputText to "BODYTEXT" & linefeed & bt
  on error
    -- Page layout mode: iterate text items
    set tiCount to count of text items of d
    set outputText to "TEXTITEMS" & tab & tiCount & linefeed
    repeat with i from 1 to tiCount
      try
        set t to (object text of text item i of d) as string
      on error
        set t to ""
      end try
      set outputText to outputText & "ITEM" & tab & i & tab & t & linefeed
    end repeat
  end try

  close d saving no
  return outputText
end tell
'''
    )

    raw = _run_osascript(script)
    lines = raw.splitlines()

    if lines and lines[0] == "BODYTEXT":
        return "\n".join(lines[1:])

    # Page layout mode
    result_parts: list[str] = []
    for line in lines:
        parts = line.split("\t", 2)
        if parts[0] == "ITEM" and len(parts) >= 3:
            result_parts.append(f"[Text Item {parts[1]}] {parts[2]}")
    return "\n".join(result_parts)


def _replace_text_pages(in_path: Path, find_text: str, replace_text: str) -> int:
    find_escaped = _escape_apple_string(find_text)
    replace_escaped = _escape_apple_string(replace_text)

    # Try word-processing mode, then page-layout
    script = (
        _build_opening_block(in_path)
        + f'''
  set findText to "{find_escaped}"
  set replText to "{replace_escaped}"
  set changedCount to 0

  -- Try word-processing mode (body text)
  try
    set bt to body text of d
    if bt contains findText then
      set newBt to my replaceAll(bt, findText, replText)
      set body text of d to newBt
      set changedCount to 1
    end if
  on error
    -- Page layout mode: iterate text items
    set tiCount to count of text items of d
    repeat with i from 1 to tiCount
      try
        set currentText to (object text of text item i of d) as string
        if currentText contains findText then
          set newText to my replaceAll(currentText, findText, replText)
          set object text of text item i of d to newText
          set changedCount to changedCount + 1
        end if
      end try
    end repeat
  end try

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


def _set_body_text(in_path: Path, text: str, append: bool) -> None:
    text_escaped = _escape_apple_string(text)
    if append:
        set_clause = f'''
  set body text of d to (body text of d) & "{text_escaped}"'''
    else:
        set_clause = f'''
  set body text of d to "{text_escaped}"'''

    script = (
        _build_opening_block(in_path)
        + set_clause
        + '''
  save d
  close d saving yes
  return "OK"
end tell
'''
    )
    _run_osascript(script)


def _get_word_count(in_path: Path) -> dict[str, int]:
    script = (
        _build_opening_block(in_path)
        + r'''
  set wCount to word count of d
  set cCount to character count of d
  set pCount to count of pages of d
  close d saving no
  return "WORDS" & tab & wCount & tab & "CHARS" & tab & cCount & tab & "PAGES" & tab & pCount
end tell
'''
    )
    raw = _run_osascript(script)
    parts = raw.split("\t")
    result: dict[str, int] = {}
    for i in range(0, len(parts) - 1, 2):
        key = parts[i].lower()
        result[key] = int(parts[i + 1])
    return result


def _create_document(output_path: Path, template: str | None) -> None:
    out_escaped = _escape_apple_string(str(output_path.resolve()))
    if template:
        template_escaped = _escape_apple_string(template)
        doc_creation = f'''
  try
    set targetTemplate to first template whose name is "{template_escaped}"
    set d to make new document with properties {{document template:targetTemplate}}
  on error
    set d to make new document
  end try'''
    else:
        doc_creation = '''
  set d to make new document'''

    script = (
        _build_app_only_block()
        + doc_creation
        + f'''
  save d in POSIX file "{out_escaped}"
  close d saving yes
  return "OK"
end tell
'''
    )
    _run_osascript(script)


def _export(
    in_path: Path,
    docx_path: Path | None,
    pdf_path: Path | None,
    epub_path: Path | None,
    txt_path: Path | None,
) -> None:
    parts: list[str] = []
    if docx_path:
        escaped = _escape_apple_string(str(docx_path.resolve()))
        parts.append(f'''
  export d to POSIX file "{escaped}" as Microsoft Word''')
    if pdf_path:
        escaped = _escape_apple_string(str(pdf_path.resolve()))
        parts.append(f'''
  export d to POSIX file "{escaped}" as PDF''')
    if epub_path:
        escaped = _escape_apple_string(str(epub_path.resolve()))
        parts.append(f'''
  export d to POSIX file "{escaped}" as EPUB''')
    if txt_path:
        escaped = _escape_apple_string(str(txt_path.resolve()))
        parts.append(f'''
  export d to POSIX file "{escaped}" as Unformatted Text''')

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
    data = _inspect(args.input)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    print(f"Name: {data.get('name', 'Unknown')}")
    print(f"Type: {data.get('document_type', 'Unknown')}")
    print(f"Pages: {data.get('page_count', 0)}")
    print(f"Words: {data.get('word_count', 0)}")
    print(f"Characters: {data.get('character_count', 0)}")
    if data.get("text_item_count", 0) > 0:
        print(f"Text items: {data['text_item_count']}")
    return 0


def cmd_dump_text(args: argparse.Namespace) -> int:
    text = _dump_text(args.input)
    print(text)
    return 0


def cmd_replace_text(args: argparse.Namespace) -> int:
    target = _prepare_output(args)
    updated = _replace_text_pages(target, args.find, args.replace)
    print(f"Updated: {updated} replacement(s)")
    print(f"Target file: {target}")
    return 0


def cmd_set_body_text(args: argparse.Namespace) -> int:
    target = _prepare_output(args)
    _set_body_text(target, args.text, args.append)
    action = "Appended to" if args.append else "Set"
    print(f"{action} body text")
    print(f"Target file: {target}")
    return 0


def cmd_get_word_count(args: argparse.Namespace) -> int:
    data = _get_word_count(args.input)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(f"Words: {data.get('words', 0)}")
        print(f"Characters: {data.get('chars', 0)}")
        print(f"Pages: {data.get('pages', 0)}")
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    _create_document(args.output, args.template)
    print(f"Created: {args.output}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    if not args.docx and not args.pdf and not args.epub and not args.txt:
        raise RuntimeError("Provide at least one target: --docx, --pdf, --epub, and/or --txt")

    for path in [args.docx, args.pdf, args.epub, args.txt]:
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)

    _export(args.input, args.docx, args.pdf, args.epub, args.txt)
    if args.docx:
        print(f"Exported DOCX: {args.docx}")
    if args.pdf:
        print(f"Exported PDF: {args.pdf}")
    if args.epub:
        print(f"Exported EPUB: {args.epub}")
    if args.txt:
        print(f"Exported TXT: {args.txt}")
    return 0


def cmd_render_images(args: argparse.Namespace) -> int:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("`pdftoppm` not found. Install poppler to use render-images.")

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="pages_render_") as tmp:
        pdf_path = Path(tmp) / "render.pdf"
        _export(args.input, None, pdf_path, None, None)
        prefix = out_dir / "page"
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
    parser = argparse.ArgumentParser(description="Automate Apple Pages documents (.pages)")
    sub = parser.add_subparsers(dest="command", required=True)

    # --- inspect ---
    p_inspect = sub.add_parser("inspect", help="Inspect document properties")
    p_inspect.add_argument("input", type=Path, help="Path to .pages file")
    p_inspect.add_argument("--json", action="store_true", help="Print JSON output")
    p_inspect.set_defaults(func=cmd_inspect)

    # --- dump-text ---
    p_dump = sub.add_parser("dump-text", help="Extract document text")
    p_dump.add_argument("input", type=Path, help="Path to .pages file")
    p_dump.set_defaults(func=cmd_dump_text)

    # --- replace-text ---
    p_replace = sub.add_parser("replace-text", help="Find/replace text in document")
    p_replace.add_argument("input", type=Path, help="Path to .pages file")
    p_replace.add_argument("--find", required=True, help="Text to find")
    p_replace.add_argument("--replace", required=True, help="Replacement text")
    p_replace.add_argument("--output", type=Path, help="Optional output file (copy + edit)")
    p_replace.set_defaults(func=cmd_replace_text)

    # --- set-body-text ---
    p_set_body = sub.add_parser("set-body-text", help="Set or append body text")
    p_set_body.add_argument("input", type=Path, help="Path to .pages file")
    p_set_body.add_argument("--text", required=True, help="Text content")
    p_set_body.add_argument("--append", action="store_true", help="Append instead of replace")
    p_set_body.add_argument("--output", type=Path, help="Optional output file (copy + edit)")
    p_set_body.set_defaults(func=cmd_set_body_text)

    # --- get-word-count ---
    p_wc = sub.add_parser("get-word-count", help="Get word and character counts")
    p_wc.add_argument("input", type=Path, help="Path to .pages file")
    p_wc.add_argument("--json", action="store_true", help="Print JSON output")
    p_wc.set_defaults(func=cmd_get_word_count)

    # --- create ---
    p_create = sub.add_parser("create", help="Create a new Pages document")
    p_create.add_argument("--output", type=Path, required=True, help="Output .pages file path")
    p_create.add_argument("--template", default=None, help="Template name (optional)")
    p_create.set_defaults(func=cmd_create)

    # --- export ---
    p_export = sub.add_parser("export", help="Export Pages to DOCX/PDF/EPUB/TXT")
    p_export.add_argument("input", type=Path, help="Path to .pages file")
    p_export.add_argument("--docx", type=Path, help="Output .docx path")
    p_export.add_argument("--pdf", type=Path, help="Output .pdf path")
    p_export.add_argument("--epub", type=Path, help="Output .epub path")
    p_export.add_argument("--txt", type=Path, help="Output .txt path")
    p_export.set_defaults(func=cmd_export)

    # --- render-images ---
    p_render = sub.add_parser("render-images", help="Render page images via PDF + pdftoppm")
    p_render.add_argument("input", type=Path, help="Path to .pages file")
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
