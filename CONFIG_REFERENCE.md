# Mem0 Docker Configuration Reference

完整的环境变量配置参考指南。所有参数都通过 `.env` 文件配置，无需修改代码。

## 概览

系统包含以下可配置组件：
1. **Qdrant Vector Store** - 向量数据库
2. **LLM (Zhipu AI)** - 大语言模型，用于事实提取
3. **Embedding (ModelArk)** - 向量化引擎

## 快速示例

### 生产环境配置（低资源消耗）
```env
# API Keys
ZHIPU_API_KEY=your_key
MODELARK_API_KEY=your_key

# Qdrant
QDRANT_HOST=115.190.24.157
QDRANT_PORT=6333

# LLM - 标准配置
LLM_PROVIDER=openai
LLM_MODEL=glm-4-flash-250414
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# Embedding - 低资源模式
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=Qwen3-Embedding-0.6B
EMBEDDING_DIMS=1024
EMBEDDING_BASE_URL=https://ai.gitee.com/v1
```

### 开发环境配置（高精度）
```env
# ... 相同的 API Keys ...

# LLM - 更高温度获得多样化输出
LLM_TEMPERATURE=1.2
LLM_MAX_TOKENS=4000

# Embedding - 高质量模型
EMBEDDING_MODEL=Qwen3-Embedding-8B
EMBEDDING_DIMS=4096
```

## 完整配置表

### 1. API Keys (必需)

| 变量 | 示例值 | 说明 |
|------|--------|------|
| `ZHIPU_API_KEY` | `sk-xxxx...` | 智谱 AI API Key，从 https://open.bigmodel.cn 获取 |
| `MODELARK_API_KEY` | `XXXX...` | 模力方舟 API Key，从 https://modelark.cn 获取 |

### 2. Qdrant Vector Store

| 变量 | 默认值 | 范围/选项 | 说明 |
|------|--------|----------|------|
| `QDRANT_HOST` | `115.190.24.157` | IP 地址或域名 | Qdrant 服务器地址 |
| `QDRANT_PORT` | `6333` | 1-65535 | Qdrant 服务端口 |

**用例：**
```env
# 本地 Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# 远程 Qdrant
QDRANT_HOST=qdrant.example.com
QDRANT_PORT=6333

# 云服务 Qdrant
QDRANT_HOST=qdrant-cloud.company.com
QDRANT_PORT=6334
```

### 3. LLM 配置（智谱 AI）

| 变量 | 默认值 | 类型 | 说明 |
|------|--------|------|------|
| `LLM_PROVIDER` | `openai` | string | 固定为 `openai`（OpenAI 兼容 API） |
| `LLM_MODEL` | `glm-4-flash-250414` | string | Zhipu 模型 ID |
| `LLM_BASE_URL` | `https://open.bigmodel.cn/api/paas/v4` | URL | Zhipu API 端点 |
| `LLM_TEMPERATURE` | `0.7` | 0.0 - 2.0 | 生成多样性（越高越创意） |
| `LLM_MAX_TOKENS` | `2000` | 1 - 32000 | 最大生成标记数 |

**Zhipu AI 可用模型：**
```
- glm-4-flash-250414 (默认, 快速)
- glm-4 (高精度)
- glm-3.5-turbo (轻量)
```

**温度参数说明：**
- `0.0` - 完全确定性，适合数据抽取
- `0.7` - 平衡创意和稳定性（推荐）
- `1.5+` - 高度创意，适合创意生成

**示例：**
```env
# 标准配置
LLM_MODEL=glm-4-flash-250414
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# 高精度配置
LLM_MODEL=glm-4
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=4000

# 轻量配置
LLM_MODEL=glm-3.5-turbo
LLM_TEMPERATURE=0.5
LLM_MAX_TOKENS=1000
```

### 4. Embedding 配置（模力方舟）

| 变量 | 默认值 | 类型 | 说明 |
|------|--------|------|------|
| `EMBEDDING_PROVIDER` | `openai` | string | 固定为 `openai`（OpenAI 兼容 API） |
| `EMBEDDING_MODEL` | `Qwen3-Embedding-0.6B` | string | Embedding 模型 |
| `EMBEDDING_DIMS` | `1024` | 1024 / 4096 | 向量维度（必须匹配模型） |
| `EMBEDDING_BASE_URL` | `https://ai.gitee.com/v1` | URL | ModelArk API 端点 |

**可用模型对比：**

| 模型 | 维度 | Qdrant 存储/M向量 | 精度 | 推荐场景 |
|------|------|-----------------|------|---------|
| `Qwen3-Embedding-0.6B` | 1024 | ~256 MB | 中等 | **生产环境**（资源受限） |
| `Qwen3-Embedding-8B` | 4096 | ~1 GB | 高 | 开发/小规模部署 |

