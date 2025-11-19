# Mem0 Local Docker Deployment

这是一个完整的 Mem0 记忆系统 Docker 部署，集成了智谱 AI (LLM)、模力方舟 (Embedding) 和 Qdrant (向量数据库)。

## 功能特性

- ✅ **Mem0 记忆系统** - 自适应记忆引擎，自动提取和更新事实
- ✅ **智谱 AI LLM** - `glm-4-flash-250414` 模型用于事实提取
- ✅ **模力方舟 Embedding** - 可配置嵌入模型（`Qwen3-Embedding-0.6B` 低资源 / `Qwen3-Embedding-8B` 高质量）
- ✅ **Qdrant 向量数据库** - 高性能向量存储 (`115.190.24.157:6333`)
- ✅ **FastAPI REST API** - 完整的 CRUD 操作接口
- ✅ **异步多并发** - 支持高并发请求
- ✅ **交互式文档** - Swagger UI 在 `/docs`
- ✅ **UV 包管理** - 快速的 Python 依赖管理

## 快速开始

### 前置条件

- Docker 和 Docker Compose
- 智谱 AI API Key
- 模力方舟 API Key

### 1. 配置 API Keys 和嵌入模型

编辑 `app/.env` 文件：

```env
ZHIPU_API_KEY=your_zhipu_api_key
MODELARK_API_KEY=your_modelark_api_key
QDRANT_HOST=115.190.24.157
QDRANT_PORT=6333

# 嵌入模型配置（可选）
# 使用 Qwen3-Embedding-0.6B 以降低 Qdrant 资源占用（推荐用于生产环境）
EMBEDDING_MODEL=Qwen3-Embedding-0.6B
EMBEDDING_DIMS=1024

# 或使用 Qwen3-Embedding-8B 获得更高的嵌入质量（需要更多资源）
# EMBEDDING_MODEL=Qwen3-Embedding-8B
# EMBEDDING_DIMS=4096
```

### 2. 启动服务

```bash
docker-compose up -d
```

服务将在 `http://localhost:8000` 启动。

### 3. 查看 API 文档

打开浏览器访问：**http://localhost:8000/docs**

## API 端点

### 健康检查
```http
GET /health
```
返回服务状态和 Mem0 初始化状态。

### 添加记忆
```http
POST /memories
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "我叫张三，是一名 Python 工程师。"}
  ],
  "user_id": "user_123",
  "metadata": {"category": "profile"}
}
```

Mem0 将自动分解输入为结构化的事实。

### 搜索记忆
```http
POST /memories/search
Content-Type: application/json

{
  "query": "张三是做什么工作的？",
  "user_id": "user_123",
  "limit": 5
}
```

返回相关的记忆及相关性评分。

### 获取所有记忆
```http
GET /memories?user_id=user_123
```

### 删除单条记忆
```http
DELETE /memories/{memory_id}
```

### 重置用户记忆
```http
DELETE /memories?user_id=user_123
```

### 重置所有 Qdrant 集合 (管理员)
```http
POST /admin/reset-collections
```

**何时使用：** 当更改 `EMBEDDING_DIMS` 时，需要重置所有向量集合（因为不同维度的向量不兼容）。

**工作流：**
1. 修改 `app/.env` 中的 `EMBEDDING_MODEL` 和 `EMBEDDING_DIMS`
2. 调用 `/admin/reset-collections` 清除旧向量
3. 重启容器：`docker-compose restart`
4. Mem0 将自动以新维度创建集合

**示例响应：**
```json
{
  "status": "success",
  "message": "Reset 3 Qdrant collections",
  "deleted_collections": ["mem0", "mem0migrations", "test_collection"]
}
```

## 嵌入模型配置

### 模型选择

| 模型                   | 维度 | Qdrant 存储   | 质量 | 推荐场景                   |
| ---------------------- | ---- | ------------- | ---- | -------------------------- |
| `Qwen3-Embedding-0.6B` | 1024 | ~256MB/1M向量 | 中等 | **生产环境（资源受限）** ✅ |
| `Qwen3-Embedding-8B`   | 4096 | ~1GB/1M向量   | 高   | 开发/小规模部署            |

### 切换嵌入模型步骤

