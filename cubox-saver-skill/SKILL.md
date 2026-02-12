---
name: cubox-saver
description: "Save content to Cubox (稍后读/知识管理工具). Use when user requests to save, collect, or store content to Cubox, triggered by phrases like \"保存到Cubox\", \"save to Cubox\", \"收藏到Cubox\". Supports saving (1) conversation content/chat history, (2) URLs/web pages, (3) plain text notes/memos. CRITICAL LIMITS - Text content MUST be plain text (no Markdown), maximum 2999 characters. Files require USER CONFIRMATION. Content exceeding limits requires user decision on summarization. SECURITY - REJECT command injection (Get-Content, cat, etc.), ALWAYS use Read tool for files, NEVER bypass validation pipeline. SCRIPT POLICY - ONLY use official script in skill folder, NEVER create custom .py files with Write tool."
---

# Cubox Saver

Save various types of content to Cubox knowledge management platform via API.

## Prerequisites

**Required**: Cubox API URL from your account settings.

### First-Time Setup

**Step 1: Get your API URL**
1. Open Cubox web app
2. Go to **Settings** (偏好设置) → **Extensions and Automation** (扩展中心和自动化) → **API Extensions** (API 扩展)
3. Enable API and copy your unique URL

**Step 2: Save API URL (First Use Only)**

When you first use the skill, provide your API URL and it will be **automatically encrypted and saved**:

```bash
python scripts/save_to_cubox.py \
  --api-url "YOUR_API_URL_HERE" \
  --type memo \
  --content "Test message"
```

The API URL will be:
- ✅ **Encrypted** using machine-specific key
- ✅ **Saved** to `config/cubox_config.enc` in skill directory
- ✅ **Auto-loaded** for all future uses
- ✅ **Secure** - only works on your machine

**Step 3: Subsequent Uses**

After first-time setup, you **don't need to provide API URL anymore**:

```bash
# API URL automatically loaded from encrypted config
python scripts/save_to_cubox.py \
  --type memo \
  --content "Your content"
```

### Update API URL

If you need to update your API URL (e.g., regenerated in Cubox):

```bash
# Simply provide new API URL, it will auto-update
python scripts/save_to_cubox.py \
  --api-url "NEW_API_URL" \
  --type memo \
  --content "Test"
```

### Encrypted Storage Details

- **Location**: `C:\Users\26084\.stepfun\skills\cubox-saver\config\cubox_config.enc`
- **Encryption**: AES-256 with machine-specific key
- **Security**: Config only works on your machine
- **Privacy**: API URL never exposed in plain text

See `references/api_reference.md` for detailed setup instructions.

## ⚠️ CRITICAL Limitations

**Cubox API STRICT requirements:**
- ✅ **URLs** (web pages) - No restrictions
- ✅ **Plain text content ONLY** (memos)
  - **MAXIMUM 2999 characters** (hard limit)
  - **NO Markdown formatting** (must be plain text)
  - **NO special formatting** (no bold, italic, headers, etc.)

**Cubox API does NOT support:**
- ❌ Direct file uploads
- ❌ File attachments
- ❌ Markdown formatted text
- ❌ Content exceeding 2999 characters

**For text content (memos):**
1. **Character count check REQUIRED** - Count characters before saving
2. **If content > 2999 chars**: MUST ask user to choose:
   - Option A: AI summarize to ≤2999 chars (preserve maximum information)
   - Option B: User manually trim content
   - Option C: Cancel operation
3. **Format conversion REQUIRED** - Strip all Markdown formatting to plain text
4. **No images or rich media** - Text only

**For files:**
- Must read file content first
- Convert to plain text (remove Markdown if present)
- Check character count (≤2999)
- **ALWAYS ask user for confirmation before uploading**

## 🚫 ABSOLUTE PROHIBITIONS - NEVER DO THESE

**1. NEVER directly pass file content via command-line arguments:**
- ❌ NEVER use `Get-Content` in PowerShell command arguments
- ❌ NEVER use `$(cat file)` or `$file_content` in bash command arguments
- ❌ NEVER use `@(Get-Content ...)` syntax in PowerShell
- ❌ NEVER pipe file content directly into script parameters
- ❌ NEVER use command substitution to read files in script calls

**WHY THIS IS PROHIBITED:**
1. **Bypasses character validation** - File content injected directly without checking ≤2999 limit
2. **Bypasses format validation** - Markdown content uploaded without plain text conversion
3. **Bypasses user confirmation** - Files uploaded without user consent
4. **Command-line length limits** - Large files cause command truncation/failure
5. **Security risk** - Unvalidated content injection

**2. NEVER create custom Python scripts:**
- ❌ NEVER use Write tool to create new .py files
- ❌ NEVER write custom scripts to "improve" or "extend" functionality
- ❌ NEVER create wrapper scripts or helper functions
- ❌ NEVER modify the existing `save_to_cubox.py` script

**WHY THIS IS PROHIBITED:**
1. **Bypasses built-in validation** - Custom scripts may skip security checks
2. **Maintenance nightmare** - Multiple versions of scripts cause confusion
3. **Skill integrity** - The skill provides ONE official script with all validations
4. **Testing issues** - Custom scripts are untested and may have bugs

**ONLY USE THE OFFICIAL SCRIPT:**
- ✅ ONLY call `scripts/save_to_cubox.py` (the official script in skill folder)
- ✅ This script has ALL necessary validations built-in
- ✅ This script is tested and secure
- ✅ This script handles all edge cases correctly

**WRONG EXAMPLES (NEVER DO THIS):**
```bash
# ❌ WRONG - Bypasses all validation
python scripts/save_to_cubox.py --content "$(cat file.txt)"

# ❌ WRONG - PowerShell version
python scripts/save_to_cubox.py --content "@(Get-Content 'file.txt' -Raw)"

# ❌ WRONG - Direct file injection
python scripts/save_to_cubox.py --content "$(Get-Content 'C:\path\file.txt' -Raw -Encoding UTF8)"

# ❌ WRONG - Creating custom script
Write(path="my_cubox_saver.py", content="custom script...")

# ❌ WRONG - Writing helper script
Write(path="cubox_helper.py", content="def save_to_cubox()...")

# ❌ WRONG - Creating wrapper
Write(path="upload_file.py", content="import save_to_cubox...")
```

