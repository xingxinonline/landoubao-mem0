# 常见问题：为什么提取的是英文？

## 问题回顾

> **Q: 为什么记得是英文，lisi还能还原为李四么？**

输入中文：`"我叫李四。我是Python后端工程师。我喜欢使用FastAPI框架。"`

系统提取的是英文事实：
- `"Name is Li Si"` 而不是 `"我叫李四"`
- `"Is a Python backend engineer"` 而不是 `"是Python后端工程师"`

## 答案简述

### 1️⃣ 为什么提取英文？
**LLM 模型的语言倾向** - `glm-4-flash-250414` 接收中文后，自然输出英文事实。这是模型的特性。

### 2️⃣ "Li Si" 能还原为 "李四" 吗？
**不能精确还原，但能通过语义匹配找到。**

关键是：**向量空间是语言无关的！**

```
中文查询：        英文事实：
"李四做什么"  ←→  "Name is Li Si"
    ↓                  ↓
  向量化          向量化
    ↓                  ↓
  向量1   相似度0.467   向量2

因为语义相同，两个向量在高维空间中相邻！
```

## 实际测试结果 ✅

### 中文输入 + 中文查询
```python
# 输入（中文）
messages = "我叫李四。我是Python后端工程师。我喜欢使用FastAPI框架。"

# 提取结果（英文）
[
    "Name is Li Si",
    "Is a Python backend engineer",
    "Likes using FastAPI framework"
]

# 查询（中文）
query = "李四做什么工作"

# 搜索结果 ✓
{
    "score": 0.4674,
    "memory": "Name is Li Si"        ← 找到了！
}
```

## 多语言搜索工作原理

```
┌─────────────────────────────────────┐
│   用户输入（任何语言）              │
│   Chinese: "李四是谁"               │
│   English: "Who is Li Si"           │
│   Japanese: "リスは誰"              │
└──────────────┬──────────────────────┘
               ↓
        ┌─────────────┐
        │  向量化     │  (语言无关)
        └──────┬──────┘
               ↓
        ┌─────────────┐
        │  向量空间   │  "Name is Li Si"
        │   搜索      │  的向量附近
        └──────┬──────┘
               ↓
        ┌─────────────────────┐
        │ 返回匹配的事实      │
        │ "Name is Li Si"     │  ✓
        │ 相似度: 0.467       │
        └─────────────────────┘
```

## 为什么这很强大？

✅ **优势**
1. **真正的多语言支持** - 用任何语言查询都工作
2. **语义匹配** - "李四" 和 "Li Si" 被识别为相同的人
3. **跨文化应用** - 一个系统服务多个语言用户
4. **标准化存储** - 英文事实更易集成其他系统

⚠️ **限制**
1. 事实仍是英文，用户需要理解英文
2. 无法自动翻译为本地语言
3. 如果坚持中文事实，需要修改 LLM 提示词

## 如果需要中文事实？

### 快速方案：修改 Mem0 配置

在 `app/main.py` 中，修改 LLM 配置：

```python
config = {
    "llm": {
        "config": {
            "system_prompt": "你是一个事实提取助手。请用中文提取清晰简洁的事实。不要使用英文。"
            # ... 其他配置
        }
    }
}
```

然后重启容器：
```bash
docker-compose restart
```

### 完整修改示例

如果想完整支持中文提示词，修改 `app/main.py` 中的 config：

```python
# 原来的配置
config = {
    "llm": {
        "provider": LLM_PROVIDER,
        "config": {
            "model": LLM_MODEL,
            "api_key": ZHIPU_API_KEY,
            "openai_base_url": LLM_BASE_URL,
            "temperature": LLM_TEMPERATURE,
            "max_tokens": LLM_MAX_TOKENS
        }
    }
}

# 修改为支持中文提示词
config = {
    "llm": {
        "provider": LLM_PROVIDER,
        "config": {
            "model": LLM_MODEL,
            "api_key": ZHIPU_API_KEY,
            "openai_base_url": LLM_BASE_URL,
            "temperature": LLM_TEMPERATURE,
            "max_tokens": LLM_MAX_TOKENS,
            "system_prompt": "你是一个信息提取专家。请从用户输入中提取关键事实。"
                            "始终用简洁的中文提取事实。每个事实应该是一句简单陈述。"
        }
    }
}
```

## 总结

| 问题 | 答案 |
|------|------|
| **为什么提取英文？** | LLM 的语言特性，模型倾向英文输出 |
| **李四能还原吗？** | 不能精确还原，但能语义匹配找到 |
| **中文查询能工作吗？** | ✅ 完全支持，向量搜索语言无关 |
| **怎么变成中文提取？** | 修改 LLM 的系统提示词 |

## 测试参考

运行这个命令可以自己测试：

```bash
cd tests
uv run test_chinese_extraction.py
```

你会看到：
- 中文输入 ➜ 英文事实提取
- 中文查询 ➜ 成功找到英文事实
- 英文查询 ➜ 同样成功
