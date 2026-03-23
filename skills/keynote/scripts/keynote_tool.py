#!/usr/bin/env python3
"""Automate Apple Keynote (.key) files via AppleScript.

Commands:
- inspect
- dump-text
- replace-text
- set-text
- format-text
- add-text-item
- add-shape
- delete-shape
- delete-image
- style-shape
- get-notes
- set-notes
- get-slide-count
- add-slide
- delete-slide
- add-image
- list-themes
- list-masters
- create
- export
- render-images
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SlideInfo:
    index: int
    layout: str = ""
    text_item_count: int = 0
    shape_count: int = 0
    image_count: int = 0
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
    """AppleScript block that opens a .key file and sets ``d`` to the document.

    Handles the case where the document is already open in Keynote by checking
    existing documents by file path before attempting to open.
    """
    in_path_escaped = _escape_apple_string(str(in_path.resolve()))
    in_name = _escape_apple_string(in_path.stem)
    return f'''
set inPath to "{in_path_escaped}"
set inPosix to POSIX file inPath
set inName to "{in_name}"

tell application "Keynote"
  -- Check if document is already open by matching file name, then verify full path
  set alreadyOpen to false
  repeat with existingDoc in documents
    try
      if name of existingDoc is inName then
        -- Verify it's the same file by checking HFS path
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
    set inAlias to inPosix as alias
    set docsBefore to count of documents
    open inAlias
    set waited to 0
    repeat while (count of documents) = docsBefore and waited < 120
      delay 0.25
      set waited to waited + 1
    end repeat
    if (count of documents) = docsBefore then error "Failed to open Keynote document"
    set d to front document
  end if
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


def _parse_hex_color(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color like '#FF8800' or 'FF8800' to AppleScript RGB tuple (0-65535 range)."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: #{hex_color}. Expected 6 hex digits.")
    r = int(hex_color[0:2], 16) * 257  # Scale 0-255 to 0-65535
    g = int(hex_color[2:4], 16) * 257
    b = int(hex_color[4:6], 16) * 257
    return (r, g, b)


def _parse_slides_arg(slides_str: str) -> list[tuple[int, int]]:
    """Parse slides argument like '3,6-8,11' into list of (first, last) ranges."""
    ranges: list[tuple[int, int]] = []
    for part in slides_str.split(","):
        part = part.strip()
        if "-" in part:
            first, last = part.split("-", 1)
            ranges.append((int(first.strip()), int(last.strip())))
        else:
            n = int(part)
            ranges.append((n, n))
    return ranges


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
    set shapeCount to count of shapes of s
    set imageCount to count of images of s
    try
      set layoutName to name of base slide of s
    on error
      set layoutName to "(unknown)"
    end try
    set outputText to outputText & "SLIDE" & tab & i & tab & textCount & tab & layoutName & tab & shapeCount & tab & imageCount & linefeed

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
        elif tag == "SLIDE" and len(parts) >= 4:
            idx = int(parts[1])
            si = SlideInfo(
                index=idx,
                text_item_count=int(parts[2]),
                layout=parts[3].strip(),
            )
            if len(parts) >= 5:
                si.shape_count = int(parts[4])
            if len(parts) >= 6:
                si.image_count = int(parts[5])
            slides[idx] = si
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
                "layout": s.layout,
                "text_item_count": s.text_item_count,
                "shape_count": s.shape_count,
                "image_count": s.image_count,
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
  return "OK"
end tell
'''
    )
    _run_osascript(script)


def _format_text(
    in_path: Path,
    slide_idx: int,
    item_idx: int,
    font: str | None,
    size: int | None,
    color: str | None,
) -> None:
    """Set font, size, and/or color on a text item."""
    commands: list[str] = []
    if font is not None:
        font_escaped = _escape_apple_string(font)
        commands.append(f'set the font of object text of ti to "{font_escaped}"')
    if size is not None:
        commands.append(f"set the size of object text of ti to {size}")
    if color is not None:
        r, g, b = _parse_hex_color(color)
        commands.append(f"set the color of object text of ti to {{{r}, {g}, {b}}}")
    if not commands:
        return

    body = "\n    ".join(commands)
    script = (
        _build_opening_block(in_path)
        + f'''
  set ti to text item {item_idx} of slide {slide_idx} of d
  {body}
  save d
  return "OK"
end tell
'''
    )
    _run_osascript(script)


def _add_text_item(
    in_path: Path,
    slide_idx: int,
    text: str,
    x: int | None,
    y: int | None,
    width: int | None,
    height: int | None,
    font: str | None,
    size: int | None,
    color: str | None,
) -> None:
    """Create a new text item on a slide with optional position, size, and formatting."""
    text_escaped = _escape_apple_string(text)

    format_commands: list[str] = []
    if font is not None:
        font_escaped = _escape_apple_string(font)
        format_commands.append(f'set the font of object text of newItem to "{font_escaped}"')
    if size is not None:
        format_commands.append(f"set the size of object text of newItem to {size}")
    if color is not None:
        r, g, b = _parse_hex_color(color)
        format_commands.append(f"set the color of object text of newItem to {{{r}, {g}, {b}}}")

    format_block = "\n    ".join(format_commands) if format_commands else ""

    position_block = ""
    if x is not None and y is not None:
        position_block += f"\n    set position of newItem to {{{x}, {y}}}"
    if width is not None:
        position_block += f"\n    set width of newItem to {width}"
    if height is not None:
        position_block += f"\n    set height of newItem to {height}"

    script = (
        _build_opening_block(in_path)
        + f'''
  tell slide {slide_idx} of d
    set newItem to make new text item with properties {{object text:"{text_escaped}"}}
    {position_block}
    {format_block}
  end tell
  save d
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
  return c
end tell
'''
    )
    return int(_run_osascript(script))


def _add_slide(in_path: Path, position: int | None, layout: str) -> int:
    layout_escaped = _escape_apple_string(layout)
    script = (
        _build_opening_block(in_path)
        + f'''
  -- Find the target master slide by name
  set targetLayout to missing value
  set allMasters to master slides of d
  repeat with ms in allMasters
    if name of ms is "{layout_escaped}" then
      set targetLayout to ms
      exit repeat
    end if
  end repeat

  if targetLayout is missing value then
    set targetLayout to item 1 of allMasters
  end if

  -- Add slide at the end, then set its base slide
  tell d
    make new slide at end
  end tell
  set newSlide to last slide of d
  set base slide of newSlide to targetLayout
'''
        + (f'''
  -- Move to position if specified
  set newCount to count of slides of d
  if {position} < newCount then
    move newSlide to before slide {position} of d
  end if
''' if position is not None else '')
        + '''
  set newCount to count of slides of d
  save d
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
    script = (
        _build_opening_block(in_path)
        + f'''
  set imgFile to POSIX file "{img_escaped}"
  tell slide {slide_idx} of d
    set newImg to make new image with properties {{file:imgFile}}
  end tell
'''
    )
    if x is not None and y is not None:
        script += f"  set position of newImg to {{{x}, {y}}}\n"
    if width is not None:
        script += f"  set width of newImg to {width}\n"
    if height is not None:
        script += f"  set height of newImg to {height}\n"
    script += '''  save d
  return "OK"
end tell
'''
    _run_osascript(script)


def _add_shape(
    in_path: Path,
    slide_idx: int,
    text: str,
    x: int | None,
    y: int | None,
    width: int | None,
    height: int | None,
    font: str | None,
    size: int | None,
    color: str | None,
) -> None:
    """Create a new shape (rectangle with text) on a slide."""
    text_escaped = _escape_apple_string(text)

    format_commands: list[str] = []
    if font is not None:
        font_escaped = _escape_apple_string(font)
        format_commands.append(
            f'set the font of every character of object text of newShape to "{font_escaped}"'
        )
    if size is not None:
        format_commands.append(
            f"set the size of every character of object text of newShape to {size}"
        )
    if color is not None:
        r, g, b = _parse_hex_color(color)
        format_commands.append(
            f"set the color of every character of object text of newShape to {{{r}, {g}, {b}}}"
        )

    format_block = "\n    ".join(format_commands) if format_commands else ""

    props = f'object text:"{text_escaped}"'
    if width is not None:
        props += f", width:{width}"
    if height is not None:
        props += f", height:{height}"

    position_block = ""
    if x is not None and y is not None:
        position_block = f"\n    set position of newShape to {{{x}, {y}}}"

    script = (
        _build_opening_block(in_path)
        + f'''
  tell slide {slide_idx} of d
    set newShape to make new shape with properties {{{props}}}
    {position_block}
    {format_block}
  end tell
  save d
  return "OK"
end tell
'''
    )
    _run_osascript(script)


def _delete_shape(in_path: Path, slide_idx: int, shape_idx: int | None) -> int:
    """Delete a shape by index, or all shapes if shape_idx is None. Returns count deleted."""
    if shape_idx is not None:
        script = (
            _build_opening_block(in_path)
            + f'''
  delete shape {shape_idx} of slide {slide_idx} of d
  save d
  return "1"
end tell
'''
        )
        _run_osascript(script)
        return 1
    else:
        # Delete all shapes (in reverse order)
        script = (
            _build_opening_block(in_path)
            + f'''
  set s to slide {slide_idx} of d
  set sc to count of shapes of s
  repeat with i from sc to 1 by -1
    delete shape i of s
  end repeat
  save d
  return sc as text
end tell
'''
        )
        raw = _run_osascript(script)
        return int(raw) if raw else 0


def _delete_image(in_path: Path, slide_idx: int, image_idx: int | None) -> int:
    """Delete an image by index, or all images if image_idx is None. Returns count deleted."""
    if image_idx is not None:
        script = (
            _build_opening_block(in_path)
            + f'''
  delete image {image_idx} of slide {slide_idx} of d
  save d
  return "1"
end tell
'''
        )
        _run_osascript(script)
        return 1
    else:
        script = (
            _build_opening_block(in_path)
            + f'''
  set s to slide {slide_idx} of d
  set ic to count of images of s
  repeat with i from ic to 1 by -1
    delete image i of s
  end repeat
  save d
  return ic as text
end tell
'''
        )
        raw = _run_osascript(script)
        return int(raw) if raw else 0


def _style_shape(
    in_path: Path,
    slide_idx: int,
    shape_idx: int,
    fill: str | None,
    border: str | None,
) -> None:
    """Apply fill and/or border color to a shape via GUI scripting (System Events).

    This uses accessibility APIs because Keynote's AppleScript `background fill type`
    is read-only. Requires accessibility permissions for System Events.
    """
    # Get shape center coordinates
    coord_script = (
        _build_opening_block(in_path)
        + f'''
  tell slide {slide_idx} of d
    set sh to shape {shape_idx}
    set p to position of sh
    set w to width of sh
    set h to height of sh
    set cx to ((item 1 of p) + w / 2) as integer
    set cy to ((item 2 of p) + h / 2) as integer
    return (cx as text) & "|" & (cy as text)
  end tell
end tell
'''
    )
    raw = _run_osascript(coord_script)
    sx, sy = [int(x) for x in raw.split("|")]

    # Activate Keynote and show the slide
    show_script = f'''
tell application "Keynote"
  activate
  tell document 1
    show slide {slide_idx}
  end tell
end tell
'''
    _run_osascript(show_script)
    time.sleep(0.5)

    # Get canvas mapping from Keynote window
    # Canvas position and scale depend on the window size; we query it dynamically
    click_script = f'''
tell application "System Events"
  tell process "Keynote"
    set w to window 1
    set wPos to position of w
    set wSize to size of w

    -- Find the main canvas area (the slide editing area)
    -- The canvas is typically within the scroll area
    set canvasArea to missing value
    try
      set scrollAreas to every scroll area of w
      repeat with sa in scrollAreas
        set saSize to size of sa
        -- The main canvas is the largest scroll area
        if item 1 of saSize > 400 then
          set canvasArea to sa
          exit repeat
        end if
      end repeat
    end try

    if canvasArea is not missing value then
      set cPos to position of canvasArea
      set cSize to size of canvasArea
      -- Scale: canvas pixels / slide points (1920 wide)
      set scaleX to (item 1 of cSize) / 1920.0
      set scaleY to (item 2 of cSize) / 1080.0
      set scrX to ((item 1 of cPos) + {sx} * scaleX) as integer
      set scrY to ((item 2 of cPos) + {sy} * scaleY) as integer
    else
      -- Fallback: use window-based estimate
      set scrX to ((item 1 of wPos) + 319 + {sx} * 0.4583) as integer
      set scrY to ((item 2 of wPos) + 165 + {sy} * 0.4583) as integer
    end if

    click at {{scrX, scrY}}
    delay 0.4
    return (scrX as text) & "|" & (scrY as text)
  end tell
end tell
'''
    _run_osascript(click_script)

    # Apply fill
    if fill is not None:
        fr, fg, fb = _parse_hex_color(fill)
        fill_script = f'''
tell application "System Events"
  tell process "Keynote"
    -- Ensure Format tab is active
    try
      click radio button 1 of radio group 1 of window 1
    end try
    delay 0.3

    set allElems to entire contents of window 1

    -- Find Fill disclosure and expand
    repeat with j from 1 to count of allElems
      try
        set e to item j of allElems
        if role of e is "AXStaticText" and value of e is "Fill" then
          set dt to item (j - 1) of allElems
          if (value of dt) is 0 then
            click dt
            delay 0.5
            set allElems to entire contents of window 1
          end if
          exit repeat
        end if
      end try
    end repeat

    -- Find fill popup and set to Color Fill
    set foundFill to false
    repeat with j from 1 to count of allElems
      try
        set e to item j of allElems
        if role of e is "AXStaticText" and value of e is "Fill" then
          set foundFill to true
        end if
        if foundFill and role of e is "AXPopUpButton" then
          if value of e is not "Color Fill" then
            click e
            delay 0.5
            click menu item "Color Fill" of menu 1 of e
            delay 0.5
            set allElems to entire contents of window 1
          end if
          exit repeat
        end if
      end try
    end repeat

    -- Find first color well and set color
    repeat with j from 1 to count of allElems
      try
        set e to item j of allElems
        if role of e is "AXColorWell" then
          set value of e to {{{fr}, {fg}, {fb}}}
          exit repeat
        end if
      end try
    end repeat
    delay 0.2
  end tell
end tell
'''
        _run_osascript(fill_script)

    # Apply border
    if border is not None:
        br, bg, bb = _parse_hex_color(border)
        border_script = f'''
tell application "System Events"
  tell process "Keynote"
    set allElems to entire contents of window 1

    -- Find Border section and expand
    repeat with j from 1 to count of allElems
      try
        set e to item j of allElems
        if role of e is "AXStaticText" and value of e is "Border" then
          set dt to item (j - 1) of allElems
          if (value of dt) is 0 then
            click dt
            delay 0.5
            set allElems to entire contents of window 1
          end if
          exit repeat
        end if
      end try
    end repeat

    -- Find border popup and set to Line
    set foundBorderLabel to false
    repeat with j from 1 to count of allElems
      try
        set e to item j of allElems
        if role of e is "AXStaticText" and value of e is "Border" then
          set foundBorderLabel to true
        end if
        if foundBorderLabel and role of e is "AXPopUpButton" then
          if value of e is not "Line" then
            click e
            delay 0.5
            click menu item "Line" of menu 1 of e
            delay 0.5
          end if
          exit repeat
        end if
      end try
    end repeat

    -- Set border color (second color well)
    set allElems to entire contents of window 1
    set cwIdx to 0
    repeat with j from 1 to count of allElems
      try
        set e to item j of allElems
        if role of e is "AXColorWell" then
          set cwIdx to cwIdx + 1
          if cwIdx is 2 then
            set value of e to {{{br}, {bg}, {bb}}}
            exit repeat
          end if
        end if
      end try
    end repeat
    delay 0.2
  end tell
end tell
'''
        _run_osascript(border_script)

    # Click away to deselect
    _run_osascript('''
tell application "System Events"
  tell process "Keynote"
    click at {50, 50}
    delay 0.2
  end tell
end tell
''')


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


def _list_masters(in_path: Path) -> list[dict[str, Any]]:
    """List all master slides (layouts) available in a document."""
    script = (
        _build_opening_block(in_path)
        + r'''
  set allMasters to master slides of d
  set outputText to ""
  set idx to 1
  repeat with ms in allMasters
    set msName to name of ms
    set outputText to outputText & "MASTER" & tab & idx & tab & msName & linefeed
    set idx to idx + 1
  end repeat
  return outputText
end tell
'''
    )
    raw = _run_osascript(script)
    results: list[dict[str, Any]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) >= 3 and parts[0] == "MASTER":
            results.append({"index": int(parts[1]), "name": parts[2].strip()})
    return results


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
        layout_info = f" [{slide['layout']}]" if slide.get("layout") else ""
        extras = []
        extras.append(f"text_items={slide['text_item_count']}")
        if slide.get("shape_count"):
            extras.append(f"shapes={slide['shape_count']}")
        if slide.get("image_count"):
            extras.append(f"images={slide['image_count']}")
        print(f"Slide {slide['index']}{layout_info}: {', '.join(extras)}")
    return 0


def cmd_dump_text(args: argparse.Namespace) -> int:
    data = _collect_structure(args.input)
    max_slides = args.max_slides or data["slide_count"]
    for slide in data["slides"]:
        if slide["index"] > max_slides:
            break
        layout_info = f" [{slide['layout']}]" if slide.get("layout") else ""
        print(f"\n# Slide {slide['index']}{layout_info}")
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


def cmd_format_text(args: argparse.Namespace) -> int:
    target = _prepare_output(args)
    _format_text(target, args.slide, args.item, args.font, args.size, args.color)
    parts = []
    if args.font:
        parts.append(f"font={args.font}")
    if args.size:
        parts.append(f"size={args.size}")
    if args.color:
        parts.append(f"color={args.color}")
    print(f"Formatted slide {args.slide}, item {args.item}: {', '.join(parts)}")
    print(f"Target file: {target}")
    return 0


def cmd_add_text_item(args: argparse.Namespace) -> int:
    target = _prepare_output(args)
    _add_text_item(
        target, args.slide, args.text,
        args.x, args.y, args.width, args.height,
        args.font, args.size, args.color,
    )
    print(f"Text item added to slide {args.slide}")
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


def cmd_add_shape(args: argparse.Namespace) -> int:
    target = _prepare_output(args)
    _add_shape(
        target, args.slide, args.text,
        args.x, args.y, args.width, args.height,
        args.font, args.size, args.color,
    )
    print(f"Shape added to slide {args.slide}")
    print(f"Target file: {target}")
    return 0


def cmd_delete_shape(args: argparse.Namespace) -> int:
    target = _prepare_output(args)
    shape_idx = args.shape if not args.all else None
    deleted = _delete_shape(target, args.slide, shape_idx)
    print(f"Deleted {deleted} shape(s) from slide {args.slide}")
    print(f"Target file: {target}")
    return 0


def cmd_delete_image(args: argparse.Namespace) -> int:
    target = _prepare_output(args)
    image_idx = args.image if not args.all else None
    deleted = _delete_image(target, args.slide, image_idx)
    print(f"Deleted {deleted} image(s) from slide {args.slide}")
    print(f"Target file: {target}")
    return 0


def cmd_style_shape(args: argparse.Namespace) -> int:
    _style_shape(args.input, args.slide, args.shape, args.fill, args.border)
    parts = []
    if args.fill:
        parts.append(f"fill={args.fill}")
    if args.border:
        parts.append(f"border={args.border}")
    print(f"Styled shape {args.shape} on slide {args.slide}: {', '.join(parts)}")
    return 0


def cmd_list_themes(args: argparse.Namespace) -> int:
    themes = _list_themes()
    if args.json:
        print(json.dumps({"themes": themes}, ensure_ascii=False, indent=2))
    else:
        for t in themes:
            print(t)
    return 0


def cmd_list_masters(args: argparse.Namespace) -> int:
    masters = _list_masters(args.input)
    if args.json:
        print(json.dumps({"masters": masters}, ensure_ascii=False, indent=2))
    else:
        for m in masters:
            print(f"{m['index']}: {m['name']}")
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

        if args.slides:
            # Selective rendering: render only specified slides
            ranges = _parse_slides_arg(args.slides)
            for first, last in ranges:
                proc = subprocess.run(
                    [pdftoppm, "-jpeg", "-r", str(args.dpi),
                     "-f", str(first), "-l", str(last),
                     str(pdf_path), str(prefix)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if proc.returncode != 0:
                    raise RuntimeError(proc.stderr.strip() or "pdftoppm failed")
        else:
            # Render all slides
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
    p_inspect = sub.add_parser("inspect", help="Inspect slide structure and layouts")
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

    # --- format-text ---
    p_format = sub.add_parser("format-text", help="Set font, size, and/or color of a text item")
    p_format.add_argument("input", type=Path, help="Path to .key file")
    p_format.add_argument("--slide", type=int, required=True, help="Slide index (1-based)")
    p_format.add_argument("--item", type=int, required=True, help="Text item index (1-based)")
    p_format.add_argument("--font", default=None, help="Font name (e.g. 'Menlo', 'Helvetica Neue')")
    p_format.add_argument("--size", type=int, default=None, help="Font size in points")
    p_format.add_argument("--color", default=None, help="Hex color (e.g. '#FFFFFF', 'FF8800')")
    p_format.add_argument("--output", type=Path, help="Optional output .key file (copy + edit)")
    p_format.set_defaults(func=cmd_format_text)

    # --- add-text-item ---
    p_add_text = sub.add_parser("add-text-item", help="Create a new text box on a slide")
    p_add_text.add_argument("input", type=Path, help="Path to .key file")
    p_add_text.add_argument("--slide", type=int, required=True, help="Slide index (1-based)")
    p_add_text.add_argument("--text", required=True, help="Text content")
    p_add_text.add_argument("--x", type=int, default=None, help="X position in points")
    p_add_text.add_argument("--y", type=int, default=None, help="Y position in points")
    p_add_text.add_argument("--width", type=int, default=None, help="Width in points")
    p_add_text.add_argument("--height", type=int, default=None, help="Height in points")
    p_add_text.add_argument("--font", default=None, help="Font name")
    p_add_text.add_argument("--size", type=int, default=None, help="Font size in points")
    p_add_text.add_argument("--color", default=None, help="Hex color (e.g. '#FFFFFF')")
    p_add_text.add_argument("--output", type=Path, help="Optional output .key file (copy + edit)")
    p_add_text.set_defaults(func=cmd_add_text_item)

    # --- add-shape ---
    p_add_shape = sub.add_parser("add-shape", help="Create a new shape (rectangle with text) on a slide")
    p_add_shape.add_argument("input", type=Path, help="Path to .key file")
    p_add_shape.add_argument("--slide", type=int, required=True, help="Slide index (1-based)")
    p_add_shape.add_argument("--text", required=True, help="Text content")
    p_add_shape.add_argument("--x", type=int, default=None, help="X position in points")
    p_add_shape.add_argument("--y", type=int, default=None, help="Y position in points")
    p_add_shape.add_argument("--width", type=int, default=None, help="Width in points")
    p_add_shape.add_argument("--height", type=int, default=None, help="Height in points")
    p_add_shape.add_argument("--font", default=None, help="Font name")
    p_add_shape.add_argument("--size", type=int, default=None, help="Font size in points")
    p_add_shape.add_argument("--color", default=None, help="Text color as hex (e.g. '#FFFFFF')")
    p_add_shape.add_argument("--output", type=Path, help="Optional output .key file (copy + edit)")
    p_add_shape.set_defaults(func=cmd_add_shape)

    # --- delete-shape ---
    p_del_shape = sub.add_parser("delete-shape", help="Delete shape(s) from a slide")
    p_del_shape.add_argument("input", type=Path, help="Path to .key file")
    p_del_shape.add_argument("--slide", type=int, required=True, help="Slide index (1-based)")
    p_del_shape_group = p_del_shape.add_mutually_exclusive_group(required=True)
    p_del_shape_group.add_argument("--shape", type=int, help="Shape index to delete (1-based)")
    p_del_shape_group.add_argument("--all", action="store_true", help="Delete all shapes")
    p_del_shape.add_argument("--output", type=Path, help="Optional output .key file (copy + edit)")
    p_del_shape.set_defaults(func=cmd_delete_shape)

    # --- delete-image ---
    p_del_image = sub.add_parser("delete-image", help="Delete image(s) from a slide")
    p_del_image.add_argument("input", type=Path, help="Path to .key file")
    p_del_image.add_argument("--slide", type=int, required=True, help="Slide index (1-based)")
    p_del_image_group = p_del_image.add_mutually_exclusive_group(required=True)
    p_del_image_group.add_argument("--image", type=int, help="Image index to delete (1-based)")
    p_del_image_group.add_argument("--all", action="store_true", help="Delete all images")
    p_del_image.add_argument("--output", type=Path, help="Optional output .key file (copy + edit)")
    p_del_image.set_defaults(func=cmd_delete_image)

    # --- style-shape ---
    p_style = sub.add_parser("style-shape", help="Apply fill/border color to a shape (GUI scripting)")
    p_style.add_argument("input", type=Path, help="Path to .key file")
    p_style.add_argument("--slide", type=int, required=True, help="Slide index (1-based)")
    p_style.add_argument("--shape", type=int, required=True, help="Shape index (1-based)")
    p_style.add_argument("--fill", default=None, help="Fill color as hex (e.g. '#EE7F01')")
    p_style.add_argument("--border", default=None, help="Border color as hex (e.g. '#000000')")
    p_style.set_defaults(func=cmd_style_shape)

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

    # --- list-masters ---
    p_masters = sub.add_parser("list-masters", help="List master slide layouts in a document")
    p_masters.add_argument("input", type=Path, help="Path to .key file")
    p_masters.add_argument("--json", action="store_true", help="Print JSON output")
    p_masters.set_defaults(func=cmd_list_masters)

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
    p_render.add_argument("--slides", default=None, help="Render specific slides (e.g. '3,6-8,11')")
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
