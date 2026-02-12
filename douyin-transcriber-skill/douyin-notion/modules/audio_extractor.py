"""
音频提取模块
使用ffmpeg提取音频
"""

import subprocess
from pathlib import Path
from typing import Optional

from .logger import Logger


class AudioExtractor:
    """音频提取器 - 使用ffmpeg"""

    def __init__(self, output_dir: str = "./audio", ffmpeg_path: str = ""):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_path = ffmpeg_path or "ffmpeg"

        if not self._check_ffmpeg():
            raise RuntimeError("ffmpeg未找到。请安装ffmpeg并添加到PATH")

    def _check_ffmpeg(self) -> bool:
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except:
            return False

    def extract(self, video_path: str, output_filename: Optional[str] = None) -> str:
        """从视频提取音频"""
        video_file = Path(video_path)
        if not video_file.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        if output_filename:
            output_file = self.output_dir / f"{output_filename}.wav"
        else:
            output_file = self.output_dir / f"{video_file.stem}.wav"

        Logger.info(f"提取音频: {video_file.name} -> {output_file.name}")

        cmd = [
            self.ffmpeg_path,
            "-i",
            str(video_file),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-y",
            str(output_file),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg错误: {result.stderr}")

        if not output_file.exists():
            raise RuntimeError("音频文件未创建")

        file_size = output_file.stat().st_size / (1024 * 1024)
        Logger.success(f"音频提取完成: {output_file.name} ({file_size:.2f} MB)")

        return str(output_file)
