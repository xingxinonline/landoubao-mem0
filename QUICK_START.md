# 🚀 快速参考指南 (Quick Start Guide)

## 中文版本

### 核心功能
✅ **自动语言检测**：系统自动识别输入语言  
✅ **多语言事实提取**：用相同语言生成事实  
✅ **跨语言搜索**：无论语言，都能找到相关事实  

### 最简单的使用

```bash
# 1. 启动服务器（如果还没启动）
docker-compose up -d

# 2. 添加中文记忆
curl -X POST http://localhost:8000/memories \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role":"user","content":"我叫张三，是个Python工程师"}],
    "user_id":"user_001"
  }'

# 3. 查看提取的事实（应该是中文）
curl "http://localhost:8000/memories?user_id=user_001"

# 4. 用中文搜索
curl -X POST http://localhost:8000/memories/search \
  -H "Content-Type: application/json" \
  -d '{
    "query":"这个人是做什么的",
    "user_id":"user_001"
  }'
```

### 运行演示

```bash
cd tests
uv run demo_multilingual.py
```

演示展示：
- 中文事实提取（完全中文）
- 英文事实提取（完全英文）
- 跨语言搜索（用中文查询英文数据）
- 元数据跟踪（显示语言记录）

### 支持的语言

| 代码 | 语言 | 示例输入 |
|------|------|---------|
| zh | 中文 | "我叫李四" |
| en | 英文 | "My name is John" |
| ja | 日文 | "私の名前は田中です" |
| ko | 韩文 | "제 이름은 박입니다" |
| ar | 阿拉伯文 | "اسمي محمد" |
| ru | 俄文 | "Меня зовут Иван" |
| th | 泰文 | "ชื่อของฉันคือสมชาย" |

## English Version

### Core Features
✅ **Auto Language Detection**: System automatically detects input language  
✅ **Multilingual Fact Extraction**: Generate facts in the same language  
✅ **Cross-Language Search**: Find related facts regardless of language  

### Simplest Usage

```bash
# 1. Start the server
docker-compose up -d

# 2. Add English memory
curl -X POST http://localhost:8000/memories \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role":"user","content":"My name is Alice, I am a software engineer"}],
    "user_id":"user_002"
  }'

# 3. View extracted facts (should be in English)
curl "http://localhost:8000/memories?user_id=user_002"

# 4. Search in English
curl -X POST http://localhost:8000/memories/search \
  -H "Content-Type: application/json" \
  -d '{
    "query":"What does this person do",
    "user_id":"user_002"
  }'
```

### Run Demo

```bash
cd tests
uv run demo_multilingual.py
```

The demo shows:
- Chinese fact extraction (all facts in Chinese)
- English fact extraction (all facts in English)
- Cross-language search (Chinese query on English data)
- Metadata tracking (language records)

## 文档导航 (Documentation Navigation)

### 主要文档
- 📘 **SOLUTION_SUMMARY.md** - 完整的问题分析和解决方案（最详细）
- 📗 **MULTILINGUAL_FACTS.md** - 使用指南和API示例（最实用）
- 📕 **COMPLETION_REPORT.md** - 功能完成总结（最全面）
- 📙 **README.md** - 项目概述（最简洁）

### 代码
- 🔧 **app/main.py** - 核心实现
- 🧪 **tests/test_chinese_facts.py** - 中文测试
- 🎬 **demo_multilingual.py** - 交互式演示

## 常见问题 (FAQ)

### Q: 为什么我的中文事实还是英文？
A: 可能是旧数据。新的中文输入应该产生中文事实。清除数据库再试：
```bash
curl -X DELETE "http://localhost:8000/memories?user_id=test_user"
```

### Q: 如何强制使用某种语言？
A: 在请求中指定`language`参数：
```bash
curl -X POST http://localhost:8000/memories \
  -d '{"messages":[...], "user_id":"user_001", "language":"zh"}'
```

### Q: 搜索时有语言限制吗？
A: 没有。搜索是向量化的，跨越语言边界。用中文查询可以匹配英文事实。

### Q: 支持混合语言吗？
A: 支持。系统会检测主要语言（出现最频繁的语言）。

## 快速命令 (Quick Commands)

```bash
# 检查服务器状态
curl http://localhost:8000/health

# 清除某个用户的所有数据
curl -X DELETE "http://localhost:8000/memories?user_id=USER_ID"

# 查看所有记忆
curl "http://localhost:8000/memories?user_id=USER_ID"

# 运行所有测试
cd tests && uv run test_api.py && uv run test_chinese_facts.py

# 查看API文档
# 访问：http://localhost:8000/docs
```

## 文件结构 (File Structure)

```
mem0-docker/
├── app/
│   ├── main.py                 # 核心API服务器（包含多语言支持）
│   ├── Dockerfile              # Docker配置
│   └── pyproject.toml          # Python依赖
├── tests/
│   ├── test_api.py             # API基础测试
│   ├── test_chinese_facts.py   # 中文专项测试
│   ├── test_multilingual.py    # 多语言测试
│   └── demo_multilingual.py    # 演示脚本
├── docker-compose.yml          # Docker Compose配置
├── README.md                   # 项目说明
├── SOLUTION_SUMMARY.md         # 解决方案详解
├── MULTILINGUAL_FACTS.md       # 使用指南
└── COMPLETION_REPORT.md        # 完成报告
```

## 获取帮助 (Getting Help)

1. 查看 **SOLUTION_SUMMARY.md** 了解技术细节
2. 查看 **MULTILINGUAL_FACTS.md** 了解使用方法
3. 运行 `demo_multilingual.py` 看实际例子
4. 查看 API 文档：http://localhost:8000/docs

---

**就这样！现在你有了一个完全支持多语言的Mem0系统。** 🎉

享受用你自己的语言提取事实吧！ 🌍
