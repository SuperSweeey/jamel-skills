import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "pipeline"))

from downloader import DouyinDownloader

def download(url, output_dir, task_id, cookies_path=None):
    dl = DouyinDownloader(output_dir, cookies_path=cookies_path)
    result = dl.download(url, task_id)
    if not result:
        raise RuntimeError("抖音下载失败")
    return result

def get_title(url, cookies_path=None):
    return None
