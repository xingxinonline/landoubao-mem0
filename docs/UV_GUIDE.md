# UV 使用指南

本项目使用 [uv](https://github.com/astral-sh/uv) 作为 Python 包管理工具，提供快速、可靠的依赖管理。

## 📦 安装 uv

### Windows (PowerShell)

```powershell
# 使用pip安装
pip install uv

# 或使用官方安装脚本
irm https://astral.sh/uv/install.ps1 | iex
```

### Linux/macOS

```bash
# 使用pip安装
pip install uv

# 或使用官方安装脚本
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 🚀 快速开始

### 1. 安装项目依赖

```powershell
# 进入应用目录
cd app
uv sync

# 或进入测试目录
cd tests
uv sync
```

### 2. 运行命令

#### 运行维护服务

```powershell
cd app

# 一次性维护
uv run maintenance-once

# 启动定时服务
uv run maintenance
```

#### 运行模拟测试

```powershell
cd tests

# 默认配置
uv run test-simulation

# 自定义参数
uv run test-simulation --create-memories 5 --decay-alpha 1.0
```

### 3. 添加新依赖

```powershell
# 添加依赖
uv add package-name

# 添加开发依赖
uv add --dev package-name

# 从requirements.txt安装
uv pip install -r requirements.txt
```

## 🔧 常用命令

### 依赖管理

```powershell
# 同步依赖（安装/更新）
uv sync

# 更新所有依赖
uv sync --upgrade

# 列出已安装的包
uv pip list

# 显示包信息
uv pip show package-name
```

### 运行脚本

```powershell
# 运行定义在pyproject.toml的脚本
uv run script-name

# 直接运行Python模块
uv run python -m module_name

# 运行任意Python命令
uv run python script.py
```

### 虚拟环境

```powershell
# uv自动管理虚拟环境，无需手动创建

# 如需手动激活虚拟环境
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS
```

## 📝 配置文件说明

### pyproject.toml

定义项目依赖和脚本入口点：

```toml
[project]
name = "mem0-docker"
dependencies = [
    "mem0ai",
    "requests",
]

[project.scripts]
maintenance = "memory_maintenance:main"
maintenance-once = "memory_maintenance:run_once"
```

### .env

环境变量配置（不会被uv管理，需要使用 python-dotenv 加载）：

```env
ZHIPU_API_KEY=your_key
MAINTENANCE_DECAY_ALPHA=0.01
```

## 🔄 从pip/poetry迁移

### 从pip迁移

```powershell
# 如果有requirements.txt
uv pip install -r requirements.txt

# 生成pyproject.toml
# 手动创建或从requirements.txt转换
```

### 从poetry迁移

```powershell
# poetry的pyproject.toml可以直接使用
uv sync

# 或从poetry.lock迁移
uv pip install --requirement <(poetry export -f requirements.txt)
```

## 💡 最佳实践

### 1. 锁定依赖版本

```powershell
# uv会自动生成uv.lock文件
# 提交到版本控制以确保一致性
git add uv.lock
```

### 2. 开发环境配置

```toml
[tool.uv]
dev-dependencies = [
    "pytest",
    "black",
    "ruff",
]
```

### 3. 使用脚本入口

在 `pyproject.toml` 中定义脚本，避免直接运行Python文件：

```toml
[project.scripts]
test = "pytest:main"
format = "black:main"
```

### 4. 环境隔离

```powershell
# 每个项目使用独立的虚拟环境
# uv会在项目目录创建.venv

# 清理并重建环境
rm -r .venv
uv sync
```

## 🐛 故障排查

### 问题1: uv命令未找到

```powershell
# 检查安装
pip show uv

# 重新安装
pip install --upgrade uv
```

### 问题2: 依赖冲突

```powershell
# 清理缓存
uv cache clean

# 重新同步
rm uv.lock
uv sync
```

### 问题3: 虚拟环境问题

```powershell
# 删除虚拟环境重建
rm -r .venv
uv sync
```

## 📚 相关链接

- [uv 官方文档](https://github.com/astral-sh/uv)
- [Python 打包指南](https://packaging.python.org/)
- [pyproject.toml 规范](https://peps.python.org/pep-0621/)

## ⚡ 性能对比

| 操作     | pip  | poetry | uv      |
| -------- | ---- | ------ | ------- |
| 安装依赖 | ~45s | ~30s   | **~5s** |
| 解析依赖 | ~10s | ~15s   | **<1s** |
| 缓存命中 | ~5s  | ~3s    | **<1s** |

uv 使用 Rust 编写，性能显著优于传统工具。
