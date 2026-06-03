---
name: universal-transcriber
description: Download one or more supported video links, transcribe them, and deliver the transcript to the user-specified destination. Use this skill whenever the user provides one or more Douyin, Bilibili, Xiaohongshu, or YouTube links and a required distribution target such as Notion, GitHub, or Flomo. The skill must report end-to-end status for download, transcription, and distribution, and if a stage fails it should inspect the error, diagnose the problem, and retry until the task either completes or reaches a clear blocking condition that must be surfaced to the user.
argument-hint: "<platform> <video_url> [--cookies <path>] [--send notion|github|flomo] [--dry-run] [--save-video]"
disable-model-invocation: true
allowed-tools: Bash
---

# Universal Transcriber

Use this skill to run the local `universal-transcriber` pipeline end to end:

1. Download the source video
2. Extract audio with `ffmpeg`
3. Upload audio to OSS
4. Transcribe with DashScope
5. Optionally send the transcript to Notion, GitHub, or Flomo

By default, the downloaded video is treated as a temporary intermediate file and is deleted after audio extraction. If the user explicitly says they want to keep the source video, add `--save-video` so the pipeline preserves it locally and report the saved file path back to the user.

This is an execution skill, not just a writing aid. When it triggers, the model should gather the required inputs, run the correct command, inspect the structured result, report stage-by-stage completion, and diagnose failures by stage. If the run fails partway through, the model should continue troubleshooting and rerunning rather than stopping at the first failed attempt, unless it hits a real blocker such as missing credentials, invalid cookies, or an unreachable external service.

## When To Use

Use this skill whenever the user asks for any of the following:

- Download and transcribe a Douyin, Bilibili, Xiaohongshu, or YouTube video
- Turn video content into text, subtitles, a transcript, or notes
- Save transcript output to Notion, GitHub Pages, or Flomo
- Diagnose why download, transcription, or sending failed
- Batch-process one or more video URLs from a supported platform

If the user provides a supported video URL and wants text output, this skill should usually trigger even if they did not explicitly say "transcribe".

## Supported Platforms

| Platform | `--platform` value | Cookies usually needed |
|---|---|---|
| Douyin | `douyin` | Yes |
| Bilibili | `bilibili` | Usually yes |
| Xiaohongshu | `xiaohongshu` | Usually yes |
| YouTube | `youtube` | Usually no |

For Douyin, treat cookies as a likely requirement, not an optional afterthought.

## Required User Inputs

On first use, do not start by asking for a link. First run the read-only setup check:

```powershell
cd C:\Users\26084\.codex\skills\universal-transcriber
python .\scripts\check_setup.py
```

If the setup check reports missing Python packages, ffmpeg, `config\config.json`, DashScope, or OSS settings, guide the user through `README.md` and `docs\first-run-setup.md` and stop there until the basic setup passes.

After the basic setup passes, collect these inputs:

1. One or more supported video links
2. A save destination or destinations: local transcript file, Notion, GitHub, Flomo, or multiple targets

Collect these additional inputs when needed:

1. Platform name if it cannot be inferred from the link
2. Cookies file path only after a download failure or when the user already knows the link requires login
3. Whether the user wants to keep the downloaded video locally (default: no → audio-only fast mode)
4. Any destination-specific constraints the user cares about

If the user gives links but no destination, ask where to save the transcript before treating the task as complete. Local transcript output is a valid destination and does not require Notion, GitHub, or Flomo config. A local `--dry-run` can still be used as an intermediate validation step, but not as the final delivery state when the user asked for distribution.
If the user does not mention saving the video, default to audio-only (fast) mode. Add `--save-video` only when the user explicitly asks to keep the video file.

## Execution Contract

The skill should behave as if it owns the whole job:

1. Validate the inputs
2. Attempt the run
3. Inspect the result
4. If a stage failed, diagnose why
5. Apply a reasonable fix or next attempt
6. Re-run
7. Stop only when:
   - download, transcription, and distribution all succeeded, or
   - there is a clear blocking condition that cannot be resolved automatically

Examples of clear blockers:

- missing or invalid cookies that the user must refresh
- missing credentials in `config.json`
- external service outage
- unsupported or dead video URL

Do not treat "download succeeded but transcription failed" as a finished task. The job is not complete until all required stages succeed or a real blocker is presented to the user with the full error.

## Local Paths

**Base directory**: `C:\Users\26084\.codex\skills\universal-transcriber`

All commands below must be run from this directory. The Python code uses `Path(__file__).parent` internally, so scripts resolve paths relative to themselves.

Primary entry point:

```powershell
python .\main.py --platform <platform> --url "<video_url>" [OPTIONS]
```

If `python` is unavailable, try:

```powershell
py .\main.py --platform <platform> --url "<video_url>" [OPTIONS]
```

## Required Runtime Dependencies

The pipeline expects these to be available before a successful full run:

- `config\config.json`
- Platform cookies file when required
- `ffmpeg` (auto-detected from PATH first, then from config.json)
- Python packages used by the pipeline, including:
  - `playwright`
  - `requests`
  - `dashscope`
  - `notion-client`
  - `pyyaml`
  - platform-specific dependencies if added later

Key config file path:

```powershell
.\config\config.json
```

Important: this pipeline is not purely local transcription. It depends on OSS upload and DashScope cloud transcription. Missing OSS or DashScope credentials will cause the run to fail even if download succeeds.

## Safe Operating Procedure

Always follow this order unless the user explicitly wants something else:

1. Run the read-only setup check before the first real task: `python .\scripts\check_setup.py`.
2. If the setup check fails, guide the user through the missing item and rerun the check. Do not continue to link collection until the basic setup passes.
3. Confirm the video link.
4. Check that the platform is supported or infer it from the link.
5. Ask where to save the transcript: local file, Notion, GitHub, Flomo, or multiple targets.
6. Check only the selected save target config, for example `python .\scripts\check_setup.py --send notion`.
7. Do not require cookies before the first run. Ask for cookies only after download failure, login or verification redirect, rate limit, or known restricted content.
8. Decide whether to preserve the downloaded video. Default to audio-only unless the user explicitly asked to save the video.
9. Use `--dry-run` only as a validation step when helpful.
10. Run the real command with the selected `--send ...` targets. Use `--send local` when the user only wants a local transcript file.
11. Add `--save-video` only when the user explicitly asked to keep the video (slower but preserves the full video file).
12. Inspect the result JSON and confirm all required stages succeeded.
13. If a stage failed, diagnose and re-run.

This avoids wasting time debugging Notion or GitHub when the real failure is still in the download or transcription stage, while still preserving the user's requirement that distribution is part of the finished task.

## Dual Mode

The pipeline has two modes:

| Mode | Flag | Behavior | Speed |
|---|---|---|---|
| **Audio-only (default)** | (none) | Downloads audio track only → converts to Opus → uploads → transcribes | ~4-6 min |
| **Full video** | `--save-video` | Downloads video+audio → merges → extracts Opus → keeps video file | ~8-14 min |

Audio-only mode is **~2-3x faster** because it skips downloading the video track and merging.

## Download Strategy

Automatic fallback chain (Bilibili):
1. **you-get** (primary) — lightweight, no cookies needed for 360P
2. **yt-dlp** (fallback) — if you-get fails, retry with yt-dlp

## Command Templates

All commands must be run **from `C:\Users\26084\.config\opencode\skill\universal-transcriber`**.

### Dry run only

```powershell
python .\main.py --platform <platform> --url "<video_url>" --dry-run
```

### Dry run with cookies

```powershell
python .\main.py --platform <platform> --url "<video_url>" --cookies ".\config\<platform>_cookies.txt" --dry-run
```

### Send to one or more targets (fast mode)

```powershell
python .\main.py --platform bilibili --url "<video_url>" --send notion
```

### Full video + keep local copy

```powershell
python .\main.py --platform bilibili --url "<video_url>" --send notion --save-video
```

## Recommended Examples

### Douyin: validate download and transcription first

```powershell
python .\main.py --platform douyin --url "https://v.douyin.com/xxxx/" --cookies ".\config\douyin_cookies.txt" --dry-run
```

### Bilibili: transcribe and send to Notion (fast, no video saved)

```powershell
python .\main.py --platform bilibili --url "https://www.bilibili.com/video/BVxxxx" --send notion
```

### Bilibili: transcribe, send to Notion, keep video

```powershell
python .\main.py --platform bilibili --url "https://www.bilibili.com/video/BVxxxx" --send notion --save-video
```

### Xiaohongshu: transcribe and send to Notion and GitHub

```powershell
python .\main.py --platform xiaohongshu --url "https://www.xiaohongshu.com/explore/xxxx" --cookies ".\config\xiaohongshu_cookies.txt" --send notion --send github
```

### YouTube: often no cookies needed

```powershell
python .\main.py --platform youtube --url "https://www.youtube.com/watch?v=xxxx" --dry-run
```

### Keep video for local archiving

```powershell
python .\main.py --platform youtube --url "https://www.youtube.com/watch?v=xxxx" --dry-run --save-video
```

## Actual Pipeline Behavior

The current implementation in `main.py` executes these stages in order:

1. Download audio track (audio-only default mode)
2. Convert to Opus (16kHz 16kbps)
3. Upload audio to OSS
4. Transcribe from OSS URL via DashScope
5. Dispatch transcript to configured targets

