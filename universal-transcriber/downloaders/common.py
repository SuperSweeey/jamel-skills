import json
import shutil
import subprocess
import time
from pathlib import Path


def find_ffmpeg():
    """先查系统 PATH，再读 config.json，返回 ffmpeg 可执行路径或 None。"""
    which = shutil.which("ffmpeg")
    if which:
        return which
    config_path = Path(__file__).parent.parent / "config" / "config.json"
    try:
        with open(config_path, encoding="utf-8") as f:
            cfg = json.load(f)
        fp = cfg.get("ffmpeg_path", "")
        if fp and Path(fp).exists():
            return fp
    except Exception:
        pass
    return None


def _get_ffmpeg_dir():
    ffmpeg = find_ffmpeg()
    if ffmpeg:
        return str(Path(ffmpeg).parent)
    return None


def classify_yt_dlp_error(stderr: str) -> tuple[str, str]:
    text = (stderr or "").strip()
    lower = text.lower()

    if "too many requests" in lower or "http error 429" in lower:
        return "RATE_LIMITED", "平台限流，建议稍后重试或补充 cookies。"
    if "no supported javascript runtime" in lower:
        return "JS_RUNTIME_MISSING", "缺少可用的 JavaScript runtime，建议安装 node 或 deno。"
    if "sign in" in lower or "cookies" in lower or "login" in lower:
        return "AUTH_REQUIRED", "平台要求登录态，建议提供有效 cookies。"
    if "private" in lower or "unavailable" in lower or "not available" in lower:
        return "UNAVAILABLE", "视频不可访问，可能已删除、私密或地域受限。"
    if "timed out" in lower or "timeout" in lower or "connection" in lower or "network" in lower:
        return "NETWORK", "网络波动导致下载失败，可稍后重试。"
    return "UNKNOWN", "下载器返回了未分类错误，请查看原始 stderr。"


def run_yt_dlp_download(platform: str, url: str, output_path: Path, cookies_path=None, max_retries: int = 3, audio_only: bool = True) -> str:
    cmd = ["yt-dlp", "-o", str(output_path)]
    if audio_only:
        cmd += ["-f", "bestaudio"]  # 直接拉音频流，无需 ffmpeg
    else:
        cmd += ["--merge-output-format", "mp4"]
    # Speed optimizations
    cmd += ["-N", "8"]  # 8 线程并行下载
    cmd += ["--no-embed-metadata"]  # 跳过元数据写入（避免 ffmpeg 依赖）
    # Use Node.js as JS runtime (required for YouTube)
    if shutil.which("node"):
        cmd += ["--js-runtimes", "node"]
    if cookies_path:
        cmd += ["--cookies", str(cookies_path)]
    cmd.append(url)  # URL must be last

    last_error = ""
    for attempt in range(1, max_retries + 1):
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        # Check if file was created even if exit code is non-zero
        # (yt-dlp sometimes fails on metadata post-processing but the file is fine)
        existing = list(output_path.parent.glob(f"{output_path.stem}*"))
        if existing:
            # Return the largest file (or the only non-.meta file)
            data_files = [f for f in existing if f.suffix != ".meta"]
            if data_files:
                return str(data_files[0])
            return str(existing[0])

        if result.returncode == 0:
            raise RuntimeError(f"{platform}下载完成但找不到输出文件: {output_path.parent}")

        last_error = result.stderr.strip() or result.stdout.strip()
        code, hint = classify_yt_dlp_error(last_error)
        retryable = code in {"RATE_LIMITED", "NETWORK"}
        if retryable and attempt < max_retries:
            time.sleep(3 * attempt)
            continue
        raise RuntimeError(f"{platform}下载失败[{code}]: {hint}\n原始错误: {last_error}")

    raise RuntimeError(f"{platform}下载失败: {last_error}")


def run_yt_dlp_get_title(url: str, cookies_path=None) -> str | None:
    cmd = ["yt-dlp", "--get-title", url]
    if cookies_path:
        cmd += ["--cookies", str(cookies_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        return result.stdout.strip()
    return None