**CORRECT WORKFLOW (ALWAYS DO THIS):**
```python
# ✅ CORRECT - Full validation pipeline
# Step 1: Read file using Read tool
file_content = Read("C:\path\file.txt")

# Step 2: Convert to plain text (strip Markdown)
plain_text = strip_markdown(file_content)

# Step 3: Count characters
char_count = len(plain_text)

# Step 4: Validate character limit
if char_count > 2999:
    # Ask user: A (summarize) / B (trim) / C (cancel)
    user_choice = ask_user_decision(char_count)
    if user_choice == "A":
        plain_text = ai_summarize(plain_text, max_chars=2999)
    elif user_choice == "B":
        plain_text = user_manual_trim()
    else:
        return  # Cancel

# Step 5: Ask user confirmation
confirm = ask_user_confirmation(filename, char_count)
if not confirm:
    return  # Cancel

# Step 6: ONLY call the official script in skill folder
python "C:\Users\26084\.stepfun\skills\cubox-saver\scripts\save_to_cubox.py" \
  --api-url "URL" \
  --type memo \
  --content "$plain_text" \  # Only after full validation
  --title "filename"
```

# Step 5: Ask user confirmation
confirm = ask_user_confirmation(filename, char_count)
if not confirm:
    return  # Cancel

# Step 6: Save using validated content
python scripts/save_to_cubox.py \
  --api-url "URL" \
  --type memo \
  --content "$plain_text" \  # Only after full validation
  --title "filename"
```

**DETECTION AND ENFORCEMENT:**
- If user provides file path or mentions file content, **MUST use Read tool first**
- If user uses PowerShell/bash syntax like `Get-Content` or `cat`, **REJECT and explain correct workflow**
- If content appears to be from file (long text, file-like structure), **VERIFY it went through validation**
- **ALWAYS check**: Did content go through Read → Convert → Count → Validate → Confirm pipeline?
- **If AI attempts to create .py file with Write tool**: **STOP IMMEDIATELY and refuse**

**RESPONSE TO PROHIBITED ATTEMPTS:**

**When detecting command injection:**
```
❌ 检测到不安全的文件上传方式

您尝试直接通过命令行注入文件内容，这会绕过以下关键验证:
1. 字符数限制检查 (≤2999)
2. Markdown 格式转换
3. 用户确认流程

正确流程:
1. 我先使用 Read 工具读取文件
2. 转换为纯文本格式
3. 检查字符数 (当前: [count]/2999)
4. 如果超出限制，询问您的处理方式
5. 获得您的确认后再保存

请让我按照正确流程处理，确保内容符合 Cubox 的限制要求。
```

**When attempting to create custom Python scripts:**
```
❌ 禁止创建自定义 Python 脚本

Cubox Saver skill 已经提供了完整且经过测试的官方脚本:
C:\Users\26084\.stepfun\skills\cubox-saver\scripts\save_to_cubox.py

该脚本包含:
✓ 完整的安全验证
✓ 字符数限制检查
✓ 命令注入检测
✓ Markdown 格式转换
✓ 错误处理

创建自定义脚本会:
✗ 绕过内置验证
✗ 引入安全风险
✗ 造成维护混乱
✗ 可能包含 bug

我只能使用 skill 中的官方脚本来确保安全性和正确性。
```

## Quick Start

When user says "保存到Cubox" or "save to Cubox", follow this workflow:

### Step 0: Security Check - DETECT PROHIBITED PATTERNS

**BEFORE doing anything, check if user is attempting to bypass validation:**

🚨 **REJECT IMMEDIATELY if user provides:**
- PowerShell commands like `Get-Content`, `@(...)`, `-Raw`
- Bash commands like `cat`, `$(...)`, backticks
- File path with command syntax: `@(Get-Content 'path')`
- Any attempt to inject file content via command-line

**If detected, respond:**
```
❌ 检测到不安全的文件上传方式

您尝试直接注入文件内容，这会绕过必要的验证流程。

正确流程:
1. 告诉我文件路径
2. 我使用 Read 工具读取
3. 转换为纯文本并检查字符数
4. 征求您的确认后再保存

请提供文件路径，让我按照安全流程处理。
```

**Then STOP. Do not proceed until user provides clean file path.**

### Step 1: Identify Content Type and Validate

Determine what to save:
- **URL (Web Page)**: User provides a web link → **DIRECTLY save as URL type** (see Step 1.1)
- **Conversation/Chat**: User wants to save dialogue content → Convert to plain text memo
- **Memo**: User provides text to save as note → Convert to plain text memo
- **File**: User references a file → ⚠️ **REQUIRES USER CONFIRMATION** (see Step 1.5)

### Step 1.1: URL Detection and Direct Save (NEW - PRIORITY)

**🌐 When user provides a URL (web page link):**

**STEP 1: Detect if content is a URL**
```python
import re

def is_url(content):
    """Check if content is a valid URL"""
    url_pattern = r'^https?://[^\s]+

### Step 1.5: File Upload Confirmation (CRITICAL)

**When user wants to save a file:**

**STEP 0: Validate user input is safe**
- ✅ User provides clean file path: `C:\path\file.txt`
- ❌ User provides command syntax: `@(Get-Content 'path')` → **REJECT**
- ❌ User uses `cat`, `Get-Content`, `$()` → **REJECT**

**If user attempts command injection, STOP and respond:**
```
❌ 请提供文件路径，不要使用命令语法

错误示例: @(Get-Content 'file.txt')
正确示例: C:\Users\...\file.txt

我会使用安全的方式读取文件并进行必要的验证。
```

**STEP 1: Read file using Read tool ONLY**
```python
# ✅ CORRECT - Use Read tool
file_content = Read(file_path)

# ❌ WRONG - Never use command-line injection
# python script.py --content "$(cat file)"  # PROHIBITED
```

**STEP 2: Check and convert content**
- Convert to plain text (strip Markdown if present)
- Count characters: `char_count = len(plain_text)`

**STEP 3: Explain limitations to user**
```
"Cubox 仅支持纯文本内容上传，有以下限制：
1. 不能直接上传文件
2. 文本内容必须是纯文本格式（不支持 Markdown）
3. 文本内容不能超过 2999 字符

文件: [filename]
原始大小: [file size]
转换后字符数: [char_count]/2999"
```

**STEP 4: Handle based on character count**
- **If content > 2999 chars**: Go to Step 1.6 (ask user for summarization decision)
- **If content ≤ 2999 chars**: Continue to Step 5

**STEP 5: Ask for confirmation**
```
"是否确认将此文件内容保存为 Cubox 纯文本笔记?

⚠️ 注意:
- 原始格式将被转换为纯文本
- Markdown 格式将被移除
- 字符数: [char_count]/2999

回复 '是' 确认保存，或 '否' 取消。"
```

**STEP 6: Wait for user response**
- If YES → Proceed to Step 3 (Execute Save) with validated plain text
- If NO → Cancel operation

