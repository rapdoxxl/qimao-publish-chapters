#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Upload local chapters to Qimao author backend one by one."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


@dataclass
class Chapter:
    number: int
    title: str
    path: Path
    content: str


def parse_chapters(value: str) -> list[int]:
    result: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = [int(x.strip()) for x in part.split("-", 1)]
            result.extend(range(start, end + 1))
        else:
            result.append(int(part))
    return sorted(dict.fromkeys(result))


def clean_markdown(text: str) -> str:
    lines: list[str] = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if re.match(r"^#+\s", line):
            continue
        if re.match(r"^\s*---+\s*$", line):
            continue
        line = re.sub(r"!\[(.*?)\]\(.*?\)", r"\1", line)
        line = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", line)
        line = re.sub(r"`([^`]+)`", r"\1", line)
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        line = re.sub(r"\*(.+?)\*", r"\1", line)
        line = re.sub(r"^>\s?", "", line)
        lines.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def find_chapter_file(root: Path, number: int) -> Path:
    prefixes = [
        f"{number}_",
        f"{number} ",
        f"{number:02d}_",
        f"{number:02d} ",
        f"{number:03d}_",
        f"{number:03d} ",
    ]
    matches = [
        item
        for item in root.rglob("*")
        if item.is_file()
        and item.suffix.lower() in {".md", ".txt"}
        and any(item.name.startswith(prefix) for prefix in prefixes)
    ]
    if not matches:
        raise RuntimeError(f"找不到第{number}章文件：{root}")
    return sorted(matches, key=lambda p: str(p))[0]


def infer_title(path: Path, raw_text: str, number: int) -> str:
    heading = re.search(r"^#+\s*第.+?章[：:\s]*(.+?)\s*$", raw_text, re.M)
    if heading:
        return heading.group(1).strip()
    stem = path.stem
    stem = re.sub(rf"^{number:03d}[\s_]*", "", stem)
    stem = re.sub(rf"^{number:02d}[\s_]*", "", stem)
    stem = re.sub(rf"^{number}[\s_]*", "", stem)
    stem = re.sub(r"^第.+?章[：_\s-]*", "", stem)
    return stem.strip() or f"第{number}章"


def load_chapter(root: Path, number: int) -> Chapter:
    path = find_chapter_file(root, number)
    raw = path.read_text(encoding="utf-8-sig")
    title = infer_title(path, raw, number)
    content = clean_markdown(raw) if path.suffix.lower() == ".md" else raw.strip()
    if not content:
        raise RuntimeError(f"第{number}章正文为空：{path}")
    return Chapter(number=number, title=title, path=path, content=content)


def click_text(page, text: str, exact: bool = False) -> bool:
    locator = page.get_by_text(text, exact=exact)
    count = locator.count()
    for i in range(count):
        item = locator.nth(i)
        try:
            if item.is_visible():
                item.click(force=True)
                return True
        except Exception:
            pass
    return False


def click_visible_control(page, text: str) -> bool:
    handles = page.query_selector_all("button, a, [role=button], .qm-btn, .el-button, .btn")
    for item in handles:
        try:
            if item.is_visible() and text in (item.inner_text() or ""):
                box = item.bounding_box()
                if box:
                    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                else:
                    item.click(force=True)
                return True
        except Exception:
            pass
    best = page.evaluate_handle(
        """(target) => {
            const items = Array.from(document.querySelectorAll('*'))
                .filter(el => {
                    const txt = (el.innerText || '').trim();
                    if (!txt.includes(target)) return false;
                    const rect = el.getBoundingClientRect();
                    if (!rect.width || !rect.height) return false;
                    const style = window.getComputedStyle(el);
                    if (style.visibility === 'hidden' || style.display === 'none') return false;
                    return true;
                })
                .map(el => ({ el, area: el.getBoundingClientRect().width * el.getBoundingClientRect().height }))
                .sort((a, b) => a.area - b.area);
            return items.length ? items[0].el : null;
        }""",
        text,
    )
    element = best.as_element()
    if element:
        try:
            box = element.bounding_box()
            if box:
                page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                return True
        except Exception:
            pass
    locator = page.get_by_text(text, exact=False)
    count = locator.count()
    for i in range(count - 1, -1, -1):
        item = locator.nth(i)
        try:
            if item.is_visible():
                box = item.bounding_box()
                if box:
                    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                else:
                    item.click(force=True)
                return True
        except Exception:
            pass
    return False


def screenshot(page, out_dir: Path, label: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out_dir / f"{label}.png"), full_page=True)


