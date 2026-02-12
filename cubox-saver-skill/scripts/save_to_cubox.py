#!/usr/bin/env python3
"""
Save content to Cubox using their API.
Supports URLs, memos, and file content.
Auto-loads encrypted API URL from config.
"""

import sys
import json
import argparse
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# Import config manager
try:
    from config_manager import ConfigManager
except ImportError:
    # Fallback if import fails
    ConfigManager = None


def read_file_content(file_path):
    """Read content from a file."""
    try:
        path = Path(file_path)
        if not path.exists():
            return None, f"File not found: {file_path}"
        
        # Read file content
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content, None
    except Exception as e:
        return None, f"Error reading file: {str(e)}"


def detect_command_injection(content):
    """
    Detect if content appears to be from command injection.
    Returns (is_suspicious: bool, reason: str or None)
    """
    # Patterns that indicate command injection attempts
    suspicious_patterns = [
        'Get-Content',
        'cat ',
        '$(cat',
        '@(',
        '-Raw',
        '-Encoding',
        'gc ',  # PowerShell alias for Get-Content
        'type ',  # Windows command
    ]
    
    # Check for suspicious patterns
    for pattern in suspicious_patterns:
        if pattern in content:
            return True, f"检测到命令注入模式: '{pattern}'"
    
    # Check if content looks like it came from a file path
    # (very long single line with file-like structure)
    if len(content) > 5000 and '\n' not in content[:1000]:
        return True, "内容疑似来自未经验证的文件读取"
    
    return False, None


