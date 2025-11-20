# 记忆更新策略设计文档

## 核心理念

**记忆衰退的本质是内容压缩，而非简单的权重降低**

- **被动演化**：定时服务压缩久远记忆，**不刷新时间戳**（保持历史感）
- **主动激活**：用户提及相关内容时，根据语义相似度决定合并或新建，**刷新时间戳**

---

## 两种场景对比

| 维度         | 场景1：被动压缩                        | 场景2：用户提及              |
| ------------ | -------------------------------------- | ---------------------------- |
| **触发者**   | 定时服务                               | 用户交互                     |
| **时间戳**   | 保持原始时间（体现历史感）             | 刷新为当前时间（记忆被激活） |
| **内容变化** | 压缩（full→summary→tag→trace→archive） | 根据相似度合并/新建          |
| **权重变化** | 持续衰减                               | 提升（激活）                 |
| **层级变化** | 单向降级                               | 可能升级（高相似度）         |

---

## 场景1：被动压缩（定时服务）

### 特点
```
✅ 时间戳不变
✅ 内容压缩
✅ 权重衰减
✅ 保持历史感
```

### 执行逻辑
```python
# 压缩记忆
memory_level: full → summary (7天)
              summary → tag (30天)
              tag → trace (90天)
              trace → archive (180天)

# 时间戳保持
updated_at: "2024-01-01T10:00:00"  # 不变

# 权重持续衰减
weight: 1.0 → 0.909 → 0.714 → 0.500 → 0.357
```

### 示例
```
原始: [2024-01-01] "我叫张三，是一名AI工程师，目前在北京工作" (full)
10天: [2024-01-01] "我叫张三，是一名AI工程师..." (summary)  # 时间戳未变
40天: [2024-01-01] "#职业:工程师 #地点:北京" (tag)        # 时间戳未变
100天: [2024-01-01] "曾有职业相关记忆" (trace)            # 时间戳未变
200天: [2024-01-01] "[已归档]" (archive)                  # 时间戳未变
```

---

## 场景2：用户提及（主动激活）

### 决策树
```
用户提及新内容
    |
    ├─→ 计算与旧记忆的语义相似度
    |
    ├─→ 高相似度 (≥0.85)
    |     ├─ 策略: 合并更新
    |     ├─ 时间戳: ✅ 刷新
    |     ├─ 层级: 可能升级 (tag→summary→full)
    |     └─ 权重: 大幅提升 (+60%)
    |
    ├─→ 中等相似度 (0.60-0.84)
    |     ├─ 策略: 保留双轨
    |     ├─ 旧记忆: 时间戳不变，保持压缩状态
    |     └─ 新记忆: 新建 full 级别记忆
    |
    └─→ 低相似度 (<0.60)
          ├─ 策略: 新建独立记忆
          ├─ 旧记忆: 保持压缩状态，时间戳不变
          └─ 新记忆: 新建 full 级别记忆
```

### 场景2.1：高相似度 → 合并更新
```
旧记忆: [2024-01-01] "#职业:工程师" (tag, weight=0.2)
用户提及: "我是AI工程师张三"
相似度: 0.92

执行:
  ✅ 合并内容: "#职业:工程师" + "我是AI工程师张三" → "我是AI工程师张三"
  ✅ 升级层级: tag → summary
  ✅ 刷新时间戳: 2024-01-01 → 2024-11-20
  ✅ 提升权重: 0.2 → 0.68 (+60%)

结果: [2024-11-20] "我是AI工程师张三" (summary, weight=0.68)
```

### 场景2.2：中等相似度 → 保留双轨
```
旧记忆: [2024-01-01] "曾有职业相关记忆" (trace, weight=0.08)
用户提及: "我现在是产品经理了"
相似度: 0.68

执行:
  ✅ 保留旧记忆: [2024-01-01] "曾有职业相关记忆" (trace, 不变)
  ✅ 新建记忆: [2024-11-20] "我现在是产品经理了" (full, weight=1.0)

结果: 双轨并存，保留历史痕迹
```

### 场景2.3：低相似度 → 新建独立记忆
```
旧记忆: [2024-01-01] "#职业:工程师" (tag, weight=0.12)
用户提及: "我喜欢喝咖啡"
相似度: 0.15

执行:
  ✅ 保持旧记忆: [2024-01-01] "#职业:工程师" (tag, 不变)
  ✅ 新建记忆: [2024-11-20] "我喜欢喝咖啡" (full, weight=1.0)

结果: 独立记忆，旧记忆保持压缩状态
```

---

## 相似度阈值

| 范围      | 策略     | 时间戳刷新   | 层级变化 | 权重提升 |
| --------- | -------- | ------------ | -------- | -------- |
| ≥ 0.85    | 合并更新 | ✅ 是         | 可能升级 | +60%     |
| 0.60-0.84 | 保留双轨 | ❌ 否（旧的） | 无       | 无       |
| < 0.60    | 新建独立 | ❌ 否（旧的） | 无       | 无       |

---

## 权重提升机制

### 被动压缩
```python
# 不提升权重，持续衰减
weight(t) = w₀ / (1 + α * t)
```

### 用户提及
```python
# 高相似度 (≥0.85)
boost = (1.0 - old_weight) * 0.6
new_weight = min(1.0, old_weight + boost)
# 示例: 0.2 → 0.68 (+60% of gap)

# 中等相似度 (0.60-0.84)
boost = (1.0 - old_weight) * 0.3
new_weight = min(1.0, old_weight + boost)
# 示例: 0.3 → 0.51 (+30% of gap)

# 低相似度 (<0.60)
new_weight = min(1.0, old_weight + 0.1)
# 示例: 0.3 → 0.4 (固定+0.1)
```

