# 记忆维护服务文档

## 📋 概述

记忆维护服务是一个定时后台任务，负责自动维护Mem0中存储的所有用户记忆，包括权重衰减、层次转换和过期清理。

## 🎯 核心功能

### 1. 时间衰减
- **自动计算**：根据记忆创建时间，自动计算权重衰减
- **渐进式**：使用公式 `w(t) = w₀ / (1 + α * t)` 实现平滑衰减
- **可配置**：衰减系数α可调整（默认0.01）

### 2. 层次转换
- **智能摘要**：使用LLM将完整记忆转为摘要
- **三层架构**：
  - 完整记忆（权重 ≥ 0.7）
  - 摘要记忆（0.3 ≤ 权重 < 0.7）
  - 标签记忆（权重 < 0.3）

### 3. 过期清理
- **阈值清理**：删除权重低于阈值的记忆（默认0.05）
- **可选功能**：可配置是否启用自动删除
- **保留追溯**：可选保留原始内容用于回溯

### 4. 维护报告
- **详细统计**：记录每次维护的处理数量
- **JSON格式**：便于分析和可视化
- **历史追踪**：保留所有维护记录

## 🛠️ 部署方式

### 方式1: Docker容器（推荐）

#### 使用增强版docker-compose
```bash
# 启动包含维护服务的完整系统
docker-compose -f docker-compose-with-maintenance.yml up -d

# 查看维护服务日志
docker-compose -f docker-compose-with-maintenance.yml logs -f memory-maintenance

# 停止维护服务
docker-compose -f docker-compose-with-maintenance.yml stop memory-maintenance
```

#### 环境变量配置
在`docker-compose-with-maintenance.yml`中配置：
```yaml
environment:
  - MEM0_URL=http://mem0-api:8000
  - SCAN_INTERVAL_HOURS=24        # 扫描间隔（小时）
  - DECAY_ALPHA=0.01              # 衰减系数
  - CLEANUP_THRESHOLD=0.05        # 清理阈值
```

### 方式2: 本地运行

#### 一次性执行
```powershell
# Windows PowerShell
.\run_maintenance.ps1 once

# 或直接运行Python
cd app
python memory_maintenance.py --once
```

#### 定时服务
```powershell
# 启动定时服务
.\run_maintenance.ps1 start

# 查看日志
.\run_maintenance.ps1 logs

# 查看状态
.\run_maintenance.ps1 status

# 停止服务
.\run_maintenance.ps1 stop
```

### 方式3: 系统定时任务

#### Windows任务计划程序
1. 打开任务计划程序
2. 创建基本任务
3. 触发器：每天凌晨2点
4. 操作：启动程序
   - 程序：`powershell.exe`
   - 参数：`-File "G:\Temp\mem0-docker\run_maintenance.ps1" once`

#### Linux Cron
```bash
# 编辑crontab
crontab -e

# 添加定时任务（每天凌晨2点执行）
0 2 * * * cd /path/to/mem0-docker/app && python memory_maintenance.py --once >> /var/log/mem0_maintenance.log 2>&1
```

## ⚙️ 配置参数

### MaintenanceConfig类参数

| 参数 | 默认值 | 说明 |
|-----|--------|------|
| `mem0_url` | `http://localhost:8000` | Mem0 API地址 |
| `zhipu_api_key` | 从.env读取 | 智谱AI API密钥（用于摘要生成） |
| `decay_alpha` | `0.01` | 衰减系数（越大衰减越快） |
| `full_memory_threshold` | `0.7` | 完整记忆阈值 |
| `summary_memory_threshold` | `0.3` | 摘要记忆阈值 |
| `cleanup_threshold` | `0.05` | 清理阈值（低于此值删除） |
| `scan_interval_hours` | `24` | 扫描间隔（小时） |
| `cleanup_interval_days` | `7` | 清理间隔（天） |
| `batch_size` | `100` | 批处理大小 |

### 修改配置
编辑`app/memory_maintenance.py`中的`main()`函数：
```python
config = MaintenanceConfig(
    scan_interval_hours=12,      # 改为每12小时运行
    decay_alpha=0.02,            # 加快衰减速度
    cleanup_threshold=0.03,      # 提高清理阈值
)
```

