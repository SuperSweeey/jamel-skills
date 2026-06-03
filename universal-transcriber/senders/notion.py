import time


def _text_blocks(text):
    blocks = []
    for i in range(0, len(text), 1900):
        blocks.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": text[i : i + 1900]}}]},
            }
        )
    return blocks


def _database_payload(transcript, title, url, database_id):
    return {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]},
        },
        "children": [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": f"来源: {url}"}}]},
            },
            {"object": "block", "type": "divider", "divider": {}},
            *_text_blocks(transcript),
        ],
    }


def _page_append_payload(transcript, title, url):
    return {
        "children": [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": title}}]},
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": f"来源: {url}"}}]},
            },
            {"object": "block", "type": "divider", "divider": {}},
            *_text_blocks(transcript),
        ]
    }


def _is_retryable_notion_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(
        token in text
        for token in [
            "ssl",
            "eof",
            "timed out",
            "timeout",
            "connection reset",
            "temporarily unavailable",
            "502",
            "503",
            "504",
            "429",
        ]
    )


def _notion_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def _send_via_requests(transcript, title, url, token, database_id=None, page_id=None):
    import requests

    headers = _notion_headers(token)
    timeout = 60

    if database_id:
        payload = _database_payload(transcript, title, url, database_id)
        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        notion_url = response.json().get("url", "")
        print(f"[OK] Notion 写入完成（requests fallback）: {title}")
        print(f"[OK] Notion 页面链接: {notion_url}")
        return notion_url

    if page_id:
        payload = _page_append_payload(transcript, title, url)
        response = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        notion_url = f"https://notion.so/{page_id.replace('-', '')}"
        print(f"[OK] Notion 页面追加完成（requests fallback）: {title}")
        print(f"[OK] Notion 页面链接: {notion_url}")
        return notion_url

    raise RuntimeError("notion sender 需要 database_id 或 page_id，请检查 send_rules.yaml")


def send(transcript, title, url, config, options=None):
    """发送到 Notion，优先 notion_client，失败后退化到 requests 直连 REST API。"""
    options = options or {}
    database_id = options.get("database_id")
    page_id = options.get("page_id")
    token = config.notion_token

    if not (database_id or page_id):
        raise RuntimeError("notion sender 需要 database_id 或 page_id，请检查 send_rules.yaml")

    try:
        from notion_client import Client
    except ImportError:
        print("[WARN] notion_client 未安装，直接使用 requests fallback")
        return _send_via_requests(transcript, title, url, token, database_id=database_id, page_id=page_id)

    client = Client(auth=token)
    last_error = None

    for attempt in range(1, 4):
        try:
            if database_id:
                response = client.pages.create(**_database_payload(transcript, title, url, database_id))
                notion_url = response.get("url", "")
                print(f"[OK] Notion 写入完成: {title}")
                print(f"[OK] Notion 页面链接: {notion_url}")
                return notion_url

            response = client.blocks.children.append(block_id=page_id, **_page_append_payload(transcript, title, url))
            notion_url = f"https://notion.so/{page_id.replace('-', '')}"
            print(f"[OK] Notion 页面追加完成: {title}")
            print(f"[OK] Notion 页面链接: {notion_url}")
            return notion_url
        except Exception as exc:
            last_error = exc
            if attempt < 3 and _is_retryable_notion_error(exc):
                print(f"[WARN] Notion 写入重试（第 {attempt}/3 次）: {exc}")
                time.sleep(2 * attempt)
                continue
            break

    print(f"[WARN] notion_client 写入失败，切换到 requests fallback: {last_error}")
    return _send_via_requests(transcript, title, url, token, database_id=database_id, page_id=page_id)
