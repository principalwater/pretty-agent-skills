#!/usr/bin/env python3
"""Automate Apple Keynote (.key) files via AppleScript.

Commands:
- inspect
- dump-text
- replace-text
- set-text
- get-notes
- set-notes
- get-slide-count
- add-slide
- delete-slide
- add-image
- list-themes
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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SlideInfo:
    index: int
    text_item_count: int = 0
    text_items: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
    """AppleScript block that opens a .key file and sets ``d`` to the front document."""
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


def _build_app_only_block() -> str:
    """AppleScript block that addresses Keynote without opening a document."""
    return '''
tell application "Keynote"
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


def _set_text(in_path: Path, slide_idx: int, item_idx: int, text: str) -> None:
    text_escaped = _escape_apple_string(text)
    script = (
        _build_opening_block(in_path)
        + f'''
  set object text of text item {item_idx} of slide {slide_idx} of d to "{text_escaped}"
  save d
  close d saving yes
  return "OK"
end tell
'''
    )
    _run_osascript(script)


def _get_notes(in_path: Path, slide_idx: int | None) -> list[dict[str, Any]]:
    if slide_idx is not None:
        script = (
            _build_opening_block(in_path)
            + f'''
  set n to presenter notes of slide {slide_idx} of d
  close d saving no
  return "NOTE" & tab & {slide_idx} & tab & n
end tell
'''
        )
    else:
        script = (
            _build_opening_block(in_path)
            + r'''
  set slideCount to count of slides of d
  set outputText to ""
  repeat with i from 1 to slideCount
    set n to presenter notes of slide i of d
    set outputText to outputText & "NOTE" & tab & i & tab & n & linefeed
  end repeat
  close d saving no
  return outputText
end tell
'''
        )
    raw = _run_osascript(script)
    results: list[dict[str, Any]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) >= 3 and parts[0] == "NOTE":
            results.append({"slide": int(parts[1]), "notes": parts[2]})
        elif len(parts) == 2 and parts[0] == "NOTE":
            results.append({"slide": int(parts[1]), "notes": ""})
    return results


def _set_notes(in_path: Path, slide_idx: int, text: str) -> None:
    text_escaped = _escape_apple_string(text)
    script = (
        _build_opening_block(in_path)
        + f'''
  set presenter notes of slide {slide_idx} of d to "{text_escaped}"
  save d
  close d saving yes
  return "OK"
end tell
'''
    )
    _run_osascript(script)


def _get_slide_count(in_path: Path) -> int:
    script = (
        _build_opening_block(in_path)
        + r'''
  set c to count of slides of d
  close d saving no
  return c
end tell
'''
    )
    return int(_run_osascript(script))


def _add_slide(in_path: Path, position: int | None, layout: str) -> int:
    layout_escaped = _escape_apple_string(layout)
    if position is not None:
        pos_clause = f"at before slide {position} of d"
    else:
        pos_clause = "at end of slides of d"
    script = (
        _build_opening_block(in_path)
        + f'''
  try
    set targetLayout to first master slide of d whose name is "{layout_escaped}"
  on error
    set targetLayout to first master slide of d
  end try
  make new slide {pos_clause} with properties {{base slide:targetLayout}}
  set newCount to count of slides of d
  save d
  close d saving yes
  return newCount
end tell
'''
    )
    return int(_run_osascript(script))


def _delete_slide(in_path: Path, slide_idx: int) -> int:
    script = (
        _build_opening_block(in_path)
        + f'''
  delete slide {slide_idx} of d
  set newCount to count of slides of d
  save d
  close d saving yes
  return newCount
end tell
'''
    )
    return int(_run_osascript(script))


def _add_image(
    in_path: Path,
    slide_idx: int,
    image_path: Path,
    x: int | None,
    y: int | None,
    width: int | None,
    height: int | None,
) -> None:
    img_escaped = _escape_apple_string(str(image_path.resolve()))
    props = f'file name:"{img_escaped}"'
    if x is not None and y is not None:
        props += f", position:{{{x}, {y}}}"
    if width is not None:
        props += f", width:{width}"
    if height is not None:
        props += f", height:{height}"
    script = (
        _build_opening_block(in_path)
        + f'''
  tell slide {slide_idx} of d
    make new image with properties {{{props}}}
  end tell
  save d
  close d saving yes
  return "OK"
end tell
'''
    )
    _run_osascript(script)


def _list_themes() -> list[str]:
    script = (
        _build_app_only_block()
        + r'''
  set themeNames to name of every theme
  set outputText to ""
  repeat with t in themeNames
    set outputText to outputText & t & linefeed
  end repeat
  return outputText
end tell
'''
    )
    raw = _run_osascript(script)
    return [line.strip() for line in raw.splitlines() if line.strip()]


def _create_document(output_path: Path, theme: str) -> None:
    theme_escaped = _escape_apple_string(theme)
    out_escaped = _escape_apple_string(str(output_path.resolve()))
    script = (
        _build_app_only_block()
        + f'''
  try
    set targetTheme to first theme whose name is "{theme_escaped}"
  on error
    set targetTheme to first theme
  end try
  set d to make new document with properties {{document theme:targetTheme}}
  save d in POSIX file "{out_escaped}"
  close d saving yes
  return "OK"
end tell
'''
    )
    _run_osascript(script)


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


# ---------------------------------------------------------------------------
# CLI command handlers
# ---------------------------------------------------------------------------

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
    target = _prepare_output(args)
    updated = _replace_text(target, args.find, args.replace)
    print(f"Updated text items: {updated}")
    print(f"Target file: {target}")
    return 0


def cmd_set_text(args: argparse.Namespace) -> int:
    target = _prepare_output(args)
    _set_text(target, args.slide, args.item, args.text)
    print(f"Set text of slide {args.slide}, item {args.item}")
    print(f"Target file: {target}")
    return 0


def cmd_get_notes(args: argparse.Namespace) -> int:
    slide_idx = args.slide if hasattr(args, "slide") else None
    notes = _get_notes(args.input, slide_idx)
    if args.json:
        print(json.dumps(notes, ensure_ascii=False, indent=2))
    else:
        for entry in notes:
            print(f"\n# Slide {entry['slide']} Notes")
            print(entry["notes"] if entry["notes"] else "(empty)")
    return 0


def cmd_set_notes(args: argparse.Namespace) -> int:
    target = _prepare_output(args)
    _set_notes(target, args.slide, args.text)
    print(f"Set presenter notes for slide {args.slide}")
    print(f"Target file: {target}")
    return 0


def cmd_get_slide_count(args: argparse.Namespace) -> int:
    count = _get_slide_count(args.input)
    if args.json:
        print(json.dumps({"slide_count": count}))
    else:
        print(f"Slides: {count}")
    return 0


def cmd_add_slide(args: argparse.Namespace) -> int:
    target = _prepare_output(args)
    new_count = _add_slide(target, args.position, args.layout)
    print(f"Slide added. Total slides: {new_count}")
    print(f"Target file: {target}")
    return 0


def cmd_delete_slide(args: argparse.Namespace) -> int:
    target = _prepare_output(args)
    new_count = _delete_slide(target, args.index)
    print(f"Slide {args.index} deleted. Remaining slides: {new_count}")
    print(f"Target file: {target}")
    return 0


def cmd_add_image(args: argparse.Namespace) -> int:
    if not args.image.exists():
        raise RuntimeError(f"Image file does not exist: {args.image}")
    target = _prepare_output(args)
    _add_image(target, args.slide, args.image, args.x, args.y, args.width, args.height)
    print(f"Image added to slide {args.slide}")
    print(f"Target file: {target}")
    return 0


def cmd_list_themes(args: argparse.Namespace) -> int:
    themes = _list_themes()
    if args.json:
        print(json.dumps({"themes": themes}, ensure_ascii=False, indent=2))
    else:
        for t in themes:
            print(t)
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    _create_document(args.output, args.theme)
    print(f"Created: {args.output}")
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


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automate Apple Keynote presentations (.key)")
    sub = parser.add_subparsers(dest="command", required=True)

    # --- inspect ---
    p_inspect = sub.add_parser("inspect", help="Inspect slide structure")
    p_inspect.add_argument("input", type=Path, help="Path to .key file")
    p_inspect.add_argument("--json", action="store_true", help="Print JSON output")
    p_inspect.set_defaults(func=cmd_inspect)

    # --- dump-text ---
    p_dump = sub.add_parser("dump-text", help="Extract readable text by slide")
    p_dump.add_argument("input", type=Path, help="Path to .key file")
    p_dump.add_argument("--max-slides", type=int, default=None, help="Limit output to first N slides")
    p_dump.set_defaults(func=cmd_dump_text)

    # --- replace-text ---
    p_replace = sub.add_parser("replace-text", help="Replace text across all text items")
    p_replace.add_argument("input", type=Path, help="Path to source .key file")
    p_replace.add_argument("--find", required=True, help="Text to find")
    p_replace.add_argument("--replace", required=True, help="Replacement text")
    p_replace.add_argument("--output", type=Path, help="Optional output .key file (copy + edit)")
    p_replace.set_defaults(func=cmd_replace_text)

    # --- set-text ---
    p_set_text = sub.add_parser("set-text", help="Set text of a specific text item")
    p_set_text.add_argument("input", type=Path, help="Path to .key file")
    p_set_text.add_argument("--slide", type=int, required=True, help="Slide index (1-based)")
    p_set_text.add_argument("--item", type=int, required=True, help="Text item index (1-based)")
    p_set_text.add_argument("--text", required=True, help="New text content")
    p_set_text.add_argument("--output", type=Path, help="Optional output .key file (copy + edit)")
    p_set_text.set_defaults(func=cmd_set_text)

    # --- get-notes ---
    p_get_notes = sub.add_parser("get-notes", help="Read presenter notes")
    p_get_notes.add_argument("input", type=Path, help="Path to .key file")
    p_get_notes.add_argument("--slide", type=int, default=None, help="Slide index (omit for all)")
    p_get_notes.add_argument("--json", action="store_true", help="Print JSON output")
    p_get_notes.set_defaults(func=cmd_get_notes)

    # --- set-notes ---
    p_set_notes = sub.add_parser("set-notes", help="Set presenter notes for a slide")
    p_set_notes.add_argument("input", type=Path, help="Path to .key file")
    p_set_notes.add_argument("--slide", type=int, required=True, help="Slide index (1-based)")
    p_set_notes.add_argument("--text", required=True, help="Notes text")
    p_set_notes.add_argument("--output", type=Path, help="Optional output .key file (copy + edit)")
    p_set_notes.set_defaults(func=cmd_set_notes)

    # --- get-slide-count ---
    p_count = sub.add_parser("get-slide-count", help="Get number of slides")
    p_count.add_argument("input", type=Path, help="Path to .key file")
    p_count.add_argument("--json", action="store_true", help="Print JSON output")
    p_count.set_defaults(func=cmd_get_slide_count)

    # --- add-slide ---
    p_add_slide = sub.add_parser("add-slide", help="Add a new slide")
    p_add_slide.add_argument("input", type=Path, help="Path to .key file")
    p_add_slide.add_argument("--position", type=int, default=None, help="Insert before this slide index (default: end)")
    p_add_slide.add_argument("--layout", default="Blank", help="Master slide / layout name (default: Blank)")
    p_add_slide.add_argument("--output", type=Path, help="Optional output .key file (copy + edit)")
    p_add_slide.set_defaults(func=cmd_add_slide)

    # --- delete-slide ---
    p_del_slide = sub.add_parser("delete-slide", help="Delete a slide by index")
    p_del_slide.add_argument("input", type=Path, help="Path to .key file")
    p_del_slide.add_argument("--index", type=int, required=True, help="Slide index to delete (1-based)")
    p_del_slide.add_argument("--output", type=Path, help="Optional output .key file (copy + edit)")
    p_del_slide.set_defaults(func=cmd_delete_slide)

    # --- add-image ---
    p_add_img = sub.add_parser("add-image", help="Insert an image on a slide")
    p_add_img.add_argument("input", type=Path, help="Path to .key file")
    p_add_img.add_argument("--slide", type=int, required=True, help="Slide index (1-based)")
    p_add_img.add_argument("--image", type=Path, required=True, help="Path to image file")
    p_add_img.add_argument("--x", type=int, default=None, help="X position in points")
    p_add_img.add_argument("--y", type=int, default=None, help="Y position in points")
    p_add_img.add_argument("--width", type=int, default=None, help="Width in points")
    p_add_img.add_argument("--height", type=int, default=None, help="Height in points")
    p_add_img.add_argument("--output", type=Path, help="Optional output .key file (copy + edit)")
    p_add_img.set_defaults(func=cmd_add_image)

    # --- list-themes ---
    p_themes = sub.add_parser("list-themes", help="List available Keynote themes")
    p_themes.add_argument("--json", action="store_true", help="Print JSON output")
    p_themes.set_defaults(func=cmd_list_themes)

    # --- create ---
    p_create = sub.add_parser("create", help="Create a new Keynote document")
    p_create.add_argument("--output", type=Path, required=True, help="Output .key file path")
    p_create.add_argument("--theme", default="White", help="Theme name (default: White)")
    p_create.set_defaults(func=cmd_create)

    # --- export ---
    p_export = sub.add_parser("export", help="Export Keynote to PPTX/PDF")
    p_export.add_argument("input", type=Path, help="Path to .key file")
    p_export.add_argument("--pptx", type=Path, help="Output .pptx path")
    p_export.add_argument("--pdf", type=Path, help="Output .pdf path")
    p_export.set_defaults(func=cmd_export)

    # --- render-images ---
    p_render = sub.add_parser("render-images", help="Render slide images via PDF + pdftoppm")
    p_render.add_argument("input", type=Path, help="Path to .key file")
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
