# 模拟测试使用指南

## 📋 概述

记忆维护服务模拟测试工具，使用**秒/分钟级时间周期**快速验证五层记忆架构的衰减和转换逻辑。

## 🚀 快速开始

### 1. 安装依赖

```powershell
# 进入测试目录
cd tests

# 使用uv安装依赖
uv sync
```

### 2. 配置环境变量

复制示例配置文件：

```powershell
# 如果还没有.env文件
cp ..\app\.env.example ..\app\.env
```

编辑 `app/.env` 文件，设置必需的配置：

```env
ZHIPU_API_KEY=your_api_key_here
SIM_CREATE_MEMORIES=5
```

### 3. 启动 Mem0 服务

```powershell
# 启动服务（如果还未启动）
docker-compose up -d
```

### 4. 运行模拟测试

```powershell
# 使用默认配置运行
cd tests
uv run test-simulation

# 创建5条测试记忆并运行
uv run test-simulation --create-memories 5

# 清空历史后重新测试
uv run test-simulation --clean --create-memories 5
```

## ⚙️ 配置方式

### 方式1: 环境变量（推荐）

编辑 `.env` 文件或设置环境变量：

```env
# 模拟测试配置
SIM_TIME_UNIT=second        # 时间单位
SIM_TIME_SCALE=1.0          # 时间加速倍数
SIM_SCAN_INTERVAL=10        # 扫描间隔（秒）
SIM_DECAY_ALPHA=0.5         # 衰减系数
SIM_MAX_CYCLES=10           # 最大周期数
SIM_USER_ID=test_user_sim   # 测试用户ID
```

然后运行：

```powershell
uv run test-simulation
```

### 方式2: 命令行参数

命令行参数会覆盖环境变量：

```powershell
uv run test-simulation --decay-alpha 1.0 --max-cycles 20
```

### 方式3: 临时环境变量

Windows PowerShell:

```powershell
$env:SIM_DECAY_ALPHA="2.0"; $env:SIM_MAX_CYCLES="15"; uv run test-simulation
```

Linux/macOS:

```bash
SIM_DECAY_ALPHA=2.0 SIM_MAX_CYCLES=15 uv run test-simulation
```

## 📊 预设测试场景

在 `.env` 文件中取消注释对应场景：

### 场景1: 快速验证

10秒扫描周期，适合快速功能验证。

```env
SIM_SCAN_INTERVAL=10
SIM_DECAY_ALPHA=0.5
SIM_MAX_CYCLES=5
```

**预期效果**：
- 总时长: 50秒
- 模拟天数: ~50天
- 可观察到 full → summary 转换

### 场景2: 闪电测试

5秒扫描周期，极速衰减，快速观察所有层次转换。

```env
SIM_SCAN_INTERVAL=5
SIM_DECAY_ALPHA=2.0
SIM_MAX_CYCLES=12
```

**预期效果**：
- 总时长: 60秒
- 模拟天数: ~60天
- 可观察到完整的五层转换过程

**层次转换时间**：
- full → summary: ~0.21天 (约1秒)
- summary → tag: ~1.17天 (约6秒)
- tag → trace: ~4.50天 (约23秒)
- trace → archive: ~16.17天 (约81秒)

### 场景3: 分钟级测试

30秒扫描周期，使用分钟为单位，时间加速10倍。

```env
SIM_SCAN_INTERVAL=30
SIM_TIME_UNIT=minute
SIM_TIME_SCALE=10.0
SIM_DECAY_ALPHA=1.0
SIM_MAX_CYCLES=10
```

**预期效果**：
- 总时长: 300秒 (5分钟)
- 模拟天数: ~500天
- 可观察到长期衰减效果

## 📖 命令行参数详解

```powershell
uv run test-simulation [选项]

选项:
  --user-id TEXT             测试用户ID (默认: test_user_sim)
  --create-memories INT      创建测试记忆数量 (默认: 0)
  --time-unit {second|minute}  时间单位
  --time-scale FLOAT         时间加速倍数
  --scan-interval INT        扫描间隔（秒）
  --decay-alpha FLOAT        衰减系数
  --max-cycles INT           最大测试周期数
  --clean                    清空用户历史记忆
  -h, --help                显示帮助信息
```

## 🎯 使用示例

### 示例1: 基础测试

创建5条记忆，运行10个周期，每10秒扫描一次：

```powershell
uv run test-simulation --create-memories 5
```

### 示例2: 快速衰减测试

测试快速衰减，观察层次转换：

```powershell
uv run test-simulation `
  --create-memories 5 `
  --decay-alpha 2.0 `
  --scan-interval 5 `
  --max-cycles 12
```

### 示例3: 长期衰减测试

模拟更长时间的衰减过程：

```powershell
uv run test-simulation `
  --create-memories 5 `
  --time-unit minute `
  --time-scale 10.0 `
  --scan-interval 30 `
  --decay-alpha 0.5 `
  --max-cycles 20
```

### 示例4: 清空后重测

清空历史记忆，重新创建并测试：