```bash
# 1. 编辑 app/.env
# EMBEDDING_MODEL=Qwen3-Embedding-8B
# EMBEDDING_DIMS=4096

# 2. 重置集合
curl -X POST http://localhost:8000/admin/reset-collections

# 3. 重启服务
docker-compose restart

# 4. 等待 Mem0 重新初始化（观察日志）
docker-compose logs -f mem0-server
```

## 测试

### 运行诊断脚本
```bash
cd tests
uv run diagnose.py
```

检查 Qdrant、Zhipu AI、ModelArk 连接状态。

### 运行 API 测试
```bash
cd tests
uv run test_api.py
```

完整的 API 端点测试（添加、搜索、列出、删除）。

### 直接测试 Zhipu AI
```bash
cd tests
uv run test_zhipu_direct.py
```

验证 Zhipu AI API 工作正常。

## 项目结构

```
mem0-docker/
├── app/
│   ├── .env                      # 配置文件
│   ├── Dockerfile                # Docker 镜像定义
│   ├── main.py                   # FastAPI 应用主文件
│   └── pyproject.toml            # Python 依赖 (UV)
│
├── tests/
│   ├── diagnose.py               # 连接诊断脚本
│   ├── test_api.py               # API 测试脚本
│   ├── test_zhipu_direct.py      # Zhipu AI 直接测试
│   ├── pyproject.toml            # 测试依赖 (UV)
│   └── README.md                 # 测试说明
│
├── docker-compose.yml            # Docker 编排文件
├── DEPLOYMENT_SUMMARY.md         # 部署总结文档
└── README.md                     # 本文件
```

## 配置说明

### LLM (智谱 AI)
- **提供商**: OpenAI 兼容
- **模型**: `glm-4-flash-250414`
- **API 端点**: `https://open.bigmodel.cn/api/paas/v4`
- **参数**: 温度 0.7，最大令牌 2000

### Embedder (模力方舟)
- **提供商**: OpenAI 兼容
- **模型**: `Qwen3-Embedding-8B`
- **维度**: 4096
- **API 端点**: `https://ai.gitee.com/v1`

### Vector Store (Qdrant)
- **主机**: `115.190.24.157`
- **端口**: `6333`
- **嵌入维度**: 4096 (匹配 Qwen3)

## 常见问题

### Q: 如何修改 LLM 配置？
**A:** 编辑 `app/main.py` 中的 `config` 字典，然后运行：
```bash
docker-compose up --build -d
```

### Q: 数据存储在哪里？
**A:** 
- 向量数据：Qdrant (`115.190.24.157:6333`)
- 历史记录：容器内 SQLite (默认 `/root/.mem0/history.db`)

### Q: 如何持久化数据？
**A:** 在 `docker-compose.yml` 中添加 volume 挂载：
```yaml
volumes:
  - mem0_data:/root/.mem0
```

### Q: 容器无法连接 Qdrant？
**A:** 运行诊断脚本：
```bash
cd tests && uv run diagnose.py
```

## 生产部署建议

1. **安全性**
   - 使用密钥管理系统 (Vault, Secrets Manager)
   - 添加 HTTPS/TLS 支持
   - 配置身份认证 (API Key, JWT)
   - 配置速率限制

2. **性能**
   - 配置数据卷持久化
   - 调整 FastAPI worker 进程数
   - 配置 Mem0 缓存策略
   - 使用负载均衡器

3. **监控**
   - 添加日志系统 (ELK, Loki)
   - 性能监控 (Prometheus, DataDog)
   - 错误追踪 (Sentry)
   - 健康检查告警

## 故障排除

### 日志查看
```bash
docker logs mem0-server
```

### 进入容器
```bash
docker exec -it mem0-server /bin/bash
```

### 重启服务
```bash
docker-compose restart
```

### 完整重建
```bash
docker-compose down
docker system prune -a
docker-compose up --build -d
```

## 许可证

MIT

## 支持

有任何问题或建议，请参考以下资源：
- [Mem0 文档](https://docs.mem0.ai)
- [Qdrant 文档](https://qdrant.tech/documentation/)
- [FastAPI 文档](https://fastapi.tiangolo.com)