def goto_upload(page, book_id: str, book_title: str) -> None:
    page.goto(f"https://zuozhe.qimao.com/front/book-upload?id={book_id}&title={book_title}", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(6000)
    body = page.inner_text("body")
    if "登录" in body and "立即发布" not in body:
        raise RuntimeError("七猫后台未登录或登录已失效")
    if "立即发布" not in body:
        raise RuntimeError("没有进入七猫上传章节页面")


def current_chapter_number(page) -> int | None:
    body = page.inner_text("body")
    match = re.search(r"第\s*(\d+)\s*章\s+请输入正文", body)
    if match:
        return int(match.group(1))
    matches = re.findall(r"第\s*(\d+)\s*章", body)
    if matches:
        return int(matches[-1])
    return None


def fill_chapter(page, chapter: Chapter) -> None:
    title_input = page.locator("input[placeholder*='章节名称']").first
    if title_input.count() == 0:
        raise RuntimeError("找不到章节名称输入框")
    title_input.fill(chapter.title)
    page.wait_for_timeout(500)
    editor = page.locator(".q-contenteditable.book").first
    if editor.count() == 0:
        editor = page.locator("[contenteditable=true]").first
    if editor.count() == 0:
        raise RuntimeError("找不到正文编辑器")
    editor.click(force=True)
    page.evaluate(
        """([selector, text]) => {
            const el = document.querySelector(selector);
            if (!el) throw new Error('editor missing');
            el.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('insertText', false, text);
            el.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: text }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        }""",
        [".q-contenteditable.book", chapter.content],
    )
    page.wait_for_timeout(3000)


def wait_countdown_and_ack(page) -> None:
    waited = False
    for _ in range(50):
        body = page.inner_text("body")
        if "我已阅读并知晓" in body:
            if not waited:
                page.wait_for_timeout(12000)
                waited = True
            button = page.locator(".first-upload-dialog a.qm-btn.important").first
            if button.count() and button.is_visible():
                page.evaluate(
                    """() => {
                        const el = document.querySelector('.first-upload-dialog a.qm-btn.important');
                        if (!el) return;
                        const rect = el.getBoundingClientRect();
                        const opts = { bubbles: true, cancelable: true, view: window, clientX: rect.x + rect.width / 2, clientY: rect.y + rect.height / 2 };
                        for (const type of ['mouseover', 'mousemove', 'mousedown', 'mouseup', 'click']) {
                            el.dispatchEvent(new MouseEvent(type, opts));
                        }
                    }"""
                )
                page.wait_for_timeout(5000)
            else:
                click_visible_control(page, "我已阅读并知晓")
                page.wait_for_timeout(3000)
            if "我已阅读并知晓" not in page.inner_text("body"):
                return
        page.wait_for_timeout(1000)
    raise RuntimeError("重要提醒弹窗没有成功关闭")


def click_modal_ok(page) -> None:
    for text in ["我知道了", "确定", "确认", "知道了"]:
        if click_visible_control(page, text):
            page.wait_for_timeout(2000)
            return


def publish_current(page, chapter: Chapter, out_dir: Path) -> None:
    if not click_visible_control(page, "立即发布"):
        screenshot(page, out_dir, f"{chapter.number:03d}_no_publish_button")
        raise RuntimeError("找不到立即发布按钮")
    page.wait_for_timeout(2000)
    screenshot(page, out_dir, f"{chapter.number:03d}_after_publish_click")
    for _ in range(90):
        body = page.inner_text("body")
        if "确认发布" in body:
            if click_visible_control(page, "确认发布"):
                page.wait_for_timeout(3000)
                continue
        if "重要提醒" in body or "我已阅读并知晓" in body:
            wait_countdown_and_ack(page)
            continue
        if "上传成功" in body or "发布成功" in body or "章节上传成功" in body:
            click_modal_ok(page)
            page.wait_for_timeout(5000)
            return
        if "章节管理" in body and f"第{chapter.number}章 {chapter.title}" in body:
            return
        if "我知道了" in body or "确定" in body:
            click_modal_ok(page)
            page.wait_for_timeout(3000)
            if current_chapter_number(page) and current_chapter_number(page) > chapter.number:
                return
        if current_chapter_number(page) and current_chapter_number(page) > chapter.number:
            return
        page.wait_for_timeout(1000)
    screenshot(page, out_dir, f"{chapter.number:03d}_publish_stuck")
    raise RuntimeError(f"第{chapter.number}章发布流程超时")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--book-id", required=True)
    parser.add_argument("--book-title", required=True)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--chapters", required=True)
    parser.add_argument("--profile-dir", type=Path)
    parser.add_argument("--chrome-exe", default=DEFAULT_CHROME)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    chapters = [load_chapter(args.root, number) for number in parse_chapters(args.chapters)]
    for chapter in chapters:
        print(f"PLAN 第{chapter.number}章 {chapter.title} <- {chapter.path} ({len(chapter.content)}字)")
    if args.dry_run:
        return

    profile_dir = args.profile_dir or (args.root.parent / ".qimao_publish_profile")
    out_dir = args.out_dir or (args.root.parent / ".qimao_publish_screenshots")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            executable_path=args.chrome_exe,
            headless=False,
            viewport={"width": 1400, "height": 950},
        )
        page = context.pages[0] if context.pages else context.new_page()
        try:
            goto_upload(page, args.book_id, args.book_title)
            for chapter in chapters:
                number = current_chapter_number(page)
                if number is not None and number != chapter.number:
                    raise RuntimeError(f"七猫当前上传页是第{number}章，但准备上传第{chapter.number}章，停止以避免错章")
                fill_chapter(page, chapter)
                publish_current(page, chapter, out_dir)
                print(f"OK 第{chapter.number}章 {chapter.title}")
                if chapter != chapters[-1]:
                    goto_upload(page, args.book_id, args.book_title)
        finally:
            context.close()


if __name__ == "__main__":
    main()
