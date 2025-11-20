# 多用户、多轮、多语言对话系统

本系统实现了一个完整的多用户、多轮对话和多语言支持的Mem0 API服务，每个用户由唯一的UUID标识。

## 核心功能

### 1. **用户会话管理**
- 每个用户自动分配唯一的UUID
- 追踪用户的会话元数据（创建时间、最后活动时间等）
- 支持用户会话的创建、查询和删除

### 2. **多轮对话支持**
- 每个用户可以进行多轮对话
- 自动记录对话轮次
- 跟踪每轮的时间戳和元数据

### 3. **多语言支持**
- 自动检测用户输入的语言
- 支持中文、英文、日文、韩文、阿拉伯文、俄文、泰文等
- 不同语言使用不同的系统提示词进行事实提取
- 追踪用户使用的所有语言

## API 端点

### 用户会话管理API

#### 创建新用户会话
```http
POST /users/session
Content-Type: application/json

{
  "metadata": {
    "name": "李四",
    "country": "China",
    "role": "Software Engineer"
  }
}
```

**响应示例：**
```json
{
  "status": "success",
  "user_id": "38a5c3be-2aa1-4d1d-9452-15a26001768c",
  "message": "User session created successfully",
  "created_at": "2025-11-19T15:35:36.516511"
}
```

#### 获取用户会话信息
```http
GET /users/{user_id}/session
```

**响应示例：**
```json
{
  "user_id": "38a5c3be-2aa1-4d1d-9452-15a26001768c",
  "created_at": "2025-11-19T15:35:36.516511",
  "last_activity": "2025-11-19T15:36:11.187558",
  "conversation_turns": 4,
  "languages": ["zh"],
  "total_memories": 10,
  "metadata": {
    "name": "李四",
    "country": "China",
    "role": "Software Engineer"
  }
}
```

#### 记录对话轮次
```http
POST /users/{user_id}/conversation-turn
Content-Type: application/json

{
  "user_id": "38a5c3be-2aa1-4d1d-9452-15a26001768c",
  "message_content": "我叫李四，今年28岁，在北京的一家互联网公司担任高级软件工程师。",
  "language": "zh",  # 可选，留空则自动检测
  "metadata": {
    "turn_number": 1,
    "sentiment": "neutral"
  }
}
```

**响应示例：**
```json
{
  "status": "success",
  "user_id": "38a5c3be-2aa1-4d1d-9452-15a26001768c",
  "turn": 1,
  "language": "zh",
  "memory_added": true,
  "session_info": {
    "user_id": "38a5c3be-2aa1-4d1d-9452-15a26001768c",
    "created_at": "2025-11-19T15:35:36.516511",
    "last_activity": "2025-11-19T15:36:11.187558",
    "conversation_turns": 1,
    "languages": ["zh"],
    "total_memories": 3,
    "metadata": {...}
  }
}
```

#### 获取用户记忆摘要
```http
GET /users/{user_id}/memories-summary
```

**响应示例：**
```json
{
  "user_id": "38a5c3be-2aa1-4d1d-9452-15a26001768c",
  "session_created": "2025-11-19T15:35:36.516511",
  "last_activity": "2025-11-19T15:36:11.187558",
  "conversation_turns": 4,
  "languages_used": ["zh"],
  "total_memories": 10,
  "memory_sample": [
    {
      "id": "memory-id-1",
      "memory": "拥有8年的Python开发经验"
    },
    {
      "id": "memory-id-2",
      "memory": "今年28岁"
    }
  ]
}
```

#### 列出所有活跃用户
```http
GET /users/list
```

**响应示例：**
```json
{
  "total_users": 3,
  "users": [
    {
      "user_id": "38a5c3be-2aa1-4d1d-9452-15a26001768c",
      "created_at": "2025-11-19T15:35:36.516511",
      "conversation_turns": 4,
      "languages": ["zh"],
      "total_memories": 10
    },
    {
      "user_id": "ae688003-5017-4d58-a3f0-f479449fe2ec",
      "created_at": "2025-11-19T15:35:36.529443",
      "conversation_turns": 4,
      "languages": ["en"],
      "total_memories": 12
    }
  ]
}
```

#### 删除用户会话
```http
DELETE /users/{user_id}/session
```

**响应示例：**
```json
{
  "status": "success",
  "message": "User session 38a5c3be-2aa1-4d1d-9452-15a26001768c deleted successfully"
}
```

## 测试脚本

### 1. 多用户多语言多轮对话测试
```bash
cd tests
uv run test_multilingual_multiuser.py
```

