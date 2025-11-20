# 个人助理快速启动指南

## 概述

这个个人助理系统是一个集成MCP Server记忆模块的大模型对话应用，具有以下特点：

- ✅ **智能对话**: 使用Zhipu AI (GLM-4-Flash) 提供流畅的中英文对话
- 📝 **自动记忆**: 通过MCP Server保存、搜索和管理用户信息
- 🧠 **上下文感知**: 自动在对话中融合之前的记忆信息
- 🌍 **多语言支持**: 自动检测和处理中文、英文、日文等多语言
- 💾 **灵活存储**: 支持手动和自动保存重要信息
- 🔍 **记忆搜索**: 快速搜索相关的历史记忆

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                   Personal Assistant (CLI)                   │
│  - 对话管理                                                  │
│  - 记忆交互                                                  │
│  - 用户界面                                                  │
└──────────────┬──────────────────────┬───────────────────────┘
               │                      │
       ┌───────▼────────┐     ┌───────▼──────────┐
       │  OpenAI Client │     │ MCP Server Client │
       │  (LLM Calls)   │     │ (Memory Ops)     │
       └───────┬────────┘     └───────┬──────────┘
               │                      │
       ┌───────▼────────┐     ┌───────▼──────────┐
       │  Zhipu AI      │     │  MCP HTTP Server │
       │  GLM-4-Flash   │     │  Port 8001       │
       └────────────────┘     └───────┬──────────┘
                                      │
                            ┌─────────▼───────┐
                            │  Mem0 Memory    │
                            │  Qdrant Vector  │
                            │  Store          │
                            └─────────────────┘
```

## 安装步骤

### 1. 环境准备

```bash
# 进入项目目录
cd d:\landoubao-mem0

# 安装依赖
pip install openai requests

# 如果使用 uv 包管理器
uv pip install openai requests
```

### 2. 配置API密钥

编辑 `.env` 文件或设置环境变量：

```bash
# Windows PowerShell
$env:ZHIPU_API_KEY = "your_zhipu_api_key"
$env:MCP_SERVER_URL = "http://localhost:8001"
$env:LLM_MODEL = "glm-4-flash-250414"
$env:LLM_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
```

或者创建 `.env` 文件：

```env
ZHIPU_API_KEY=your_zhipu_api_key
MODELARK_API_KEY=your_modelark_api_key
QDRANT_HOST=115.190.24.157
QDRANT_PORT=6333
MCP_SERVER_URL=http://localhost:8001
LLM_MODEL=glm-4-flash-250414
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
```

### 3. 启动MCP Server

确保MCP Server在后台运行：

```bash
# 使用docker-compose
docker-compose up -d mcp-http

# 或者直接运行Python
python app/mcp_server_http.py
```

验证服务可用：
```bash
curl http://localhost:8001/health
```

### 4. 运行个人助理

```bash
# 进入交互模式
python app/personal_assistant.py
```

## 使用指南

### 基础对话

```
👤 你: 你好，我叫王老五，我是一名产品经理
🤖 助理: 很高兴认识你，王老五！产品经理是一个很有挑战性的职位...
👤 你: /save
💾 自动保存: 开启
```

### 可用命令

| 命令               | 说明         | 示例               |
| ------------------ | ------------ | ------------------ |
| `/help`            | 显示帮助信息 | `/help`            |
| `/memories`        | 列出所有记忆 | `/memories`        |
| `/search <关键词>` | 搜索记忆     | `/search 产品经理` |
| `/stats`           | 显示记忆统计 | `/stats`           |
| `/save`            | 切换自动保存 | `/save`            |
| `/clear`           | 清空对话历史 | `/clear`           |
| `/exit`            | 退出程序     | `/exit`            |

### 示例工作流

```
1. 启动助理
   python app/personal_assistant.py

2. 加载记忆
   /memories

3. 启用自动保存
   /save

4. 进行对话
   👤 你: 我最近在做一个新项目...
   🤖 助理: 基于你之前的经验，我建议...

5. 搜索相关记忆
   /search 项目管理

6. 查看统计
   /stats

7. 退出
   /exit
```

## 高级用法

### 以编程方式使用

```python
from app.personal_assistant import PersonalAssistant

# 创建助理实例
assistant = PersonalAssistant(user_id="user_123")

# 加载记忆
assistant.load_memories()

# 进行对话（带自动保存）
response = assistant.chat("我今天很开心", save_memory=True)
print(response)

# 搜索记忆
memories = assistant.search_memories("心情")

# 获取统计
stats = assistant.get_memory_stats()
print(stats)
```

### 异步模式

```python
import asyncio
from app.personal_assistant import PersonalAssistant

async def main():
    assistant = PersonalAssistant()
    
    responses = []
    for msg in ["你好", "你叫什么", "你能做什么"]:
        resp = await asyncio.to_thread(assistant.chat, msg)
        responses.append(resp)
    
    return responses

asyncio.run(main())
```

### 自定义系统提示

```python
assistant = PersonalAssistant()

