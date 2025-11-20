# Mem0 Local Docker Deployment

基于 Mem0 的本地化部署方案，支持五层智能记忆管理架构。

## ✨ 特性

- 🧠 **五层记忆架构** - 完整→摘要→标签→痕迹→存档，永不遗忘
- 🌍 **多语言支持** - 自动检测并处理中文、英文、日文等多种语言
- 🔄 **自动维护** - 时间衰减、层次转换、智能摘要
- ⚡ **快速测试** - 秒/分钟级模拟测试，快速验证配置
- 🐳 **Docker部署** - 一键启动，包含完整维护服务
- 🛠️ **uv管理** - 现代化Python包管理，快速可靠

## 📋 前置要求

- Docker 和 Docker Compose
- Python 3.11+ (本地运行时)
- [uv](https://github.com/astral-sh/uv) - Python包管理工具
- API密钥：智谱AI、ModelArk

## 🚀 快速开始

### 1. 配置环境变量

复制配置示例：

```bash
cp .env.example app/.env
```

编辑 `app/.env`，设置必需的API密钥：

```env
ZHIPU_API_KEY=your_zhipu_api_key
MODELARK_API_KEY=your_modelark_api_key
```

### 2. 启动服务

#### Docker方式（推荐）

```bash
# 仅启动Mem0服务
docker-compose up -d

# 启动Mem0 + 维护服务
docker-compose --profile maintenance up -d
```

#### 本地运行

```bash
# 安装uv（如果还没有）
pip install uv

# 启动Mem0服务
cd app
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

服务将在 `http://localhost:8000` 启动。

### 3. 运行测试

```bash
# 进入测试目录
cd tests

# 安装依赖
uv sync

# 运行模拟测试（创建5条记忆）
uv run test-simulation --create-memories 5
```

## API Endpoints

-   **POST /memories**: Add a memory with automatic language detection and language-aware fact extraction.
-   **POST /memories/search**: Search memories (supports cross-language search via vector embeddings).
-   **GET /memories**: Get all memories for a user.
-   **DELETE /memories/{memory_id}**: Delete a specific memory.
-   **DELETE /memories?user_id={user_id}**: Reset memories for a user.
-   **GET /health**: Health check with Mem0 initialization status.

### Language Support

The system automatically detects input language and extracts facts in the same language:

- **中文 (Chinese)** - 自动提取中文事实
- **English** - Automatically extracts English facts
- **日本語 (Japanese)** - 日本語で事実を抽出
- **한국어 (Korean)** - 한국어로 사실 추출
- **العربية (Arabic)** - استخراج الحقائق بالعربية
- **Русский (Russian)** - Извлечение фактов на русском
- **ไทย (Thai)** - สกัดข้อเท็จจริงในภาษาไทย

See [MULTILINGUAL_FACTS.md](./MULTILINGUAL_FACTS.md) for detailed multilingual usage examples.

## 🎯 核心功能

### 五层记忆架构

| 层次       | 权重范围 | 特性     | 示例                         |
| ---------- | -------- | -------- | ---------------------------- |
| ✓ 完整记忆 | > 0.7    | 原文保留 | "用户喜欢喝美式咖啡，不加糖" |
| 📝 摘要记忆 | 0.3-0.7  | 智能摘要 | "用户偏好黑咖啡"             |
| 🏷️ 标签记忆 | 0.1-0.3  | 模糊标签 | "用户喜欢饮品"               |
| 👣 痕迹记忆 | 0.03-0.1 | 痕迹描述 | "曾经有饮品相关记忆"         |
| 📦 存档记忆 | ≤ 0.03   | 历史痕迹 | "历史痕迹：饮品偏好"         |

详见：[五层架构说明](./SMART_MEMORY_FIVE_LEVELS.md)

### 记忆维护服务

自动化维护所有用户记忆：

```bash
# 一次性维护
cd app
uv run maintenance-once

# 启动定时服务（默认每24小时）
uv run maintenance
```

配置方式：

```env
# .env文件
MAINTENANCE_DECAY_ALPHA=0.01
MAINTENANCE_SCAN_INTERVAL_HOURS=24
MAINTENANCE_FULL_THRESHOLD=0.7
```

详见：[维护服务文档](./docs/MAINTENANCE_SERVICE.md)

### 模拟测试

快速验证记忆衰减和层次转换：

```bash
cd tests

# 快速测试（10秒周期，5次）
uv run test-simulation --create-memories 5

# 闪电测试（5秒周期，极速衰减）
SIM_DECAY_ALPHA=2.0 SIM_SCAN_INTERVAL=5 uv run test-simulation

# 自定义参数
uv run test-simulation --decay-alpha 1.0 --max-cycles 20
```

详见：[模拟测试指南](./docs/SIMULATION_TEST_GUIDE.md)

## 📚 文档

- [快速开始指南](./QUICK_START.md) - 完整的入门教程
- [五层记忆架构](./SMART_MEMORY_FIVE_LEVELS.md) - 核心设计理念
- [维护服务文档](./docs/MAINTENANCE_SERVICE.md) - 自动维护配置
- [模拟测试指南](./docs/SIMULATION_TEST_GUIDE.md) - 测试使用说明
- [UV使用指南](./docs/UV_GUIDE.md) - 包管理工具文档
- [多语言支持](./MULTILINGUAL_FACTS.md) - 多语言使用示例
- [个人助理测试](./PERSONAL_ASSISTANT_TEST.md) - 实际应用案例

## 🔧 环境变量配置

复制 `.env.example` 到 `app/.env` 并配置：

```env
# 必需配置
ZHIPU_API_KEY=your_api_key
MODELARK_API_KEY=your_api_key

# 维护服务配置（可选）
MAINTENANCE_DECAY_ALPHA=0.01
MAINTENANCE_SCAN_INTERVAL_HOURS=24
MAINTENANCE_FULL_THRESHOLD=0.7
MAINTENANCE_SUMMARY_THRESHOLD=0.3

# 模拟测试配置（可选）
SIM_TIME_UNIT=second
SIM_SCAN_INTERVAL=10
SIM_DECAY_ALPHA=0.5
SIM_MAX_CYCLES=10
```

完整配置参考：[.env.example](./.env.example)

## Implementation Details

-   **LLM**: Zhipu AI (`glm-4-flash-250414`) via OpenAI-compatible provider.
-   **Embedder**: ModelArk (`Qwen3-Embedding-8B`) via OpenAI-compatible provider.
-   **Vector Store**: Qdrant at `115.190.27.17:6333`.
-   **Package Management**: Uses `uv` for fast Python package management.
-   **Concurrency**: The server uses FastAPI. Blocking Mem0 calls are run in a thread pool to support concurrency.
