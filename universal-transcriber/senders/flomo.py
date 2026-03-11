import sys
import os
from pathlib import Path

FLOMO_SKILL_PATH = Path("/root/.openclaw/workspace/skill-backups/jamel-skills/flomo-skill/scripts")

def send(transcript, title, url, config, options=None):
    """发送到Flomo"""
    sys.path.insert(0, str(FLOMO_SKILL_PATH))
    from send_to_flomo import send_to_flomo
    
    api_key = (options or {}).get("api_key") or os.environ.get("FLOMO_API_KEY")
    content = f"**​{title}​**\n\n来源: {url}\n\n{transcript[:1000]}"
    
    result = send_to_flomo(content, api_key=api_key)
    if result:
        print(f"[OK] Flomo发送完成: {title}")
    else:
        raise RuntimeError("Flomo发送失败，请检查 API Key")
