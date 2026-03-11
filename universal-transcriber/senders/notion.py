def send(transcript, title, url, config, options=None):
    """发送到 Notion，支持 database 和 page 两种目标类型"""
    try:
        from notion_client import Client
    except ImportError:
        raise RuntimeError("notion_client未安装，请运行: pip install notion-client")
    
    options = options or {}
    database_id = options.get("database_id")
    page_id = options.get("page_id")
    token = config.notion_token
    client = Client(auth=token)
    
    def text_blocks(text):
        blocks = []
        for i in range(0, len(text), 1900):
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": text[i:i+1900]}}]}
            })
        return blocks
    
    if database_id:
        response = client.pages.create(
            parent={"database_id": database_id},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
            },
            children=[
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": f"来源: {url}"}}]}
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                },
                *text_blocks(transcript)
            ]
        )
        notion_url = response.get("url", "")
        print(f"[OK] Notion 写入完成: {title}")
        print(f"[OK] Notion 页面链接: {notion_url}")
        return notion_url
    elif page_id:
        response = client.blocks.children.append(
            block_id=page_id,
            children=[
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": title}}]}
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": f"来源: {url}"}}]}
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {}
                },
                *text_blocks(transcript)
            ]
        )
        notion_url = f"https://notion.so/{page_id.replace('-', '')}"
        print(f"[OK] Notion 页面追加完成: {title}")
        print(f"[OK] Notion 页面链接: {notion_url}")
        return notion_url
    else:
        raise RuntimeError("notion sender 需要 database_id 或 page_id，请检查 send_rules.yaml")
