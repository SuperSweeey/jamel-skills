#!/usr/bin/env python3
"""
Send content to flomo (浮墨笔记)
"""

import argparse
import json
import os
import sys
from pathlib import Path
import requests


def get_flomo_api_key():
    """Get flomo API key from environment or config file"""
    # Try environment variable first
    api_key = os.environ.get("FLOMO_API_KEY")
    if api_key:
        return api_key

    # Try config file
    config_path = Path.home() / ".flomo" / "config.json"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("api_key")
        except Exception as e:
            print(f"Warning: Could not read config file: {e}", file=sys.stderr)

    return None


def send_to_flomo(content, image_urls=None, api_key=None):
    """
    Send content to flomo

    Args:
        content: Text content to send
        image_urls: List of image URLs (optional)
        api_key: flomo API key (optional, will try to get from env/config if not provided)
    """
    if not api_key:
        api_key = get_flomo_api_key()

    if not api_key:
        print("Error: No flomo API key found!", file=sys.stderr)
        print("Please set FLOMO_API_KEY environment variable or create ~/.flomo/config.json", file=sys.stderr)
        return False

    # Prepare payload
    payload = {
        "content": content
    }
    
    if image_urls:
        payload["images"] = image_urls
    
    # Send to flomo webhook
    try:
        response = requests.post(
            api_key,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        print(f"✅ Successfully sent to flomo!")
        print(f"Content: {content}")
        if image_urls:
            print(f"Images: {image_urls}")
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending to flomo: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Send content to flomo")
    parser.add_argument("content", help="Text content to send")
    parser.add_argument("--images", help="Comma-separated list of image URLs")
    parser.add_argument("--api-key", help="flomo API key")
    
    args = parser.parse_args()
    
    image_urls = None
    if args.images:
        image_urls = [url.strip() for url in args.images.split(",") if url.strip()]
    
    success = send_to_flomo(
        content=args.content,
        image_urls=image_urls,
        api_key=args.api_key
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
