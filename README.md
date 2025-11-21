# Mem0 MCP Server (Simplified)

这是一个基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) 的记忆服务，使用 Mem0 作为后端存储。它专为大语言模型 (LLM) 设计，提供简单、高效的长期记忆能力。

## ✨ 核心特性

- **极简 API**: 仅提供 2 个核心工具 (`add_memory`, `search_memory`)，降低 LLM 认知负担。
- **安全设计**: 移除删除功能，防止误操作，仅保留增加和搜索能力。
- **多语言支持**: 内置自动语言检测和处理，支持中、英、日、韩等多种语言。
- **跨语言搜索**: 基于语义向量检索，支持跨语言查询（如用中文搜英文记忆）。
- **Docker 部署**: 提供一键启动的 Docker 环境，生产就绪。
- **HTTP SSE 传输**: 使用标准的 HTTP Server-Sent Events 协议，支持远程访问。

## 🚀 快速开始

### 1. 环境准备

确保已安装 Docker 和 Docker Compose。

配置环境变量：
```bash
cp app/.env.example app/.env
# 编辑 app/.env 填入你的 API Key (智谱 AI, ModelArk, Qdrant)
```

### 2. 启动服务

```bash
docker-compose -f docker-compose.mcp-http.yml up -d
```

服务将在 `http://localhost:8001` 启动。

### 3. 测试运行

我们提供了一个测试脚本，模拟 LLM 调用 MCP 工具：

```bash
# 设置 API Key (Windows PowerShell)
$env:ZHIPU_API_KEY = "your_zhipu_api_key"

# 运行测试
uv run --directory app python ../test_llm_with_mcp_tools.py
```

## 📚 文档

- [**集成指南 (MCP_INTEGRATION_GUIDE.md)**](./MCP_INTEGRATION_GUIDE.md): 面向智能体开发者的完整集成参考，包含架构图、API 定义和 System Prompt 示例。
- [**测试脚本**](./test_llm_with_mcp_tools.py): 包含完整的客户端实现代码，可作为开发参考。

## 🛠️ 工具列表

| 工具名称        | 描述                                 |
| --------------- | ------------------------------------ |
| `add_memory`    | 添加记忆。自动检测语言并提取事实。   |
| `search_memory` | 搜索记忆。基于语义匹配，支持跨语言。 |

## 🏗️ 项目结构

```
.
├── app/
│   ├── mcp_server_http.py    # MCP Server 核心代码
│   ├── Dockerfile.mcp-http   # Docker 构建文件
│   └── pyproject.toml        # 依赖管理
├── docker-compose.mcp-http.yml # Docker Compose 配置
├── test_llm_with_mcp_tools.py  # LLM 集成测试脚本
└── MCP_INTEGRATION_GUIDE.md # 集成指南
```
