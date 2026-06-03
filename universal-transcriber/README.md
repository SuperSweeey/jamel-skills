# Universal Transcriber Skill

把任何一个视频链接，变成完整文字，再送到你要去的地方。

DOWNLOAD · TRANSCRIBE · DISTRIBUTE

一个面向视频内容转写与分发的 Codex / ChatGPT Skill，用于把 Douyin、Bilibili、Xiaohongshu、YouTube 等平台的视频内容下载、提取音频、上传到 OSS、调用 DashScope 转写，并把结果保存到本地、Notion、GitHub 或 Flomo。

它不是普通下载器，也不是单纯的语音识别脚本，而是一条把视频接进知识工作流的入口。

想看更完整的费用拆分和技术路线，请看 [费用和技术路线说明.md](<C:/Users/26084/.codex/skills/universal-transcriber/费用和技术路线说明.md>).

## 适合谁使用

- 需要把公开视频、课程视频、访谈视频、播客视频转成文字的人
- 需要把转写结果保存到 Notion、GitHub Pages 或 Flomo 的内容整理者
- 第一次使用时不知道 DashScope、OSS、ffmpeg、Python 依赖怎么配置的人
- 希望失败时能定位是下载、音频、OSS、转写还是分发阶段出问题的人
- 希望默认不保存视频文件，只保留转写结果的人
- 希望 cookies 只在下载失败后再处理，而不是一开始就被要求配置的人

## 核心能力

- 基础检查：先检查 Python、依赖、ffmpeg、config、DashScope 和 OSS 是否就绪
- 缺失引导：缺什么就提示配置什么，并指向具体教程
- 多平台入口：统一支持 Douyin、Bilibili、Xiaohongshu、YouTube
- 音频提取：使用 ffmpeg 从下载内容中提取并转换音频
- OSS 临时上传：将音频上传到 OSS 并生成短期可访问 URL
- DashScope 转写：调用云端 ASR 服务生成文字稿
- 本地保存：默认将 transcript 保存到 `output\transcripts`
- 目标分发：按用户选择发送到 Notion、GitHub 或 Flomo
- 失败诊断：按下载、音频、OSS、转写、分发阶段定位问题

## 整体流程

第一次使用时，先做基础检查，再进入任务流程。

### 第一步：基础检查

```powershell
cd C:\Users\26084\.codex\skills\universal-transcriber
python .\scripts\check_setup.py
```

基础检查包括：

- Python 是否可用
- 必要 Python 依赖是否可导入
- ffmpeg 是否可用
- `config\config.json` 是否存在
- DashScope Key 是否配置
- OSS AccessKey、Bucket、Endpoint 是否配置

如果这里没通过，就先看 [docs/first-run-setup.md](docs/first-run-setup.md) 补齐配置，不要先急着问链接。

### 第二步：确认链接和平台

基础检查通过后，再提供视频链接，并确认平台是 Douyin、Bilibili、Xiaohongshu 还是 YouTube。

### 第三步：先问保存目标

把转写结果保存到哪里，先问用户，不默认 Notion 或 GitHub。

- local
- Notion
- GitHub
- Flomo
- multiple targets

### 第四步：执行完整链路

DOWNLOAD → AUDIO → OSS → DASHSCOPE → TRANSCRIPT → DISTRIBUTION

### 技术路线简要

- 本地先完成下载和 ffmpeg 音频提取
- 音频通过 OSS 做临时中转，再交给 DashScope 转写
- 转写结果按用户选择保存到本地、Notion、GitHub 或 Flomo
- 临时 OSS 对象默认在完成后删除

### 第五步：失败就按阶段回看

如果失败，先判断是在下载、提取音频、OSS、转写，还是分发阶段出的问题。

## Operating Modes

| Mode | 用途 | 典型输出 |
|---|---|---|
| `setup_check` | 第一次使用前检查基础环境和核心配置 | OK / MISSING 清单、缺失项教程提示 |
| `local_save` | 只保存本地转写文本 | `output\transcripts\transcript_<task_id>.txt` |
| `dry_run` | 验证下载、音频、OSS、转写链路，但不分发 | 转写文件、跳过分发说明 |
| `send_notion` | 将转写结果保存到 Notion | Notion 写入结果、失败诊断 |
| `send_github` | 将转写结果发布到 GitHub Pages | HTML 文件、提交推送结果、页面链接 |
| `send_flomo` | 将转写结果发送到 Flomo | Flomo 发送结果 |
| `save_video` | 保留下载的视频文件 | 转写结果、本地视频路径 |
| `retry_with_cookies` | 下载失败后使用 cookies 重试 | 下载诊断、cookies 路径、重试结果 |

## 多平台入口

平台各有规则，入口只有一个。

### Douyin

适合短视频、分享链接和高频刷到的内容。首次使用不强制 cookies，下载失败后再补。

### Bilibili

适合课程、访谈和长视频内容沉淀。常见场景下可直接跑，遇到登录或权限限制再补 cookies。

### Xiaohongshu

适合笔记型视频和生活经验内容。入口统一，失败后再处理 cookies。

### YouTube

公开视频通常更少依赖 cookies，适合知识类批处理。

## 输出去向

### Local

保存到本地文件，适合先做一个最轻量的成功路径。

### Notion

把转写结果沉淀到知识库，适合长期整理和复盘。

### GitHub

把结果发布到仓库或页面，适合公开归档和静态展示。

### Flomo

把转写结果快速塞进灵感流，适合快速收藏和稍后整理。

## 为什么强

它强的不是“把声音转成字”，而是把零散视频变成可管理、可搜索、可分发的内容资产。

- 以前视频看完就散，信息留在平台里，靠记忆和手抄接力
- 现在一条链接进去，文字出来，内容就能进入你的知识系统
- 下载、转写、整理、分发被串成一条完整链路
- 转写结果可以搜索、引用、复盘、再创作、再发布

## 安装方式

当前本地路径：

```powershell
C:\Users\26084\.codex\skills\universal-transcriber
```

在 Codex / ChatGPT 中调用：

```text
请使用 universal-transcriber skill，先检查第一次使用配置是否就绪。
```

或者：

```text
请使用 universal-transcriber skill，把这个视频链接转写后保存到本地：<video_url>
```

## 推荐仓库结构

```text
universal-transcriber/
├── README.md
├── SKILL.md
├── main.py
├── dispatcher.py
├── publish_to_github.py
├── config/
│   ├── config.json
│   ├── send_rules.yaml
│   └── *_cookies.txt
├── docs/
│   └── first-run-setup.md
├── scripts/
│   └── check_setup.py
├── downloaders/
├── pipeline/
├── senders/
└── output/
    ├── audio/
    ├── downloads/
    └── transcripts/
```

## 免责声明

本 skill 只用于辅助视频内容转写、整理和分发。它不能保证所有平台链接都能下载，也不能绕过平台权限、登录、验证码、地区限制或版权限制。使用者应确认自己有权下载、转写和保存相关内容。

本 skill 会使用 OSS 和 DashScope 进行云端处理。请不要提交或公开 `config.json`、API Key、Token、cookies 或任何敏感音视频内容。对于涉及隐私、商业秘密、未公开课程、会议录音或受版权保护的内容，使用者应自行判断合规性和授权范围。