Important behavioral notes:

- **Audio format**: Opus 16kHz 16kbps (compressed, ~10-15MB for 1.5h) instead of WAV.
- **Default mode (audio-only)**: Downloads only the audio track, ~2-3x faster.
- **Full video mode**: Add `--save-video` to download and keep the complete video file.
- The intermediate audio track / video file is deleted after Opus extraction by default.
- The transcript is saved under `output\transcripts\transcript_<task_id>.txt`.
- When `--save-video` is used, the result payload includes `source_file` and `source_saved`.
- `--dry-run` skips sending, but still performs download, audio extraction, OSS upload, and transcription.
- If `--send` is omitted and `--dry-run` is not used, dispatch rules in `config\send_rules.yaml` may still choose targets automatically.

## Dispatch Rules

Send behavior is controlled by:

```powershell
.\config\send_rules.yaml
```

The dispatcher can:

- Use CLI `--send` targets directly
- Fall back to platform rules
- Fall back again to default success policy

So if the user wants a strictly local run, prefer `--dry-run`.

## Required Output To The User

For every execution, the model should present a complete status summary for each requested link:

- Download status: success or failed
- Transcription status: success or failed
- Distribution status: success or failed for each requested destination
- Final artifact location if available, such as the transcript file path
- Video file location when `--save-video` was requested
- Full error message if any stage failed
- What retry or fix was attempted
- Whether the task is now complete or blocked

If multiple links are provided, report them separately so the user can see which ones finished and which ones still need attention.

## Result Format

The script prints structured JSON between:

- `=== RESULT_JSON_START ===`
- `=== RESULT_JSON_END ===`

Typical success payload:

```json
{
  "task_id": "abc12345",
  "task_status": "success",
  "platform": "douyin",
  "title": "AI generated title",
  "original_title": "fallback title",
  "char_count": 889,
  "transcript": "full transcript text",
  "transcript_file": "C:\\path\\to\\transcript.txt",
  "video_file": "C:\\path\\to\\downloaded_video.mp4",
  "video_saved": true,
  "send_results": {
    "notion": "success",
    "github": "success"
  },
  "dry_run": false
}
```

Typical failure payload:

```json
{
  "task_id": "abc12345",
  "task_status": "failed",
  "platform": "douyin",
  "url": "https://v.douyin.com/xxxx/",
  "stage": "download stage name from runtime",
  "error": "error details here",
  "video_file": "C:\\path\\to\\downloaded_video.mp4",
  "video_saved": true
}
```

When debugging, always identify the failing `stage` first and preserve the full error text instead of replacing it with a vague summary.

## Failure Triage

Do not give generic advice first. Identify which stage failed, then debug that stage. After diagnosing, try a reasonable rerun if the problem looks recoverable.

### 1. Download failed

Most likely causes:

- Cookies missing or expired
- Douyin or Xiaohongshu blocked the automated browser
- Playwright not installed
- Page returned login, verification, or anti-bot content
- Video URL format changed

What to check:

- Whether the cookies file exists and is valid
- Whether the target page really loads video content
- Whether the platform redirected to login or verification
- Whether the downloader returned `CAPTURE_FAILED`
- Whether the network is blocking the platform

If the failure looks recoverable, retry after the relevant fix. Examples include:

- rerun with a cookies file that was previously missing from the command
- rerun after correcting the URL
- rerun after Playwright or browser dependencies are fixed

For Douyin specifically:

- Suspect cookies first
- Then suspect anti-automation detection
- Then inspect API path changes or blob-only playback behavior

### 2. Audio extraction failed

Most likely causes:

- `ffmpeg` path is wrong
- Downloaded video is corrupted or empty
- Local path permissions are broken

What to check:

- `ffmpeg_path` in `config.json`
- Whether the video file was successfully created before cleanup
- Whether `output\downloads` and `output\audio` are writable

If `ffmpeg_path` or local output paths were the issue, fix that first and rerun the job.

### 3. OSS upload failed

Most likely causes:

- OSS key or secret invalid
- Bucket name or endpoint wrong
- Network problem

What to check:

- OSS credentials in `config.json`
- Endpoint format
- Bucket accessibility

If OSS credentials or endpoint values were wrong and have been corrected, rerun the job instead of stopping at the first failed attempt.

### 4. Cloud transcription failed

Most likely causes:

- DashScope API key invalid
- Uploaded file inaccessible
- DashScope service timeout or request failure

What to check:

- `dashscope_api_key`
- Whether OSS upload succeeded and returned a usable URL
- Exact error returned by the transcriber

If transcription failed because of a temporary cloud error, timeout, or a previously broken OSS URL that has now been fixed, rerun the job.

