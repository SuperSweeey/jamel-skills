"""
Notion同步模块
Notion数据库同步
"""

from datetime import datetime
from typing import Tuple

from .logger import Logger


class NotionSync:
    """Notion数据库同步器"""

    def __init__(self, token: str, database_id: str):
        try:
            from notion_client import Client
        except ImportError:
            raise RuntimeError(
                "notion_client库未安装，请运行: pip install notion-client"
            )

        self.client = Client(auth=token)
        self.database_id = database_id

    def classify_content(self, content: str) -> Tuple[str, str]:
        """根据内容自动分类"""
        content_lower = content.lower()

        # 领域分类
        if any(
            kw in content_lower
            for kw in [
                "ai",
                "人工智能",
                "算法",
                "技术",
                "人类",
                "思维",
                "情感",
                "哲学",
                "意识",
            ]
        ):
            field = "人类大逻辑"
        elif any(
            kw in content_lower
            for kw in ["商业", "资本", "经济", "投资", "融资", "创业"]
        ):
            field = "商业大逻辑"
        elif any(
            kw in content_lower
            for kw in ["国际", "关系", "政治", "地缘", "外交", "战争"]
        ):
            field = "国际关系..."
        else:
            field = "人类大逻辑"

        # 分类
        if any(
            kw in content_lower for kw in ["理论", "逻辑", "模型", "框架", "分析工具"]
        ):
            category = "逻辑&理论&模型库"
        else:
            category = "话题资料库"

        return field, category

    def create_page(
        self,
        title: str,
        url: str,
        content: str,
        field: str = None,
        category: str = None,
    ):
        """创建Notion页面"""
        Logger.info(f"创建Notion页面: {title}")

        # 自动分类
        if not field or not category:
            auto_field, auto_category = self.classify_content(content)
            field = field or auto_field
            category = category or auto_category

        # 分割长文本
        content_blocks = []
        max_chunk = 1900

        for i in range(0, len(content), max_chunk):
            chunk = content[i : i + max_chunk]
            content_blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": chunk}}]},
                }
            )

        # 使用用户数据库的实际字段名
        properties = {
            "标题": {"title": [{"text": {"content": title}}]},
        }

        if field:
            properties["领域"] = {"multi_select": [{"name": field}]}
        if category:
            properties["分类"] = {"select": {"name": category}}

        page = self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=properties,
            children=content_blocks,
        )

        Logger.success(f"Notion页面创建成功: {page.get('url', 'N/A')}")

        return page
