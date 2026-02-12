---
name: douyin-transcriber
description: 抖音视频转录并同步到Notion的完整工作流。接收一条或多条抖音链接，自动完成视频下载、音频提取、云端转录（阿里云Paraformer）、本地保存转录文本、同步到Notion数据库。适用于内容创作者、研究员、知识管理者需要批量处理抖音视频内容并整理到Notion的场景。用户需要提供：抖音链接（必填）、Notion页面标题（必填）、领域和分类（可选，系统会给出建议）。
---

# 抖音视频转录同步工具

完整工作流：抖音下载 → 音频提取 → OSS上传 → 云端转录 → Notion同步

## 依赖组件

此 Skill 依赖 **douyin-notion** 程序，需要单独安装：

```bash
# 1. 进入 Skill 目录
cd /path/to/douyin-transcriber-skill

# 2. 安装 douyin-notion 依赖
cd douyin-notion
pip install -r requirements.txt
playwright install chromium

# 3. 配置
cp config.json.template config.json
# 编辑 config.json 填入你的 API keys
```

## 所需服务

- **阿里云 OSS**：临时存储音频文件
- **阿里云 DashScope**：语音识别（Paraformer）
- **Notion Integration**：同步到 Notion 数据库

## 快速开始

### 1. 确认环境准备

确保以下文件和配置已就位：
- `douyin-notion/config.json` - 包含所有API密钥配置
- `douyin-notion/cookies.txt` - 抖音cookies（如需要）
- `douyin-notion/tools/ffmpeg/bin/ffmpeg.exe` - 音频提取工具
- Python依赖已安装：`pip install -r douyin-notion/requirements.txt`

### 2. 执行转录流程

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

然后执行：
```bash
python main.py --batch urls.txt
```

### 3. 指定Notion分类（可选但推荐）

如果需要自定义标题、领域、分类，参考 `douyin-notion/references/classification-guide.md` 获取建议。

## 完整Workflow步骤

### Step 1: 接收用户输入

收集以下信息：
- ✅ 抖音链接（一条或多条）- **必填**
- ✅ Notion页面标题 - **必填**，建议格式：`视频主题_作者` 或 `核心观点提炼`
- 📝 领域 - 可选，如果不提供会根据内容自动建议
- 📝 分类 - 可选，如果不提供会根据内容自动建议

**示例对话：**
```
用户：请帮我转录这个视频：https://v.douyin.com/OG2cK3gITno/
我：好的！请为这个视频提供一个标题（用于Notion页面），我可以根据内容自动建议领域和分类。
用户：标题就用"京东总裁谈电商与就业"
我：收到！根据视频内容，建议分类如下：
- 领域：人类大逻辑 / 商业大逻辑
- 分类：话题资料库 / 逻辑&理论&模型库
用户：就用"人类大逻辑"和"话题资料库"
```

### Step 2: 执行Python脚本

切换到项目目录：
```bash
cd douyin-notion
```

执行转录：
```bash
python main.py --url "用户提供的链接"
```

### Step 3: 监控处理过程

脚本会自动输出处理进度：
1. Step 1/5: 下载视频
2. Step 2/5: 提取音频  
3. Step 3/5: 上传到OSS
4. Step 4/5: 云端转录
5. Step 5/5: 保存到Notion

### Step 4: 检查结果

处理完成后，检查以下内容：
- ✅ 本地视频文件：`output/downloads/video_xxx.mp4`
- ✅ 本地转录文本：`output/transcripts/transcript_xxx.txt`
- ✅ Notion页面是否创建成功
- ✅ 领域和分类是否正确

### Step 5: 生成报告

向用户输出完整报告（详见输出示例）。

## 分类建议策略

根据视频内容自动建议领域和分类：

### 领域建议关键词

| 关键词 | 建议领域 |
|--------|----------|
| AI、人工智能、算法、技术、人类、思维、情感、哲学、意识 | 人类大逻辑 |
| 商业、资本、经济、投资、融资、创业、管理 | 商业大逻辑 |
| 国际、关系、政治、地缘、外交、战争、军事 | 国际关系... |
| 历史、文化、社会、教育、心理 | 人类大逻辑 |
| 科技、互联网、数字经济 | 商业大逻辑 |

### 分类建议关键词

| 关键词 | 建议分类 |
|--------|----------|
| 理论、逻辑、模型、框架、分析工具、方法论 | 逻辑&理论&模型库 |
| 观点、讨论、热点、事件分析、个人见解 | 话题资料库 |
| 案例、实例、具体事件 | 话题资料库 |
| 概念、定义、原理 | 逻辑&理论&模型库 |

## 费用说明

### 阿里云Paraformer
- 价格: 0.008元/分钟
- 限制: 单次最大4小时音频
- 费用查看：https://billing-cost.console.aliyun.com/home

### 阿里云OSS
- 上传: 免费
- 存储: 0.09元/GB/月（临时存储几分钟，费用可忽略）
- 数据网站：https://oss.console.aliyun.com/oss-console2/light/bucket-list?view=card

### Notion API
- 免费额度: 足够个人使用
- 限制: 每秒3次请求

## 许可证

MIT License
