# qimao-publish-chapters

Codex skill for publishing local Markdown or TXT novel chapters to the Qimao author backend one chapter at a time.

The skill keeps account data out of the repository. It does not include book IDs, pen names, cookies, saved passwords, browser local storage, GitHub tokens, or machine-specific workspace paths.

## Install

Copy this folder into your Codex skills directory:

```powershell
Copy-Item ".\qimao-publish-chapters" "$env:USERPROFILE\.codex\skills\" -Container
```

Restart Codex, then ask for the `qimao-publish-chapters` skill when publishing Qimao chapters.

## Usage

Run a dry run first:

```powershell
& 'D:\Program Files\Python\python.exe' `
  .\scripts\qimao_upload_chapters.py `
  --book-id YOUR_QIMAO_BOOK_ID `
  --book-title "YOUR_BOOK_TITLE" `
  --root "F:\path\to\novel\chapters" `
  --chapters 2-20 `
  --dry-run
```

Then publish:

```powershell
& 'D:\Program Files\Python\python.exe' `
  .\scripts\qimao_upload_chapters.py `
  --book-id YOUR_QIMAO_BOOK_ID `
  --book-title "YOUR_BOOK_TITLE" `
  --root "F:\path\to\novel\chapters" `
  --chapters 2-20 `
  --profile-dir ".qimao_publish_profile" `
  --out-dir ".qimao_publish_screenshots"
```

Use a Python environment with Playwright installed. If browser verification fails in Chrome, pass `--chrome-exe` with a Chromium-family browser path.

## Safety

- Publish one chapter at a time and verify the backend moves to the next chapter before continuing.
- Stop on chapter-number mismatch, unknown modal, missing publish button, captcha, slider verification, or login prompt.
- Let the user complete login and human verification interactively in the browser.
- Never read, export, commit, or reuse cookies, passwords, local storage, or tokens.

