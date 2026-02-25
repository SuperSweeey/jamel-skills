---
name: hotspot-analysis
description: 跨平台热点数据采集与分析工具。支持从抖音、B站、小红书等平台获取热榜数据,并进行多维度内容分析(标题长度、关键词提取、热度分布、话题分类)。增强版支持自动重试、并行采集、批量处理和平台对比分析。默认仅输出结果不保存文件,除非用户明确要求保存。当用户需要:(1)获取各平台热点榜单数据,(2)分析热点内容趋势和特征,(3)生成热点分析报告,(4)追踪社交媒体热点话题,(5)对比多平台热点差异时使用。
---

# 热点分析技能

这个技能提供跨平台热点数据采集和智能分析能力,帮助用户了解当前社交媒体热点趋势。

## 🚨 AI 使用规则（必读）

**⚠️ 重要：禁止创建新的 Python 文件！**

当使用此 skill 时，AI 助手**必须遵守**以下规则：

1. **只能使用 skill 目录中已有的脚本文件**，禁止在用户输出目录或任何其他位置创建新的 Python 文件
2. **脚本位置**：所有可用脚本都在 `C:\Users\26084\.stepfun\skills\hotspot-analysis\scripts\` 目录下
3. **执行方式**：必须使用绝对路径直接执行 skill 目录中的脚本
4. **工作目录**：执行脚本时，工作目录应设置为 skill 根目录或用户输出目录（用于保存结果文件）

### 正确的执行方式示例

```powershell
# 切换到 skill 目录
Set-Location "C:\Users\26084\.stepfun\skills\hotspot-analysis"

# 执行批量处理（推荐）
python scripts/batch_process.py

# 或者单独执行采集
python scripts/fetch_hotlist_enhanced.py

# 或者单独执行分析
python scripts/analyze_content_enhanced.py output/douyin_hotlist_20260210.json
```

**注意：** Windows PowerShell 使用分号 `;` 连接命令，不支持 `&&`。

### ❌ 错误做法（禁止）

- ❌ 在用户输出目录创建新的 Python 脚本
- ❌ 复制 skill 中的代码到新文件
- ❌ 修改或重写 skill 中的脚本功能
- ❌ 创建临时脚本文件

### ✅ 正确做法

- ✅ 直接使用 skill 目录中的现有脚本
- ✅ 通过命令行参数控制脚本行为
- ✅ 将输出结果保存到用户指定目录
- ✅ 使用 Python 的 `-c` 参数执行简单的数据处理（如果必要）

## 重要说明

⚠️ **默认行为**: 采集和分析结果**仅输出显示,不保存文件**,除非用户明确要求保存。

## 数据字段映射

不同平台的API返回字段不同,已做统一处理:
- **抖音**: 标题字段为 `word`
- **B站**: 标题字段为 `show_name`
- **小红书**: 标题字段为 `title`

脚本会自动识别并提取正确的字段。

## 版本说明

- **基础版**: 提供基本的数据采集和分析功能
- **增强版**: 提供自动重试、并行处理、批量分析等高级功能

## 核心功能

### 🎯 推荐使用方式

**最简单的方式：直接使用批量处理脚本**

```powershell
# 切换到 skill 目录
Set-Location "C:\Users\26084\.stepfun\skills\hotspot-analysis"

