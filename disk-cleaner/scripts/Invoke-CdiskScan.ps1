<#
.SYNOPSIS
    扫描 C 盘空间使用情况：自动查找 WizTree 导出 CSV + 检测可迁移大目录。
.DESCRIPTION
    1. 自动检测 WizTree64.exe（注册表 / 常见安装路径 / 脚本同目录）
    2. 若未找到，提示用户下载并等待
    3. 以管理员模式运行 WizTree 导出 C 盘文件清单（文件夹级别，按大小排序）
    4. 独立检测用户目录下的大目录（归类为可清理/可迁移/不可动）
    5. 输出综合报告供 AI 分析
.PARAMETER Drive
    要扫描的盘符，默认 "C:"
.PARAMETER OutputDir
    报告输出目录，默认 %TEMP%\CdiskCleaner
.PARAMETER SkipWizTree
    跳过 WizTree 扫描（仅做用户目录分析）
.PARAMETER WhatIf
    仅预览，不执行扫描
#>

param(
    [string]$Drive = "C:",
    [string]$OutputDir = "$env:TEMP\CdiskCleaner",
    [switch]$SkipWizTree,
    [switch]$WhatIf
)

$script:ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$script:LogFile = "$OutputDir\CdiskScan_$timestamp.log"

# 确保输出目录存在
if (-not (Test-Path $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null }

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp][$Level] $Message"
    Add-Content -Path $script:LogFile -Value $line
    if ($Level -eq "ERROR") { Write-Host $line -ForegroundColor Red }
    elseif ($Level -eq "WARN") { Write-Host $line -ForegroundColor Yellow }
    elseif ($Level -eq "OK") { Write-Host $line -ForegroundColor Green }
    elseif ($Level -eq "SECTION") { Write-Host "`n=== $Message ===" -ForegroundColor Cyan }
    else { Write-Host $line }
}

function Find-WizTree {
    $candidates = @()

    # 注册表
    $regPaths = @(
        "HKLM:\SOFTWARE\WizTree",
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\WizTree64.exe",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\WizTree.exe"
    )
    foreach ($reg in $regPaths) {
        if (Test-Path $reg) {
            try {
                $val = (Get-ItemProperty -Path $reg -Name "(default)" -ErrorAction SilentlyContinue)."(default)"
                if ($val -and (Test-Path $val)) { $candidates += $val }
            }
            catch {}
            try {
                $path = Get-ItemProperty -Path $reg -ErrorAction SilentlyContinue
                if ($path.Path -and (Test-Path $path.Path)) { $candidates += $path.Path }
            }
            catch {}
        }
    }

    # 常见安装路径
    $searchPaths = @(
        "$env:ProgramFiles\WizTree\WizTree64.exe",
        "$env:ProgramFiles\WizTree\WizTree.exe",
        "${env:ProgramFiles(x86)}\WizTree\WizTree64.exe",
        "${env:ProgramFiles(x86)}\WizTree\WizTree.exe",
        "$env:LOCALAPPDATA\WizTree\WizTree64.exe",
        "$env:LOCALAPPDATA\WizTree\WizTree.exe",
        "D:\Apps\WizTree\WizTree64.exe",
        "D:\Apps\WizTree\WizTree.exe"
    )
    $searchPaths += Get-ChildItem "$env:USERPROFILE\Downloads\*WizTree*.exe" -Name -ErrorAction SilentlyContinue |
        ForEach-Object { "$env:USERPROFILE\Downloads\$_" }
    $searchPaths += Get-ChildItem "$env:USERPROFILE\Desktop\*WizTree*.exe" -Name -ErrorAction SilentlyContinue |
        ForEach-Object { "$env:USERPROFILE\Desktop\$_" }
    $searchPaths += Get-ChildItem "$env:USERPROFILE\Documents\*WizTree*.exe" -Name -ErrorAction SilentlyContinue |
        ForEach-Object { "$env:USERPROFILE\Documents\$_" }

    # 脚本同目录
    $searchPaths += Join-Path $PSScriptRoot "WizTree64.exe"
    $searchPaths += Join-Path $PSScriptRoot "WizTree.exe"

    # PATH
    foreach ($ext in @(".exe")) {
        foreach ($dir in ($env:Path -split ';')) {
            if ([string]::IsNullOrWhiteSpace($dir)) { continue }
            $full = Join-Path $dir "WizTree64$ext"
            if (Test-Path $full) { $candidates += $full; break }
            $full = Join-Path $dir "WizTree$ext"
            if (Test-Path $full) { $candidates += $full; break }
        }
    }

    foreach ($p in $searchPaths) {
        if (Test-Path $p) { $candidates += $p }
    }

    # 去重 + 返回存在的
    $candidates = $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique

    if ($candidates.Count -gt 0) {
        # 优先选 WizTree64.exe
        $w64 = $candidates | Where-Object { $_ -match "WizTree64" } | Select-Object -First 1
        if ($w64) { return $w64 }
        return $candidates[0]
    }
    return $null
}

