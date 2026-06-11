DiskCleaner Skill
磁盘安全清理助手

一句话定位：把 WizTree 导出的磁盘占用结果，变成可确认、可执行、可回滚的清理与迁移建议。

SAFE SCAN · SMART CLEANUP · JUNCTION MIGRATION

这是一个面向 Windows 磁盘清理场景的 Codex / ChatGPT Skill，用来处理“C 盘爆红、空间不足、想清理但不敢乱动”的问题。它先依赖 WizTree 做真实扫描，再让 AI 只读 CSV 做分析，最后把安全清理、谨慎确认和 Junction 迁移串成一条完整流程。

它不是一个让 AI 直接扫硬盘、列文件树、替用户乱删目录的工具。它真正的定位是：用专业扫描软件负责真实数据，用 AI 负责解释和归类，用脚本负责执行，用用户保留最终决定权。

想看更完整的首次使用要求，请看 [初始配置要求.md](./初始配置要求.md)

适合谁使用
磁盘空间经常爆满、但不想冒风险乱删文件的人
普通清理软件只能清表层缓存、想继续往下找空间黑洞的人
想把大目录迁到其他盘、但不想破坏原路径的人

核心能力
只读 WizTree 导出的 CSV，不让 AI 自己扫盘
按 `safe / caution / danger / migrate` 四级规则输出建议
区分“该删的垃圾”和“更适合迁移的大目录”
支持 Junction 迁移，并保留校验与回滚能力

整体流程
第一次使用时，先确认 WizTree 和脚本入口，再进入清理任务。

第一步：基础检查
先确认：
WizTree 已安装，且知道可执行文件路径
PowerShell 可运行脚本
要分析的目标盘符已经明确
如果首次上手不确定边界，先看 [初始配置要求.md](./初始配置要求.md)

第二步：确认盘符和扫描入口
先问清楚两件事：
要分析哪个盘
WizTree 路径在哪里

第三步：先给出分析结果
先扫描并导出 CSV，再由 AI 只读分析，输出四类结果：
可安全清理项
需用户确认项
禁止操作项
可迁移项

第四步：执行完整链路
WIZTREE → CSV → AI ANALYSIS → USER CONFIRMATION → CLEAN OR MIGRATE

技术路线简要
本地用 WizTree 负责真实扫描
AI 只读取 CSV 做目录归因、风险分级和处理建议
脚本负责清理、迁移、校验和回滚
迁移通过 Junction 保持原路径继续可用

第五步：有问题就按阶段回看
如果失败，先判断是在：
WizTree 扫描阶段
CSV 分析阶段
清理阶段
迁移阶段
校验或回滚阶段

Operating Modes
analyze_only
只扫描和分析，不执行删除或迁移

clean_only
只执行用户确认的清理项

migrate_only
只执行用户确认的迁移项

verify_again
重新扫描同一盘符，验证处理结果

输入入口
Target Drive
例如 `C:`、`D:`、`E:`

WizTree Path
WizTree 可执行文件的本地路径

User Confirmation
逐项确认哪些要删，哪些要迁

输出去向
Local
扫描结果和执行结果保留在本机

Console Summary
向用户展示可清理项、可迁移项、谨慎项和禁止项

Rollback Material
迁移时生成回滚脚本和校验材料

为什么强
它强的不是“会删文件”，而是把高风险磁盘清理变成了一条可解释、可确认、可回滚的工作流。WizTree 负责真实数据，所以不是模型猜测；AI 负责理解结果，所以不止能看到大文件，还能继续追到真正的目录根因；Junction 迁移则让“释放空间”和“保持原工作路径”可以同时成立。

安装方式
当前仓库路径：
`disk-cleaner/`

在 Codex / ChatGPT 中调用：
请使用 `disk-cleaner` skill，先分析指定盘符，并按安全边界给出清理或迁移建议。

推荐仓库结构
disk-cleaner/
├─ README.md
├─ SKILL.md
├─ 初始配置要求.md
├─ references/
│  └─ cleanup-rules.md
├─ scripts/
│  ├─ Invoke-CdiskScan.ps1
│  ├─ Invoke-CdiskClean.ps1
│  └─ Invoke-CdiskMigrate.ps1
└─ assets/

免责声明
本 skill 只用于辅助磁盘空间分析、清理建议和目录迁移。它不能替代用户判断，也不应该绕过用户确认直接操作高风险目录。使用者应自行确认自己有权删除、迁移或处理相关文件，并在涉及系统目录、云同步目录、聊天数据、工作资料或隐私内容时自行判断风险和授权范围。
