#!/usr/bin/env pwsh
<#
.SYNOPSIS
    记忆维护服务模拟测试启动脚本

.DESCRIPTION
    提供多种测试场景的快速启动

.EXAMPLE
    .\run_simulation.ps1 -Scenario quick
    快速测试（10秒周期，5次循环）

.EXAMPLE
    .\run_simulation.ps1 -Scenario lightning
    闪电测试（5秒周期，1秒=1天）

.EXAMPLE
    .\run_simulation.ps1 -Custom -ScanInterval 15 -DecayAlpha 1.0 -MaxCycles 20
    自定义参数测试
#>

param(
    [Parameter(HelpMessage = "预设场景: quick(快速), lightning(闪电), minute(分钟级), custom(自定义)")]
    [ValidateSet("quick", "lightning", "minute", "custom")]
    [string]$Scenario = "quick",
    
    [Parameter(HelpMessage = "自定义：扫描间隔（秒）")]
    [int]$ScanInterval = 10,
    
    [Parameter(HelpMessage = "自定义：衰减系数")]
    [double]$DecayAlpha = 0.5,
    
    [Parameter(HelpMessage = "自定义：最大周期数")]
    [int]$MaxCycles = 10,
    
    [Parameter(HelpMessage = "自定义：时间加速倍数")]
    [double]$TimeScale = 1.0,
    
    [Parameter(HelpMessage = "自定义：时间单位")]
    [ValidateSet("second", "minute")]
    [string]$TimeUnit = "second",
    
    [Parameter(HelpMessage = "创建测试记忆数量")]
    [int]$CreateMemories = 5,
    
    [Parameter(HelpMessage = "清空历史记忆")]
    [switch]$Clean,
    
    [Parameter(HelpMessage = "用户ID")]
    [string]$UserId = "test_user_sim"
)

# 颜色输出
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

# 打印横幅
function Show-Banner {
    Write-Host ""
    Write-ColorOutput "================================================================================" "Cyan"
    Write-ColorOutput "           🧠 记忆维护服务模拟测试" "Yellow"
    Write-ColorOutput "           Memory Maintenance Simulation Test" "Yellow"
    Write-ColorOutput "================================================================================" "Cyan"
    Write-Host ""
}

Show-Banner

# 场景配置
$scenarios = @{
    "quick"     = @{
        Name           = "快速测试"
        Description    = "10秒扫描周期，适合快速验证"
        ScanInterval   = 10
        DecayAlpha     = 0.5
        MaxCycles      = 5
        TimeScale      = 1.0
        TimeUnit       = "second"
        CreateMemories = 5
    }
    "lightning" = @{
        Name           = "闪电测试"
        Description    = "5秒扫描周期，1秒=1天，极速衰减"
        ScanInterval   = 5
        DecayAlpha     = 2.0
        MaxCycles      = 12
        TimeScale      = 1.0
        TimeUnit       = "second"
        CreateMemories = 5
    }
    "minute"    = @{
        Name           = "分钟级测试"
        Description    = "30秒扫描周期，1分钟=10天"
        ScanInterval   = 30
        DecayAlpha     = 1.0
        MaxCycles      = 10
        TimeScale      = 10.0
        TimeUnit       = "minute"
        CreateMemories = 5
    }
    "custom"    = @{
        Name           = "自定义测试"
        Description    = "使用自定义参数"
        ScanInterval   = $ScanInterval
        DecayAlpha     = $DecayAlpha
        MaxCycles      = $MaxCycles
        TimeScale      = $TimeScale
        TimeUnit       = $TimeUnit
        CreateMemories = $CreateMemories
    }
}

# 获取场景配置
$config = $scenarios[$Scenario]

# 显示配置
Write-ColorOutput "📋 测试场景: $($config.Name)" "Green"
Write-ColorOutput "   $($config.Description)" "Gray"
Write-Host ""
Write-ColorOutput "⚙️  配置参数:" "Cyan"
Write-Host "   用户ID:        $UserId"
Write-Host "   扫描间隔:      $($config.ScanInterval) 秒"
Write-Host "   衰减系数:      α = $($config.DecayAlpha)"
Write-Host "   最大周期:      $($config.MaxCycles) 次"
Write-Host "   时间单位:      $($config.TimeUnit)"
Write-Host "   时间加速:      1$($config.TimeUnit) = $($config.TimeScale) 天"
Write-Host "   创建记忆:      $($config.CreateMemories) 条"
if ($Clean) {
    Write-Host "   清空历史:      是" -ForegroundColor Yellow
}
Write-Host ""

# 检查Python
Write-ColorOutput "🔍 检查环境..." "Cyan"
try {
    $pythonVersion = python --version 2>&1
    Write-ColorOutput "   ✓ Python: $pythonVersion" "Green"
}
catch {
    Write-ColorOutput "   ✗ Python未安装" "Red"
    exit 1
}

