# API配置指南

本文档提供各平台API的详细配置说明和使用注意事项。

## 抖音热榜API

### 接口信息
- **API地址**: `https://v2.xxapi.cn/api/douyinhot`
- **请求方式**: GET
- **是否需要鉴权**: 否
- **费用**: 免费

### 使用说明
抖音热榜使用第三方免费API,无需任何配置即可直接使用。

### 返回数据格式
```json
{
  "code": 200,
  "data": [
    {
      "title": "热点标题",
      "hot_value": "1234567",
      "url": "https://..."
    }
  ]
}
```

### 注意事项
- 该API为第三方服务,稳定性依赖于服务提供商
- 建议不要频繁请求,避免被限流
- 如果API失效,可搜索其他抖音热榜API替代

---

## B站热榜API

### 接口信息
- **API地址**: `https://api.bilibili.com/x/web-interface/wbi/search/square`
- **请求方式**: GET
- **是否需要鉴权**: 否(需要请求头)
- **费用**: 免费

### 必需请求头
```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com"
}
```

### 请求参数
- `limit`: 返回数量限制(可选,默认10,最大50)

### 返回数据格式
```json
{
  "code": 0,
  "data": {
    "trending": {
      "list": [
        {
          "show_name": "热搜词",
          "keyword": "关键词",
          "icon": "热度图标"
        }
      ]
    }
  }
}
```

### 注意事项
- 必须设置User-Agent和Referer,否则可能被拒绝访问
- 这是B站官方API,相对稳定
- 返回的是热搜词而非具体视频
- 热度值以图标形式返回(如"热"、"新"等)

---

## 小红书热榜API

### 接口信息
- **API地址**: `https://api.szlessthan.com/xiaohongshu/hotlist`
- **请求方式**: GET
- **是否需要鉴权**: 是(需要API Key)
- **费用**: 付费服务

### 获取API Key
1. 访问 https://api.szlessthan.com
2. 注册账号并登录
3. 在控制台创建应用
4. 获取API Key

### 请求头配置
```python
headers = {
    "Authorization": f"Bearer {api_key}"
}
```

### 返回数据格式
```json
{
  "code": 200,
  "data": [
    {
      "title": "笔记标题",
      "hot_value": "123456",
      "link": "https://..."
    }
  ]
}
```

### 费用说明
- 该API为第三方聚合服务,需要付费使用
- 不同套餐有不同的调用次数限制
- 建议根据实际需求选择合适的套餐

### 替代方案
如果不想付费,可以考虑:
1. 使用浏览器自动化工具(如Selenium)爬取小红书网页
2. 寻找其他免费的小红书API服务
3. 仅使用抖音和B站的免费API

### 注意事项
- API Key需要妥善保管,不要泄露
- 注意API调用次数限制,避免超额
- 定期检查API服务状态和更新

---

## 通用注意事项

### 请求频率控制
为避免被限流或封禁,建议:
- 在请求之间添加延迟(1-2秒)
- 不要在短时间内大量请求
- 使用缓存机制,避免重复请求

### 错误处理
脚本已包含基本错误处理:
- 网络超时(timeout=10秒)
- HTTP错误状态码检查
- JSON解析错误处理
- API返回码验证

### 数据存储
- 数据以UTF-8编码保存为JSON格式
- 文件名格式: `{platform}_hotlist.json`
- 包含平台名、获取时间、数据总量等元信息

### 法律合规
- 仅用于个人学习和研究目的
- 遵守各平台的服务条款和robots.txt
- 不要用于商业用途或大规模数据采集
- 尊重用户隐私,不采集个人敏感信息

---

## 故障排查

### 常见问题

**问题1: 请求超时**
- 检查网络连接
- 尝试增加timeout时间
- 使用代理服务器

**问题2: API返回错误**
- 检查API地址是否正确
- 验证请求头和参数
- 查看API服务商的状态页面

**问题3: 数据解析失败**
- 打印原始响应内容进行调试
- 检查API返回格式是否变化
- 更新解析逻辑以适配新格式

**问题4: 小红书API鉴权失败**
- 确认API Key是否正确
- 检查Authorization头格式
- 验证API Key是否过期或被禁用

### 调试技巧
1. 使用`print(response.text)`查看原始响应
2. 使用Postman等工具测试API
3. 查看API服务商的文档和示例代码
4. 启用详细日志记录

---

## 更新日志

### 2026-02-10
- 初始版本
- 支持抖音、B站、小红书三大平台
- 提供基础的错误处理和数据保存功能
