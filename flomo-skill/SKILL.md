---
name: flomo-skill
description: Send content to flomo (浮墨笔记). Use when user wants to send notes, ideas, or any content to their flomo account.
---

# flomo Skill

Send content to flomo (浮墨笔记) using the incoming webhook API.

## Usage

### Using the Python script

```bash
python3 /root/.openclaw/workspace/skills/flomo-skill/scripts/send_to_flomo.py "你的内容"
```

### With image URLs

```bash
python3 /root/.openclaw/workspace/skills/flomo-skill/scripts/send_to_flomo.py "你的内容" --images "https://example.com/image1.jpg,https://example.com/image2.jpg"
```

## Configuration

You need to set up your flomo webhook URL in one of two ways:

### Option 1: Environment variable

```bash
export FLOMO_API_KEY="https://flomoapp.com/iwh/xxx/xxx/"
```

### Option 2: Config file

Create a config file at `~/.flomo/config.json`:

```json
{
  "api_key": "https://flomoapp.com/iwh/xxx/xxx/"
}
```

## Getting your webhook URL

1. Go to https://flomoapp.com/mine?source=incoming_webhook
2. You need a PRO membership
3. Copy your webhook URL from the page

## API Documentation

- flomo API: https://help.flomoapp.com/advance/api.html
- Incoming webhook: https://flomoapp.com/mine?source=incoming_webhook

## Important Note

Keep your webhook URL secret! It's like a password to your flomo account.

