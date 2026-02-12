"""
OSS上传模块
阿里云OSS文件上传
"""

import uuid
from pathlib import Path
from typing import Tuple

from .logger import Logger


class OSSUploader:
    """阿里云OSS上传器"""

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        bucket_name: str,
        endpoint: str,
    ):
        try:
            import oss2
        except ImportError:
            raise RuntimeError("oss2库未安装，请运行: pip install oss2")

        self.auth = oss2.Auth(access_key_id, access_key_secret)
        self.bucket = oss2.Bucket(self.auth, endpoint, bucket_name)
        self.bucket_name = bucket_name

    def upload_audio(
        self, local_file_path: str, expiration: int = 3600
    ) -> Tuple[str, str]:
        """上传音频文件到OSS"""
        local_file = Path(local_file_path)
        if not local_file.exists():
            raise FileNotFoundError(f"文件不存在: {local_file_path}")

        object_name = f"douyin-transcribe/{uuid.uuid4()}.wav"

        Logger.info(f"上传 {local_file.name} 到 OSS...")

        self.bucket.put_object_from_file(object_name, str(local_file))
        url = self.bucket.sign_url("GET", object_name, expiration)

        Logger.success(f"上传完成，生成临时URL（有效期{expiration // 3600}小时）")

        return url, object_name

    def delete_object(self, object_name: str):
        """删除OSS对象"""
        try:
            self.bucket.delete_object(object_name)
            Logger.info(f"已删除OSS对象: {object_name}")
        except:
            pass