**ENFORCEMENT:**
- **NEVER skip Read tool** - Always use Read to get file content
- **NEVER accept command-injected content** - Reject PowerShell/bash syntax
- **NEVER skip character validation** - Always count and check ≤2999
- **NEVER skip user confirmation** - Always ask before saving file content

### Step 1.6: Handle Content Exceeding 2999 Characters (MANDATORY)

**When content exceeds 2999 characters, MUST ask user to choose:**

```
"⚠️ 内容超出限制

当前字符数: [char_count]
Cubox 限制: 2999 字符
超出: [char_count - 2999] 字符

请选择处理方式:

A. AI 智能总结 - 我将内容总结至 2999 字符以内，保留最大化信息
B. 手动删减 - 您自己决定保留哪些内容
C. 取消操作 - 不保存到 Cubox

请回复 A、B 或 C"
```

**User chooses A (AI Summarization):**
- Intelligently summarize content to ≤2999 characters
- Preserve key information and main points
- Maintain readability
- Show summary to user for confirmation before saving

**User chooses B (Manual Trim):**
- Show current character count
- Ask user to provide trimmed content
- Verify new content ≤2999 chars
- Proceed to save

**User chooses C (Cancel):**
- Cancel operation
- Suggest alternatives (save as URL if applicable)

### Step 2: Prepare Content (CRITICAL for text/memos)

**For text content (memos), MUST perform these steps:**

1. **Strip Markdown formatting** - Convert to plain text:
   ```python
   # Remove Markdown syntax:
   # - Headers (# ## ###)
   # - Bold (**text** or __text__)
   # - Italic (*text* or _text_)
   # - Links ([text](url))
   # - Code blocks (```code```)
   # - Inline code (`code`)
   # - Lists (- * +)
   # - Blockquotes (>)
   # - Horizontal rules (---)
   # Keep only plain text with line breaks
   ```

2. **Count characters**:
   ```python
   char_count = len(plain_text_content)
   ```

3. **Verify character limit**:
   - If char_count > 2999: Go to Step 1.6 (ask user for decision)
   - If char_count ≤ 2999: Proceed to Step 3

4. **Gather optional parameters** (if not provided):
   - **Title**: Custom title (if not provided, Cubox auto-generates)
   - **Tags**: Comma-separated tags for organization
   - **Folder**: Target folder name (defaults to Inbox)
   - **Description**: Optional description

**Example interaction:**
```
User: "保存到Cubox"
Claude: "好的,我来帮你保存到Cubox。
内容已转换为纯文本格式。
字符数: [count]/2999

请问:
1. 需要添加标签吗?(例如: AI,笔记)
2. 要保存到特定收藏夹吗?
3. 需要自定义标题吗?"
```

### Step 3: Execute Save - ONLY USE OFFICIAL SCRIPT

**🚨 CRITICAL: NEVER create custom Python scripts**
- ❌ DO NOT use Write tool to create .py files
- ❌ DO NOT write helper scripts or wrappers
- ✅ ONLY call the official script: `C:\Users\26084\.stepfun\skills\cubox-saver\scripts\save_to_cubox.py`

**The official script path:**
```
C:\Users\26084\.stepfun\skills\cubox-saver\scripts\save_to_cubox.py
```

**🔓 API URL Auto-Loading**
- ✅ API URL is **automatically loaded** from encrypted config
- ❌ **No need to provide --api-url** parameter (unless updating)
- 🔐 First-time users: Provide --api-url once, it will be saved

**For conversation content:**
```bash
# Content MUST be plain text, ≤2999 chars
# API URL auto-loaded from encrypted config
python "C:\Users\26084\.stepfun\skills\cubox-saver\scripts\save_to_cubox.py" \
  --type memo \
  --content "Plain text conversation (no Markdown, ≤2999 chars)" \
  --title "AI对话 - YYYY-MM-DD" \
  --tags "AI,对话" \
  --folder "AI笔记"
```

**For URLs:**
```bash
# URLs have no character limit or format restrictions
# API URL auto-loaded from encrypted config
python "C:\Users\26084\.stepfun\skills\cubox-saver\scripts\save_to_cubox.py" \
  --type url \
  --content "https://example.com" \
  --title "Article Title" \
  --tags "tech,reading" \
  --folder "Articles"
```
```

**For files (after user confirmation and validation):**
```bash
# ❌ WRONG - Never use command injection
# file_content=$(cat "/path/to/file.txt")

# ✅ CORRECT - Content already validated through Read tool
# After: Read → Convert → Count → Validate → Confirm
# API URL auto-loaded from encrypted config
python "C:\Users\26084\.stepfun\skills\cubox-saver\scripts\save_to_cubox.py" \
  --type memo \
  --content "$validated_plain_text" \
  --title "filename.txt" \
  --tags "notes" \
  --folder "Documents"
```

**For memos:**
```bash
# Content MUST be plain text, ≤2999 chars
# API URL auto-loaded from encrypted config
python "C:\Users\26084\.stepfun\skills\cubox-saver\scripts\save_to_cubox.py" \
  --type memo \
  --content "Plain text note (≤2999 chars)" \
  --title "Meeting Notes" \
  --tags "work,meetings" \
  --folder "Work"
```

**First-time setup (provide API URL once):**
```bash
# Only needed on first use or when updating API URL
python "C:\Users\26084\.stepfun\skills\cubox-saver\scripts\save_to_cubox.py" \
  --api-url "YOUR_CUBOX_API_URL" \
  --type memo \
  --content "Test message"

# API URL will be encrypted and saved
# Future uses don't need --api-url parameter
```

**REMINDER: Why only use the official script?**
- ✅ Contains all security validations (command injection detection)
- ✅ Contains character limit checks (≤2999)
- ✅ Contains Markdown format detection
- ✅ Tested and verified to work correctly
- ✅ Maintained and updated with bug fixes

### Step 4: Report Success with Link

After successful save, **ALWAYS display the Cubox link** to the user:

```
✅ 内容已成功保存到 Cubox!

🔗 查看链接: https://cubox.pro/my/card?id=xxxxx

标题: [title]
标签: [tags]
收藏夹: [folder]
```

If link is not available in API response:
```
✅ 内容已成功保存到 Cubox!

您可以在 Cubox 应用中查看: https://cubox.pro/my/

