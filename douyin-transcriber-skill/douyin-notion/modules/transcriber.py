"""
云端转录模块
阿里云Paraformer语音识别
"""

import json
import urllib.request
from typing import List

from .logger import Logger


class CloudTranscriber:
    """阿里云Paraformer语音识别"""

    def __init__(self, api_key: str, model: str = "paraformer-v2"):
        try:
            import dashscope
            from dashscope.audio.asr import Transcription
        except ImportError:
            raise RuntimeError("dashscope库未安装，请运行: pip install dashscope")

        dashscope.api_key = api_key
        self.model = model
        self.Transcription = Transcription

    def transcribe(
        self, oss_url: str, language_hints: List[str] = None, task_id: str = ""
    ) -> str:
        """转录音频文件"""
        if language_hints is None:
            language_hints = ["zh", "en"]

        Logger.step(4, 5, "提交转录任务", task_id)

        task_response = self.Transcription.async_call(
            model=self.model, file_urls=[oss_url], language_hints=language_hints
        )

        Logger.info(f"转录任务已提交: {task_response.output.task_id}", task_id)

        Logger.info("等待转录完成...", task_id)
        transcription_response = self.Transcription.wait(
            task=task_response.output.task_id
        )

        if transcription_response.status_code != 200:
            raise RuntimeError(f"转录失败: {transcription_response.output.message}")

        results = []
        for result in transcription_response.output.get("results", []):
            if result.get("subtask_status") == "SUCCEEDED":
                transcript_url = result["transcription_url"]
                transcript_data = json.loads(
                    urllib.request.urlopen(transcript_url).read().decode("utf-8")
                )

                for transcript in transcript_data.get("transcripts", []):
                    text = transcript.get("text", "")
                    if text:
                        results.append(text)
            else:
                Logger.warning(
                    f"子任务失败: {result.get('message', 'Unknown error')}", task_id
                )

        if not results:
            raise RuntimeError("转录结果为空")

        full_text = "\n".join(results)
        Logger.success(f"转录完成，共 {len(full_text)} 字符", task_id)

        return full_text
