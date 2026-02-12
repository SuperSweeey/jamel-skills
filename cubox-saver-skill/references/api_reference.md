# Cubox API Configuration Guide

## Getting Your API URL

To use this skill, you need to obtain your personal Cubox API URL:

1. Open Cubox (web version recommended)
2. Go to **Settings** (偏好设置)
3. Navigate to **Extensions and Automation** (扩展中心和自动化)
4. Find **API Extensions** (API 扩展)
5. Click **Enable API Link** (启用 API 链接)
6. Copy your unique API URL

⚠️ **Security Warning**: Your API URL is a unique credential. Keep it private and do not share it with others. If compromised, you can regenerate a new URL in the same settings page (the old one will be invalidated).

## API Specifications

### Endpoint
Your personal API URL (obtained from settings)

### Request Format
- Method: `POST`
- Content-Type: `application/json`

### Supported Content Types

#### 1. URL (Web Page)
Save a web page to Cubox. Cubox will automatically parse the article, create a snapshot, etc.

**No restrictions on URLs.**

```json
{
  "type": "url",
  "content": "https://example.com",
  "title": "Optional title",
  "description": "Optional description",
  "tags": ["tag1", "tag2"],
  "folder": "Folder name"
}
```

#### 2. Memo (Quick Note)
Save text content as a quick note.

**CRITICAL RESTRICTIONS:**
- ✅ **Content MUST be plain text** (no Markdown, no HTML, no rich formatting)
- ✅ **Content MUST be ≤2999 characters** (hard limit, strictly enforced)
- ❌ **NO Markdown syntax** (headers, bold, italic, links, code blocks, etc.)
- ❌ **NO special formatting**

```json
{
  "type": "memo",
  "content": "Your PLAIN TEXT content here (≤2999 characters)",
  "title": "Optional title",
  "description": "Optional description",
  "tags": ["tag1", "tag2"],
  "folder": "Folder name"
}
```

### Field Descriptions

- **type** (required): Content type - `url` or `memo`
- **content** (required): 
  - For `url`: Any valid URL (no restrictions)
  - For `memo`: **Plain text only, maximum 2999 characters**
- **title** (optional): Custom title. If not provided, Cubox will try to generate one
- **description** (optional): Custom description. If not provided, Cubox will try to generate one
- **tags** (optional): Array of tag names
- **folder** (optional): Folder name. If not specified, content goes to Inbox

### Character Limit Details

**For memo type:**
- **Maximum**: 2999 characters (not 3000, not 3001)
- **Counting**: Includes all characters (letters, numbers, spaces, punctuation, line breaks)
- **Enforcement**: Server-side validation, requests exceeding limit will be rejected
- **Recommendation**: Always validate character count before sending request

**Character counting example:**
```python
content = "Your plain text content here"
char_count = len(content)  # Must be ≤ 2999
```

### Format Requirements

**For memo type, content must be plain text:**

❌ **NOT allowed:**
```
# Header (Markdown header)
**bold text** (Markdown bold)
*italic text* (Markdown italic)
[link](url) (Markdown link)
`code` (Markdown inline code)
```code block``` (Markdown code block)
```

✅ **Allowed:**
```
Header (plain text)
bold text (plain text)
italic text (plain text)
link: url (plain text with URL)
code (plain text)
code block (plain text)
```

### Rate Limits

- Premium users: 500 API calls per day

### Response

- Success: HTTP 200
  ```json
  {
    "code": "item_id_here",
    "message": "success"
  }
  ```
- Error: HTTP error code with error message
  - HTTP 400: Bad request (may indicate content too long or invalid format)
  - HTTP 401/403: Invalid or expired API URL
  - HTTP 429: Rate limit exceeded

## Usage Notes

1. **Always validate character count** for memo type before sending request
2. **Always convert to plain text** - strip all Markdown/HTML formatting
3. After successful save, Cubox will process the content in the background (parsing, snapshot, etc.), which may take some time
4. If title or description is not specified, Cubox will attempt to auto-generate them
5. If folder is not specified, content will be saved to your Inbox
6. Tags and folders will be created automatically if they don't exist
7. **Content exceeding 2999 characters will be rejected** - summarize or trim first

## Error Handling

**HTTP 400 (Bad Request):**
- Most common cause: Content exceeds 2999 characters
- Solution: Reduce content length to ≤2999 characters

**HTTP 401/403 (Unauthorized):**
- Cause: Invalid or expired API URL
- Solution: Regenerate API URL in Cubox settings

**HTTP 429 (Too Many Requests):**
- Cause: Rate limit exceeded (500 calls/day for premium users)
- Solution: Wait until next day or reduce API call frequency
