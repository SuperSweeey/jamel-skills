"""
流程编排模块
协调所有组件完成转录流程
"""

import os
import uuid
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from .config import Config
from .logger import Logger
from .downloader import DouyinDownloader
from .audio_extractor import AudioExtractor
from .oss_uploader import OSSUploader
from .transcriber import CloudTranscriber
from .notion_sync import NotionSync


class TranscriptionPipeline:
    """转录流程管道"""

    def __init__(self, config: Config):
        self.config = config

        self.output_dir = Path(config.output_dir)
        self.download_dir = self.output_dir / "downloads"
        self.audio_dir = self.output_dir / "audio"
        self.transcripts_dir = self.output_dir / "transcripts"

        for d in [
            self.output_dir,
            self.download_dir,
            self.audio_dir,
            self.transcripts_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

        Logger.info("初始化组件...")

        self.downloader = DouyinDownloader(str(self.download_dir))
        self.audio_extractor = AudioExtractor(str(self.audio_dir), config.ffmpeg_path)
        self.oss_uploader = OSSUploader(
            config.oss_access_key_id,
            config.oss_access_key_secret,
            config.oss_bucket_name,
            config.oss_endpoint,
        )
        self.transcriber = CloudTranscriber(config.dashscope_api_key)
        self.notion = NotionSync(config.notion_token, config.notion_database_id)

        Logger.success("所有组件初始化完成")

    def process(self, url: str, save_to_notion: bool = True) -> Dict:
        """处理单个抖音视频"""
        task_id = str(uuid.uuid4())[:8]

        print(f"\n{'=' * 70}")
        print(f"[{task_id}] 开始处理: {url}")
        print(f"{'=' * 70}\n")

        video_path = None
        audio_path = None
        oss_object = None

        try:
            Logger.step(1, 5, "下载视频", task_id)
            video_path = self.downloader.download(url, f"video_{task_id}")

            Logger.step(2, 5, "提取音频", task_id)
            audio_path = self.audio_extractor.extract(video_path, f"audio_{task_id}")

            Logger.step(3, 5, "上传到OSS", task_id)
            oss_url, oss_object = self.oss_uploader.upload_audio(audio_path)

            Logger.step(4, 5, "云端转录", task_id)
            text = self.transcriber.transcribe(oss_url, task_id=task_id)

            # 保存转录文本到本地文件
            transcript_file = self.transcripts_dir / f"transcript_{task_id}.txt"
            with open(transcript_file, "w", encoding="utf-8") as f:
                f.write(f"URL: {url}\n")
                f.write(f"Task ID: {task_id}\n")
                f.write(f"Time: {datetime.now().isoformat()}\n")
                f.write("=" * 70 + "\n\n")
                f.write(text)
            Logger.success(f"转录文本已保存: {transcript_file.name}")

            if save_to_notion:
                Logger.step(5, 5, "保存到Notion", task_id)
                try:
                    self.notion.create_page(f"抖音_{task_id}", url, text)
                except Exception as e:
                    Logger.warning(f"Notion同步失败: {e}")

            self._cleanup(video_path, audio_path, oss_object)

            print(f"\n{'=' * 70}")
            Logger.success(f"处理完成! 任务ID: {task_id}", task_id)
            print(f"{'=' * 70}\n")

            return {"success": True, "task_id": task_id, "text": text, "url": url}

        except Exception as e:
            self._cleanup(video_path, audio_path, oss_object)
            Logger.error(f"处理失败: {e}", task_id)
            return {"success": False, "task_id": task_id, "error": str(e), "url": url}

    def _cleanup(
        self,
        video_path: Optional[str],
        audio_path: Optional[str],
        oss_object: Optional[str],
    ):
        """清理临时文件 - 保留原视频"""
        try:
            if video_path and os.path.exists(video_path):
                Logger.info(f"保留视频文件: {os.path.basename(video_path)}")

            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
                Logger.info("已删除临时音频文件")

            if oss_object:
                self.oss_uploader.delete_object(oss_object)
        except Exception as e:
            Logger.warning(f"清理文件失败: {e}")
