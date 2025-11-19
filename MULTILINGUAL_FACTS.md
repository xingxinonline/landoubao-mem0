# 多语言事实提取功能说明

## 问题

之前用户发现当使用中文输入时，系统提取出的事实仍然是英文。例如，输入"我叫李四"会提取为"Name is Li Si"（英文）而不是"名字是李四"（中文）。

## 解决方案

已实现**语言自适应事实提取**功能，根据输入语言自动选择提取语言。

### 支持的语言

- **中文 (zh)** - 简体中文
- **English (en)** - 英文  
- **日本語 (ja)** - 日文
- **한국어 (ko)** - 韩文
- **العربية (ar)** - 阿拉伯文
- **Русский (ru)** - 俄文
- **ไทย (th)** - 泰文

### 工作原理

1. **语言检测**：通过正则表达式模式匹配检测输入文本的语言
   - 中文：识别 Unicode 范围 `[\u4e00-\u9fff]`
   - 日文：识别平假名/片假名 `[\u3040-\u309f\u30a0-\u30ff]`
   - 韩文：识别韩文字符 `[\uac00-\ud7af]`
   - 等等...

2. **语言特定提示**：为每种语言准备特定的系统提示，明确告诉LLM用该语言提取事实

3. **消息注入**：在发送给LLM的消息中注入语言提示，确保事实以正确的语言生成

### 使用示例

#### 中文输入

```bash
curl -X POST http://localhost:8000/memories \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "我叫李四。我是一名高级Python后端工程师。我喜欢使用FastAPI框架。"
      }
    ],
    "user_id": "user_zh_001"
  }'
```

**响应**（提取的事实为中文）：
```json
{
  "results": [
    {
      "memory": "名字是李四"  // ✓ 中文
    },
    {
      "memory": "喜欢使用FastAPI框架"  // ✓ 中文
    }
  ]
}
```

#### 英文输入

```bash
curl -X POST http://localhost:8000/memories \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "My name is John Smith. I am a senior Python backend engineer. I love using FastAPI."
      }
    ],
    "user_id": "user_en_001"
  }'
```

**响应**（提取的事实为英文）：
```json
{
  "results": [
    {
      "memory": "Name is John Smith"  // ✓ English
    },
    {
      "memory": "Likes using FastAPI"  // ✓ English
    }
  ]
}
```

### 手动语言指定

如果需要，可以手动指定语言而不依赖自动检测：

```bash
curl -X POST http://localhost:8000/memories \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "..."
      }
    ],
    "user_id": "user_001",
    "language": "zh"  // 明确指定中文
  }'
```

### 元数据追踪

每个提取的事实都会在元数据中记录检测到的语言：

```bash
curl http://localhost:8000/memories?user_id=user_zh_001
```

**响应包含**：
```json
{
  "results": [
    {
      "memory": "名字是李四",
      "metadata": {
        "detected_language": "zh"  // 记录的语言
      }
    }
  ]
}
```

### 搜索支持

无论事实以哪种语言提取，搜索都支持跨语言匹配（基于向量嵌入）：

```bash
// 用中文查询
curl -X POST http://localhost:8000/memories/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "这个人使用什么框架",  // 中文查询
    "user_id": "user_zh_001"
  }'

// 返回匹配的事实（可能是中文或英文）
```

## 实现细节

### 代码位置
- `app/main.py` - 主实现
  - 第 39-75 行：`LANGUAGE_PATTERNS` - 语言检测正则表达式
  - 第 77-119 行：`LANGUAGE_PROMPTS` - 每种语言的系统提示
  - 第 121-135 行：`detect_language()` - 语言检测函数
  - 第 137-139 行：`get_system_prompt()` - 获取语言提示
  - 第 237-279 行：`add_memory()` - 增强的内存添加端点

### 系统提示示例

中文提示：
```
提取以下中文内容中的关键事实。重要：所有事实必须用中文写出！
从给定的文本中提取具体的、可验证的事实。每个事实应该是：
- 简洁的中文陈述
- 现在时或一般时
- 避免冗余

例如，如果输入是"我叫李四，是个工程师"，则应提取为：
- 名字是李四
- 是工程师
```

## 测试

### 运行测试

```bash
# 中文测试
cd tests && uv run test_chinese_facts.py

# 完整的多语言测试
uv run test_multilingual.py

# API基础测试
uv run test_api.py
```

### 测试覆盖

- ✓ 中文输入 → 中文事实提取
- ✓ 英文输入 → 英文事实提取  
- ✓ 日文输入 → 日文事实提取
- ✓ 跨语言搜索
- ✓ 元数据记录
- ✓ 后向兼容性

## 限制和注意事项

1. **语言检测准确性**：混合多种语言的输入会根据字符频率检测主要语言
2. **LLM限制**：最终的事实语言取决于LLM（Zhipu AI）的执行
3. **向量化**：嵌入模型（ModelArk）用于搜索，与提取语言无关

## 未来改进

- [ ] 支持更多语言
- [ ] 语言混合输入的更智能处理
- [ ] 用户语言偏好设置
- [ ] 事实语言转换API
