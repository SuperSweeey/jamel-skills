#!/usr/bin/env python3
import sys
import uuid
import time
import requests
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from publish_to_github import publish_to_github


def generate_summary(text, api_key, api_url, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[INFO] 生成AI总结（第 {attempt}/{max_retries} 次）...")
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "glm-4.7-flash",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的内容总结助手。请为下面的文本生成一个简洁、清晰的总结，突出重点内容，不要超过300字。直接输出总结内容，不要有任何前缀。"
                    },
                    {
                        "role": "user",
                        "content": f"请为下面的文本生成总结：\n{text[:4000]}"
                    }
                ],
                "max_tokens": 1500,
                "temperature": 0.7
            }
            resp = requests.post(api_url, headers=headers, json=payload, timeout=90)
            resp.raise_for_status()
            msg = resp.json()["choices"][0]["message"]
            content = msg.get("content", "").strip()
            if not content:
                reasoning = msg.get("reasoning_content", "")
                content = reasoning[-500:].strip() if reasoning else ""
                if not content:
                    raise ValueError("AI返回内容为空")
            print(f"[OK] AI总结生成完成（{len(content)}字）")
            return content
        except Exception as e:
            print(f"[WARN] 第 {attempt} 次失败: {str(e)[:80]}")
            if attempt < max_retries:
                time.sleep(5)
    print("[WARN] AI总结全部失败，使用截断文本")
    return text[:300] + "..."


def send(transcript, title, url, config, options=None):
    transcript_id = str(uuid.uuid4())[:8]
    summary = generate_summary(transcript, config.zhipu_api_key, config.zhipu_api_url)
    github_url = publish_to_github(
        transcript_id, title, url, transcript_id, summary, transcript, config
    )
    return github_url
