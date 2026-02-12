# 抖音视频转录同步工具

抖音视频转录并同步到Notion的完整工作流。

## 项目结构

```
douyin-transcriber-skill/        ← Skill 根目录
├── SKILL.md                      ← Skill 定义
├── README.md                     ← 本文件
├── douyin-notion/               ← 依赖的程序
│   ├── main.py
│   ├── requirements.txt
│   ├── config.json.template
│   └── modules/
└── LICENSE
```

## 组件说明

- **SKILL.md**: Claude Skill 定义文件
- **douyin-notion/**: 核心Python程序，负责视频下载、转录、同步
- **config.json.template**: 配置模板（需要用户自行填入API密钥）

## 安装使用

参见 `SKILL.md` 中的详细说明。

## 许可证

MIT
