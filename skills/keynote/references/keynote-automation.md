# Keynote Automation Notes

## Environment Constraints

- Native `.key` operations are supported only on macOS with `Keynote.app` installed.
- AppleScript open is asynchronous; always wait for document count to increase before reading/editing.
- `.key` is a ZIP container with `.iwa` payloads; direct binary editing is not a stable workflow for production updates.

## Safe Editing Pattern

1. Copy original file.
2. Apply scripted text updates to the copy.
3. Export to PDF/PPTX for verification.
4. Compare text and visuals before replacing original.

## AppleScript Patterns

### Opening a document (handles already-open files)
```applescript
tell application "Keynote"
  -- Check if already open by name
  set alreadyOpen to false
  repeat with existingDoc in documents
    if name of existingDoc is "myfile.key" then
      set d to existingDoc
      set alreadyOpen to true
      exit repeat
    end if
  end repeat

  if not alreadyOpen then
    set docsBefore to count of documents
    open (POSIX file "/path/to/file.key") as alias
    repeat while (count of documents) = docsBefore
      delay 0.25
    end repeat
    set d to front document
  end if
end tell
```

### Creating a new document
```applescript
tell application "Keynote"
  set targetTheme to first theme whose name is "White"
  set d to make new document with properties {document theme:targetTheme}
  save d in POSIX file "/path/to/output.key"
  close d saving yes
end tell
```

### Discovering master slide layouts
```applescript
tell application "Keynote"
  set allMasters to master slides of front document
  repeat with ms in allMasters
    log name of ms
  end repeat
end tell
```

### Adding a slide with a specific layout
```applescript
tell application "Keynote"
  tell front document
    -- Method 1: make + set base slide (most reliable)
    make new slide at end
    set newSlide to last slide
    set targetLayout to first master slide whose name is "Title Only"
    set base slide of newSlide to targetLayout

    -- Method 2: with properties (may fail with duplicate names)
    -- make new slide at end with properties {base slide:targetLayout}
  end tell
end tell
```

**Important:** Some templates have duplicate master slide names (e.g., multiple "Title" layouts for different themes). Use `list-masters` to discover exact names and iterate by index if needed.

### Setting text on a specific text item
```applescript
tell application "Keynote"
  tell front document
    set object text of text item 1 of slide 1 to "Hello World"
  end tell
end tell
```

### Formatting text (font, size, color)
```applescript
tell application "Keynote"
  tell front document
    set ti to text item 3 of slide 6
    set the font of object text of ti to "Menlo"
    set the size of object text of ti to 18
    set the color of object text of ti to {65535, 65535, 65535}  -- white (RGB 0-65535)
  end tell
end tell
```

**Color format:** AppleScript uses `{R, G, B}` with values 0-65535. To convert from hex: multiply each 0-255 component by 257.

### Creating a new text box
```applescript
tell application "Keynote"
  tell slide 6 of front document
    set newItem to make new text item with properties {object text:"code here"}
    set position of newItem to {60, 160}
    set width of newItem to 1800
    set height of newItem to 800
    set the font of object text of newItem to "Menlo"
    set the size of object text of newItem to 18
    set the color of object text of newItem to {65535, 65535, 65535}
  end tell
end tell
```

### Creating a shape (rectangle)
```applescript
tell application "Keynote"
  tell slide 4 of front document
    set sh to make new shape with properties {object text:"Kafka", width:300, height:55}
    set position of sh to {100, 200}
    set font of every character of object text of sh to "Helvetica Neue"
    set size of every character of object text of sh to 18
    set color of every character of object text of sh to {65535, 65535, 65535}
  end tell
end tell
```

**Important:** Use `tell slide N of document` context for `make new shape`. A flat reference like `make new shape at slide N of d` fails with error -10000.

**Text formatting:** Use `every character of object text of sh` instead of `object text of sh` to avoid -10003 errors.

### Deleting shapes and images
```applescript
tell application "Keynote"
  tell slide 4 of front document
    -- Delete specific shape
    delete shape 3
    -- Delete all shapes (reverse order)
    repeat with i from (count of shapes) to 1 by -1
      delete shape i
    end repeat
    -- Delete all images
    repeat with i from (count of images) to 1 by -1
      delete image i
    end repeat
  end tell
end tell
```

