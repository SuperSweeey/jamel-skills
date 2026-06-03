import subprocess
import time
from pathlib import Path

from downloaders.common import find_ffmpeg, run_yt_dlp_download, run_yt_dlp_get_title


def _try_youget_download(url, output_dir, cookies_path=None, timeout=300):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    before = set(output_dir.iterdir())

    cmd = ["you-get", "-o", str(output_dir), "--format", "dash-flv360-HEVC", url]
    if cookies_path:
        cmd += ["--cookies", str(cookies_path)]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        stderr = (result.stderr or result.stdout).strip()
        after = set(output_dir.iterdir())
        new = [f for f in (after - before) if f.suffix.lower() in (".mp4", ".m4a")]
        if new:
            return result, sorted(new, key=lambda f: f.stat().st_ctime)
        raise RuntimeError(f"you-get 返回错误: {stderr}")

    after = set(output_dir.iterdir())
    new = sorted(
        [f for f in (after - before) if f.suffix.lower() in (".mp4", ".m4a")],
        key=lambda f: f.stat().st_ctime,
    )
    return result, new


def get_title(url, cookies_path=None):
    try:
        result = subprocess.run(
            ["you-get", "--info", url],
            capture_output=True, text=True, timeout=30,
        )
        for line in (result.stderr or result.stdout).splitlines():
            if line.startswith("title:"):
                return line.split("title:", 1)[1].strip()
    except Exception:
        pass
    try:
        return run_yt_dlp_get_title(url, cookies_path=cookies_path)
    except Exception:
        pass
    return None


def _merge_audio_video(video_file, audio_file, output_path, ffmpeg_path):
    cmd = [ffmpeg_path, "-i", str(video_file), "-i", str(audio_file), "-c", "copy", "-y", str(output_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode == 0:
        for p in (video_file, audio_file):
            try:
                p.unlink()
            except OSError:
                pass
        return str(output_path)
    return str(video_file)


def download(url, output_dir, task_id, cookies_path=None, audio_only=True):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        ffmpeg_path = "ffmpeg"

    try:
        result, new_files = _try_youget_download(url, output_dir, cookies_path)
    except Exception as e:
        print(f"[WARN] you-get 失败，切换到 yt-dlp: {e}")
        out_path = output_dir / f"bilibili_{task_id}.mp4"
        if audio_only:
            out_path = output_dir / f"bilibili_audio_{task_id}.m4a"
            cmd = ["yt-dlp", "-f", "bestaudio", "-o", str(out_path), url]
            if cookies_path:
                cmd += ["--cookies", str(cookies_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                raise RuntimeError(f"yt-dlp 音频下载失败: {result.stderr.strip()}")
            return str(out_path)
        return run_yt_dlp_download("B站", url, out_path, cookies_path=cookies_path)

    video_parts = [f for f in new_files if "[00]" in f.name]
    audio_parts = [f for f in new_files if "[01]" in f.name]
    other_parts = [f for f in new_files if "[00]" not in f.name and "[01]" not in f.name]

    if audio_only and audio_parts:
        audio_file = audio_parts[0]
        for p in video_parts + [f for f in audio_parts if f is not audio_file]:
            try:
                p.unlink()
            except OSError:
                pass
        return str(audio_file)

    if video_parts and audio_parts:
        merged = output_dir / f"bilibili_{task_id}.mp4"
        return _merge_audio_video(video_parts[0], audio_parts[0], merged, ffmpeg_path)

    if len(other_parts) == 1:
        return str(other_parts[0])

    return str(new_files[-1])