标题: [title]
标签: [tags]
收藏夹: [folder]
```

## Content Formatting Guidelines

### CRITICAL: Plain Text Conversion

**ALL text content (memos) MUST be converted to plain text:**

1. **Remove Markdown syntax**:
   - Headers: `# Header` → `Header`
   - Bold: `**text**` or `__text__` → `text`
   - Italic: `*text*` or `_text_` → `text`
   - Links: `[text](url)` → `text (url)` or just `text`
   - Code blocks: ` ```code``` ` → `code` (remove backticks)
   - Inline code: `` `code` `` → `code`
   - Lists: `- item` → `item` (or keep dash for readability)
   - Blockquotes: `> quote` → `quote`
   - Horizontal rules: `---` → (remove or replace with line break)

2. **Preserve readability**:
   - Keep line breaks for paragraph separation
   - Keep basic structure (indentation if needed)
   - Maintain punctuation

3. **Character limit enforcement**:
   - **MUST count characters after conversion**
   - **MUST be ≤2999 characters**
   - If exceeds limit, trigger Step 1.6 (user decision)

### Conversation Content

When saving chat history, format as **plain text** (no Markdown):

```
AI对话记录 - 2026-02-10

主题: [对话主题]

对话内容:

用户: [用户消息]

AI: [AI回复]

用户: [用户消息]

AI: [AI回复]

---
保存时间: 2026-02-10
标签: AI, 对话
字符数: [count]/2999
```

**IMPORTANT**: 
- Remove all bold/italic formatting
- Keep simple text structure
- Verify ≤2999 characters before saving

### File Content

When saving file content (after user confirmation):
1. **Read file content** using Read tool
2. **Check character count** immediately
3. **Strip Markdown formatting** → convert to plain text
4. **Verify ≤2999 characters**:
   - If exceeds: Go to Step 1.6 (ask user for summarization decision)
   - If within limit: Proceed
5. **Include file name in title**
6. **Add file type as tag**
7. **Preserve basic structure** (but no Markdown syntax)

**Example transformation**:
```
Original (Markdown):
# Meeting Notes
## Action Items
- **TODO**: Review PR
- *Note*: Check [docs](url)

Converted (Plain Text):
Meeting Notes
Action Items
- TODO: Review PR
- Note: Check docs

Character count: [count]/2999 ✓
```

### URLs

For URLs, Cubox automatically:
- Fetches page content
- Creates web snapshot
- Extracts title and description
- Generates preview

Just provide the URL; Cubox handles the rest.

## Parameter Reference

