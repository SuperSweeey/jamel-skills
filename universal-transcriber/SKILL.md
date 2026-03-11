---
name: universal-transcriber
description: 下载并转录视频内容为文字，支持抖音、B站、小红书、YouTube。可将转录结果分发到 Notion、GitHub Pages 或 Flomo。当用户提供视频链接并要求转录、整理、保存视频内容时使用此 skill。
argument-hint: "<平台> <视频URL> [--cookies <路径>] [--send notion|github|flomo] [--dry-run]"
disable-model-invocation: true
allowed-tools: Bash
---

# Universal Transcriber

将视频链接转录为文字，可选择分发到指定平台。

## Windows 使用方式

本机安装路径：

```powershell
C:\Users\26084\.codex\skills\universal-transcriber
```

在 Windows PowerShell 中，先切到该目录再执行：

```powershell
Set-Location 'C:\Users\26084\.codex\skills\universal-transcriber'
python .\main.py --platform <平台> --url "<链接>" [OPTIONS]
```

如果你的环境里 `python` 不可用，可改用：

```powershell
py .\main.py --platform <平台> --url "<链接>" [OPTIONS]
```

## 支持平台

| 平台 | 参数值 | 需要 cookies |
|------|--------|-------------|
| 抖音 | `douyin` | 是，通常需要 |
| B站 | `bilibili` | 是，通常需要 |
| 小红书 | `xiaohongshu` | 是，通常需要 |
| YouTube | `youtube` | 可选 |

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--platform` | 视频平台 | `douyin` |
| `--url` | 视频链接 | `"https://v.douyin.com/xxx"` |
| `--cookies` | cookies 文件路径 | `".\config\douyin_cookies.txt"` |
| `--send` | 分发目标，可重复传入 | `--send notion --send github` |
| `--dry-run` | 只转录不分发 | `--dry-run` |

## Windows 示例命令

```powershell
# 抖音：只转录，不分发
Set-Location 'C:\Users\26084\.codex\skills\universal-transcriber'
python .\main.py --platform douyin --url "https://v.douyin.com/xxx" --cookies ".\config\douyin_cookies.txt" --dry-run

# B站：转录并发送到 Notion
python .\main.py --platform bilibili --url "https://www.bilibili.com/video/xxx" --cookies ".\config\bilibili_cookies.txt" --send notion

# 小红书：转录并发送到 Notion 和 GitHub
python .\main.py --platform xiaohongshu --url "https://www.xiaohongshu.com/xxx" --cookies ".\config\xiaohongshu_cookies.txt" --send notion --send github
```

## 运行前检查

运行前通常需要准备这些内容：

- `config\config.json`
- 对应平台的 cookies 文件
- `ffmpeg`
- Python 依赖，例如 `dashscope`、`notion-client`、`playwright`、`requests`

当前仓库默认会读取：

```powershell
C:\Users\26084\.codex\skills\universal-transcriber\config\config.json
```

如果这个文件不存在，脚本会直接失败。

## Notion 数据库确认

默认 Notion 数据库为「资料默认库」。运行前应确认是否写入该库，或者改成其他库。

可用数据库别名定义在：

```powershell
C:\Users\26084\.codex\skills\universal-transcriber\config\send_rules.yaml
```

已知别名：

- `default`：资料默认库
- `ai_learning`：Ai Learning & Creating

## 输出格式

结构化 JSON 位于 `=== RESULT_JSON_START ===` 和 `=== RESULT_JSON_END ===` 之间，典型格式如下：

```json
{
  "task_id": "abc123",
  "task_status": "success",
  "platform": "douyin",
  "title": "AI生成的标题",
  "original_title": "原始标题",
  "char_count": 889,
  "transcript": "转录全文...",
  "transcript_file": "C:\\path\\to\\transcript.txt",
  "send_results": {
    "notion": "success",
    "github": "success"
  },
  "dry_run": false
}
```

## 常见问题

- 下载失败：先检查 cookies 是否过期。
- 转录失败：检查 DashScope 密钥和网络。
- Notion 失败：检查 Integration 权限和数据库 ID。
- GitHub 推送失败：检查 token、仓库目录和本地 git 状态。

## Bug 记录

### Bug #1：OSS 上传后转录失败 FILE_DOWNLOAD_FAILED

- 时间：2026-03-03
- 原因：`main.py` 跳过 OSS 上传，直接把本地路径传给转录器
- 解决：Step 3 补上 OSS 上传，把 `oss_url` 传给转录器

### Bug #2：pipeline 相对导入失败

- 时间：2026-03-03
- 原因：`pipeline` 模块用相对导入，被 `importlib` 动态加载时失效
- 解决：批量替换为绝对导入

### Bug #3：Notion 一直用旧数据库 ID

- 时间：2026-03-04
- 原因：`config.json` 旧 ID 未更新，`dispatcher` fallback 读了旧值
- 解决：更新 `config.json`，`dispatcher` 严格从 `send_rules.yaml` 取，不 fallback

### Bug #4：智谱 AI `glm-4.7-flash` 返回空 content

- 时间：2026-03-04
- 原因：推理模型 `max_tokens` 太小，推理未完成就截断
- 解决：`max_tokens` 改为 1500，加重试机制

### Bug #5：`git pull` 失败导致推送异常

- 时间：2026-03-04
- 错误：`cannot pull with rebase: You have unstaged changes`
- 解决：push 前先 `git stash`，pull 后再 `git stash pop`