def save_to_cubox(api_url, content_type, content, title=None, description=None, 
                  tags=None, folder=None):
    """
    Save content to Cubox via API.
    
    Args:
        api_url: Cubox API URL (from settings)
        content_type: 'url' or 'memo'
        content: The content to save (URL or plain text)
        title: Optional title
        description: Optional description
        tags: Optional list of tags
        folder: Optional folder name
    
    Returns:
        (success: bool, message: str, cubox_url: str or None)
    
    CRITICAL REQUIREMENTS:
        - For 'memo' type: content MUST be plain text (no Markdown)
        - For 'memo' type: content MUST be ≤2999 characters
        - For 'url' type: no restrictions
        - SECURITY: No command injection allowed
    """
    
    # SECURITY CHECK: Detect command injection attempts
    is_suspicious, reason = detect_command_injection(str(content))
    if is_suspicious:
        error_msg = f"""
❌ 安全检查失败: 检测到不安全的内容注入

原因: {reason}

这通常意味着内容是通过命令行注入的，绕过了必要的验证流程。

正确流程:
1. 使用 Read 工具读取文件内容
2. 转换为纯文本格式
3. 验证字符数 (≤2999)
4. 获得用户确认
5. 然后保存

请使用正确的流程重新操作。
"""
        return False, error_msg, None
    
    # Validate content type
    if content_type not in ['url', 'memo']:
        return False, f"不支持的类型: {content_type}. Cubox 仅支持 'url' 或 'memo' 类型", None
    
    # CRITICAL: Validate character count for memo type
    if content_type == 'memo':
        char_count = len(content)
        if char_count > 2999:
            return False, f"❌ 内容超出限制！\n当前字符数: {char_count}\nCubox 限制: 2999 字符\n超出: {char_count - 2999} 字符\n\n请先总结或删减内容至 2999 字符以内。", None
        
        # Warn if content contains Markdown-like syntax
        markdown_indicators = ['**', '__', '```', '##', '* ', '- [', '](']
        has_markdown = any(indicator in content for indicator in markdown_indicators)
        if has_markdown:
            print("⚠️  警告: 检测到可能的 Markdown 格式。Cubox 仅支持纯文本，建议先转换为纯文本格式。")
    
    # Prepare the payload
    payload = {}
    
    if content_type == 'url':
        payload['type'] = 'url'
        payload['content'] = content
    elif content_type == 'memo':
        payload['type'] = 'memo'
        payload['content'] = content
    
    # Add optional fields
    if title:
        payload['title'] = title
    if description:
        payload['description'] = description
    if tags:
        payload['tags'] = tags if isinstance(tags, list) else [tags]
    if folder:
        payload['folder'] = folder
    
    # Make API request
    try:
        req = Request(
            api_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        
        with urlopen(req, timeout=30) as response:
            response_data = response.read().decode('utf-8')
            
            if response.status == 200:
                # Parse response to get Cubox item URL
                try:
                    result = json.loads(response_data)
                    # Cubox API typically returns item code/ID
                    # The URL format is: https://cubox.pro/my/card?id={item_code}
                    cubox_url = None
                    if 'code' in result:
                        cubox_url = f"https://cubox.pro/my/card?id={result['code']}"
                    elif 'data' in result and isinstance(result['data'], dict):
                        if 'code' in result['data']:
                            cubox_url = f"https://cubox.pro/my/card?id={result['data']['code']}"
                        elif 'url' in result['data']:
                            cubox_url = result['data']['url']
                    
                    # Include character count in success message for memo type
                    if content_type == 'memo':
                        char_count = len(content)
                        return True, f"✅ 内容已成功保存到 Cubox!\n字符数: {char_count}/2999", cubox_url
                    else:
                        return True, "✅ 内容已成功保存到 Cubox!", cubox_url
                except json.JSONDecodeError:
                    return True, "内容已成功保存到 Cubox! (无法解析返回链接)", None
            else:
                return False, f"API 返回状态 {response.status}: {response_data}", None
                
    except HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ''
        return False, f"HTTP 错误 {e.code}: {error_body or e.reason}", None
    except URLError as e:
        return False, f"连接错误: {str(e.reason)}", None
    except Exception as e:
        return False, f"未预期的错误: {str(e)}", None


def main():
    parser = argparse.ArgumentParser(
        description='Save content to Cubox (auto-loads encrypted API URL)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Save with auto-loaded API URL (recommended)
  python save_to_cubox.py --type url --content "https://example.com" --title "Example"
  
  # Save a memo (MUST be plain text, ≤2999 characters)
  python save_to_cubox.py --type memo --content "Meeting notes" --folder "Work"
  
  # Manually specify API URL (overrides saved config)
  python save_to_cubox.py --api-url "YOUR_API_URL" --type memo --content "Notes"

CRITICAL REQUIREMENTS:
  - For 'memo' type: Content MUST be plain text (no Markdown formatting)
  - For 'memo' type: Content MUST be ≤2999 characters (hard limit)
  - For 'url' type: No restrictions
  
API URL Management:
  - First time: Use --api-url to provide and save your API URL
  - Subsequent uses: API URL auto-loaded from encrypted config
  - Update: Use --api-url again to update saved API URL
        """
    )
    
    parser.add_argument('--api-url',
                        help='Cubox API URL (auto-saved on first use, optional afterwards)')
    parser.add_argument('--type', required=True, choices=['url', 'memo'],
                        help='Content type to save (url or memo)')
    parser.add_argument('--content', required=True,
                        help='Content to save (URL or plain text, ≤2999 chars for memo)')
    parser.add_argument('--title', help='Optional title')
    parser.add_argument('--description', help='Optional description')
    parser.add_argument('--tags', help='Comma-separated tags')
    parser.add_argument('--folder', help='Folder name in Cubox')
    
    args = parser.parse_args()
    
    # Get API URL (from args or config)
    api_url = None
    config_manager = None
    
    if ConfigManager:
        config_manager = ConfigManager()
    
    if args.api_url:
        # User provided API URL
        api_url = args.api_url
        
        # Save it for future use
        if config_manager:
            success, msg = config_manager.save_api_url(api_url)
            if success:
                print(f"💾 {msg}")
            else:
                print(f"⚠️  {msg}")
    else:
        # Try to load from config
        if config_manager:
            api_url, msg = config_manager.load_api_url()
            if api_url:
                print(f"🔓 {msg}")
            else:
                print(f"❌ 错误: 未找到保存的 API URL")
                print(f"\n首次使用请提供 API URL:")
                print(f"  python save_to_cubox.py --api-url \"YOUR_API_URL\" --type memo --content \"test\"")
                print(f"\n如何获取 API URL:")
                print(f"  1. 打开 Cubox 网页版")
                print(f"  2. 进入 设置 → 扩展中心和自动化 → API 扩展")
                print(f"  3. 启用 API 并复制链接")
                sys.exit(1)
        else:
            print(f"❌ 错误: 配置管理器不可用，请提供 --api-url 参数")
            sys.exit(1)
    
    # SECURITY CHECK: Detect command injection before processing
    is_suspicious, reason = detect_command_injection(args.content)
    if is_suspicious:
        print(f"❌ 安全检查失败: {reason}")
        print(f"\n这通常意味着内容是通过命令行注入的，例如:")
        print(f"  ❌ --content \"$(cat file.txt)\"")
        print(f"  ❌ --content \"@(Get-Content 'file.txt')\"")
        print(f"\n正确做法:")
        print(f"  1. 让 AI 使用 Read 工具读取文件")
        print(f"  2. 转换为纯文本并验证字符数")
        print(f"  3. 获得用户确认后再保存")
        print(f"\n请使用正确的流程重新操作。")
        sys.exit(1)
    
    # Validate character count for memo type before processing
    if args.type == 'memo':
        char_count = len(args.content)
        if char_count > 2999:
            print(f"❌ 错误: 内容超出限制！")
            print(f"当前字符数: {char_count}")
            print(f"Cubox 限制: 2999 字符")
            print(f"超出: {char_count - 2999} 字符")
            print(f"\n请先总结或删减内容至 2999 字符以内。")
            sys.exit(1)
        else:
            print(f"✓ 字符数验证通过: {char_count}/2999")
    
    # Parse tags
    tags = None
    if args.tags:
        tags = [tag.strip() for tag in args.tags.split(',')]
    
    # Save to Cubox
    success, message, cubox_url = save_to_cubox(
        api_url=api_url,
        content_type=args.type,
        content=args.content,
        title=args.title,
        description=args.description,
        tags=tags,
        folder=args.folder
    )
    
    # Output result
    print(message)
    if cubox_url:
        print(f"🔗 Cubox链接: {cubox_url}")
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
