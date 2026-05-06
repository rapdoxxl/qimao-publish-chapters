---
name: qimao-publish-chapters
description: Publish local novel chapters to the Qimao author backend one chapter at a time. Use when the user asks to upload, publish, or continue publishing Markdown/TXT chapter files to 七猫小说网/七猫作者后台 for a Qimao book ID, with per-chapter form filling, final confirmation, important-reminder acknowledgement, and stop-on-mismatch safeguards.
---

# Qimao Publish Chapters

Use this skill to publish local novel chapters to 七猫小说网作者后台 safely and repeatably.

## Rules

- Upload one chapter, then wait for the backend to move to the next chapter before continuing.
- Stop immediately if the upload page chapter number does not match the local chapter number.
- Do not fill volume name or volume number; Qimao's upload page only needs chapter number, title, and body for this workflow.
- Use only user-provided `--book-id`, `--book-title`, `--root`, and `--chapters`; do not hardcode private book IDs, pen names, phone numbers, profile paths, cookies, tokens, or account data.
- Never read, export, or reuse browser cookies, saved passwords, localStorage, or tokens. Use a normal persistent browser profile and let the user log in interactively when needed.
- If a captcha, slider, SMS login, or other human verification appears, pause and ask the user to complete it in the browser.
- If an `重要提醒` dialog appears, wait for the countdown to finish, then click `我已阅读并知晓`.
- If success dialogs appear, click `我知道了`, `确定`, or equivalent, then continue.
- If the target book already has earlier chapters, start from the next chapter to avoid duplicates.

## Quick Start

Run a dry run first:

```powershell
& 'D:\Program Files\Python\python.exe' `
  .\scripts\qimao_upload_chapters.py `
  --book-id YOUR_QIMAO_BOOK_ID `
  --book-title "书名" `
  --root "F:\path\to\novel\01_正文" `
  --chapters 2-20 `
  --dry-run
```

Then publish:

```powershell
& 'D:\Program Files\Python\python.exe' `
  .\scripts\qimao_upload_chapters.py `
  --book-id YOUR_QIMAO_BOOK_ID `
  --book-title "书名" `
  --root "F:\path\to\novel\01_正文" `
  --chapters 2-20 `
  --profile-dir ".qimao_publish_profile" `
  --out-dir ".qimao_publish_screenshots"
```

Use the Python executable that has Playwright installed. Use `--chrome-exe` to choose a Chromium-family browser executable when Chrome has verification problems.

## Inputs

- `--book-id`: Qimao book ID.
- `--book-title`: Exact book title used in the upload URL.
- `--root`: Root folder containing chapter Markdown/TXT files; recursive search is supported.
- `--chapters`: Range or list, for example `2-20` or `21,22,23`.
- `--profile-dir`: Optional persistent browser profile directory. Defaults to `.qimao_publish_profile` next to the root's parent.
- `--chrome-exe`: Optional browser executable path. Defaults to Chrome.
- `--out-dir`: Optional screenshot output directory for troubleshooting.
- `--dry-run`: Parse files and print the upload plan without opening the browser.

## Workflow

1. Run `--dry-run` and confirm the local chapter plan.
2. Open Qimao upload page for the provided book ID and title.
3. If login or verification is required, let the user complete it interactively.
4. For each chapter:
   - Confirm the page is showing the same chapter number as the local file.
   - Fill chapter title.
   - Replace the body editor content with cleaned Markdown/TXT content.
   - Click `立即发布`.
   - Click `确认发布`.
   - Handle `重要提醒` by waiting, then clicking `我已阅读并知晓`.
   - Handle success confirmation and continue.
5. Stop on any mismatch, timeout, missing button, or unknown modal. Report the latest screenshot path.

## Bundled Script

- `scripts/qimao_upload_chapters.py`: deterministic Playwright uploader for Qimao chapters.
