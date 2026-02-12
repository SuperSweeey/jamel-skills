#!/usr/bin/env python3
"""
抖音视频转录工具 - 主程序（模块化版本）

现在你可以自由组合各个模块：
- 只下载视频
- 下载+转录+保存本地
- 完整流程（包括Notion同步）
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules import (
    Config,
    Logger,
    DouyinDownloader,
    AudioExtractor,
    OSSUploader,
    CloudTranscriber,
    NotionSync,
    TranscriptionPipeline,
)


def create_config_template():
    """创建配置文件模板"""
    import json

    template = {
        "oss_access_key_id": "你的AccessKey ID",
        "oss_access_key_secret": "你的AccessKey Secret",
        "oss_bucket_name": "你的Bucket名称",
        "oss_endpoint": "oss-cn-beijing.aliyuncs.com",
        "dashscope_api_key": "sk-你的DashScope API Key",
        "notion_token": "secret_你的Notion Token",
        "notion_database_id": "你的数据库ID",
        "ffmpeg_path": "tools\\ffmpeg\\bin\\ffmpeg.exe",
        "output_dir": "./output",
    }

    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)

    print("[OK] 已创建 config.json 模板文件")


def main():
    """CLI入口"""
    import argparse

    parser = argparse.ArgumentParser(description="抖音视频转录工具 - 模块化版本")
    parser.add_argument("--url", type=str, help="抖音视频URL")
    parser.add_argument("--batch", type=str, help="批量处理URL列表文件")
    parser.add_argument("--config", type=str, default="config.json")
    parser.add_argument("--download-only", action="store_true", help="仅下载视频")
    parser.add_argument("--no-notion", action="store_true", help="不保存到Notion")
    parser.add_argument("--init", action="store_true", help="创建配置文件模板")

    args = parser.parse_args()

    if args.init:
        create_config_template()
        return

    if not args.url and not args.batch:
        parser.print_help()
        print("\n[ERROR] 必须提供 --url 或 --batch 参数")
        print("首次使用请运行: python main.py --init")
        return

    if not os.path.exists(args.config):
        print(f"[ERROR] 配置文件不存在: {args.config}")
        print("请运行: python main.py --init")
        return

    try:
        config = Config.from_file(args.config)

        # 仅下载视频
        if args.download_only:
            downloader = DouyinDownloader(output_dir="./downloads")

            if args.batch:
                with open(args.batch, "r", encoding="utf-8") as f:
                    urls = [line.strip() for line in f if line.strip()]

                for url in urls:
                    video_path = downloader.download(url)
                    print(f"[OK] {video_path}")
            else:
                video_path = downloader.download(args.url)
                print(f"\n[OK] 视频已保存: {video_path}")
            return

        # 完整流程
        pipeline = TranscriptionPipeline(config)

        if args.batch:
            with open(args.batch, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip()]

            for url in urls:
                pipeline.process(url, save_to_notion=not args.no_notion)
        else:
            result = pipeline.process(args.url, save_to_notion=not args.no_notion)

            if result["success"] and args.no_notion:
                print("\n转录结果预览:")
                print(result["text"][:500] + "...")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
