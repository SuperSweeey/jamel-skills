---
name: universal-transcriber
description: 下载并转录视频内容为文字，支持抖音、B站、小红书、YouTube。可将转录结果分发到 Notion、GitHub Pages 或 Flomo。当用户提供视频链接并要求转录、整理、保存视频内容时使用此 skill。
argument-hint: "<平台> <视频URL> [--cookies <路径>] [--send notion|github|flomo] [--dry-run]"
disable-model-invocation: true
allowed-tools: Bash
---

# Universal Transcriber

将视频链接转录为文字，可选择分发到指定平台。

## 执行命令

```bash
cd /root/.openclaw/workspace/skills/universal-transcriber
python3 main.py --platform <平台> --url "<链接>" [OPTIONS]
```

## 支持平台

| 平台 | 参数值 | 需要 cookies |
|------|--------|-------------|
| 抖音 | `douyin` | ✅ `config/douyin_cookies.txt` |
| B站 | `bilibili` | ✅ `config/bilibili_cookies.txt` |
| 小红书 | `xiaohongshu` | ✅ `config/xiaohongshu_cookies.txt` |
| YouTube | `youtube` | 可选（服务器网络限制，暂不可用）|

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--platform` | 视频平台 | `douyin` |
| `--url` | 视频链接（用引号包裹） | `"https://v.douyin.com/xxx"` |
| `--cookies` | cookies 文件路径 | `config/douyin_cookies.txt` |
| `--send` | 分发目标，可叠加 | `--send notion --send github` |
| `--dry-run` | 只转录不分发，输出 JSON | `--dry-run` |

## 重要：每次运行前必须确认 Notion 数据库

默认 Notion 数据库为「资料默认库」，运行前必须向用户确认是否存入此库，或指定其他库。

可用数据库别名（定义在 `config/send_rules.yaml`）：
- `default`：资料默认库（3185c3ba...）
- `ai_learning`：Ai Learning & Creating（20a5c3ba...）

## 调用示例

```bash
# 转录抖音，存 Notion + GitHub
python3 main.py --platform douyin --url "https://v.douyin.com/xxx" --cookies config/douyin_cookies.txt --send notion --send github

# 只转录，获取文字内容（不分发）
python3 main.py --platform bilibili --url "https://www.bilibili.com/video/xxx" --cookies config/bilibili_cookies.txt --dry-run

# 小红书转录存 Notion
python3 main.py --platform xiaohongshu --url "https://www.xiaohongshu.com/xxx" --cookies config/xiaohongshu_cookies.txt --send notion
```

## 输出格式（AI 可直接解析）

结构化 JSON 位于 `=== RESULT_JSON_START ===` 和 `=== RESULT_JSON_END ===` 之间：

```json
{
  "task_id": "abc123",
  "task_status": "success",
  "platform": "douyin",
  "title": "AI生成的标题",
  "original_title": "原始标题",
  "char_count": 889,
  "transcript": "转录全文...",
  "transcript_file": "/path/to/transcript.txt",
  "send_results": {
    "notion": "success",
    "github": "success"
  },
  "dry_run": false
}
```

## 错误处理

- **下载失败**：检查 cookies 是否过期，重新导出后替换对应文件
- **转录失败 Connection refused**：DashScope 偶发问题，重试即可
- **Notion 失败**：检查 Integration 是否有目标数据库权限
- **GitHub 推送失败**：自动重试 3 次

---

## 🔴 Bug 记录（每次遇到 Bug 必须更新此处）

### Bug #1：OSS 上传后转录失败 FILE_DOWNLOAD_FAILED
- **时间**：2026-03-03
- **原因**：main.py 跳过 OSS 上传，直接把本地路径传给转录器
- **解决**：Step 3 补上 OSS 上传，把 oss_url 传给转录器

### Bug #2：pipeline 相对导入失败
- **时间**：2026-03-03
- **原因**：pipeline 模块用相对导入，被 importlib 动态加载时失效
- **解决**：批量替换为绝对导入

### Bug #3：Notion 一直用旧数据库 ID
- **时间**：2026-03-04
- **原因**：config.json 旧 ID 未更新，dispatcher fallback 读了旧值
- **解决**：更新 config.json，dispatcher 严格从 send_rules.yaml 取，不 fallback

### Bug #4：智谱AI glm-4.7-flash 返回空 content
- **时间**：2026-03-04
- **原因**：推理模型 max_tokens 太小，推理未完成就截断
- **解决**：max_tokens 改为 1500，加重试机制（3次，间隔5秒）

### Bug #5：git pull 失败导致推送异常
- **时间**：2026-03-04
- **错误**：`cannot pull with rebase: You have unstaged changes`
- **解决**：push 前先 git stash，pull 后再 git stash pop