# 检查Mem0服务
Write-ColorOutput "   检查Mem0服务..." "Gray"
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-ColorOutput "   ✓ Mem0服务正常运行" "Green"
    }
}
catch {
    Write-ColorOutput "   ✗ Mem0服务未运行，请先启动服务" "Red"
    Write-Host ""
    Write-ColorOutput "   提示: 运行 docker-compose up -d" "Yellow"
    exit 1
}

Write-Host ""

# 构建Python命令参数
$pythonArgs = @(
    "tests\test_maintenance_simulation.py",
    "--user-id", $UserId,
    "--time-unit", $config.TimeUnit,
    "--time-scale", $config.TimeScale,
    "--scan-interval", $config.ScanInterval,
    "--decay-alpha", $config.DecayAlpha,
    "--max-cycles", $config.MaxCycles
)

if ($config.CreateMemories -gt 0) {
    $pythonArgs += "--create-memories", $config.CreateMemories
}

if ($Clean) {
    $pythonArgs += "--clean"
}

# 显示预期效果
Write-ColorOutput "📊 预期效果:" "Cyan"
Write-Host ""

$totalSeconds = $config.ScanInterval * $config.MaxCycles
if ($config.TimeUnit -eq "second") {
    $simulatedDays = $totalSeconds * $config.TimeScale
}
else {
    $simulatedDays = ($totalSeconds / 60) * $config.TimeScale
}

Write-Host "   测试总时长:    约 $totalSeconds 秒 ($([math]::Round($totalSeconds/60, 1)) 分钟)"
Write-Host "   模拟天数:      约 $([math]::Round($simulatedDays, 1)) 天"
Write-Host ""
Write-Host "   权重衰减公式:  w(t) = 1.0 / (1 + $($config.DecayAlpha) × t)"
Write-Host ""
Write-ColorOutput "   层次转换阈值:" "Gray"
Write-Host "     > 0.7        ✓ 完整记忆 (full)"
Write-Host "     0.3 ~ 0.7    📝 摘要记忆 (summary)"
Write-Host "     0.1 ~ 0.3    🏷️  标签记忆 (tag)"
Write-Host "     0.03 ~ 0.1   👣 痕迹记忆 (trace)"
Write-Host "     ≤ 0.03       📦 存档记忆 (archive)"
Write-Host ""

# 计算预期层次转换时间
function Get-DecayTime {
    param([double]$TargetWeight, [double]$Alpha)
    return (1.0 - $TargetWeight) / ($Alpha * $TargetWeight)
}

Write-ColorOutput "   预期层次转换时间（模拟天数）:" "Gray"
$t1 = Get-DecayTime -TargetWeight 0.7 -Alpha $config.DecayAlpha
$t2 = Get-DecayTime -TargetWeight 0.3 -Alpha $config.DecayAlpha
$t3 = Get-DecayTime -TargetWeight 0.1 -Alpha $config.DecayAlpha
$t4 = Get-DecayTime -TargetWeight 0.03 -Alpha $config.DecayAlpha

Write-Host "     完整 → 摘要:  $([math]::Round($t1, 2)) 天"
Write-Host "     摘要 → 标签:  $([math]::Round($t2, 2)) 天"
Write-Host "     标签 → 痕迹:  $([math]::Round($t3, 2)) 天"
Write-Host "     痕迹 → 存档:  $([math]::Round($t4, 2)) 天"
Write-Host ""

# 确认启动
Write-ColorOutput "🚀 准备启动测试..." "Yellow"
Write-Host ""
Write-Host "按任意键开始，Ctrl+C 取消..." -NoNewline
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Write-Host ""
Write-Host ""

# 运行测试
Write-ColorOutput "="*80 "Cyan"
Write-ColorOutput "开始执行测试" "Green"
Write-ColorOutput "="*80 "Cyan"
Write-Host ""

try {
    & python @pythonArgs
}
catch {
    Write-ColorOutput "测试执行出错: $_" "Red"
    exit 1
}

Write-Host ""
Write-ColorOutput "="*80 "Cyan"
Write-ColorOutput "✅ 测试完成" "Green"
Write-ColorOutput "="*80 "Cyan"
Write-Host ""

# 提供后续操作提示
Write-ColorOutput "📝 后续操作:" "Cyan"
Write-Host "   查看日志:      Get-Content maintenance_simulation.log -Tail 50"
Write-Host "   清空记忆:      .\run_simulation.ps1 -Scenario quick -Clean"
Write-Host "   自定义测试:    .\run_simulation.ps1 -Scenario custom -ScanInterval 20 -DecayAlpha 1.0"
Write-Host ""
