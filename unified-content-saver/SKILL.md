---
name: unified-content-saver
description: 统一内容保存工具 - 整合抖音/小红书转录、AI总结、多平台保存（Notion/GitHub/Cubox）
---

# 🎯 统一内容保存工具

整合了抖音/小红书视频转录、AI总结、多平台保存（Notion/GitHub/Cubox）

## 📋 目录

1. [概述](#概述)
2. [使用场景](#使用场景)
3. [工作流程](#工作流程)
4. [整合的Skill](#整合的skill)
5. [目录结构](#目录结构)
6. [使用方法](#使用方法)
7. [配置说明](#配置说明)

---

## 📖 概述

这是一个统一的内容保存工具，整合了以下功能：

- **内容获取**：
  - 抖音视频转录
  - 小红书内容读取
  - 文字内容直接输入

- **内容处理**：
  - AI智能总结
  - 格式转换

- **多平台保存**：
  - Notion数据库
  - GitHub Pages
  - Cubox稍后读

---

## 🎬 使用场景

### 场景1：看到抖音/小红书视频

1. 用户在抖音/小红书看到一个好视频
2. 把链接发给AI
3. AI自动转录成文本
4. AI生成智能总结
5. AI询问："这个内容想保存到哪里？（Notion/GitHub/Cubox/都保存）"
6. 用户选择后执行

### 场景2：有一段文字

1. 用户把一段文字发给AI
2. AI生成智能总结
3. AI询问："这个内容想保存到哪里？（Notion/GitHub/Cubox/都保存）"
4. 用户选择后执行

---

## 🔄 工作流程

```
用户输入（视频链接/文字）
    ↓
内容获取（下载视频/读取文字）
    ↓
内容处理（转录/AI总结）
    ↓
询问保存目标（Notion/GitHub/Cubox/都保存）
    ↓
执行保存
    ↓
返回结果链接
```

### 详细步骤：

1. **Step 1：内容获取
   - 视频链接 → 下载视频 → 提取音频 → 云端转录
   - 文字内容 → 直接处理

2. **Step 2**：AI总结
   - 生成智能摘要
   - 提取关键信息

3. **Step 3**：询问用户
   - 显示可选择的保存目标
   - 让用户选择

4. **Step 4**：执行保存
   - 根据用户选择保存到对应平台

---

## 🔧 整合的Skill

### 1. **douyin-transcriber-skill**
- 功能：抖音视频转录
- 目录：`../douyin-transcriber-skill/`
- 功能：
  - 抖音视频下载
  - 音频提取
  - 云端转录（阿里云Paraformer）
  - Notion同步

### 2. **github-pages-publisher**
- 功能：发布到GitHub Pages
- 目录：`../github-pages-publisher/`
- 功能：
  - 生成HTML页面
  - 更新首页列表
  - 推送到GitHub

### 3. **cubox-saver-skill**
- 功能：保存到Cubox
- 目录：`../cubox-saver-skill/`
- 功能：
  - 保存URL
  - 保存文字笔记
  - 字符数限制检查（≤2999）

### 4. **xiaohongshu-reader**
- 功能：小红书内容读取
- 目录：`../xiaohongshu-reader/`

---

## 📁 目录结构

```
unified-content-saver/
├── SKILL.md              # 本文件
├── main.py               # 主程序
├── config.json           # 配置文件
├── modules/             # 模块目录
│   ├── __init__.py
│   ├── content_fetcher.py    # 内容获取模块
│   ├── ai_summarizer.py    # AI总结模块
│   ├── notion_saver.py       # Notion保存模块
│   ├── github_saver.py       # GitHub保存模块
│   └── cubox_saver.py       # Cubox保存模块
└── utils/               # 工具目录
    ├── __init__.py
    └── helpers.py
```

---

## 🚀 使用方法

### 快速开始

#### 1. 配置

首先复制配置模板：

```bash
cp config.json.template config.json
```

编辑 `config.json`，填入你的配置：

```json
{
  "oss_access_key_id": "你的AccessKey ID",
  "oss_access_key_secret": "你的AccessKey Secret",
  "oss_bucket_name": "你的Bucket名称",
  "oss_endpoint": "oss-cn-beijing.aliyuncs.com",
  "dashscope_api_key": "sk-你的DashScope API Key",
  "notion_token": "secret_你的Notion Token",
  "notion_database_id": "你的数据库ID",
  "github_token": "ghp_你的GitHub Token",
  "github_repo": "SuperSweeey.github.io",
  "cubox_api_url": "你的Cubox API URL",
  "ffmpeg_path": "/usr/bin/ffmpeg",
  "output_dir": "./output"
}
```

#### 2. 使用

**处理抖音视频：

```bash
python main.py --url "https://v.douyin.com/xxxxx/"
```

**处理文字内容：**

```bash
python main.py --text "这是一段文字内容" --title "内容标题"
```

**批量处理：

```bash
python main.py --batch urls.txt
```

---

## ⚙️ 配置说明

### 必需配置：

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `oss_access_key_id` | 阿里云OSS AccessKey ID | `LTAI5t...` |
| `oss_access_key_secret` | 阿里云OSS AccessKey Secret | `ZWEXmw...` |
| `oss_bucket_name` | 阿里云OSS Bucket名称 | `douyin-transcribe` |
| `oss_endpoint` | 阿里云OSS Endpoint | `oss-cn-beijing.aliyuncs.com` |
| `dashscope_api_key` | 阿里云DashScope API Key | `sk-...` |
| `notion_token` | Notion Integration Token | `secret_...` |
| `notion_database_id` | Notion数据库ID | `2485c3bafe...` |
| `github_token` | GitHub Personal Access Token | `ghp_...` |
| `github_repo` | GitHub仓库名称 | `SuperSweeey.github.io` |
| `cubox_api_url` | Cubox API URL | `https://cubox.pro/...` |
| `ffmpeg_path` | FFmpeg路径 | `/usr/bin/ffmpeg` |
| `output_dir` | 输出目录 | `./output` |

---

## 📝 详细流程示例

### 示例1：处理抖音视频

```
用户：转录这个视频：https://v.douyin.com/xxxxx/

AI：好的！我来帮你处理！
[处理中...]

[处理完成！

转录完成！

📝 内容预览：
[显示转录内容前500字]

💡 AI总结：
[显示AI总结]

📋 请选择保存目标：
A. 保存到Notion
B. 保存到GitHub Pages
C. 保存到Cubox
D. 都保存
E. 只保存转录文本（不保存）

请回复A/B/C/D/E

用户：B

AI：好的！正在保存到GitHub Pages...

✅ 保存成功！
🔗 GitHub Pages链接：https://supersweeey.github.io/notes/xxxxx.html
```

### 示例2：处理文字内容

```
用户：帮我保存这段文字：
[用户粘贴文字]

AI：好的！我来帮你处理！

💡 AI总结：
[显示AI总结]

📋 请选择保存目标：
A. 保存到Notion
B. 保存到GitHub Pages
C. 保存到Cubox
D. 都保存
E. 只保存转录文本（不保存）

请回复A/B/C/D/E
```

---

## 🔒 注意事项

### Cubox限制

- 文字内容必须是纯文本（不支持Markdown）
- 文字内容不能超过2999字符
- 如果超过，需要AI总结或手动删减

### GitHub Pages

- 需要先pull再push（避免冲突）
- 网络不稳定时需要重试
- 使用HTTP/1.1配置

### Notion

- 需要先连接Integration到数据库
- 数据库字段必须有正确的字段

---

## 🛠️ 故障排除

### 问题1：TLS连接错误

**错误信息**：
```
GnuTLS recv error (-110): The TLS connection was non-properly terminated.
```

**解决方法**：
```bash
git config http.version HTTP/1.1
git config http.postBuffer 524288000
```

### 问题2：Cubox字符超限

**解决方法**：
- AI总结到2999字符以内
- 或手动删减内容

### 问题3：Notion连接失败

**检查**：
- Token是否正确
- Integration是否已连接到数据库
- 数据库字段是否正确

---

## 📚 参考资料

- [douyin-transcriber-skill](../douyin-transcriber-skill/SKILL.md)
- [github-pages-publisher](../github-pages-publisher/SKILL.md)
- [cubox-saver-skill](../cubox-saver-skill/SKILL.md)

