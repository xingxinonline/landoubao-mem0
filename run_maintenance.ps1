# 记忆维护服务管理脚本

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "once", "logs", "status")]
    [string]$Action = "once"
)

$ErrorActionPreference = "Stop"

function Show-Usage {
    Write-Host @"
记忆维护服务管理

用法:
  .\run_maintenance.ps1 [action]

操作:
  start   - 启动定时维护服务（后台运行）
  stop    - 停止维护服务
  once    - 执行一次性维护任务
  logs    - 查看维护日志
  status  - 查看服务状态

示例:
  .\run_maintenance.ps1 once          # 立即执行一次维护
  .\run_maintenance.ps1 start         # 启动定时服务
  .\run_maintenance.ps1 logs          # 查看日志
"@
}

function Start-MaintenanceService {
    Write-Host "🚀 启动记忆维护服务..." -ForegroundColor Green
    
    # 使用docker-compose启动（如果配置了容器服务）
    if (Test-Path "docker-compose-with-maintenance.yml") {
        docker-compose -f docker-compose-with-maintenance.yml up -d memory-maintenance
        Write-Host "✓ 维护服务已在Docker容器中启动" -ForegroundColor Green
    }
    else {
        # 本地启动
        Write-Host "启动本地维护服务..." -ForegroundColor Yellow
        Start-Process -FilePath "python" -ArgumentList "app\memory_maintenance.py" -NoNewWindow
        Write-Host "✓ 维护服务已启动" -ForegroundColor Green
    }
}

function Stop-MaintenanceService {
    Write-Host "🛑 停止记忆维护服务..." -ForegroundColor Yellow
    
    if (Test-Path "docker-compose-with-maintenance.yml") {
        docker-compose -f docker-compose-with-maintenance.yml stop memory-maintenance
        Write-Host "✓ 维护服务已停止" -ForegroundColor Green
    }
    else {
        # 停止本地进程
        Get-Process -Name python -ErrorAction SilentlyContinue | 
            Where-Object { $_.CommandLine -like "*memory_maintenance.py*" } | 
            Stop-Process -Force
        Write-Host "✓ 维护服务已停止" -ForegroundColor Green
    }
}

function Invoke-OnceMaintenace {
    Write-Host "🔧 执行一次性维护任务..." -ForegroundColor Cyan
    Write-Host ""
    
    cd app
    python memory_maintenance.py --once
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ 维护任务执行完成" -ForegroundColor Green
    }
    else {
        Write-Host ""
        Write-Host "❌ 维护任务执行失败" -ForegroundColor Red
    }
}

function Show-Logs {
    Write-Host "📄 查看维护日志..." -ForegroundColor Cyan
    Write-Host ""
    
    $logFile = "app\memory_maintenance.log"
    
    if (Test-Path $logFile) {
        Get-Content $logFile -Tail 50
    }
    else {
        Write-Host "未找到日志文件: $logFile" -ForegroundColor Yellow
    }
}

function Show-Status {
    Write-Host "📊 维护服务状态" -ForegroundColor Cyan
    Write-Host "="*60
    
    # 检查Docker容器状态
    $container = docker ps --filter "name=mem0-maintenance" --format "{{.Status}}" 2>$null
    
    if ($container) {
        Write-Host "Docker容器: 运行中" -ForegroundColor Green
        Write-Host "状态: $container"
    }
    else {
        Write-Host "Docker容器: 未运行" -ForegroundColor Yellow
    }
    
    # 检查本地进程
    $process = Get-Process -Name python -ErrorAction SilentlyContinue | 
                Where-Object { $_.CommandLine -like "*memory_maintenance.py*" }
    
    if ($process) {
        Write-Host "本地进程: 运行中" -ForegroundColor Green
        Write-Host "PID: $($process.Id)"
    }
    else {
        Write-Host "本地进程: 未运行" -ForegroundColor Yellow
    }
    
    # 显示最近的维护报告
    $reportDir = "app\maintenance_reports"
    if (Test-Path $reportDir) {
        $latestReport = Get-ChildItem $reportDir -Filter "report_*.json" | 
                        Sort-Object LastWriteTime -Descending | 
                        Select-Object -First 1
        
        if ($latestReport) {
            Write-Host ""
            Write-Host "最近的维护报告:"
            Write-Host "  文件: $($latestReport.Name)"
            Write-Host "  时间: $($latestReport.LastWriteTime)"
            
            $report = Get-Content $latestReport.FullName | ConvertFrom-Json
            Write-Host "  统计: 用户数=$($report.stats.users), 记忆数=$($report.stats.total_memories)"
        }
    }
    
    Write-Host "="*60
}

# 主逻辑
switch ($Action) {
    "start" { Start-MaintenanceService }
    "stop" { Stop-MaintenanceService }
    "once" { Invoke-OnceMaintenace }
    "logs" { Show-Logs }
    "status" { Show-Status }
    default { Show-Usage }
}