### 5. Distribution failed

This stage is downstream. Do not debug it until download and transcription already succeed.

What to check by target:

- `notion`: token, database/page target, integration permission
- `github`: token, repo path, local git state
- `flomo`: webhook or sender configuration

The pipeline may still complete partially if one send target fails, but the user-facing task is still incomplete if they requested that destination. Diagnose the send failure and rerun.

## Security Rules

Follow these rules every time:

- Never print or paste secrets from `config\config.json` into user-facing output.
- Never upload real `config.json`, cookies, or output artifacts to GitHub unless the user explicitly asks and understands the risk.
- Prefer `config.example.json` when sharing setup instructions.
- Treat cookies as sensitive credentials.
- If the user asks you to inspect a config file, summarize sensitive fields instead of echoing them verbatim.

## What Good Assistance Looks Like

When using this skill, the model should:

1. Recognize the platform and URL quickly.
2. Ask for cookies only when the platform likely needs them.
3. Default to audio-only (fast) mode unless the user explicitly asked to save the video with `--save-video`. Explain the speed tradeoff.
4. Prefer `--dry-run` before any sending.
5. Read the stage-specific failure and debug that stage only.
6. Explain whether the failure is in download, transcription, or sending.
7. Retry after a fix when the issue is recoverable.
8. Present full error details if the task remains blocked.
9. Preserve user secrets and avoid exposing config values.

## Common Mistakes To Avoid

- Do not assume transcription is local-only; OSS and DashScope are part of the current pipeline.
- Do not jump straight to Notion or GitHub debugging if download already failed.
- Do not treat missing cookies as a minor detail for Douyin.
- Do not recommend publishing `config.json`.
- Do not say the run succeeded until the result JSON shows `task_status: success`.
- Do not stop at a partial success when the requested distribution step has not completed.

## 经验沉淀（防坑指南）

### 1. `audio_only` 参数约定

所有 `downloaders/{platform}.py` 里的 `download()` 函数**必须**接受 `audio_only=None` 关键字参数，即使内部不用它。`main.py` 始终传 `audio_only=not save_video`，缺少此参数会导致 TypeError。

新加平台时，直接抄模板：

```python
def download(url, output_dir, task_id, cookies_path=None, audio_only=None):
    ...
```

### 2. Douyin 下载注意事项

- **Playwright cookies 必须与浏览器版本匹配**。cookies 过期后 Playwright 会静默失败（`CAPTURE_FAILED`），不会报 401。
- 如果 `CAPTURE_FAILED`，先尝试用 `browser-mcp` 的 Puppeteer 验证 cookies 是否有效：在浏览器中打开 `https://www.douyin.com/video/{video_id}`，检查页面是否正常渲染视频。
- 兜底方案：yt-dlp + cookies 文件，但 yt-dlp 对 Douyin 支持不稳定，优先 Playwright。
- Douyin `jingxuan?modal_id=` 类 URL 会被自动转为 `https://www.douyin.com/video/{modal_id}`。

### 3. Notion 标题来源

`get_title()` 的返回值会被用作 Notion 页面标题。

- **Bilibili**: `you-get --info` 提取标题，失败时 fallback 到 `yt-dlp --get-title`
- **Douyin**: 从 Playwright 拦截的 API 响应 `aweme_detail.desc` 提取，存储在 `DouyinDownloader.title` 中
- 如果所有方法都失败，回退为 `{platform}_{task_id}`

### 4. 新对话的 skill 缓存行为

SKILL.md 在本对话中**只加载一次**（首次 `skill()` 调用时）。后续修改 SKILL.md 文件不会影响当前对话。如果需要让修改生效：
- 等待新对话（推荐）
- 或在本对话中手动 `skill("universal-transcriber")` 重载

因此，如果发现 AI 使用了过时的 `.codex` 路径或旧参数，原因是此对话早期加载的 SKILL.md 缓存未更新，不影响新对话。

### 5. 安全执行顺序

当用户同时给出 `--send notion` 等分发目标时：
1. 先确认 cookies 可用（对 Douyin 强制检查）
2. 直接运行完整命令（不需要先 `--dry-run`，因为分发失败可重试且不影响转录）
3. 如果下载阶段失败，优先怀疑 cookies 过期
4. 如果转录阶段失败，检查 OSS 上传是否成功
5. 最后才排查 Notion/GitHub 分发问题

## Maintenance Notes

If the skill stops working after a platform site change, inspect these areas first:

- `downloaders\*.py`
- `pipeline\downloader.py`
- `dispatcher.py`
- `config\send_rules.yaml`

If behavior changes, update this skill file so the operational guidance stays aligned with the code.
