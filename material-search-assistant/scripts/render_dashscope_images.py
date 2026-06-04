#!/usr/bin/env python3
"""Render infographic prompts through Aliyun Bailian DashScope image generation."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path


CREATE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
CREATE_URL_V2 = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/generation"
TASK_URL_TEMPLATE = "https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"


def http_json(url: str, method: str, api_key: str, payload: dict | None = None, extra_headers: dict | None = None) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc


def download_file(url: str, dest: Path) -> None:
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=120) as response:
        dest.write_bytes(response.read())


def create_task(api_key: str, model: str, prompt: str, size: str) -> dict:
    if model.startswith("wan2.6") or model.startswith("qwen-image-2.0"):
        payload = {
            "model": model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ]
            },
            "parameters": {
                "size": size,
                "n": 1,
                "prompt_extend": False,
                "watermark": False,
                "negative_prompt": "",
            },
        }
        return http_json(
            CREATE_URL_V2,
            "POST",
            api_key,
            payload=payload,
            extra_headers={"X-DashScope-Async": "enable"},
        )

    payload = {
        "model": model,
        "input": {"prompt": prompt},
        "parameters": {
            "size": size,
            "n": 1,
            "prompt_extend": False,
            "watermark": False,
            "negative_prompt": "",
        },
    }
    return http_json(
        CREATE_URL,
        "POST",
        api_key,
        payload=payload,
        extra_headers={"X-DashScope-Async": "enable"},
    )


def poll_task(api_key: str, task_id: str, poll_interval: float, max_wait_seconds: int) -> dict:
    deadline = time.time() + max_wait_seconds
    while time.time() < deadline:
        result = http_json(TASK_URL_TEMPLATE.format(task_id=task_id), "GET", api_key)
        status = (
            result.get("output", {}).get("task_status")
            or result.get("task_status")
            or result.get("output", {}).get("status")
        )
        if status in {"SUCCEEDED", "FAILED", "CANCELED"}:
            return result
        time.sleep(poll_interval)
    raise TimeoutError(f"Task {task_id} did not finish within {max_wait_seconds} seconds")


def extract_image_urls(task_result: dict) -> list[str]:
    output = task_result.get("output", {})
    urls: list[str] = []

    for item in output.get("results", []) or []:
        if isinstance(item, dict) and item.get("url"):
            urls.append(item["url"])

    if not urls:
        for item in output.get("result_url", []) or []:
            if isinstance(item, str):
                urls.append(item)

    if not urls:
        for choice in output.get("choices", []) or []:
            message = choice.get("message", {}) if isinstance(choice, dict) else {}
            for item in message.get("content", []) or []:
                if isinstance(item, dict) and item.get("image"):
                    urls.append(item["image"])

    return urls


def main() -> int:
    parser = argparse.ArgumentParser(description="Render prompts with DashScope image generation.")
    parser.add_argument("--prompts-dir", help="Directory containing *_prompt.txt files.")
    parser.add_argument("--prompt", help="Single prompt text to render (alternative to --prompts-dir).")
    parser.add_argument("--output-dir", required=True, help="Directory for rendered images and metadata.")
    parser.add_argument("--model", default="wan2.2-t2i-flash", help="DashScope image model. Default: wan2.2-t2i-flash")
    parser.add_argument("--size", default="1024*1024", help="Image size. Default: 1024*1024")
    parser.add_argument("--max-prompts", type=int, default=3, help="Maximum number of prompt files to render in one run. Default: 3")
    parser.add_argument("--poll-interval", type=float, default=3.0, help="Polling interval in seconds. Default: 3")
    parser.add_argument("--max-wait-seconds", type=int, default=300, help="Maximum wait per task in seconds. Default: 300")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be rendered without sending API requests.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect prompts: either from --prompt, or from --prompts-dir
    prompt_sources: list[tuple[str, str]] = []  # (source_name, prompt_text)
    if args.prompt:
        prompt_sources.append(("direct_prompt", args.prompt))
    if args.prompts_dir:
        prompts_dir = Path(args.prompts_dir).expanduser().resolve()
        for pf in sorted(prompts_dir.glob("*_prompt.txt"))[: args.max_prompts]:
            prompt_sources.append((pf.stem, pf.read_text(encoding="utf-8")))

    if not prompt_sources:
        print("No prompts provided. Use --prompt or --prompts-dir.")
        return 0

    if args.dry_run:
        for name, _ in prompt_sources:
            print(f"DRY RUN: would render '{name}' with model={args.model} size={args.size}")
        return 0

    api_key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("DASHSCOPE_API_KEY is not set.")

    manifest: list[dict[str, object]] = []
    for source_name, prompt_text in prompt_sources:
        try:
            create_result = create_task(api_key, args.model, prompt_text, args.size)
            task_id = create_result.get("output", {}).get("task_id") or create_result.get("task_id")
            if not task_id:
                raise RuntimeError(f"Missing task_id in response: {create_result}")
            task_result = poll_task(api_key, task_id, args.poll_interval, args.max_wait_seconds)
            status = task_result.get("output", {}).get("task_status") or task_result.get("task_status")
            item: dict[str, object] = {
                "source": source_name,
                "task_id": task_id,
                "status": status,
            }
            if status != "SUCCEEDED":
                item["raw_response"] = task_result
                manifest.append(item)
                continue

            urls = extract_image_urls(task_result)
            downloaded = []
            for index, url in enumerate(urls, start=1):
                suffix = "" if len(urls) == 1 else f"_{index}"
                base_name = source_name.replace("_prompt", "")
                output_file = output_dir / f"{base_name}{suffix}.png"
                download_file(url, output_file)
                downloaded.append(str(output_file))
            item["images"] = downloaded
            manifest.append(item)
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            manifest.append(
                {
                    "source": source_name,
                    "status": "FAILED",
                    "error": str(exc),
                }
            )

    manifest_path = output_dir / "dashscope-render-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
