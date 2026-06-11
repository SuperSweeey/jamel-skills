<#
.SYNOPSIS
    安全地将 C 盘大目录迁移到其他盘，用 NTFS Junction 保持应用无感。
.DESCRIPTION
    7 阶段安全迁移算法:
      0. 前置安检（禁止列表、权限、空间）
      1. robocopy 完整复制
      2. 副本校验
      3. 重命名源目录（备份）
      4. 创建 Junction 联接点
      5. 验证联接点双向读写
      6. 生成独立回滚脚本（桌面）
      7. 清理备份（需用户确认）
.PARAMETER SourcePath
    要迁移的 C 盘完整路径，如 "C:\Users\xxx\Documents\WeChat Files"
.PARAMETER TargetRoot
    目标盘的根目录，如 "D:\" 或 "E:\Data"，默认 D:\
.PARAMETER Move
    若指定，迁移验证通过后自动删除 C 盘备份（不询问）
.PARAMETER Force
    跳过用户确认提示
.PARAMETER WhatIf
    仅预览，不执行任何修改
.EXAMPLE
    .\Invoke-CdiskMigrate.ps1 -SourcePath "C:\Users\alice\Documents\WeChat Files"
.EXAMPLE
    .\Invoke-CdiskMigrate.ps1 -SourcePath "C:\Users\alice\AppData\Local\Google\Chrome\User Data\Default\Cache" -TargetRoot "D:\" -Move
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateScript({ Test-Path $_ }, ErrorMessage = "源路径不存在")]
    [string]$SourcePath,

    [Parameter(Position = 1)]
    [ValidateScript({ Test-Path $_ }, ErrorMessage = "目标根目录不存在")]
    [string]$TargetRoot = "D:\",

    [switch]$Move,
    [switch]$Force,
    [switch]$WhatIf
)

#region --- 全局变量 ---
$script:ErrorActionPreference = "Stop"
$script:LogFile = "$env:TEMP\CdiskCleaner_Migrate_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$script:BackupSuffix = "_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
$script:RollbackScriptPath = "$env:USERPROFILE\Desktop\Rollback_$(Split-Path $SourcePath -Leaf)_$(Get-Date -Format 'yyyyMMdd_HHmmss').ps1"
$script:ManifestPath = "$env:TEMP\CdiskCleaner_Manifest_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$script:MigrationSuccessful = $false

# 硬编码禁止迁移路径
$script:Blocklist = @(
    "$env:WINDIR",
    "$env:WINDIR\System32",
    "$env:WINDIR\System32\*",
    "$env:PROGRAMFILES",
    "$env:PROGRAMFILES\*",
    "${env:ProgramFiles(x86)}",
    "${env:ProgramFiles(x86)}\*",
    "$env:ProgramData",
    "$env:ProgramData\*",
    "$env:SYSTEMDRIVE\System Volume Information",
    "$env:SYSTEMDRIVE\`$Recycle.Bin",
    "$env:SYSTEMDRIVE\Windows.old",
    "$env:SYSTEMDRIVE\Windows.old\*",
    "$env:SYSTEMDRIVE\Users",
    "$env:SYSTEMDRIVE\Users\Default",
    "$env:SYSTEMDRIVE\Users\Public",
    "$env:SYSTEMDRIVE\Users\All Users"
)

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp][$Level] $Message"
    Add-Content -Path $script:LogFile -Value $line
    if ($Level -eq "ERROR") { Write-Host $line -ForegroundColor Red }
    elseif ($Level -eq "WARN") { Write-Host $line -ForegroundColor Yellow }
    elseif ($Level -eq "OK") { Write-Host $line -ForegroundColor Green }
    else { Write-Host $line }
}

function Exit-WithError {
    param([string]$Message)
    Write-Log -Message $Message -Level "ERROR"
    Write-Host "`n❌ 迁移失败，详情见日志: $($script:LogFile)" -ForegroundColor Red
    if (-not $script:MigrationSuccessful) {
        Write-Host "ℹ️  源目录数据未丢失，仍然在原始位置。" -ForegroundColor Cyan
    }
    exit 1
}

function Test-IsJunction {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $false }
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    return ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq [System.IO.FileAttributes]::ReparsePoint
}