All parameters for `save_to_cubox.py`:

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `--api-url` | **No*** | Your Cubox API URL (auto-loaded from config) | `https://cubox.pro/c/api/...` |
| `--type` | Yes | Content type: `url` or `memo` | `memo` |
| `--content` | Yes | **URL or PLAIN TEXT** (≤2999 chars for memo) | `"Meeting notes"` |
| `--title` | No | Custom title | `"Project Discussion"` |
| `--tags` | No | Comma-separated tags | `"work,project,notes"` |
| `--folder` | No | Folder name (created if doesn't exist) | `"Work Notes"` |
| `--description` | No | Custom description | `"Weekly sync notes"` |

**\*About `--api-url` parameter:**
- **First-time use**: Required - provide your API URL, it will be encrypted and saved
- **Subsequent uses**: Optional - API URL auto-loaded from encrypted config
- **Update**: Optional - provide new API URL to update saved config
- **Storage**: Encrypted in `config/cubox_config.enc` (machine-specific)

**CRITICAL for `--content` parameter:**
- For `type=url`: Any valid URL (no restrictions)
- For `type=memo`: **MUST be plain text** (no Markdown), **MUST be ≤2999 characters**

**Output:**
- Success message
- **Cubox link** (if available): `https://cubox.pro/my/card?id=xxxxx`
- First-time: Confirmation of API URL encryption and storage

## Common Patterns

### Pattern 0: Save URL (Web Page) - SIMPLEST & RECOMMENDED

**When user provides a web page URL:**

```python
# 1. Detect URL pattern (starts with http:// or https://)
# 2. Inform user about advantages of URL type:
#    - No character limit
#    - Automatic content extraction
#    - Web snapshot creation
#    - Rich formatting preserved
# 3. Save directly as type=url
# 4. Display Cubox link
# 5. Inform user that Cubox is processing in background
```

**Example interaction:**
```
User: "保存这个网页到 Cubox: https://example.com/article"

AI: "检测到这是一个网页链接，我将直接保存网页到 Cubox。

✅ 优势：
- Cubox 会自动抓取完整网页内容
- 自动生成标题和描述
- 创建永久网页快照
- 保留原始格式和图片
- 无字符数限制

正在保存..."

[Execute: save_to_cubox.py --type url --content "https://example.com/article"]

"✅ 网页已成功保存到 Cubox！
🔗 查看链接: https://cubox.pro/my/card?id=xxxxx

Cubox 正在后台处理网页内容，处理完成后即可阅读。"
```

**🚨 CRITICAL: Always use type=url for web pages**
- ❌ DON'T: Fetch page content and save as memo (hits 2999 char limit)
- ✅ DO: Save URL directly, let Cubox handle content extraction

### Pattern 1: Save Recent Conversation
```python
# 1. Extract last N messages from conversation
# 2. Convert to plain text (remove Markdown formatting)
# 3. Count characters
# 4. If > 2999: Ask user for summarization decision
# 5. If ≤ 2999: Save with auto-generated title including date
# 6. Display Cubox link to user
```

### Pattern 2: Save with Character Count Validation
```python
# 1. Prepare content (strip Markdown)
# 2. Count characters: len(plain_text)
# 3. Display count to user: "[count]/2999"
# 4. If exceeds: Offer summarization options
# 5. If within limit: Proceed to save
# 6. Show success message with link
```

### Pattern 3: Save File Content (with Full Validation)
```python
# 1. Detect file save request
# 2. Read file content
# 3. Convert to plain text (strip Markdown if present)
# 4. Count characters
# 5. If > 2999: Ask user to choose (summarize/trim/cancel)
# 6. If ≤ 2999: Ask user for confirmation with details
# 7. Save as plain text memo with appropriate title/tags
# 8. Display Cubox link
```

### Pattern 4: AI Summarization (when content > 2999 chars)
```python
# 1. Detect content exceeds 2999 characters
# 2. Show user: current count, limit, excess amount
# 3. Ask user to choose: A (AI summarize) / B (manual trim) / C (cancel)
# 4. If A: Intelligently summarize to ≤2999 chars
#    - Preserve key information
#    - Maintain readability
#    - Show summary to user for confirmation
# 5. If B: Ask user to provide trimmed content
# 6. If C: Cancel operation
# 7. Verify final content ≤2999 chars
# 8. Save and display link
```

### Pattern 5: Batch Save Multiple URLs
```python
# For multiple URLs (no character limit for URLs)
# Process each URL sequentially
# Report success/failure for each with links
# Provide summary at the end
```

## Error Handling

Common errors and solutions:

**Invalid API URL**: Verify URL from Cubox settings
**HTTP 401/403**: API URL may be expired, regenerate in settings
**HTTP 429**: Rate limit exceeded (500/day for premium users)
**HTTP 400**: May indicate content format issue or character limit exceeded
**Connection timeout**: Check network connection
**Content too long**: Content exceeds 2999 characters - must summarize or trim
**Invalid format**: Content contains Markdown - must convert to plain text
**File not found**: Verify file path is correct (when reading files)
**Unsupported type**: Only `url` and `memo` types are supported

## Limitations

**CRITICAL Cubox API restrictions:**
- ✅ **URLs**: No restrictions
- ⚠️ **Text content (memos)**: 
  - **MUST be plain text** (no Markdown, no HTML, no rich formatting)
  - **MUST be ≤2999 characters** (hard limit, non-negotiable)
  - **No images or media** (text only)
- ❌ **No direct file uploads** - files must be converted to plain text memos
- ❌ **No binary files** - text files only
- 📊 **Rate limit**: Premium users get 500 API calls per day

**Character counting rules:**
- Count AFTER converting to plain text
- Count includes spaces, line breaks, and punctuation
- Must be exactly ≤2999 (not 3000, not 3001)

**Always required:**
- User confirmation before saving file content
- Character count validation before saving
- Markdown-to-plain-text conversion for all memos
- User decision when content exceeds 2999 characters

## Best Practices

1. **🚨 SECURITY FIRST - Detect and reject unsafe patterns**:
   - Check for PowerShell/bash command syntax in user input
   - Reject `Get-Content`, `cat`, `$()`, `@()` patterns immediately
   - Require clean file paths only
   - Always use Read tool for file access

2. **🌐 PRIORITIZE URL type for web pages**:
   - Detect if content is a URL (starts with http:// or https://)
   - Save as type=url (no character limit, automatic processing)
   - Inform user about advantages (snapshot, rich format, auto-extraction)
   - Let Cubox handle content extraction and parsing
   
3. **ALWAYS validate character count** - Check ≤2999 before saving any memo

4. **ALWAYS convert to plain text** - Strip all Markdown formatting from memos

5. **ALWAYS ask for user decision** when content exceeds 2999 characters:
   - Offer AI summarization option
   - Offer manual trim option
   - Allow cancellation
   
6. **ALWAYS ask for confirmation** when saving file content

7. **ALWAYS display the Cubox link** after successful save

8. **Show character count** to user: "[count]/2999" for transparency (memos only)

9. **Use descriptive titles** and relevant tags for organization

10. **Organize content** into appropriate folders

11. **For oversized content**: Suggest alternatives (save as URL if it's a web page)

12. **Preserve readability** when converting to plain text (keep line breaks, structure)

13. **Test character count** after each transformation

14. **Be transparent** about limitations upfront

15. **NEVER bypass validation pipeline**:
    - Read → Convert → Count → Validate → Confirm → Save
    - Every file MUST go through this complete pipeline
    - No shortcuts, no command-line injection
    
16. **NEVER create custom Python scripts**:
    - DO NOT use Write tool to create .py files
    - ONLY use the official script in skill folder
    - Custom scripts bypass security validations
    - One official script = consistent behavior
    
16. **Educate users** about correct workflow when they attempt unsafe methods

## Workflow Summary

**For URLs (Web Pages)** - SIMPLEST & RECOMMENDED:
1. Detect URL pattern (http:// or https://)
2. Inform user about advantages (no limit, auto-processing, snapshot)
3. Save directly as type=url
4. Display Cubox link
5. Inform user Cubox is processing in background

**For Text/Memos** (requires validation):
1. Convert to plain text (strip Markdown)
2. Count characters
3. If > 2999: Ask user (summarize/trim/cancel)
4. If ≤ 2999: Proceed
5. Save as plain text memo
6. Display link with character count

**For Files** (most complex - STRICT SECURITY):
0. **Security Check**: Reject if user provides command syntax
   - ❌ Detect: `Get-Content`, `cat`, `$()`, `@()`
   - ✅ Require: Clean file path only
1. **Read using Read tool ONLY** (never command-line injection)
2. Convert to plain text (strip Markdown)
3. Count characters
4. If > 2999: Ask user (summarize/trim/cancel)
5. If ≤ 2999: Ask confirmation with details
6. **Only after confirmation**: Save as plain text memo
7. Display link with details

**CRITICAL: Content type priority:**
```
1. Is it a URL? → Save as type=url (BEST option, no limits)
2. Is it text/conversation? → Save as memo (validate ≤2999)
3. Is it a file? → Read → validate → save as memo
```

**CRITICAL: File handling MUST follow this exact sequence:**
```
User Input → Security Check → Read Tool → Convert → Count → 
Validate (>2999?) → Confirm → Save (using OFFICIAL script only) → Display Link

❌ NEVER: User Input → Command Injection → Save (bypasses all validation)
❌ NEVER: Create custom .py script → Use custom script (bypasses security)
❌ NEVER: Fetch URL content → Save as memo (use type=url instead!)
✅ ALWAYS: Use official script at C:\Users\26084\.stepfun\skills\cubox-saver\scripts\save_to_cubox.py
```

## Resources

- `scripts/save_to_cubox.py`: Main script for API calls
- `references/api_reference.md`: Detailed API documentation and setup guide
- `assets/config_template.md`: Configuration examples

    return bool(re.match(url_pattern, content.strip()))

# Examples:
# ✅ "https://example.com" → True
# ✅ "http://blog.com/article" → True
# ❌ "这是一段文字 https://link.com" → False (contains other text)
# ❌ "example.com" → False (missing protocol)
```

**STEP 2: If URL detected, save DIRECTLY as URL type**

**✅ ADVANTAGES of saving as URL type:**
- ✅ **No character limit** (unlike memo's 2999 limit)
- ✅ **Automatic parsing** - Cubox extracts title, description, content
- ✅ **Web snapshot** - Cubox creates permanent archive
- ✅ **Rich preview** - Images, formatting preserved
- ✅ **No manual conversion** - No need to strip Markdown

**🚨 IMPORTANT: Inform user clearly**
```
"检测到这是一个网页链接，我将直接保存网页到 Cubox。

✅ 优势：
- Cubox 会自动抓取完整网页内容
- 自动生成标题和描述
- 创建永久网页快照
- 保留原始格式和图片
- 无字符数限制

正在保存..."
```

**STEP 3: Execute save with type=url**
```bash
python save_to_cubox.py \
  --type url \
  --content "https://example.com" \
  --title "Optional custom title" \
  --tags "tag1,tag2" \
  --folder "Articles"
```

**STEP 4: Report success**
```
"✅ 网页已成功保存到 Cubox！

🔗 查看链接: https://cubox.pro/my/card?id=xxxxx

Cubox 正在后台处理：
- 📄 解析文章内容
- 📸 创建网页快照
- 🏷️ 提取标题和描述

处理完成后即可在 Cubox 中阅读。"
```

### Step 1.2: Text Content Validation (For non-URL content)

**CRITICAL: For ALL text content (memos), MUST perform these checks:**

1. **Character Count Check**:
   ```python
   char_count = len(content)
   if char_count > 2999:
       # MUST ask user for decision (see Step 1.6)
   ```

2. **Format Check**:
   - Remove ALL Markdown formatting (headers, bold, italic, links, code blocks, etc.)
   - Convert to plain text only
   - Preserve line breaks for readability

3. **Source Validation Check**:
   - If content appears to be from file: **MUST have used Read tool**
   - If user provided command syntax: **REJECT and require clean path**
   - If content length suspicious: **VERIFY validation was performed**

### Step 1.5: File Upload Confirmation (CRITICAL)

**When user wants to save a file:**

**STEP 0: Validate user input is safe**
- ✅ User provides clean file path: `C:\path\file.txt`
- ❌ User provides command syntax: `@(Get-Content 'path')` → **REJECT**
- ❌ User uses `cat`, `Get-Content`, `$()` → **REJECT**

**If user attempts command injection, STOP and respond:**
```
❌ 请提供文件路径，不要使用命令语法

错误示例: @(Get-Content 'file.txt')
正确示例: C:\Users\...\file.txt

我会使用安全的方式读取文件并进行必要的验证。
```

**STEP 1: Read file using Read tool ONLY**
```python
# ✅ CORRECT - Use Read tool
file_content = Read(file_path)

# ❌ WRONG - Never use command-line injection
# python script.py --content "$(cat file)"  # PROHIBITED
```

**STEP 2: Check and convert content**
- Convert to plain text (strip Markdown if present)
- Count characters: `char_count = len(plain_text)`

**STEP 3: Explain limitations to user**
```
"Cubox 仅支持纯文本内容上传，有以下限制：
1. 不能直接上传文件
2. 文本内容必须是纯文本格式（不支持 Markdown）
3. 文本内容不能超过 2999 字符

文件: [filename]
原始大小: [file size]
转换后字符数: [char_count]/2999"
```

**STEP 4: Handle based on character count**
- **If content > 2999 chars**: Go to Step 1.6 (ask user for summarization decision)
- **If content ≤ 2999 chars**: Continue to Step 5

**STEP 5: Ask for confirmation**
```
"是否确认将此文件内容保存为 Cubox 纯文本笔记?

⚠️ 注意:
- 原始格式将被转换为纯文本
- Markdown 格式将被移除
- 字符数: [char_count]/2999

回复 '是' 确认保存，或 '否' 取消。"
```

**STEP 6: Wait for user response**
- If YES → Proceed to Step 3 (Execute Save) with validated plain text
- If NO → Cancel operation

**ENFORCEMENT:**
- **NEVER skip Read tool** - Always use Read to get file content
- **NEVER accept command-injected content** - Reject PowerShell/bash syntax
- **NEVER skip character validation** - Always count and check ≤2999
- **NEVER skip user confirmation** - Always ask before saving file content

### Step 1.6: Handle Content Exceeding 2999 Characters (MANDATORY)

**When content exceeds 2999 characters, MUST ask user to choose:**

```
"⚠️ 内容超出限制

当前字符数: [char_count]
Cubox 限制: 2999 字符
超出: [char_count - 2999] 字符

请选择处理方式:

A. AI 智能总结 - 我将内容总结至 2999 字符以内，保留最大化信息
B. 手动删减 - 您自己决定保留哪些内容
C. 取消操作 - 不保存到 Cubox

请回复 A、B 或 C"
```

**User chooses A (AI Summarization):**
- Intelligently summarize content to ≤2999 characters
- Preserve key information and main points
- Maintain readability
- Show summary to user for confirmation before saving

**User chooses B (Manual Trim):**
- Show current character count
- Ask user to provide trimmed content
- Verify new content ≤2999 chars
- Proceed to save

**User chooses C (Cancel):**
- Cancel operation
- Suggest alternatives (save as URL if applicable)

### Step 2: Prepare Content (CRITICAL for text/memos)

**For text content (memos), MUST perform these steps:**

1. **Strip Markdown formatting** - Convert to plain text:
   ```python
   # Remove Markdown syntax:
   # - Headers (# ## ###)
   # - Bold (**text** or __text__)
   # - Italic (*text* or _text_)
   # - Links ([text](url))
   # - Code blocks (```code```)
   # - Inline code (`code`)
   # - Lists (- * +)
   # - Blockquotes (>)
   # - Horizontal rules (---)
   # Keep only plain text with line breaks
   ```

2. **Count characters**:
   ```python
   char_count = len(plain_text_content)
   ```

3. **Verify character limit**:
   - If char_count > 2999: Go to Step 1.6 (ask user for decision)
   - If char_count ≤ 2999: Proceed to Step 3

4. **Gather optional parameters** (if not provided):
   - **Title**: Custom title (if not provided, Cubox auto-generates)
   - **Tags**: Comma-separated tags for organization
   - **Folder**: Target folder name (defaults to Inbox)
   - **Description**: Optional description

**Example interaction:**
```
User: "保存到Cubox"
Claude: "好的,我来帮你保存到Cubox。
内容已转换为纯文本格式。
字符数: [count]/2999

请问:
1. 需要添加标签吗?(例如: AI,笔记)
2. 要保存到特定收藏夹吗?
3. 需要自定义标题吗?"
```

### Step 3: Execute Save - ONLY USE OFFICIAL SCRIPT

**🚨 CRITICAL: NEVER create custom Python scripts**
- ❌ DO NOT use Write tool to create .py files
- ❌ DO NOT write helper scripts or wrappers
- ✅ ONLY call the official script: `C:\Users\26084\.stepfun\skills\cubox-saver\scripts\save_to_cubox.py`

**The official script path:**
```
C:\Users\26084\.stepfun\skills\cubox-saver\scripts\save_to_cubox.py
```

**🔓 API URL Auto-Loading**
- ✅ API URL is **automatically loaded** from encrypted config
- ❌ **No need to provide --api-url** parameter (unless updating)
- 🔐 First-time users: Provide --api-url once, it will be saved

**For conversation content:**
```bash
# Content MUST be plain text, ≤2999 chars
# API URL auto-loaded from encrypted config
python "C:\Users\26084\.stepfun\skills\cubox-saver\scripts\save_to_cubox.py" \
  --type memo \
  --content "Plain text conversation (no Markdown, ≤2999 chars)" \
  --title "AI对话 - YYYY-MM-DD" \
  --tags "AI,对话" \
  --folder "AI笔记"
```

**For URLs:**
```bash
# URLs have no character limit or format restrictions
# API URL auto-loaded from encrypted config
python "C:\Users\26084\.stepfun\skills\cubox-saver\scripts\save_to_cubox.py" \
  --type url \
  --content "https://example.com" \
  --title "Article Title" \
  --tags "tech,reading" \
  --folder "Articles"
```
```

**For files (after user confirmation and validation):**
```bash
# ❌ WRONG - Never use command injection
# file_content=$(cat "/path/to/file.txt")

# ✅ CORRECT - Content already validated through Read tool
# After: Read → Convert → Count → Validate → Confirm
# API URL auto-loaded from encrypted config
python "C:\Users\26084\.stepfun\skills\cubox-saver\scripts\save_to_cubox.py" \
  --type memo \
  --content "$validated_plain_text" \
  --title "filename.txt" \
  --tags "notes" \
  --folder "Documents"
```

**For memos:**
```bash
# Content MUST be plain text, ≤2999 chars
# API URL auto-loaded from encrypted config
python "C:\Users\26084\.stepfun\skills\cubox-saver\scripts\save_to_cubox.py" \
  --type memo \
  --content "Plain text note (≤2999 chars)" \
  --title "Meeting Notes" \
  --tags "work,meetings" \
  --folder "Work"
```

**First-time setup (provide API URL once):**
```bash
# Only needed on first use or when updating API URL
python "C:\Users\26084\.stepfun\skills\cubox-saver\scripts\save_to_cubox.py" \
  --api-url "YOUR_CUBOX_API_URL" \
  --type memo \
  --content "Test message"

# API URL will be encrypted and saved
# Future uses don't need --api-url parameter
```

**REMINDER: Why only use the official script?**
- ✅ Contains all security validations (command injection detection)
- ✅ Contains character limit checks (≤2999)
- ✅ Contains Markdown format detection
- ✅ Tested and verified to work correctly
- ✅ Maintained and updated with bug fixes

### Step 4: Report Success with Link

After successful save, **ALWAYS display the Cubox link** to the user:

```
✅ 内容已成功保存到 Cubox!

🔗 查看链接: https://cubox.pro/my/card?id=xxxxx

标题: [title]
标签: [tags]
收藏夹: [folder]
```

If link is not available in API response:
```
✅ 内容已成功保存到 Cubox!

您可以在 Cubox 应用中查看: https://cubox.pro/my/

标题: [title]
标签: [tags]
收藏夹: [folder]
```

## Content Formatting Guidelines

### CRITICAL: Plain Text Conversion

**ALL text content (memos) MUST be converted to plain text:**

1. **Remove Markdown syntax**:
   - Headers: `# Header` → `Header`
   - Bold: `**text**` or `__text__` → `text`
   - Italic: `*text*` or `_text_` → `text`
   - Links: `[text](url)` → `text (url)` or just `text`
   - Code blocks: ` ```code``` ` → `code` (remove backticks)
   - Inline code: `` `code` `` → `code`
   - Lists: `- item` → `item` (or keep dash for readability)
   - Blockquotes: `> quote` → `quote`
   - Horizontal rules: `---` → (remove or replace with line break)

2. **Preserve readability**:
   - Keep line breaks for paragraph separation
   - Keep basic structure (indentation if needed)
   - Maintain punctuation

3. **Character limit enforcement**:
   - **MUST count characters after conversion**
   - **MUST be ≤2999 characters**
   - If exceeds limit, trigger Step 1.6 (user decision)

### Conversation Content

When saving chat history, format as **plain text** (no Markdown):

```
AI对话记录 - 2026-02-10

主题: [对话主题]

对话内容:

用户: [用户消息]

AI: [AI回复]

用户: [用户消息]

AI: [AI回复]

---
保存时间: 2026-02-10
标签: AI, 对话
字符数: [count]/2999
```

**IMPORTANT**: 
- Remove all bold/italic formatting
- Keep simple text structure
- Verify ≤2999 characters before saving

### File Content

When saving file content (after user confirmation):
1. **Read file content** using Read tool
2. **Check character count** immediately
3. **Strip Markdown formatting** → convert to plain text
4. **Verify ≤2999 characters**:
   - If exceeds: Go to Step 1.6 (ask user for summarization decision)
   - If within limit: Proceed
5. **Include file name in title**
6. **Add file type as tag**
7. **Preserve basic structure** (but no Markdown syntax)

**Example transformation**:
```
Original (Markdown):
# Meeting Notes
## Action Items
- **TODO**: Review PR
- *Note*: Check [docs](url)

Converted (Plain Text):
Meeting Notes
Action Items
- TODO: Review PR
- Note: Check docs

Character count: [count]/2999 ✓
```

### URLs

For URLs, Cubox automatically:
- Fetches page content
- Creates web snapshot
- Extracts title and description
- Generates preview

Just provide the URL; Cubox handles the rest.

## Parameter Reference

All parameters for `save_to_cubox.py`:

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `--api-url` | **No*** | Your Cubox API URL (auto-loaded from config) | `https://cubox.pro/c/api/...` |
| `--type` | Yes | Content type: `url` or `memo` | `memo` |
| `--content` | Yes | **URL or PLAIN TEXT** (≤2999 chars for memo) | `"Meeting notes"` |
| `--title` | No | Custom title | `"Project Discussion"` |
| `--tags` | No | Comma-separated tags | `"work,project,notes"` |
| `--folder` | No | Folder name (created if doesn't exist) | `"Work Notes"` |
| `--description` | No | Custom description | `"Weekly sync notes"` |

**\*About `--api-url` parameter:**
- **First-time use**: Required - provide your API URL, it will be encrypted and saved
- **Subsequent uses**: Optional - API URL auto-loaded from encrypted config
- **Update**: Optional - provide new API URL to update saved config
- **Storage**: Encrypted in `config/cubox_config.enc` (machine-specific)

**CRITICAL for `--content` parameter:**
- For `type=url`: Any valid URL (no restrictions)
- For `type=memo`: **MUST be plain text** (no Markdown), **MUST be ≤2999 characters**

**Output:**
- Success message
- **Cubox link** (if available): `https://cubox.pro/my/card?id=xxxxx`
- First-time: Confirmation of API URL encryption and storage

## Common Patterns

### Pattern 1: Save Recent Conversation
```python
# 1. Extract last N messages from conversation
# 2. Convert to plain text (remove Markdown formatting)
# 3. Count characters
# 4. If > 2999: Ask user for summarization decision
# 5. If ≤ 2999: Save with auto-generated title including date
# 6. Display Cubox link to user
```

### Pattern 2: Save with Character Count Validation
```python
# 1. Prepare content (strip Markdown)
# 2. Count characters: len(plain_text)
# 3. Display count to user: "[count]/2999"
# 4. If exceeds: Offer summarization options
# 5. If within limit: Proceed to save
# 6. Show success message with link
```

### Pattern 3: Save File Content (with Full Validation)
```python
# 1. Detect file save request
# 2. Read file content
# 3. Convert to plain text (strip Markdown if present)
# 4. Count characters
# 5. If > 2999: Ask user to choose (summarize/trim/cancel)
# 6. If ≤ 2999: Ask user for confirmation with details
# 7. Save as plain text memo with appropriate title/tags
# 8. Display Cubox link
```

### Pattern 4: AI Summarization (when content > 2999 chars)
```python
# 1. Detect content exceeds 2999 characters
# 2. Show user: current count, limit, excess amount
# 3. Ask user to choose: A (AI summarize) / B (manual trim) / C (cancel)
# 4. If A: Intelligently summarize to ≤2999 chars
#    - Preserve key information
#    - Maintain readability
#    - Show summary to user for confirmation
# 5. If B: Ask user to provide trimmed content
# 6. If C: Cancel operation
# 7. Verify final content ≤2999 chars
# 8. Save and display link
```

### Pattern 5: Batch Save Multiple URLs
```python
# For multiple URLs (no character limit for URLs)
# Process each URL sequentially
# Report success/failure for each with links
# Provide summary at the end
```

## Error Handling

Common errors and solutions:

**Invalid API URL**: Verify URL from Cubox settings
**HTTP 401/403**: API URL may be expired, regenerate in settings
**HTTP 429**: Rate limit exceeded (500/day for premium users)
**HTTP 400**: May indicate content format issue or character limit exceeded
**Connection timeout**: Check network connection
**Content too long**: Content exceeds 2999 characters - must summarize or trim
**Invalid format**: Content contains Markdown - must convert to plain text
**File not found**: Verify file path is correct (when reading files)
**Unsupported type**: Only `url` and `memo` types are supported

## Limitations

**CRITICAL Cubox API restrictions:**
- ✅ **URLs**: No restrictions
- ⚠️ **Text content (memos)**: 
  - **MUST be plain text** (no Markdown, no HTML, no rich formatting)
  - **MUST be ≤2999 characters** (hard limit, non-negotiable)
  - **No images or media** (text only)
- ❌ **No direct file uploads** - files must be converted to plain text memos
- ❌ **No binary files** - text files only
- 📊 **Rate limit**: Premium users get 500 API calls per day

**Character counting rules:**
- Count AFTER converting to plain text
- Count includes spaces, line breaks, and punctuation
- Must be exactly ≤2999 (not 3000, not 3001)

**Always required:**
- User confirmation before saving file content
- Character count validation before saving
- Markdown-to-plain-text conversion for all memos
- User decision when content exceeds 2999 characters

## Best Practices

1. **🚨 SECURITY FIRST - Detect and reject unsafe patterns**:
   - Check for PowerShell/bash command syntax in user input
   - Reject `Get-Content`, `cat`, `$()`, `@()` patterns immediately
   - Require clean file paths only
   - Always use Read tool for file access
   
2. **ALWAYS validate character count** - Check ≤2999 before saving any memo

3. **ALWAYS convert to plain text** - Strip all Markdown formatting from memos

4. **ALWAYS ask for user decision** when content exceeds 2999 characters:
   - Offer AI summarization option
   - Offer manual trim option
   - Allow cancellation
   
5. **ALWAYS ask for confirmation** when saving file content

6. **ALWAYS display the Cubox link** after successful save

7. **Show character count** to user: "[count]/2999" for transparency

8. **Use descriptive titles** and relevant tags for organization

9. **Organize content** into appropriate folders

10. **For oversized content**: Suggest alternatives (cloud storage + URL)

11. **Preserve readability** when converting to plain text (keep line breaks, structure)

12. **Test character count** after each transformation

13. **Be transparent** about limitations upfront

14. **NEVER bypass validation pipeline**:
    - Read → Convert → Count → Validate → Confirm → Save
    - Every file MUST go through this complete pipeline
    - No shortcuts, no command-line injection
    
15. **NEVER create custom Python scripts**:
    - DO NOT use Write tool to create .py files
    - ONLY use the official script in skill folder
    - Custom scripts bypass security validations
    - One official script = consistent behavior
    
16. **Educate users** about correct workflow when they attempt unsafe methods

## Workflow Summary

**For URLs** (simple):
1. Validate URL format
2. Save directly (no restrictions)
3. Display link

**For Text/Memos** (requires validation):
1. Convert to plain text (strip Markdown)
2. Count characters
3. If > 2999: Ask user (summarize/trim/cancel)
4. If ≤ 2999: Proceed
5. Save as plain text memo
6. Display link with character count

**For Files** (most complex - STRICT SECURITY):
0. **Security Check**: Reject if user provides command syntax
   - ❌ Detect: `Get-Content`, `cat`, `$()`, `@()`
   - ✅ Require: Clean file path only
1. **Read using Read tool ONLY** (never command-line injection)
2. Convert to plain text (strip Markdown)
3. Count characters
4. If > 2999: Ask user (summarize/trim/cancel)
5. If ≤ 2999: Ask confirmation with details
6. **Only after confirmation**: Save as plain text memo
7. Display link with details

**CRITICAL: File handling MUST follow this exact sequence:**
```
User Input → Security Check → Read Tool → Convert → Count → 
Validate (>2999?) → Confirm → Save (using OFFICIAL script only) → Display Link

❌ NEVER: User Input → Command Injection → Save (bypasses all validation)
❌ NEVER: Create custom .py script → Use custom script (bypasses security)
✅ ALWAYS: Use official script at C:\Users\26084\.stepfun\skills\cubox-saver\scripts\save_to_cubox.py
```

## Resources

- `scripts/save_to_cubox.py`: Main script for API calls
- `references/api_reference.md`: Detailed API documentation and setup guide
- `assets/config_template.md`: Configuration examples
