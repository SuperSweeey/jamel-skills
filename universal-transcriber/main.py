#!/usr/bin/env python3
import json
import os
import sys
import traceback
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "config.json"
OUTPUT_DIR = BASE_DIR / "output"

sys.path.insert(0, str(BASE_DIR))

from dispatcher import dispatch
from pipeline.audio_extractor import AudioExtractor
from pipeline.config import Config
from pipeline.logger import Logger
from pipeline.oss_uploader import OSSUploader
from pipeline.transcriber import CloudTranscriber

PLATFORMS = ["douyin", "bilibili", "youtube", "xiaohongshu"]
SENDERS = ["local", "notion", "github", "flomo"]


def configure_console():
    """Force UTF-8 console output on Windows to avoid mojibake."""
    if os.name == "nt":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleCP(65001)
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass

    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


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


def cleanup_video(video_path, keep_video=False):
    """Delete the downloaded video unless the user asked to keep it."""
    try:
        if not video_path or not os.path.exists(str(video_path)):
            return
        if keep_video:
            Logger.info(f"保留视频文件: {os.path.basename(str(video_path))}")
            return
        os.remove(str(video_path))
        Logger.info(f"已删除视频文件: {os.path.basename(str(video_path))}")
    except Exception as e:
        Logger.warning(f"删除视频文件失败: {e}")


def main():
    configure_console()
    args = sys.argv[1:]

    if "--platform" not in args or "--url" not in args:
        print(
            json.dumps(
                {
                    "error": "缺少必要参数",
                    "usage": (
                        "python3 main.py --platform <平台> --url <链接> "
                        "[--cookies <路径>] [--send notion] [--send github] "
                        "[--send flomo] [--dry-run] [--save-video]"
                    ),
                    "platforms": PLATFORMS,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.exit(1)

    platform = args[args.index("--platform") + 1]
    url = args[args.index("--url") + 1]
    cookies_path = args[args.index("--cookies") + 1] if "--cookies" in args else None
    send_targets = parse_send_targets(args)
    dry_run = "--dry-run" in args
    save_video = "--save-video" in args or "--keep-video" in args

    if platform not in PLATFORMS:
        print(json.dumps({"error": f"不支持的平台: {platform}", "platforms": PLATFORMS}, ensure_ascii=False))
        sys.exit(1)

    task_id = str(uuid.uuid4())[:8]
    config = Config.from_file(str(CONFIG_PATH))

    download_dir = OUTPUT_DIR / "downloads"
    audio_dir = OUTPUT_DIR / "audio"
    transcripts_dir = OUTPUT_DIR / "transcripts"
    for directory in [download_dir, audio_dir, transcripts_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    Logger.info(f"[{task_id}] 平台: {platform} | URL: {url} | dry-run: {dry_run} | save-video: {save_video}")
    if send_targets:
        Logger.info(f"[{task_id}] 分发目标: {', '.join(send_targets)}")
    else:
        Logger.info(f"[{task_id}] 仅保存本地，未指定分发目标")

    downloader = get_downloader(platform)
    oss_object = None
    uploader = None
    source_path = None
    stage = "初始化"

    try:
        stage = "下载视频/音频"
        Logger.step(1, 5, "下载视频/音频", task_id)
        source_path = downloader.download(url, str(download_dir), task_id, cookies_path, audio_only=not save_video)
        Logger.info(f"下载完成: {source_path}")

        stage = "提取音频"
        Logger.step(2, 5, "提取音频", task_id)
        extractor = AudioExtractor(str(audio_dir), config.ffmpeg_path)
        audio_path = extractor.extract(source_path, f"audio_{task_id}")
        Logger.info(f"音频提取完成: {audio_path}")

        if save_video:
            Logger.info(f"保留视频文件: {Path(source_path).name}")
        else:
            if source_path and os.path.exists(source_path):
                os.remove(source_path)
                Logger.info(f"已删除临时源文件: {Path(source_path).name}")
            source_path = None

        stage = "上传OSS"
        Logger.step(3, 5, "上传到OSS", task_id)
        uploader = OSSUploader(
            config.oss_access_key_id,
            config.oss_access_key_secret,
            config.oss_bucket_name,
            config.oss_endpoint,
        )
        oss_url, oss_object = uploader.upload_audio(audio_path)
        Logger.info("OSS上传完成")

        stage = "云端转录"
        Logger.step(4, 5, "云端转录", task_id)
        transcriber = CloudTranscriber(config.dashscope_api_key)
        transcript = transcriber.transcribe(oss_url, task_id=task_id)
        transcript_path = transcripts_dir / f"transcript_{task_id}.txt"
        transcript_path.write_text(transcript, encoding="utf-8")
        Logger.info(f"转录完成: {transcript_path}")
        print(f"\n转录预览（前300字）:\n{transcript[:300]}\n")

        stage = "分发内容"
        Logger.step(5, 5, "分发内容", task_id)
        title = downloader.get_title(url, cookies_path) or f"{platform}_{task_id}"
        dispatch_result = dispatch(
            transcript,
            title,
            url,
            platform,
            config,
            cli_targets=send_targets if send_targets else None,
            dry_run=dry_run,
        )
        dispatch_result["task_id"] = task_id
        dispatch_result["transcript_file"] = str(transcript_path)
        dispatch_result["source_file"] = str(source_path) if save_video and source_path else None
        dispatch_result["source_saved"] = bool(save_video and source_path)

        if not dry_run:
            for target, res in dispatch_result["send_results"].items():
                if res == "success":
                    Logger.info(f"{target} 分发成功")
                else:
                    Logger.warning(f"{target} 分发失败（不影响其他目标）: {res}")

        print(f"\n完成！转录文件: {transcript_path}")
        if save_video and source_path:
            print(f"保留的视频文件: {source_path}\n")
        else:
            print("")

    except Exception as e:
        cleanup_video(source_path, keep_video=save_video)
        error_result = {
            "task_id": task_id,
            "task_status": "failed",
            "platform": platform,
            "url": url,
            "stage": stage,
            "error": str(e),
            "source_file": str(source_path) if save_video and source_path else None,
            "source_saved": bool(save_video and source_path),
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2), file=sys.stderr)
        Logger.error(f"任务失败，阶段: {stage} | 原因: {e}", task_id)
        traceback.print_exc()
        sys.exit(1)
    finally:
        try:
            if oss_object and uploader:
                uploader.delete_object(oss_object)
        except Exception:
            pass


if __name__ == "__main__":
    main()
