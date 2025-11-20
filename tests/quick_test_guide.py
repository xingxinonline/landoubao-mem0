#!/usr/bin/env python3
"""
超快速测试配置
修改衰减系数，在1-2分钟内达到存档状态
"""

# 在 app/main.py 中添加此维护触发接口

MAINTENANCE_ENDPOINT = """
# 在 app/main.py 中添加以下代码

from memory_maintenance import MemoryMaintenanceService, MaintenanceConfig

# 在 FastAPI app 初始化后添加
maintenance_service = None

@app.on_event("startup")
async def startup_event():
    global maintenance_service
    config = MaintenanceConfig(
        mem0_url="http://localhost:8000",
        test_mode=True,  # 测试模式
        decay_alpha=1.0   # 快速衰减：1分钟后权重降至0.5
    )
    maintenance_service = MemoryMaintenanceService(config)
    # 不自动启动定时任务，手动触发

@app.post("/admin/maintenance/run")
async def trigger_maintenance():
    '''手动触发维护任务'''
    if maintenance_service:
        report = await maintenance_service.run_single_maintenance()
        return {
            "status": "completed",
            "report": report,
            "timestamp": datetime.now().isoformat()
        }
    return {"status": "error", "message": "Maintenance service not initialized"}

@app.get("/admin/maintenance/config")
async def get_maintenance_config():
    '''查看维护配置'''
    if maintenance_service:
        return {
            "decay_alpha": maintenance_service.config.decay_alpha,
            "test_mode": maintenance_service.config.test_mode,
            "thresholds": {
                "full": maintenance_service.config.full_memory_threshold,
                "summary": maintenance_service.config.summary_memory_threshold,
                "tag": maintenance_service.config.tag_memory_threshold,
                "trace": maintenance_service.config.trace_memory_threshold
            }
        }
    return {"status": "error"}

# 使用方法：
# 1. 添加上述代码到 app/main.py
# 2. 重启容器: docker-compose restart
# 3. 运行测试: python test_archive_memory.py
"""

# 快速衰减配置说明
DECAY_CONFIGS = {
    "标准": {
        "alpha": 0.01,
        "说明": "生产环境，30天后权重约0.77",
        "到存档时间": "约100天"
    },
    "加速": {
        "alpha": 0.1,
        "说明": "测试环境，1天后权重约0.91",
        "到存档时间": "约10天"
    },
    "快速": {
        "alpha": 1.0,
        "说明": "快速测试，1小时后权重约0.5",
        "到存档时间": "约1天"
    },
    "超快": {
        "alpha": 10.0,
        "说明": "极速测试，6分钟后权重约0.5",
        "到存档时间": "约2小时"
    },
    "闪电": {
        "alpha": 100.0,
        "说明": "闪电测试，36秒后权重约0.5",
        "到存档时间": "约12分钟"
    }
}

print("=" * 70)
print("  快速测试配置指南")
print("=" * 70)
print()
print("公式: w(t) = 1 / (1 + alpha × t)")
print("存档阈值: 0.03")
print()
print("推荐配置:")
print()

for name, config in DECAY_CONFIGS.items():
    print(f"{name}模式 (alpha={config['alpha']}):")
    print(f"  {config['说明']}")
    print(f"  到达存档状态: {config['到存档时间']}")
    print()

print("-" * 70)
print("使用步骤:")
print()
print("方式1: 修改配置文件（推荐）")
print("  1. 编辑 app/memory_maintenance.py")
print("  2. 找到 decay_alpha: float = 0.01")
print("  3. 改为 decay_alpha: float = 100.0  (闪电模式)")
print("  4. 重启容器: docker-compose restart")
print("  5. 运行: python test_archive_memory.py")
print()
print("方式2: 手动修改时间戳")
print("  1. 进入容器: docker exec -it mem0-docker-app-1 bash")
print("  2. 连接数据库: sqlite3 /app/mem0_data.db")
print("  3. 查看记忆: SELECT id, memory, weight, updated_at FROM memories;")
print("  4. 更新时间: UPDATE memories SET updated_at = datetime('now', '-10 days');")
print("  5. 退出: .exit")
print()
print("方式3: 等待自然衰减")
print("  使用标准配置，等待100天后自然达到存档状态")
print()
print("=" * 70)
