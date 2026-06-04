#!/usr/bin/env python3
"""Render prompts through Volcengine Ark image generation models."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path


CREATE_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"


def http_json(url: str, api_key: str, payload: dict) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc


def download_file(url: str, dest: Path) -> None:
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=180) as response:
        dest.write_bytes(response.read())


def build_payload(model: str, prompt: str, size: str, response_format: str) -> dict:
    return {
        "model": model,
        "prompt": prompt,
        "size": size,
        "response_format": response_format,
    }


def extract_image_urls(response: dict) -> list[str]:
    urls: list[str] = []
    for item in response.get("data", []) or []:
        if not isinstance(item, dict):
            continue
        if item.get("url"):
            urls.append(str(item["url"]))
    return urls


def load_prompt_sources(prompt: str | None, prompts_dir: str | None, max_prompts: int) -> list[tuple[str, str]]:
    prompt_sources: list[tuple[str, str]] = []
    if prompt:
        prompt_sources.append(("direct_prompt", prompt))
    if prompts_dir:
        prompt_dir_path = Path(prompts_dir).expanduser().resolve()
        for prompt_file in sorted(prompt_dir_path.glob("*_prompt.txt"))[:max_prompts]:
            prompt_sources.append((prompt_file.stem, prompt_file.read_text(encoding="utf-8")))
    return prompt_sources


def maybe_load_env_file(env_file: str | None) -> None:
    if not env_file:
        return
    env_path = Path(env_file).expanduser().resolve()
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Render prompts with Volcengine Ark image generation.")
    parser.add_argument("--prompts-dir", help="Directory containing *_prompt.txt files.")
    parser.add_argument("--prompt", help="Single prompt text to render (alternative to --prompts-dir).")
    parser.add_argument("--output-dir", required=True, help="Directory for rendered images and metadata.")
    parser.add_argument(
        "--model",
        default="doubao-seedream-5-0-260128",
        help="Ark image model. Default: doubao-seedream-5-0-260128",
    )
    parser.add_argument("--size", default="2K", help="Image size. Default: 2K")
    parser.add_argument("--response-format", default="url", choices=["url"], help="Response format. Default: url")
    parser.add_argument("--max-prompts", type=int, default=3, help="Maximum number of prompt files to render in one run. Default: 3")
    parser.add_argument("--poll-seconds", type=float, default=0.0, help="Optional delay between requests in seconds. Default: 0")
    parser.add_argument("--env-file", help="Optional .env file containing ARK_API_KEY.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be rendered without sending API requests.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt_sources = load_prompt_sources(args.prompt, args.prompts_dir, args.max_prompts)
    if not prompt_sources:
        print("No prompts provided. Use --prompt or --prompts-dir.")
        return 0

    maybe_load_env_file(args.env_file)

    if args.dry_run:
        for name, _ in prompt_sources:
            print(f"DRY RUN: would render '{name}' with model={args.model} size={args.size}")
        return 0

    api_key = os.environ.get("ARK_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("ARK_API_KEY is not set.")

    manifest: list[dict[str, object]] = []
    for source_name, prompt_text in prompt_sources:
        try:
            payload = build_payload(args.model, prompt_text, args.size, args.response_format)
            response = http_json(CREATE_URL, api_key, payload)
            urls = extract_image_urls(response)
            item: dict[str, object] = {
                "source": source_name,
                "model": args.model,
                "size": args.size,
                "status": "SUCCEEDED" if urls else "FAILED",
            }
            if not urls:
                item["raw_response"] = response
                manifest.append(item)
                continue

            downloaded = []
            for index, url in enumerate(urls, start=1):
                suffix = "" if len(urls) == 1 else f"_{index}"
                base_name = source_name.replace("_prompt", "")
                output_file = output_dir / f"{base_name}{suffix}.png"
                download_file(url, output_file)
                downloaded.append(str(output_file))
            item["images"] = downloaded
            manifest.append(item)
            if args.poll_seconds > 0:
                time.sleep(args.poll_seconds)
        except (urllib.error.URLError, RuntimeError) as exc:
            manifest.append(
                {
                    "source": source_name,
                    "model": args.model,
                    "size": args.size,
                    "status": "FAILED",
                    "error": str(exc),
                }
            )

    manifest_path = output_dir / "ark-render-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
