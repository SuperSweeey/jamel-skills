from pathlib import Path

from downloaders.common import run_yt_dlp_download, run_yt_dlp_get_title


def download(url, output_dir, task_id, cookies_path=None):
    output_path = Path(output_dir) / f"bilibili_{task_id}.mp4"
    return run_yt_dlp_download("B站", url, output_path, cookies_path=cookies_path)


def get_title(url, cookies_path=None):
    return run_yt_dlp_get_title(url, cookies_path=cookies_path)
