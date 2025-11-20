# 🧩 完整记忆管理系统

**基于Mem0的智能多模态记忆管理解决方案**

[![测试状态](https://img.shields.io/badge/测试-7%2F7通过-brightgreen)](./TEST_VALIDATION_REPORT.md)
[![文档](https://img.shields.io/badge/文档-完整-blue)](./COMPLETE_MEMORY_SOLUTION.md)
[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://www.python.org/)
[![许可证](https://img.shields.io/badge/许可证-MIT-green)](./LICENSE)

---

## 📖 项目简介

这是一个**完整的记忆管理系统设计与实现**，采用增强型6因子衰退曲线，支持多模态记忆存储、智能检索、自动压缩、生命周期管理等功能。

### 核心特性

- ✅ **身份与根ID管理**: DeviceUUID + UserID双重保障，支持多用户环境
- ✅ **五级存储层级**: FULL → SUMMARY → TAG → TRACE → ARCHIVE
- ✅ **六因子权重公式**: W = w_time × S × C × I × U × M
- ✅ **多模态支持**: 文本、图片、语音统一管理
- ✅ **智能检索**: 三阶段检索（层级过滤→粗排→精排）
- ✅ **自动调度**: 压缩/合并/清理无人值守
- ✅ **完整溯源**: 压缩链、合并链、修正链可追踪
- ✅ **生命周期管理**: 冻结、敏感标记、软删除

---

## 🚀 快速开始

### 安装依赖

```bash
# 使用uv包管理器
uv sync

# 或使用pip
pip install -r requirements.txt
```

### 运行测试

```bash
cd tests
uv run python test_complete_simulation.py
```

### 预期输出

```
======================================================================
🧩 完整记忆管理系统 - 模拟测试
======================================================================

✅ 身份与根ID管理 - 通过
✅ 多模态记忆存储 - 通过
✅ 增强型衰退曲线 - 通过
✅ 智能检索与Reranker - 通过
✅ 定时调度服务 - 通过
✅ 生命周期管理 - 通过
✅ 特殊情形处理 - 通过

======================================================================
通过: 7/7 (100%)
======================================================================

🎉 恭喜！所有测试通过！
```

---

## 📂 项目结构

```
mem0-docker/
├── app/
│   ├── complete_memory_system.py      # 核心数据结构
│   ├── complete_memory_engine.py      # 权重计算与决策引擎
│   ├── smart_retriever.py             # 智能检索与Reranker
│   └── scheduler_lifecycle.py         # 调度服务与生命周期管理
│
├── tests/
│   ├── test_complete_simulation.py    # 完整模拟测试
│   └── test_complete_system.py        # 系统综合测试
│
├── docs/
│   ├── COMPLETE_MEMORY_SOLUTION.md    # 完整方案设计文档
│   └── TEST_VALIDATION_REPORT.md      # 测试验证报告
│
├── docker-compose.yml                 # Docker配置
├── README.md                          # 本文件
└── pyproject.toml                     # 项目配置
```

---

## 🎯 核心概念

### 1. 记忆ID结构

```
{DeviceUUID}_{UserID}_{Timestamp}_{SequenceID}

示例: b2e182b2_alice_20251120190034_00001
```

- **DeviceUUID**: 设备唯一标识（前8位）
- **UserID**: 用户标识符
- **Timestamp**: 创建时间戳（YYYYMMDDHHmmss）
- **SequenceID**: 序列号（5位递增）

### 2. 六因子权重公式

$$
W(t) = w_{time}(t) \times S(t) \times C(t) \times I \times U \times M(t)
$$

| 因子       | 名称     | 范围       | 作用     |
| ---------- | -------- | ---------- | -------- |
| $w_{time}$ | 时间权重 | [0, 1]     | 基础衰减 |
| $S$        | 语义强化 | [1.0, 1.5] | 激活提升 |
| $C$        | 冲突修正 | [0.3, 1.0] | 否定降权 |
| $I$        | 重要性   | [0.8, 1.5] | 类别差异 |
| $U$        | 用户因子 | [0.7, 1.5] | 个性化   |
| $M$        | 动量     | [1.0, 1.3] | 频繁控制 |

### 3. 五级存储层级

| 层级        | 权重范围   | 内容形式     | 用途           |
| ----------- | ---------- | ------------ | -------------- |
| **FULL**    | 0.6 ~ 2.0  | 原始完整内容 | 最近、重要记忆 |
| **SUMMARY** | 0.3 ~ 0.6  | LLM生成摘要  | 中期压缩       |
| **TAG**     | 0.1 ~ 0.3  | 关键词标签   | 久远索引       |
| **TRACE**   | 0.05 ~ 0.1 | 最小元数据   | 痕迹保留       |
| **ARCHIVE** | 0.0 ~ 0.05 | 归档状态     | 待清理         |

---

## 💡 使用示例

### 基础使用

```python
from complete_memory_system import (
    DeviceManager, UserIdentity, MemoryIDGenerator,
    MemoryStore, Memory, MultimodalContent, MemoryMetadata
)
from complete_memory_engine import CompleteMemoryEngine

# 1. 初始化
device_manager = DeviceManager()
user_identity = UserIdentity(user_id="alice")
id_generator = MemoryIDGenerator(device_manager)
store = MemoryStore()

# 2. 创建记忆引擎
engine = CompleteMemoryEngine(user_factor=1.0)

# 3. 创建记忆
memory_id = id_generator.generate_memory_id("alice")
content = MultimodalContent(
    text="我喜欢喝咖啡",
    image_url="https://example.com/coffee.jpg"
)

metadata = MemoryMetadata(
    memory_id=memory_id,
    device_uuid=device_manager.get_device_id(),
    user_id="alice",
    created_at=datetime.now().isoformat(),
    last_activated_at=datetime.now().isoformat(),
    category=MemoryCategory.STABLE_PREFERENCE
)

memory = Memory(memory_id=memory_id, content=content, metadata=metadata)
store.add_memory(memory)

# 4. 计算权重
factors = engine.calculate_enhanced_weight(memory)
print(f"权重: {factors.total_weight:.4f}")
```

### 智能检索

```python
from smart_retriever import SmartRetriever, RetrievalConfig, QueryMode

# 1. 创建检索器
retriever = SmartRetriever(engine)

# 2. 配置检索参数
config = RetrievalConfig(
    query_mode=QueryMode.NORMAL,
    top_k=10,
    similarity_threshold=0.6
)

# 3. 执行检索
results = retriever.retrieve(
    query="咖啡偏好",
    memories=store.get_user_memories("alice"),
    config=config
)

# 4. 查看结果
for result in results:
    print(f"{result.memory.content.text} - 相关性: {result.relevance_score:.4f}")
```

### 定时调度

```python
from scheduler_lifecycle import MemoryScheduler, SchedulerConfig

# 1. 配置调度器
config = SchedulerConfig(
    compression_interval_seconds=3600,  # 1小时压缩
    merge_interval_seconds=7200,        # 2小时合并
    cleanup_interval_seconds=86400      # 1天清理
)

# 2. 创建调度器
scheduler = MemoryScheduler(store, engine, id_generator, config)

# 3. 启动服务
await scheduler.start()

# 4. 运行中...（自动压缩/合并/清理）

# 5. 停止服务
await scheduler.stop()
```

---

## 📊 测试结果

### 全面验证

| 测试模块       | 状态 | 说明                                         |
| -------------- | ---- | -------------------------------------------- |
| 身份与根ID管理 | ✅    | 设备UUID、用户ID、记忆ID生成解析             |
| 多模态记忆存储 | ✅    | TEXT+IMAGE+AUDIO三模态                       |
| 增强型衰退曲线 | ✅    | 6因子公式验证（衰减-6%, 激活+41%, 否定-70%） |
| 智能检索       | ✅    | 三阶段检索，相关性排序                       |
| 定时调度服务   | ✅    | 自动压缩/合并/清理                           |
| 生命周期管理   | ✅    | 冻结、敏感标记、软删除                       |
| 特殊情形处理   | ✅    | 频繁强化、用户否定、批量合并                 |

**通过率**: **7/7 (100%)**

详见 [测试验证报告](./TEST_VALIDATION_REPORT.md)

---

## 📚 文档资源

| 文档                                                         | 描述                   |
| ------------------------------------------------------------ | ---------------------- |
| [COMPLETE_MEMORY_SOLUTION.md](./COMPLETE_MEMORY_SOLUTION.md) | 🧩 完整方案设计（70页） |
| [TEST_VALIDATION_REPORT.md](./TEST_VALIDATION_REPORT.md)     | 📊 测试验证报告         |
| [README.md](./README.md)                                     | 📖 项目说明（本文件）   |

---

## 🔧 配置参数

### 用户个性化

```python
user_factor = 1.0   # 普通用户
user_factor = 0.7   # 慢遗忘用户
user_factor = 1.5   # 快遗忘用户
```

### 时间刻度

```python
time_scale = 86400  # 生产环境：1天=86400秒
time_scale = 60     # 测试环境：1分钟=1天
```

### 调度周期

```python
compression_interval = 3600   # 1小时
merge_interval = 7200         # 2小时
cleanup_interval = 86400      # 1天
```

---

## 🚧 生产环境集成

### 1. 语义相似度（推荐）

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def calculate_semantic_similarity(query, memory):
    query_emb = model.encode(query)
    memory_emb = model.encode(memory.content.text)
    return cosine_similarity(query_emb, memory_emb)
```

### 2. LLM摘要生成

```python
from openai import OpenAI

client = OpenAI(api_key="your-key")

def summarize_with_llm(texts):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{
            "role": "user",
            "content": f"请合并以下记忆为简洁摘要：\n{texts}"
        }]
    )
    return response.choices[0].message.content
```

### 3. Mem0 API集成

```python
from mem0 import MemoryClient

client = MemoryClient(api_key="your-api-key")

memory_data = {
    "messages": [{"role": "user", "content": "我喜欢喝咖啡"}],
    "user_id": "alice",
    "metadata": {
        "device_uuid": device_uuid,
        "factors": factors.to_dict()
    }
}

result = client.add(memory_data)
```

---

## 🎓 设计亮点

### 1. 双时间戳设计

- **created_at**: 保持历史感，永不改变
- **last_activated_at**: 计算活跃衰减，用户激活时刷新

### 2. 动量因子饱和

防止频繁提及导致权重无限增长，上限1.3：

$$
M(t) = 1 + 0.3 \times (1 - e^{-0.5 \times n})
$$

### 3. 冲突自愈机制

用户否定时立即降权70%，随时间缓慢恢复：

$$
C(t) = 0.3 + 0.7 \times e^{-0.01 \times \Delta t}
$$

### 4. 完整溯源链

```python
metadata = {
    "source_ids": [...],         # 来源记忆
    "merged_from": [...],        # 合并自哪些记忆
    "compressed_from": "...",    # 压缩自哪条记忆
    "parent_id": "...",          # 父记忆（修正关系）
    "children_ids": [...]        # 子记忆列表
}
```

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 📜 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- **Mem0**: 提供强大的记忆管理基础设施
- **sentence-transformers**: 多语言语义相似度
- **OpenAI/GLM**: LLM智能摘要生成

---

## 📞 联系方式

- **项目主页**: [GitHub Repository](https://github.com/xingxinonline/landoubao-mem0)
- **问题反馈**: [Issues](https://github.com/xingxinonline/landoubao-mem0/issues)
- **作者**: GitHub Copilot

---

**⭐ 如果这个项目对你有帮助，欢迎Star支持！**

---

*最后更新: 2025-11-20*