### GUI Scripting for Fill/Stroke Colors

Keynote's `background fill type` property is **read-only** in AppleScript. The only way to set fill colors programmatically is via GUI scripting through System Events.

**Prerequisites:** macOS accessibility permissions for the controlling app.

**Workflow:**
1. Activate Keynote, show the target slide
2. Click at shape center (convert slide coords to screen coords)
3. In Format panel: expand Fill disclosure, select "Color Fill", set color well value
4. For border: expand Border disclosure, select "Line", set 2nd color well

**Coordinate conversion:** Slide coords (1920x1080) must be mapped to screen coordinates. Query the canvas area position and size from System Events, then: `screen_x = canvas_x + slide_x * scale`.

**Locale warning:** AppleScript may use locale-specific decimal separators (e.g., comma in Russian locale). Use `as integer` and non-comma delimiters (e.g., `|`) when parsing coordinate values.

### Presenter notes
```applescript
-- Read
set n to presenter notes of slide 1 of front document
-- Write
set presenter notes of slide 1 of front document to "Speaker notes here"
```

### Inserting an image
```applescript
tell application "Keynote"
  tell slide 1 of front document
    set imgFile to POSIX file "/path/to/image.png"
    set newImg to make new image with properties {file:imgFile}
    set position of newImg to {100, 100}
    set width of newImg to 400
    set height of newImg to 300
  end tell
end tell
```

**Important:** Use `file:(POSIX file "/path")` not `file name:"/path"`. The latter may fail silently or cause -2700 errors.

### Listing themes
```applescript
tell application "Keynote"
  name of every theme
end tell
```

### Exporting
```applescript
tell application "Keynote"
  export front document to POSIX file "/path/out.pptx" as Microsoft PowerPoint
  export front document to POSIX file "/path/out.pdf" as PDF
end tell
```

## Master Slide Linked Text Items

Some master layouts have **linked text items** where setting text on one automatically updates another. This is common with master slides that have both a "default" and "title" text placeholder.

### Known patterns:

- **Code layout:** text items t1 and t3 are often linked (both are the title). The actual code area may not exist as a separate text item on new slides.
- **Title layouts:** t1 and t4 (or t3) are often linked pairs.
- **Statement layout:** t1 and t4 may mirror each other.

### Workaround for linked items:

When you need independent text (e.g., a code block separate from the title on a Code slide), use `add-text-item` to create a new text box:

```bash
python scripts/keynote_tool.py add-text-item presentation.key \
  --slide 6 --text "SELECT * FROM events" \
  --x 60 --y 160 --width 1800 --height 800 \
  --font "Menlo" --size 18 --color "#FFFFFF"
```

## Selective Slide Rendering

When doing QA on large presentations, render only the slides you changed to save time:

```bash
# Render only slides 3, 6, 7, and 11
python scripts/keynote_tool.py render-images presentation.key \
  --out-dir rendered --slides 3,6-7,11
```

This uses `pdftoppm -f N -l N` under the hood for efficient partial rendering.

## Common Failures

- `Invalid index` / `document 1` errors: document not opened yet; add wait loop.
- `-2700 Failed to open`: document may already be open in Keynote. The tool now handles this automatically.
- Export fails silently: verify output path permissions and that Keynote has completed opening the file.
- Missing slide images: `pdftoppm` is not installed.
- Theme not found: theme names are case-sensitive; use `list-themes` to discover exact names.
- Image not inserted: use `POSIX file` reference, not a bare string path. Verify the file exists.
- Text formatting not applied: some text items are linked to master slide placeholders. Use `add-text-item` for independent text boxes.
- `background fill type: Can't set read-only property`: use `style-shape` command (GUI scripting) instead.
- `-10003 Access not allowed`: use `every character of object text` for color/font formatting.
- `-10000 AppleEvent handler failed` on `make new shape`: use `tell slide N of d ... make new shape ... end tell` context.