## 📊 维护报告

### 报告位置
```
app/maintenance_reports/
├── report_20251120_020000.json
├── report_20251121_020000.json
└── report_20251122_020000.json
```

### 报告格式
```json
{
  "timestamp": "2025-11-20T02:00:00",
  "config": {
    "decay_alpha": 0.01,
    "full_threshold": 0.7,
    "summary_threshold": 0.3,
    "cleanup_threshold": 0.05
  },
  "stats": {
    "users": 4,
    "total_memories": 156,
    "updated": 12,
    "summarized": 8,
    "cleaned": 3
  },
  "cumulative": {
    "total_scanned": 1523,
    "total_updated": 89,
    "total_summarized": 45,
    "total_cleaned": 12,
    "last_run": "2025-11-20T02:00:00"
  }
}
```

### 查看报告
```powershell
# 查看最新报告
Get-Content app\maintenance_reports\report_*.json | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 1 | 
    ConvertFrom-Json | 
    ConvertTo-Json -Depth 10

# 统计分析
Get-ChildItem app\maintenance_reports -Filter "report_*.json" | 
    ForEach-Object {
        $report = Get-Content $_.FullName | ConvertFrom-Json
        [PSCustomObject]@{
            Date = $report.timestamp
            Users = $report.stats.users
            Memories = $report.stats.total_memories
            Summarized = $report.stats.summarized
            Cleaned = $report.stats.cleaned
        }
    } | Format-Table
```

## 📝 日志管理

### 日志文件
```
app/memory_maintenance.log
```

### 日志级别
- `INFO`: 正常操作日志
- `WARNING`: 警告信息（如缺少时间戳）
- `ERROR`: 错误信息（如API调用失败）
- `DEBUG`: 详细调试信息（默认不输出）

### 查看日志
```powershell
# 实时查看日志
Get-Content app\memory_maintenance.log -Wait -Tail 50

# 过滤错误日志
Select-String -Path app\memory_maintenance.log -Pattern "ERROR"

# 统计每日维护次数
Select-String -Path app\memory_maintenance.log -Pattern "开始记忆维护周期" | 
    Group-Object { ($_.Line -split ' ')[0] } | 
    Format-Table Count, Name
```

### 日志轮转
建议配置日志轮转避免文件过大：
```python
# 使用Python的RotatingFileHandler
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'memory_maintenance.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

## 🔧 高级用法

### 自定义用户列表

#### 方式1: users.txt文件
编辑`app/users.txt`：
```
user_001
user_002
user_003
```

#### 方式2: 从数据库读取
修改`get_all_users()`方法：
```python
def get_all_users(self) -> List[str]:
    # 从PostgreSQL/MySQL读取
    conn = psycopg2.connect(...)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM users")
    return [row[0] for row in cursor.fetchall()]
```

#### 方式3: 从Qdrant查询
```python
def get_all_users(self) -> List[str]:
    # 直接查询Qdrant获取所有user_id
    from qdrant_client import QdrantClient
    client = QdrantClient(host="localhost", port=6333)
    
    # 获取所有点并提取user_id
    points = client.scroll(
        collection_name="mem0_collection",
        limit=10000
    )
    
    user_ids = set()
    for point in points[0]:
        user_id = point.payload.get("user_id")
        if user_id:
            user_ids.add(user_id)
    
    return list(user_ids)
```

### 禁用自动删除
如果只想衰减权重而不删除记忆：
```python
def process_memory(self, memory: Dict[str, Any], user_id: str):
    # ...
    if current_weight < self.config.cleanup_threshold:
        logger.info(f"记忆权重过低但保留: {content}")
        # self.delete_memory(memory_id)  # 注释掉删除操作
        return {"action": "skipped", "reason": "low_weight_but_kept"}
```

### 自定义摘要策略
修改`MemorySummarizer.summarize()`方法使用不同的摘要模型或规则。

### 监控告警
```python
# 在run_maintenance_cycle()结束时添加
if total_stats["cleaned"] > 50:
    send_alert(f"警告：本次清理了{total_stats['cleaned']}条记忆")

