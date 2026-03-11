#!/usr/bin/env python3
import json
import importlib.util
import traceback
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent


def generate_ai_title(transcript, api_key, api_url, max_retries=3):
    """用智谱AI glm-4.7-flash 生成吸引人的一句话标题"""
    import requests
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[INFO] 生成AI标题（第 {attempt}/{max_retries} 次）...")
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "glm-4.7-flash",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的标题生成助手。请为下面的文本生成一个吸引人、有吸引力的标题，适合社交媒体或内容平台使用。标题要简洁有力，不超过30字。直接输出标题内容，不要有任何前缀或引号。"
                    },
                    {
                        "role": "user",
                        "content": f"请为下面的文本生成标题：\n{transcript[:4000]}"
                    }
                ],
                "max_tokens": 1500,
                "temperature": 0.8
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
            
            print(f"[OK] AI标题生成完成: {content}")
            return content
        except Exception as e:
            print(f"[WARN] 第 {attempt} 次失败: {str(e)[:80]}")
            if attempt < max_retries:
                print(f"[INFO] 等待 5 秒后重试...")
                time.sleep(5)
    
    print("[WARN] AI标题生成全部失败，使用原标题")
    return None

def load_rules(rules_path=None):
    try:
        import yaml
    except ImportError:
        raise RuntimeError("pyyaml未安装")
    path = rules_path or BASE_DIR / "config" / "send_rules.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def resolve_targets(rules, platform, cli_targets=None):
    if cli_targets:
        return cli_targets
    platform_rule = rules.get("platform_rules", {}).get(platform, {})
    if "send" in platform_rule:
        return platform_rule["send"]
    return rules.get("ai_policy", {}).get("on_transcribe_success", [])

def resolve_notion_options(rules, platform, cli_notion_target=None):
    dbs = rules.get("notion_databases", {})
    alias = cli_notion_target
    if not alias:
        platform_rule = rules.get("platform_rules", {}).get(platform, {})
        alias = platform_rule.get("notion_database")
    if not alias:
        alias = rules.get("default_notion_database")
    if not alias:
        raise RuntimeError("send_rules.yaml 没有 default_notion_database")
    target_id = dbs.get(alias)
    if not target_id:
        raise RuntimeError(f"notion_databases 找不到 {alias}，现有: {list(dbs.keys())}")
    return {"page_id": target_id} if alias.endswith("_page") else {"database_id": target_id}

def get_sender(name):
    path = BASE_DIR / "senders" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def dispatch(transcript, title, url, platform, config, cli_targets=None, dry_run=False, rules_path=None, notion_target=None):
    rules = load_rules(rules_path)
    targets = resolve_targets(rules, platform, cli_targets)
    
    # 先用AI生成吸引人的标题
    ai_title = generate_ai_title(transcript, config.zhipu_api_key, config.zhipu_api_url)
    final_title = ai_title if ai_title else title
    
    result = {
        "task_status": "success",
        "platform": platform,
        "url": url,
        "title": final_title,
        "original_title": title,
        "char_count": len(transcript),
        "transcript": transcript,
        "dry_run": dry_run,
        "targets": targets,
        "send_results": {}
    }
    if dry_run:
        result["send_skipped"] = True
        return result
    for target in targets:
        try:
            sender = get_sender(target)
            options = {}
            if target == "notion":
                options = resolve_notion_options(rules, platform, notion_target)
                print(f"[INFO] Notion options: {options}")
            sender.send(transcript, final_title, url, config, options)
            result["send_results"][target] = "success"
        except Exception as e:
            print(f"[ERROR] {target} 失败: {e}")
            traceback.print_exc()
            result["send_results"][target] = f"failed: {str(e)}"
    return result