这个脚本演示了：
- 创建3个不同语言的用户
- 每个用户进行3轮对话
- 自动语言检测和多语言支持
- 记忆搜索和检索

**功能演示：**
- 中文用户(李四)：个人介绍、技能经验、个人爱好
- 英文用户(John)：个人介绍、职业背景、兴趣爱好
- 混合语言用户(田中太郎)：日文、英文、中文混合对话

### 2. 用户会话管理高级测试
```bash
cd tests
uv run test_user_session_management.py
```

这个脚本演示了：
- 创建具有元数据的用户会话
- 记录多轮对话
- 查询用户会话详情
- 获取记忆摘要
- 列出所有活跃用户
- 删除用户会话

**测试统计：**
- 创建3个用户会话
- 每个用户4轮对话
- 自动语言检测和追踪
- 总共32条记忆

## 架构设计

### 用户会话存储
```python
user_sessions: Dict[str, Dict[str, Any]] = {
    "user_uuid": {
        "user_id": "user_uuid",
        "created_at": "ISO_TIMESTAMP",
        "last_activity": "ISO_TIMESTAMP",
        "conversation_turns": int,
        "languages": ["zh", "en", ...],
        "total_memories": int,
        "metadata": {...}
    }
}
```

### 工作流程
1. **创建会话** → 系统生成UUID
2. **记录对话** → 自动检测语言，保存到Mem0
3. **追踪语言** → 更新用户会话的语言列表
4. **更新计数** → 更新对话轮次和记忆数量
5. **查询数据** → 获取用户及其记忆的详细信息

## 语言支持

系统支持以下语言的自动检测和处理：

| 代码 | 语言     | 检测方式                   | 事实提取提示   |
| ---- | -------- | -------------------------- | -------------- |
| zh   | 中文     | Unicode范围: U+4E00-U+9FFF | 中文提示词     |
| en   | 英文     | 字符模式                   | 英文提示词     |
| ja   | 日文     | Unicode范围: U+3040-U+30FF | 日文提示词     |
| ko   | 韩文     | Unicode范围: UAC00-UD7AF   | 韩文提示词     |
| ar   | 阿拉伯文 | Unicode范围: U+0600-U+06FF | 阿拉伯文提示词 |
| ru   | 俄文     | 西里尔字母                 | 俄文提示词     |
| th   | 泰文     | Unicode范围: U+0E00-U+0E7F | 泰文提示词     |

## 数据流示例

### 场景：多语言用户的多轮对话

```
用户: 田中太郎 (user_id: 24748aa1-0e3b-4397-ba65-c4675b4e5ec4)

Turn 1 (日文):
  Input: "こんにちは。私の名前は田中太郎です。"
  Detected Language: ja
  Memory Count: 2
  Languages Tracked: [ja]

Turn 2 (英文):
  Input: "I manage a team of 15 engineers."
  Detected Language: en
  Memory Count: 5
  Languages Tracked: [ja, en]

Turn 3 (中文):
  Input: "我最近在参与全球产品发布。"
  Detected Language: zh
  Memory Count: 7
  Languages Tracked: [ja, en, zh]

Turn 4 (英文):
  Input: "I'm passionate about user research."
  Detected Language: en
  Memory Count: 10
  Languages Tracked: [ja, en, zh]  (no change)

最终会话状态:
  - Total Turns: 4
  - Total Memories: 10
  - Languages: 3 (ja, en, zh)
  - Last Activity: 2025-11-19T15:37:17.995727
```

## 生产环境建议

### 持久化存储
当前实现使用内存存储用户会话。在生产环境中，建议：
- 使用数据库（PostgreSQL、MongoDB等）存储用户会话
- 实现会话持久化到数据库的接口
- 添加会话过期管理

### 认证和授权
- 添加用户认证机制
- 实现访问控制列表（ACL）
- 保护敏感的用户数据

### 扩展性
- 实现会话分片以支持大规模用户
- 添加缓存层（Redis）
- 实现异步任务队列处理记忆存储

## 性能指标

根据测试结果：
- **用户创建速度**: < 10ms
- **对话记录速度**: < 500ms（包括事实提取）
- **会话查询速度**: < 50ms
- **并发支持**: 取决于后端Mem0配置

## 相关文件

- `app/main.py` - 主应用文件，包含所有API端点
- `tests/test_multilingual_multiuser.py` - 多语言多轮对话测试
- `tests/test_user_session_management.py` - 用户会话管理测试

## 反馈和改进

欢迎提交改进建议和bug报告！
