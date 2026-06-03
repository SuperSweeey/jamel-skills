#!/usr/bin/env python3
"""Read-only setup checker for universal-transcriber.

This script does not download, upload, transcribe, dispatch, or print secrets.
It only verifies local readiness and explains what to configure next.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = BASE_DIR / "config" / "config.json"
SEND_RULES_PATH = BASE_DIR / "config" / "send_rules.yaml"
SUPPORTED_PLATFORMS = {"douyin", "bilibili", "xiaohongshu", "youtube"}
SUPPORTED_SEND_TARGETS = {"local", "notion", "github", "flomo"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check universal-transcriber first-run setup without running the pipeline."
    )
    parser.add_argument("--platform", choices=sorted(SUPPORTED_PLATFORMS), help="Optional platform to validate.")
    parser.add_argument(
        "--send",
        action="append",
        choices=sorted(SUPPORTED_SEND_TARGETS),
        help="Optional destination to validate. Repeat for multiple destinations.",
    )
    parser.add_argument("--config", default=str(CONFIG_PATH), help="Config JSON path.")
    return parser.parse_args()


def load_config(path: Path) -> tuple[dict[str, Any], str | None]:
    if not path.exists():
        return {}, f"Config file not found: {path}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return {}, f"Config file is not valid JSON: {exc}"


def has_value(config: dict[str, Any], key: str) -> bool:
    value = config.get(key)
    return value is not None and str(value).strip() != ""


def importable(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def check_ffmpeg(config: dict[str, Any]) -> tuple[bool, str]:
    configured = str(config.get("ffmpeg_path") or "").strip()
    candidates = []
    if configured:
        candidates.append(configured)
    which = shutil.which("ffmpeg")
    if which:
        candidates.append(which)

    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception:
            continue
        if result.returncode == 0:
            return True, candidate

    if configured:
        return False, f"Configured ffmpeg_path is not usable: {configured}"
    return False, "ffmpeg was not found in PATH and ffmpeg_path is empty."


def add_missing(messages: list[str], key: str, meaning: str) -> None:
    messages.append(f"- `{key}`: {meaning}")


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    send_targets = set(args.send or [])

    print("universal-transcriber setup check")
    print(f"Base: {BASE_DIR}")
    print("")

    failures: list[str] = []
    warnings: list[str] = []
    next_steps: list[str] = []

    print("[OK] Python is available")
    print(f"     {sys.executable}")

    config, config_error = load_config(config_path)
    if config_error:
        print(f"[MISSING] {config_error}")
        failures.append("config")
        next_steps.append(
            "Create `config/config.json` from the template in `docs/first-run-setup.md`, then rerun this check."
        )
    else:
        print(f"[OK] Config file exists: {config_path}")

    required_core = {
        "dashscope_api_key": "DashScope API key used for cloud transcription.",
        "oss_access_key_id": "Alibaba Cloud OSS AccessKey ID.",
        "oss_access_key_secret": "Alibaba Cloud OSS AccessKey Secret.",
        "oss_bucket_name": "OSS bucket used for temporary audio upload.",
        "oss_endpoint": "OSS endpoint, for example `oss-cn-beijing.aliyuncs.com`.",
    }
    missing_core: list[str] = []
    if config:
        for key, meaning in required_core.items():
            if not has_value(config, key):
                add_missing(missing_core, key, meaning)
        if missing_core:
            print("[MISSING] Core transcription config is incomplete:")
            for item in missing_core:
                print(f"     {item}")
            failures.append("core-config")
            next_steps.append(
                "Fill the missing DashScope/OSS fields in `config/config.json`. See `docs/first-run-setup.md`."
            )
        else:
            print("[OK] Core DashScope and OSS fields are present")

    required_modules = {
        "requests": "HTTP requests and sender fallbacks.",
        "dashscope": "DashScope transcription SDK.",
        "oss2": "Temporary OSS upload.",
        "yaml": "Read `config/send_rules.yaml`.",
    }
    optional_modules = {
        "notion_client": "Only required when sending to Notion through the official client; requests fallback may still work.",
        "playwright": "Only required for download paths that use browser automation.",
    }
    missing_modules = [f"- `{name}`: {desc}" for name, desc in required_modules.items() if not importable(name)]
    if missing_modules:
        print("[MISSING] Required Python packages are missing:")
        for item in missing_modules:
            print(f"     {item}")
        failures.append("python-packages")
        next_steps.append(
            "Install missing packages after connectivity and package-risk checks. Start with: `pip install requests dashscope oss2 pyyaml`."
        )
    else:
        print("[OK] Required Python packages are importable")

    optional_missing = [name for name in optional_modules if not importable(name)]
    if optional_missing:
        warnings.append("Optional packages missing: " + ", ".join(optional_missing))

    ffmpeg_ok, ffmpeg_detail = check_ffmpeg(config)
    if ffmpeg_ok:
        print(f"[OK] ffmpeg is usable: {ffmpeg_detail}")
    else:
        print(f"[MISSING] {ffmpeg_detail}")
        failures.append("ffmpeg")
        next_steps.append(
            "Install ffmpeg or set `ffmpeg_path` in `config/config.json` to the full `ffmpeg.exe` path."
        )

    if args.platform:
        print(f"[OK] Platform value is supported: {args.platform}")
        if args.platform in {"douyin", "xiaohongshu", "bilibili"}:
            warnings.append(
                f"{args.platform} cookies are not required before the first run. If download fails, provide a cookies file then rerun."
            )

    if send_targets:
        invalid_targets = send_targets - SUPPORTED_SEND_TARGETS
        if invalid_targets:
            print(f"[MISSING] Unsupported send target(s): {', '.join(sorted(invalid_targets))}")
            failures.append("send-targets")

    if "notion" in send_targets:
        missing = []
        if not has_value(config, "notion_token"):
            missing.append("notion_token")
        if not SEND_RULES_PATH.exists():
            missing.append("config/send_rules.yaml")
        if missing:
            print("[MISSING] Notion destination is not ready: " + ", ".join(missing))
            failures.append("notion")
            next_steps.append(
                "Configure `notion_token` and Notion database/page rules only if you want to send to Notion."
            )
        else:
            print("[OK] Notion destination fields are present")

    if "github" in send_targets:
        github_fields = ["github_token", "github_user", "github_repo", "github_repo_dir"]
        missing = [key for key in github_fields if not has_value(config, key)]
        repo_dir = Path(str(config.get("github_repo_dir") or "")).expanduser()
        if not missing and not repo_dir.exists():
            missing.append("github_repo_dir path does not exist")
        if missing:
            print("[MISSING] GitHub destination is not ready: " + ", ".join(missing))
            failures.append("github")
            next_steps.append(
                "Configure GitHub fields only if you want to publish transcripts to GitHub Pages."
            )
        else:
            print("[OK] GitHub destination fields are present")

    if "flomo" in send_targets:
        if not os.environ.get("FLOMO_API_KEY"):
            print("[MISSING] Flomo destination is not ready: FLOMO_API_KEY")
            failures.append("flomo")
            next_steps.append(
                "Set `FLOMO_API_KEY` only if you want to send transcripts to Flomo."
            )
        else:
            print("[OK] Flomo API key is present in environment")

    if "local" in send_targets:
        print("[OK] Local transcript output needs no extra sender config")

    print("")
    for warning in warnings:
        print(f"[WARN] {warning}")

    if failures:
        print("")
        print("Result: setup is not ready.")
        print("Next steps:")
        for index, step in enumerate(dict.fromkeys(next_steps), start=1):
            print(f"{index}. {step}")
        return 1

    print("")
    print("Result: basic setup is ready.")
    print("Next: provide a link, confirm the platform, then choose where to save the transcript.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
