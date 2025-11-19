# 中文事实提取问题解决方案总结

## 问题描述

用户在使用Mem0系统时发现，当输入中文内容时，系统提取出的事实仍然是英文。例如：

**输入**（中文）：
```
我叫李四。我是一名Python后端工程师。
```

**期望输出**（中文）：
```
- 名字是李四
- 是Python后端工程师
```

**实际输出**（英文）：
```
- Name is Li Si
- Is a Python backend engineer
```

用户提出的问题：
> "为什么记得是英文，lisi还能还原为李四么？"
> "根据输入语言来区别使用中文还是英文或者其他语言来生成和提取摘要"

## 根本原因分析

### 1. 向量搜索的语言无关性 ✓ 已验证
- Mem0使用向量数据库（Qdrant）存储和搜索事实
- 向量嵌入模型（ModelArk）创建的向量空间是语言无关的
- 中文查询"李四"可以匹配到英文事实"Li Si"的向量表示
- **结论**：这是特性而非缺陷

### 2. 事实提取的语言问题 ✗ 需要修复
- Mem0使用LLM（Zhipu AI）来提取事实
- LLM的系统提示（system prompt）控制了输出语言
- 原始系统提示是英文，导致所有事实都以英文生成
- **需求**：根据输入语言动态调整系统提示

## 解决方案实现

### 第一步：语言检测 ✓ 完成

实现了基于字符模式匹配的多语言检测：

```python
LANGUAGE_PATTERNS = {
    'zh': re.compile(r'[\u4e00-\u9fff]'),           # 中文字符
    'ja': re.compile(r'[\u3040-\u309f\u30a0-\u30ff]'),  # 日文
    'ko': re.compile(r'[\uac00-\ud7af]'),          # 韩文
    'ar': re.compile(r'[\u0600-\u06ff]'),          # 阿拉伯文
    'ru': re.compile(r'[а-яА-ЯёЁ]'),              # 俄文
    'th': re.compile(r'[\u0e00-\u0e7f]'),          # 泰文
}

def detect_language(text: str) -> str:
    """通过字符频率检测输入文本的语言"""
    language_scores = {}
    for lang, pattern in LANGUAGE_PATTERNS.items():
        matches = len(pattern.findall(text))
        if matches > 0:
            language_scores[lang] = matches
    return max(language_scores, key=language_scores.get) if language_scores else 'en'
```

**支持7种语言**：中文、英文、日文、韩文、阿拉伯文、俄文、泰文

### 第二步：多语言系统提示 ✓ 完成

为每种语言准备特定的系统提示：

```python
LANGUAGE_PROMPTS = {
    'zh': """提取以下中文内容中的关键事实。重要：所有事实必须用中文写出！
...
例如，如果输入是"我叫李四，是个工程师"，则应提取为：
- 名字是李四
- 是工程师""",
    'en': """You are a fact extraction expert. Extract key facts from user input.
...""",
    # 其他语言...
}
```

### 第三步：消息注入策略 ✓ 完成（经过多次迭代）

**尝试1**：使用config中的system_prompt
- ❌ 失败：OpenAI兼容API不支持此参数

**尝试2**：创建临时Memory实例  
- ❌ 失败：Mem0创建新实例成本高，存储分离

**尝试3**：注入system角色消息
- ❌ 失败：Mem0内部有自己的系统提示逻辑，覆盖了注入的

**尝试4**：消息内容注入 ✓ 成功
- 在用户消息前加入语言提示
- Mem0将其视为用户输入的一部分，传给LLM
- LLM根据提示生成相应语言的事实

```python
# 增强的消息构造
enhanced_messages = []
if request.messages:
    first_msg = request.messages[0]
    # 注入语言提示到内容中
    enhanced_content = f"{system_prompt}\n\n[用户输入]\n{first_msg.content}"
    enhanced_messages.append({
        "role": "user",
        "content": enhanced_content
    })
    # 添加剩余消息
    for msg in request.messages[1:]:
        enhanced_messages.append(msg.model_dump())
```

