import subprocess
import time
from pathlib import Path


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


def run_yt_dlp_download(platform: str, url: str, output_path: Path, cookies_path=None, max_retries: int = 3) -> str:
    cmd = ["yt-dlp", "-o", str(output_path), "--merge-output-format", "mp4", url]
    if cookies_path:
        cmd += ["--cookies", str(cookies_path)]

    last_error = ""
    for attempt in range(1, max_retries + 1):
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            for file_path in output_path.parent.glob(f"{output_path.stem}*"):
                return str(file_path)
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
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return None
