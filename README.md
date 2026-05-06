# 七猫章节发布 Skill

这是一个用于 Codex 的 skill，可以把本地 Markdown 或 TXT 小说章节逐章发布到七猫小说网作者后台。

它的重点是稳妥发布：每次只处理一章，发布后确认后台进入下一章，再继续后面的章节。仓库中不包含书号、笔名、Cookie、密码、浏览器本地存储、GitHub token 或本机工作区路径。

## 安装

把整个文件夹复制到 Codex 的 skills 目录：

```powershell
Copy-Item ".\qimao-publish-chapters" "$env:USERPROFILE\.codex\skills\" -Container
```

重启 Codex 后，在需要发布七猫章节时让 Codex 使用 `qimao-publish-chapters` skill。

## 使用方法

先执行一次 dry run，确认章节识别结果：

```powershell
& 'D:\Program Files\Python\python.exe' `
  .\scripts\qimao_upload_chapters.py `
  --book-id YOUR_QIMAO_BOOK_ID `
  --book-title "你的书名" `
  --root "F:\path\to\novel\chapters" `
  --chapters 2-20 `
  --dry-run
```

确认无误后再正式发布：

```powershell
& 'D:\Program Files\Python\python.exe' `
  .\scripts\qimao_upload_chapters.py `
  --book-id YOUR_QIMAO_BOOK_ID `
  --book-title "你的书名" `
  --root "F:\path\to\novel\chapters" `
  --chapters 2-20 `
  --profile-dir ".qimao_publish_profile" `
  --out-dir ".qimao_publish_screenshots"
```

请使用已安装 Playwright 的 Python 环境。如果 Chrome 的验证流程异常，可以通过 `--chrome-exe` 指定其他 Chromium 内核浏览器。

## 安全规则

- 一次只发布一章，确认后台进入下一章后再继续。
- 如果页面章节号和本地章节号不一致，立即停止，避免错章。
- 遇到未知弹窗、缺少发布按钮、验证码、滑块验证或登录页时停止，让用户处理。
- 登录和人机验证只在浏览器中交给用户手动完成。
- 不读取、不导出、不提交、不复用 Cookie、密码、本地存储或 token。

## 参数说明

- `--book-id`：七猫书号。
- `--book-title`：七猫上传页使用的书名。
- `--root`：本地章节目录，支持递归查找 Markdown/TXT 文件。
- `--chapters`：要发布的章节范围，例如 `2-20` 或 `21,22,23`。
- `--profile-dir`：可选的持久浏览器资料目录，用于保留正常登录态。
- `--chrome-exe`：可选的浏览器路径。
- `--out-dir`：可选的截图输出目录，用于排查异常。
- `--dry-run`：只解析章节并打印计划，不打开浏览器、不发布。
