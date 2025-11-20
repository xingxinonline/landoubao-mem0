# Mem0 MCP Server Deployment Guide

## 概述

本项目将Mem0记忆管理系统部署为MCP (Model Context Protocol) Docker镜像，使其可以通过标准的MCP协议与AI应用集成。

## MCP服务器特性

### 可用工具

MCP服务器提供以下工具：

1. **add_memory** - 添加新的记忆
2. **search_memory** - 搜索相关记忆
3. **get_all_memories** - 获取用户所有记忆
4. **delete_memory** - 删除特定记忆
5. **delete_all_memories** - 删除用户所有记忆
6. **create_user_session** - 创建新用户会话
7. **get_memory_stats** - 获取记忆统计信息

## 快速开始

### 1. 构建MCP Docker镜像

```bash
# 构建MCP服务器镜像
docker build -f app/Dockerfile.mcp -t mem0-mcp-server ./app
```

### 2. 使用docker-compose启动

```bash
# 启动MCP服务器
docker-compose -f docker-compose.mcp.yml up -d mem0-mcp-server

# 或同时启动HTTP和MCP服务器
docker-compose -f docker-compose.mcp.yml up -d
```

### 3. 直接运行MCP服务器（用于测试）

```bash
docker run -i --rm --env-file ./app/.env mem0-mcp-server
```

## 配置

### 环境变量

在 `app/.env` 文件中配置：

```env
# Qdrant向量数据库
QDRANT_HOST=115.190.24.157
QDRANT_PORT=6333

# LLM配置 (智谱AI)
LLM_PROVIDER=openai
LLM_MODEL=glm-4-flash-250414
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2000

# 嵌入模型配置 (ModelArk)
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=Qwen3-Embedding-0.6B
EMBEDDING_DIMS=1024
EMBEDDING_BASE_URL=https://ai.gitee.com/v1

# API密钥
ZHIPU_API_KEY=your_zhipu_api_key_here
MODELARK_API_KEY=your_modelark_api_key_here
```

## MCP客户端集成

### Claude Desktop配置

将以下配置添加到Claude Desktop的配置文件中：

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mem0": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--env-file",
        "/path/to/landoubao-mem0/app/.env",
        "mem0-mcp-server"
      ]
    }
  }
}
```

### VS Code Copilot配置

在VS Code设置中添加：

```json
{
  "github.copilot.advanced": {
    "mcp": {
      "servers": {
        "mem0": {
          "command": "docker",
          "args": [
            "run",
            "-i",
            "--rm",
            "--env-file",
            "./app/.env",
            "mem0-mcp-server"
          ]
        }
      }
    }
  }
}
```

## 使用示例

### 示例1: 添加记忆

```json
{
  "tool": "add_memory",
  "arguments": {
    "messages": [
      {
        "role": "user",
        "content": "我叫李四，今年28岁，是一名软件工程师。"
      }
    ],
    "user_id": "user-123",
    "metadata": {
      "source": "conversation",
      "topic": "personal_info"
    }
  }
}
```

### 示例2: 搜索记忆

```json
{
  "tool": "search_memory",
  "arguments": {
    "query": "李四的职业是什么？",
    "user_id": "user-123",
    "limit": 5
  }
}
```

### 示例3: 创建用户会话

```json
{
  "tool": "create_user_session",
  "arguments": {
    "metadata": {
      "name": "张三",
      "role": "产品经理"
    }
  }
}
```

## 架构说明

```
┌─────────────────────────────────────┐
│   MCP Client (Claude/VSCode)        │
└────────────┬────────────────────────┘
             │ stdio communication
             ▼
┌─────────────────────────────────────┐
│   Docker Container                  │
│   ┌─────────────────────────────┐   │
│   │   mcp_server.py             │   │
│   │   (MCP Protocol Handler)    │   │
│   └──────────┬──────────────────┘   │
│              │                       │
│   ┌──────────▼──────────────────┐   │
│   │   Mem0 Memory Engine        │   │
│   └──────────┬──────────────────┘   │
└──────────────┼───────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Qdrant Vector Database            │
│   (External Service)                │
└─────────────────────────────────────┘
```

## 双模式运行

本项目支持两种运行模式：

### 1. MCP模式（stdio通信）
- 通过stdio与MCP客户端通信
- 适合与Claude Desktop、VS Code等集成
- 启动命令：`python mcp_server.py`

### 2. HTTP API模式
- 提供RESTful API接口
- 适合传统HTTP客户端调用
- 启动命令：`uvicorn main:app --host 0.0.0.0 --port 8000`

可以使用docker-compose同时运行两种模式：

```bash
docker-compose -f docker-compose.mcp.yml up -d
```

## 测试MCP服务器

### 使用MCP Inspector

```bash
# 安装MCP Inspector
npm install -g @modelcontextprotocol/inspector

# 运行Inspector连接到MCP服务器
mcp-inspector docker run -i --rm --env-file ./app/.env mem0-mcp-server
```

### 使用Python客户端测试

```python
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    server_params = StdioServerParameters(
        command="docker",
        args=[
            "run",
            "-i",
            "--rm",
            "--env-file",
            "./app/.env",
            "mem0-mcp-server"
        ]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 列出可用工具
            tools = await session.list_tools()
            print("Available tools:", tools)
            
            # 调用工具
            result = await session.call_tool(
                "create_user_session",
                arguments={"metadata": {"name": "测试用户"}}
            )
            print("Result:", result)

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
```

## 故障排除

### 问题1: Docker容器无法启动

**解决方案**:
- 检查 `.env` 文件是否存在且配置正确
- 验证API密钥是否有效
- 检查Qdrant服务是否可访问

### 问题2: MCP客户端无法连接

**解决方案**:
- 确保Docker镜像已正确构建
- 检查配置文件中的路径是否正确
- 查看Docker日志：`docker logs mem0-mcp-server`

### 问题3: 记忆操作失败

**解决方案**:
- 验证Qdrant连接配置
- 检查API密钥权限
- 查看错误日志以获取详细信息

## 生产环境建议

1. **使用环境变量管理密钥**
   - 不要在配置文件中硬编码API密钥
   - 使用Docker secrets或环境变量

2. **配置资源限制**
   ```yaml
   services:
     mem0-mcp-server:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
   ```

3. **设置健康检查**
   ```yaml
   healthcheck:
     test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
     interval: 30s
     timeout: 10s
     retries: 3
   ```

4. **启用日志管理**
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

## 性能优化

- **连接池**: Mem0和Qdrant使用连接池
- **缓存**: 考虑为频繁查询启用缓存
- **批处理**: 大量操作时使用批处理API

## 安全性

- ✅ API密钥通过环境变量管理
- ✅ stdio通信避免了网络暴露
- ✅ Docker容器隔离
- ⚠️ 生产环境建议使用TLS加密

## 监控和日志

查看MCP服务器日志：

```bash
# 实时日志
docker logs -f mem0-mcp-server

# 查看最近100行
docker logs --tail 100 mem0-mcp-server
```

## 更新和维护

### 更新镜像

```bash
# 重新构建镜像
docker build -f app/Dockerfile.mcp -t mem0-mcp-server ./app

# 重启服务
docker-compose -f docker-compose.mcp.yml restart mem0-mcp-server
```

### 备份数据

```bash
# 备份Qdrant数据（如果本地运行）
docker exec qdrant-container tar czf /backup/qdrant-backup.tar.gz /qdrant/storage
```

## 许可证

遵循原项目许可证

## 支持

- GitHub Issues: [项目地址]
- 文档: [文档链接]

---

**最后更新**: 2025-11-20
**版本**: 1.0.0-mcp
