# C 盘清理规则知识库

本文档供 AI 分析 WizTree CSV 扫描结果时参考，判断哪些文件/目录可安全清理或迁移。

---

## 一、安全等级说明

| 等级 | 标签 | 含义 |
|------|------|------|
| 🟢 **safe** | 可安全删除 | 删除不影响系统/软件运行，都是自动生成的临时数据 |
| 🟡 **caution** | 需确认 | 可能是个人有用数据，或删除后由软件自动重建但会有短暂影响 |
| 🔴 **danger** | 禁止操作 | 删除会导致系统崩溃、软件无法运行、数据丢失 |
| 🟣 **migrate** | 推荐迁移 | 用 Junction 方式迁移到其他盘，既保留功能又释放 C 盘 |

---

## 二、C 盘目录逐项规则

### 2.1 根目录

| 路径 | 等级 | 说明 |
|------|------|------|
| `C:\Windows` | 🔴 danger | 系统核心，不可动 |
| `C:\Windows\System32` | 🔴 danger | 系统关键组件 |
| `C:\Windows\WinSxS` | 🔴 danger | 组件存储，不可手动删除（可用 DISM 清理） |
| `C:\Windows\Temp` | 🟢 safe | 临时文件，可全删 |
| `C:\Windows\Prefetch` | 🟢 safe | 预读缓存，可全删（系统自动重建） |
| `C:\Windows\SoftwareDistribution\Download` | 🟢 safe | 更新缓存，可全删（先停 wuauserv 服务） |
| `C:\Windows\System32\LogFiles` | 🟢 safe | 系统日志，可删 |
| `C:\Windows\System32\winevt\Logs` | 🟢 safe | 事件日志，可删 |
| `C:\Windows\Logs` | 🟢 safe | Windows 日志，可删 |
| `C:\Windows\DeliveryOptimization\Cache` | 🟢 safe | 传递优化缓存，可删 |
| `C:\Windows\System32\DriverStore\FileRepository` | 🟡 caution | 驱动备份，可用 `pnputil` 清理旧版，不可直接删 |
| `C:\Windows\Installer` | 🔴 danger | MSI 安装缓存，删除会导致部分软件无法卸载/更新 |
| `C:\Windows\assembly` | 🔴 danger | .NET 全局程序集缓存，不可动 |
| `C:\Windows\Microsoft.NET` | 🔴 danger | .NET Framework，不可动 |

### 2.2 用户目录 `C:\Users\<用户名>`

| 路径 | 等级 | 说明 |
|------|------|------|
| `C:\Users\<user>\AppData\Local\Temp` | 🟢 safe | 用户临时文件，可全删（系统跳过正在使用的） |
| `C:\Users\<user>\AppData\Local\Microsoft\Windows\INetCache` | 🟢 safe | IE/Edge 缓存 |
| `C:\Users\<user>\AppData\Local\Microsoft\Windows\Explorer` | 🟢 safe | 图标缓存，可删 |
| `C:\Users\<user>\AppData\Local\Google\Chrome\User Data\Default\Cache` | 🟢 safe | Chrome 缓存 |
| `C:\Users\<user>\AppData\Local\Microsoft\Edge\User Data\Default\Cache` | 🟢 safe | Edge 缓存 |
| `C:\Users\<user>\AppData\Local\Packages` | 🔴 danger | UWP 应用数据，删除导致应用重置 |
| `C:\Users\<user>\AppData\Local\Microsoft` | 🔴 danger | 含 Outlook/Office 等核心数据，不可整体迁移 |
| `C:\Users\<user>\AppData\Roaming\Microsoft` | 🔴 danger | 同上 |
| `C:\Users\<user>\Documents\WeChat Files` | 🟣 migrate | 微信聊天文件，纯数据，推荐迁移 |
| `C:\Users\<user>\Documents\Tencent Files` | 🟣 migrate | QQ 聊天文件，纯数据，推荐迁移 |
| `C:\Users\<user>\Downloads` | 🟡 caution | 下载文件，需要用户判断哪些不要了 |
| `C:\Users\<user>\Desktop` | 🟡 caution | 桌面文件，需用户判断 |
| `C:\Users\<user>\.npm` | 🟣 migrate | npm 缓存，可迁移或清理 |
| `C:\Users\<user>\.cache` | 🟣 migrate | 通用缓存，可迁移 |
| `C:\Users\<user>\.gradle` | 🟣 migrate | Gradle 构建缓存，可迁移 |
| `C:\Users\<user>\.cargo` | 🟣 migrate | Rust/Cargo 缓存，可迁移 |
| `C:\Users\<user>\scoop` | 🟣 migrate | Scoop 包管理器，可迁移 |

### 2.3 程序目录

| 路径 | 等级 | 说明 |
|------|------|------|
| `C:\Program Files` | 🔴 danger | 64 位应用安装目录，不要手动删 |
| `C:\Program Files (x86)` | 🔴 danger | 32 位应用安装目录，不要手动删 |
| `C:\ProgramData` | 🔴 danger | 应用共享数据，不要手动删 |

