from pathlib import Path

from downloaders.common import run_yt_dlp_download, run_yt_dlp_get_title


def download(url, output_dir, task_id, cookies_path=None, audio_only=True):
    output_path = Path(output_dir) / f"xiaohongshu_{task_id}"
    return run_yt_dlp_download("小红书", url, output_path, cookies_path=cookies_path, audio_only=audio_only)


def get_title(url, cookies_path=None):
    return run_yt_dlp_get_title(url, cookies_path=cookies_path)
