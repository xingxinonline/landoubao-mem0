# 智能记忆管理策略 - 五层架构

## 🎯 核心改进

### 不再遗忘，只是模糊

**传统做法**：低权重记忆直接删除 ❌  
**新策略**：所有记忆永久保留，逐渐模糊 ✅

---

## 📊 五层记忆架构

| 权重区间       | 层次名称              | 表现形式     | 示例                     | 检索模式               |
| -------------- | --------------------- | ------------ | ------------------------ | ---------------------- |
| **> 0.7**      | 完整记忆<br>(FULL)    | 完整保留原文 | "用户喜欢喝咖啡"         | 普通模式✓<br>回顾模式✓ |
| **0.3 ~ 0.7**  | 摘要记忆<br>(SUMMARY) | 摘要化       | "用户偏好咖啡类饮品"     | 普通模式✓<br>回顾模式✓ |
| **0.1 ~ 0.3**  | 模糊标签<br>(TAG)     | 模糊化标签   | "用户喜欢饮品"           | 回顾模式✓              |
| **0.01 ~ 0.1** | 痕迹记忆<br>(TRACE)   | 极低权重层级 | "用户曾经有饮品相关记忆" | 回顾模式✓              |
| **≤ 0.01**     | 存档记忆<br>(ARCHIVE) | 最低保留阈值 | "历史痕迹：饮品偏好"     | 回顾模式✓<br>(仅存档)  |

---

## 🔄 回顾模式

### 触发条件

#### 1. 用户明确请求（关键词触发）
```
关键词：回顾、以前、过去、历史、很久以前、曾经、早期

示例：
- "我以前说过什么？"
- "帮我回顾一下我过去的偏好"
- "十年前我提到过什么？"
- "很久以前我好像提过咖啡"
```

#### 2. 系统主动提示（可选）
```
场景：用户长时间未交互

系统提示："要不要进入回顾模式，看看你过去的记录？"
```

### 模式切换逻辑

| 模式         | 检索范围   | 返回内容                         | 适用场景         |
| ------------ | ---------- | -------------------------------- | ---------------- |
| **普通模式** | 权重 > 0.3 | 完整记忆 + 摘要记忆              | 日常对话         |
| **回顾模式** | 所有权重   | 完整 + 摘要 + 标签 + 痕迹 + 存档 | 明确要求回顾历史 |

### 检索策略

```python
# 普通模式
def search_normal_mode(query, user_id):
    memories = search_memory(query, user_id)
    return [m for m in memories if m.weight > 0.3]  # 只返回高权重

# 回顾模式
def search_review_mode(query, user_id):
    memories = search_memory(query, user_id)
    return memories  # 返回所有层次，包括痕迹和存档
```

### 输出形式对比

**普通模式**：
```
✓ 你喜欢喝咖啡
~ 你偏好咖啡类饮品（较早前的印象）
```

**回顾模式**：
```
✓ 你喜欢喝咖啡
~ 你偏好咖啡类饮品（较早前的印象）
· 用户喜欢饮品（模糊的记忆）
👣 你曾经有饮品相关记忆
📦 历史痕迹：饮品偏好
```

---

## ⚙️ 实现逻辑

### 决策流程

```python
def decide_memory_action(user_message):
    """LLM分析用户消息"""
    
    # 检测回顾模式触发词
    review_keywords = ["回顾", "以前", "过去", "历史", "很久以前", "曾经"]
    
    if any(kw in user_message for kw in review_keywords):
        return {
            "action": "QUERY",
            "review_mode": True  # 启用回顾模式
        }
    
    # 其他操作...
    return {"action": "...", "review_mode": False}
```

### 格式化上下文

```python
def format_memory_for_context(memories, review_mode=False):
    """根据模式格式化记忆"""
    
    context_lines = []
    
    for mem in memories:
        weight = mem["current_weight"]
        level = mem["memory_level"]
        content = mem["memory"]
        
        # 普通模式：跳过低权重记忆
        if not review_mode and weight < 0.3:
            continue
        
        # 根据层次格式化
        if level == "full":
            context_lines.append(f"✓ {content}")
        elif level == "summary":
            context_lines.append(f"~ {content}（较早前的印象）")
        elif level == "tag":
            context_lines.append(f"· {content}（模糊的记忆）")
        elif level == "trace":
            context_lines.append(f"👣 {content}")
        elif level == "archive":
            context_lines.append(f"📦 {content}")
    
    return "\n".join(context_lines)
```

---

## 🔧 维护服务逻辑

### 层次转换规则

```python
def process_memory(memory):
    """维护服务处理单条记忆"""
    
    current_weight = calculate_decay(memory)
    new_level = get_memory_level(current_weight)
    old_level = memory["level"]
    
    # 判断是否需要转换层次
    if new_level != old_level:
        if new_level == "summary":
            new_content = llm_summarize(memory["content"])
        elif new_level == "tag":
            new_content = llm_tag(memory["content"])
        elif new_level == "trace":
            new_content = f"用户曾经有{extract_topic(memory['content'])}相关记忆"
        elif new_level == "archive":
            new_content = f"历史痕迹：{extract_topic(memory['content'])}"
        
        # 更新记忆（保留原始内容在metadata中）
        update_memory(memory["id"], {
            "content": new_content,
            "level": new_level,
            "weight": current_weight,
            "original_content": memory["content"]  # 可追溯
        })
```

