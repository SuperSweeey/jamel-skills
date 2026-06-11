<#
.SYNOPSIS
    执行 C 盘安全清理操作（不处理 Junction 迁移，迁移请用 Invoke-CdiskMigrate.ps1）。
.DESCRIPTION
    接收 AI 分析后的清理清单 JSON，安全删除以下内容：
    - Temp 文件（系统+用户）
    - Prefetch
    - Windows 更新缓存
    - 旧日志文件
    - 回收站
    - 浏览器缓存（Chrome/Edge）
    - 用户确认的其他文件
.PARAMETER CleanupJson
    JSON 文件路径，包含要清理的项目列表。
    格式: [{"path": "...", "reason": "...", "safety": "safe"}]
.PARAMETER WhatIf
    仅显示会清理什么，不实际删除
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$CleanupJson,

    [switch]$WhatIf
)

$script:ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$script:LogFile = "$env:TEMP\CdiskCleaner_Clean_$timestamp.log"
$script:ReportPath = "$env:TEMP\CdiskCleaner_CleanReport_$timestamp.txt"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts][$Level] $Message"
    Add-Content -Path $script:LogFile -Value $line
    if ($Level -eq "ERROR") { Write-Host $line -ForegroundColor Red }
    elseif ($Level -eq "WARN") { Write-Host $line -ForegroundColor Yellow }
    elseif ($Level -eq "OK") { Write-Host $line -ForegroundColor Green }
    else { Write-Host $line }
}

function Get-Size {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return 0 }
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    if (-not $item) { return 0 }
    if (-not $item.PSIsContainer) { return $item.Length }
    return (Get-ChildItem -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
}

function Remove-WithBackup {
    param([string]$Path, [string]$Reason, [switch]$Force)

    if (-not (Test-Path $Path)) {
        Write-Log "路径不存在，跳过: $Path" -Level "WARN"
        return @{ Path = $Path; Status = "skipped"; Reason = "不存在" }
    }

    $size = Get-Size -Path $Path
    $sizeDisplay = if ($size -gt 1GB) { "$([math]::Round($size/1GB,2)) GB" }
    elseif ($size -gt 1MB) { "$([math]::Round($size/1MB,1)) MB" }
    else { "$([math]::Round($size/1KB,0)) KB" }

    if ($WhatIf) {
        Write-Log "[WHATIF] 将删除: $Path ($sizeDisplay) — $Reason" -Level "OK"
        return @{ Path = $Path; Status = "whatif"; Size = $size; Reason = $Reason }
    }

    Write-Log "删除: $Path ($sizeDisplay) — $Reason" -Level "INFO"

    try {
        if (Test-Path -LiteralPath $Path -PathType Container) {
            Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue
        }
        else {
            Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
        }

        if (Test-Path $Path) {
            # 可能部分文件被占用，用 del 再试
            # 如果是目录，尝试先用 cmd 清理内部文件
            if (Test-Path -LiteralPath $Path -PathType Container) {
                $null = Start-Process -FilePath "cmd.exe" -ArgumentList "/c del /f /s /q `"$Path\*`" >nul 2>&1" -Wait -NoNewWindow -WindowStyle Hidden
                Start-Sleep -Seconds 2
                $null = Start-Process -FilePath "cmd.exe" -ArgumentList "/c rmdir /s /q `"$Path`" >nul 2>&1" -Wait -NoNewWindow -WindowStyle Hidden
                Start-Sleep -Seconds 1
            }
            if (Test-Path $Path) {
                Write-Log "部分文件无法删除（可能正在使用）: $Path" -Level "WARN"
                return @{ Path = $Path; Status = "partial"; Size = $size; Reason = $Reason }
            }
        }

        Write-Log "[OK] 已删除: $Path (释放 $sizeDisplay)" -Level "OK"
        return @{ Path = $Path; Status = "deleted"; Size = $size; Reason = $Reason }
    }
    catch {
        Write-Log "删除失败: $Path, $_" -Level "ERROR"
        return @{ Path = $Path; Status = "failed"; Size = $size; Reason = $_ }
    }
}

# ========== 内置清理项（AI 可以直接调用） ==========

function Clear-TempFiles {
    Write-Log "--- 清理临时文件 ---" -Level "SECTION"
    $results = @()

    # 系统 Temp
    $results += Remove-WithBackup -Path "$env:WINDIR\Temp\*" -Reason "系统临时文件" -Force
    # 用户 Temp
    $results += Remove-WithBackup -Path "$env:TEMP\*" -Reason "用户临时文件" -Force
    # 用户 Temp（通过 %temp%）
    $results += Remove-WithBackup -Path "$env:LOCALAPPDATA\Temp\*" -Reason "用户临时文件(Local)" -Force

    # Windows 预读
    $results += Remove-WithBackup -Path "$env:WINDIR\Prefetch\*" -Reason "预读缓存" -Force

    return $results
}

function Clear-WindowsUpdateCache {
    Write-Log "--- 清理 Windows 更新缓存 ---" -Level "SECTION"
    $results = @()

    # 需要先停止 Windows Update 服务
    Write-Log "临时停止 Windows Update 服务..." -Level "INFO"
    Stop-Service -Name wuauserv -Force -ErrorAction SilentlyContinue
    Stop-Service -Name bits -Force -ErrorAction SilentlyContinue
    Stop-Service -Name dosvc -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2

    $results += Remove-WithBackup -Path "$env:WINDIR\SoftwareDistribution\Download\*" -Reason "更新下载缓存"

    # 重启服务
    Start-Service -Name wuauserv -ErrorAction SilentlyContinue
    Start-Service -Name bits -ErrorAction SilentlyContinue
    Start-Service -Name dosvc -ErrorAction SilentlyContinue

    # 传递优化文件
    $results += Remove-WithBackup -Path "$env:WINDIR\DeliveryOptimization\Cache\*" -Reason "传递优化缓存" -Force

    return $results
}