```powershell
uv run test-simulation --clean --create-memories 5
```

## 📈 输出解读

### 实时输出

```
================================================================================
🔧 维护周期 #1
================================================================================
真实时间: 14:30:15
模拟天数: 0.00 天
衰减系数: α = 0.5

📊 发现 5 条记忆

  [abc12345] 我叫张三，是一名AI工程师...
    时间: 10.0秒 (模拟10.00天)
    权重: 1.000 → 0.167 (-0.833)
    层次: ✓ full → 🏷️  tag ⚡

--------------------------------------------------------------------------------
📈 本周期统计
--------------------------------------------------------------------------------
总记忆数: 5
层次转换: 3
权重更新: 2

当前层次分布:
  ✓ 完整记忆 (full):    2
  📝 摘要记忆 (summary): 0
  🏷️  标签记忆 (tag):     3
  👣 痕迹记忆 (trace):   0
  📦 存档记忆 (archive): 0
================================================================================
```

### 层次图标说明

- ✓ **完整记忆** (full): 权重 > 0.7，原文保留
- 📝 **摘要记忆** (summary): 0.3 ~ 0.7，摘要化
- 🏷️ **标签记忆** (tag): 0.1 ~ 0.3，模糊标签
- 👣 **痕迹记忆** (trace): 0.03 ~ 0.1，痕迹描述
- 📦 **存档记忆** (archive): ≤ 0.03，历史痕迹

### 日志文件

查看详细日志：

```powershell
# 实时查看
Get-Content tests\maintenance_simulation.log -Wait -Tail 50

# 查看完整日志
Get-Content tests\maintenance_simulation.log
```

## 🔧 高级用法

### 自定义测试记忆

编辑 `test_maintenance_simulation.py` 中的 `test_messages` 列表：

```python
test_messages = [
    "我叫张三，是一名AI工程师",
    "我特别喜欢喝咖啡，尤其是美式咖啡",
    # 添加自定义测试记忆
    "你的自定义测试内容",
]
```

### 测试不同衰减公式

修改 `calculate_decay_weight` 方法：

```python
# 当前公式: w(t) = w0 / (1 + α * t)
current_weight = initial_weight / (1 + self.config.decay_alpha * simulated_days)

# 示例：指数衰减
# current_weight = initial_weight * math.exp(-self.config.decay_alpha * simulated_days)
```

### 验证特定权重阈值

临时修改阈值测试边界情况：

```powershell
# 测试更宽松的阈值
$env:SIM_DECAY_ALPHA="0.3"
uv run test-simulation
```

## 🐛 故障排查

### 问题1: 无法连接Mem0服务

```
❌ 无法连接Mem0服务: Connection refused
```

**解决**：
```powershell
# 检查服务状态
docker-compose ps

# 启动服务
docker-compose up -d

# 检查健康状态
curl http://localhost:8000/health
```

### 问题2: 未找到ZHIPU_API_KEY

```
⚠️  智谱API密钥未配置
```

**解决**：
```powershell
# 编辑.env文件
notepad ..\app\.env

# 或设置环境变量
$env:ZHIPU_API_KEY="your_key_here"
```

### 问题3: 未创建测试记忆

```
⚠️  暂无记忆
```

**解决**：
```powershell
# 使用 --create-memories 参数
uv run test-simulation --create-memories 5
```

### 问题4: uv命令未找到

```
uv: 无法将"uv"项识别为 cmdlet
```

**解决**：
```powershell
# 安装uv
pip install uv

# 或使用标准Python
cd tests
python test_maintenance_simulation.py
```

## 📚 相关文档

- [五层记忆架构说明](../SMART_MEMORY_FIVE_LEVELS.md)
- [维护服务文档](../docs/MAINTENANCE_SERVICE.md)
- [快速开始指南](../QUICK_START.md)

## 💡 最佳实践

1. **首次测试**：使用默认配置，创建5条记忆
2. **观察转换**：使用闪电场景观察完整的层次转换
3. **验证阈值**：调整阈值参数，确认转换时机符合预期
4. **长期测试**：使用分钟级场景模拟长期衰减
5. **清理数据**：测试结束后使用 `--clean` 清理测试数据

## 🎓 理解衰减公式

权重衰减公式：**w(t) = w₀ / (1 + α × t)**

- **w₀**: 初始权重（通常为1.0）
- **α**: 衰减系数（控制衰减速度）
- **t**: 经过的时间（模拟天数）

**计算示例**：

```
初始权重 w₀ = 1.0
衰减系数 α = 0.5
时间 t = 10天

w(10) = 1.0 / (1 + 0.5 × 10)
      = 1.0 / 6
      = 0.167
```

**层次转换时间**：

达到权重0.7（full→summary）所需天数：

```
0.7 = 1.0 / (1 + α × t)
1 + α × t = 1.0 / 0.7
α × t = (1.0 / 0.7) - 1
t = ((1.0 / 0.7) - 1) / α
```

当 α=0.5 时，t ≈ 0.86天
