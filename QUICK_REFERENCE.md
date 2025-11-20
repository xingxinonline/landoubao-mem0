# 快速参考卡 - 个人助理系统

## 🚀 30秒快速启动

```bash
# 1. 设置API密钥
$env:ZHIPU_API_KEY = "your_key"

# 2. 启动系统
python start_assistant.py

# 3. 打开浏览器
http://localhost:8002/static/index.html
```

---

## 📱 三种使用方式

### 命令行 CLI
```bash
python app/personal_assistant.py
```
**命令:**
- `/save` - 启用自动保存
- `/memories` - 查看记忆
- `/search 关键词` - 搜索
- `/stats` - 统计
- `/exit` - 退出

### Web浏览器
```
http://localhost:8002/static/index.html
```
**特点:** 现代化界面，即时对话，自动保存

### HTTP API
```bash
# 创建会话
curl -X POST http://localhost:8002/api/session

# 对话
curl -X POST http://localhost:8002/api/chat \
  -d '{"message":"你好","user_id":"...","save_memory":true}'
```

---

## 🔧 常用配置

### 环境变量
```bash
$env:ZHIPU_API_KEY = "your_key"           # 必须
$env:MCP_SERVER_URL = "http://localhost:8001"  # 可选
$env:LLM_MODEL = "glm-4-flash-250414"     # 可选
```

### 修改端口
```python
# 在代码中修改
uvicorn.run(app, port=8002)  # Web API
# 或
PORT=9000 python app/personal_assistant_web.py
```

---

## 📝 常用代码片段

### Python使用
```python
from app.personal_assistant import PersonalAssistant

# 创建助理
assistant = PersonalAssistant()

# 对话并保存
response = assistant.chat("你好", save_memory=True)

# 搜索记忆
results = assistant.search_memories("工作")

# 查看统计
stats = assistant.get_memory_stats()

# 进入交互模式
assistant.interactive_mode()
```

### API调用
```python
import requests

BASE = "http://localhost:8002/api"

# 创建会话
user = requests.post(f"{BASE}/session").json()
user_id = user["user_id"]

# 对话
requests.post(f"{BASE}/chat", json={
    "message": "你好",
    "user_id": user_id,
    "save_memory": True
})

# 搜索
requests.get(f"{BASE}/search?user_id={user_id}&query=工作")
```

---

## 🔍 故障排查

| 问题           | 命令                                |
| -------------- | ----------------------------------- |
| MCP Server检查 | `curl http://localhost:8001/health` |
| Web API检查    | `curl http://localhost:8002/health` |
| 查看日志       | 控制台输出                          |
| 重启服务       | `Ctrl+C` 然后重新运行               |

---

## 📊 服务端口

| 服务       | 端口        | 说明     |
| ---------- | ----------- | -------- |
| MCP Server | 8001        | 记忆服务 |
| Web API    | 8002        | HTTP接口 |
| Web界面    | 8002/static | 前端UI   |

---

## 🎯 常见任务

### 任务1: 保存重要信息
```
输入: 我叫张三，是个产品经理
输入: /save
↓
信息已保存到记忆库
```

### 任务2: 搜索相关信息
```
输入: /search 产品
↓
显示所有相关记忆
```

### 任务3: 查看统计信息
```
输入: /stats
↓
显示: 总对话数、记忆数等
```

### 任务4: 启用自动保存
```
输入: /save
↓
之后每条消息自动保存到记忆
```

---

## 💡 最佳实践

1. **开始前加载记忆** - 帮助AI理解你的背景
   ```
   /memories
   ```

2. **提供清晰的信息** - 包含具体的细节
   ```
   ✅ 好: "我在一家互联网公司做产品经理，管理15人团队"
   ❌ 差: "我是产品经理"
   ```

3. **定期搜索记忆** - 检查保存的信息
   ```
   /search 工作经验
   ```

4. **关键信息手动保存** - 确保重要信息被记录
   ```
   /save (启用自动保存)
   ```

---

## 🔐 安全建议

- ✅ 使用环境变量存储API密钥
- ✅ 定期检查和清理敏感记忆
- ✅ 不同用户使用不同user_id
- ✅ 在生产环境启用HTTPS

---

## 📚 进一步阅读

| 文档                          | 内容         |
| ----------------------------- | ------------ |
| `COMPLETE_MANUAL.md`          | 完整用户手册 |
| `PERSONAL_ASSISTANT_GUIDE.md` | 快速启动指南 |
| `PROJECT_DELIVERY.md`         | 项目交付清单 |
| `http://localhost:8002/docs`  | API交互文档  |

---

## 🆘 快速获帮

**问题: 对话无响应**
```bash
# 1. 检查API密钥
echo $env:ZHIPU_API_KEY

# 2. 检查网络
curl https://open.bigmodel.cn

# 3. 重启服务
python start_assistant.py
```

**问题: 记忆无法保存**
```bash
# 1. 检查MCP Server
curl http://localhost:8001/health

# 2. 启动MCP Server
python app/mcp_server_http.py

# 3. 检查Qdrant
curl http://115.190.24.157:6333/health
```

**问题: 性能缓慢**
```bash
# 1. 减少记忆加载
assistant.load_memories(limit=50)

# 2. 检查系统资源
tasklist | grep python

# 3. 重启应用
```

---

## 📈 升级和维护

### 更新依赖
```bash
pip install --upgrade openai fastapi uvicorn
```

### 清理旧数据
```python
# 清除所有记忆
assistant.mcp_client.delete_all_memories(assistant.user_id)
```

### 备份记忆
```python
# 导出所有记忆
memories = assistant.load_memories(limit=10000)
import json
with open("backup.json", "w") as f:
    json.dump(memories, f)
```

---

## 🎓 示例对话

### 场景1: 知识积累
```
👤: 我叫李明，我是后端开发
🤖: 很高兴认识你！...

👤: /save

👤: 最近在学Golang
🤖: (融合记忆) 作为后端开发，学习Golang是个...

👤: 推荐一些最佳实践
🤖: (使用记忆信息) 对于像你这样的后端开发...
```

### 场景2: 项目协助
```
👤: 我们在做一个电商平台
🤖: 很感兴趣！...

👤: /save

👤: 现在遇到并发问题
🤖: (融合记忆) 在电商平台开发中，并发问题...

👤: 你的建议很有帮助！
🤖: 高兴能帮助！(已记录此对话)
```

---

## 🚀 下一步行动

- [ ] 运行 `python start_assistant.py`
- [ ] 打开 `http://localhost:8002/static/index.html`
- [ ] 进行第一次对话
- [ ] 尝试 `/save` 保存信息
- [ ] 尝试 `/search` 搜索记忆
- [ ] 探索Web API (打开 `/docs`)
- [ ] 读完 `COMPLETE_MANUAL.md`
- [ ] 自定义系统提示词

---

**准备好了吗？开始你的AI对话之旅吧！** 🚀

```bash
python start_assistant.py
```
