# 增强型记忆管理系统 - 快速参考

## 核心公式 🧮

```
W(t) = w_time(t) × S(t) × C(t) × I × U × M(t)
```

| 因子          | 含义     | 范围     | 关键参数  |
| ------------- | -------- | -------- | --------- |
| **w_time(t)** | 时间衰减 | 0.01-1.0 | α=0.01    |
| **S(t)**      | 语义强化 | 1.0-1.5  | s_max=0.5 |
| **C(t)**      | 冲突修正 | 0.3-1.0  | c_min=0.3 |
| **I**         | 重要性   | 0.8-1.5  | 类别相关  |
| **U**         | 用户因子 | 0.7-1.5  | 个性化    |
| **M(t)**      | 动量     | 1.0-1.3  | m=0.3     |

---

## 关键场景 📋

### 1️⃣ 被动压缩
```
触发: 定时服务
时间戳: ❌ 不刷新
权重: 持续衰减
```

### 2️⃣ 用户激活（高相似度≥0.85）
```
触发: 用户提及
时间戳: ✅ 刷新 last_activated_at
权重: 提升 1.5-2.0x
强化: S(t) = 1.5 (立即) → 1.35 (7天) → 1.11 (30天)
```

### 3️⃣ 用户否定
```
触发: "我不喜欢咖啡了"
旧记忆: 降权70%, 标记is_negated
新记忆: FULL层级, weight=1.0
时间戳: 旧的不刷新
```

### 4️⃣ 频繁强化（24h内≥3次）
```
检测: detect_frequent_reinforce()
处理: 适度提升, 限制过度放大
动量: M(t) ≤ 1.3
```

### 5️⃣ 批量合并
```
条件: 大量相似记忆
结果: N条 → 1条摘要
保留: merged_from, mention_count
```

---

## 类别权重 🏷️

| 类别     | 重要性 I | 衰减速度 | 180天权重 |
| -------- | -------- | -------- | --------- |
| 身份信息 | 1.5      | 最慢     | 0.45      |
| 稳定偏好 | 1.3      | 慢       | 0.42      |
| 事实     | 1.1      | 中       | 0.38      |
| 短期偏好 | 0.9      | 快       | 0.33      |
| 临时信息 | 0.8      | 最快     | 0.31      |

---

## 双时间戳 🕐

```python
created_at: "2024-01-01"        # 历史感（不变）
last_activated_at: "2024-01-20" # 活跃度（刷新）
```

| 操作     | created_at | last_activated_at |
| -------- | ---------- | ----------------- |
| 创建     | 设置       | 设置              |
| 被动压缩 | 不变       | 不变              |
| 用户提及 | 不变       | ✅ 刷新            |
| 权重计算 | 不用       | ✅ 用于衰减        |

---

## 决策矩阵 🎯

| 场景     | 相似度    | 动作       | 刷新时间戳 | 权重变化 |
| -------- | --------- | ---------- | ---------- | -------- |
| 被动压缩 | -         | compress   | ❌          | 衰减     |
| 高相似   | ≥0.85     | merge      | ✅          | +60%     |
| 中等相似 | 0.60-0.84 | keep_both  | ❌          | 旧的不变 |
| 低相似   | <0.60     | create_new | ❌          | 旧的不变 |
| 用户否定 | -         | negate     | ❌          | -70%     |

---

## 查询模式 🔍

| 模式   | 召回层级       | 权重阈值 | 用途     |
| ------ | -------------- | -------- | -------- |
| NORMAL | FULL + SUMMARY | ≥0.3     | 日常对话 |
| REVIEW | 全部           | ≥0.01    | 回顾历史 |
| DEBUG  | 全部+已删除    | 无       | 调试     |

---

## 敏感级别 🔒

| 级别 | 类型 | 处理     |
| ---- | ---- | -------- |
| 0    | 公开 | 正常压缩 |
| 1    | 一般 | 慢速压缩 |
| 2    | 敏感 | 不压缩   |
| 3    | 高敏 | 加密存储 |

---

## 快速启动 🚀

### 创建策略引擎
```python
from enhanced_memory_strategy import (
    EnhancedMemoryStrategy,
    MemoryMetadata,
    MemoryCategory,
    UpdateTrigger
)

# 遗忘正常的用户
strategy = EnhancedMemoryStrategy(user_factor=1.0)

# 遗忘慢的用户
strategy = EnhancedMemoryStrategy(user_factor=0.8)
```

### 计算权重
```python
metadata = MemoryMetadata(
    created_at="2024-01-01T10:00:00",
    last_activated_at="2024-01-01T10:00:00",
    category=MemoryCategory.STABLE_PREFERENCE
)

weight = strategy.calculate_enhanced_weight(metadata)
# 结果: 0.8125
```

### 决策
```python
decision = strategy.decide_enhanced_action(
    trigger=UpdateTrigger.USER_MENTION,
    old_memory=memory,
    new_content="我是AI工程师",
    similarity_score=0.92
)

if decision.should_refresh_timestamp:
    memory["last_activated_at"] = now()
```

---

## 测试命令 🧪

```bash
# 增强策略测试（9项）
uv run python tests/test_enhanced_strategy.py

# 基础策略测试（5项）
uv run python tests/test_memory_update_strategy.py

# 对比演示
uv run python tests/demo_basic_vs_enhanced.py

# 集成测试
uv run python tests/test_integrated_compression_and_update.py
```

---

## 关键数据 📊

### 权重对比
```
普通记忆30天: 0.58
激活记忆30天: 1.54 (提升2.7x)
否定记忆30天: 0.61 (降至0.82)
```

### 语义强化衰减
```
提及后  0天: +50%
提及后  7天: +35%
提及后 30天: +11%
```

### 冲突惩罚恢复
```
否定后  0天: 100%
否定后 30天:  82%
否定后 90天:  58%
```

### 动量上限
```
提及  0次: 1.00
提及  3次: 1.23
提及 10次: 1.30 (上限)
```

---

## 常见问题 ❓

### Q: 为什么用双时间戳？
A: 区分历史感（created_at）和活跃度（last_activated_at），被动压缩不刷新，用户激活才刷新。

### Q: 频繁提及会无限增长吗？
A: 不会，动量因子有上限（1.3），权重边界是[0.01, 2.0]。

### Q: 用户否定后旧记忆会删除吗？
A: 不会，旧记忆标记为is_negated，降权70%，保留版本供溯源。

### Q: 如何处理重复记忆？
A: 使用merge_memories_batch()批量合并为摘要，保留mention_count。

### Q: 敏感信息会被压缩吗？
A: 不会，sensitivity_level≥2的记忆不压缩，≥3的加密存储。

---

## 文档导航 📚

- **详细设计**: `ENHANCED_MEMORY_SYSTEM.md`
- **实现报告**: `ENHANCED_MEMORY_IMPLEMENTATION.md`
- **基础策略**: `MEMORY_UPDATE_STRATEGY.md`
- **代码文件**: `app/enhanced_memory_strategy.py`

---

**版本**: v2.0  
**更新**: 2025-11-20  
**测试**: ✅ 9+5项全部通过
