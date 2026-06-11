---
name: disk-cleaner
description: "磁盘空间分析引导清理工具。基于 WizTree 导出 CSV 做纯数据驱动分析，AI 不得自行扫描硬盘。支持任意盘符（C/D/E 等），内置 safe/caution/danger/migrate 四级规则和 Junction 迁移回滚机制。使用场景：『磁盘满了』『清理C盘』『空间不足』『C盘变红』『迁移大文件到D盘』。安全第一：每一步都问用户、不动系统目录、Onedrive 占位文件视为谣言。"
---

## 工作流总览

```
用户触发
  ↓
Step 1 ─ 问用户要分析哪个盘（C:/D:/E: 等），以及 WizTree 路径（未安装则询问）
  ↓
Step 2 ─ 运行 Invoke-CdiskScan.ps1 扫描指定盘 → 导出 3 个 CSV（文件清单、文件夹清单、文件类型分布）
  ↓
Step 3 ─ AI **只读取 CSV 做分析**（不得 Get-ChildItem / 自行搜硬盘）
          → 对照 cleanup-rules.md 逐项分类 safe / caution / danger / migrate
          → 注意 OneDrive 等云同步目录的文件可能是"幽灵占位"（仅云端存在），不实际占用空间
  ↓
Step 4 ─ 向用户展示分析结果：
          ✅ 可安全清理项（带预计释放空间）
          🟣 可迁移项（Junction 到其他盘）
          🟡 需用户确认项（Downloads、Desktop 等）
          🔴 禁止项（隐藏注明原因）
  ↓
Step 5 ─ 用户逐项选择 → 只操作用户确认的路径
  ↓
Step 6 ─ 执行清理（Invoke-CdiskClean.ps1）和/或迁移（Invoke-CdiskMigrate.ps1）
  ↓
Step 7 ─ 清理残留：删除 WizTree 导出的 CSV 文件、临时文件
  ↓
完成
```

**关键约束：AI 不得自主决定任何事情。每一步都必须问用户。**

---

## Step 1：询问用户 → 准备扫描

先问用户：
1. **要分析哪个盘？**（C: / D: / E: 等，不要假设是 C 盘）
2. **WizTree 安装在哪儿？**（如果没安装，问用户是否要安装，不要自行下载）

然后调用扫描脚本。

---

## Step 2：运行扫描脚本

```powershell
# 不需要管理员权限，非管理员模式也能扫描
powershell -ExecutionPolicy Bypass -File "<skill_dir>\scripts\Invoke-CdiskScan.ps1" -TargetDrive "C:"
```

脚本会：
1. 按用户指定的 WizTree 路径查找；找不到则报错返回，**AI 再问用户**
2. 扫描指定盘符，导出 3 个 CSV 到 `$env:TEMP\CdiskCleaner\`
3. 打印 CSV 路径，AI 读取分析

---

## Step 3：AI 分析 CSV（只读 CSV，不扫硬盘）

### 3.1 读取 CSV

读取以下三个文件（路径由扫描脚本打印到控制台）：

| CSV | 用途 |
|-----|------|
| `Cdisk_FolderList_*.csv` | 树形目录 + 大小 + 文件/文件夹数 |
| `Cdisk_FileList_*.csv` | 每个文件的路径 + 大小 + 修改日期 |
| `Cdisk_FileTypes_*.csv` | 按扩展名汇总大小 + 数量 + 占比 |

### 3.2 空间分析方法

**所有分析只基于 CSV 内容，不得用 PowerShell 的 Get-ChildItem 或其他命令扫硬盘。**

分析步骤：
1. 从 `FolderList` 提取指定盘符根目录→二级目录→三级目录的大小
2. 定位 top-N 大目录（>1 GB 的重点关注）
3. 对每个大目录，对照 `references/cleanup-rules.md` 做分级
4. 从 `FileTypes` 看哪些文件类型占比高（如 .mp4/.mov 视频文件、.rar/.zip 压缩包、.dll 系统文件等）
5. 如果有 OneDrive 目录，**提示用户**：OneDrive 文件可能只是云端占位符（在线文件），实际不占用本地空间。不要仅凭 Size 字段判断，建议在文件资源管理器右键 OneDrive → 属性确认实际占用。

### 3.3 分级规则（同 cleanup-rules.md）

| 安全等级 | 含义 | 示例 |
|----------|------|------|
| 🟢 **safe** | 安全删除 | Temp、Cache、Prefetch、日志、回收站 |
| 🟡 **caution** | 需问用户 | Downloads、Desktop、Windows.old、hiberfil.sys |
| 🔴 **danger** | 禁止操作 | System32、Program Files、WinSxS、Windows\Installer |
| 🟣 **migrate** | 可迁移 | 微信/QQ 数据、开发缓存（.npm/.gradle）、通用缓存 |

---

## Step 4：展示给用户

输出示例：

```
📊 D 盘空间概览
  总空间: 500 GB | 已用: 350 GB | 可用: 150 GB (30%)
  扫描自: Cdisk_FolderList_20250611_122438.csv

