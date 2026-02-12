# 用户使用指南

欢迎来到 `douyin-transcriber-skill`！本指南将帮助你从零开始安装和使用这个工具。

## 📋 目录

1. [快速开始](#快速开始)
2. [详细安装步骤](#详细安装步骤)
3. [配置服务账号](#配置服务账号)
4. [使用方法](#使用方法)
5. [常见问题](#常见问题)
6. [故障排除](#故障排除)

---

## 🚀 快速开始

如果你已经熟悉 Python 和命令行，可以按照以下快速步骤操作：

```bash
# 1. 进入 douyin-notion 目录
cd douyin-notion

# 2. 安装依赖
pip install -r requirements.txt
playwright install chromium

# 3. 配置（填入你的 API keys）
cp config.json.template config.json
# 编辑 config.json 填入你的配置

# 4. 开始使用
python main.py --url "https://v.douyin.com/xxxxx/"
```

**详细说明请继续阅读下文。**

---

## 📦 详细安装步骤

### 步骤 1: 前提条件

确保你的系统满足以下要求：

- **操作系统**: Windows 10/11, macOS, 或 Linux
- **Python**: 3.8 或更高版本
- **网络**: 稳定的互联网连接
- **存储空间**: 至少 1GB 可用空间（用于下载视频和临时文件）

**检查 Python 版本**:

```bash
python --version
# 或
python3 --version
```

如果 Python 未安装，请访问 [python.org](https://www.python.org/downloads/) 下载安装。

### 步骤 2: 获取代码

#### 方法一：使用 Git 克隆（推荐）

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/douyin-transcriber-skill.git

# 进入目录
cd douyin-transcriber-skill
```

#### 方法二：下载 ZIP 文件

1. 访问 GitHub 仓库页面
2. 点击绿色的 `Code` 按钮
3. 选择 `Download ZIP`
4. 解压 ZIP 文件到你想存放的位置
5. 进入解压后的文件夹

### 步骤 3: 进入 douyin-notion 目录

```bash
cd douyin-notion
```

目录结构应该如下：

```
douyin-notion/
├── main.py
├── requirements.txt
├── config.json.template
└── modules/
    ├── __init__.py
    ├── config.py
    ├── logger.py
    ├── downloader.py
    ├── audio_extractor.py
    ├── oss_uploader.py
    ├── transcriber.py
    ├── notion_sync.py
    └── pipeline.py
```

### 步骤 4: 创建虚拟环境（可选但推荐）

虚拟环境可以隔离项目依赖，避免与其他 Python 项目冲突。

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

激活后，命令行提示符前面会显示 `(venv)`。

### 步骤 5: 安装 Python 依赖

```bash
pip install -r requirements.txt
```

这会安装以下包：
- `dashscope` - 阿里云 DashScope SDK
- `oss2` - 阿里云 OSS SDK
- `notion-client` - Notion API 客户端
- `playwright` - 浏览器自动化
- `requests` - HTTP 请求库

安装过程可能需要几分钟，请耐心等待。

### 步骤 6: 安装 Playwright 浏览器

```bash
playwright install chromium
```

这会下载 Chromium 浏览器，用于下载抖音视频。

---

## 🔧 配置服务账号

在使用工具之前，你需要配置三个服务的 API 密钥：

1. **阿里云 OSS** - 临时存储音频文件
2. **阿里云 DashScope** - 语音识别服务
3. **Notion Integration** - 同步到 Notion 数据库

### 1. 阿里云 OSS 配置

**步骤：**

1. 访问 [阿里云 OSS 控制台](https://oss.console.aliyun.com/)
2. 登录你的阿里云账号
3. 创建 Bucket（存储桶）：
   - 点击 `创建 Bucket`
   - Bucket 名称：例如 `douyin-transcribe`（全局唯一）
   - 地域：选择离你最近的地域，例如 `华北2（北京）`
   - 存储类型：标准存储
   - 访问权限：私有
   - 点击 `确定`
4. 获取 AccessKey：
   - 点击右上角头像 → `AccessKey 管理`
   - 创建 AccessKey
   - **保存 AccessKey ID 和 AccessKey Secret**（Secret 只显示一次！）

**需要的信息：**
- `oss_access_key_id`: 你的 AccessKey ID
- `oss_access_key_secret`: 你的 AccessKey Secret
- `oss_bucket_name`: 你的 Bucket 名称（例如 `douyin-transcribe`）
- `oss_endpoint`: 地域对应的 Endpoint（例如 `oss-cn-beijing.aliyuncs.com`）

**Endpoint 查询**：在 OSS 控制台 → Bucket 列表 → 点击你的 Bucket → `概览` 页面可以看到 `Endpoint（地域节点）`

### 2. 阿里云 DashScope 配置

**步骤：**

1. 访问 [DashScope 控制台](https://dashscope.console.aliyun.com/)
2. 登录你的阿里云账号
3. 点击左侧 `API-KEY 管理`
4. 点击 `创建新的 API-KEY`
5. **保存 API-KEY**（只显示一次！）

**需要的信息：**
- `dashscope_api_key`: 你的 API-KEY（格式如 `sk-xxxxxx`）

### 3. Notion Integration 配置

**步骤 1: 创建 Integration**

1. 访问 [Notion Developers](https://www.notion.so/my-integrations)
2. 点击 `New integration`
3. 填写信息：
   - Name: `Douyin Transcriber`（或你喜欢的名称）
   - Associated workspace: 选择你的工作区
   - 点击 `Submit`
4. **保存 `Internal Integration Token`**（这很重要！）

**步骤 2: 创建数据库**

1. 在 Notion 中创建一个新页面
2. 添加一个 `Database - Inline`
3. 设置数据库属性：
   - `Name` (Title) - 页面标题
   - `URL` (URL) - 抖音链接
   - `Category` (Select) - 分类
   - `Field` (Select) - 领域
   - `Transcript` (Text) - 转录文本
4. 点击数据库页面右上角的 `...` → `Copy link`
5. 从链接中提取 `database_id`：
   - 链接格式：`https://www.notion.so/workspace/[database_id]?v=...`
   - `database_id` 是一串 32 位的字符

**步骤 3: 连接 Integration 到数据库**

1. 在你的数据库页面，点击右上角的 `...`
2. 选择 `Add connections`
3. 找到你创建的 Integration（如 `Douyin Transcriber`）
4. 点击 `Confirm`

**需要的信息：**
- `notion_token`: 你的 Internal Integration Token（格式如 `secret_xxxxxx`）
- `notion_database_id`: 你的数据库 ID（32 位字符）

### 4. 创建配置文件

现在你已经收集了所有需要的信息，创建配置文件：

1. 复制模板文件：
   ```bash
   cd douyin-notion
   cp config.json.template config.json
   ```

2. 编辑 `config.json`，填入你的配置：
   ```json
   {
     "oss_access_key_id": "LTAI5t...",
     "oss_access_key_secret": "ZWEXmwMV...",
     "oss_bucket_name": "douyin-transcribe",
     "oss_endpoint": "oss-cn-beijing.aliyuncs.com",
     "dashscope_api_key": "sk-ba378c81ec...",
     "notion_token": "ntn_247586484...",
     "notion_database_id": "2485c3bafe...",
     "ffmpeg_path": "tools\\ffmpeg\\bin\\ffmpeg.exe",
     "output_dir": "./output"
   }
   ```

   **注意**：将示例中的值替换为你自己的真实配置。

---

## 🎯 使用方法

### 基本命令

**单条链接：**
```bash
cd douyin-notion
python main.py --url "https://v.douyin.com/xxxxx/"
```

**批量处理：**

创建 `urls.txt` 文件，每行一个链接：
```
https://v.douyin.com/xxx1/
https://v.douyin.com/xxx2/
https://v.douyin.com/xxx3/
```

执行：
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

### 工作流程

1. **准备链接**：复制抖音分享链接
2. **执行命令**：运行 `python main.py --url "链接"`
3. **等待处理**：脚本会自动完成下载、转录、同步
4. **查看结果**：
   - 本地文件：`output/downloads/` 和 `output/transcripts/`
   - Notion 页面：在你配置的数据库中查看

---

## ❓ 常见问题

### Q1: 安装依赖时出现错误怎么办？

**A:** 尝试以下解决方案：

1. **升级 pip**:
   ```bash
   pip install --upgrade pip
   ```

2. **使用国内镜像**（如果下载慢）:
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

3. **单独安装失败的包**:
   ```bash
   pip install dashscope
   pip install oss2
   # ... 逐个安装
   ```

### Q2: 视频下载失败怎么办？

**A:** 常见原因和解决方案：

1. **cookies.txt 过期**:
   - 更新 `cookies.txt` 文件
   - 或者删除 `cookies.txt` 让程序自动获取

2. **网络问题**:
   - 检查网络连接
   - 尝试使用 VPN（如果需要）

3. **链接失效**:
   - 确认抖音链接有效
   - 尝试复制新的分享链接

### Q3: OSS 上传失败怎么办？

**A:** 检查以下几点：

1. **AccessKey 配置**:
   - 确认 `config.json` 中的 `oss_access_key_id` 和 `oss_access_key_secret` 正确
   - 检查 AccessKey 是否有 OSS 访问权限

2. **Bucket 名称和 Endpoint**:
   - 确认 `oss_bucket_name` 和 `oss_endpoint` 与你在阿里云控制台创建的一致
   - Endpoint 格式如：`oss-cn-beijing.aliyuncs.com`

3. **Bucket 权限**:
   - 确认 Bucket 不是私有的，或者 AccessKey 有写入权限

### Q4: Notion 同步失败怎么办？

**A:** 常见问题和解决方案：

1. **Token 无效**:
   - 确认 `notion_token` 正确
   - 在 Notion 中检查 Integration 是否已连接到数据库

2. **Database ID 错误**:
   - 确认 `notion_database_id` 是 32 位的字符串
   - 从 Notion 数据库页面 URL 中提取

3. **数据库字段不匹配**:
   - 确认数据库有以下字段：
     - `Name` (Title)
     - `URL` (URL)
     - `Category` (Select)
     - `Field` (Select)
     - `Transcript` (Text)

4. **Integration 权限**:
   - 在 Notion 中，点击数据库页面右上角的 `...`
   - 选择 `Add connections`
   - 找到你的 Integration 并确认已连接

### Q5: 转录费用是多少？

**A:** 大致费用如下：

- **阿里云 Paraformer**: 0.008 元/分钟
  - 10 分钟视频 ≈ 0.08 元
  - 30 分钟视频 ≈ 0.24 元

- **阿里云 OSS**: 
  - 上传免费
  - 临时存储费用可忽略（几毛钱每月）

- **Notion API**: 
  - 免费额度足够个人使用

**总结**: 转录一个 10 分钟的视频大约需要 **0.1 元**（1毛钱）左右。

### Q6: 可以批量处理多少个视频？

**A:** 理论上没有限制，但建议：

- **单次批量**: 10-50 个视频为宜
- **每日总量**: 根据你的 API 配额和预算决定
- **并发限制**: Notion API 限制每秒 3 次请求，程序会自动处理

**建议**: 大批量处理时，先测试 1-2 个视频确保配置正确，再批量处理。

---

## 🔧 故障排除

### 启动失败

**现象**: 运行 `python main.py` 时报错

**检查清单**:
1. 是否在正确的目录？应该进入 `douyin-notion` 目录
2. 依赖是否安装？运行 `pip list` 检查是否安装了 `dashscope`, `oss2`, `notion-client` 等
3. Python 版本是否正确？需要 Python 3.8+

### 处理过程中断

**现象**: 处理到某个步骤时卡住或报错

**解决方案**:
1. **网络问题**: 检查网络连接，尝试重新运行
2. **API 限制**: 如果提示 rate limit，等待几分钟后重试
3. **临时文件**: 删除 `output/` 目录中的临时文件后重试

### 找不到输出文件

**现象**: 处理成功但找不到视频或转录文本

**检查位置**:
- 视频文件: `douyin-notion/output/downloads/`
- 转录文本: `douyin-notion/output/transcripts/`
- Notion: 在你配置的数据库中查看

---

## 💡 使用技巧

### 1. 自定义配置

编辑 `douyin-notion/config.json`：

```json
{
  "output_dir": "./output",    // 修改输出目录
  "ffmpeg_path": "...",        // 如果 FFmpeg 在系统 PATH 中，可以留空
  // ... 其他配置
}
```

### 2. 批量处理优化

创建 `urls.txt` 文件时，可以：
- 按顺序排列（先处理的放在前面）
- 添加注释（以 `#` 开头的行会被忽略）

示例 `urls.txt`:
```
# 这是注释
https://v.douyin.com/xxx1/
https://v.douyin.com/xxx2/
# https://v.douyin.com/xxx3/  # 这行被注释掉了
```

### 3. 结合 Notion 模板

在 Notion 中创建数据库模板，包含常用属性：
- 自动填充的字段（如处理时间）
- 预设的 Select 选项（领域、分类）
- 公式字段（自动计算视频时长等）

### 4. 定期清理

定期清理 `output/downloads/` 目录，释放存储空间：

```bash
# 删除 7 天前的视频文件（Windows PowerShell）
Get-ChildItem -Path "output/downloads" -File | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | Remove-Item

# 或手动删除
rm output/downloads/*.mp4
```

### 5. 监控费用

定期查看阿里云和 Notion 的使用情况：

- **阿里云 OSS/DashScope**: 登录 [阿里云控制台](https://www.aliyun.com/) → 费用中心
- **Notion**: 免费版足够个人使用，查看 [Notion Settings](https://www.notion.so/settings)

---

## 📞 获取帮助

如果在使用过程中遇到问题：

1. **查看故障排除章节**：本文档的 [故障排除](#故障排除) 部分
2. **查看 GitHub Issues**：访问项目的 GitHub 页面，查看是否有类似问题
3. **提交 Issue**：在 GitHub 上提交新的 Issue，描述你的问题
4. **检查日志**：查看 `douyin-notion/output/logs/` 目录中的日志文件（如果有）

---

## 🎉 恭喜！

你已经了解了如何使用 `douyin-transcriber-skill`！

**下一步**：
1. 完成 [安装步骤](#详细安装步骤)
2. 配置 [服务账号](#配置服务账号)
3. 开始 [使用](#使用方法)
4. 享受自动转录的便利！

祝你使用愉快！🚀
