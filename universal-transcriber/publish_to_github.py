#!/usr/bin/env python3
import os
import sys
import datetime
import subprocess
import time
import uuid
from pathlib import Path


def generate_note_html(transcript_id, title, url, task_id, summary, original_content):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            color: #333;
            line-height: 1.7;
        }}
        h1 {{
            font-size: 1.8rem;
            border-bottom: 2px solid #eee;
            padding-bottom: 0.5rem;
        }}
        .meta {{
            color: #888;
            font-size: 0.9rem;
            margin-bottom: 1.5rem;
        }}
        .meta a {{
            color: #888;
        }}
        .summary {{
            background: #f8f9fa;
            border-left: 4px solid #4a90e2;
            padding: 1rem 1.5rem;
            margin: 1.5rem 0;
            border-radius: 0 8px 8px 0;
        }}
        .summary-title {{
            font-weight: bold;
            color: #4a90e2;
            margin-bottom: 0.5rem;
        }}
        .content {{
            white-space: pre-wrap;
            background: #fafafa;
            padding: 1.5rem;
            border-radius: 8px;
            font-size: 0.95rem;
        }}
        .back-link {{
            margin-top: 2rem;
        }}
        .back-link a {{
            color: #4a90e2;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="meta">
        <p><strong>原始链接：</strong><a href="{url}" target="_blank">{url}</a></p>
        <p><strong>日期：</strong>{date_str}</p>
    </div>
    <div class="summary">
        <div class="summary-title">AI 总结</div>
        <div>{summary}</div>
    </div>
    <div class="content">{original_content}</div>
    <div class="back-link"><a href="../index.html">← 返回首页</a></div>
</body>
</html>"""


def update_index_html(transcript_id, title, summary, github_repo_dir):
    index_path = os.path.join(github_repo_dir, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        index_content = f.read()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    new_item = f"""        <li class="note-item" data-date="{date_str}">
            <a href="notes/{transcript_id}.html">{title}</a>
            <div class="note-date">{date_str}</div>
            <div class="note-summary">{summary}</div>
        </li>
"""
    marker = '<ul class="note-list" id="noteList">'
    if marker in index_content:
        start = index_content.find(marker)
        end = index_content.find("</ul>", start)
        if end != -1:
            index_content = index_content[:end] + new_item + "    " + index_content[end:]
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)


def git_stable_push(commit_message, github_token, github_user, github_repo, github_repo_dir, max_retries=3):
    original_dir = os.getcwd()
    try:
        os.chdir(github_repo_dir)
        subprocess.run(["git", "config", "http.version", "HTTP/1.1"], check=True, capture_output=True)
        subprocess.run(["git", "config", "http.postBuffer", "524288000"], check=True, capture_output=True)
        subprocess.run([
            "git", "remote", "set-url", "origin",
            f"https://{github_token}@github.com/{github_user}/{github_repo}.git"
        ], check=True, capture_output=True)
        stash = subprocess.run(["git", "stash"], capture_output=True, text=True)
        stashed = "No local changes" not in stash.stdout
        pull = subprocess.run(["git", "pull", "origin", "main", "--rebase"], capture_output=True, text=True)
        if pull.returncode != 0:
            print(f"[WARN] pull 失败，继续推送: {pull.stderr[:100]}")
        if stashed:
            subprocess.run(["git", "stash", "pop"], capture_output=True)
        subprocess.run(["git", "add", "--all"], check=True, capture_output=True)
        commit = subprocess.run(["git", "commit", "-m", commit_message], capture_output=True, text=True)
        if commit.returncode != 0:
            print("[INFO] No changes to commit")
            return True
        for attempt in range(1, max_retries + 1):
            print(f"[INFO] 推送到 GitHub（第 {attempt}/{max_retries} 次）...")
            push = subprocess.run(["git", "push", "-u", "origin", "main"], capture_output=True, text=True)
            if push.returncode == 0:
                print("[OK] GitHub Pages 推送成功")
                return True
            print(f"[WARN] 推送失败: {push.stderr[-200:]}")
            if attempt < max_retries:
                time.sleep(5)
        raise RuntimeError(f"GitHub 推送失败，已重试 {max_retries} 次")
    finally:
        os.chdir(original_dir)


def publish_to_github(transcript_id, title, url, task_id, summary, original_content, config):
    github_repo_dir = config.github_repo_dir
    notes_dir = Path(github_repo_dir) / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    note_html = generate_note_html(transcript_id, title, url, task_id, summary, original_content)
    note_path = notes_dir / f"{transcript_id}.html"
    note_path.write_text(note_html, encoding="utf-8")
    print(f"[OK] HTML 已生成: {note_path}")
    update_index_html(transcript_id, title, summary, github_repo_dir)
    print("[OK] 首页已更新")
    git_stable_push(
        f"Add transcript: {title[:50]}",
        config.github_token,
        config.github_user,
        config.github_repo,
        github_repo_dir
    )
    github_url = f"https://{config.github_user}.github.io/notes/{transcript_id}.html"
    print(f"[OK] GitHub Pages 发布完成: {github_url}")
    return github_url