**选择建议：**
- 生产环境、服务器资源受限 → 使用 `0.6B (1024)`
- 开发测试、追求最高精度 → 使用 `8B (4096)`
- 内存有限的 ARM 设备 → 必须使用 `0.6B`

**示例：**
```env
# 低资源生产配置
EMBEDDING_MODEL=Qwen3-Embedding-0.6B
EMBEDDING_DIMS=1024

# 高精度开发配置
EMBEDDING_MODEL=Qwen3-Embedding-8B
EMBEDDING_DIMS=4096
```

## 配置变更工作流

### 更改 LLM 模型

```bash
# 1. 编辑 .env
LLM_MODEL=glm-4
LLM_TEMPERATURE=0.5

# 2. 重启容器（无需清理数据）
docker-compose restart

# 3. 新的 LLM 配置立即生效
curl http://localhost:8000/health
```

### 切换 Embedding 模型维度

```bash
# 1. 编辑 .env
EMBEDDING_MODEL=Qwen3-Embedding-8B
EMBEDDING_DIMS=4096

# 2. 清空旧向量（维度不兼容）
curl -X POST http://localhost:8000/admin/reset-collections

# 3. 重启容器
docker-compose restart

# 4. Mem0 自动以新维度重建集合
```

### 更改 API 端点

```bash
# 若想使用不同的 Zhipu/ModelArk 端点
ZHIPU_API_KEY=new_key
LLM_BASE_URL=https://custom.zhipu.endpoint/v1

MODELARK_API_KEY=new_key
EMBEDDING_BASE_URL=https://custom.modelark.endpoint/v1

docker-compose restart
```

## 常见配置场景

### 场景 1: 资源严格受限（树莓派/边缘设备）

```env
# 最小化配置
LLM_TEMPERATURE=0.5
LLM_MAX_TOKENS=1000

EMBEDDING_MODEL=Qwen3-Embedding-0.6B
EMBEDDING_DIMS=1024
```

### 场景 2: 高精度企业应用

```env
# 高精度配置
LLM_MODEL=glm-4
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=4000

EMBEDDING_MODEL=Qwen3-Embedding-8B
EMBEDDING_DIMS=4096
```

### 场景 3: 快速原型开发

```env
# 快速迭代配置
LLM_MODEL=glm-3.5-turbo
LLM_TEMPERATURE=1.0

EMBEDDING_MODEL=Qwen3-Embedding-0.6B  # 快速启动
EMBEDDING_DIMS=1024
```

## 验证配置

### 查看当前配置

```bash
# 通过健康检查端点查看初始化状态
curl http://localhost:8000/health
# 返回: {"status":"healthy","mem0_initialized":true}

# 查看 .env 文件
cat app/.env
```

### 测试配置

```bash
# 运行诊断脚本
cd tests
uv run diagnose.py

# 运行 API 测试
uv run test_api.py
```

## 故障排查

### 问题：更改配置后 API 报错

**解决：** 确保重启了容器
```bash
docker-compose restart
docker-compose logs mem0-server  # 检查初始化日志
```

### 问题：向量维度不匹配错误

**解决：** 使用 `/admin/reset-collections` 清空旧向量
```bash
curl -X POST http://localhost:8000/admin/reset-collections
docker-compose restart
```

### 问题：API Key 错误

**解决：** 
1. 确认 API Key 在 `.env` 中正确设置
2. 确认没有包含引号：`KEY=value` 而非 `KEY="value"`
3. 重启容器以加载新 keys

```bash
docker-compose restart
```

## 高级配置

### 多环境部署

```bash
# 开发环境
cp .env.development app/.env
docker-compose up -d

# 生产环境
cp .env.production app/.env
docker-compose up -d
```

**.env.development 示例：**
```env
EMBEDDING_MODEL=Qwen3-Embedding-8B
EMBEDDING_DIMS=4096
LLM_TEMPERATURE=1.0
```

**.env.production 示例：**
```env
EMBEDDING_MODEL=Qwen3-Embedding-0.6B
EMBEDDING_DIMS=1024
LLM_TEMPERATURE=0.5
```

### Docker Compose 覆盖

也可通过 Docker Compose 环境变量覆盖：

```bash
# 临时改变配置
EMBEDDING_DIMS=4096 docker-compose up -d
```

## 更新日志

### v1.2.0 (Latest)
- 所有配置项均可通过环境变量驱动
- 支持 LLM 和 Embedding 提供商切换
- 完整的配置参考文档

### v1.1.0
- 可配置的 Embedding 模型维度
- `/admin/reset-collections` 端点

### v1.0.0
- 初始版本，基础功能完整