### 2.4 系统特殊目录

| 路径 | 等级 | 说明 |
|------|------|------|
| `C:\System Volume Information` | 🔴 danger | 系统还原点，通过"系统保护"界面清理 |
| `C:\$Recycle.Bin` | 🟢 safe | 回收站，直接清空即可 |
| `C:\Windows.old` | 🟡 caution | 旧系统备份，确认新系统稳定后可删（用磁盘清理工具） |
| `C:\hiberfil.sys` | 🟡 caution | 休眠文件，不用休眠可关（powercfg -h off） |
| `C:\pagefile.sys` | 🔴 danger | 虚拟内存文件，可调整大小但不要删 |

---

## 三、清理规则 — 路径匹配模式

AI 分析时应优先使用以下模式匹配来分类：

```regex
# 安全删除类
Temp\\$              → safe  临时文件
Prefetch\\$          → safe  预读
Cache\\$             → safe  缓存
Log[s]?\\$           → safe  日志
SoftwareDistribution\\Download\\$  → safe  更新缓存
DeliveryOptimization\\Cache\\$     → safe  传递优化
\$Recycle\.Bin       → safe  回收站
INetCache\\$         → safe  浏览器缓存

# 可迁移类
WeChat Files\\$      → migrate 微信
Tencent Files\\$     → migrate QQ
\.[a-z]+\\(cache|npm|gradle|cargo)\\w*  → migrate 开发工具缓存
scoop\\$             → migrate 包管理

# 禁止操作类
System32\\$          → danger
WinSxS\\$            → danger
Program Files        → danger
ProgramData          → danger
System Volume        → danger
Windows\\$           → danger (根目录)
Microsoft\\$         → danger (AppData 下)
Packages\\$          → danger (UWP)
Installer\\$         → danger (MSI)
assembly\\$          → danger (.NET GAC)
```

---

## 四、缓存目录大小参考（典型值）

| 目录 | 典型大小 | 增长速率 |
|------|---------|---------|
| `C:\Windows\Temp` | 2-10 GB | 中等 |
| `C:\Users\<user>\AppData\Local\Temp` | 1-5 GB | 快 |
| `C:\Windows\Prefetch` | 100-500 MB | 慢 |
| `C:\Windows\SoftwareDistribution\Download` | 3-15 GB | 更新时爆发 |
| `C:\Users\<user>\Documents\WeChat Files` | 5-50 GB | 快（取决于使用频率） |
| `C:\Users\<user>\Documents\Tencent Files` | 3-30 GB | 快 |
| `C:\Users\<user>\AppData\Local\Google\Chrome\User Data` | 2-10 GB | 中等 |
| `C:\Windows\System32\LogFiles` | 1-5 GB | 慢 |
| `C:\Windows.old` | 10-25 GB | 仅升级时产生 |
| `C:\hiberfil.sys` | 6-20 GB | 固定（= 物理内存的 40-75%） |
| `C:\Users\<user>\.gradle` | 2-10 GB | 中等（开发） |
| `C:\Users\<user>\.npm` | 1-5 GB | 中等（开发） |

---

## 五、常见问题

### Q: 删除 Temp 文件会影响正在运行的程序吗？
不会。Windows 正在使用的文件会被锁定无法删除，跳过即可。其余都是已经不再使用的临时文件。

### Q: 微信聊天记录迁移到 D 盘后还能正常使用吗？
可以。用 Junction 方式迁移后，微信无感，读写自动重定向到 D 盘。删除 C 盘原文件前务必验证 Junction 正常工作。

### Q: 迁移 WeChat Files 到 D 盘要注意什么？
1. 迁移前**关闭微信**（如果开着，部分文件被占用无法复制）
2. 验证 Junction 正常工作后再删 C 盘备份
3. 回滚脚本保存到桌面，1 个月内不要删

### Q: 迁移目录到 D 盘会影响性能吗？
- 如果 C 盘是 SSD，D 盘是 HDD，首次加载缓存内容时会有可感知的变慢
- 如果都是 SSD，基本无感
- 浏览器缓存这种频繁读写的，不建议迁到 HDD

### Q: `Windows.old` 可以直接删吗？
建议用"磁盘清理"工具（`cleanmgr.exe`）的"清理系统文件"来删，这样保证系统认知一致。

### Q: `hiberfil.sys` 能删吗？
不能直接删文件。如果不用休眠，在管理员命令行执行 `powercfg -h off`，系统会自动删除。

### Q: 迁移后软件报错找不到路径怎么办？
立即执行桌面上的回滚脚本恢复。如果回滚脚本丢失，手动操作：
```
rmdir "C:\原路径"                    # 删除 Junction（不影响 D 盘数据）
ren "C:\原路径_backup_*" "原路径名"  # 恢复备份
```

### Q: 如何检测一个目录已经是 Junction？
PowerShell: `(Get-Item "路径").Attributes -match "ReparsePoint"`
返回 True 说明已是联接点，不应再次迁移。