# 修改系统提示词
custom_prompt = """
你是一个专业的技术顾问...
"""
assistant.SYSTEM_PROMPT = custom_prompt

# 然后进行对话
response = assistant.chat("告诉我关于微服务的最佳实践")
```

## 功能特性详解

### 1. 自动语言检测

系统自动检测输入语言并在记忆中保存：

```python
# 中文输入 - 自动识别为中文
assistant.chat("我叫李明，是个工程师", save_memory=True)

# 英文输入 - 自动识别为英文
assistant.chat("My name is John, I'm an engineer", save_memory=True)
```

### 2. 上下文感知对话

助理在生成回答前自动加载相关记忆：

```
之前保存: "我是产品经理，专注于用户体验"
用户问: "你能帮我改进这个界面吗？"
助理回: "根据你的产品管理背景，我建议从用户调研开始..."
```

### 3. 记忆管理

```python
# 查看所有记忆
memories = assistant.context.memories

# 搜索特定记忆
results = assistant.search_memories("工作经验")

# 获取统计信息
stats = assistant.get_memory_stats()
# 输出: {'user_id': '...', 'total_memories': 45, 'timestamp': '...'}

# 删除特定记忆
assistant.mcp_client.delete_memory("memory_id")

# 清空用户所有记忆
assistant.mcp_client.delete_all_memories(assistant.user_id)
```

## 故障排查

### 问题1: MCP Server连接失败

**症状**: `⚠️  警告: MCP Server不可用，记忆功能将被禁用`

**解决方案**:
```bash
# 检查MCP Server是否运行
curl http://localhost:8001/health

# 启动MCP Server
python app/mcp_server_http.py

# 或使用docker
docker-compose up -d mcp-http
```

### 问题2: API密钥错误

**症状**: `❌ 对话失败: Invalid API key`

**解决方案**:
```bash
# 检查环境变量
echo $env:ZHIPU_API_KEY

# 重新设置密钥
$env:ZHIPU_API_KEY = "your_correct_key"

# 或编辑 .env 文件
```

### 问题3: 记忆保存失败

**症状**: `⚠️  保存记忆失败`

**解决方案**:
```bash
# 检查Qdrant连接
curl http://115.190.24.157:6333/health

# 查看MCP Server日志
docker logs mcp-http

# 检查环境变量
echo $env:QDRANT_HOST
echo $env:QDRANT_PORT
```

## 性能优化建议

1. **对话历史管理**: 系统默认保留最近10条消息，避免上下文过长

2. **记忆加载**: 默认加载100条记忆，可根据需要调整：
   ```python
   assistant.load_memories(limit=50)
   ```

3. **记忆搜索**: 搜索时默认返回5条结果：
   ```python
   results = assistant.search_memories("query", limit=10)
   ```

4. **API超时**: 默认超时30秒，可自定义：
   ```python
   mcp_client = MCPServerClient(timeout=60)
   ```

## 安全建议

1. ✅ 不要在代码中硬编码API密钥，使用环境变量
2. ✅ 定期检查和清理敏感记忆
3. ✅ 使用用户ID隔离不同用户的数据
4. ✅ 在生产环境启用HTTPS和身份认证

## API文档

### PersonalAssistant 类

#### 初始化
```python
assistant = PersonalAssistant(
    user_id: str = None,  # 用户ID，自动生成UUID
    model: str = "glm-4-flash-250414",  # 大模型
    api_key: str = "your_key"  # API密钥
)
```

#### 主要方法

| 方法                                   | 说明     | 返回值     |
| -------------------------------------- | -------- | ---------- |
| `chat(input, save_memory)`             | 进行对话 | str        |
| `load_memories(limit)`                 | 加载记忆 | List[Dict] |
| `search_memories(query)`               | 搜索记忆 | List[Dict] |
| `save_memory(user_msg, assistant_msg)` | 保存对话 | bool       |
| `get_memory_stats()`                   | 获取统计 | Dict       |
| `interactive_mode()`                   | 交互模式 | None       |

### MCPServerClient 类

#### 主要方法

| 方法                            | 说明             |
| ------------------------------- | ---------------- |
| `add_memory(messages, user_id)` | 添加记忆         |
| `search_memory(query, user_id)` | 搜索记忆         |
| `get_all_memories(user_id)`     | 获取所有记忆     |
| `delete_memory(memory_id)`      | 删除记忆         |
| `delete_all_memories(user_id)`  | 删除用户所有记忆 |
| `get_memory_stats(user_id)`     | 获取统计         |
| `create_user_session(metadata)` | 创建会话         |
| `detect_language(text)`         | 检测语言         |

## 日志和调试

启用详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)

assistant = PersonalAssistant()
assistant.chat("你好")
```

## 下一步

- 集成更多大模型（如OpenAI GPT-4、Claude等）
- 添加语音输入/输出支持
- 实现Web UI界面
- 支持多用户并发
- 添加任务管理功能
- 集成日历、邮件等外部服务

## 支持和反馈

如有问题，请检查：
1. 日志输出
2. 环境变量配置
3. 网络连接
4. MCP Server状态
