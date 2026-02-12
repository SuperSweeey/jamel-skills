# 快速开始指南

如果你已经熟悉 Python 和命令行，可以按照以下步骤快速开始使用 `douyin-transcriber-skill`。

## 📋 前置要求

- Python 3.8+
- 阿里云账号（OSS + DashScope）
- Notion 账号
- 稳定的网络连接

## 🚀 5 分钟快速开始

### 1. 获取代码

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/douyin-transcriber-skill.git

# 进入目录
cd douyin-transcriber-skill/douyin-notion
```

### 2. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装浏览器（用于下载视频）
playwright install chromium
```

### 3. 配置 API Keys

```bash
# 复制配置模板
cp config.json.template config.json

# 编辑 config.json，填入你的 API keys
# 使用你喜欢的编辑器，例如：
# Windows: notepad config.json
# macOS/Linux: nano config.json 或 vim config.json
```

**config.json 配置说明：**

```json
{
  "oss_access_key_id": "你的阿里云OSS AccessKey ID",
  "oss_access_key_secret": "你的阿里云OSS AccessKey Secret",
  "oss_bucket_name": "你的OSS Bucket名称",
  "oss_endpoint": "oss-cn-beijing.aliyuncs.com",
  "dashscope_api_key": "sk-你的DashScope API Key",
  "notion_token": "secret_你的Notion Token",
  "notion_database_id": "你的Notion数据库ID",
  "ffmpeg_path": "tools\\ffmpeg\\bin\\ffmpeg.exe",
  "output_dir": "./output"
}
```

**如何获取这些值：**

- **阿里云 OSS**: [阿里云控制台](https://oss.console.aliyun.com/) → 创建 Bucket → 获取 AccessKey
- **阿里云 DashScope**: [DashScope 控制台](https://dashscope.console.aliyun.com/) → 创建 API-KEY
- **Notion**: [Notion Developers](https://www.notion.so/my-integrations) → 创建 Integration → 复制 Token
  - 然后在 Notion 中创建数据库 → 连接 Integration → 从 URL 复制 database_id

详细步骤参见 `USER_GUIDE.md` 的 [配置服务账号](#配置服务账号) 章节。

### 4. 开始使用

**处理单个视频：**

```bash
python main.py --url "https://v.douyin.com/xxxxx/"
```

**批量处理多个视频：**

1. 创建 `urls.txt` 文件，每行一个链接：
   ```
   https://v.douyin.com/xxx1/
   https://v.douyin.com/xxx2/
   https://v.douyin.com/xxx3/
   ```

2. 执行批量处理：
   ```bash
   python main.py --batch urls.txt
   ```

**仅下载视频（不进行转录）：**

```bash
python main.py --url "https://v.douyin.com/xxxxx/" --download-only
```

**跳过 Notion 同步（仅本地保存）：**

```bash
python main.py --url "https://v.douyin.com/xxxxx/" --no-notion
```

### 5. 查看结果

处理完成后，你可以在以下位置查看结果：

- **本地视频文件**：`output/downloads/video_xxx.mp4`
- **本地转录文本**：`output/transcripts/transcript_xxx.txt`
- **Notion 页面**：在你配置的数据库中查看

---

## 🎉 恭喜！

你已经完成了 `douyin-transcriber-skill` 的快速开始设置！

**下一步建议：**
1. 阅读 `USER_GUIDE.md` 了解更多详细功能
2. 探索批量处理、自定义配置等高级功能
3. 查看 `UPLOAD_GUIDE.md` 了解如何分享到 GitHub

**需要帮助？**
- 查看 `USER_GUIDE.md` 的 [故障排除](#故障排除) 章节
- 在 GitHub 上提交 Issue
- 检查日志文件（如果有）

祝你使用愉快！🚀
