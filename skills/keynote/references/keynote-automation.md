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

### Opening a document
```applescript
tell application "Keynote"
  set docsBefore to count of documents
  open (POSIX file "/path/to/file.key") as alias
  -- wait for document to open
  repeat while (count of documents) = docsBefore
    delay 0.25
  end repeat
  set d to front document
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

### Adding a slide
```applescript
tell application "Keynote"
  tell front document
    set targetLayout to first master slide whose name is "Blank"
    make new slide at end of slides with properties {base slide:targetLayout}
  end tell
end tell
```

### Setting text on a specific text item
```applescript
tell application "Keynote"
  tell front document
    set object text of text item 1 of slide 1 to "Hello World"
  end tell
end tell
```

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
    make new image with properties {file name:"/path/to/image.png", position:{100, 100}, width:400, height:300}
  end tell
end tell
```

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

## Common Failures

- `Invalid index` / `document 1` errors: document not opened yet; add wait loop.
- Export fails silently: verify output path permissions and that Keynote has completed opening the file.
- Missing slide images: `pdftoppm` is not installed.
- Theme not found: theme names are case-sensitive; use `list-themes` to discover exact names.
- Image not inserted: verify the image file path is absolute and the file exists.
