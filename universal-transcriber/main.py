#!/usr/bin/env python3
import sys
import uuid
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "config.json"
OUTPUT_DIR = BASE_DIR / "output"

sys.path.insert(0, str(BASE_DIR))

from pipeline.config import Config
from pipeline.logger import Logger
from pipeline.audio_extractor import AudioExtractor
from pipeline.oss_uploader import OSSUploader
from pipeline.transcriber import CloudTranscriber
from dispatcher import dispatch

PLATFORMS = ["douyin", "bilibili", "youtube", "xiaohongshu"]
SENDERS = ["notion", "github", "flomo"]

def get_downloader(platform):
    import importlib.util
    path = BASE_DIR / "downloaders" / f"{platform}.py"
    spec = importlib.util.spec_from_file_location(platform, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def parse_send_targets(args):
    targets = []
    for i, arg in enumerate(args):
        if arg == "--send" and i + 1 < len(args):
            targets.append(args[i + 1])
    return targets

def cleanup_video(video_path):
    """音频提取完成后删除视频文件，释放空间"""
    try:
        if video_path and os.path.exists(str(video_path)):
            os.remove(str(video_path))
            Logger.info(f"已删除视频文件: {os.path.basename(str(video_path))}")
    except Exception as e:
        Logger.warning(f"删除视频文件失败: {e}")

def main():
    args = sys.argv[1:]

    if "--platform" not in args or "--url" not in args:
        print(json.dumps({
            "error": "缺少必要参数",
            "usage": "python3 main.py --platform <平台> --url <链接> [--cookies <路径>] [--send notion] [--send github] [--send flomo] [--dry-run]",
            "platforms": PLATFORMS
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    platform = args[args.index("--platform") + 1]
    url = args[args.index("--url") + 1]
    cookies_path = args[args.index("--cookies") + 1] if "--cookies" in args else None
    send_targets = parse_send_targets(args)
    dry_run = "--dry-run" in args

    if platform not in PLATFORMS:
        print(json.dumps({"error": f"不支持的平台: {platform}", "platforms": PLATFORMS}, ensure_ascii=False))
        sys.exit(1)

    task_id = str(uuid.uuid4())[:8]
    config = Config.from_file(str(CONFIG_PATH))

    download_dir = OUTPUT_DIR / "downloads"
    audio_dir = OUTPUT_DIR / "audio"
    transcripts_dir = OUTPUT_DIR / "transcripts"
    for d in [download_dir, audio_dir, transcripts_dir]:
        d.mkdir(parents=True, exist_ok=True)

    Logger.info(f"[{task_id}] 平台: {platform} | URL: {url} | dry-run: {dry_run}")
    if send_targets:
        Logger.info(f"[{task_id}] 分发目标: {', '.join(send_targets)}")
    else:
        Logger.info(f"[{task_id}] 仅保存本地，未指定分发目标")

    downloader = get_downloader(platform)
    oss_object = None
    uploader = None
    video_path = None

    try:
        # Step 1: 下载
        Logger.step(1, 5, "下载视频", task_id)
        video_path = downloader.download(url, str(download_dir), task_id, cookies_path)
        Logger.info(f"下载完成: {video_path}")

        # Step 2: 提取音频
        Logger.step(2, 5, "提取音频", task_id)
        extractor = AudioExtractor(str(audio_dir), config.ffmpeg_path)
        audio_path = extractor.extract(video_path, f"audio_{task_id}")
        Logger.info(f"音频提取完成: {audio_path}")

        # 音频提取完成后立即删除视频，释放空间
        cleanup_video(video_path)
        video_path = None

        # Step 3: 上传OSS
        Logger.step(3, 5, "上传到OSS", task_id)
        uploader = OSSUploader(
            config.oss_access_key_id,
            config.oss_access_key_secret,
            config.oss_bucket_name,
            config.oss_endpoint,
        )
        oss_url, oss_object = uploader.upload_audio(audio_path)
        Logger.info("OSS上传完成")

        # Step 4: 转录
        Logger.step(4, 5, "云端转录", task_id)
        transcriber = CloudTranscriber(config.dashscope_api_key)
        transcript = transcriber.transcribe(oss_url, task_id=task_id)
        transcript_path = transcripts_dir / f"transcript_{task_id}.txt"
        transcript_path.write_text(transcript, encoding="utf-8")
        Logger.info(f"转录完成: {transcript_path}")
        print(f"\n转录预览（前300字）:\n{transcript[:300]}\n")

        # Step 5: 分发
        Logger.step(5, 5, "分发内容", task_id)
        title = downloader.get_title(url, cookies_path) or f"{platform}_{task_id}"
        dispatch_result = dispatch(
            transcript,
            title,
            url,
            platform,
            config,
            cli_targets=send_targets if send_targets else None,
            dry_run=dry_run
        )
        dispatch_result["task_id"] = task_id
        dispatch_result["transcript_file"] = str(transcript_path)

        if not dry_run:
            for target, res in dispatch_result["send_results"].items():
                if res == "success":
                    Logger.info(f"{target} 分发成功")
                else:
                    Logger.warning(f"{target} 分发失败（不影响其他目标）: {res}")

        print(f"\n✅ 完成！转录文件: {transcript_path}\n")

    except Exception as e:
        cleanup_video(video_path)
        error_result = {
            "task_id": task_id,
            "task_status": "failed",
            "platform": platform,
            "url": url,
            "error": str(e)
        }
        sys.exit(1)
    finally:
        try:
            if oss_object and uploader:
                uploader.delete_object(oss_object)
        except:
            pass

if __name__ == "__main__":
    main()