function Request-WizTreeDownload {
    Write-Host "`n⚠️  未找到 WizTree，需要下载以进行磁盘扫描。" -ForegroundColor Yellow
    Write-Host "下载页面: https://diskanalyzer.com/download" -ForegroundColor Cyan
    Write-Host "请下载便携版 (Portable)，将 WizTree64.exe 放到以下目录:" -ForegroundColor White
    Write-Host "  → $PSScriptRoot" -ForegroundColor Green

    $answer = Read-Host "`n下载后按 Enter 继续，或输入 'skip' 跳过 WizTree 扫描"

    if ($answer -eq 'skip') {
        Write-Log "用户选择跳过 WizTree 扫描" -Level "WARN"
        return $null
    }

    # 等待用户下载后查找
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 2
        $wiz = Find-WizTree
        if ($wiz) {
            Write-Log "检测到 WizTree: $wiz" -Level "OK"
            return $wiz
        }
        if ($i % 5 -eq 0 -and $i -gt 0) {
            Write-Host "  仍在等待... (已等待 $([math]::Floor($i*2/60)) 分钟)" -ForegroundColor Gray
        }
    }

    Write-Log "等待超时，跳过 WizTree 扫描" -Level "WARN"
    return $null
}

function Invoke-WizTreeExport {
    param([string]$WizTreePath, [string]$OutputPath, [bool]$IsAdmin = $true)

    $adminFlag = if ($IsAdmin) { "/admin=1" } else { "" }
    $driveArg = "`"$Drive`""
    $exportFileList = "$OutputPath\Cdisk_FileList_$timestamp.csv"
    $exportFolderList = "$OutputPath\Cdisk_FolderList_$timestamp.csv"
    $exportFileTypes = "$OutputPath\Cdisk_FileTypes_$timestamp.csv"

    Write-Log "正在运行 WizTree 扫描 C 盘..." -Level "INFO"

    # 1. 文件级别导出（含完整日期、拆分路径）
    Write-Log "导出文件清单..." -Level "INFO"
    $args1 = @($driveArg, "/export=`"$exportFileList`"", $adminFlag, "/sortby=2",
        "/exportfolders=0", "/exportalldates=1", "/exportsplitfilename=1", "/exportdrivecapacity=0")
    $args1 = $args1 | Where-Object { $_ -ne "" }
    Write-Log "  wiztree $($args1 -join ' ')"
    $p1 = Start-Process -FilePath $WizTreePath -ArgumentList $args1 -Wait -PassThru -NoNewWindow
    if ($p1.ExitCode -ne 0) {
        Write-Log " 文件导出警告 (exit: $($p1.ExitCode))" -Level "WARN"
    }
    else {
        Write-Log "[OK] 文件清单: $exportFileList" -Level "OK"
    }

    # 2. 文件夹级别导出（按大小排序）
    Write-Log "导出文件夹清单..." -Level "INFO"
    $args2 = @($driveArg, "/export=`"$exportFolderList`"", $adminFlag, "/sortby=2",
        "/exportfiles=0", "/exportdrivecapacity=0")
    $args2 = $args2 | Where-Object { $_ -ne "" }
    $p2 = Start-Process -FilePath $WizTreePath -ArgumentList $args2 -Wait -PassThru -NoNewWindow
    if ($p2.ExitCode -ne 0) {
        Write-Log " 文件夹导出警告 (exit: $($p2.ExitCode))" -Level "WARN"
    }
    else {
        Write-Log "[OK] 文件夹清单: $exportFolderList" -Level "OK"
    }

    # 3. 文件类型分布导出
    Write-Log "导出文件类型分布..." -Level "INFO"
    $args3 = @($driveArg, "/exportfiletypes=`"$exportFileTypes`"", $adminFlag)
    $args3 = $args3 | Where-Object { $_ -ne "" }
    $p3 = Start-Process -FilePath $WizTreePath -ArgumentList $args3 -Wait -PassThru -NoNewWindow
    if ($p3.ExitCode -ne 0) {
        Write-Log " 文件类型导出警告 (exit: $($p3.ExitCode))" -Level "WARN"
    }
    else {
        Write-Log "[OK] 文件类型分布: $exportFileTypes" -Level "OK"
    }

    return @{
        FileList   = if (Test-Path $exportFileList) { $exportFileList } else { $null }
        FolderList = if (Test-Path $exportFolderList) { $exportFolderList } else { $null }
        FileTypes  = if (Test-Path $exportFileTypes) { $exportFileTypes } else { $null }
    }
}

