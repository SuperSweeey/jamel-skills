"""
配置管理模块
"""

import json
from dataclasses import dataclass


@dataclass
class Config:
    """配置类"""

    # 阿里云OSS
    oss_access_key_id: str
    oss_access_key_secret: str
    oss_bucket_name: str
    oss_endpoint: str
    # 阿里云DashScope
    dashscope_api_key: str
    # Notion
    notion_token: str
    notion_database_id: str
    # FFmpeg路径（可选，如果在系统PATH中则不需要）
    ffmpeg_path: str = ""
    output_dir: str = "./output"

    @classmethod
    def from_file(cls, filepath: str = "config.json") -> "Config":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)
