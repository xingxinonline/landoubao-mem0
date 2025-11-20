# 🎬 智能记忆管理演示指南

## 快速演示

### 方式1: 完整集成演示（推荐）

展示记忆存储、时间衰减、自动维护的完整流程：

```powershell
# 确保Mem0服务运行中
docker-compose up -d

# 运行完整演示
cd tests
uv run python test_integrated_demo.py
```

**演示内容**：
- ✅ 创建6条测试记忆
- ✅ 模拟不同时间的记忆（0天、30天、100天、200天、300天、500天前）
- ✅ 执行维护任务（自动衰减、摘要化、清理）
- ✅ 对比维护前后的记忆状态
- ✅ 测试查询功能

### 方式2: 单独运行维护服务

#### 一次性维护
```powershell
cd app
python memory_maintenance.py --once
```

#### 测试模式（每2分钟运行一次）
```powershell
cd app
python memory_maintenance.py --test
```

#### 生产模式（每24小时运行一次）
```powershell
cd app
python memory_maintenance.py
```

### 方式3: 使用管理脚本

```powershell
# 执行一次性维护
.\run_maintenance.ps1 once

# 查看维护日志
.\run_maintenance.ps1 logs

# 查看服务状态
.\run_maintenance.ps1 status
```

---

## 📊 演示效果预览

### 维护前
```
当前记忆总数: 6

1. 我叫张三，是一名AI工程师
   层次: full | 权重: 1.0 | 时间: 2025-11-20 14:30:00

2. 我特别喜欢喝咖啡，尤其是美式咖啡
   层次: full | 权重: 1.0 | 时间: 2025-10-21 14:30:00

3. 我住在北京朝阳区
   层次: full | 权重: 1.0 | 时间: 2025-08-12 14:30:00

...
```

### 维护后
```
维护后记忆总数: 5

1. 我叫张三，是一名AI工程师
   层次: full | 权重: 1.000 | 时间: 2025-11-20 14:30:00

2. 📝 [已摘要] 用户偏好咖啡类饮品
   层次: summary | 权重: 0.435 | 时间: 2025-10-21 14:30:00

3. 🏷️ [已标签化] 居住信息
   层次: tag | 权重: 0.182 | 时间: 2025-08-12 14:30:00

...

统计:
  完整记忆: 1
  摘要记忆: 2
  标签记忆: 2
```

---

## 🔧 配置说明

### 测试模式配置

编辑 `app/memory_maintenance.py`：

```python
config = MaintenanceConfig(
    scan_interval_minutes=2,    # 测试模式：每2分钟
    decay_alpha=0.1,            # 加速衰减（正常0.01）
    cleanup_threshold=0.05,     # 清理阈值
    test_mode=True,             # 启用测试模式
)
```

### 生产模式配置

```python
config = MaintenanceConfig(
    scan_interval_hours=24,     # 每24小时运行
    decay_alpha=0.01,           # 正常衰减速度
    cleanup_threshold=0.05,     # 清理阈值
    test_mode=False,            # 生产模式
)
```

---

## 📁 输出文件

### 维护日志
```
app/memory_maintenance.log
```

示例内容：
```
2025-11-20 14:35:00 - INFO - 🔧 开始记忆维护周期
2025-11-20 14:35:01 - INFO - 找到 4 个用户
2025-11-20 14:35:02 - INFO - 扫描用户: demo_user_001
2025-11-20 14:35:02 - INFO - 找到 6 条记忆
2025-11-20 14:35:03 - INFO - 记忆 abc123... | 天数: 100.5 | 权重: 1.00 → 0.50 | 层次: full → summary
2025-11-20 14:35:04 - INFO - 🔄 转换记忆层次: full → summary
2025-11-20 14:35:05 - INFO - ✓ 维护周期完成
```

### 维护报告
```
app/maintenance_reports/report_20251120_143500.json
```

示例内容：
```json
{
  "timestamp": "2025-11-20T14:35:00",
  "config": {
    "decay_alpha": 0.01,
    "full_threshold": 0.7,
    "summary_threshold": 0.3,
    "cleanup_threshold": 0.05
  },
  "stats": {
    "users": 4,
    "total_memories": 24,
    "updated": 8,
    "summarized": 5,
    "cleaned": 2
  }
}
```

---

## 🎯 测试场景

### 场景1: 快速验证（2分钟演示）

```powershell
# 1. 启动Mem0
docker-compose up -d

# 2. 创建测试记忆并立即维护
cd tests
uv run python test_integrated_demo.py
```

### 场景2: 持续观察（定时维护）

```powershell
# 终端1: 启动测试模式维护服务（每2分钟运行）
cd app
python memory_maintenance.py --test

# 终端2: 持续添加记忆
cd tests
uv run python test_smart_memory.py

# 终端3: 实时查看日志
Get-Content app\memory_maintenance.log -Wait -Tail 20
```

**观察重点**：
- 记忆权重随时间降低
- 完整记忆→摘要记忆→标签记忆
- 低权重记忆被清理

### 场景3: 真实用户场景

```powershell
# 1. 运行多轮对话（建立记忆）
cd tests
uv run python test_personal_assistant.py

# 2. 等待几分钟（或手动触发维护）
cd ..
.\run_maintenance.ps1 once

# 3. 再次对话，观察记忆召回
cd tests
uv run python test_personal_assistant.py
```

---

## 🐛 常见问题

### Q1: 维护服务无法启动

**检查清单**：
- [ ] Mem0服务是否运行：`curl http://localhost:8000/health`
- [ ] API密钥是否配置：`cat app\.env | Select-String ZHIPU_API_KEY`
- [ ] users.txt是否存在：`cat app\users.txt`

### Q2: 记忆没有被摘要化

**可能原因**：
1. 时间太短，权重未降到阈值
2. decay_alpha太小，衰减太慢
3. LLM调用失败

**解决**：
```python
# 加大衰减系数用于测试
config = MaintenanceConfig(decay_alpha=0.1)
```

### Q3: 想看到更快的效果

**方法1**：手动修改记忆时间戳（需直接操作Qdrant）

**方法2**：提高decay_alpha和降低阈值
```python
config = MaintenanceConfig(
    decay_alpha=0.5,              # 极快衰减
    full_memory_threshold=0.8,     # 更容易触发摘要
    summary_memory_threshold=0.4,  # 更容易触发标签化
)
```

---

## 📚 文档索引

- **核心策略**：[docs/SMART_MEMORY_STRATEGY.md](docs/SMART_MEMORY_STRATEGY.md)
- **维护服务**：[docs/MAINTENANCE_SERVICE.md](docs/MAINTENANCE_SERVICE.md)
- **快速开始**：[QUICK_START.md](QUICK_START.md)
- **多语言测试**：[tests/test_multilingual.py](tests/test_multilingual.py)
- **私人助理**：[tests/test_personal_assistant.py](tests/test_personal_assistant.py)

---

## 🚀 下一步

1. **运行演示**：`cd tests && uv run python test_integrated_demo.py`
2. **查看日志**：`cat app\memory_maintenance.log`
3. **查看报告**：`cat app\maintenance_reports\report_*.json`
4. **启动定时**：`python app\memory_maintenance.py --test`（测试模式）

## 💡 提示

**Docker部署非必需**：
- ✅ **推荐**：本地直接运行（方便调试和测试）
- ⚠️ **可选**：Docker部署（适合生产环境24/7运行）

**测试时**：使用 `--test` 参数，每2分钟运行一次
**生产时**：不加参数，每24小时运行一次