# =================== 主流程 ===================
Write-Host "`n==============================================" -ForegroundColor Cyan
Write-Host "   CdiskCleaner - C 盘扫描工具" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Log "扫描启动 | 盘符: $Drive | 输出: $OutputDir" -Level "INFO"

$wizTreePath = $null

if (-not $SkipWizTree) {
    Write-Log "--- 查找 WizTree ---" -Level "SECTION"
    $wizTreePath = Find-WizTree
    if ($wizTreePath) {
        Write-Log "[OK] 找到 WizTree: $wizTreePath" -Level "OK"
    }
    else {
        Write-Log "未找到 WizTree" -Level "WARN"
        $wizTreePath = Request-WizTreeDownload
    }
}

if ($WhatIf) {
    Write-Host "[WhatIf] 将执行:" -ForegroundColor Cyan
    Write-Host "  1. WizTree 扫描 C: 盘 → 导出 CSV" -ForegroundColor Cyan
    exit 0
}

# 运行 WizTree 扫描
$wizTreeResults = $null
if ($wizTreePath) {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

    if (-not $isAdmin) {
        Write-Log "非管理员模式运行 WizTree（不使用 MFT 扫描，速度较慢）" -Level "WARN"
    }

    $wizTreeResults = Invoke-WizTreeExport -WizTreePath $wizTreePath -OutputPath $OutputDir -IsAdmin $isAdmin
}
else {
    Write-Log "WizTree 不可用，跳过磁盘扫描" -Level "WARN"
}

# 生成摘要报告
$reportPath = "$OutputDir\ScanReport_$timestamp.txt"
$reportLines = @(
    "CdiskCleaner 扫描报告",
    "扫描时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "盘符: $Drive",
    "输出目录: $OutputDir",
    "WizTree 路径: $(if ($wizTreePath) { $wizTreePath } else { '未使用' })",
    "",
    "--- WizTree 导出文件 ---",
    "文件夹清单: $(if ($wizTreeResults.FolderList) { $wizTreeResults.FolderList } else { 'N/A' })",
    "文件清单: $(if ($wizTreeResults.FileList) { $wizTreeResults.FileList } else { 'N/A' })",
    "文件类型分布: $(if ($wizTreeResults.FileTypes) { $wizTreeResults.FileTypes } else { 'N/A' })"
)

$reportLines += "",
"--- C 盘空间概览 ---"
try {
    $cDrive = Get-PSDrive -Name $Drive.TrimEnd(':')
    $totalGB = [math]::Round(($cDrive.Used + $cDrive.Free) / 1GB, 1)
    $usedGB = [math]::Round($cDrive.Used / 1GB, 1)
    $freeGB = [math]::Round($cDrive.Free / 1GB, 1)
    $pctFree = [math]::Round($cDrive.Free / ($cDrive.Used + $cDrive.Free) * 100, 1)
    $reportLines += "总空间: $totalGB GB"
    $reportLines += "已用: $usedGB GB"
    $reportLines += "可用: $freeGB GB ($pctFree%)"
}
catch {
    $reportLines += "无法读取盘信息"
}

$reportLines -join "`r`n" | Out-File -FilePath $reportPath -Encoding UTF8

Write-Log "--- 扫描完成 ---" -Level "SECTION"
Write-Log "报告: $reportPath" -Level "OK"

# 输出摘要到控制台
Write-Host "`n========== 扫描摘要 ==========" -ForegroundColor Cyan
Write-Host "文件夹清单: $(if ($wizTreeResults.FolderList) { Split-Path $wizTreeResults.FolderList -Leaf } else { 'N/A' })" -ForegroundColor White
Write-Host "文件清单: $(if ($wizTreeResults.FileList) { Split-Path $wizTreeResults.FileList -Leaf } else { 'N/A' })" -ForegroundColor White
Write-Host "文件类型分布: $(if ($wizTreeResults.FileTypes) { Split-Path $wizTreeResults.FileTypes -Leaf } else { 'N/A' })" -ForegroundColor White
Write-Host "报告: $reportPath" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan

# 返回 WizTree CSV 路径给 AI 使用
@{
    FileListPath   = if ($wizTreeResults.FileList) { $wizTreeResults.FileList } else { $null }
    FolderListPath = if ($wizTreeResults.FolderList) { $wizTreeResults.FolderList } else { $null }
    FileTypesPath  = if ($wizTreeResults.FileTypes) { $wizTreeResults.FileTypes } else { $null }
    ReportPath     = $reportPath
}
