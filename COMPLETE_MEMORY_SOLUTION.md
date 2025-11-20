# 🧩 完整记忆管理方案设计

## 📋 目录

1. [系统概述](#系统概述)
2. [核心架构](#核心架构)
3. [身份与根ID管理](#身份与根id管理)
4. [记忆存储层](#记忆存储层)
5. [记忆衰退曲线](#记忆衰退曲线)
6. [定时调度服务](#定时调度服务)
7. [用户交互逻辑](#用户交互逻辑)
8. [检索与Reranker](#检索与reranker)
9. [特殊情形处理](#特殊情形处理)
10. [生命周期管理](#生命周期管理)
11. [实现细节](#实现细节)
12. [部署指南](#部署指南)

---

## 系统概述

### 设计目标

构建一个**智能、多模态、可追溯**的记忆管理系统，支持：

- ✅ **多用户环境**：通过设备UUID + 用户ID精准区分
- ✅ **多模态融合**：文本、图片、语音统一管理
- ✅ **智能衰退**：6因子增强型衰退曲线
- ✅ **自动压缩**：定时服务无感压缩，保持历史性
- ✅ **精准检索**：语义 + 时间 + 权重融合排序
- ✅ **完整溯源**：压缩链、合并链、修正链可追踪
- ✅ **隐私保护**：敏感标记、加密存储、分级保护

### 核心特性

| 特性           | 说明                                   | 优势                 |
| -------------- | -------------------------------------- | -------------------- |
| **身份管理**   | DeviceUUID + UserID + Timestamp        | 多用户环境准确归属   |
| **五级存储**   | FULL → SUMMARY → TAG → TRACE → ARCHIVE | 渐进式压缩，节省空间 |
| **六因子权重** | W = w_time × S × C × I × U × M         | 精准建模记忆重要性   |
| **双时间戳**   | created_at + last_activated_at         | 历史感 + 活跃度分离  |
| **三阶段检索** | 层级过滤 → 粗排 → 精排                 | 高效且准确           |
| **自动调度**   | 压缩 / 合并 / 清理任务                 | 无人值守运行         |

---

## 核心架构

### 系统组件

```
┌─────────────────────────────────────────────────────────┐
│                  完整记忆管理系统                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ 身份管理层   │  │ 存储管理层   │  │ 检索层      │  │
│  │              │  │              │  │             │  │
│  │ • DeviceUUID │  │ • MemoryStore│  │ • Retriever │  │
│  │ • UserID     │  │ • 多模态内容 │  │ • Reranker  │  │
│  │ • IDGenerator│  │ • 元数据     │  │ • 相似度    │  │
│  └──────────────┘  └──────────────┘  └─────────────┘  │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ 权重计算层   │  │ 决策引擎层   │  │ 调度服务层  │  │
│  │              │  │              │  │             │  │
│  │ • 6因子公式  │  │ • 场景识别   │  │ • 自动压缩  │  │
│  │ • 衰退曲线   │  │ • 动作决策   │  │ • 批量合并  │  │
│  │ • 因子跟踪   │  │ • 溯源管理   │  │ • 定期清理  │  │
│  └──────────────┘  └──────────────┘  └─────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │              生命周期管理层                       │  │
│  │  • 冻结/解冻  • 软删除/硬删除  • 敏感标记  • 日志 │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 数据流

```
用户输入 → 身份识别 → 语义分析 → 记忆检索 → 决策引擎
                                              ↓
                                         动作执行
                                              ↓
                    ┌─────────────────────────┴─────────────────────────┐
                    ↓                         ↓                         ↓
                 新建记忆                   合并更新                  标记否定
                    ↓                         ↓                         ↓
                权重计算                   刷新时间戳                 降权处理
                    ↓                         ↓                         ↓
                 存储入库 ←─────────────── 溯源链更新 ────────────→ 日志记录
```

---

## 身份与根ID管理

### 1. 设备UUID

**作用**：作为记忆存储的根标识符，区分不同设备。

**生成方式**：
```python
import uuid

device_uuid = str(uuid.uuid4())
# 示例: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**持久化**：存储在设备本地配置文件，首次启动生成，后续复用。

### 2. 用户ID

**作用**：在设备下区分不同用户。

**识别方式**：
- **声纹识别**：通过声纹特征生成用户ID
- **人脸识别**：通过面部特征生成用户ID
- **指纹识别**：通过指纹特征生成用户ID
- **手动输入**：用户自定义ID（测试模式）

**安全处理**：
```python
import hashlib

biometric_data = b"..."  # 生物特征原始数据
biometric_hash = hashlib.sha256(biometric_data).hexdigest()
# 仅存储哈希，不存储原始数据
```

### 3. 记忆ID结构

**格式**：`{DeviceUUID}_{UserID}_{Timestamp}_{SequenceID}`

**示例**：`a1b2c3d4_alice_20241120103045_00001`

**组成部分**：
- `DeviceUUID`（前8位）：设备短标识
- `UserID`：用户标识符
- `Timestamp`：创建时间（YYYYMMDDHHmmss）
- `SequenceID`：序列号（5位，递增）

**优势**：
- ✅ 全局唯一性保证
- ✅ 时间排序友好
- ✅ 易于解析和追溯
- ✅ 支持多设备同步（通过DeviceUUID区分）

---

## 记忆存储层

### 1. 五级层级结构

| 层级        | 名称     | 权重范围   | 内容形式     | 用途             |
| ----------- | -------- | ---------- | ------------ | ---------------- |
| **FULL**    | 完整记忆 | 0.6 ~ 2.0  | 原始完整内容 | 最近、重要的记忆 |
| **SUMMARY** | 压缩摘要 | 0.3 ~ 0.6  | LLM生成摘要  | 中期记忆压缩     |
| **TAG**     | 模糊标签 | 0.1 ~ 0.3  | 关键词标签   | 久远记忆索引     |
| **TRACE**   | 痕迹     | 0.05 ~ 0.1 | 最小元数据   | 仅保留存在痕迹   |
| **ARCHIVE** | 存档     | 0.0 ~ 0.05 | 归档状态     | 可能被清理       |

**压缩示例**：

```
FULL (W=0.85):
  "今天早上8点我在星巴克喝了一杯卡布奇诺，感觉很不错"

    ↓ (权重降至0.45)

SUMMARY (W=0.45):
  "早上在星巴克喝咖啡"

    ↓ (权重降至0.18)

TAG (W=0.18):
  ["星巴克", "咖啡", "早晨"]

    ↓ (权重降至0.07)

TRACE (W=0.07):
  {event: "咖啡消费", date: "2024-11-20"}

    ↓ (权重降至0.02)

ARCHIVE (W=0.02):
  [待清理或永久存档]
```

### 2. 多模态内容

**支持模态**：
- 📝 **TEXT**：文本内容
- 🖼️ **IMAGE**：图片URL + embeddings
- 🎤 **AUDIO**：语音URL + embeddings
- 🎬 **VIDEO**：视频URL + embeddings

**数据结构**：
```python
@dataclass
class MultimodalContent:
    text: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    embeddings: Dict[str, List[float]] = field(default_factory=dict)
```

**存储策略**：
- 小文本：直接存储
- 大文件：存储URL + 云端OSS
- Embeddings：用于相似度检索

### 3. 元数据设计

**核心字段**：

```python
@dataclass
class MemoryMetadata:
    # 身份信息
    memory_id: str
    device_uuid: str
    user_id: str
    
    # 双时间戳
    created_at: str          # 创建时间（历史感）
    last_activated_at: str   # 最后激活（活跃度）
    
    # 记忆属性
    level: MemoryLevel       # 层级
    category: MemoryCategory # 类别
    
    # 权重因子
    factors: MemoryFactors   # 6因子
    
    # 行为统计
    mention_count: int       # 提及次数
    reinforce_count: int     # 强化次数
    recent_mentions: List[str]
    
    # 冲突与修正
    is_negated: bool
    is_corrected: bool
    correction_history: List[Dict]
    
    # 溯源链
    source_ids: List[str]
    merged_from: List[str]
    compressed_from: Optional[str]
    parent_id: Optional[str]
    children_ids: List[str]
    
    # 多模态
    modalities: List[Modality]
    
    # 隐私与敏感性
    is_sensitive: bool
    sensitivity_level: int   # 0-3
    is_encrypted: bool
    
    # 生命周期
    is_deleted: bool
    deletion_time: Optional[str]
    is_frozen: bool
    
    # 可解释性
    weight_change_log: List[Dict]
    compression_history: List[Dict]
    
    # 群体记忆
    is_group_memory: bool
    group_id: Optional[str]
    shared_with: List[str]
```

### 4. 类别重要性

| 类别                  | 重要性 I | 衰减系数 α | 说明                     |
| --------------------- | -------- | ---------- | ------------------------ |
| **IDENTITY**          | 1.5      | 0.002      | 身份信息（姓名、职业等） |
| **STABLE_PREFERENCE** | 1.3      | 0.005      | 稳定偏好（饮食、兴趣）   |
| **SKILL**             | 1.2      | 0.007      | 技能知识                 |
| **FACT**              | 1.1      | 0.008      | 事实信息                 |
| **SHORT_PREFERENCE**  | 1.0      | 0.01       | 短期偏好                 |
| **EVENT**             | 0.9      | 0.012      | 事件记录                 |
| **TEMPORARY**         | 0.8      | 0.015      | 临时信息                 |

---

## 记忆衰退曲线

### 1. 基础公式

**时间权重**：
$$
w_{time}(t) = \frac{1}{1 + \alpha_{effective} \cdot t}
$$

其中：
$$
\alpha_{effective} = \alpha_{base} \times U \times category\_factor
$$

- $\alpha_{base}$：类别基础衰减系数（见上表）
- $U$：用户个性化因子（0.7 = 慢遗忘，1.5 = 快遗忘）
- $category\_factor$：类别调整因子
- $t$：距离 `last_activated_at` 的天数

### 2. 增强因子

#### 语义强化因子 S(t)

**公式**：
$$
S(t) = 1 + 0.5 \times e^{-0.05 \times \Delta t}
$$

**含义**：用户再次提及时，权重提升最多50%，随时间指数衰减。

**曲线**：
```
S(t)
1.50 ┤●
     │ ●●
1.40 ┤   ●●
     │     ●●●
1.30 ┤        ●●●
     │           ●●●●
1.20 ┤              ●●●●●
     │                  ●●●●●●
1.10 ┤                       ●●●●●●●●●
     │                              ●●●●●●●●●●●
1.00 ┤                                        ●●●●●●●
     └────────────────────────────────────────────────
      0    7   14   21   28   35   42   49   56  days
```

#### 冲突修正因子 C(t)

**公式**：
$$
C(t) = 0.3 + 0.7 \times e^{-0.01 \times \Delta t}
$$

**含义**：用户否定时，权重立即降至30%，随时间缓慢恢复。

**曲线**：
```
C(t)
1.00 ┤                                        ●●●●●●●
     │                              ●●●●●●●●●●
0.90 ┤                       ●●●●●●●
     │                  ●●●●●●
0.80 ┤              ●●●●●
     │           ●●●●
0.70 ┤        ●●●
     │     ●●●
0.60 ┤   ●●
     │ ●●
0.50 ┤●
     │●
0.30 ┤●
     └────────────────────────────────────────────────
      0   10   20   30   40   50   60   70   80  days
```

#### 动量因子 M(t)

**公式**：
$$
M(t) = 1 + 0.3 \times (1 - e^{-0.5 \times n})
$$

其中 $n$ 为近期（24小时内）提及次数。

**含义**：防止频繁提及导致权重无限放大，上限约1.3。

**曲线**：
```
M(n)
1.30 ┤              ●●●●●●●●●●●●●●●●●●●●●●●●
     │          ●●●●
1.25 ┤       ●●●
     │     ●●
1.20 ┤   ●●
     │  ●●
1.15 ┤ ●●
     │●●
1.10 ┤●
     │●
1.05 ┤●
     │●
1.00 ┤●
     └────────────────────────────────────────────────
      0    2    4    6    8   10   12   14   16  mentions
```

### 3. 综合权重公式

$$
W(t) = w_{time}(t) \times S(t) \times C(t) \times I \times U \times M(t)
$$

**边界约束**：$W(t) \in [0.01, 2.0]$

**六因子说明**：

| 因子     | 符号       | 范围       | 作用     |
| -------- | ---------- | ---------- | -------- |
| 时间权重 | $w_{time}$ | [0, 1]     | 基础衰减 |
| 语义强化 | $S$        | [1.0, 1.5] | 激活提升 |
| 冲突修正 | $C$        | [0.3, 1.0] | 否定降权 |
| 重要性   | $I$        | [0.8, 1.5] | 类别差异 |
| 用户因子 | $U$        | [0.7, 1.5] | 个性化   |
| 动量     | $M$        | [1.0, 1.3] | 频繁控制 |

### 4. 权重演化示例

**场景**：身份信息（I=1.5），普通用户（U=1.0），无激活/否定

| 天数 | w_time | S   | C   | I   | U   | M   | W(t)      | 层级 |
| ---- | ------ | --- | --- | --- | --- | --- | --------- | ---- |
| 0    | 1.000  | 1.0 | 1.0 | 1.5 | 1.0 | 1.0 | **1.500** | FULL |
| 7    | 0.986  | 1.0 | 1.0 | 1.5 | 1.0 | 1.0 | **1.479** | FULL |
| 30   | 0.943  | 1.0 | 1.0 | 1.5 | 1.0 | 1.0 | **1.414** | FULL |
| 90   | 0.847  | 1.0 | 1.0 | 1.5 | 1.0 | 1.0 | **1.271** | FULL |
| 180  | 0.735  | 1.0 | 1.0 | 1.5 | 1.0 | 1.0 | **1.103** | FULL |
| 365  | 0.578  | 1.0 | 1.0 | 1.5 | 1.0 | 1.0 | **0.867** | FULL |

**场景对比**（30天后）：

| 操作                | S    | C    | M    | W(30)     | 变化 |
| ------------------- | ---- | ---- | ---- | --------- | ---- |
| 无操作              | 1.00 | 1.00 | 1.00 | 1.414     | 基准 |
| **用户激活**        | 1.35 | 1.00 | 1.00 | **1.909** | +35% |
| **用户否定**        | 1.00 | 0.82 | 1.00 | **1.159** | -18% |
| **频繁强化（3次）** | 1.00 | 1.00 | 1.23 | **1.739** | +23% |

---

## 定时调度服务

### 1. 调度任务

**三大任务**：

| 任务         | 周期  | 职责                       |
| ------------ | ----- | -------------------------- |
| **自动压缩** | 1小时 | 计算权重，跨阈值压缩层级   |
| **批量合并** | 2小时 | 查找高度相似记忆，批量合并 |
| **定期清理** | 1天   | 删除无价值或过期记忆       |

### 2. 自动压缩流程

```
定时触发 (每1小时)
    ↓
遍历所有用户
    ↓
获取用户记忆列表
    ↓
逐条计算权重 W(t)
    ↓
判断是否跨阈值
    ↓
执行压缩操作
    ↓
记录压缩历史
    ↓
更新元数据（不刷新时间戳）
    ↓
记录权重变化日志
```

**关键规则**：
- ✅ **不刷新时间戳**：使用 `last_activated_at` 计算，保持历史感
- ✅ **尊重冻结标记**：`is_frozen=True` 跳过压缩
- ✅ **保护敏感记忆**：`sensitivity_level>=3` 不压缩
- ✅ **溯源链更新**：记录 `compressed_from`

### 3. 批量合并流程

```
定时触发 (每2小时)
    ↓
按类别分组
    ↓
计算组内相似度
    ↓
查找相似度 >= 0.85 的记忆组
    ↓
至少3条才合并
    ↓
生成摘要（LLM）
    ↓
创建新记忆（SUMMARY层级）
    ↓
累加 mention_count
    ↓
保留溯源链（merged_from）
    ↓
软删除旧记忆
```

**合并示例**：

```
记忆1: "我喜欢喝咖啡" (mention_count=3)
记忆2: "我喜欢喝黑咖啡" (mention_count=2)
记忆3: "我喜欢美式咖啡" (mention_count=1)

    ↓ 相似度 0.90

合并后:
  "用户对咖啡有稳定偏好，包括黑咖啡和美式咖啡"
  mention_count = 6
  merged_from = [memory1_id, memory2_id, memory3_id]
  level = SUMMARY
```

### 4. 定期清理规则

**删除条件**（同时满足）：
1. 权重 < 0.01
2. 创建时间 > 365天
3. 非冻结记忆
4. 非敏感记忆

**软删除记忆处理**：
- 软删除超过30天 → 硬删除

---

## 用户交互逻辑

### 1. 决策矩阵

| 触发类型       | 相似度    | 决策动作     | 时间戳刷新 | 权重变化 |
| -------------- | --------- | ------------ | ---------- | -------- |
| **被动衰减**   | -         | COMPRESS     | ❌ 不刷新   | 自然衰减 |
| **用户提及**   | ≥ 0.85    | MERGE        | ✅ 刷新     | +35% (S) |
| **用户提及**   | 0.60~0.85 | CREATE_NEW   | ❌          | 新建     |
| **用户提及**   | < 0.60    | CREATE_NEW   | ❌          | 新建     |
| **用户否定**   | -         | MARK_NEGATED | ❌          | -70% (C) |
| **频繁强化**   | -         | MERGE (cap)  | ✅          | +23% (M) |
| **跨模态更新** | -         | MERGE        | ✅          | 合并模态 |

### 2. 场景详解

#### 场景1：被动衰减

**触发**：定时服务（无用户操作）

**流程**：
```python
# 计算当前权重
factors = engine.calculate_enhanced_weight(memory, trigger=PASSIVE_DECAY)

# 决定新层级
new_level = engine.decide_compression_level(factors.total_weight, ...)

# 不刷新时间戳
# last_activated_at 保持不变

# 更新层级和元数据
memory.metadata.level = new_level
memory.metadata.factors = factors
```

#### 场景2：用户激活（高相似度）

**触发**：用户再次提及相似内容（similarity ≥ 0.85）

**流程**：
```python
# 合并更新
action, params = engine.decide_action(
    memory,
    new_content="我喜欢喝黑咖啡",
    similarity=0.90,
    trigger=USER_MENTION
)
# action = "MERGE"

# 刷新时间戳
memory.metadata.last_activated_at = now.isoformat()
memory.metadata.last_mention_time = now.isoformat()

# 更新内容（可选）
memory.content.text = merge(old_text, new_text)

# 增加提及次数
memory.metadata.mention_count += 1
memory.metadata.recent_mentions.append(now.isoformat())

# 重新计算权重（S因子提升）
factors = engine.calculate_enhanced_weight(memory, trigger=USER_MENTION)
```

#### 场景3：用户否定

**触发**：用户明确否定/修正记忆

**流程**：
```python
# 标记否定
memory.metadata.is_negated = True
memory.metadata.correction_history.append({
    "timestamp": now.isoformat(),
    "old_content": old_text,
    "new_content": new_text,
    "penalty": -0.7
})

# 不刷新时间戳（旧记忆）
# last_activated_at 保持不变

# 降权（C因子降至0.3）
factors = engine.calculate_enhanced_weight(memory, trigger=USER_NEGATION)

# 创建新记忆（FULL层级）
new_memory = create_memory(new_content, level=FULL, weight=1.0)
new_memory.metadata.parent_id = old_memory_id
```

#### 场景4：频繁强化

**触发**：24小时内提及 ≥ 3次

**流程**：
```python
# 检测频繁强化
is_frequent = engine.detect_frequent_reinforce(
    memory.metadata.recent_mentions,
    now
)

if is_frequent:
    # 合并更新，但动量因子有上限（1.3）
    factors = engine.calculate_enhanced_weight(memory)
    # M(t) = 1.23 (3次) 或 1.30 (10次+)
    
    # 防止权重无限增长
```

### 3. 冷启动处理

**定义**：用户首次提到某个主题/实体。

**策略**：
- 层级：`FULL`
- 权重：`1.0`
- 类别：根据内容自动分类（或用户指定）
- 时间戳：`created_at = last_activated_at = now`

---

## 检索与Reranker

### 1. 三阶段检索

```
查询输入
    ↓
【阶段1：层级过滤】
    ↓
根据查询模式过滤层级
  • NORMAL: 仅FULL/SUMMARY
  • REVIEW: 允许TRACE/ARCHIVE
  • DEBUG: 显示所有
    ↓
【阶段2：粗排（初筛）】
    ↓
计算简单相似度
    ↓
阈值过滤（similarity >= 0.6）
    ↓
Top-K初筛（取2倍留给精排）
    ↓
【阶段3：精排（Reranker）】
    ↓
计算综合相关性分数
    ↓
融合因子：
  α × semantic + β × time + γ × weight
    ↓
用户行为加成
    ↓
类别加成
    ↓
最终排序
    ↓
返回Top-K结果
```

### 2. 相关性分数公式

$$
relevance = \alpha \times semantic + \beta \times time + \gamma \times weight
$$

**默认配置**：
- $\alpha = 0.7$（语义权重）
- $\beta = 0.3$（时间权重）
- $\gamma = 0.0$（权重融入时间中）

**分数计算**：

1. **语义分数**：
   ```python
   # 使用embeddings计算余弦相似度（生产环境）
   semantic_score = cosine_similarity(query_embedding, memory_embedding)
   
   # 简化版（当前）
   semantic_score = jaccard_similarity(query_tokens, content_tokens)
   ```

2. **时间分数**：
   ```python
   time_score = exp(-0.01 × days_since_last_active)
   ```

3. **权重分数**：
   ```python
   weight_score = W(t) / 2.0  # 归一化到[0, 1]
   ```

### 3. 行为信号加成

```python
behavior_boost = 1.0

if memory.mention_count > 5:
    behavior_boost += 0.1  # 高频记忆

if memory.reinforce_count > 3:
    behavior_boost += 0.1  # 强化记忆

final_score = relevance × behavior_boost
```

### 4. 类别加成

```python
category_boost = 1.0

if memory.category in [IDENTITY, STABLE_PREFERENCE]:
    category_boost = 1.2  # 重要类别优先

final_score = relevance × category_boost
```

### 5. 查询模式

| 模式       | 层级范围          | 用途     |
| ---------- | ----------------- | -------- |
| **NORMAL** | FULL, SUMMARY     | 日常对话 |
| **REVIEW** | 全部层级          | 回顾往事 |
| **DEBUG**  | 全部层级 + 已删除 | 系统调试 |

---

## 特殊情形处理

### 1. 频繁强化

**问题**：用户短时间内多次提及同一主题，导致权重无限放大。

**解决方案**：
- **检测窗口**：24小时
- **阈值**：≥ 3次提及
- **动量上限**：M(t) ≤ 1.3
- **操作**：合并冗余记忆，避免库膨胀

### 2. 用户否定/修正

**问题**：用户发现旧记忆不准确，需要修正。

**解决方案**：
- **旧记忆**：标记 `is_negated=True`，降权70%（C=0.3）
- **新记忆**：创建 `FULL` 级别，权重1.0
- **溯源链**：`new_memory.parent_id = old_memory.id`
- **保留历史**：不删除旧记忆，记录修正历史

### 3. 跨模态更新

**场景**：用户先发送文本，后补充图片/语音。

**解决方案**：
```python
# 原记忆：TEXT
old_modalities = [Modality.TEXT]

# 用户补充图片
trigger = CROSS_MODAL_UPDATE
action = "MERGE"

# 合并模态
memory.content.image_url = new_image_url
memory.metadata.modalities.append(Modality.IMAGE)
memory.metadata.last_activated_at = now.isoformat()
```

### 4. 批量合并冗余

**场景**：同类别下存在多条高度相似的记忆。

**解决方案**：
- **相似度阈值**：≥ 0.85
- **最小数量**：≥ 3条
- **合并策略**：
  1. 提取共同特征
  2. LLM生成摘要
  3. 累加 `mention_count`
  4. 保留 `merged_from` 溯源链
  5. 软删除旧记忆

### 5. 冷启动记忆

**场景**：用户首次提到新主题。

**策略**：
- 层级：`FULL`
- 权重：`1.0`
- 时间戳：`created_at = last_activated_at = now`
- 类别：自动分类或用户指定

### 6. 群体记忆

**场景**：多用户共享的记忆（如家庭成员共同回忆）。

**设计**：
```python
memory.metadata.is_group_memory = True
memory.metadata.group_id = "family_001"
memory.metadata.shared_with = ["alice", "bob", "charlie"]
```

**检索**：查询时同时返回个人记忆 + 群体记忆。

### 7. 冲突记忆

**场景**：不同时期的记忆存在冲突（如搬家前后的地址）。

**策略**：
- **保留多版本**：通过 `created_at` 区分时间顺序
- **权重差异**：最新版本权重更高
- **溯源链**：`correction_history` 记录修正关系

---

## 生命周期管理

### 1. 用户控制

#### 冻结/解冻

**作用**：禁止系统自动压缩/删除。

**使用场景**：
- 重要记忆（如证件号码）
- 永久保留的回忆
- 调试特定记忆

```python
lifecycle.freeze_memory(memory_id)
# memory.metadata.is_frozen = True
```

#### 删除

**软删除**：
- 标记 `is_deleted=True`
- 30天后自动硬删除
- 可恢复

**硬删除**：
- 立即从存储中移除
- 不可恢复

```python
lifecycle.delete_memory(memory_id, soft=True)  # 软删除
lifecycle.delete_memory(memory_id, soft=False) # 硬删除
```

#### 敏感标记

**分级保护**（0-3）：
- **0**：普通记忆
- **1**：轻度敏感，权重<0.1才压缩
- **2**：中度敏感，权重<0.3才压缩
- **3**：高度敏感，永不压缩

```python
lifecycle.mark_sensitive(
    memory_id,
    sensitivity_level=3,
    encrypt=True  # 加密存储
)
```

### 2. 日志与可解释性

#### 权重变化日志

```json
{
  "timestamp": "2024-11-20T10:30:00",
  "trigger": "user_mention",
  "old_weight": 0.7543,
  "new_weight": 1.0183,
  "change": +0.2640,
  "factors": {
    "w_time": 0.8543,
    "S": 1.35,
    "C": 1.0,
    "I": 1.3,
    "U": 1.0,
    "M": 1.0
  },
  "reason": "用户激活，语义强化+35%"
}
```

#### 压缩历史

```json
{
  "timestamp": "2024-11-20T10:30:00",
  "old_level": "full",
  "new_level": "summary",
  "old_weight": 0.6543,
  "new_weight": 0.4321,
  "reason": "自动压缩（定时服务）"
}
```

#### 权重解释

```python
explanation = lifecycle.explain_weight(memory_id)
# 返回：
{
  "memory_id": "...",
  "total_weight": 1.2345,
  "factors": {
    "w_time": 0.8543,
    "S(t)": 1.35,
    "C(t)": 1.0,
    "I": 1.3,
    "U": 1.0,
    "M(t)": 1.0
  },
  "level": "full",
  "category": "stable_preference",
  "created_at": "2024-10-20T10:00:00",
  "last_activated_at": "2024-11-20T10:30:00",
  "mention_count": 5
}
```

### 3. 监控指标

**收集指标**：

```python
@dataclass
class MetricsSnapshot:
    timestamp: str
    total_memories: int
    level_distribution: Dict[str, int]  # 各层级数量
    category_distribution: Dict[str, int]  # 各类别数量
    compression_count: int
    merge_count: int
    deletion_count: int
    activation_count: int
    avg_weight: float
    min_weight: float
    max_weight: float
    processing_time_ms: float
```

**导出格式**：JSON

---

## 实现细节

### 1. 文件结构

```
app/
├── complete_memory_system.py    # 核心数据结构
├── complete_memory_engine.py    # 权重计算与决策引擎
├── smart_retriever.py            # 智能检索与Reranker
└── scheduler_lifecycle.py        # 调度服务与生命周期管理

tests/
└── test_complete_system.py       # 综合测试
```

### 2. 依赖库

```toml
[project]
dependencies = [
    "python-dotenv",
    "asyncio",
    # 生产环境建议：
    # "sentence-transformers",  # 语义相似度
    # "openai",                 # LLM摘要
    # "redis",                  # 缓存
    # "sqlalchemy",             # 持久化
]
```

### 3. 配置参数

```python
# 用户个性化
user_factor = 1.0  # 0.7=慢遗忘, 1.5=快遗忘

# 时间刻度
time_scale = 86400  # 1天=86400秒（生产环境）
time_scale = 60     # 1分钟=1天（测试环境）

# 调度周期
compression_interval = 3600   # 1小时
merge_interval = 7200         # 2小时
cleanup_interval = 86400      # 1天

# 检索配置
similarity_threshold = 0.6
top_k = 10
```

### 4. 性能优化

**并行处理**：
```python
config = SchedulerConfig(
    enable_parallel=True,
    max_workers=4
)
```

**批量处理**：
```python
batch_size = 100  # 每批处理100条记忆
```

**索引优化**：
```python
# 用户索引
user_index: Dict[str, Set[str]]  # user_id -> memory_ids

# 设备索引
device_index: Dict[str, Set[str]]  # device_uuid -> memory_ids

# 群组索引
group_index: Dict[str, Set[str]]  # group_id -> memory_ids
```

---

## 部署指南

### 1. 快速启动

```bash
# 1. 克隆仓库
git clone https://github.com/your-repo/mem0-system.git
cd mem0-system

# 2. 安装依赖
uv sync

# 3. 运行测试
uv run python tests/test_complete_system.py

# 4. 启动调度服务
uv run python app/scheduler_lifecycle.py
```

### 2. 生产环境集成

#### 与Mem0 API集成

```python
# app/mem0_integration.py

from mem0 import MemoryClient
from complete_memory_engine import CompleteMemoryEngine

client = MemoryClient(api_key="your-api-key")
engine = CompleteMemoryEngine(user_factor=1.0)

# 创建记忆
memory_data = {
    "messages": [{"role": "user", "content": "我喜欢喝咖啡"}],
    "user_id": "alice",
    "metadata": {
        "device_uuid": device_uuid,
        "category": "stable_preference",
        "factors": engine.calculate_enhanced_weight(...).to_dict()
    }
}

result = client.add(memory_data)
```

#### 使用真实Embeddings

```python
# 安装
# pip install sentence-transformers

from sentence_transformers import SentenceTransformer

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def calculate_semantic_similarity(query: str, memory: Memory) -> float:
    query_emb = model.encode(query)
    memory_emb = model.encode(memory.content.text)
    
    # 余弦相似度
    similarity = cosine_similarity(query_emb, memory_emb)
    return similarity
```

#### 使用LLM生成摘要

```python
from openai import OpenAI

client = OpenAI(api_key="your-key")

def summarize_with_llm(texts: List[str]) -> str:
    prompt = f"请将以下记忆合并为一段简洁的摘要：\n" + "\n".join(texts)
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content
```

### 3. 监控与运维

**日志配置**：
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('memory_system.log'),
        logging.StreamHandler()
    ]
)
```

**指标导出**：
```python
# 定期导出指标
scheduler.metrics.export_metrics("metrics_2024-11-20.json")
```

**备份与恢复**：
```python
# 备份
store.export_to_json("backup_2024-11-20.json", user_id="alice")

# 恢复
store.import_from_json("backup_2024-11-20.json")
```

---

## 总结

### 核心优势

1. **🎯 精准归属**：DeviceUUID + UserID 双重保障
2. **📊 智能衰退**：6因子公式，平衡遗忘与保留
3. **🔄 自动优化**：定时压缩/合并/清理，无需人工干预
4. **🔍 高效检索**：三阶段检索，语义+时间+权重融合
5. **📜 完整溯源**：压缩链、合并链、修正链可追踪
6. **🔒 隐私保护**：分级敏感标记，加密存储
7. **🛠️ 可解释性**：权重日志、压缩历史、决策透明

### 技术创新

- ✨ **双时间戳设计**：历史感与活跃度分离
- ✨ **动量因子饱和**：防止频繁提及无限放大
- ✨ **冲突自愈机制**：否定降权+渐进恢复
- ✨ **多模态统一**：文本/图片/语音一体化管理
- ✨ **群体记忆支持**：个人与群组记忆并存

### 适用场景

- 🤖 **个人AI助手**：长期陪伴，记住用户偏好
- 👨‍👩‍👧‍👦 **家庭机器人**：多用户环境，群体记忆
- 🏥 **医疗助手**：敏感信息保护，长期健康追踪
- 📚 **教育助手**：知识积累，学习轨迹追踪
- 🏢 **企业知识库**：团队记忆共享，版本追溯

---

**文档版本**：v1.0  
**最后更新**：2024-11-20  
**作者**：GitHub Copilot  
**许可证**：MIT
