# 快速入门 - 多用户多语言对话系统

## 一分钟快速开始

### 1. 启动系统
```bash
docker-compose up -d --build
```

### 2. 验证系统运行
```bash
curl http://localhost:8000/health
```

### 3. 运行测试
```bash
cd tests
uv run test_user_session_management.py
```

## 最小化示例

### Python示例

```python
import requests
import uuid

API_URL = "http://localhost:8000"

# Step 1: 创建用户会话
response = requests.post(
    f"{API_URL}/users/session",
    json={"metadata": {"name": "Alice", "role": "Developer"}}
)
user_id = response.json()["user_id"]
print(f"User created: {user_id}")

# Step 2: 记录对话轮次
response = requests.post(
    f"{API_URL}/users/{user_id}/conversation-turn",
    json={
        "user_id": user_id,
        "message_content": "Hello! My name is Alice. I work as a software engineer.",
        "language": "en"
    }
)
print(f"Turn 1 recorded: {response.json()['turn']}")

# Step 3: 再来一轮对话
response = requests.post(
    f"{API_URL}/users/{user_id}/conversation-turn",
    json={
        "user_id": user_id,
        "message_content": "I have 5 years of experience in Python development."
    }
)
print(f"Turn 2 recorded: {response.json()['turn']}")

# Step 4: 获取用户会话信息
response = requests.get(f"{API_URL}/users/{user_id}/session")
session = response.json()
print(f"\nSession Info:")
print(f"  Turns: {session['conversation_turns']}")
print(f"  Languages: {session['languages']}")
print(f"  Memories: {session['total_memories']}")

# Step 5: 获取记忆摘要
response = requests.get(f"{API_URL}/users/{user_id}/memories-summary")
summary = response.json()
print(f"\nMemories Summary:")
print(f"  Total Memories: {summary['total_memories']}")
if summary['memory_sample']:
    print(f"  Sample Memory: {summary['memory_sample'][0]['memory']}")
```

### cURL 示例

```bash
# 创建用户会话
curl -X POST http://localhost:8000/users/session \
  -H "Content-Type: application/json" \
  -d '{"metadata": {"name": "Bob"}}'

# 记录对话（假设user_id为abc123）
curl -X POST http://localhost:8000/users/abc123/conversation-turn \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "abc123",
    "message_content": "我是Bob，来自北京",
    "language": "zh"
  }'

# 获取会话信息
curl http://localhost:8000/users/abc123/session

# 列出所有用户
curl http://localhost:8000/users/list
```

## 常见场景

### 场景 1: 多语言用户

```python
# 用户可以混合使用多种语言
turns = [
    "Hello, I am from Japan",  # 自动检测: en
    "私の名前は田中です",       # 自动检测: ja
    "我在学习编程",             # 自动检测: zh
    "I love programming"        # 自动检测: en
]

for turn_idx, message in enumerate(turns, 1):
    requests.post(
        f"{API_URL}/users/{user_id}/conversation-turn",
        json={
            "user_id": user_id,
            "message_content": message
            # 不指定language，让系统自动检测
        }
    )
    print(f"Turn {turn_idx} recorded")
```

### 场景 2: 批量创建用户

```python
num_users = 100
users = []

for i in range(num_users):
    response = requests.post(
        f"{API_URL}/users/session",
        json={"metadata": {"user_number": i+1}}
    )
    user_id = response.json()["user_id"]
    users.append(user_id)

print(f"Created {len(users)} users")

# 查看所有用户
response = requests.get(f"{API_URL}/users/list")
print(f"Total users: {response.json()['total_users']}")
```

### 场景 3: 分析用户统计

```python
response = requests.get(f"{API_URL}/users/list")
data = response.json()

total_turns = sum(u['conversation_turns'] for u in data['users'])
total_memories = sum(u['total_memories'] for u in data['users'])
all_languages = set()

for user in data['users']:
    all_languages.update(user['languages'])

print(f"Statistics:")
print(f"  Total Users: {data['total_users']}")
print(f"  Total Turns: {total_turns}")
print(f"  Total Memories: {total_memories}")
print(f"  Languages: {', '.join(sorted(all_languages))}")
```

## 测试脚本说明

### test_multilingual_multiuser.py
- 演示3个不同语言的用户
- 每个用户3轮对话
- 展示记忆搜索功能

```bash
uv run test_multilingual_multiuser.py
```

### test_user_session_management.py
- 演示完整的会话管理API
- 3个用户，每个4轮对话
- 包括创建、查询、删除操作
- 最后显示统计信息

```bash
uv run test_user_session_management.py
```

## 调试技巧

### 查看容器日志
```bash
docker logs mem0-server -f
```

### 健康检查
```bash
curl http://localhost:8000/health
```

### 重启容器
```bash
docker-compose restart
```

### 查看所有用户
```bash
curl http://localhost:8000/users/list | python -m json.tool
```

### 清理（删除所有用户）
```bash
# 获取所有用户
users=$(curl -s http://localhost:8000/users/list | python -c "import sys, json; print('\n'.join([u['user_id'] for u in json.load(sys.stdin)['users']]))")

# 删除每个用户
for user_id in $users; do
  curl -X DELETE http://localhost:8000/users/$user_id/session
done
```

## 常见问题

**Q: 如何修改用户元数据？**
A: 当前版本不支持修改元数据。可以删除用户会话后重新创建。

**Q: 数据会持久化吗？**
A: 用户会话信息存储在内存中，容器重启后会丢失。建议使用数据库进行持久化。

**Q: 如何处理大量用户？**
A: 在生产环境中，应该使用数据库替代内存存储，并实现分页等优化。

**Q: 支持多少种语言？**
A: 系统支持自动检测中文、英文、日文、韩文、阿拉伯文、俄文、泰文等多种语言。

**Q: 如何获取用户的所有记忆？**
A: 可以使用 `/users/{user_id}/memories-summary` 端点获取记忆摘要，或使用原有的 `/memories/search` 端点进行高级查询。

## 性能优化建议

1. **缓存用户会话**：使用Redis缓存活跃用户
2. **数据库连接池**：使用连接池管理数据库连接
3. **异步处理**：使用异步任务队列处理长耗时操作
4. **索引优化**：为frequently-queried字段创建数据库索引

## 下一步

- 查看 `MULTIUSER_MULTILINGUAL_GUIDE.md` 了解完整API文档
- 查看 `app/main.py` 了解实现细节
- 运行测试脚本进行功能验证
- 根据需要自定义系统配置

祝你使用愉快！ 🚀