def send_alert(message: str):
    # 发送邮件/企业微信/钉钉通知
    requests.post(
        "https://qyapi.weixin.qq.com/cgi-bin/webhook/send",
        json={"msgtype": "text", "text": {"content": message}}
    )
```

## 🐛 故障排查

### 问题1: 服务无法启动
**症状**：运行后立即退出

**排查**：
```powershell
# 查看完整错误信息
python app\memory_maintenance.py --once

# 检查API连接
curl http://localhost:8000/health

# 检查API密钥
cat app\.env | Select-String "ZHIPU_API_KEY"
```

### 问题2: 无法获取用户列表
**症状**：日志显示"未找到用户列表"

**解决**：
1. 创建`app/users.txt`文件
2. 或实现自定义的`get_all_users()`方法

### 问题3: 摘要生成失败
**症状**：日志显示"LLM摘要失败"

**排查**：
```powershell
# 测试API连接
curl -X POST https://open.bigmodel.cn/api/paas/v4/chat/completions `
  -H "Authorization: Bearer YOUR_API_KEY" `
  -H "Content-Type: application/json" `
  -d '{"model":"glm-4-flash","messages":[{"role":"user","content":"test"}]}'

# 检查API配额
# 登录智谱AI控制台查看
```

### 问题4: 记忆未更新
**症状**：权重计算正确但数据库未变化

**原因**：当前实现中`update_memory()`仅记录日志，未实际更新

**解决**：根据Mem0 API文档实现实际更新逻辑：
```python
def update_memory(self, memory_id: str, new_content: str, new_metadata: Dict):
    # 如果Mem0支持PUT/PATCH
    response = requests.put(
        f"{self.config.mem0_url}/memories/{memory_id}",
        json={"memory": new_content, "metadata": new_metadata}
    )
    return response.status_code == 200
```

## 📈 性能优化

### 批处理
默认每批处理100条记忆，可根据服务器性能调整：
```python
config = MaintenanceConfig(batch_size=200)  # 增加批大小
```

### 并发处理
使用异步并发处理多个用户：
```python
async def scan_all_users(self, users: List[str]):
    tasks = [self.scan_user_memories(user_id) for user_id in users]
    results = await asyncio.gather(*tasks)
    return results
```

### 缓存优化
缓存用户列表避免重复查询：
```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_all_users_cached(self) -> List[str]:
    return self.get_all_users()
```

## 🔐 安全建议

1. **API密钥管理**
   - 使用环境变量或密钥管理服务
   - 不要在代码中硬编码

2. **访问控制**
   - 限制维护服务对Mem0 API的访问权限
   - 使用专用API token

3. **日志脱敏**
   - 避免在日志中记录敏感内容
   - 定期清理历史日志

4. **备份策略**
   - 定期备份Qdrant数据
   - 在删除前可选创建快照

## 📚 最佳实践

1. **初次部署**
   - 先执行`--once`测试
   - 检查维护报告是否正常
   - 确认无误后启动定时服务

2. **定期检查**
   - 每周查看维护报告
   - 监控清理数量是否异常
   - 调整衰减参数以适应业务

3. **渐进式清理**
   - 初期设置较高的cleanup_threshold（如0.1）
   - 观察一段时间后逐步降低
   - 避免误删重要记忆

4. **测试环境验证**
   - 在测试环境先运行验证
   - 确认摘要质量符合预期
   - 再部署到生产环境

## 🔄 更新日志

### v1.0.0 (2025-11-20)
- ✅ 初始版本发布
- ✅ 支持时间衰减计算
- ✅ 支持LLM摘要生成
- ✅ 支持定时任务调度
- ✅ 支持维护报告生成
- ✅ 支持Docker容器部署

### 未来计划
- [ ] 支持更多LLM模型（OpenAI、Claude等）
- [ ] 图形化维护报告面板
- [ ] 记忆相关性分析
- [ ] 智能清理建议
- [ ] 用户记忆画像生成