### 不再清理删除

```python
# ❌ 旧逻辑
if current_weight < 0.05:
    delete_memory(memory_id)  # 遗忘

# ✅ 新逻辑
if current_weight <= 0.01:
    convert_to_archive(memory_id)  # 存档，不删除
```

---

## 🎬 使用示例

### 场景1: 普通对话

```
用户: "我喜欢什么？"

系统: [普通模式检索，权重 > 0.3]
✓ 你喜欢喝咖啡
~ 你偏好咖啡类饮品（较早前的印象）

助理: "你喜欢喝咖啡，特别是美式咖啡。"
```

### 场景2: 回顾历史

```
用户: "我以前说过什么？"

系统: [检测到"以前"，进入回顾模式，检索所有层次]
✓ 你喜欢喝咖啡（权重: 0.85）
~ 你偏好咖啡类饮品（权重: 0.45）
· 用户喜欢饮品（权重: 0.18）
👣 你曾经有饮品相关记忆（权重: 0.05）
📦 历史痕迹：饮品偏好（权重: 0.008）

助理: "根据你的历史记录，你现在喜欢喝咖啡，之前也提到过饮品相关的偏好，
       这个习惯从很久以前就有了。"
```

### 场景3: 时间衰减演示

```
初始状态（第1天）：
✓ 用户喜欢喝美式咖啡，不加糖不加奶（权重: 1.0, 层次: full）

30天后：
✓ 用户喜欢喝美式咖啡，不加糖不加奶（权重: 0.77, 层次: full）

100天后：
~ 用户偏好黑咖啡（权重: 0.50, 层次: summary）

300天后：
· 用户喜欢饮品（权重: 0.25, 层次: tag）

1000天后：
👣 用户曾经有饮品相关记忆（权重: 0.09, 层次: trace）

3000天后：
📦 历史痕迹：饮品偏好（权重: 0.003, 层次: archive）
```

---

## 🔐 安全与效率

### 避免过度干扰

```
✅ 普通模式：只用近期和摘要记忆（权重 > 0.3）
   - 保证对话高效
   - 不被久远记忆干扰

✅ 回顾模式：用户明确请求时才检索低权重记忆
   - 用户控制
   - 按需召回
```

### 效率优化

```python
# 索引优化：按权重分层索引
{
    "high_weight": [memories with weight > 0.3],    # 普通模式索引
    "low_weight": [memories with weight ≤ 0.3],    # 回顾模式专用
    "archive": [memories with weight ≤ 0.01]       # 存档层
}

# 查询优化
if review_mode:
    search_all_indexes()
else:
    search_high_weight_index_only()  # 更快
```

---

## 📈 优势对比

| 特性         | 传统删除策略   | 五层模糊化策略      |
| ------------ | -------------- | ------------------- |
| **记忆保留** | 低权重直接删除 | 永久保留，逐渐模糊  |
| **可追溯性** | 遗忘后无法恢复 | 可通过回顾模式召回  |
| **用户体验** | 硬遗忘，突兀   | 渐进模糊，自然      |
| **检索效率** | 单一模式       | 双模式（普通/回顾） |
| **数据安全** | 不可逆删除     | 保留历史痕迹        |

---

## 🛠️ 配置参数

```python
# 维护服务配置
config = MaintenanceConfig(
    # 衰减参数
    decay_alpha=0.01,  # 衰减系数
    
    # 五层阈值
    full_memory_threshold=0.7,      # > 0.7 = 完整
    summary_memory_threshold=0.3,   # 0.3~0.7 = 摘要
    tag_memory_threshold=0.1,       # 0.1~0.3 = 标签
    trace_memory_threshold=0.01,    # 0.01~0.1 = 痕迹
    # ≤ 0.01 = 存档
    
    # 不再有 cleanup_threshold
)
```

---

## ✅ 总结

### 核心理念
1. **不遗忘**：所有记忆都保留，只是逐渐模糊
2. **渐进式**：五层架构，平滑过渡
3. **用户控制**：普通模式高效，回顾模式全面
4. **可追溯**：原始内容保留在metadata中

### 关键功能
- ✅ 五层记忆架构（完整 → 摘要 → 标签 → 痕迹 → 存档）
- ✅ 双检索模式（普通模式 vs 回顾模式）
- ✅ 关键词触发回顾模式
- ✅ 时间衰减自动转换层次
- ✅ 永久保留，不删除

### 实现文件
- `app/memory_maintenance.py` - 维护服务
- `tests/test_smart_memory.py` - 智能记忆助理
- `docs/SMART_MEMORY_STRATEGY.md` - 本文档