---

## 层级升级规则

| 当前层级 | 升级条件      | 升级后  |
| -------- | ------------- | ------- |
| archive  | 相似度 > 0.9  | trace   |
| trace    | 相似度 > 0.9  | tag     |
| tag      | 相似度 > 0.9  | summary |
| summary  | 相似度 > 0.95 | full    |
| full     | -             | full    |

---

## 实现文件

### 核心模块
```
app/
  memory_update_strategy.py    # 策略引擎
  memory_maintenance.py         # 定时维护服务

tests/
  test_memory_update_strategy.py                   # 单元测试
  test_integrated_compression_and_update.py        # 集成测试
```

### 关键类
```python
# 更新触发类型
class UpdateTrigger(Enum):
    PASSIVE_DECAY = "passive_decay"      # 定时服务
    USER_MENTION = "user_mention"        # 用户提及
    MANUAL_EDIT = "manual_edit"          # 手动编辑

# 合并策略
class MergeStrategy(Enum):
    MERGE_UPDATE = "merge_update"        # 合并更新
    CREATE_NEW = "create_new"            # 新建记忆
    KEEP_BOTH = "keep_both"              # 保留双轨

# 决策结果
@dataclass
class UpdateDecision:
    strategy: MergeStrategy
    should_refresh_timestamp: bool       # ✅ 关键字段
    should_upgrade_level: bool
    reason: str
    similarity_score: float
```

---

## 测试验证

### 单元测试
```bash
cd tests
uv run python test_memory_update_strategy.py
```

**验证点**：
- ✅ 被动压缩不刷新时间戳
- ✅ 高相似度合并更新 + 刷新时间戳
- ✅ 中等相似度保留双轨
- ✅ 低相似度新建独立记忆
- ✅ 权重提升机制正确

### 集成测试
```bash
cd tests
uv run python test_integrated_compression_and_update.py
```

**场景模拟**：
1. 第1天：创建3条记忆
2. 第10天：定时压缩到summary（时间戳不变）
3. 第15天：用户提及工程师话题（高相似度，刷新时间戳）
4. 第40天：继续压缩到tag
5. 第45天：用户提及咖啡（中等相似度，保留双轨）
6. 第100天：压缩到trace
7. 第105天：用户提及新话题（低相似度，新建独立）

---

## 设计原则

### 1. 历史感保留
- 被动压缩不刷新时间戳
- 用户能够看到记忆的真实年代
- 区分"久远记忆"和"近期记忆"

### 2. 智能激活
- 用户提及相关内容时
- 高相似度记忆被"唤醒"
- 权重提升，层级升级
- 时间戳刷新表示"最近被回忆"

### 3. 双轨保留
- 中等相似度时
- 保留历史记忆（压缩状态）
- 新建当前记忆（完整状态）
- 同时维护历史脉络和当前状态

### 4. 独立性
- 低相似度时
- 旧记忆保持压缩
- 新记忆独立创建
- 避免无关内容混淆

---

## 生产环境建议

### 语义相似度计算
当前实现使用简化的Jaccard相似度，生产环境建议：

```python
# 方案1: sentence-transformers
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
embeddings = model.encode([text1, text2])
similarity = cosine_similarity(embeddings[0], embeddings[1])

# 方案2: OpenAI Embeddings
import openai
emb1 = openai.Embedding.create(input=text1, model="text-embedding-ada-002")
emb2 = openai.Embedding.create(input=text2, model="text-embedding-ada-002")
similarity = cosine_similarity(emb1, emb2)

# 方案3: 智谱AI Embeddings
from zhipuai import ZhipuAI
client = ZhipuAI(api_key="your-api-key")
response = client.embeddings.create(
    model="embedding-2",
    input=[text1, text2]
)
```

### 内容合并
当前使用简单字符串拼接，生产环境建议：

```python
# 使用LLM生成高质量合并
def merge_with_llm(old_content: str, new_content: str) -> str:
    prompt = f"""
    旧记忆: {old_content}
    新内容: {new_content}
    
    请合并这两段内容，保留关键信息，生成一段简洁的摘要。
    """
    return llm.generate(prompt)
```

---

## 配置参数

```env
# 相似度阈值
HIGH_SIMILARITY_THRESHOLD=0.85
MEDIUM_SIMILARITY_THRESHOLD=0.60

# 权重提升系数
HIGH_SIMILARITY_BOOST=0.6
MEDIUM_SIMILARITY_BOOST=0.3
LOW_SIMILARITY_BOOST=0.1

# 升级阈值
UPGRADE_THRESHOLD_FULL=0.95
UPGRADE_THRESHOLD_SUMMARY=0.90
UPGRADE_THRESHOLD_TAG=0.90
```

---

## 总结

### 核心创新点
1. **时间戳分离策略**：被动维护不刷新，主动激活才刷新
2. **语义相似度决策**：根据相似度智能选择合并/双轨/新建
3. **双轨记忆保留**：中等相似度时保留历史和当前
4. **权重动态提升**：用户激活时权重回升

### 解决的问题
- ✅ 久远记忆保持历史感（时间戳不变）
- ✅ 活跃记忆体现新鲜度（时间戳刷新）
- ✅ 相关记忆智能合并（高相似度）
- ✅ 相关记忆双轨并存（中等相似度）
- ✅ 无关记忆独立管理（低相似度）

### 适用场景
- 个人助手系统
- 知识库管理
- 客户关系管理
- 长期对话记忆
- 学习笔记系统