# 一键完成采集、分析、对比
python scripts/batch_process.py
```

这会自动完成所有操作，结果保存在 `output/` 目录。

---

### 1. 热点数据采集

#### 基础版 (fetch_hotlist.py)
基本的数据采集功能,支持单平台或全平台采集。

**AI 执行方式:**
```powershell
Set-Location "C:\Users\26084\.stepfun\skills\hotspot-analysis"; python scripts/fetch_hotlist.py
```

#### 增强版 (fetch_hotlist_enhanced.py) ⭐
提供更强大和稳定的采集功能:
- ✅ **自动重试机制**: 网络失败自动重试3次,指数退避策略
- ✅ **并行采集**: 同时获取多个平台数据,速度提升3倍
- ✅ **配置文件支持**: 从`api_keys.json`加载API密钥
- ✅ **完善错误处理**: 区分网络错误、HTTP错误、数据错误
- ✅ **会话复用**: 复用TCP连接,提高效率

**AI 执行方式:**
```powershell
Set-Location "C:\Users\26084\.stepfun\skills\hotspot-analysis"; python scripts/fetch_hotlist_enhanced.py
```

**配置API密钥:**
1. 复制 `api_keys.json.example` 为 `api_keys.json`
2. 填入你的API密钥
3. 运行脚本时自动加载

### 2. 热点内容分析

#### 基础版 (analyze_content.py)
基本的数据分析功能,提供四大维度分析。

**AI 执行方式:**
```powershell
Set-Location "C:\Users\26084\.stepfun\skills\hotspot-analysis"; python scripts/analyze_content.py output/douyin_hotlist_20260210.json
```

#### 增强版 (analyze_content_enhanced.py) ⭐
提供更深入和全面的分析:
- ✅ **数据验证**: 自动验证数据完整性和格式
- ✅ **扩展统计指标**: 增加标准差、百分位数等指标
- ✅ **智能单位转换**: 自动处理"万"、"亿"等单位
- ✅ **扩展话题分类**: 8大类话题,更多关键词,准确率提升至80%
- ✅ **百分位数分析**: P10/P30/P50/P70/P90多层次分析

**AI 执行方式:**
```powershell
Set-Location "C:\Users\26084\.stepfun\skills\hotspot-analysis"; python scripts/analyze_content_enhanced.py output/douyin_hotlist_20260210.json output/douyin_analysis.json
```

### 3. 批量处理 (batch_process.py) 🚀

一键完成采集、分析、对比全流程:

**功能特性:**
- ✅ **自动化工作流**: 采集 → 分析 → 对比,一键完成
- ✅ **并行处理**: 同时处理多个平台
- ✅ **平台对比报告**: 自动生成多平台对比分析
- ✅ **统一输出**: 所有文件保存到output目录

**AI 执行方式:**
```powershell
Set-Location "C:\Users\26084\.stepfun\skills\hotspot-analysis"; python scripts/batch_process.py
```

**输出内容:**
- 各平台原始数据文件
- 各平台分析报告文件
- 控制台输出平台对比报告

**对比维度:**
- 标题长度对比
- 热度值对比
- 话题分布对比
- 高频关键词对比

## 分析维度详解

### 标题长度分析
- **基础版**: 平均值、最大/最小值、中位数、3档分布
- **增强版**: 增加标准差、5档分布(very_short/short/medium/long/very_long)

### 关键词提取
- **基础版**: Top 20关键词,基础停用词过滤
- **增强版**: 扩展停用词库,支持自定义词长,显示百分比

### 热度值分析
- **基础版**: 基本统计量、3档分布
- **增强版**: 增加标准差、百分位数(P10/P30/P50/P70/P90)、5档分布

### 话题分类
- **基础版**: 6大类(娱乐/科技/生活/游戏/社会/教育)
- **增强版**: 8大类(增加体育/财经),扩展关键词库,显示百分比

## 工作流程

### 基础流程
```
1. 运行 fetch_hotlist.py 采集数据
2. 运行 analyze_content.py 分析数据
3. 查看控制台报告和JSON文件
```

### 增强流程
```
1. 配置 api_keys.json (可选)
2. 运行 batch_process.py
3. 自动完成采集、分析、对比
4. 查看 output/ 目录下的所有结果
```

## API配置说明

详见 `references/api_guide.md`:

- **抖音**: 无需配置,直接使用
- **B站**: 无需配置,直接使用
- **小红书**: 需要API Key,支持配置文件

## 输出格式

### 数据文件
```json
{
  "platform": "平台标识",
  "platform_name": "平台名称",
  "fetch_time": "获取时间",
  "total": 数据总量,
  "data": [热榜数据列表]
}
```

### 分析报告
```json
{
  "source_data": {源数据信息},
  "analysis_time": "分析时间",
  "analysis_results": {
    "title_length": {标题长度分析},
    "keywords": [关键词列表],
    "hot_value": {热度值分析},
    "topics": {话题分类统计}
  }
}
```

## 最佳实践

### 1. 日常使用
- 使用**增强版脚本**获得更好的稳定性
- 使用**批量处理**节省时间
- 定期运行,建立历史数据库

### 2. 生产环境
- 配置定时任务自动运行
- 添加日志记录
- 设置错误通知
- 定期清理旧文件

### 3. 深度分析
- 保留历史数据进行趋势分析
- 对比不同时间段的热点变化
- 结合多个平台发现共同热点

## 技术特性

### 稳定性
- ✅ 自动重试机制(3次,指数退避)
- ✅ 多层异常处理
- ✅ 数据验证机制
- ✅ 完善的错误提示

### 性能
- ✅ 并行采集(3倍速度提升)
- ✅ 会话复用
- ✅ 批量处理

### 扩展性
- ✅ 配置化管理
- ✅ 插件化架构
- ✅ 模块化设计
- ✅ 易于添加新平台

## 故障排查

### 常见问题

**Q: 采集失败怎么办?**
A: 增强版会自动重试3次。如果仍然失败,检查网络连接和API状态。

**Q: 如何提高采集速度?**
A: 使用增强版的并行采集功能,或使用批量处理脚本。

**Q: 分析结果不准确?**
A: 使用增强版获得更准确的分析,支持更多统计指标和更大的关键词库。

**Q: 如何对比多个平台?**
A: 使用批量处理脚本,自动生成平台对比报告。

## 扩展方向

- 数据可视化(Matplotlib/Seaborn)
- 情感分析(NLP)
- 趋势预测(时间序列)
- Web可视化界面
- 实时监控预警

## 技术文档

- **API配置指南**: `references/api_guide.md`
- **技术深度解析**: `TECHNICAL_DEEP_DIVE.md`
- **使用示例**: `EXAMPLES.md`

## 注意事项

- 遵守各平台API使用规范和频率限制
- 小红书API需要付费,请根据需求选择
- 数据仅供分析研究使用,请勿用于商业目的
- 建议保存历史数据,便于长期趋势分析