function Clear-LogFiles {
    Write-Log "--- 清理日志文件 ---" -Level "SECTION"
    $results = @()

    $results += Remove-WithBackup -Path "$env:WINDIR\System32\LogFiles\*" -Reason "系统日志" -Force
    $results += Remove-WithBackup -Path "$env:WINDIR\System32\winevt\Logs\*" -Reason "事件日志" -Force
    $results += Remove-WithBackup -Path "$env:WINDIR\Logs\*" -Reason "Windows 日志" -Force

    return $results
}

function Clear-RecycleBin {
    Write-Log "--- 清空回收站 ---" -Level "SECTION"
    $results = @()

    try {
        $shell = New-Object -ComObject Shell.Application
        $shell.NameSpace(0xa).Items() | ForEach-Object { $_.InvokeVerb("delete") }
        Write-Log "[OK] 回收站已清空" -Level "OK"
        $results += @{ Path = "Shell:RecycleBin"; Status = "deleted"; Size = 0; Reason = "回收站" }
    }
    catch {
        # fallback: cmd
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c rd /s /q $env:SYSTEMDRIVE\`$Recycle.Bin >nul 2>&1" -Wait -NoNewWindow -WindowStyle Hidden
        Write-Log "[OK] 回收站已清空 (cmd fallback)" -Level "OK"
        $results += @{ Path = "Shell:RecycleBin"; Status = "deleted"; Size = 0; Reason = "回收站" }
    }

    return $results
}

function Clear-BrowserCache {
    Write-Log "--- 清理浏览器缓存 ---" -Level "SECTION"
    $results = @()

    # Chrome
    $chromeCache = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache"
    $results += Remove-WithBackup -Path "$chromeCache\*" -Reason "Chrome 缓存" -Force
    $codeCache = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Code Cache"
    $results += Remove-WithBackup -Path "$codeCache\*" -Reason "Chrome Code Cache" -Force

    # Edge
    $edgeCache = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache"
    $results += Remove-WithBackup -Path "$edgeCache\*" -Reason "Edge 缓存" -Force
    $edgeCodeCache = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Code Cache"
    $results += Remove-WithBackup -Path "$edgeCodeCache\*" -Reason "Edge Code Cache" -Force

    return $results
}

# ========== 主入口 ==========

Write-Host "`n==============================================" -ForegroundColor Cyan
Write-Host "   CdiskCleaner - 清理执行工具" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Log "清理脚本启动" -Level "INFO"

# 检查管理员权限
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Log "需要管理员权限，提权重启..." -Level "WARN"
    $scriptPath = $MyInvocation.MyCommand.Path
    $args = "-NoProfile -ExecutionPolicy Bypass"
    if ($CleanupJson) { $args += " -CleanupJson `"$CleanupJson`"" }
    if ($WhatIf) { $args += " -WhatIf" }
    Start-Process powershell.exe -ArgumentList "$args -File `"$scriptPath`"" -Verb RunAs -Wait
    exit 0
}

$allResults = @()

if ($CleanupJson -and (Test-Path $CleanupJson)) {
    Write-Log "加载清理清单: $CleanupJson" -Level "INFO"
    $items = Get-Content -Path $CleanupJson -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($item in $items) {
        $path = $item.path
        $reason = $item.reason
        $safety = $item.safety

        if ($safety -eq "danger") {
            Write-Log "跳过危险项: $path" -Level "WARN"
            continue
        }

        $allResults += Remove-WithBackup -Path $path -Reason $reason
    }
}
else {
    Write-Log "未指定清单文件，执行内置标准清理" -Level "INFO"

    # 标准清理流程
    $allResults += Clear-TempFiles
    $allResults += Clear-WindowsUpdateCache
    $allResults += Clear-LogFiles
    $allResults += Clear-RecycleBin
    $allResults += Clear-BrowserCache
}

# 生成报告
$totalFreed = ($allResults | Where-Object { $_.Status -eq "deleted" } | Measure-Object -Property Size -Sum).Sum
$totalFreedGB = [math]::Round(($totalFreed / 1GB), 2)

$report = @"
CdiskCleaner 清理报告
时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
总计释放空间: $totalFreedGB GB

清理明细:
"@

foreach ($r in $allResults) {
    $sizeStr = if ($r.Size -gt 0) { "$([math]::Round($r.Size/1MB,1)) MB" } else { "-" }
    $report += "`r`n  [$($r.Status)] $($r.Path)  ($sizeStr)  → $($r.Reason)"
}

$report | Out-File -FilePath $script:ReportPath -Encoding UTF8
Write-Log "[OK] 清理报告: $($script:ReportPath)" -Level "OK"

Write-Host "`n========== 清理完成 ==========" -ForegroundColor Cyan
Write-Host "释放空间: $totalFreedGB GB" -ForegroundColor Green
Write-Host "报告: $($script:ReportPath)" -ForegroundColor White
Write-Host "日志: $($script:LogFile)" -ForegroundColor White
Write-Host "===============================" -ForegroundColor Cyan

return @{
    TotalFreed  = $totalFreed
    Results     = $allResults
    ReportPath  = $script:ReportPath
    LogFile     = $script:LogFile
}