🧹 可安全清理（请确认是否执行）:
  ✅ D:\Windows\Temp                              → 约 3.2 GB
  ✅ D:\Users\xxx\AppData\Local\JianyingPro\Cache  → 约 4.5 GB
  预计释放: ~7.7 GB

📦 可迁移到其他盘（Junction）:
  🟣 D:\Users\xxx\.npm                              → 1.5 GB → 建议迁到 E:\.npm
  🟣 D:\Users\xxx\AppData\Local\Tabbit              → 2.2 GB → 建议迁到 E:\Tabbit

⚠️ 需要你确认:
  🟡 D:\Users\xxx\Downloads                        → 12.0 GB → 哪些文件还要？

ℹ️ 注意:
  🌀 D:\Users\xxx\OneDrive                         → 看起来 356 GB，但可能多数是云端占位符，实际占用请右键属性确认
```

**展示完后，逐项问用户：**
- "这个路径 XXX（XX GB）要清理吗？"
- "这个路径 XXX（XX GB）要迁移到哪个盘？"
- 不得跳过用户确认直接执行

---

## Step 5：用户确认

用户确认后，按用户选择执行：

### 5.1 清理操作

```powershell
# JSON 格式传入要清理的路径（由 AI 根据用户选择生成）
powershell -ExecutionPolicy Bypass -File "<skill_dir>\scripts\Invoke-CdiskClean.ps1" -CleanupJson "C:\Temp\cleanup_list.json"
```

JSON 格式：
```json
[
    {"path": "D:\\Windows\\Temp\\*", "reason": "系统临时文件", "safety": "safe"},
    {"path": "D:\\Users\\xxx\\AppData\\Local\\Temp\\*", "reason": "用户临时文件", "safety": "safe"}
]
```

### 5.2 迁移操作（每次只迁移一个目录）

```powershell
# 每次只迁移一个目录，迁移前会问用户目标盘符
powershell -ExecutionPolicy Bypass -File "<skill_dir>\scripts\Invoke-CdiskMigrate.ps1" -SourcePath "D:\Users\xxx\.npm" -DestinationRoot "E:"
```

迁移脚本 7 阶段安全保证：
1. 前置安检（禁止列表、权限、空间）
2. robocopy 复制（/COPYALL /B /XJ）
3. 校验副本
4. 重命名源为备份
5. 创建 Junction
6. 验证 Junction 双向读写
7. 生成回滚脚本到桌面

---

## Step 6：清理残留

所有操作完成后：
1. 询问用户是否删除 WizTree 导出的 CSV 文件（`$env:TEMP\CdiskCleaner\` 下）
2. 询问用户是否删除迁移脚本生成的临时文件
3. 删除后告知用户已清理

---

## Step 7：验证结果

询问用户是否要重新扫描同一盘符来验证清理效果。如果要，回到 Step 2。

---

## 安全准则（严格遵守）

1. **AI 分析只读 CSV，绝不自己扫描硬盘** — 一切数据来源只有 WizTree 导出的 CSV
2. **每一步都问用户** — 找不到 WizTree 要问、要删哪个目录要问、要迁到哪个盘要问
3. **OneDrive 文件可能是假的** — 云同步占位符显示大小但实际不在本地，必须提示用户确认
4. **永不动以下路径**：`System32`, `WinSxS`, `Program Files`, `ProgramData`, `System Volume Information`, `Windows\Installer`, `AppData\Local\Microsoft`, `AppData\Local\Packages`
5. **迁移前先关目标软件**
6. **不要一次性迁移多个目录** — 逐个迁移逐个验证
7. **回滚脚本不要删** — 建议保留至少 1 个月
8. **清理完成后删除所有临时 CSV 和日志文件**

---

## 注意事项

### OneDrive / 云同步目录的特殊处理

OneDrive 支持"文件按需同步"：文件显示在文件资源管理器中、有图标、有大小，但实际可能不在本地。WizTree 扫描时这些文件会显示大小为 0（或同步状态的缓存大小），**但有些云盘客户端可能将占位符报告为实际大小**。

处理方式：
- 在展示给用户时，对 OneDrive 目录加注 🌀 标记
- 建议用户在文件资源管理器中右键 OneDrive 目录 → 属性，查看"占用空间"确认
- **不要建议用户删除 OneDrive 文件**，只提"启用按需同步"选项

### 关于改名

本技能原名 `cdisk-cleaner`（仅 C 盘），但实际支持任意盘符。技能目录名暂不更改（不影响功能），内部名称已改为 `disk-cleaner`，代码中通过 `-TargetDrive` 参数指定盘符。

---

## 文件速查

| 文件 | 用途 |
|------|------|
| `SKILL.md` | 本文件 — AI 工作流入口 |
| `scripts/Invoke-CdiskScan.ps1` | 扫描 + 导出 CSV |
| `scripts/Invoke-CdiskClean.ps1` | 安全清理 |
| `scripts/Invoke-CdiskMigrate.ps1` | Junction 迁移 |
| `references/cleanup-rules.md` | 规则知识库 |
