import subprocess
from pathlib import Path

def download(url, output_dir, task_id, cookies_path=None):
    output_path = Path(output_dir) / f"bilibili_{task_id}.mp4"
    cmd = ["yt-dlp", "-o", str(output_path), "--merge-output-format", "mp4", url]
    if cookies_path:
        cmd += ["--cookies", str(cookies_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"B站下载失败: {result.stderr}")
    for f in Path(output_dir).glob(f"bilibili_{task_id}*"):
        return str(f)
    raise RuntimeError("下载完成但找不到文件")

def get_title(url, cookies_path=None):
    cmd = ["yt-dlp", "--get-title", url]
    if cookies_path:
        cmd += ["--cookies", str(cookies_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return None
