#!/usr/bin/env python3
"""Automate Apple Keynote (.key) files via AppleScript.

Commands:
- inspect
- dump-text
- replace-text
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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SlideInfo:
    index: int
    text_item_count: int = 0
    text_items: list[str] = field(default_factory=list)


def _require_macos() -> None:
    if sys.platform != "darwin":
        raise RuntimeError("This tool requires macOS because it automates Keynote via AppleScript.")


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
    in_path_escaped = _escape_apple_string(str(in_path.resolve()))
    return f'''
set inPath to "{in_path_escaped}"
set inAlias to (POSIX file inPath) as alias

tell application "Keynote"
  set docsBefore to count of documents
  open inAlias
  set waited to 0
  repeat while (count of documents) = docsBefore and waited < 120
    delay 0.25
    set waited to waited + 1
  end repeat
  if (count of documents) = docsBefore then error "Failed to open Keynote document"
  set d to front document
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


def _collect_structure(in_path: Path) -> dict[str, Any]:
    script = (
        _build_opening_block(in_path)
        + r'''
  set slideCount to count of slides of d
  set outputText to "SLIDES" & tab & slideCount & linefeed

  repeat with i from 1 to slideCount
    set s to slide i of d
    set textCount to count of text items of s
    set outputText to outputText & "SLIDE" & tab & i & tab & textCount & linefeed

    repeat with j from 1 to textCount
      try
        set t to (object text of text item j of s) as string
      on error
        set t to ""
      end try
      set tClean to my sanitizeText(t)
      set outputText to outputText & "TEXT" & tab & i & tab & j & tab & tClean & linefeed
    end repeat
  end repeat

  close d saving no
  return outputText
end tell
'''
        + _build_common_handlers()
    )

    raw = _run_osascript(script)
    slides: dict[int, SlideInfo] = {}
    slide_count = 0

    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        tag = parts[0]
        if tag == "SLIDES" and len(parts) >= 2:
            slide_count = int(parts[1])
        elif tag == "SLIDE" and len(parts) >= 3:
            idx = int(parts[1])
            slides[idx] = SlideInfo(index=idx, text_item_count=int(parts[2]))
        elif tag == "TEXT" and len(parts) >= 4:
            idx = int(parts[1])
            text_value = "\t".join(parts[3:]).strip()
            slides.setdefault(idx, SlideInfo(index=idx)).text_items.append(text_value)

    ordered = [slides[i] for i in sorted(slides)]
    return {
        "slide_count": slide_count,
        "slides": [
            {
                "index": s.index,
                "text_item_count": s.text_item_count,
                "text_items": s.text_items,
            }
            for s in ordered
        ],
    }


def _replace_text(in_path: Path, find_text: str, replace_text: str) -> int:
    find_escaped = _escape_apple_string(find_text)
    replace_escaped = _escape_apple_string(replace_text)

    script = (
        _build_opening_block(in_path)
        + f'''
  set findText to "{find_escaped}"
  set replText to "{replace_escaped}"
  set changedCount to 0
  set slideCount to count of slides of d

  repeat with i from 1 to slideCount
    set s to slide i of d
    set textCount to count of text items of s
    repeat with j from 1 to textCount
      try
        set currentText to (object text of text item j of s) as string
      on error
        set currentText to ""
      end try

      if currentText contains findText then
        set newText to my replaceAll(currentText, findText, replText)
        set object text of text item j of s to newText
        set changedCount to changedCount + 1
      end if
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


def _export(in_path: Path, pptx_path: Path | None, pdf_path: Path | None) -> None:
    pptx_escaped = _escape_apple_string(str(pptx_path.resolve())) if pptx_path else ""
    pdf_escaped = _escape_apple_string(str(pdf_path.resolve())) if pdf_path else ""

    script = (
        _build_opening_block(in_path)
        + f'''
  set pptxOut to "{pptx_escaped}"
  set pdfOut to "{pdf_escaped}"

  if pptxOut is not "" then
    export d to POSIX file pptxOut as Microsoft PowerPoint
  end if

  if pdfOut is not "" then
    export d to POSIX file pdfOut as PDF
  end if

  close d saving no
  return "OK"
end tell
'''
    )

    _run_osascript(script)


def cmd_inspect(args: argparse.Namespace) -> int:
    data = _collect_structure(args.input)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    print(f"Slides: {data['slide_count']}")
    for slide in data["slides"]:
        print(f"Slide {slide['index']}: text_items={slide['text_item_count']}")
    return 0


def cmd_dump_text(args: argparse.Namespace) -> int:
    data = _collect_structure(args.input)
    max_slides = args.max_slides or data["slide_count"]
    for slide in data["slides"]:
        if slide["index"] > max_slides:
            break
        print(f"\n# Slide {slide['index']}")
        if not slide["text_items"]:
            print("(no text items)")
            continue
        for item in slide["text_items"]:
            if item.strip():
                print(f"- {item}")
    return 0


def cmd_replace_text(args: argparse.Namespace) -> int:
    target = args.input
    if args.output:
        target = args.output
        if target.resolve() != args.input.resolve():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(args.input, target)

    updated = _replace_text(target, args.find, args.replace)
    print(f"Updated text items: {updated}")
    print(f"Target file: {target}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    if not args.pptx and not args.pdf:
        raise RuntimeError("Provide at least one target: --pptx and/or --pdf")

    if args.pptx:
        args.pptx.parent.mkdir(parents=True, exist_ok=True)
    if args.pdf:
        args.pdf.parent.mkdir(parents=True, exist_ok=True)

    _export(args.input, args.pptx, args.pdf)
    if args.pptx:
        print(f"Exported PPTX: {args.pptx}")
    if args.pdf:
        print(f"Exported PDF: {args.pdf}")
    return 0


def cmd_render_images(args: argparse.Namespace) -> int:
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        raise RuntimeError("`pdftoppm` not found. Install poppler to use render-images.")

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="keynote_render_") as tmp:
        pdf_path = Path(tmp) / "render.pdf"
        _export(args.input, None, pdf_path)
        prefix = out_dir / "slide"
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automate Apple Keynote presentations (.key)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_inspect = sub.add_parser("inspect", help="Inspect slide structure")
    p_inspect.add_argument("input", type=Path, help="Path to .key file")
    p_inspect.add_argument("--json", action="store_true", help="Print JSON output")
    p_inspect.set_defaults(func=cmd_inspect)

    p_dump = sub.add_parser("dump-text", help="Extract readable text by slide")
    p_dump.add_argument("input", type=Path, help="Path to .key file")
    p_dump.add_argument("--max-slides", type=int, default=None, help="Limit output to first N slides")
    p_dump.set_defaults(func=cmd_dump_text)

    p_replace = sub.add_parser("replace-text", help="Replace text across all text items")
    p_replace.add_argument("input", type=Path, help="Path to source .key file")
    p_replace.add_argument("--find", required=True, help="Text to find")
    p_replace.add_argument("--replace", required=True, help="Replacement text")
    p_replace.add_argument("--output", type=Path, help="Optional output .key file (copy + edit)")
    p_replace.set_defaults(func=cmd_replace_text)

    p_export = sub.add_parser("export", help="Export Keynote to PPTX/PDF")
    p_export.add_argument("input", type=Path, help="Path to .key file")
    p_export.add_argument("--pptx", type=Path, help="Output .pptx path")
    p_export.add_argument("--pdf", type=Path, help="Output .pdf path")
    p_export.set_defaults(func=cmd_export)

    p_render = sub.add_parser("render-images", help="Render slide images via PDF + pdftoppm")
    p_render.add_argument("input", type=Path, help="Path to .key file")
    p_render.add_argument("--out-dir", type=Path, required=True, help="Output directory for JPEG images")
    p_render.add_argument("--dpi", type=int, default=150, help="Render DPI (default: 150)")
    p_render.set_defaults(func=cmd_render_images)

    return parser


def main() -> int:
    try:
        _require_macos()
        _require_osascript()
        parser = build_parser()
        args = parser.parse_args()
        if not args.input.exists():
            raise RuntimeError(f"Input file does not exist: {args.input}")
        return int(args.func(args))
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
