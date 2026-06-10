# First Run Setup

This guide is for a first-time user who does not yet know which keys are required.

Start with the read-only setup check:

```powershell
cd skill位置
python .\scripts\check_setup.py
```

Do not start with a video link. If the basic setup is incomplete, fix it first.

## 1. Python

Check Python:

```powershell
python --version
```

If `python` is unavailable, try:

```powershell
py --version
```

Use whichever command works in later examples.

## 2. Python Packages

The basic pipeline needs:

- `requests`
- `dashscope`
- `oss2`
- `pyyaml`

Optional packages:

- `notion-client`, only for the official Notion client path. The sender can fall back to `requests`.
- `playwright`, only for downloader paths that need browser automation.

Before installing packages, check connectivity to GitHub, npm, and PyPI. If any response takes more than 2 seconds, configure mirrors first.

Install only after connectivity and package-risk checks:

```powershell
pip install requests dashscope oss2 pyyaml notion-client playwright
```

## 3. ffmpeg

The pipeline uses ffmpeg to extract and convert audio.

Option A: put `ffmpeg.exe` on PATH.

Option B: set the full path in `config\config.json`:

```json
{
  "ffmpeg_path": "D:\\Tools\\ffmpeg\\bin\\ffmpeg.exe"
}
```

Verify with:

```powershell
python .\scripts\check_setup.py
```

## 4. config.json

Create:

```powershell
C:\Users\26084\.codex\skills\universal-transcriber\config\config.json
```

Never publish this file. It contains secrets.

Minimal template:

```json
{
  "oss_access_key_id": "YOUR_OSS_ACCESS_KEY_ID",
  "oss_access_key_secret": "YOUR_OSS_ACCESS_KEY_SECRET",
  "oss_bucket_name": "YOUR_OSS_BUCKET_NAME",
  "oss_endpoint": "oss-cn-beijing.aliyuncs.com",
  "dashscope_api_key": "YOUR_DASHSCOPE_API_KEY",
  "notion_token": "",
  "notion_database_id": "",
  "ffmpeg_path": "",
  "output_dir": "./output",
  "zhipu_api_key": "",
  "zhipu_api_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
  "title_model": "qwen3.5-flash",
  "title_api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "github_token": "",
  "github_user": "",
  "github_repo": "",
  "github_repo_dir": ""
}
```

## 5. DashScope

DashScope is required for cloud transcription.

What to prepare:

- `dashscope_api_key`

Where to put it:

```json
{
  "dashscope_api_key": "YOUR_DASHSCOPE_API_KEY"
}
```

After filling it, rerun:

```powershell
python .\scripts\check_setup.py
```

## 6. OSS

OSS is required because the current transcription flow uploads audio to OSS, creates a temporary signed URL, and gives that URL to DashScope.

What to prepare:

- `oss_access_key_id`
- `oss_access_key_secret`
- `oss_bucket_name`
- `oss_endpoint`

Recommended security settings:

- Use the least-privilege account available.
- Restrict permissions to the target bucket when possible.
- Do not reuse a personal all-powerful key if a scoped key is available.
- Do not commit or screenshot secrets.

Where to put the values:

```json
{
  "oss_access_key_id": "YOUR_OSS_ACCESS_KEY_ID",
  "oss_access_key_secret": "YOUR_OSS_ACCESS_KEY_SECRET",
  "oss_bucket_name": "YOUR_OSS_BUCKET_NAME",
  "oss_endpoint": "oss-cn-beijing.aliyuncs.com"
}
```

Rerun:

```powershell
python .\scripts\check_setup.py
```

## 7. Save Target

After the basic setup passes, ask where the transcript should be saved:

- Local file
- Notion
- GitHub
- Flomo
- Multiple targets

Local output needs no extra sender config.

Check a chosen target:

```powershell
python .\scripts\check_setup.py --send local
python .\scripts\check_setup.py --send notion
python .\scripts\check_setup.py --send github
python .\scripts\check_setup.py --send flomo
```

## 8. Notion Setup

Only needed if the user chooses Notion.

Required:

- `notion_token`
- A database or page rule in `config\send_rules.yaml`

Config:

```json
{
  "notion_token": "YOUR_NOTION_TOKEN"
}
```

Rules file:

```yaml
default_notion_database: default

notion_databases:
  default: "YOUR_NOTION_DATABASE_OR_PAGE_ID"
```

Then check:

```powershell
python .\scripts\check_setup.py --send notion
```

## 9. GitHub Setup

Only needed if the user chooses GitHub publishing.

Required:

- `github_token`
- `github_user`
- `github_repo`
- `github_repo_dir`

Config:

```json
{
  "github_token": "YOUR_GITHUB_TOKEN",
  "github_user": "YOUR_GITHUB_USER",
  "github_repo": "YOUR_REPO_NAME",
  "github_repo_dir": "D:\\path\\to\\local\\repo"
}
```

The local repo must exist and be safe to commit and push.

Then check:

```powershell
python .\scripts\check_setup.py --send github
```

## 10. Flomo Setup

Only needed if the user chooses Flomo.

Set the API key in the current PowerShell session:

```powershell
$env:FLOMO_API_KEY="YOUR_FLOMO_API_KEY"
```

Then check:

```powershell
python .\scripts\check_setup.py --send flomo
```

## 11. Cookies

Cookies are not required before the first run.

Start without cookies. Add cookies only when download fails because of:

- Login required
- Verification or captcha
- Age, region, or member-only restriction
- Rate limit
- Platform blocks automated download

Then rerun with:

```powershell
python .\main.py --platform douyin --url "https://v.douyin.com/xxxx/" --cookies ".\config\douyin_cookies.txt" --send local
```

Treat cookies as secrets.

## 12. After Setup Passes

Basic validation:

```powershell
python .\scripts\check_setup.py
```

Then choose the task details:

1. Video link
2. Platform
3. Save target

Example dry run:

```powershell
python .\main.py --platform youtube --url "https://www.youtube.com/watch?v=xxxx" --dry-run
```

Example local save:

```powershell
python .\main.py --platform youtube --url "https://www.youtube.com/watch?v=xxxx" --send local
```
