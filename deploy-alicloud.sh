#!/bin/bash

# 阿里云部署脚本 - Mem0 MCP Server

set -e

echo "=========================================="
echo "Mem0 MCP Server - 阿里云部署脚本"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Docker Compose 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装${NC}"
    echo "请先安装 Docker: https://docs.docker.com/engine/install/"
    exit 1
fi

# 检查 Docker Compose V2
if ! docker compose version &> /dev/null; then
    echo -e "${RED}错误: Docker Compose V2 未安装${NC}"
    echo "请升级到 Docker Compose V2"
    exit 1
fi

echo -e "${GREEN}✓ Docker 环境检查通过${NC}"

# 检查 .env 文件
if [ ! -f "app/.env" ]; then
    echo -e "${YELLOW}警告: app/.env 文件不存在${NC}"
    echo "从 .env.example 创建 .env 文件..."
    cp app/.env.example app/.env
    echo -e "${YELLOW}请编辑 app/.env 文件，填入正确的 API Keys${NC}"
    echo "然后重新运行此脚本"
    exit 1
fi

echo -e "${GREEN}✓ 环境配置文件检查通过${NC}"

# 创建数据目录
echo "创建数据持久化目录..."
mkdir -p qdrant_storage qdrant_snapshots

# 停止旧容器
echo "停止旧容器..."
docker compose -f docker-compose.mcp-http.yml down 2>/dev/null || true

# 构建镜像
echo "构建 Docker 镜像..."
docker compose -f docker-compose.mcp-http.yml build --no-cache

# 启动服务
echo "启动服务..."
docker compose -f docker-compose.mcp-http.yml up -d

# 等待服务启动
echo "等待服务启动..."
sleep 15

# 检查服务状态
echo ""
echo "=========================================="
echo "服务状态检查"
echo "=========================================="

# 检查容器状态
echo -e "\n${YELLOW}容器状态:${NC}"
docker compose -f docker-compose.mcp-http.yml ps

# 检查健康状态
echo -e "\n${YELLOW}健康检查:${NC}"
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ MCP 服务器健康检查通过${NC}"
    
    # 显示详细信息
    health_info=$(curl -s http://localhost:8001/health | python3 -m json.tool 2>/dev/null || echo "{}")
    echo "$health_info"
else
    echo -e "${RED}✗ MCP 服务器健康检查失败${NC}"
    echo "查看日志:"
    docker compose -f docker-compose.mcp-http.yml logs --tail=50 mem0-mcp-http-server
    exit 1
fi

# 显示访问信息
echo ""
echo "=========================================="
echo "部署成功！"
echo "=========================================="
echo ""
echo "服务访问地址:"
echo "  - MCP 服务器: http://localhost:8001"
echo "  - 健康检查: http://localhost:8001/health"
echo "  - Qdrant 控制台: http://localhost:6333/dashboard"
echo ""
echo "查看日志:"
echo "  docker compose -f docker-compose.mcp-http.yml logs -f"
echo ""
echo "停止服务:"
echo "  docker compose -f docker-compose.mcp-http.yml down"
echo ""
echo "=========================================="

# 显示资源使用
echo -e "\n${YELLOW}资源使用情况:${NC}"
docker stats --no-stream mem0-qdrant mem0-mcp-http-server
