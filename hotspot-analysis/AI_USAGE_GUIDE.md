# AI 使用指南

## 🚨 核心原则

**禁止创建任何新的 Python 文件！**

本 skill 已经包含所有必要的功能脚本，AI 助手在使用时必须：
1. 只使用 skill 目录中已有的脚本
2. 不在用户输出目录创建新脚本
3. 不复制或修改现有脚本
4. 不创建任何临时 Python 文件

## 📁 Skill 目录结构

```
C:\Users\26084\.stepfun\skills\hotspot-analysis\
├── SKILL.md                              # 主文档
├── AI_USAGE_GUIDE.md                     # 本文件
├── scripts/                              # 所有可用脚本
│   ├── fetch_hotlist.py                  # 基础版采集
│   ├── fetch_hotlist_enhanced.py         # 增强版采集 ⭐
│   ├── analyze_content.py                # 基础版分析
│   ├── analyze_content_enhanced.py       # 增强版分析 ⭐
│   └── batch_process.py                  # 批量处理 ⭐⭐⭐
└── output/                               # 输出目录（自动创建）
```

## 🎯 标准执行流程

### 场景 1：用户要求获取热点数据（推荐）

**最佳方案：使用批量处理脚本**

```powershell
Set-Location "C:\Users\26084\.stepfun\skills\hotspot-analysis"; python scripts/batch_process.py
```

这会自动完成：
- 采集所有平台数据
- 分析所有平台数据
- 生成对比报告
- 保存到 output/ 目录

### 场景 2：用户只要求采集数据

```powershell
Set-Location "C:\Users\26084\.stepfun\skills\hotspot-analysis"; python scripts/fetch_hotlist_enhanced.py
```

### 场景 3：用户只要求分析已有数据

```powershell
Set-Location "C:\Users\26084\.stepfun\skills\hotspot-analysis"; python scripts/analyze_content_enhanced.py output/douyin_hotlist_20260210.json
```

## 🔧 执行命令模板

### Windows PowerShell

```powershell
# 推荐方式：使用分号分隔命令
Set-Location "C:\Users\26084\.stepfun\skills\hotspot-analysis"; python scripts/batch_process.py

# 或者分两步执行
Set-Location "C:\Users\26084\.stepfun\skills\hotspot-analysis"
python scripts/batch_process.py
```

**注意：** Windows PowerShell 不支持 `&&` 操作符，必须使用分号 `;` 或分两步执行。

### 处理用户交互

某些脚本需要用户输入（如选择平台），可以使用以下方式：

```powershell
# 方式1：让脚本自动处理（推荐批量处理脚本）
Set-Location "C:\Users\26084\.stepfun\skills\hotspot-analysis"; python scripts/batch_process.py

# 方式2：如果需要交互，提前告知用户
# "脚本会提示您选择平台，请根据提示输入数字"
Set-Location "C:\Users\26084\.stepfun\skills\hotspot-analysis"; python scripts/fetch_hotlist_enhanced.py
```

## 📊 输出处理

### 默认行为
- 脚本会在控制台输出分析结果
- 如果用户要求保存，文件会保存到 `output/` 目录
- AI 应该读取控制台输出并总结给用户

### 文件输出位置
所有输出文件都在：
```
C:\Users\26084\.stepfun\skills\hotspot-analysis\output\
```

### 输出文件命名规则
- 采集数据：`{platform}_hotlist_{date}.json`
- 分析报告：`{platform}_analysis_{date}.json`

## ❌ 错误示例（禁止）

### 错误 1：创建新脚本
```python
# ❌ 错误：在用户目录创建新脚本
Write("C:\\Users\\26084\\OneDrive\\文档\\Output-xiaoyue\\fetch_data.py", "...")
```

### 错误 2：复制代码到新文件
```python
# ❌ 错误：复制 skill 代码到新位置
Write("C:\\Users\\26084\\OneDrive\\文档\\Output-xiaoyue\\hotspot_tool.py", 
      "import requests\n...")
```

### 错误 3：使用相对路径
```bash
# ❌ 错误：假设当前在某个目录
python scripts/batch_process.py
```

## ✅ 正确示例

### 正确 1：直接使用 skill 脚本
```powershell
Set-Location "C:\Users\26084\.stepfun\skills\hotspot-analysis"; python scripts/batch_process.py
```

### 正确 2：使用绝对路径
```powershell
python "C:\Users\26084\.stepfun\skills\hotspot-analysis\scripts\batch_process.py"
```

### 正确 3：先切换目录再执行
```powershell
Set-Location "C:\Users\26084\.stepfun\skills\hotspot-analysis"
python scripts/batch_process.py
```

## 🎨 用户沟通模板

### 开始任务时
```
我将使用 hotspot-analysis skill 为您获取热点数据。
这个 skill 会自动采集抖音、B站等平台的热榜，并进行多维度分析。

正在执行...
```

### 执行完成后
```
✓ 热点数据采集和分析完成！

【分析结果摘要】
- 平台：抖音、B站、小红书
- 数据量：共 150 条热榜数据
- 热门话题：娱乐 (35%)、科技 (28%)、生活 (20%)...
- 高频关键词：AI、春节、电影...

详细报告已保存到：
C:\Users\26084\.stepfun\skills\hotspot-analysis\output\
```

## 🔍 故障排查

### 问题：脚本执行失败

**检查清单：**
1. 是否使用了正确的绝对路径？
2. 是否切换到了 skill 目录？
3. 是否安装了必要的依赖（requests, numpy）？
4. 网络连接是否正常？

**解决方案：**
```powershell
# 1. 确保在正确的目录
Set-Location "C:\Users\26084\.stepfun\skills\hotspot-analysis"

# 2. 检查 Python 环境
python --version

# 3. 安装依赖（如果需要）
pip install requests numpy

# 4. 重新执行
python scripts/batch_process.py
```

### 问题：找不到输出文件

**检查位置：**
```
C:\Users\26084\.stepfun\skills\hotspot-analysis\output\
```

如果目录不存在，脚本会自动创建。

## 📝 总结

**记住三个原则：**
1. **只用现有脚本** - 不创建新文件
2. **使用绝对路径** - 避免路径错误
3. **推荐批量处理** - 一键完成所有操作

**最常用的命令：**
```powershell
Set-Location "C:\Users\26084\.stepfun\skills\hotspot-analysis"; python scripts/batch_process.py
```

这一条命令就能完成大部分用户需求！
