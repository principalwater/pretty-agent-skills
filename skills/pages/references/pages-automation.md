# Pages Automation Notes

## Environment Constraints

- Native `.pages` operations are supported only on macOS with `Pages.app` installed.
- AppleScript open is asynchronous; always wait for document count to increase before reading/editing.
- `.pages` is a ZIP container; direct binary editing is not a stable workflow.
- Pages has two document modes: **word processing** and **page layout**. The mode determines which AppleScript properties are available.

## Word Processing vs Page Layout

- **Word processing**: `body text of d` is available for reading and writing the full document body.
- **Page layout**: `body text` is not available; text is stored in individual text items (text boxes). Use `text items of d` to access them.
- Use `inspect` to detect the document type before editing.

## Safe Editing Pattern

1. Copy original file.
2. Apply scripted text updates to the copy.
3. Export to PDF/DOCX for verification.
4. Compare text and formatting before replacing original.

## AppleScript Patterns

### Opening a document
```applescript
tell application "Pages"
  set docsBefore to count of documents
  open (POSIX file "/path/to/file.pages") as alias
  repeat while (count of documents) = docsBefore
    delay 0.25
  end repeat
  set d to front document
end tell
```

### Reading document properties
```applescript
tell application "Pages"
  tell front document
    set pCount to count of pages
    set wCount to word count
    set cCount to character count
  end tell
end tell
```

### Reading body text (word processing)
```applescript
tell application "Pages"
  set bt to body text of front document
end tell
```

### Setting body text
```applescript
tell application "Pages"
  set body text of front document to "New content here."
end tell
```

### Find/replace in body text
```applescript
tell application "Pages"
  set bt to body text of front document
  -- use text item delimiters for replacement
  set AppleScript's text item delimiters to "old text"
  set chunks to text items of bt
  set AppleScript's text item delimiters to "new text"
  set body text of front document to chunks as text
end tell
```

### Iterating text items (page layout)
```applescript
tell application "Pages"
  tell front document
    set tiCount to count of text items
    repeat with i from 1 to tiCount
      set t to object text of text item i
    end repeat
  end tell
end tell
```

### Creating a document
```applescript
tell application "Pages"
  set d to make new document
  save d in POSIX file "/path/to/output.pages"
  close d saving yes
end tell
```

### Exporting
```applescript
tell application "Pages"
  export front document to POSIX file "/path/out.docx" as Microsoft Word
  export front document to POSIX file "/path/out.pdf" as PDF
  export front document to POSIX file "/path/out.epub" as EPUB
  export front document to POSIX file "/path/out.txt" as Unformatted Text
end tell
```

## Common Failures

- `Invalid index` errors: document not opened yet; add wait loop.
- `body text` not available: document is in page layout mode; iterate text items instead.
- Export fails silently: verify output path permissions.
- Formatting loss: setting body text via AppleScript strips rich formatting.
- Template not found: template names may not match visible names in Pages UI.
