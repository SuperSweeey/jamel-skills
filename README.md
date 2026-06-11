# jamel-skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

我自己打造并日常使用的 Skill 仓库。

## Included Skills

- `universal-transcriber`：面向多平台视频链接的下载、转录和分发工作流
- `material-search-assistant`：按文案自动组织可剪辑素材包的工作流
- `disk-cleaner`：基于 WizTree CSV 的安全磁盘清理与 Junction 迁移 Skill

## disk-cleaner

路径：[`disk-cleaner/`](./disk-cleaner)

这个 skill 的核心原则是：

- 不让 AI 直接扫硬盘
- 只读 WizTree 导出的 CSV 做分析
- 所有删除和迁移动作都要用户确认
- 支持 Junction 迁移、校验和回滚

## License

This project is licensed under the [MIT License](./LICENSE).