function Test-OnBlocklist {
    param([string]$Path)
    $normalized = $Path.TrimEnd('\').ToLower()
    foreach ($blocked in $script:Blocklist) {
        $blockedNorm = $blocked.TrimEnd('\').ToLower()
        if ($blockedNorm.EndsWith('*')) {
            $prefix = $blockedNorm.TrimEnd('*')
            if ($normalized.StartsWith($prefix)) { return $true }
        }
        else {
            if ($normalized -eq $blockedNorm) { return $true }
        }
    }
    return $false
}

function Get-DirectorySize {
    param([string]$Path)
    $result = robocopy "$Path" "$env:TEMP\__null__" /L /E /R:0 /W:0 /NP /NJH /NJS /NDL /NC /NS /BYTES 2>$null
    $totalSize = 0
    $fileCount = 0
    foreach ($line in $result) {
        if ($line -match '^\s*(\d+)\s+(\d+)') {
            $fileCount += [int]$Matches[2]
        }
    }
    $totalSize = (Get-ChildItem -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum).Sum
    return [PSCustomObject]@{ Bytes = [long]$totalSize; Files = $fileCount }
}
#endregion

Write-Log "==================== CdiskCleaner 迁移脚本启动 ===================="
Write-Log "源路径: $SourcePath"
Write-Log "目标根: $TargetRoot"

# === Phase -2: 前置安全检查 ===

# 1. 管理员权限
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Exit-WithError "必须用管理员身份运行 PowerShell"
}
Write-Log "[PASS] 管理员权限" -Level "OK"

# 2. 源路径标准化
$SourcePath = (Resolve-Path $SourcePath).Path.TrimEnd('\')
Write-Log "标准化源路径: $SourcePath"

# 3. 检查禁止列表
if (Test-OnBlocklist -Path $SourcePath) {
    Exit-WithError "路径 '$SourcePath' 在禁止迁移列表中，不可迁移！"
}
Write-Log "[PASS] 不在禁止列表" -Level "OK"

# 4. 检查是否为 Junction
if (Test-IsJunction -Path $SourcePath) {
    $target = (Get-Item -LiteralPath $SourcePath -Force).Target
    Exit-WithError "源路径已是 Junction 联接点，指向: $target。无需重复迁移。"
}
Write-Log "[PASS] 不是已有联接点" -Level "OK"

# 5. 空目录检查
$srcItem = Get-Item -LiteralPath $SourcePath -Force
if (-not $srcItem.PSIsContainer) {
    Exit-WithError "源路径不是目录"
}
if ((Get-ChildItem -LiteralPath $SourcePath -Force).Count -eq 0) {
    Exit-WithError "源目录为空，无需迁移"
}

# 6. 目标路径构建
$folderName = Split-Path $SourcePath -Leaf
$TargetPath = "$TargetRoot\$folderName".TrimEnd('\')
Write-Log "目标路径: $TargetPath"

# 7. 目标路径是否已存在
if (Test-Path $TargetPath) {
    if ($Force) {
        Write-Log "目标路径已存在（Force 模式），跳过" -Level "WARN"
    }
    else {
        Exit-WithError "目标路径已存在: $TargetPath，请先移除或换个名字"
    }
}

# 8. 源大小估算 + 目标盘空间检查
Write-Log "正在计算源目录大小..." -Level "INFO"
$srcSize = Get-DirectorySize -Path $SourcePath
$srcSizeGB = [math]::Round($srcSize.Bytes / 1GB, 2)
Write-Log "源目录: $srcSizeGB GB, $($srcSize.Files) 个文件" -Level "OK"

$targetDrive = (Get-Item $TargetRoot).PSDrive.Name + ":"
$targetFree = (Get-PSDrive -Name (Get-Item $TargetRoot).PSDrive.Name).Free
$targetFreeGB = [math]::Round($targetFree / 1GB, 2)
$neededGB = [math]::Round($srcSize.Bytes * 1.3 / 1GB, 2)

if ($targetFree -lt ($srcSize.Bytes * 1.3)) {
    Exit-WithError "目标盘 $targetDrive 剩余空间 $targetFreeGB GB，需要 $neededGB GB，空间不足"
}
Write-Log "[PASS] 目标盘空间: $targetFreeGB GB，需要: $neededGB GB" -Level "OK"

# 9. 用户确认
if (-not $Force -and -not $WhatIf) {
    Write-Host "`n========== 迁移摘要 ==========" -ForegroundColor Cyan
    Write-Host "源:  $SourcePath  ($srcSizeGB GB)" -ForegroundColor White
    Write-Host "目标: $TargetPath" -ForegroundColor White
    Write-Host "日志: $($script:LogFile)" -ForegroundColor White
    Write-Host "===============================`n" -ForegroundColor Cyan
    $answer = Read-Host "确认要迁移以上目录吗？(y/n)"
    if ($answer -notmatch '^[yY]') {
        Write-Log "用户取消迁移" -Level "WARN"
        exit 0
    }
}

if ($WhatIf) {
    Write-Host "`n[WhatIf] 源: $SourcePath" -ForegroundColor Cyan
    Write-Host "[WhatIf] 目标: $TargetPath" -ForegroundColor Cyan
    Write-Host "[WhatIf] 大小: $srcSizeGB GB, $($srcSize.Files) 文件" -ForegroundColor Cyan
    Write-Host "[WhatIf] 将执行 7 阶段安全迁移算法" -ForegroundColor Cyan
    exit 0
}

# === Phase 1: robocopy 复制 ===
Write-Log "--- Phase 1: robocopy 复制 ---"

$robocopyArgs = @(
    "`"$SourcePath`"", "`"$TargetPath`"",
    "/E", "/COPYALL", "/DCOPY:T", "/B",
    "/R:3", "/W:5", "/XJ", "/NP",
    "/LOG+:`"$($script:LogFile)`""
)

Write-Log "执行: robocopy $($robocopyArgs -join ' ')" -Level "INFO"

$robocopyResult = Start-Process -FilePath "robocopy.exe" -ArgumentList $robocopyArgs -Wait -PassThru -NoNewWindow
$robocopyExitCode = $robocopyResult.ExitCode

if ($robocopyExitCode -ge 8) {
    Exit-WithError "robocopy 复制失败 (exit code: $robocopyExitCode)"
}
Write-Log "[PASS] robocopy 复制完成 (exit code: $robocopyExitCode)" -Level "OK"

# === Phase 2: 校验副本完整性 ===
Write-Log "--- Phase 2: 完整性校验 ---"

$targetSize = Get-DirectorySize -Path $TargetPath
$sizeDiff = [math]::Abs($targetSize.Bytes - $srcSize.Bytes)
$sizeDiffGB = [math]::Round($sizeDiff / 1GB, 3)
$sizeDiffRatio = if ($srcSize.Bytes -gt 0) { $sizeDiff / $srcSize.Bytes } else { 0 }

Write-Log "源: $($srcSize.Files) 文件, $($srcSize.Bytes) bytes"
Write-Log "目标: $($targetSize.Files) 文件, $($targetSize.Bytes) bytes"

if ($sizeDiffRatio -gt 0.05) {
    # 差异大于 5%，回滚
    Write-Log "校验不一致: 差异 $sizeDiffRatio" -Level "WARN"
    Write-Host "文件校验不一致，正在回滚..." -ForegroundColor Yellow
    Remove-Item -LiteralPath $TargetPath -Recurse -Force -ErrorAction SilentlyContinue
    Exit-WithError "副本校验失败（差异 $sizeDiffGB GB, $([math]::Round($sizeDiffRatio*100,1))%），已回滚"
}
elseif ($sizeDiffRatio -gt 0.01) {
    Write-Log "校验存在微小差异 ($([math]::Round($sizeDiffRatio*100,1))%)，可能因运行中文件变化，继续" -Level "WARN"
}
else {
    Write-Log "[PASS] 副本一致性校验通过" -Level "OK"
}

# === Phase 3: 备份源目录（重命名）===
Write-Log "--- Phase 3: 源目录重命名备份 ---"

$backupPath = "$SourcePath$script:BackupSuffix"
try {
    Rename-Item -LiteralPath $SourcePath -NewName (Split-Path $backupPath -Leaf) -Force
    Write-Log "[PASS] 源目录已重命名为: $backupPath" -Level "OK"
}
catch {
    # 重命名失败，可能是文件被占用
    Write-Log "重命名失败: $_" -Level "WARN"
    Write-Host "源目录中可能有文件正被占用，请关闭以下应用后重试:" -ForegroundColor Yellow
    $lockingApps = @()
    $srcBase = Split-Path $SourcePath -Leaf
    if ($srcBase -match "WeChat|Tencent|QQ") { $lockingApps += "微信/QQ" }
    if ($srcBase -match "Chrome|Edge|Firefox") { $lockingApps += "浏览器" }
    if ($lockingApps.Count -gt 0) {
        Write-Host "  → " -NoNewline; Write-Host ($lockingApps -join ", ") -ForegroundColor Cyan
    }
    # 清理目标
    Remove-Item -LiteralPath $TargetPath -Recurse -Force -ErrorAction SilentlyContinue
    Exit-WithError "无法重命名源目录，迁移中止"
}

# === Phase 4: 创建 Junction ===
Write-Log "--- Phase 4: 创建 Junction ---"

try {
    $null = New-Item -ItemType Junction -Path $SourcePath -Target $TargetPath -Force
    Write-Log "[PASS] Junction 已创建: $SourcePath → $TargetPath" -Level "OK"
}
catch {
    Write-Log "创建 Junction 失败: $_" -Level "WARN"
    Write-Host "正在回滚..." -ForegroundColor Yellow
    # 回滚: 恢复备份
    Remove-Item -LiteralPath $SourcePath -Force -ErrorAction SilentlyContinue  # 删除可能部分创建的 junction
    Rename-Item -LiteralPath $backupPath -NewName (Split-Path $SourcePath -Leaf) -Force
    # 清理目标
    Remove-Item -LiteralPath $TargetPath -Recurse -Force -ErrorAction SilentlyContinue
    Exit-WithError "Junction 创建失败，已回滚"
}

# === Phase 5: 验证 Junction ===
Write-Log "--- Phase 5: 验证 Junction ---"

try {
    $junctionItem = Get-Item -LiteralPath $SourcePath -Force
    if (-not ($junctionItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        throw "Junction 属性丢失"
    }
    Write-Log "[PASS] Junction 属性正常" -Level "OK"

    $junctionTarget = $junctionItem.Target
    if ($junctionTarget.TrimEnd('\') -ne $TargetPath.TrimEnd('\')) {
        throw "Junction 目标不匹配: $junctionTarget ≠ $TargetPath"
    }
    Write-Log "[PASS] Junction 目标匹配" -Level "OK"

    $testFiles = Get-ChildItem -LiteralPath $SourcePath -Force -ErrorAction Stop
    Write-Log "[PASS] 通过 Junction 可读取文件列表 ($($testFiles.Count) 项)" -Level "OK"

    $testFilePath = "$SourcePath\__cdisk_verify__.tmp"
    "verify" | Out-File -FilePath $testFilePath -Encoding ASCII -Force
    if (-not (Test-Path $testFilePath)) { throw "无法通过 Junction 创建文件" }
    $realTestFile = "$TargetPath\__cdisk_verify__.tmp"
    if (-not (Test-Path $realTestFile)) { throw "文件未出现在真实目标路径" }
    Remove-Item -LiteralPath $testFilePath -Force
    Remove-Item -LiteralPath $realTestFile -Force -ErrorAction SilentlyContinue
    Write-Log "[PASS] Junction 双向读写验证通过" -Level "OK"
}
catch {
    Write-Log "Junction 验证失败: $_" -Level "WARN"
    Write-Host "正在回滚..." -ForegroundColor Yellow
    Remove-Item -LiteralPath $SourcePath -Force -ErrorAction SilentlyContinue
    Rename-Item -LiteralPath $backupPath -NewName (Split-Path $SourcePath -Leaf) -Force
    Remove-Item -LiteralPath $TargetPath -Recurse -Force -ErrorAction SilentlyContinue
    Exit-WithError "Junction 验证失败，已回滚"
}

$script:MigrationSuccessful = $true

# === Phase 6: 生成独立回滚脚本 ===
Write-Log "--- Phase 6: 生成回滚脚本 ---"

$rollbackContent = @"
<#
.SYNOPSIS
    回滚脚本 — 由 CdiskCleaner 迁移工具自动生成
    创建时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    原始源路径: $SourcePath (当前为 Junction)
    备份路径: $backupPath
    真实目标: $TargetPath
#>

Write-Host "=== 回滚操作 ===" -ForegroundColor Yellow

# 1. 验证备份目录存在
if (-not (Test-Path "$backupPath")) {
    Write-Host "[ERROR] 备份目录不存在: $backupPath" -ForegroundColor Red
    Write-Host "无法回滚，请手动检查。" -ForegroundColor Red
    exit 1
}

# 2. 删除 Junction（不会影响目标盘数据）
if (Test-Path "$SourcePath") {
    $item = Get-Item -LiteralPath "$SourcePath" -Force
    if (`$item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        Remove-Item -LiteralPath "$SourcePath" -Force
        Write-Host "[OK] Junction 已删除" -ForegroundColor Green
    }
}

# 3. 恢复备份
Rename-Item -LiteralPath "$backupPath" -NewName "$(Split-Path $SourcePath -Leaf)" -Force
Write-Host "[OK] 备份已恢复" -ForegroundColor Green

# 4. 验证
if (Test-Path "$SourcePath") {
    Write-Host "[OK] 回滚完成，源路径已恢复" -ForegroundColor Green
}
else {
    Write-Host "[ERROR] 回滚后源路径不可用，请手动恢复: $backupPath → $SourcePath" -ForegroundColor Red
}

# 注意：目标盘的数据不会被删除，可手动确认后删除: $TargetPath
"@

try {
    $rollbackContent | Out-File -FilePath $script:RollbackScriptPath -Encoding UTF8
    Write-Log "[PASS] 回滚脚本已生成: $($script:RollbackScriptPath)" -Level "OK"
    Write-Host "`n📄 回滚脚本已保存到桌面: $($script:RollbackScriptPath)" -ForegroundColor Cyan
}
catch {
    Write-Log "生成回滚脚本失败: $_" -Level "WARN"
}

# === Phase 7: 清理备份 ===
Write-Log "--- Phase 7: 清理备份 ---"

if ($Move) {
    # -Move 参数指定了自动清理
    try {
        Remove-Item -LiteralPath $backupPath -Recurse -Force
        Write-Log "[OK] 备份已自动删除 (Move 模式)" -Level "OK"
    }
    catch {
        Write-Log "删除备份失败: $_" -Level "WARN"
        Write-Host "⚠️  备份目录删除失败，请手动删除: $backupPath" -ForegroundColor Yellow
    }
}
elseif ($Force) {
    # Force 模式下自动跳过备份清理，留给用户决定
    Write-Log "Force 模式，跳过备份清理。备份保留: $backupPath" -Level "INFO"
}
else {
    # 交互询问
    $backupSize = Get-DirectorySize -Path $backupPath
    $backupSizeGB = [math]::Round($backupSize.Bytes / 1GB, 2)
    Write-Host "`n备份目录保留在: $backupPath ($backupSizeGB GB)" -ForegroundColor White
    $answer = Read-Host "是否删除备份以释放空间？(y/n)"
    if ($answer -match '^[yY]') {
        try {
            Remove-Item -LiteralPath $backupPath -Recurse -Force
            Write-Host "[OK] 备份已删除" -ForegroundColor Green
            Write-Log "备份已删除" -Level "OK"
        }
        catch {
            Write-Host "⚠️  删除失败，请手动删除: $backupPath" -ForegroundColor Yellow
            Write-Log "删除备份失败: $_" -Level "WARN"
        }
    }
    else {
        Write-Host "保留备份，你可稍后手动删除: $backupPath" -ForegroundColor Yellow
    }
}

# === 完成 ===
Write-Host "`n✅ 迁移成功完成！" -ForegroundColor Green
Write-Host "  源路径 (Junction): $SourcePath" -ForegroundColor Green
Write-Host "  真实数据路径: $TargetPath" -ForegroundColor Green
Write-Host "  日志: $($script:LogFile)" -ForegroundColor White
if (Test-Path $script:RollbackScriptPath) {
    Write-Host "  回滚脚本: $($script:RollbackScriptPath)" -ForegroundColor White
}
Write-Log "==================== 迁移成功完成 ===================="