### 第四步：元数据追踪 ✓ 完成

在每个事实的元数据中记录检测到的语言：

```python
result = m.add(
    messages=enhanced_messages,
    user_id=request.user_id,
    metadata={
        **(request.metadata or {}),
        "detected_language": detected_lang  # 记录语言
    }
)
```

## 实现结果

### ✓ 成功：中文输入现在生成中文事实

```json
{
  "results": [
    {
      "memory": "名字是李四",
      "metadata": {
        "detected_language": "zh"
      }
    },
    {
      "memory": "喜欢使用FastAPI框架进行异步编程",
      "metadata": {
        "detected_language": "zh"
      }
    }
  ]
}
```

### ✓ 后向兼容性：英文仍然正常工作

```json
{
  "results": [
    {
      "memory": "Name is John Smith",
      "metadata": {
        "detected_language": "en"
      }
    }
  ]
}
```

### ✓ 跨语言搜索：向量搜索不受语言限制

中文查询可以匹配到英文事实，反之亦然。

## 代码变更

### 修改文件：`app/main.py`

**第39-119行**：添加
- `LANGUAGE_PATTERNS`：语言检测正则表达式
- `LANGUAGE_PROMPTS`：多语言系统提示

**第121-139行**：添加
- `detect_language()`：自动语言检测函数
- `get_system_prompt()`：获取语言提示函数

**第192行**：修改
- 添加可选的`language`字段到`AddMemoryRequest`

**第237-279行**：修改
- 增强`add_memory()`端点以支持多语言

## 测试覆盖

所有功能已通过测试：

```bash
# 中文测试（新增）
cd tests && uv run test_chinese_facts.py
# ✓ 提取了2个事实（中文）
# ✓ 搜索结果包含中文事实
# ✓ 元数据正确记录语言

# 英文测试（回归）
uv run test_api.py
# ✓ 所有现有测试仍然通过
# ✓ 英文输入继续产生英文事实

# 多语言测试（可选）
uv run test_multilingual.py
# ✓ 测试7种语言的支持
```

## 使用指南

### 自动语言检测（推荐）

系统自动检测输入语言，无需额外配置：

```bash
# 中文输入 → 中文事实
curl -X POST http://localhost:8000/memories \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role":"user","content":"我叫李四"}],
    "user_id":"user_001"
  }'
```

### 手动语言指定

如需明确指定语言（覆盖自动检测）：

```bash
curl -X POST http://localhost:8000/memories \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role":"user","content":"..."}],
    "user_id":"user_001",
    "language":"zh"  # 明确指定中文
  }'
```

## 性能考虑

- **语言检测开销**：O(n) 其中n是文本长度，通常 <1ms
- **LLM调用开销**：无额外开销（只是改变了提示内容）
- **向量搜索**：不受影响（与语言无关）

## 局限性和改进空间

### 当前局限
1. **混合语言输入**：多种语言的混合输入使用频率最高的语言
2. **LLM能力**：最终输出受限于LLM的能力（但Zhipu AI表现很好）
3. **方言和变种**：只检测主要语言分类

### 未来改进方向
- [ ] 支持更多语言变体（繁体中文、方言等）
- [ ] 混合语言内容的更智能处理
- [ ] 用户语言偏好设置
- [ ] 事实语言转换API
- [ ] 多语言训练的自定义模型

## 总结

**问题已解决**：
✅ 中文输入现在生成中文事实  
✅ 自动语言检测支持7种语言  
✅ 保持后向兼容性  
✅ 所有测试通过  
✅ 完整的文档和使用指南  

**用户现在可以**：
- 用中文提出事实 → 获得中文事实提取
- 用日文、韩文等输入 → 获得相应语言的事实
- 混合多种语言搜索 → 向量搜索跨越语言边界
- 跟踪每个事实的提取语言 → 通过元数据记录
