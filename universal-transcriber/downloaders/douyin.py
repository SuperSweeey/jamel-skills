import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))

from downloader import DouyinDownloader

_last_title = None

def download(url, output_dir, task_id, cookies_path=None, audio_only=None):
    global _last_title
    dl = DouyinDownloader(output_dir, cookies_path=cookies_path)
    result = dl.download(url, task_id, audio_only=bool(audio_only))
    if not result:
        raise RuntimeError("抖音下载失败")
    if dl.title:
        _last_title = dl.title
    return result

def get_title(url, cookies_path=None):
    return _last_title
